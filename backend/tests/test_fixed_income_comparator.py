from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from ironman.ai.gateway import ModelGateway, ModelRegistry, ModelSpec
from ironman.data_fabric.models import DataObservation, DataSource, FreshnessState, ObservationQuality, ObservationType
from ironman.intelligence.orchestrator import CapitalDeploymentOrchestrator
from ironman.intelligence.schemas import CapitalDeploymentRequest, OpportunityInput
from ironman.ledger.models import Instrument, InstrumentType, PortfolioStateVersion
from ironman.research.fixed_income import FakeFixedIncomeComparatorModel, FixedIncomeComparatorAgent, FixedIncomeComparisonError, deterministic_fixed_income_facts
from ironman.research.schemas import EvidenceItem, ResearchRequest


def gsec():
    return {"instrument_id": str(uuid4()), "instrument_type": "G_SEC", "currency": "INR", "maturity_date": "2030-01-01", "face_amount": "100000", "settlement_amount": "98500", "clean_price": "98000", "accrued_interest": "500", "coupon_rate": "7.18", "cash_flows": [{"date": "2027-01-01", "amount": "7180", "currency": "INR"}, {"date": "2030-01-01", "amount": "107180", "currency": "INR"}], "yield_metric": {"name": "yield_to_maturity", "value": "7.75", "unit": "percent",}, "credit_quality": "sovereign", "liquidity": "HIGH", "portfolio_role": "capital_preservation", "quality": "VALID", "freshness": "VALID", "provenance": {"source": "fixture"}}


def tbill():
    item = gsec()
    item.update({"instrument_type": "T_BILL", "maturity_date": "2027-01-01", "cash_flows": [{"date": "2027-01-01", "amount": "100000", "currency": "INR"}], "yield_metric": {"name": "discount_yield", "value": "6.8", "unit": "percent"}, "credit_quality": "sovereign"})
    return item


def corporate():
    item = gsec()
    item.update({"instrument_type": "NCD", "issuer": "Example Corp", "credit_quality": "AA", "liquidity": "MEDIUM", "tax_treatment": "taxable"})
    return item


def agent():
    model = ModelSpec("fake", "fixed-income-fixture", "fixture-v1", "fixed_income_comparator", "fixed-income-prompt-v1", {})
    return FixedIncomeComparatorAgent(ModelGateway(ModelRegistry([model]), {"fake": FakeFixedIncomeComparatorModel()}))


def evidence():
    return [EvidenceItem(evidence_id="fi-e1", source="fixture", excerpt="Fixed-income terms were supplied by the application fixture.", provenance={"source": "fixture"})]


def test_gsec_deterministic_cashflows_and_settlement():
    facts = deterministic_fixed_income_facts(gsec())
    assert facts["status"] == "PASS"
    assert facts["cash_flow_total"] == "114360"
    assert facts["settlement_amount"] == "98500"
    assert facts["yield_metric"]["value"] == "7.75"


def test_tbill_and_corporate_bond_terms():
    assert deterministic_fixed_income_facts(tbill())["instrument_type"] == "T_BILL"
    facts = deterministic_fixed_income_facts(corporate())
    assert facts["credit_quality"] == "AA"
    assert facts["issuer"] == "Example Corp"
    assert facts["tax_treatment"] == "taxable"


def test_comparator_output_has_explicit_dimensions_and_no_score_or_allocation():
    result = agent().run(ResearchRequest(question="Compare", evidence=evidence()), gsec(), {"name": "cash", "kind": "CASH", "currency": "INR"})
    assert result.assessment == "COMPARABLE"
    assert "114360" in result.cash_flow_interpretation
    assert result.currency_interpretation.endswith("no conversion was applied.")
    assert result.opportunity_cost_interpretation
    assert not hasattr(result, "score")
    assert not hasattr(result, "allocation")
    assert result.input_evidence_ids == ["fi-e1"]


def test_missing_cashflows_and_conflicting_terms_abstain():
    missing = gsec()
    missing["cash_flows"] = []
    assert agent().run(ResearchRequest(question="Compare", evidence=evidence()), missing).assessment == "INSUFFICIENT"
    conflicting = {**gsec(), "settlement_amount": "99000"}
    assert agent().run(ResearchRequest(question="Compare", evidence=evidence()), conflicting).assessment == "INSUFFICIENT"


def test_missing_maturity_invalid_currency_and_stale_fail_closed():
    missing = {**gsec(), "maturity_date": None}
    with pytest.raises(FixedIncomeComparisonError):
        deterministic_fixed_income_facts(missing)
    with pytest.raises(FixedIncomeComparisonError):
        deterministic_fixed_income_facts({**gsec(), "currency": "US"})
    stale = {**gsec(), "freshness": "STALE"}
    assert agent().run(ResearchRequest(question="Compare", evidence=evidence()), stale).uncertainty == "HIGH"


def test_orchestrator_selectively_persists_comparison(sqlite_session):
    instrument_id = uuid4()
    state = PortfolioStateVersion(id=uuid4(), ledger_boundary=datetime(2026, 1, 1, tzinfo=timezone.utc), boundary_sequence=1, boundary_event_id=uuid4(), calculation_version="phase2", content_hash="fi-state", holdings=[], cash_balances=[{"account_id": "a", "currency": "INR", "amount": "100000"}], tax_lots=[], data_context={}, created_at=datetime.now(timezone.utc))
    instrument = Instrument(id=instrument_id, name="Equity alternative", instrument_type=InstrumentType.EQUITY, native_currency="INR", created_at=datetime.now(timezone.utc))
    sqlite_session.add_all([state, instrument])
    sqlite_session.flush()
    source = DataSource(provider="fixture", source_identifier="fi-test", licensing={"send_to_ai": False}, adapter_version="1", created_at=datetime.now(timezone.utc))
    sqlite_session.add(source)
    sqlite_session.flush()
    observation = DataObservation(observation_type=ObservationType.PRICE, instrument_id=instrument_id, source_id=source.id, observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc), ingested_at=datetime(2026, 1, 1, 1, tzinfo=timezone.utc), currency="INR", unit="price", value=Decimal("100"), quality=ObservationQuality.VALID, freshness=FreshnessState.VALID, schema_version="1", provenance={"source": "fixture"}, licensing={"send_to_ai": False}, created_at=datetime.now(timezone.utc))
    sqlite_session.add(observation)
    sqlite_session.flush()
    candidate = OpportunityInput(name="Equity", kind="CANDIDATE", instrument_id=instrument_id, currency="INR", value=Decimal("100"), observation_ids=[observation.id], analytics={"fixed_income_relevant": True, "fixed_income_facts": gsec(), "fixed_income_alternative": {"name": "Equity opportunity", "kind": "CANDIDATE", "currency": "INR"}}, evidence=[{"evidence_id": "fi-e1", "source": "fixture", "excerpt": "Comparison evidence.", "provenance": {"source": "fixture"}}])
    request = CapitalDeploymentRequest(portfolio_state_version_id=state.id, amount=Decimal("1000"), opportunities=[candidate])
    insight = CapitalDeploymentOrchestrator().run(sqlite_session, state, request, "owner")
    assert insight.analytics["fixed_income_comparison"]["assessment"] == "COMPARABLE"
    assert insight.portfolio_state_version_id == state.id
    assert insight.action in {"ADD", "NO_ACTION"}
