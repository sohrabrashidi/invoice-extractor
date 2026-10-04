"""Generate the sample invoices in samples/.

All vendors and numbers are invented. Three different layouts, plus one
invoice with a deliberate arithmetic mistake and one duplicate, so the
checks have something to find.

    python scripts/make_samples.py
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

OUT = Path(__file__).resolve().parent.parent / "samples"


def money(v: float, dp: int = 2) -> str:
    return f"{v:,.{dp}f}"


def table(c: canvas.Canvas, y: float, rows: list[tuple], dp: int, header=("Description", "Qty", "Unit price", "Amount")) -> float:
    xs = [50, 330, 410, 500]
    c.setFont("Helvetica-Bold", 10)
    for x, h in zip(xs, header):
        c.drawString(x, y, h)
    c.setFont("Helvetica", 10)
    for desc, qty, price, amount in rows:
        y -= 18
        c.drawString(xs[0], y, desc)
        c.drawRightString(xs[1] + 30, y, f"{qty:g}")
        c.drawRightString(xs[2] + 60, y, money(price, dp))
        c.drawRightString(xs[3] + 60, y, money(amount, dp))
    return y


def bluegate(path: Path, number: str, wrong_total: bool = False) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 790, "Bluegate Hosting Ltd")
    c.setFont("Helvetica", 10)
    c.drawString(50, 774, "14 Harbour Street, Dublin, Ireland")
    c.drawString(50, 760, "VAT No: IE9876543X")
    c.drawString(380, 790, f"Invoice No: {number}")
    c.drawString(380, 774, "Invoice Date: 2026-08-03")
    c.drawString(380, 760, "Due Date: 2026-09-02")
    c.drawString(380, 746, "Currency: USD")
    rows = [("Web hosting (annual)", 1, 480.00, 480.00), ("SSL certificate", 2, 45.00, 90.00), ("Managed backups", 12, 8.50, 102.00)]
    y = table(c, 700, rows, 2)
    subtotal = sum(r[3] for r in rows)
    tax = 0.0
    total = subtotal + tax + (50 if wrong_total else 0)
    c.drawString(380, y - 40, "Subtotal:")
    c.drawRightString(560, y - 40, money(subtotal))
    c.drawString(380, y - 56, "Tax (0%):")
    c.drawRightString(560, y - 56, money(tax))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(380, y - 76, "Total Due:")
    c.drawRightString(560, y - 76, money(total))
    c.save()


def alnoor(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(50, 790, "Al Noor Office Supplies Co.")
    c.setFont("Helvetica", 10)
    c.drawString(50, 775, "Block 3, Street 12, Kuwait City")
    c.drawString(50, 760, "Tax Registration: KW-200481")
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, 725, "TAX INVOICE")
    c.setFont("Helvetica", 10)
    c.drawString(50, 705, "Invoice # AN-26-0917")
    c.drawString(250, 705, "Date: 17/09/2026")
    c.drawString(420, 705, "Payment due: 17/10/2026")
    c.drawString(50, 690, "All amounts in KWD")
    rows = [
        ("A4 paper, 80gsm (box of 5 reams)", 10, 4.250, 42.500),
        ("Toner cartridge HP 26A", 3, 18.900, 56.700),
        ("Ring binders, 2-inch", 24, 0.650, 15.600),
        ("Whiteboard markers, pack of 8", 5, 1.375, 6.875),
    ]
    y = table(c, 650, rows, 3)
    subtotal = sum(r[3] for r in rows)
    c.drawString(380, y - 40, "Sub-total")
    c.drawRightString(560, y - 40, money(subtotal, 3))
    c.drawString(380, y - 56, "VAT 0%")
    c.drawRightString(560, y - 56, money(0, 3))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(380, y - 76, "Grand Total")
    c.drawRightString(560, y - 76, money(subtotal, 3))
    c.save()


def kestrel(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 790, "Kestrel Logistics GmbH")
    c.setFont("Helvetica", 10)
    c.drawString(50, 774, "Lagerstrasse 8, 20457 Hamburg")
    c.drawString(50, 760, "VAT ID: DE312456789")
    c.drawString(50, 720, "Invoice Number: KL-2026-04417")
    c.drawString(50, 705, "Date of issue: 22 Sep 2026")
    c.drawString(50, 690, "Payment due: 22 Oct 2026")
    c.drawString(300, 720, "Bill to: Harbor Point Trading")
    c.drawString(300, 705, "Currency: EUR")
    rows = [
        ("Sea freight HAM-KWI, 20ft container", 1, 2150.00, 2150.00),
        ("Customs documentation", 1, 185.00, 185.00),
        ("Warehouse handling (pallets)", 14, 12.50, 175.00),
    ]
    y = table(c, 650, rows, 2)
    subtotal = sum(r[3] for r in rows)
    tax = round(subtotal * 0.19, 2)
    c.drawString(380, y - 40, "Net amount")
    c.drawRightString(560, y - 40, money(subtotal))
    c.drawString(380, y - 56, "VAT 19%")
    c.drawRightString(560, y - 56, money(tax))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(380, y - 76, "Total")
    c.drawRightString(560, y - 76, money(subtotal + tax))
    c.save()


def main() -> None:
    OUT.mkdir(exist_ok=True)
    bluegate(OUT / "bluegate-INV-10482-original.pdf", "INV-10482")
    bluegate(OUT / "bluegate-INV-10511-wrong-total.pdf", "INV-10511", wrong_total=True)
    bluegate(OUT / "bluegate-INV-10482-resent.pdf", "INV-10482")
    alnoor(OUT / "alnoor-AN-26-0917.pdf")
    kestrel(OUT / "kestrel-KL-2026-04417.pdf")
    print(f"wrote {len(list(OUT.glob('*.pdf')))} files to {OUT}")


if __name__ == "__main__":
    main()
