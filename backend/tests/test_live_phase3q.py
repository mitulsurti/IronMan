"""Phase 3Q: live-captured Kite price through the real Azure synthesis path.

The Kite MCP is external to the Python process. The quote below is captured from
the read-only MCP immediately before this validation and is deliberately passed
through KiteReadOnlyMarketDataAdapter; no raw quote is passed to intelligence.
"""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import os
import pytest

from ironman.ai.azure_provider import AzureChatModel, AzureModelConfig
from ironman.ai.gateway import ModelGateway, ModelRegistry, ModelSpec
from ironman.data_fabric.models import DataObservation, DataSource
from ironman.intelligence.models import StructuredInsight
from ironman.intelligence.orchestrator import CapitalDeploymentOrchestrator
from ironman.intelligence.schemas import CapitalDeploymentRequest, OpportunityInput
from ironman.ledger.models import Instrument, InstrumentType, PortfolioStateVersion
from ironman.providers.kite import KiteReadOnlyMarketDataAdapter


pytestmark = pytest.mark.live

APPLICATION_INSTRUMENT_ID = uuid4()
LIVE_KITE_SYMBOL = "NSE:RELIANCE"
LIVE_KITE_QUOTE = {
    "instrument_token": 738561,
    "timestamp": "1970-01-01T05:30:00+05:30",
    "last_price": "1257.5",
    "last_trade_time": "2026-09-11T15:58:29+05:30",
    "ohlc": {"open": "1267", "high": "1267.4", "low": "1253", "close": "1257.5"},
}


def _azure_synthesis_gateway() -> ModelGateway:
    config = AzureModelConfig.from_environment()
    deployment = os.getenv("IRONMAN_AZURE_OPENAI_DEPLOYMENT")
    if config is None:
        pytest.skip("Phase 3Q skipped: Azure endpoint or API key is missing")
    if not deployment:
        pytest.skip("Phase 3Q skipped: Azure deployment is missing")
    model = ModelSpec(
        "azure",
        deployment,
        os.getenv("IRONMAN_AZURE_MODEL_VERSION", "configured"),
        "synthesis",
        os.getenv("IRONMAN_RESEARCH_PROMPT_VERSION", "research-prompt-v1"),
        {},
    )
    return ModelGateway(ModelRegistry([model]), {"azure": AzureChatModel(config)})


def test_live_kite_to_real_azure_structured_insight(sqlite_session):
    instrument = Instrument(
        id=APPLICATION_INSTRUMENT_ID,
        name="Reliance Industries",
        instrument_type=InstrumentType.EQUITY,
        native_currency="INR",
        created_at=datetime.now(timezone.utc),
    )
    sqlite_session.add(instrument)
    sqlite_session.flush()

    observation = KiteReadOnlyMarketDataAdapter().fetch_quote(
        sqlite_session, instrument.id, LIVE_KITE_SYMBOL, "INR", LIVE_KITE_QUOTE
    )
    state = PortfolioStateVersion(
        id=uuid4(),
        ledger_boundary=datetime(2026, 9, 1, tzinfo=timezone.utc),
        boundary_sequence=1,
        boundary_event_id=uuid4(),
        calculation_version="phase2-ledger-v1",
        policy_version="fixture-policy-v1",
        data_context={"source": "phase3q-live-kite"},
        holdings=[],
        cash_balances=[{"account_id": "fixture-account", "currency": "INR", "amount": "100000"}],
        tax_lots=[],
        content_hash="phase3q-live-state",
        created_at=datetime.now(timezone.utc),
    )
    sqlite_session.add(state)
    sqlite_session.flush()

    # Fundamentals and evidence are intentionally offline fixtures.
    candidate = OpportunityInput(
        name="Reliance Industries",
        kind="CANDIDATE",
        instrument_id=instrument.id,
        currency="INR",
        value=observation.value,
        quality_state="PASS",
        freshness_state="PASS",
        observation_ids=[observation.id],
        portfolio_weight=Decimal("0"),
        analytics={
            "current_price": str(observation.value),
            "valuation_inputs": {"price": str(observation.value), "eps": "100", "book_value_per_share": "900"},
            "valuation_assumptions": {"reference_assessment": "REASONABLE"},
            "thesis": {"statement": "The business remains financially resilient."},
        },
        evidence=[{
            "evidence_id": "phase3q-fixture-evidence",
            "source": "offline-fixture",
            "excerpt": "Offline fixture evidence states that operating performance improved.",
            "provenance": {"source": "offline-fixture"},
        }],
    )
    request = CapitalDeploymentRequest(
        portfolio_state_version_id=state.id,
        amount=Decimal("10000"),
        currency="INR",
        horizon="CORE",
        max_concentration=Decimal("0.50"),
        opportunities=[candidate],
    )
    gateway = _azure_synthesis_gateway()
    insight = CapitalDeploymentOrchestrator(synthesis_gateway=gateway).run(
        sqlite_session, state, request, "phase3q-live-test"
    )
    sqlite_session.commit()
    persisted_observation = sqlite_session.get(DataObservation, observation.id)
    persisted_insight = sqlite_session.get(StructuredInsight, insight.id)

    assert persisted_observation is not None
    assert persisted_observation.provider_observation_id == LIVE_KITE_SYMBOL
    assert persisted_observation.instrument_id == APPLICATION_INSTRUMENT_ID
    assert persisted_observation.value == Decimal("1257.5")
    assert persisted_observation.provenance["provider_instrument_token"] == 738561
    assert persisted_observation.values["timestamp_quality"] == "TRUSTED_LAST_TRADE_TIME"
    assert persisted_insight is not None
    assert persisted_insight.portfolio_state_version_id == state.id
    assert persisted_insight.instrument_id == APPLICATION_INSTRUMENT_ID
    assert persisted_insight.analytics["deterministic_valuation"]["methods"]["pe"] == "12.575"
    assert persisted_insight.analytics["synthesis"]["model_provider"] == "azure"
    assert persisted_insight.analytics["synthesis"]["input_evidence_ids"] == ["phase3q-fixture-evidence"]
    assert persisted_insight.gates["observations"] == "PASS"
    assert gateway.telemetry and gateway.telemetry[-1].status == "SUCCEEDED"
    assert gateway.telemetry[-1].latency_ms >= 0
    assert gateway.telemetry[-1].input_tokens is None or gateway.telemetry[-1].input_tokens >= 0
    assert gateway.telemetry[-1].output_tokens is None or gateway.telemetry[-1].output_tokens >= 0