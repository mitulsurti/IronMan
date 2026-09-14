from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class ClaimKind(StrEnum):
    FACT = "FACT"
    INFERENCE = "INFERENCE"
    UNKNOWN = "UNKNOWN"
    CONTRADICTION = "CONTRADICTION"


class ThesisImpact(StrEnum):
    STRENGTHENS = "STRENGTHENS"
    WEAKENS = "WEAKENS"
    CONTRADICTS = "CONTRADICTS"
    DOES_NOT_ADDRESS = "DOES_NOT_ADDRESS"


class EvidenceItem(BaseModel):
    evidence_id: str
    source: str
    observed_at: datetime | None = None
    vintage: str | None = None
    excerpt: str
    provenance: dict = Field(default_factory=dict)
    quality: str = "VALID"
    freshness: str = "VALID"
    document_id: UUID | None = None
    title: str | None = None
    external_reference: str | None = None
    source_tier: str | None = None
    content_hash: str | None = None
    status: str = "VALID"
    passage_reference: str | None = None


class ResearchRequest(BaseModel):
    question: str
    instrument_id: UUID | None = None
    portfolio_state_version_id: UUID | None = None
    thesis: dict | None = None
    observations: list[dict] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    scope: str = "investment_research"


class ResearchClaim(BaseModel):
    text: str
    kind: ClaimKind
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: str = "LOW"


class ResearchResult(BaseModel):
    conclusion: str
    claims: list[ResearchClaim]
    material_changes: list[str] = Field(default_factory=list)
    thesis_impacts: list[ThesisImpact] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    unanswered_questions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    uncertainty: str
    data_quality_concerns: list[str] = Field(default_factory=list)
    model_provider: str
    model_version: str
    prompt_version: str
    researched_at: datetime
    input_evidence_ids: list[str] = Field(default_factory=list)
    assessment: str | None = None
    relevant_macro_factors: list[str] = Field(default_factory=list)
    fx_implications: list[str] = Field(default_factory=list)
    data_quality_assessment: str | None = None
    comparison_summary: str | None = None
    cash_flow_interpretation: str | None = None
    yield_interpretation: str | None = None
    maturity_liquidity_interpretation: str | None = None
    credit_interpretation: str | None = None
    currency_interpretation: str | None = None
    tax_cost_interpretation: str | None = None
    portfolio_role: str | None = None
    opportunity_cost_interpretation: str | None = None
