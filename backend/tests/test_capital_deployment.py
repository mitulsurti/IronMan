from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from ironman.intelligence.models import OpportunityKind
from ironman.data_fabric.models import DataObservation, DataSource, FreshnessState, ObservationQuality, ObservationType
from ironman.ledger.models import Instrument, InstrumentType, PortfolioStateVersion
from ironman.intelligence.orchestrator import CapitalDeploymentOrchestrator
from ironman.intelligence.schemas import CapitalDeploymentRequest, OpportunityInput


def state_version():
    return PortfolioStateVersion(
        id=uuid4(), ledger_boundary=datetime(2026, 1, 1, tzinfo=timezone.utc), boundary_sequence=1,
        boundary_event_id=uuid4(), calculation_version="phase2", content_hash="valid",
        holdings=[], cash_balances=[{"account_id": "a", "currency": "INR", "amount": "100000"}],
        tax_lots=[], data_context={}, created_at=datetime.now(timezone.utc),
    )


def opportunity(name="Candidate", **kwargs):
    return OpportunityInput(name=name, kind=OpportunityKind.CANDIDATE, instrument_id=uuid4(), currency="INR", evidence=[{"source": "fixture", "claim": "supported"}], **kwargs)


def persist_instrument(session, item):
    session.add(Instrument(id=item.instrument_id, name=item.name, instrument_type=InstrumentType.EQUITY, native_currency=item.currency, created_at=datetime.now(timezone.utc)))
    session.flush()
    source = DataSource(provider="fixture", source_identifier="capital-deployment", licensing={"send_to_ai": True}, adapter_version="1", created_at=datetime.now(timezone.utc))
    session.add(source)
    session.flush()
    observation = DataObservation(observation_type=ObservationType.PRICE, instrument_id=item.instrument_id, source_id=source.id, observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc), ingested_at=datetime(2026, 1, 1, 1, tzinfo=timezone.utc), currency=item.currency, unit="price", value=Decimal("100"), quality=ObservationQuality.VALID, freshness=FreshnessState.VALID, schema_version="1", provenance={"source": "fixture"}, licensing={"send_to_ai": True}, created_at=datetime.now(timezone.utc))
    session.add(observation)
    session.flush()
    item.observation_ids = [observation.id]
    return item


def request(state, *opportunities, **kwargs):
    return CapitalDeploymentRequest(portfolio_state_version_id=state.id, amount=Decimal("10000"), opportunities=list(opportunities), **kwargs)


def test_valid_capital_deployment_persists_insight(sqlite_session):
    state = state_version()
    sqlite_session.add(state)
    sqlite_session.flush()
    candidate = persist_instrument(sqlite_session, opportunity())
    candidate.evidence = [{"evidence_id": "e1", "source": "fixture", "excerpt": "Revenue increased", "provenance": {"source": "fixture"}}]
    insight = CapitalDeploymentOrchestrator().run(sqlite_session, state, request(state, candidate), "owner")
    sqlite_session.commit()
    assert insight.action == "ADD"
    assert insight.portfolio_state_version_id == state.id
    assert insight.evidence
    assert insight.gates["quality"] == "PASS"
    assert insight.analytics["research"]["model_version"] == "fixture-v1"


def test_capital_deployment_consumes_fundamental_thesis_result(sqlite_session):
    state = state_version()
    sqlite_session.add(state)
    sqlite_session.flush()
    candidate = persist_instrument(sqlite_session, opportunity())
    candidate.analytics["thesis"] = {"statement": "The business compounds earnings", "assumptions": ["growth remains strong"]}
    candidate.evidence = [{"evidence_id": "e1", "source": "filing", "excerpt": "Revenue growth improved strongly", "provenance": {"source": "fixture"}}]
    insight = CapitalDeploymentOrchestrator().run(sqlite_session, state, request(state, candidate), "owner")
    assert insight.analytics["fundamental_thesis"]["thesis_impacts"] == ["STRENGTHENS"]


def test_capital_deployment_consumes_deterministic_valuation_and_agent_result(sqlite_session):
    state = state_version()
    sqlite_session.add(state)
    sqlite_session.flush()
    candidate = persist_instrument(sqlite_session, opportunity())
    candidate.analytics["valuation_inputs"] = {"price": "100", "eps": "10"}
    candidate.analytics["valuation_assumptions"] = {"reference_assessment": "REASONABLE"}
    candidate.evidence = [{"evidence_id": "e1", "source": "filing", "excerpt": "Reference supports supplied valuation", "provenance": {"source": "fixture"}}]
    insight = CapitalDeploymentOrchestrator().run(sqlite_session, state, request(state, candidate), "owner")
    assert insight.analytics["deterministic_valuation"]["methods"]["pe"] == "10"
    assert "REASONABLE" in insight.analytics["valuation"]["conclusion"]
    assert insight.analytics["portfolio_risk"]["model_version"] == "fixture-v1"
    assert insight.analytics["synthesis"]["model_version"] == "fixture-v1"


def test_stale_candidate_produces_no_action(sqlite_session):
    state = state_version()
    sqlite_session.add(state)
    sqlite_session.flush()
    insight = CapitalDeploymentOrchestrator().run(sqlite_session, state, request(state, persist_instrument(sqlite_session, opportunity(freshness_state="STALE"))), "owner")
    assert insight.action == "NO_ACTION"
    assert "freshness" in insight.abstention_reason


def test_concentration_gate_blocks_candidate(sqlite_session):
    state = state_version()
    sqlite_session.add(state)
    sqlite_session.flush()
    insight = CapitalDeploymentOrchestrator().run(sqlite_session, state, request(state, persist_instrument(sqlite_session, opportunity(portfolio_weight=Decimal("0.95"))), max_concentration=Decimal("0.10")), "owner")
    assert insight.action == "NO_ACTION"
    assert insight.gates["concentration"] == "BLOCKED"


def test_cash_alternative_waits_and_preserves_alternatives(sqlite_session):
    state = state_version()
    sqlite_session.add(state)
    sqlite_session.flush()
    insight = CapitalDeploymentOrchestrator().run(sqlite_session, state, request(state, OpportunityInput(name="Cash", kind=OpportunityKind.CASH, currency="INR", evidence=[{"source": "fixture"}])), "owner")
    assert insight.action == "WAIT"
    assert insight.alternatives
