export interface Leader {
  name: string;
  role: string;
  linkedin_url?: string | null;
  source_url: string;
  grounded: boolean;
}

export interface ProductOrService {
  name: string;
  description: string;
  source_url: string;
  grounded: boolean;
}

export interface ContactPoint {
  type: string;
  value: string;
  source_url: string;
  grounded: boolean;
}

export interface CompanyIntelligence {
  domain: string;
  company_name: string;
  company_overview: string;
  overview_source_url: string;
  target_audience: string;
  target_audience_source_url: string;
  products_services: ProductOrService[];
  contact_points: ContactPoint[];
  leadership: Leader[];
  llm_confidence_score: number;
  heuristic_confidence_score: number;
  confidence_score: number;
  confidence_rationale: string;
  extraction_status: string;
  all_processed_urls: string[];
  total_tokens_used: number;
  estimated_cost_usd: number;
}

export type DomainProcessingStage =
  | "Queued"
  | "Discovering pages"
  | "Extracting information"
  | "Enriching leadership"
  | "Completed"
  | "Partial extraction"
  | "Failed";

export interface DomainStatusItem {
  domain: string;
  stage: DomainProcessingStage;
  error?: string;
  result?: CompanyIntelligence;
}

export interface SSEEventStarted {
  total: number;
  domains: string[];
}

export interface SSEEventDomainStarted {
  domain: string;
  status: string;
}

export interface SSEEventDomainCompleted {
  domain: string;
  status: string;
  result: CompanyIntelligence;
}

export interface SSEEventDomainFailed {
  domain: string;
  status: string;
  error: string;
  result: CompanyIntelligence;
}

export interface SSEEventCompleted {
  total: number;
  success_count: number;
  failure_count: number;
}

export interface BackendHealthResponse {
  status: string;
  service: string;
  version: string;
  environment: {
    GROQ_API_KEY_configured: boolean;
    SERPAPI_API_KEY_configured: boolean;
    ENABLE_SERPAPI: boolean;
    MAX_CONCURRENT_DOMAINS: number;
    MAX_DOMAINS_PER_REQUEST: number;
  };
}

