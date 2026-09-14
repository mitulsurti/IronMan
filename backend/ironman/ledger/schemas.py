from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AccountCreate(BaseModel):
    name: str
    account_type: str
    base_timezone: str | None = None


class AccountRead(AccountCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    active: bool


class InstrumentCreate(BaseModel):
    name: str
    instrument_type: str
    native_currency: str | None = Field(default=None, min_length=3, max_length=3)


class InstrumentRead(InstrumentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    active: bool


class InstrumentIdentifierCreate(BaseModel):
    provider: str
    identifier_type: str
    identifier: str
    valid_from: date | None = None
    valid_to: date | None = None


class StateVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    ledger_boundary: datetime
    boundary_sequence: int
    boundary_event_id: UUID | None
    calculation_version: str
    policy_version: str | None
    data_context: dict
    holdings: list
    cash_balances: list
    tax_lots: list
    content_hash: str
    created_at: datetime


class LegCreate(BaseModel):
    leg_type: str
    direction: str
    account_id: UUID
    instrument_id: UUID | None = None
    currency: str | None = None
    quantity: Decimal | None = Field(default=None, ge=0)
    amount: Decimal | None = Field(default=None, ge=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    cost_basis: Decimal | None = Field(default=None, ge=0)


class EventCreate(BaseModel):
    event_type: str
    effective_at: datetime
    financial_date: date
    timezone: str
    sequence: int = 0
    source: str
    source_event_id: str | None = None
    ingestion_id: str | None = None
    correlation_id: UUID | None = None
    correction_of_id: UUID | None = None
    metadata_json: dict = Field(default_factory=dict)
    legs: list[LegCreate]
    lot_allocations: list[dict] = Field(default_factory=list)


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    event_type: str
    effective_at: datetime
    financial_date: date
    timezone: str
    sequence: int
    source: str
    source_event_id: str | None
    posted: bool
