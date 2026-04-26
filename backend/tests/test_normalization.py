from decimal import Decimal

from app.engine.normalization import normalize_amount, normalize_employer, normalize_period


def test_normalize_period_handles_named_and_iso_months() -> None:
    assert normalize_period("March 2026") == "2026-03"
    assert normalize_period("2026-03") == "2026-03"


def test_normalize_period_rejects_invalid_iso_month() -> None:
    try:
        normalize_period("2026-13")
    except ValueError as exc:
        assert "Unsupported period" in str(exc)
    else:
        raise AssertionError("Expected invalid month to fail")


def test_normalize_amount_strips_currency_and_grouping() -> None:
    assert normalize_amount("Rs. 6,000") == Decimal("6000.00")
    assert normalize_amount("₹5,500.50") == Decimal("5500.50")


def test_normalize_employer_removes_legal_suffix_noise() -> None:
    assert normalize_employer("Acme India Pvt Ltd") == normalize_employer("Acme India Private Limited")
