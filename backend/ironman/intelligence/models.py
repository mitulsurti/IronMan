from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ironman.db.base import Base


class InsightAction(StrEnum):
    BUY = "BUY"
    ADD = "ADD"
    ACCUMULATE = "ACCUMULATE"
    HOLD = "HOLD"
    WAIT = "WAIT"
    WATCH = "WATCH"
    NO_ACTION = "NO_ACTION"
    RESEARCH_REQUIRED = "RESEARCH_REQUIRED"


class GateStatus(StrEnum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"
    INSUFFICIENT = "INSUFFICIENT"
    CONFLICTING = "CONFLICTING"
    STALE = "STALE"


class HumanDecision(StrEnum):
    ACCEPT = "ACCEPT"
    MODIFY = "MODIFY"
    REJECT = "REJECT"
    DEFER = "DEFER"


class OpportunityKind(StrEnum):
    HOLDING = "HOLDING"
    CANDIDATE = "CANDIDATE"
    WATCHLIST = "WATCHLIST"
    CASH = "CASH"
    FIXED_INCOME = "FIXED_INCOME"


class Opportunity(Base):
    __tablename__ = "intelligence_opportunities"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    instrument_id: Mapped[UUID | None] = mapped_column(ForeignKey("instruments.id"))
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False, default=0)
    quality_state: Mapped[str] = mapped_column(String(30), nullable=False)
    freshness_state: Mapped[str] = mapped_column(String(30), nullable=False)
    portfolio_weight: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False, default=0)
    concentration_group: Mapped[str | None] = mapped_column(String(200))
    analytics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    evidence: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StructuredInsight(Base):
    __tablename__ = "intelligence_insights"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    portfolio_state_version_id: Mapped[UUID] = mapped_column(ForeignKey("portfolio_state_versions.id"), nullable=False)
    requested_amount: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    horizon: Mapped[str] = mapped_column(String(30), nullable=False)
    conclusion: Mapped[str] = mapped_column(String(2000), nullable=False)
    thesis: Mapped[str | None] = mapped_column(String(2000))
    instrument_id: Mapped[UUID | None] = mapped_column(ForeignKey("instruments.id"))
    portfolio_context: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    analytics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    evidence: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    alternatives: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    gates: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    confidence: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    contradictions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    abstention_reason: Mapped[str | None] = mapped_column(String(1000))
    expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class InsightDecision(Base):
    __tablename__ = "intelligence_decisions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    insight_id: Mapped[UUID] = mapped_column(ForeignKey("intelligence_insights.id"), nullable=False)
    decision: Mapped[str] = mapped_column(String(30), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(200), nullable=False)
    rationale: Mapped[str | None] = mapped_column(String(2000))
    modified_amount: Mapped[Decimal | None] = mapped_column(Numeric(30, 12))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
