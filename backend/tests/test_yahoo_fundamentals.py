from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from ironman.intelligence.analytics import valuation_facts, valuation_inputs_from_observations
from ironman.ledger.models import Instrument, InstrumentType
from ironman.providers.yahoo_finance import ProviderAdapterError, YahooFinanceFundamentalAdapter
from ironman.data_fabric.models import DataObservation


def fundamental_payload(**overrides):
    values = {
        "trailingEps": {"raw": 10.25}, "bookValue": {"raw": 50.5}, "ebitda": {"raw": 1000},
        "enterpriseValue": {"raw": 10000}, "marketCap": {"raw": 9000}, "freeCashflow": {"raw": 450},
    }
    values.update(overrides)
    provider_currency = overrides.pop("currency", None)
    result = {"financialData": values, "defaultKeyStatistics": {}, "summaryDetail": {}}
    if provider_currency:
        result["currency"] = provider_currency
    return {"quoteSummary": {"result": [result]}}


def instrument(session, currency="USD"):
    item = Instrument(id=uuid4(), name="Fixture", instrument_type=InstrumentType.EQUITY, native_currency=currency, created_at=datetime.now(timezone.utc))
    session.add(item)
    session.flush()
    return item


def adapter(payload=None):
    return YahooFinanceFundamentalAdapter(http_get=lambda symbol: payload or fundamental_payload())


def test_valid_fundamentals_map_all_supported_fields_and_persist(sqlite_session):
    item = instrument(sqlite_session)
    observations = adapter().fetch_fundamentals(sqlite_session, item.id, "FIX", "USD")
    sqlite_session.commit()
    assert {observation.values["field"] for observation in observations} == {"eps", "book_value_per_share", "ebitda", "enterprise_value", "market_cap", "free_cash_flow"}
    assert all(observation.instrument_id == item.id and observation.currency == "USD" for observation in observations)
    assert all(observation.content_hash and observation.provenance["source"] == "yahoo_finance" for observation in observations)
    assert valuation_inputs_from_observations(observations)["eps"] == "10.25"


def test_fundamental_precision_and_valuation_consumption(sqlite_session):
    item = instrument(sqlite_session)
    observations = adapter(fundamental_payload(trailingEps={"raw": "10.123456789012"})).fetch_fundamentals(sqlite_session, item.id, "FIX", "USD")
    inputs = valuation_inputs_from_observations(observations)
    facts = valuation_facts({"price": "100", **inputs, "currency": "USD"})
    assert inputs["eps"] == "10.123456789012"
    assert facts["methods"]["pe"] == str(Decimal("100") / Decimal("10.123456789012"))


def test_missing_malformed_invalid_and_currency_failures(sqlite_session):
    item = instrument(sqlite_session)
    with pytest.raises(ProviderAdapterError):
        adapter({"quoteSummary": {"result": []}}).fetch_fundamentals(sqlite_session, item.id, "FIX", "USD")
    with pytest.raises(ProviderAdapterError):
        adapter(fundamental_payload(ebitda={"raw": "bad"})).fetch_fundamentals(sqlite_session, item.id, "FIX", "USD")
    with pytest.raises(ProviderAdapterError):
        adapter(fundamental_payload(ebitda={"raw": -1})).fetch_fundamentals(sqlite_session, item.id, "FIX", "USD")
    with pytest.raises(ProviderAdapterError):
        adapter(fundamental_payload(currency="USD")).fetch_fundamentals(sqlite_session, item.id, "FIX", "INR")


def test_no_supported_fields_and_identity_failure(sqlite_session):
    item = instrument(sqlite_session)
    with pytest.raises(ProviderAdapterError):
        adapter(fundamental_payload(**{key: None for key in ("trailingEps", "bookValue", "ebitda", "enterpriseValue", "marketCap", "freeCashflow")})).fetch_fundamentals(sqlite_session, item.id, "FIX", "USD")
    with pytest.raises(ProviderAdapterError):
        adapter().fetch_fundamentals(sqlite_session, None, "FIX", "USD")
