from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from ironman.data_fabric.models import DataObservation
from ironman.ledger.models import Instrument, InstrumentType
from ironman.providers.kite import KiteAdapterError, KiteReadOnlyMarketDataAdapter


APPLICATION_INSTRUMENT_ID = uuid4()


def quote(symbol="NIFTY 50", token=256265, last_trade_time="0001-01-01T00:00:00Z"):
    return {
        "instrument_token": token,
        "timestamp": "1970-01-01T05:30:00+05:30",
        "last_price": "23398.10" if symbol == "NIFTY 50" else "1257.50",
        "last_trade_time": last_trade_time,
        "ohlc": {"open": "23270.30", "high": "23448.10", "low": "23231.40", "close": "23398.10"}
        if symbol == "NIFTY 50"
        else {"open": "1267.00", "high": "1267.40", "low": "1253.00", "close": "1257.50"},
    }


def instrument(session):
    item = Instrument(
        id=APPLICATION_INSTRUMENT_ID,
        name="Application instrument",
        instrument_type=InstrumentType.EQUITY,
        native_currency="INR",
        created_at=datetime.now(timezone.utc),
    )
    session.add(item)
    session.flush()
    return item


def test_nifty_quote_maps_decimal_values_and_untrusted_timestamp(sqlite_session):
    item = instrument(sqlite_session)
    observation = KiteReadOnlyMarketDataAdapter().fetch_quote(
        sqlite_session, item.id, "NSE:NIFTY 50", "INR", quote()
    )

    assert observation.instrument_id == APPLICATION_INSTRUMENT_ID
    assert observation.provider_observation_id == "NSE:NIFTY 50"
    assert observation.value == Decimal("23398.10")
    assert observation.currency == "INR"
    assert observation.unit == "price"
    assert observation.observed_at is None
    assert observation.ingested_at.tzinfo is not None
    assert observation.values["instrument_token"] == 256265
    assert observation.values["ohlc"]["high"] == "23448.10"
    assert observation.values["timestamp_quality"] == "UNTRUSTED_OR_MISSING"
    assert observation.provenance["provider_instrument_token"] == 256265


def test_reliance_last_trade_time_is_distinct_and_trusted(sqlite_session):
    item = instrument(sqlite_session)
    observation = KiteReadOnlyMarketDataAdapter().fetch_quote(
        sqlite_session,
        item.id,
        "NSE:RELIANCE",
        "INR",
        quote("RELIANCE", 738561, "2026-09-11T15:58:29+05:30"),
    )
    sqlite_session.commit()
    loaded = sqlite_session.get(DataObservation, observation.id)

    assert loaded.instrument_id == item.id
    assert loaded.provider_observation_id == "NSE:RELIANCE"
    assert loaded.value == Decimal("1257.50")
    assert loaded.observed_at == datetime(2026, 9, 11, 10, 28, 29, tzinfo=timezone.utc)
    assert loaded.ingested_at > loaded.observed_at
    assert loaded.values["timestamp_quality"] == "TRUSTED_LAST_TRADE_TIME"
    assert loaded.provenance["provider_last_trade_time"] == "2026-09-11T15:58:29+05:30"
    assert loaded.content_hash


def test_provider_identity_is_not_canonical_identity(sqlite_session):
    item = instrument(sqlite_session)
    observation = KiteReadOnlyMarketDataAdapter().parse_quote(
        quote(), item.id, "NSE:DIFFERENT", "INR"
    )
    assert observation.instrument_id == item.id
    assert observation.provider_observation_id == "NSE:DIFFERENT"


def test_malformed_missing_and_invalid_quotes_fail_closed(sqlite_session):
    item = instrument(sqlite_session)
    adapter = KiteReadOnlyMarketDataAdapter()
    for bad in ({}, {"last_price": "1", "ohlc": {}}, {**quote(), "last_price": "bad"}, {**quote(), "instrument_token": 0}):
        with pytest.raises(KiteAdapterError):
            adapter.fetch_quote(sqlite_session, item.id, "NSE:NIFTY 50", "INR", bad)


def test_identity_and_currency_validation(sqlite_session):
    adapter = KiteReadOnlyMarketDataAdapter()
    with pytest.raises(KiteAdapterError):
        adapter.fetch_quote(sqlite_session, None, "NSE:NIFTY 50", "INR", quote())
    item = instrument(sqlite_session)
    with pytest.raises(KiteAdapterError):
        adapter.fetch_quote(sqlite_session, item.id, "NSE:NIFTY 50", "", quote())


def test_read_only_adapter_exposes_no_broker_write_methods():
    methods = dir(KiteReadOnlyMarketDataAdapter)
    assert not any(name.startswith(("place_", "modify_", "cancel_", "delete_", "transfer_", "withdraw_")) for name in methods)
