from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .export import to_excel, to_json
from .llm import LlmConfig, LlmExtractor
from .pipeline import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="invoice-extract",
        description="Extract data from PDF invoices into Excel, with arithmetic checks.",
    )
    parser.add_argument("inputs", nargs="+", type=Path, help="PDF files or folders")
    parser.add_argument("-o", "--output", type=Path, default=Path("out/invoices.xlsx"))
    parser.add_argument("--json", type=Path, help="also write a JSON file")
    parser.add_argument(
        "--engine",
        choices=["auto", "llm", "rules"],
        default="auto",
        help="auto = LLM if OPENAI_API_KEY is set, otherwise rules",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(levelname)s %(message)s")

    pdfs: list[Path] = []
    for p in args.inputs:
        pdfs.extend(sorted(p.glob("*.pdf")) if p.is_dir() else [p])
    if not pdfs:
        print("No PDF files found.", file=sys.stderr)
        return 2

    llm = None
    if args.engine != "rules":
        config = LlmConfig.from_env()
        if config:
            llm = LlmExtractor(config)
        elif args.engine == "llm":
            print("--engine llm needs OPENAI_API_KEY.", file=sys.stderr)
            return 2

    result = run(pdfs, llm)
    to_excel(result, args.output)
    if args.json:
        to_json(result, args.json)

    errors = sum(1 for i in result.issues if i.severity == "error")
    print(f"engine:    {'llm (' + llm.config.model + ')' if llm else 'rules'}")
    print(f"processed: {len(result.invoices)}/{len(pdfs)}")
    print(f"issues:    {errors} errors, {len(result.issues) - errors} warnings")
    for name, reason in result.failed:
        print(f"failed:    {name}: {reason}")
    print(f"written:   {args.output}")
    return 1 if result.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
