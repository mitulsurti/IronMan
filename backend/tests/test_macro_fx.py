from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from ironman.ai.gateway import ModelGateway, ModelRegistry, ModelSpec
from ironman.data_fabric.models import DataObservation, DataSource, FreshnessState, ObservationQuality, ObservationType
from ironman.intelligence.orchestrator import CapitalDeploymentOrchestrator
from ironman.intelligence.schemas import CapitalDeploymentRequest, OpportunityInput
from ironman.ledger.models import Instrument, InstrumentType, PortfolioStateVersion
from ironman.research.macro_fx import FakeMacroFXModel, MacroFXAgent, MacroFXValidationError, deterministic_macro_fx_facts
from ironman.research.schemas import EvidenceItem, ResearchRequest


def observations():
    return [
        {"observation_id": "rate-1", "factor": "policy_rate", "value": "6.50", "unit": "percent", "currency": "INR", "quality": "VALID", "freshness": "VALID"},
        {"observation_id": "fx-1", "factor": "usd_inr", "value": "83.25", "unit": "INR_per_USD", "currency": "INR", "quality": "VALID", "freshness": "VALID"},
    ]


def agent():
    model = ModelSpec("fake", "macro-fixture", "fixture-v1", "macro_fx", "macro-fx-prompt-v1", {})
    return MacroFXAgent(ModelGateway(ModelRegistry([model]), {"fake": FakeMacroFXModel()}))


def evidence():
    return [EvidenceItem(evidence_id="macro-e1", source="fixture", excerpt="Fixture macro context supplied.", provenance={"source": "fixture"})]


def test_deterministic_macro_facts_preserve_fx_direction():
    facts = deterministic_macro_fx_facts(observations())
    assert facts["status"] == "PASS"
    assert facts["observations"][1]["unit"] == "INR_per_USD"
    assert facts["observations"][1]["value"] == "83.25"


def test_direction_is_not_silently_inverted():
    with pytest.raises(MacroFXValidationError):
        deterministic_macro_fx_facts([{**observations()[1], "unit": "USD_per_INR"}])


def test_stale_and_conflicting_macro_data_fail_closed():
    stale = deterministic_macro_fx_facts([{**observations()[0], "freshness": "STALE"}])
    assert stale["status"] == "INSUFFICIENT"
    conflicting = deterministic_macro_fx_facts([observations()[1], {**observations()[1], "observation_id": "fx-2", "value": "84.10"}])
    assert conflicting["status"] == "CONFLICTING"


def test_macro_agent_returns_structured_interpretation_without_mutation():
    request = ResearchRequest(question="Assess macro context", evidence=evidence(), thesis={"statement": "Stable margins"})
    result = agent().run(request, observations())
    assert result.assessment == "RELEVANT"
    assert result.relevant_macro_factors == ["policy_rate", "usd_inr"]
    assert result.fx_implications[0].startswith("usd_inr is quoted as INR_per_USD")
    assert result.model_provider == "fake"
    assert result.input_evidence_ids == ["macro-e1"]
    assert request.thesis == {"statement": "Stable margins"}


def test_missing_macro_data_abstains():
    result = agent().run(ResearchRequest(question="Assess macro context", evidence=evidence()), [])
    assert result.assessment == "INSUFFICIENT"
    assert result.uncertainty == "HIGH"


def test_orchestrator_selective_macro_invocation_and_persistence(sqlite_session):
    instrument_id = uuid4()
    state = PortfolioStateVersion(id=uuid4(), ledger_boundary=datetime(2026, 1, 1, tzinfo=timezone.utc), boundary_sequence=1, boundary_event_id=uuid4(), calculation_version="phase2", content_hash="macro-state", holdings=[], cash_balances=[{"account_id": "a", "currency": "INR", "amount": "100000"}], tax_lots=[], data_context={}, created_at=datetime.now(timezone.utc))
    instrument = Instrument(id=instrument_id, name="Candidate", instrument_type=InstrumentType.EQUITY, native_currency="INR", created_at=datetime.now(timezone.utc))
    sqlite_session.add_all([state, instrument])
    sqlite_session.flush()
    source = DataSource(provider="fixture", source_identifier="macro-test", licensing={"send_to_ai": False}, adapter_version="1", created_at=datetime.now(timezone.utc))
    sqlite_session.add(source)
    sqlite_session.flush()
    observation = DataObservation(observation_type=ObservationType.PRICE, instrument_id=instrument_id, source_id=source.id, observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc), ingested_at=datetime(2026, 1, 1, 1, tzinfo=timezone.utc), currency="INR", unit="price", value=Decimal("100"), quality=ObservationQuality.VALID, freshness=FreshnessState.VALID, schema_version="1", provenance={"source": "fixture"}, licensing={"send_to_ai": False}, created_at=datetime.now(timezone.utc))
    sqlite_session.add(observation)
    sqlite_session.flush()
    candidate = OpportunityInput(name="Candidate", kind="CANDIDATE", instrument_id=instrument_id, currency="INR", value=Decimal("100"), observation_ids=[observation.id], analytics={"macro_fx_relevant": True, "macro_fx_observations": observations(), "valuation_inputs": {"price": "100", "eps": "10"}}, evidence=[{"evidence_id": "e1", "source": "fixture", "excerpt": "Macro evidence fixture.", "provenance": {"source": "fixture"}}])
    request = CapitalDeploymentRequest(portfolio_state_version_id=state.id, amount=Decimal("1000"), opportunities=[candidate])
    insight = CapitalDeploymentOrchestrator().run(sqlite_session, state, request, "owner")
    assert insight.analytics["macro_fx"]["assessment"] == "RELEVANT"
    assert insight.portfolio_state_version_id == state.id
    assert insight.action in {"ADD", "NO_ACTION"}
