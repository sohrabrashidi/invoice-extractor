# invoice-extractor

Turn a folder of PDF supplier invoices into a clean Excel file, and **flag the ones where the numbers don't add up**.

Most "AI invoice extraction" demos stop at "the model returned JSON". In accounts payable the real work starts after that: is the total right, is this a duplicate, did the model read `1,375` as `1.375`? This tool extracts the data with an LLM (or a rule-based fallback), then checks every invoice before anything reaches the spreadsheet.

```
$ invoice-extract samples/ -o out/invoices.xlsx --engine rules
engine:    rules
processed: 5/5
issues:    2 errors, 0 warnings
written:   out/invoices.xlsx
```

## What you get

An Excel workbook with three sheets:

- **Invoices**: one row per invoice: vendor, tax ID, number, dates, currency, subtotal, tax, total, and a status of `OK` or `CHECK` (highlighted).
- **Line items**: every line from every invoice, ready for a pivot table.
- **Issues**: what is wrong and where, in plain language:
  - `line_amount`: quantity × unit price doesn't match the line amount
  - `subtotal`: line items don't add up to the subtotal
  - `total`: subtotal + tax ≠ total
  - `duplicate`: same vendor and invoice number already seen in the batch
  - `due_date`: due date before invoice date
  - `not_processed`: file couldn't be read (scanned image, corrupt PDF)

Optionally a JSON file with the same data, for loading into another system.

## How it works

1. **Text extraction** with `pdfplumber`, keeping the visual layout so table columns stay apart.
2. **Field extraction**, two engines:
   - **LLM**: any OpenAI-compatible endpoint, called with a strict JSON schema (`response_format: json_schema`, `strict: true`) and temperature 0. The prompt tells the model to copy what's printed and never calculate or guess. Retries on 429/5xx with backoff.
   - **Rules**: label and pattern matching for common English layouts. No API key needed. It's the default when `OPENAI_API_KEY` isn't set, and useful as a cross-check.
3. **Validation** with Pydantic (types, dates, currency codes), then the arithmetic and duplicate checks above. Money is handled as `Decimal` throughout, so three-decimal currencies like KWD stay exact.
4. **Export** to Excel (`openpyxl`) with formatting, filters and frozen headers.

One unreadable file never stops the batch. It's listed in the Issues sheet and the rest are processed.

## Usage

```bash
pip install -e .

# offline, rule-based
invoice-extract samples/ -o out/invoices.xlsx --engine rules

# with an LLM
export OPENAI_API_KEY=sk-...
invoice-extract path/to/invoices/ -o out/invoices.xlsx --json out/invoices.json

# a local model through Ollama / LM Studio
export OPENAI_BASE_URL=http://localhost:11434/v1
export INVOICE_MODEL=llama3.1
```

Exit code is `1` if any file failed to process, so it can run in a scheduled job.

## Sample data

`scripts/make_samples.py` generates five invoices from three made-up vendors, each with a different layout (USD, KWD with 3 decimals, EUR with 19% VAT). Two of them contain planted problems: one total that doesn't match its lines, and one invoice sent twice.

```bash
pip install -e ".[dev]"
python scripts/make_samples.py      # writes samples/*.pdf
```

The tests generate them automatically if they're missing.

## Tests

```bash
pytest
```

The tests cover each sample layout, date formats, thousands separators, all checks, the Excel output, and the LLM path using a mocked HTTP transport (no network, no key).

## Limits

- Scanned PDFs without a text layer need OCR first (e.g. `ocrmypdf`). They are reported as `not_processed` instead of guessed.
- The rules engine is tuned for common English layouts. Unusual layouts are what the LLM engine is for.
- For a production setup I'd add: a vendor master list to normalise names, matching against purchase orders, and a review screen for `CHECK` invoices.

## License

MIT
