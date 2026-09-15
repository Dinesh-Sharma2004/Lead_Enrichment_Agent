import asyncio
import pytest
from src.schemas import CompanyIntelligence

def test_batch_processing_failure_isolation():
    async def _test_impl():
        domains = ["good1.com", "failing.com", "good2.com"]

        async def mock_process_domain(domain, browser_manager):
            if domain == "failing.com":
                raise ValueError("Simulated domain crash")
            return CompanyIntelligence(
                domain=domain,
                company_name=domain.split('.')[0].capitalize(),
                company_overview="Valid overview text.",
                confidence_score=0.9,
                llm_confidence_score=0.9,
                heuristic_confidence_score=0.9,
                extraction_status="Success"
            )

        tasks = [mock_process_domain(d, None) for d in domains]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        results = []
        for domain, res in zip(domains, raw_results):
            if isinstance(res, Exception):
                fallback = CompanyIntelligence(
                    domain=domain,
                    company_name=domain.split('.')[0].capitalize(),
                    company_overview="",
                    extraction_status=f"Failed - Unhandled exception: {res}",
                    confidence_score=0.0,
                    llm_confidence_score=0.0,
                    heuristic_confidence_score=0.0
                )
                results.append(fallback)
            else:
                results.append(res)

        assert len(results) == 3
        assert results[0].domain == "good1.com"
        assert results[0].confidence_score == 0.9
        assert results[1].domain == "failing.com"
        assert "Failed - Unhandled exception" in results[1].extraction_status
        assert results[1].confidence_score == 0.0
        assert results[2].domain == "good2.com"

    asyncio.run(_test_impl())
