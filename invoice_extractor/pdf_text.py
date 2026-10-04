from __future__ import annotations

from pathlib import Path

import pdfplumber


class NoTextError(Exception):
    """The PDF has no text layer (scanned image). Needs OCR first."""


def read_text(path: Path, max_pages: int = 10) -> str:
    """Return the text of the first pages, keeping the visual line layout."""
    parts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages[:max_pages]:
            text = page.extract_text(layout=True) or ""
            # layout=True pads with lots of spaces; collapse right-hand padding only
            parts.append("\n".join(line.rstrip() for line in text.splitlines()))

    text = "\n\n".join(p for p in parts if p.strip())
    if len(text.strip()) < 20:
        raise NoTextError(f"{path.name}: no text layer found, run OCR first")
    return text
