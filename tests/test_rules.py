from datetime import date
from decimal import Decimal

import pytest

from invoice_extractor import rules
from invoice_extractor.pdf_text import read_text


@pytest.mark.parametrize(
    "file, vendor, number, currency, total",
    [
        ("alnoor-AN-26-0917.pdf", "Al Noor Office Supplies Co.", "AN-26-0917", "KWD", Decimal("121.675")),
        ("bluegate-INV-10482-original.pdf", "Bluegate Hosting Ltd", "INV-10482", "USD", Decimal("672.00")),
        ("kestrel-KL-2026-04417.pdf", "Kestrel Logistics GmbH", "KL-2026-04417", "EUR", Decimal("2986.90")),
    ],
)
def test_reads_each_layout(samples, file, vendor, number, currency, total):
    data = rules.extract(read_text(samples / file))

    assert data["vendor_name"] == vendor
    assert data["invoice_number"] == number
    assert data["currency"] == currency
    assert data["total"] == total


def test_dates_in_different_formats(samples):
    alnoor = rules.extract(read_text(samples / "alnoor-AN-26-0917.pdf"))
    kestrel = rules.extract(read_text(samples / "kestrel-KL-2026-04417.pdf"))

    assert alnoor["invoice_date"] == date(2026, 9, 17)
    assert alnoor["due_date"] == date(2026, 10, 17)
    assert kestrel["invoice_date"] == date(2026, 9, 22)


def test_line_items_keep_three_decimals_for_kwd(samples):
    data = rules.extract(read_text(samples / "alnoor-AN-26-0917.pdf"))

    assert len(data["line_items"]) == 4
    markers = data["line_items"][3]
    assert markers["unit_price"] == Decimal("1.375")
    assert markers["amount"] == Decimal("6.875")


def test_thousands_separators(samples):
    data = rules.extract(read_text(samples / "kestrel-KL-2026-04417.pdf"))

    assert data["line_items"][0]["amount"] == Decimal("2150.00")
    assert data["subtotal"] == Decimal("2510.00")


@pytest.mark.parametrize("raw, expected", [
    ("2026-08-03", date(2026, 8, 3)),
    ("17/09/2026", date(2026, 9, 17)),
    ("22 Sep 2026", date(2026, 9, 22)),
    ("September 5, 2026", date(2026, 9, 5)),
])
def test_to_date(raw, expected):
    assert rules.to_date(raw) == expected


def test_unknown_date_format_is_an_error():
    with pytest.raises(ValueError):
        rules.to_date("next tuesday")
