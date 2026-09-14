"""Read-only Kite market-data mapping into the provider-independent data fabric."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from uuid import UUID

from ironman.data_fabric.models import (
    DataObservation,
    DataSource,
    FreshnessState,
    ObservationQuality,
    ObservationType,
)
from ironman.data_fabric.service import persist_observation, persist_source


class KiteAdapterError(RuntimeError):
    def __init__(self, category: str, message: str) -> None:
        super().__init__(message)
        self.category = category


class KiteReadOnlyMarketDataAdapter:
    """Map a read-only Kite quote; this class has no broker-write operations."""

    provider = "kite"
    adapter_version = "kite-quote-v1"

    def fetch_quote(
        self,
        session,
        instrument_id: UUID,
        provider_symbol: str,
        currency: str,
        quote: dict,
    ) -> DataObservation:
        if not instrument_id or not provider_symbol or len(currency) != 3:
            raise KiteAdapterError("identity", "canonical identity, provider symbol, and currency are required")
        observation = self.parse_quote(quote, instrument_id, provider_symbol, currency)
        source = session.query(DataSource).filter_by(provider=self.provider, source_identifier="quote").first()
        if source is None:
            source = persist_source(
                session,
                DataSource(
                    provider=self.provider,
                    source_identifier="quote",
                    licensing={"send_to_ai": False},
                    adapter_version=self.adapter_version,
                    created_at=datetime.now(timezone.utc),
                ),
            )
        observation.source_id = source.id
        return persist_observation(session, observation)

    def parse_quote(self, quote: dict, instrument_id: UUID, provider_symbol: str, currency: str) -> DataObservation:
        try:
            price = self._decimal(quote["last_price"], "last_price")
            ohlc = quote["ohlc"]
            open_price = self._decimal(ohlc["open"], "open")
            high = self._decimal(ohlc["high"], "high")
            low = self._decimal(ohlc["low"], "low")
            close = self._decimal(ohlc["close"], "close")
            token = int(quote["instrument_token"])
        except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
            raise KiteAdapterError("malformed_response", "Kite quote lacks valid LTP, OHLC, or instrument token") from exc
        if any(value < 0 for value in (price, open_price, high, low, close)) or token <= 0:
            raise KiteAdapterError("invalid_numeric", "Kite quote contains a negative value or invalid instrument token")

        observed_at, timestamp_quality = self._trusted_trade_time(quote)
        ingested_at = datetime.now(timezone.utc)
        payload = {"provider_symbol": provider_symbol, "quote": quote}
        content_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
        return DataObservation(
            observation_type=ObservationType.PRICE,
            instrument_id=instrument_id,
            source_id=UUID(int=0),
            provider_observation_id=provider_symbol,
            observed_at=observed_at,
            ingested_at=ingested_at,
            currency=currency,
            unit="price",
            value=price,
            values={
                "ltp": str(price),
                "ohlc": {"open": str(open_price), "high": str(high), "low": str(low), "close": str(close)},
                "instrument_token": token,
                "timestamp_quality": timestamp_quality,
            },
            quality=ObservationQuality.VALID,
            freshness=FreshnessState.VALID if observed_at is not None else FreshnessState.INSUFFICIENT,
            raw_reference=f"kite://quote/{provider_symbol}",
            content_hash=content_hash,
            schema_version=self.adapter_version,
            provenance={
                "source": self.provider,
                "provider_symbol": provider_symbol,
                "provider_instrument_token": token,
                "provider_timestamp": quote.get("timestamp"),
                "provider_last_trade_time": quote.get("last_trade_time"),
                "timestamp_quality": timestamp_quality,
            },
            licensing={"send_to_ai": False},
            created_at=ingested_at,
        )

    @staticmethod
    def _decimal(value, field: str) -> Decimal:
        try:
            result = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise KiteAdapterError("invalid_numeric", f"Kite {field} is not numeric") from exc
        if not result.is_finite():
            raise KiteAdapterError("invalid_numeric", f"Kite {field} is not finite")
        return result

    @staticmethod
    def _trusted_trade_time(quote: dict) -> tuple[datetime | None, str]:
        raw = quote.get("last_trade_time")
        if not raw or raw in {"0001-01-01T00:00:00Z", "1970-01-01T00:00:00+05:30"}:
            return None, "UNTRUSTED_OR_MISSING"
        try:
            parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except ValueError:
            return None, "INVALID"
        if parsed.tzinfo is None:
            return None, "INVALID"
        return parsed.astimezone(timezone.utc), "TRUSTED_LAST_TRADE_TIME"