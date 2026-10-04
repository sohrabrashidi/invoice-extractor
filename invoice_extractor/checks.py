"""Arithmetic and sanity checks.

An extracted invoice is only useful if the numbers can be trusted. These
checks catch both extraction mistakes and genuine errors on the invoice.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .models import Invoice

TOLERANCE = Decimal("0.01")


@dataclass(frozen=True)
class Issue:
    file: str
    severity: str  # "error" or "warning"
    check: str
    message: str


def _close(a: Decimal, b: Decimal) -> bool:
    return abs(a - b) <= TOLERANCE


def check_invoice(inv: Invoice) -> list[Issue]:
    issues: list[Issue] = []

    def add(severity: str, check: str, message: str) -> None:
        issues.append(Issue(inv.source_file, severity, check, message))

    for n, item in enumerate(inv.line_items, start=1):
        expected = item.quantity * item.unit_price
        if not _close(expected, item.amount):
            add("error", "line_amount", f"line {n} '{item.description}': {item.quantity} x {item.unit_price} = {expected}, invoice says {item.amount}")

    if inv.line_items:
        lines_sum = sum((i.amount for i in inv.line_items), Decimal("0"))
        if not _close(lines_sum, inv.subtotal):
            add("error", "subtotal", f"line items add up to {lines_sum}, subtotal is {inv.subtotal}")
    else:
        add("warning", "no_lines", "no line items found")

    if not _close(inv.subtotal + inv.tax, inv.total):
        add("error", "total", f"subtotal {inv.subtotal} + tax {inv.tax} = {inv.subtotal + inv.tax}, total is {inv.total}")

    if inv.due_date and inv.due_date < inv.invoice_date:
        add("warning", "due_date", f"due date {inv.due_date} is before invoice date {inv.invoice_date}")

    if inv.total <= 0:
        add("warning", "total_not_positive", f"total is {inv.total}; credit note?")

    return issues


def check_batch(invoices: list[Invoice]) -> list[Issue]:
    """Cross-invoice checks. Duplicate invoices are the classic way to pay twice."""
    issues: list[Issue] = []
    seen: dict[tuple[str, str], str] = {}
    for inv in invoices:
        key = (inv.vendor_name.casefold(), inv.invoice_number.casefold())
        if key in seen:
            issues.append(Issue(inv.source_file, "error", "duplicate", f"same vendor and invoice number as {seen[key]}"))
        else:
            seen[key] = inv.source_file
    return issues
