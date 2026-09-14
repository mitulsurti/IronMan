from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, JSON, Numeric, String, Uuid, event
from sqlalchemy.orm import Mapped, mapped_column

from ironman.db.base import Base


class ObservationQuality(StrEnum):
    VALID = "VALID"
    MISSING = "MISSING"
    CONFLICTING = "CONFLICTING"
    INVALID = "INVALID"


class FreshnessState(StrEnum):
    VALID = "VALID"
    STALE = "STALE"
    INSUFFICIENT = "INSUFFICIENT"


class ObservationType(StrEnum):
    PRICE = "PRICE"
    FX = "FX"
    FUNDAMENTAL = "FUNDAMENTAL"


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    provider: Mapped[str] = mapped_column(String(200), nullable=False)
    source_identifier: Mapped[str] = mapped_column(String(300), nullable=False)
    licensing: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    adapter_version: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DataObservation(Base):
    __tablename__ = "data_observations"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    observation_type: Mapped[str] = mapped_column(String(30), nullable=False)
    instrument_id: Mapped[UUID | None] = mapped_column(ForeignKey("instruments.id"))
    source_id: Mapped[UUID] = mapped_column(ForeignKey("data_sources.id"), nullable=False)
    provider_observation_id: Mapped[str | None] = mapped_column(String(300))
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    vintage_date: Mapped[date | None] = mapped_column(Date)
    currency: Mapped[str | None] = mapped_column(String(3))
    unit: Mapped[str | None] = mapped_column(String(50))
    frequency: Mapped[str | None] = mapped_column(String(30))
    value: Mapped[Decimal | None] = mapped_column(Numeric(30, 12))
    values: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    quality: Mapped[str] = mapped_column(String(30), nullable=False)
    freshness: Mapped[str] = mapped_column(String(30), nullable=False)
    raw_reference: Mapped[str | None] = mapped_column(String(500))
    content_hash: Mapped[str | None] = mapped_column(String(128))
    schema_version: Mapped[str] = mapped_column(String(100), nullable=False)
    provenance: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    licensing: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


@event.listens_for(DataObservation, "before_insert")
def _normalize_observation_enums(mapper, connection, target) -> None:
    target.observation_type = getattr(target.observation_type, "value", target.observation_type)
    target.quality = getattr(target.quality, "value", target.quality)
    target.freshness = getattr(target.freshness, "value", target.freshness)
