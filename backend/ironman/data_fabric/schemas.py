from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from ironman.data_fabric.models import FreshnessState, ObservationQuality, ObservationType


class ObservationCreate(BaseModel):
    observation_type: ObservationType
    instrument_id: UUID | None = None
    source_id: UUID
    provider_observation_id: str | None = None
    observed_at: datetime | None = None
    ingested_at: datetime
    vintage_date: date | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    unit: str | None = None
    frequency: str | None = None
    value: Decimal | None = None
    values: dict = Field(default_factory=dict)
    quality: ObservationQuality
    freshness: FreshnessState
    raw_reference: str | None = None
    content_hash: str | None = None
    schema_version: str
    provenance: dict = Field(default_factory=dict)
    licensing: dict = Field(default_factory=dict)


class DataSourceCreate(BaseModel):
    provider: str
    source_identifier: str
    licensing: dict = Field(default_factory=dict)
    adapter_version: str
