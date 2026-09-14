from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, UniqueConstraint, Uuid, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ironman.db.base import Base


class AccountType(StrEnum):
    BANK = "BANK"
    BROKER = "BROKER"
    CUSTODY = "CUSTODY"
    OTHER = "OTHER"


class InstrumentType(StrEnum):
    EQUITY = "EQUITY"
    BOND = "BOND"
    FUND = "FUND"
    GOLD = "GOLD"
    MLD = "MLD"
    OTHER = "OTHER"


class EventType(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    CASH_DEPOSIT = "CASH_DEPOSIT"
    CASH_WITHDRAWAL = "CASH_WITHDRAWAL"
    DIVIDEND = "DIVIDEND"
    FEE = "FEE"
    TAX = "TAX"
    TRANSFER = "TRANSFER"
    SPLIT = "SPLIT"
    BONUS = "BONUS"
    CORRECTION = "CORRECTION"


class LegType(StrEnum):
    CASH = "CASH"
    SECURITY = "SECURITY"
    FEE = "FEE"
    TAX = "TAX"


class LegDirection(StrEnum):
    IN = "IN"
    OUT = "OUT"


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    account_type: Mapped[str] = mapped_column(String(30), nullable=False)
    base_timezone: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    instrument_type: Mapped[str] = mapped_column(String(30), nullable=False)
    native_currency: Mapped[str | None] = mapped_column(String(3))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    identifiers: Mapped[list[InstrumentIdentifier]] = relationship(back_populates="instrument")


class InstrumentIdentifier(Base):
    __tablename__ = "instrument_identifiers"
    __table_args__ = (UniqueConstraint("provider", "identifier", "valid_from", name="uq_identifier_version"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    instrument_id: Mapped[UUID] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    identifier_type: Mapped[str] = mapped_column(String(50), nullable=False)
    identifier: Mapped[str] = mapped_column(String(300), nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    instrument: Mapped[Instrument] = relationship(back_populates="identifiers")


class LedgerEvent(Base):
    __tablename__ = "ledger_events"
    __table_args__ = (
        UniqueConstraint("source", "source_event_id", name="uq_ledger_source_event"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    financial_date: Mapped[date] = mapped_column(Date, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    source_event_id: Mapped[str | None] = mapped_column(String(300))
    ingestion_id: Mapped[str | None] = mapped_column(String(300))
    actor_id: Mapped[str] = mapped_column(String(200), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(30), nullable=False)
    correlation_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    correction_of_id: Mapped[UUID | None] = mapped_column(ForeignKey("ledger_events.id"))
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    posted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    legs: Mapped[list[LedgerLeg]] = relationship(back_populates="event", cascade="all, delete-orphan")
    lot_allocations: Mapped[list[TaxLotAllocation]] = relationship(
        foreign_keys="TaxLotAllocation.consumption_event_id",
        cascade="all, delete-orphan",
    )


class LedgerLeg(Base):
    __tablename__ = "ledger_legs"
    __table_args__ = (
        CheckConstraint("coalesce(quantity, 0) >= 0", name="ck_leg_quantity_nonnegative"),
        CheckConstraint("coalesce(amount, 0) >= 0", name="ck_leg_amount_nonnegative"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("ledger_events.id"), nullable=False)
    leg_type: Mapped[str] = mapped_column(String(30), nullable=False)
    direction: Mapped[str] = mapped_column(String(3), nullable=False)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    instrument_id: Mapped[UUID | None] = mapped_column(ForeignKey("instruments.id"))
    currency: Mapped[str | None] = mapped_column(String(3))
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(30, 12))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(30, 12))
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(30, 12))
    cost_basis: Mapped[Decimal | None] = mapped_column(Numeric(30, 12))
    event: Mapped[LedgerEvent] = relationship(back_populates="legs")


class TaxLotAllocation(Base):
    __tablename__ = "tax_lot_allocations"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_lot_allocation_quantity_positive"),
        CheckConstraint("cost_basis >= 0", name="ck_lot_allocation_cost_basis_nonnegative"),
        UniqueConstraint("consumption_event_id", "acquisition_event_id", name="uq_lot_allocation_pair"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    consumption_event_id: Mapped[UUID] = mapped_column(ForeignKey("ledger_events.id"), nullable=False)
    acquisition_event_id: Mapped[UUID] = mapped_column(ForeignKey("ledger_events.id"), nullable=False)
    instrument_id: Mapped[UUID] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    cost_basis: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CorporateAction(Base):
    __tablename__ = "corporate_actions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    instrument_id: Mapped[UUID] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(30), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    terms: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PortfolioStateVersion(Base):
    __tablename__ = "portfolio_state_versions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    ledger_boundary: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    boundary_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    boundary_event_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    calculation_version: Mapped[str] = mapped_column(String(100), nullable=False)
    policy_version: Mapped[str | None] = mapped_column(String(100))
    data_context: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    holdings: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    cash_balances: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    tax_lots: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


@event.listens_for(LedgerEvent, "before_update")
@event.listens_for(LedgerEvent, "before_delete")
def _protect_posted_event(mapper, connection, target) -> None:
    if target.posted:
        raise ValueError("posted ledger events are immutable")


@event.listens_for(LedgerLeg, "before_update")
@event.listens_for(LedgerLeg, "before_delete")
def _protect_posted_leg(mapper, connection, target) -> None:
    event_row = connection.execute(
        LedgerEvent.__table__.select().with_only_columns(LedgerEvent.posted).where(LedgerEvent.id == target.event_id)
    ).scalar_one_or_none()
    if event_row:
        raise ValueError("legs of posted ledger events are immutable")


@event.listens_for(PortfolioStateVersion, "before_update")
@event.listens_for(PortfolioStateVersion, "before_delete")
def _protect_state_version(mapper, connection, target) -> None:
    raise ValueError("portfolio state versions are immutable")
