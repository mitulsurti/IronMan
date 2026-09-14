from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from ironman.data_fabric.models import DataObservation, DataSource, FreshnessState, ObservationQuality, ObservationType
from ironman.data_fabric.service import ObservationValidationError, observation_gate, persist_observation
from ironman.intelligence.orchestrator import CapitalDeploymentOrchestrator
from ironman.intelligence.schemas import CapitalDeploymentRequest, OpportunityInput
from ironman.intelligence.models import OpportunityKind
from ironman.ledger.models import Instrument, InstrumentType, PortfolioStateVersion


def source(session):
    item = DataSource(provider="fixture", source_identifier="fixture-v1", licensing={"send_to_ai": True}, adapter_version="1", created_at=datetime.now(timezone.utc))
    session.add(item)
    session.flush()
    return item


def observation(session, source_id, **kwargs):
    instrument_id = kwargs.pop("instrument_id", uuid4())
    session.add(__import__("ironman.ledger.models", fromlist=["Instrument"]).Instrument(id=instrument_id, name="Fixture", instrument_type="EQUITY", native_currency="INR", created_at=datetime.now(timezone.utc)))
    session.flush()
    item = DataObservation(observation_type=ObservationType.PRICE, instrument_id=instrument_id, source_id=source_id, observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc), ingested_at=datetime(2026, 1, 1, 1, tzinfo=timezone.utc), currency="INR", unit="price", value=Decimal("100"), quality=ObservationQuality.VALID, freshness=FreshnessState.VALID, schema_version="1", provenance={"source": "fixture"}, licensing={"send_to_ai": True}, created_at=datetime.now(timezone.utc), **kwargs)
    persist_observation(session, item)
    return item


def test_valid_and_provenance_survive_persistence(sqlite_session):
    item = observation(sqlite_session, source(sqlite_session).id)
    sqlite_session.commit()
    loaded = sqlite_session.get(DataObservation, item.id)
    assert loaded.provenance["source"] == "fixture"
    assert loaded.instrument_id == item.instrument_id


def test_stale_invalid_conflicting_and_missing_gate():
    source_id = uuid4()
    base = {"observation_type": ObservationType.PRICE, "source_id": source_id, "instrument_id": uuid4()}
    assert observation_gate([type("O", (), {"observation_type": ObservationType.PRICE, "quality": ObservationQuality.VALID, "freshness": FreshnessState.STALE})()], required_types={ObservationType.PRICE}) == "STALE"
    assert observation_gate([type("O", (), {"observation_type": ObservationType.PRICE, "quality": ObservationQuality.CONFLICTING, "freshness": FreshnessState.VALID})()], required_types={ObservationType.PRICE}) == "CONFLICTING"
    assert observation_gate([], required_types={ObservationType.PRICE}) == "INSUFFICIENT"


def test_fx_requires_explicit_distinct_pair(sqlite_session):
    source_id = source(sqlite_session).id
    item = DataObservation(observation_type=ObservationType.FX, source_id=source_id, observed_at=datetime.now(timezone.utc), ingested_at=datetime.now(timezone.utc), value=Decimal("83"), quality=ObservationQuality.VALID, freshness=FreshnessState.VALID, schema_version="1", provenance={"source": "fixture"}, licensing={}, values={"base_currency": "INR", "quote_currency": "USD"}, created_at=datetime.now(timezone.utc))
    persist_observation(sqlite_session, item)
    with pytest.raises(ObservationValidationError):
        persist_observation(sqlite_session, DataObservation(observation_type=ObservationType.FX, source_id=source_id, observed_at=datetime.now(timezone.utc), ingested_at=datetime.now(timezone.utc), value=Decimal("1"), quality=ObservationQuality.VALID, freshness=FreshnessState.VALID, schema_version="1", provenance={"source": "fixture"}, licensing={}, values={"base_currency": "INR", "quote_currency": "INR"}, created_at=datetime.now(timezone.utc)))


def test_capital_deployment_blocks_missing_observation(sqlite_session):
    state = PortfolioStateVersion(id=uuid4(), ledger_boundary=datetime.now(timezone.utc), boundary_sequence=1, boundary_event_id=uuid4(), calculation_version="phase2", content_hash="valid", holdings=[], cash_balances=[{"account_id": "a", "currency": "INR", "amount": "100000"}], tax_lots=[], data_context={}, created_at=datetime.now(timezone.utc))
    instrument = Instrument(id=uuid4(), name="Candidate", instrument_type=InstrumentType.EQUITY, native_currency="INR", created_at=datetime.now(timezone.utc))
    sqlite_session.add_all([state, instrument])
    sqlite_session.flush()
    request = CapitalDeploymentRequest(portfolio_state_version_id=state.id, amount=Decimal("1000"), opportunities=[OpportunityInput(name="Candidate", kind=OpportunityKind.CANDIDATE, instrument_id=instrument.id, currency="INR", evidence=[{"source": "fixture"}])])
    insight = CapitalDeploymentOrchestrator().run(sqlite_session, state, request, "owner")
    assert insight.action == "NO_ACTION"
    assert insight.gates["observations"] == "INSUFFICIENT"
