from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID

from ironman.data_fabric.models import DataObservation, DataSource, FreshnessState, ObservationQuality, ObservationType
from ironman.data_fabric.service import ObservationValidationError, persist_observation, persist_source


class ProviderAdapterError(RuntimeError):
    def __init__(self, category: str, message: str) -> None:
        super().__init__(message)
        self.category = category


class CanonicalInstrumentMappingError(ProviderAdapterError):
    pass


class YahooFinancePriceAdapter:
    """Narrow Yahoo Finance chart endpoint adapter for current equity/ETF prices."""

    provider = "yahoo_finance"
    adapter_version = "yahoo-chart-v1"

    def __init__(self, http_get=None, timeout_seconds: float = 10.0) -> None:
        self.http_get = http_get or self._http_get
        self.timeout_seconds = timeout_seconds

    def fetch_price(self, session, instrument_id: UUID, provider_symbol: str, currency: str) -> DataObservation:
        if not provider_symbol or not instrument_id or len(currency) != 3:
            raise CanonicalInstrumentMappingError("identity", "identity and currency are required")
        payload = self.http_get(provider_symbol)
        observation = self.parse_price(payload, instrument_id, provider_symbol, currency)
        source = session.query(DataSource).filter_by(provider=self.provider, source_identifier="chart").first()
        if source is None:
            source = persist_source(session, DataSource(provider=self.provider, source_identifier="chart", licensing={"send_to_ai": False}, adapter_version=self.adapter_version, created_at=datetime.now(timezone.utc)))
        observation.source_id = source.id
        return persist_observation(session, observation)

    def parse_price(self, payload: dict, instrument_id: UUID, provider_symbol: str, currency: str) -> DataObservation:
        try:
            result = payload["chart"]["result"][0]
            meta = result["meta"]
            timestamp = datetime.fromtimestamp(int(meta["regularMarketTime"]), tz=timezone.utc)
            raw_price = meta["regularMarketPrice"]
            value = Decimal(str(raw_price))
            if value < 0:
                raise ValueError("negative price")
        except (KeyError, IndexError, TypeError, ValueError, InvalidOperation) as exc:
            raise ProviderAdapterError("malformed_response", "Yahoo response lacks a valid current price") from exc
        if meta.get("currency") and meta["currency"] != currency:
            raise ProviderAdapterError("currency_mismatch", "provider currency does not match canonical instrument currency")
        content_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
        return DataObservation(observation_type=ObservationType.PRICE, instrument_id=instrument_id, source_id=UUID(int=0), provider_observation_id=provider_symbol, observed_at=timestamp, ingested_at=datetime.now(timezone.utc), currency=currency, unit="price", value=value, quality=ObservationQuality.VALID, freshness=FreshnessState.VALID, raw_reference=f"yahoo://chart/{provider_symbol}", content_hash=content_hash, schema_version=self.adapter_version, provenance={"source": self.provider, "provider_symbol": provider_symbol}, licensing={"send_to_ai": False}, created_at=datetime.now(timezone.utc))

    def _http_get(self, provider_symbol: str) -> dict:
        request = Request(f"https://query1.finance.yahoo.com/v8/finance/chart/{provider_symbol}", headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise ProviderAdapterError("provider_http", f"Yahoo request failed with status {exc.code}") from exc
        except (URLError, TimeoutError) as exc:
            raise ProviderAdapterError("network_or_timeout", "Yahoo request failed or timed out") from exc
        except json.JSONDecodeError as exc:
            raise ProviderAdapterError("malformed_response", "Yahoo response was not JSON") from exc


class YahooFinanceFundamentalAdapter:
    """Narrow Yahoo Finance quoteSummary adapter for selected fundamentals."""

    provider = "yahoo_finance"
    adapter_version = "yahoo-fundamentals-v1"
    supported_fields = frozenset({"eps", "book_value_per_share", "ebitda", "enterprise_value", "market_cap", "free_cash_flow"})

    def __init__(self, http_get=None, timeout_seconds: float = 10.0) -> None:
        self.http_get = http_get or self._http_get
        self.timeout_seconds = timeout_seconds

    def fetch_fundamentals(self, session, instrument_id: UUID, provider_symbol: str, currency: str) -> list[DataObservation]:
        if not instrument_id or not provider_symbol or len(currency) != 3:
            raise CanonicalInstrumentMappingError("identity", "canonical identity and currency are required")
        payload = self.http_get(provider_symbol)
        observations = self.parse_fundamentals(payload, instrument_id, provider_symbol, currency)
        source = session.query(DataSource).filter_by(provider=self.provider, source_identifier="quoteSummary").first()
        if source is None:
            source = persist_source(session, DataSource(provider=self.provider, source_identifier="quoteSummary", licensing={"send_to_ai": False}, adapter_version=self.adapter_version, created_at=datetime.now(timezone.utc)))
        for observation in observations:
            observation.source_id = source.id
            persist_observation(session, observation)
        return observations

    def parse_fundamentals(self, payload: dict, instrument_id: UUID, provider_symbol: str, currency: str) -> list[DataObservation]:
        try:
            modules = payload["quoteSummary"]["result"][0]
            timestamp = datetime.now(timezone.utc)
            raw_values = modules["financialData"] | modules["defaultKeyStatistics"] | modules["summaryDetail"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderAdapterError("malformed_response", "Yahoo fundamentals response is incomplete") from exc
        provider_currency = modules.get("currency") or raw_values.get("currency")
        if isinstance(provider_currency, dict):
            provider_currency = provider_currency.get("raw")
        if provider_currency and provider_currency != currency:
            raise ProviderAdapterError("currency_mismatch", "provider currency does not match canonical instrument currency")
        content_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
        field_map = {
            "eps": ("trailingEps", "EPS"),
            "book_value_per_share": ("bookValue", "book_value_per_share"),
            "ebitda": ("ebitda", "EBITDA"),
            "enterprise_value": ("enterpriseValue", "enterprise_value"),
            "market_cap": ("marketCap", "market_cap"),
            "free_cash_flow": ("freeCashflow", "free_cash_flow"),
        }
        observations = []
        for field_name, (provider_field, unit) in field_map.items():
            raw = raw_values.get(provider_field)
            if raw is None:
                continue
            if isinstance(raw, dict):
                raw = raw.get("raw")
            try:
                value = Decimal(str(raw))
            except (InvalidOperation, TypeError, ValueError) as exc:
                raise ProviderAdapterError("invalid_numeric", f"Yahoo fundamental {field_name} is not numeric") from exc
            if value < 0 and field_name not in {"eps"}:
                raise ProviderAdapterError("invalid_numeric", f"Yahoo fundamental {field_name} is negative")
            observations.append(DataObservation(observation_type=ObservationType.FUNDAMENTAL, instrument_id=instrument_id, source_id=UUID(int=0), provider_observation_id=f"{provider_symbol}:{provider_field}", observed_at=timestamp, ingested_at=datetime.now(timezone.utc), currency=currency, unit=unit, value=value, values={"field": field_name, "provider_field": provider_field}, quality=ObservationQuality.VALID, freshness=FreshnessState.VALID, raw_reference=f"yahoo://quoteSummary/{provider_symbol}/{provider_field}", content_hash=content_hash, schema_version=self.adapter_version, provenance={"source": self.provider, "provider_symbol": provider_symbol, "provider_field": provider_field}, licensing={"send_to_ai": False}, created_at=datetime.now(timezone.utc)))
        if not observations:
            raise ProviderAdapterError("missing_fields", "Yahoo fundamentals response contains no supported fields")
        return observations

    def _http_get(self, provider_symbol: str) -> dict:
        modules = "financialData,defaultKeyStatistics,summaryDetail"
        request = Request(f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{provider_symbol}?modules={modules}", headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise ProviderAdapterError("provider_http", f"Yahoo fundamentals request failed with status {exc.code}") from exc
        except (URLError, TimeoutError) as exc:
            raise ProviderAdapterError("network_or_timeout", "Yahoo fundamentals request failed or timed out") from exc
        except json.JSONDecodeError as exc:
            raise ProviderAdapterError("malformed_response", "Yahoo fundamentals response was not JSON") from exc
