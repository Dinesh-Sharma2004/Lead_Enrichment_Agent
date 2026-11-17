"""
FastAPI application for the Autonomous Lead Enrichment Agent.
Designed for Vercel Services deployment and local development.
"""

import sys
import os
import asyncio
import json
import re
import ipaddress
import socket
from pathlib import Path
from typing import List, Optional, AsyncGenerator

# ---------------------------------------------------------------------------
# Ensure backend directory is in sys.path so `src.*` modules resolve cleanly
# whether launched from repository root or backend directory.
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

ROOT_DIR = BACKEND_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.browser import BrowserManager
from src.agent import process_domain
from src.schemas import CompanyIntelligence
from src.logger import get_logger
from src.config import (
    MAX_CONCURRENT_DOMAINS,
    MAX_DOMAINS_PER_REQUEST,
    BATCH_TIMEOUT_SECONDS,
)

logger = get_logger("backend.main")

# ---------------------------------------------------------------------------
# App Initialization & OpenAPI Configuration
# Explicitly registers docs under /api to comply with Vercel path preservation
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Autonomous Lead Enrichment Agent API",
    description="Enterprise-grade corporate intelligence extraction engine powered by Groq LLMs and SerpAPI.",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Enable CORS for local development across Vite/Next.js and FastAPI ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Limits (loaded from src.config with environment fallbacks)

# SSRF and Private IP blocklists
BLOCKED_HOSTNAMES = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "metadata.google.internal",
    "instance-data",
    "169.254.169.254",
}

DOMAIN_REGEX = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)


class EnrichRequest(BaseModel):
    domains: List[str] = Field(
        ...,
        description="List of company domains to enrich (e.g. ['stripe.com', 'linear.app'])",
        json_schema_extra={"example": ["stripe.com", "notion.so"]},
    )


