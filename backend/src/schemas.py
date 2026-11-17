from typing import List, Optional
from pydantic import BaseModel, Field

class Leader(BaseModel):
    name: str = Field(default="", description="Full name of the leader or key team member.")
    role: str = Field(default="", description="Job title or role of the person.")
    linkedin_url: Optional[str] = Field(default=None, description="LinkedIn profile URL if available.")
    source_url: str = Field(default="", min_length=1, description="The specific URL where this leadership information was found.")
    grounded: bool = Field(default=True, description="Whether this entry was verified against crawled page URLs.")

class ProductOrService(BaseModel):
    name: str = Field(default="", description="Name of the product or service.")
    description: str = Field(default="", min_length=1, description="Brief description of the product or service.")
    source_url: str = Field(default="", min_length=1, description="The URL where this product/service was described.")
    grounded: bool = Field(default=True, description="Whether this entry was verified against crawled page URLs.")

class ContactPoint(BaseModel):
    type: str = Field(default="Email", description="Type of contact (e.g., General Email, Sales Email, Support, Phone).")
    value: str = Field(default="", min_length=1, description="The email address or phone number.")
    source_url: str = Field(default="", min_length=1, description="The URL where this contact point was found.")
    grounded: bool = Field(default=True, description="Whether this entry was verified against crawled page URLs.")

class CompanyIntelligence(BaseModel):
    domain: str = Field(default="", description="The company's domain name.")
    company_name: str = Field(default="Unknown", description="The official name of the company.")
    company_overview: str = Field(default="", description="Exactly two concise sentences describing what the company does.")
    overview_source_url: str = Field(default="", description="The primary URL used to determine the company overview.")
    target_audience: str = Field(default="", description="Description of the target audience or ideal customer profile.")
    target_audience_source_url: str = Field(default="", description="The URL used to determine the target audience.")
    products_services: List[ProductOrService] = Field(default_factory=list, description="List of products or services offered.")
    contact_points: List[ContactPoint] = Field(default_factory=list, description="Public contact emails or phone numbers.")
    leadership: List[Leader] = Field(default_factory=list, description="Key leadership or team members.")
    llm_confidence_score: float = Field(default=0.0, description="LLM self-assessed confidence score between 0.0 and 1.0.")
    heuristic_confidence_score: float = Field(default=0.0, description="Heuristic rule-based confidence score between 0.0 and 1.0.")
    confidence_score: float = Field(default=0.0, description="Final confidence score (minimum of LLM and heuristic scores).")
    confidence_rationale: str = Field(default="", description="Short rationale for the confidence assessment.")
    extraction_status: str = Field(default="Success", description="Status of the extraction, e.g., 'Success', 'Partial - Missing Leadership', etc.")
    all_processed_urls: List[str] = Field(default_factory=list, description="All URLs successfully processed during this extraction.")
    total_tokens_used: int = Field(default=0, description="Total LLM tokens consumed for this domain extraction.")
    estimated_cost_usd: float = Field(default=0.0, description="Estimated API cost in USD based on Groq token pricing.")


class SerpSearchResult(BaseModel):
    name: str
    role: str
    linkedin_url: Optional[str] = None

