"""Explicit Phase 3O live connectivity validation.

Run with ``pytest -m live``. These tests are excluded from the normal suite.
"""
import os
from datetime import datetime, timezone
from uuid import UUID

import pytest

from ironman.ai.azure_provider import AzureChatModel, AzureModelConfig
from ironman.ai.gateway import ModelGateway, ModelRegistry, ModelSpec
from ironman.data_fabric.models import DataObservation
from ironman.intelligence.analytics import valuation_facts, valuation_inputs_from_observations
from ironman.ledger.models import Instrument, InstrumentType
from ironman.providers.yahoo_finance import YahooFinanceFundamentalAdapter, YahooFinancePriceAdapter
from ironman.research.agent import ResearchEvidenceAgent
from ironman.research.schemas import EvidenceItem, ResearchRequest
from ironman.research.synthesis import SynthesisAgent


pytestmark = [pytest.mark.live, pytest.mark.live_yahoo]

LIVE_SYMBOL = "SPY"
LIVE_CURRENCY = "USD"
APPLICATION_INSTRUMENT_ID = UUID("00000000-0000-0000-0000-0000000003f0")


def _instrument(session) -> Instrument:
    instrument = Instrument(
        id=APPLICATION_INSTRUMENT_ID,
        name="Phase 3O live validation ETF",
        instrument_type=InstrumentType.EQUITY,
        native_currency=LIVE_CURRENCY,
        created_at=datetime.now(timezone.utc),
    )
    session.add(instrument)
    session.flush()
    return instrument


def _azure_gateway() -> ModelGateway:
    config = AzureModelConfig.from_environment()
    deployment = os.getenv("IRONMAN_AZURE_OPENAI_DEPLOYMENT")
    if config is None:
        pytest.skip("Phase 3O Azure live test skipped: endpoint or API key is missing")
    if not deployment:
        pytest.skip("Phase 3O Azure live test skipped: deployment is missing")
    models = [
        ModelSpec(
            "azure",
            deployment,
            os.getenv("IRONMAN_AZURE_MODEL_VERSION", "configured"),
            capability,
            os.getenv("IRONMAN_RESEARCH_PROMPT_VERSION", "research-prompt-v1"),
            {},
        )
        for capability in ("research", "synthesis")
    ]
    return ModelGateway(ModelRegistry(models), {"azure": AzureChatModel(config)})


def test_live_yahoo_price_persists_application_identity(sqlite_session):
    instrument = _instrument(sqlite_session)
    observation = YahooFinancePriceAdapter().fetch_price(
        sqlite_session, instrument.id, LIVE_SYMBOL, LIVE_CURRENCY
    )
    sqlite_session.commit()
    loaded = sqlite_session.get(DataObservation, observation.id)

    assert loaded is not None
    assert loaded.instrument_id == APPLICATION_INSTRUMENT_ID
    assert loaded.provider_observation_id == LIVE_SYMBOL
    assert loaded.value is not None and loaded.value > 0
    assert loaded.currency == LIVE_CURRENCY
    assert loaded.observed_at.tzinfo is not None
    assert loaded.provenance == {"source": "yahoo_finance", "provider_symbol": LIVE_SYMBOL}
    assert loaded.content_hash
    assert loaded.quality == "VALID"
    assert loaded.freshness == "VALID"


def test_live_yahoo_fundamentals_persist_and_feed_deterministic_valuation(sqlite_session):
    instrument = _instrument(sqlite_session)
    observations = YahooFinanceFundamentalAdapter().fetch_fundamentals(
        sqlite_session, instrument.id, LIVE_SYMBOL, LIVE_CURRENCY
    )
    sqlite_session.commit()
    loaded = [sqlite_session.get(DataObservation, observation.id) for observation in observations]
    fields = {observation.values["field"] for observation in loaded}
    inputs = valuation_inputs_from_observations(loaded)
    facts = valuation_facts({"price": "100", **inputs, "currency": LIVE_CURRENCY})

    assert fields
    assert fields <= YahooFinanceFundamentalAdapter.supported_fields
    assert all(observation.instrument_id == APPLICATION_INSTRUMENT_ID for observation in loaded)
    assert all(observation.value is not None for observation in loaded)
    assert all(observation.currency == LIVE_CURRENCY for observation in loaded)
    assert all(observation.observed_at.tzinfo is not None for observation in loaded)
    assert all(observation.provenance["source"] == "yahoo_finance" for observation in loaded)
    assert all(observation.provenance["provider_symbol"] == LIVE_SYMBOL for observation in loaded)
    assert all(observation.content_hash for observation in loaded)
    assert facts["currency"] == LIVE_CURRENCY
    assert facts["status"] in {"PASS", "INSUFFICIENT"}


