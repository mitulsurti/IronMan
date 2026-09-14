from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ironman.data_fabric.models import DataObservation, DataSource, FreshnessState, ObservationQuality, ObservationType


class ObservationValidationError(ValueError):
    pass


def validate_observation(observation) -> None:
    if observation.ingested_at.tzinfo is None:
        raise ObservationValidationError("ingestion timestamp must be timezone-aware")
    if observation.observed_at is not None and observation.observed_at.tzinfo is None:
        raise ObservationValidationError("observation timestamp must be timezone-aware when supplied")
    if observation.observed_at is not None and observation.observed_at.utcoffset() != timezone.utc.utcoffset(observation.observed_at):
        raise ObservationValidationError("observation timestamp must be UTC")
    if observation.ingested_at.utcoffset() != timezone.utc.utcoffset(observation.ingested_at):
        raise ObservationValidationError("ingestion timestamp must be UTC")
    if observation.observation_type in (ObservationType.PRICE, ObservationType.FUNDAMENTAL) and observation.instrument_id is None:
        raise ObservationValidationError("instrument_id is required for price/fundamental observations")
    if observation.observation_type == ObservationType.FX:
        if not observation.values.get("base_currency") or not observation.values.get("quote_currency"):
            raise ObservationValidationError("FX observations require an explicit currency pair")
        if observation.values["base_currency"] == observation.values["quote_currency"]:
            raise ObservationValidationError("FX currency pair must differ")
    if observation.value is not None and observation.value < 0:
        raise ObservationValidationError("observation value cannot be negative")
    if not observation.provenance or not observation.provenance.get("source"):
        raise ObservationValidationError("observation provenance requires source")
    if observation.freshness in (FreshnessState.STALE, FreshnessState.INSUFFICIENT) or observation.quality in (ObservationQuality.INVALID, ObservationQuality.CONFLICTING, ObservationQuality.MISSING):
        return


def persist_source(session: Session, source: DataSource) -> DataSource:
    session.add(source)
    session.flush()
    return source


def persist_observation(session: Session, observation: DataObservation) -> DataObservation:
    validate_observation(observation)
    observation.observation_type = getattr(observation.observation_type, "value", observation.observation_type)
    observation.quality = getattr(observation.quality, "value", observation.quality)
    observation.freshness = getattr(observation.freshness, "value", observation.freshness)
    session.add(observation)
    session.flush()
    return observation


def observation_gate(observations: list[DataObservation], *, required_types: set[str]) -> str:
    by_type = {item.observation_type: item for item in observations}
    for observation_type in required_types:
        observation = by_type.get(observation_type)
        if observation is None or observation.quality in (ObservationQuality.MISSING, ObservationQuality.INVALID) or observation.freshness in (FreshnessState.STALE, FreshnessState.INSUFFICIENT):
            return "STALE" if observation and observation.freshness == FreshnessState.STALE else "INSUFFICIENT"
        if observation.quality == ObservationQuality.CONFLICTING:
            return "CONFLICTING"
    return "PASS"
