"""Offline extractor based on labels and patterns.

It handles common English invoice layouts and is used when no LLM is
configured, and as a cross-check. It will not cope with every vendor
format; that's what the LLM path is for.
"""
from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

NUMBER = r"-?\d{1,3}(?:,\d{3})*(?:\.\d+)?|-?\d+(?:\.\d+)?"

LABELS = {
    "invoice_number": r"(?:invoice\s*(?:no\.?|number|#)|inv\s*#)\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-/]+)",
    "invoice_date": r"(?:invoice\s*date|date\s*of\s*issue|issue\s*date|(?<!due )(?<!payment )\bdate)\s*[:\-]?\s*([0-9A-Za-z ,./\-]{6,20}\d)",
    "due_date": r"(?:due\s*date|payment\s*due)\s*[:\-]?\s*([0-9A-Za-z ,./\-]{6,20}\d)",
    "vendor_tax_id": r"(?:vat|tax|trn|gst)\s*(?:id|no\.?|number|reg(?:istration)?)\s*[:\-]?\s*([A-Z0-9\-]{5,})",
    "subtotal": rf"(?:sub\s*-?\s*total|net\s*amount)\s*[:\-]?\s*(?:[A-Z]{{3}}\s*)?({NUMBER})",
    "tax": rf"(?:vat|tax|gst)(?:\s*\(?\d+(?:\.\d+)?\s*%\)?)?\s*(?:amount)?\s*[:\-]?\s*(?:[A-Z]{{3}}\s*)?({NUMBER})\s*$",
    "total": rf"(?:total\s*due|amount\s*due|grand\s*total|^\s*total)\s*[:\-]?\s*(?:[A-Z]{{3}}\s*)?({NUMBER})",
}

CURRENCY = r"\b(USD|EUR|GBP|KWD|AED|SAR|QAR|BHD|OMR|INR)\b"

# "Web hosting (annual)     2     150.00     300.00"
LINE_ITEM = re.compile(rf"^\s*(?P<desc>[A-Za-z][^\n]*?\S)\s{{2,}}(?P<qty>{NUMBER})\s{{2,}}(?P<price>{NUMBER})\s{{2,}}(?P<amount>{NUMBER})\s*$")

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y"]


def to_decimal(raw: str) -> Decimal:
    try:
        return Decimal(raw.replace(",", ""))
    except InvalidOperation as exc:
        raise ValueError(f"not a number: {raw!r}") from exc


def to_date(raw: str) -> date:
    raw = raw.strip().rstrip(".")
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"unrecognised date: {raw!r}")


def _find(name: str, text: str) -> str | None:
    match = re.search(LABELS[name], text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def extract(text: str) -> dict:
    lines = [line for line in text.splitlines() if line.strip()]

    items = []
    for line in lines:
        m = LINE_ITEM.match(line)
        if m and not re.search(r"\b(total|subtotal|vat|tax)\b", m["desc"], re.IGNORECASE):
            items.append({
                "description": m["desc"].strip(),
                "quantity": to_decimal(m["qty"]),
                "unit_price": to_decimal(m["price"]),
                "amount": to_decimal(m["amount"]),
            })

    currency = re.search(CURRENCY, text)
    raw_date = _find("invoice_date", text)
    raw_due = _find("due_date", text)
    subtotal = _find("subtotal", text)
    tax = _find("tax", text)
    total = _find("total", text)

    return {
        # Vendor name is normally the first line of the header.
        "vendor_name": " ".join(lines[0].split()) if lines else "",
        "vendor_tax_id": _find("vendor_tax_id", text),
        "invoice_number": _find("invoice_number", text) or "",
        "invoice_date": to_date(raw_date) if raw_date else None,
        "due_date": to_date(raw_due) if raw_due else None,
        "currency": currency.group(1) if currency else "",
        "line_items": items,
        "subtotal": to_decimal(subtotal) if subtotal else sum((i["amount"] for i in items), Decimal("0")),
        "tax": to_decimal(tax) if tax else Decimal("0"),
        "total": to_decimal(total) if total else None,
    }
