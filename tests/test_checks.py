from datetime import date
from decimal import Decimal

from invoice_extractor.checks import check_batch, check_invoice
from invoice_extractor.models import Invoice, LineItem


def make(**overrides) -> Invoice:
    data = dict(
        source_file="a.pdf",
        vendor_name="Vendor",
        invoice_number="1",
        invoice_date=date(2026, 9, 1),
        due_date=date(2026, 10, 1),
        currency="usd",
        line_items=[
            LineItem(description="x", quantity=Decimal("2"), unit_price=Decimal("10"), amount=Decimal("20")),
            LineItem(description="y", quantity=Decimal("1"), unit_price=Decimal("5.5"), amount=Decimal("5.5")),
        ],
        subtotal=Decimal("25.5"),
        tax=Decimal("1.275"),
        total=Decimal("26.775"),
    )
    data.update(overrides)
    return Invoice(**data)


def test_clean_invoice_has_no_issues():
    assert check_invoice(make()) == []


def test_currency_is_upper_cased():
    assert make().currency == "USD"


def test_wrong_line_amount():
    inv = make(line_items=[LineItem(description="x", quantity=Decimal("3"), unit_price=Decimal("10"), amount=Decimal("20"))],
               subtotal=Decimal("20"), tax=Decimal("0"), total=Decimal("20"))

    assert [i.check for i in check_invoice(inv)] == ["line_amount"]


def test_total_does_not_add_up():
    issues = check_invoice(make(total=Decimal("30")))

    assert [i.check for i in issues] == ["total"]
    assert "26.775" in issues[0].message


def test_rounding_within_a_cent_is_accepted():
    assert check_invoice(make(total=Decimal("26.78"))) == []


def test_due_date_before_invoice_date():
    issues = check_invoice(make(due_date=date(2026, 8, 1)))

    assert [(i.severity, i.check) for i in issues] == [("warning", "due_date")]


def test_duplicates_are_caught_case_insensitively():
    a = make(source_file="a.pdf", invoice_number="INV-1")
    b = make(source_file="b.pdf", vendor_name="VENDOR", invoice_number="inv-1")
    c = make(source_file="c.pdf", invoice_number="INV-2")

    issues = check_batch([a, b, c])

    assert len(issues) == 1
    assert issues[0].file == "b.pdf"
    assert "a.pdf" in issues[0].message
