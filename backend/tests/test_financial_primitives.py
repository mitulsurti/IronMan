from decimal import Decimal

import pytest

from ironman.financial.primitives import (
    Currency,
    FinancialConventionError,
    decimal,
    quantize,
    require_explicit_convention,
)


def test_decimal_accepts_exact_inputs() -> None:
    assert decimal("1.10") == Decimal("1.10")
    assert Currency.INR.value == "INR"


def test_binary_float_is_rejected() -> None:
    with pytest.raises(TypeError):
        decimal(1.1)  # type: ignore[arg-type]


def test_quantization_requires_explicit_conventions() -> None:
    assert quantize("1.235", Decimal("0.01"), "ROUND_HALF_EVEN") == Decimal("1.24")


def test_missing_convention_is_rejected() -> None:
    with pytest.raises(FinancialConventionError):
        require_explicit_convention(None, "day_count")
