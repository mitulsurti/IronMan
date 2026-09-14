from decimal import Decimal, ROUND_HALF_EVEN
from enum import StrEnum


class Currency(StrEnum):
    INR = "INR"
    USD = "USD"


def decimal(value: Decimal | int | str) -> Decimal:
    if isinstance(value, float):
        raise TypeError("binary floating point is not accepted for financial values")
    return Decimal(value)


def quantize(value: Decimal | int | str, quantum: Decimal, rounding: str) -> Decimal:
    """Quantize only when the calling financial convention is explicit."""
    return decimal(value).quantize(quantum, rounding=rounding)


class FinancialConventionError(ValueError):
    """Raised when an unspecified financial convention is required."""


def require_explicit_convention(value: str | None, name: str) -> str:
    if not value:
        raise FinancialConventionError(f"{name} must be explicit")
    return value
