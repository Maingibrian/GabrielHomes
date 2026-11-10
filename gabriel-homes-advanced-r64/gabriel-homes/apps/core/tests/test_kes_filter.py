"""Tests for the kes template filter."""
from decimal import Decimal

import pytest

from apps.core.templatetags.core_tags import kes, kes_short

pytestmark = pytest.mark.django_db


def test_kes_formats_integer_decimal():
    assert kes(Decimal("12500000")) == "KES 12,500,000"


def test_kes_handles_zero():
    assert kes(Decimal("0")) == "KES 0"


def test_kes_handles_none():
    assert kes(None) == ""


def test_kes_handles_string_input():
    assert kes("9500000") == "KES 9,500,000"


def test_kes_with_monthly_period_suffix():
    assert kes(Decimal("95000"), "monthly") == "KES 95,000 / month"


def test_kes_with_total_period_no_suffix():
    assert kes(Decimal("12500000"), "total") == "KES 12,500,000"


def test_kes_handles_decimal_amounts():
    assert kes(Decimal("99.99")) == "KES 99.99"


def test_kes_short_millions():
    assert kes_short(Decimal("12500000")) == "KES 12M"
    assert kes_short(Decimal("22500000")) == "KES 22M"


def test_kes_short_thousands():
    assert kes_short(Decimal("95000")) == "KES 95K"


def test_kes_short_small():
    assert kes_short(Decimal("500")) == "KES 500"
