"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  CompanyIntelligence,
  DomainStatusItem,
  BackendHealthResponse,
} from "@/lib/types";
import { checkBackendHealth } from "@/lib/api";
import { streamEnrichment } from "@/lib/sse";
import { DomainInput } from "@/components/DomainInput";
import { ProcessingStatus } from "@/components/ProcessingStatus";
import { CompanyCard } from "@/components/CompanyCard";
import { ExportResults } from "@/components/ExportResults";
import {
  Bot,
  FileCode2,
  Activity,
  AlertCircle,
  Database,
  ExternalLink,
  ShieldAlert,
} from "lucide-react";

export default function Home() {
  const [health, setHealth] = useState<BackendHealthResponse | null>(null);
  const [healthChecked, setHealthChecked] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [statusItems, setStatusItems] = useState<DomainStatusItem[]>([]);
  const [results, setResults] = useState<CompanyIntelligence[]>([]);
  const [streamError, setStreamError] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    async function loadHealth() {
      const h = await checkBackendHealth();
      setHealth(h);
      setHealthChecked(true);
    }
    loadHealth();
  }, []);

  const handleStartEnrichment = async (domains: string[]) => {
    setIsLoading(true);
    setStreamError(null);

    // Initialize domain status items
    const initialStatuses: DomainStatusItem[] = domains.map((domain) => ({
      domain,
      stage: "Queued",
    }));
    setStatusItems(initialStatuses);

    // Setup AbortController for cancel capability
    const controller = new AbortController();
    abortControllerRef.current = controller;

    await streamEnrichment(
      domains,
      {
        onStarted: (data) => {
          setStatusItems(
            data.domains.map((d) => ({
              domain: d,
              stage: "Discovering pages",
            }))
          );
        },
        onDomainStarted: (data) => {
          setStatusItems((prev) =>
            prev.map((item) =>
              item.domain === data.domain
                ? { ...item, stage: "Extracting information" }
                : item
            )
          );
        },
        onDomainCompleted: (data) => {
          setStatusItems((prev) =>
            prev.map((item) =>
              item.domain === data.domain
                ? { ...item, stage: "Completed", result: data.result }
                : item
            )
          );

          // Add or replace completed company result immediately
          setResults((prev) => {
            const exists = prev.some((c) => c.domain === data.domain);
            if (exists) {
              return prev.map((c) => (c.domain === data.domain ? data.result : c));
            }
            return [data.result, ...prev];
          });
        },
        onDomainFailed: (data) => {
          setStatusItems((prev) =>
            prev.map((item) =>
              item.domain === data.domain
                ? {
                    ...item,
                    stage: "Failed",
                    error: data.error,
                    result: data.result,
                  }
                : item
            )
          );

          // Still preserve the failed record so the user can inspect details
          if (data.result) {
            setResults((prev) => {
              const exists = prev.some((c) => c.domain === data.domain);
              if (exists) {
                return prev.map((c) => (c.domain === data.domain ? data.result : c));
              }
              return [data.result, ...prev];
            });
          }
        },
        onCompleted: () => {
          setIsLoading(false);
          abortControllerRef.current = null;
        },
        onError: (errMsg) => {
          setStreamError(errMsg);
          setIsLoading(false);
          abortControllerRef.current = null;
        },
      },
      controller.signal
    );

    setIsLoading(false);
    abortControllerRef.current = null;
  };

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsLoading(false);
    setStatusItems((prev) =>
      prev.map((item) =>
        item.stage === "Completed" || item.stage === "Failed"
          ? item
          : { ...item, stage: "Failed", error: "Cancelled by user" }
      )
    );
  };

  return (
    <main className="min-h-screen pb-16 bg-[#0b0f19] text-slate-100">
      {/* Header / Navbar */}
      <header className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-base tracking-tight text-slate-100 flex items-center gap-2">
                Lead Enrichment Agent
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-400 font-mono border border-sky-500/20 font-medium">
                  v2.0
                </span>
              </h1>
              <p className="text-xs text-slate-400 hidden sm:block">
                Turn company websites into structured, evidence-backed intelligence.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Backend connection pill */}
            <div
              className={`px-2.5 py-1 rounded-full text-xs font-medium border flex items-center gap-1.5 ${
                health
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                  : healthChecked
                  ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                  : "bg-slate-800 text-slate-400 border-slate-700"
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              <span>
                {health
                  ? "FastAPI Backend Ready"
                  : healthChecked
                  ? "Backend Offline"
                  : "Checking Backend..."}
              </span>
            </div>

            {/* Swagger API docs link */}
            <a
              href="/api/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 sm:px-2.5 sm:py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors flex items-center gap-1.5"
              title="Open FastAPI Swagger Documentation"
            >
              <FileCode2 className="w-4 h-4 text-sky-400" />
              <span className="hidden sm:inline">API Docs</span>
              <ExternalLink className="w-3 h-3 text-slate-400 hidden sm:inline" />
            </a>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 pt-8 space-y-6">
        {/* Domain Input Section */}
        <DomainInput
          onEnrich={handleStartEnrichment}
          isLoading={isLoading}
          maxDomains={health?.environment?.MAX_DOMAINS_PER_REQUEST || 3}
        />

        {/* Stream Error Alert */}
        {streamError && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="font-semibold text-rose-200">Pipeline Communication Error</h4>
              <p className="text-xs text-rose-300/90 leading-relaxed">{streamError}</p>
            </div>
          </div>
        )}

        {/* Live Processing Status Panel */}
        <ProcessingStatus
          items={statusItems}
          onCancel={handleCancel}
          isLoading={isLoading}
        />

        {/* Results Section */}
        <section className="space-y-4 pt-2">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-sky-400" />
              <h2 className="font-bold text-slate-100 text-base">
                Enriched Corporate Intelligence
              </h2>
              {results.length > 0 && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 font-mono">
                  {results.length} companies
                </span>
              )}
            </div>

            <ExportResults companies={results} />
          </div>

          {/* Result Cards List */}
          {results.length > 0 ? (
            <div className="space-y-3">
              {results.map((comp, idx) => (
                <CompanyCard
                  key={`${comp.domain}-${idx}`}
                  company={comp}
                  defaultExpanded={idx === 0}
                />
              ))}
            </div>
          ) : (
            !isLoading && (
              <div className="p-12 text-center rounded-xl border border-dashed border-slate-800 bg-slate-900/30 space-y-2">
                <Database className="w-8 h-8 text-slate-600 mx-auto" />
                <h3 className="font-medium text-slate-300 text-sm">No Companies Enriched Yet</h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  Submit up to 3 domains above to crawl their websites, clean HTML, and extract structured B2B corporate intelligence.
                </p>
              </div>
            )
          )}
        </section>
      </div>
    </main>
  );
}

