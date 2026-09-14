from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class OpportunityInput(BaseModel):
    name: str
    kind: str
    instrument_id: UUID | None = None
    currency: str
    value: Decimal = Decimal("0")
    quality_state: str = "PASS"
    freshness_state: str = "PASS"
    concentration_group: str | None = None
    portfolio_weight: Decimal = Field(default=Decimal("0"), ge=0)
    observation_ids: list[UUID] = Field(default_factory=list)
    analytics: dict = Field(default_factory=dict)
    evidence: list[dict] = Field(default_factory=list)


class CapitalDeploymentRequest(BaseModel):
    portfolio_state_version_id: UUID
    amount: Decimal = Field(gt=0)
    currency: str = "INR"
    horizon: str = "CORE"
    minimum_cash_reserve: Decimal = Field(default=Decimal("0"), ge=0)
    max_concentration: Decimal | None = Field(default=None, ge=0, le=1)
    opportunities: list[OpportunityInput] = Field(min_length=1)


class InsightRead(BaseModel):
    id: UUID
    action: str
    horizon: str
    conclusion: str
    abstention_reason: str | None
    portfolio_state_version_id: UUID
    gates: dict
    alternatives: list
    evidence: list
    analytics: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class DecisionCreate(BaseModel):
    decision: str
    rationale: str | None = None
    modified_amount: Decimal | None = Field(default=None, ge=0)


class InsightRequestResponse(BaseModel):
    insight_id: UUID


class DecisionRead(BaseModel):
    id: UUID
    insight_id: UUID
    decision: str
    rationale: str | None
    modified_amount: Decimal | None
    created_at: datetime

    model_config = {"from_attributes": True}