def validate_and_normalize_domain(raw_domain: str) -> str:
    """
    Validates, sanitizes, and normalizes a submitted domain string.
    Guards against SSRF, internal network probing, and malicious input.
    """
    if not raw_domain or not isinstance(raw_domain, str):
        raise ValueError("Domain must be a non-empty string.")

    cleaned = raw_domain.strip().lower()

    # Strip URL schemes
    if cleaned.startswith("http://"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("https://"):
        cleaned = cleaned[8:]

    # Remove paths, queries, ports, and trailing slashes
    cleaned = cleaned.split("/")[0].split("?")[0].split("#")[0].split(":")[0].strip()

    if not cleaned:
        raise ValueError("Domain name cannot be empty.")

    # Check blocked hostnames
    if cleaned in BLOCKED_HOSTNAMES:
        raise ValueError(f"Domain '{cleaned}' is not permitted.")

    # Check if string is an IP address
    try:
        ip_obj = ipaddress.ip_address(cleaned)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved or ip_obj.is_multicast:
            raise ValueError(f"IP destination '{cleaned}' is in a reserved/private range.")
        raise ValueError(f"IP addresses are not permitted as domains: '{cleaned}'.")
    except ValueError as e:
        if "is not permitted" in str(e) or "reserved/private" in str(e):
            raise

    # Validate domain name syntax
    if not DOMAIN_REGEX.match(cleaned):
        raise ValueError(f"Invalid domain format: '{cleaned}'. Must be a valid FQDN (e.g. 'company.com').")

    return cleaned


# ---------------------------------------------------------------------------
# Health Check Endpoint
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health_check():
    """
    Returns API health status and environment readiness without exposing keys.
    """
    groq_set = bool(os.environ.get("GROQ_API_KEY"))
    serpapi_set = bool(os.environ.get("SERPAPI_API_KEY"))
    enable_serpapi = os.environ.get("ENABLE_SERPAPI", "False").lower() in ("true", "1", "yes")

    return {
        "status": "ok",
        "service": "Lead Enrichment Agent Backend",
        "version": "2.0.0",
        "environment": {
            "GROQ_API_KEY_configured": groq_set,
            "SERPAPI_API_KEY_configured": serpapi_set,
            "ENABLE_SERPAPI": enable_serpapi,
            "MAX_CONCURRENT_DOMAINS": MAX_CONCURRENT_DOMAINS,
            "MAX_DOMAINS_PER_REQUEST": MAX_DOMAINS_PER_REQUEST,
        },
    }


# Root info endpoint
@app.get("/api")
async def api_root():
    return {
        "status": "ok",
        "service": "Autonomous Lead Enrichment Agent API",
        "docs": "/api/docs",
        "health": "/api/health",
        "stream": "/api/enrich/stream",
    }


# ---------------------------------------------------------------------------
# Streaming Enrichment Endpoint (Server-Sent Events)
# ---------------------------------------------------------------------------
@app.post("/api/enrich/stream")
async def enrich_stream(request: Request, body: EnrichRequest):
    """
    Executes the lead enrichment pipeline for submitted domains and streams
    results incrementally via Server-Sent Events (SSE).
    """
    if not body.domains:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain list cannot be empty.",
        )

    # Validate and normalize domains
    normalized_domains = []
    seen = set()
    validation_errors = []

    for d in body.domains:
        try:
            clean = validate_and_normalize_domain(d)
            if clean not in seen:
                seen.add(clean)
                normalized_domains.append(clean)
        except ValueError as err:
            validation_errors.append(str(err))

    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Domain validation failed: {'; '.join(validation_errors)}",
        )

    if not normalized_domains:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid domains found after normalization.",
        )

    if len(normalized_domains) > MAX_DOMAINS_PER_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_DOMAINS_PER_REQUEST} domains allowed per request to ensure execution safety.",
        )

    async def event_generator() -> AsyncGenerator[str, None]:
        def format_sse(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data)}\n\n"

        # Emit initial started event
        yield format_sse("started", {
            "total": len(normalized_domains),
            "domains": normalized_domains
        })

        effective_concurrency = min(MAX_CONCURRENT_DOMAINS, 2)
        browser_manager = BrowserManager(max_concurrent=effective_concurrency)
        await browser_manager.start()

        success_count = 0
        failure_count = 0
        start_time = asyncio.get_event_loop().time()

        try:
            for domain in normalized_domains:
                # Check for client disconnection
                if await request.is_disconnected():
                    logger.warning("Client disconnected from SSE stream. Terminating pipeline.")
                    break

                # Bounded execution budget check
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= BATCH_TIMEOUT_SECONDS:
                    logger.warning(f"Batch timeout budget ({BATCH_TIMEOUT_SECONDS}s) reached. Aborting domain {domain}.")
                    timeout_fallback = CompanyIntelligence(
                        domain=domain,
                        company_name=domain.split(".")[0].capitalize(),
                        company_overview="",
                        extraction_status="Failed - Execution timeout budget reached.",
                        confidence_score=0.0,
                        llm_confidence_score=0.0,
                        heuristic_confidence_score=0.0,
                        confidence_rationale="Execution halted to prevent serverless function termination.",
                    )
                    failure_count += 1
                    yield format_sse("domain_failed", {
                        "domain": domain,
                        "status": "failed",
                        "error": "Execution timeout budget reached.",
                        "result": timeout_fallback.model_dump(),
                    })
                    continue

                # Notify that domain processing has started
                yield format_sse("domain_started", {
                    "domain": domain,
                    "status": "processing"
                })

                try:
                    # Execute domain enrichment pipeline
                    intel: CompanyIntelligence = await process_domain(domain, browser_manager)
                    
                    if "Failed" in intel.extraction_status or intel.confidence_score == 0.0:
                        failure_count += 1
                        yield format_sse("domain_failed", {
                            "domain": domain,
                            "status": "partial_or_failed",
                            "error": intel.extraction_status,
                            "result": intel.model_dump(),
                        })
                    else:
                        success_count += 1
                        yield format_sse("domain_completed", {
                            "domain": domain,
                            "status": "completed",
                            "result": intel.model_dump(),
                        })
                except Exception as exc:
                    logger.error(f"Unhandled exception processing domain {domain}: {exc}", exc_info=True)
                    failure_count += 1
                    err_fallback = CompanyIntelligence(
                        domain=domain,
                        company_name=domain.split(".")[0].capitalize(),
                        company_overview="",
                        extraction_status=f"Failed - Internal error processing domain: {str(exc)[:100]}",
                        confidence_score=0.0,
                        llm_confidence_score=0.0,
                        heuristic_confidence_score=0.0,
                        confidence_rationale=f"Error encountered: {str(exc)[:100]}",
                    )
                    yield format_sse("domain_failed", {
                        "domain": domain,
                        "status": "failed",
                        "error": str(exc)[:200],
                        "result": err_fallback.model_dump(),
                    })

            # Emit final completed event
            yield format_sse("completed", {
                "total": len(normalized_domains),
                "success_count": success_count,
                "failure_count": failure_count,
            })

        finally:
            await browser_manager.stop()
            logger.info("Browser manager stopped and SSE stream closed.")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream",
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
