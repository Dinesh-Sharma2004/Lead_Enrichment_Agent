import { CompanyIntelligence } from "./types";

/**
 * Escapes a single CSV field value according to RFC 4180:
 * Wraps values with double quotes and doubles any existing double quotes.
 */
function escapeCsvValue(val: unknown): string {
  if (val === null || val === undefined) return '""';
  const str = String(val);
  return `"${str.replace(/"/g, '""')}"`;
}

/**
 * Converts a list of CompanyIntelligence records into a valid CSV string.
 */
export function generateCompanyCsv(companies: CompanyIntelligence[]): string {
  const headers = [
    "Domain",
    "Company Name",
    "Company Overview",
    "Overview Source URL",
    "Target Audience",
    "Target Audience Source URL",
    "Products & Services",
    "Leadership",
    "Contact Points",
    "Overall Confidence Score",
    "LLM Confidence Score",
    "Heuristic Confidence Score",
    "Confidence Rationale",
    "Extraction Status",
    "Total Tokens Used",
    "Estimated Cost (USD)",
    "Processed URLs",
  ];

  const rows: string[] = [headers.map(escapeCsvValue).join(",")];

  for (const c of companies) {
    const productsStr = (c.products_services || [])
      .map((p) => `${p.name}: ${p.description}`)
      .join(" | ");

    const leadershipStr = (c.leadership || [])
      .map((l) => {
        const li = l.linkedin_url ? ` [LinkedIn: ${l.linkedin_url}]` : "";
        return `${l.name} (${l.role || "Team"})${li}`;
      })
      .join(" | ");

    const contactsStr = (c.contact_points || [])
      .map((cp) => `${cp.type}: ${cp.value}`)
      .join(" | ");

    const processedUrlsStr = (c.all_processed_urls || []).join(", ");

    const row = [
      c.domain,
      c.company_name,
      c.company_overview,
      c.overview_source_url,
      c.target_audience,
      c.target_audience_source_url,
      productsStr,
      leadershipStr,
      contactsStr,
      c.confidence_score,
      c.llm_confidence_score,
      c.heuristic_confidence_score,
      c.confidence_rationale,
      c.extraction_status,
      c.total_tokens_used,
      c.estimated_cost_usd,
      processedUrlsStr,
    ];

    rows.push(row.map(escapeCsvValue).join(","));
  }

  return rows.join("\r\n");
}

/**
 * Triggers a browser-side file download without requiring server-side storage.
 */
export function triggerFileDownload(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

