from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from ironman.providers.yahoo_finance import CanonicalInstrumentMappingError, ProviderAdapterError, YahooFinancePriceAdapter
from ironman.data_fabric.models import DataObservation
from ironman.ledger.models import Instrument, InstrumentType


def payload(price=123.45, timestamp=1770000000, currency="USD"):
    return {"chart": {"result": [{"meta": {"regularMarketPrice": price, "regularMarketTime": timestamp, "currency": currency}}]}}


def instrument(session, currency="USD"):
    item = Instrument(id=uuid4(), name="Fixture ETF", instrument_type=InstrumentType.EQUITY, native_currency=currency, created_at=datetime.now(timezone.utc))
    session.add(item)
    session.flush()
    return item


def adapter(payload_value=None):
    return YahooFinancePriceAdapter(http_get=lambda symbol: payload_value if payload_value is not None else payload())


def test_valid_response_maps_to_canonical_observation_and_persists(sqlite_session):
    item = instrument(sqlite_session)
    observation = adapter().fetch_price(sqlite_session, item.id, "SPY", "USD")
    sqlite_session.commit()
    loaded = sqlite_session.get(DataObservation, observation.id)
    assert loaded.instrument_id == item.id
    assert loaded.provider_observation_id == "SPY"
    assert loaded.value == Decimal("123.45")
    assert loaded.currency == "USD"
    assert loaded.provenance["source"] == "yahoo_finance"
    assert loaded.content_hash


def test_provider_symbol_does_not_define_canonical_identity(sqlite_session):
    item = instrument(sqlite_session)
    observation = adapter().fetch_price(sqlite_session, item.id, "DIFFERENT-SYMBOL", "USD")
    assert observation.instrument_id == item.id
    assert observation.provider_observation_id == "DIFFERENT-SYMBOL"


def test_mapping_failure_and_currency_mismatch(sqlite_session):
    with pytest.raises(CanonicalInstrumentMappingError):
        adapter().fetch_price(sqlite_session, None, "SPY", "USD")
    item = instrument(sqlite_session)
    with pytest.raises(ProviderAdapterError, match="currency"):
        adapter().fetch_price(sqlite_session, item.id, "SPY", "INR")


def test_malformed_missing_and_invalid_numeric_responses(sqlite_session):
    item = instrument(sqlite_session)
    for bad in ({}, {"chart": {"result": []}}, payload(price="bad"), payload(price=-1)):
        with pytest.raises(ProviderAdapterError):
            adapter(bad).fetch_price(sqlite_session, item.id, "SPY", "USD")


def test_provider_failure_is_not_fabricated(sqlite_session):
    item = instrument(sqlite_session)
    def fail(symbol):
        raise ProviderAdapterError("network_or_timeout", "timeout")
    with pytest.raises(ProviderAdapterError):
        YahooFinancePriceAdapter(http_get=fail).fetch_price(sqlite_session, item.id, "SPY", "USD")


def test_decimal_precision_and_timestamp(sqlite_session):
    item = instrument(sqlite_session)
    observation = adapter(payload(price="123.456789012345", timestamp=1770000000)).fetch_price(sqlite_session, item.id, "SPY", "USD")
    assert observation.value == Decimal("123.456789012345")
    assert observation.observed_at.tzinfo is not None
    assert observation.freshness == "VALID"
