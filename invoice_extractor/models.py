from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class LineItem(BaseModel):
    description: str
    quantity: Decimal = Decimal("1")
    unit_price: Decimal
    amount: Decimal


class Invoice(BaseModel):
    """What we pull out of one invoice. Field names match the Excel columns."""

    source_file: str = ""
    vendor_name: str
    vendor_tax_id: str | None = None
    invoice_number: str
    invoice_date: date
    due_date: date | None = None
    currency: str = Field(min_length=3, max_length=3)
    line_items: list[LineItem] = Field(default_factory=list)
    subtotal: Decimal
    tax: Decimal = Decimal("0")
    total: Decimal

    @field_validator("currency")
    @classmethod
    def upper_currency(cls, value: str) -> str:
        return value.upper()

    @field_validator("invoice_number", "vendor_name")
    @classmethod
    def strip(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


# JSON schema sent to the model. Kept separate from the pydantic model so the
# prompt can use plain strings/numbers; pydantic does the strict parsing after.
EXTRACTION_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "vendor_name", "vendor_tax_id", "invoice_number", "invoice_date", "due_date",
        "currency", "line_items", "subtotal", "tax", "total",
    ],
    "properties": {
        "vendor_name": {"type": "string"},
        "vendor_tax_id": {"type": ["string", "null"]},
        "invoice_number": {"type": "string"},
        "invoice_date": {"type": "string", "description": "ISO date, YYYY-MM-DD"},
        "due_date": {"type": ["string", "null"], "description": "ISO date, YYYY-MM-DD"},
        "currency": {"type": "string", "description": "ISO 4217 code, e.g. USD, EUR, KWD"},
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["description", "quantity", "unit_price", "amount"],
                "properties": {
                    "description": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit_price": {"type": "number"},
                    "amount": {"type": "number"},
                },
            },
        },
        "subtotal": {"type": "number"},
        "tax": {"type": "number"},
        "total": {"type": "number"},
    },
}