def test_live_azure_gateway_returns_structured_research_and_telemetry():
    gateway = _azure_gateway()
    evidence = EvidenceItem(
        evidence_id="phase3o-live-evidence",
        source="phase3o-fixture",
        excerpt="The supplied fixture states only that the observed price was retrieved.",
        provenance={"source": "phase3o-fixture"},
    )
    result = ResearchEvidenceAgent(gateway).run(
        ResearchRequest(
            question="Classify the supplied evidence without calculating or recommending execution.",
            evidence=[evidence],
        )
    )
    telemetry = gateway.telemetry[-1]

    assert result.input_evidence_ids == [evidence.evidence_id]
    assert result.model_provider == "azure"
    assert telemetry.status == "SUCCEEDED"
    assert telemetry.latency_ms >= 0
    assert telemetry.model.deployment_id == os.environ["IRONMAN_AZURE_OPENAI_DEPLOYMENT"]
    assert telemetry.model.prompt_version
    assert telemetry.error_category is None
    assert telemetry.input_tokens is None or telemetry.input_tokens >= 0
    assert telemetry.output_tokens is None or telemetry.output_tokens >= 0


@pytest.mark.live_azure
def test_live_end_to_end_synthesis_keeps_deterministic_facts_and_gates(sqlite_session):
    instrument = _instrument(sqlite_session)
    price = YahooFinancePriceAdapter().fetch_price(
        sqlite_session, instrument.id, LIVE_SYMBOL, LIVE_CURRENCY
    )
    fundamentals = YahooFinanceFundamentalAdapter().fetch_fundamentals(
        sqlite_session, instrument.id, LIVE_SYMBOL, LIVE_CURRENCY
    )
    observations = [price, *fundamentals]
    inputs = {"price": str(price.value), **valuation_inputs_from_observations(fundamentals)}
    deterministic_valuation = valuation_facts({**inputs, "currency": LIVE_CURRENCY})
    evidence = EvidenceItem(
        evidence_id="phase3o-live-market-data",
        source="yahoo_finance",
        observed_at=price.observed_at,
        excerpt="Live Yahoo Finance observations were retrieved for the application-owned instrument.",
        provenance={"source": "yahoo_finance", "provider_symbol": LIVE_SYMBOL},
        content_hash=price.content_hash,
        external_reference=price.raw_reference,
    )
    gateway = _azure_gateway()
    request = ResearchRequest(
        question="Synthesize the supplied observations for human review; deterministic facts and gates are authoritative.",
        instrument_id=APPLICATION_INSTRUMENT_ID,
        portfolio_state_version_id=UUID("00000000-0000-0000-0000-0000000003a0"),
        observations=[{"field": item.values.get("field", "price"), "value": str(item.value)} for item in observations],
        evidence=[evidence],
    )
    research = ResearchEvidenceAgent(gateway).run(request)
    result = SynthesisAgent(gateway).run(
        request,
        portfolio_state_version_id=request.portfolio_state_version_id,
        portfolio_facts={"state_version_id": str(request.portfolio_state_version_id)},
        deterministic_valuation=deterministic_valuation,
        research=research,
        fundamental_thesis=None,
        valuation=None,
        portfolio_risk=None,
        alternatives=[{"name": "WAIT", "kind": "CASH"}],
        gates={"identity": "PASS", "quality": "PASS", "freshness": "PASS", "evidence": "PASS"},
    )

    assert result.input_evidence_ids == [evidence.evidence_id]
    assert result.model_provider == "azure"
    assert result.model_version
    assert deterministic_valuation["calculation_version"] == "valuation-v1"