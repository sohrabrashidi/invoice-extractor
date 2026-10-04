from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from . import rules
from .checks import Issue, check_batch, check_invoice
from .llm import LlmExtractor
from .models import Invoice
from .pdf_text import NoTextError, read_text

log = logging.getLogger(__name__)


@dataclass
class BatchResult:
    invoices: list[Invoice] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)


def extract_file(path: Path, llm: LlmExtractor | None) -> Invoice:
    text = read_text(path)
    raw = llm.extract(text) if llm else rules.extract(text)
    raw["source_file"] = path.name
    return Invoice.model_validate(raw)


def run(paths: list[Path], llm: LlmExtractor | None = None) -> BatchResult:
    result = BatchResult()
    for path in sorted(paths):
        try:
            invoice = extract_file(path, llm)
        except NoTextError as exc:
            result.failed.append((path.name, str(exc)))
            continue
        except ValidationError as exc:
            fields = ", ".join(".".join(str(p) for p in e["loc"]) for e in exc.errors())
            result.failed.append((path.name, f"could not read: {fields}"))
            continue
        except Exception as exc:  # one bad file must not stop the batch
            log.exception("failed on %s", path.name)
            result.failed.append((path.name, f"{type(exc).__name__}: {exc}"))
            continue

        result.invoices.append(invoice)
        result.issues.extend(check_invoice(invoice))

    result.issues.extend(check_batch(result.invoices))
    return result
