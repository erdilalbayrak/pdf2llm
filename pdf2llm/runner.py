"""Run orchestration: convert, build the summary, and emit output."""

from __future__ import annotations

import argparse
import json
import sys
import time

from pdf2llm.converter import ConversionResult, convert


def build_summary(
    result: ConversionResult | None,
    *,
    elapsed: float,
    status: str,
    error: str | None,
    input_path: str,
    output_dir: str,
) -> dict:
    summary = {
        "status": status,
        "input": input_path,
        "output_dir": output_dir,
        "markdown_file": str(result.markdown_file) if result else None,
        "pages": result.pages if result else 0,
        "images": result.images if result else 0,
        "image_files": list(result.image_files) if result else [],
        "elapsed_seconds": round(elapsed, 3),
    }
    if error:
        summary["error"] = error
    return summary


def format_human(summary: dict) -> str:
    lines = [
        f"pdf2llm: {summary['status']}",
        f"  input:        {summary['input']}",
        f"  output_dir:   {summary['output_dir']}",
        f"  markdown:     {summary['markdown_file']}",
        f"  pages:        {summary['pages']}",
        f"  images:       {summary['images']}",
        f"  elapsed:      {summary['elapsed_seconds']}s",
    ]
    if summary.get("error"):
        lines.append(f"  error:        {summary['error']}")
    return "\n".join(lines)


def run(args: argparse.Namespace) -> int:
    input_path = str(args.input)
    output_dir = str(args.output_dir)

    if not args.quiet:
        print(f"pdf2llm: converting {input_path} -> {output_dir}", file=sys.stderr)

    start = time.perf_counter()
    try:
        result = convert(args.input, args.output_dir)
    except Exception as exc:  # noqa: BLE001 - surface any conversion failure
        elapsed = time.perf_counter() - start
        summary = build_summary(
            None,
            elapsed=elapsed,
            status="error",
            error=str(exc),
            input_path=input_path,
            output_dir=output_dir,
        )
        _emit(summary, as_json=args.as_json)
        return 1

    elapsed = time.perf_counter() - start
    summary = build_summary(
        result,
        elapsed=elapsed,
        status="ok",
        error=None,
        input_path=input_path,
        output_dir=output_dir,
    )

    if not args.quiet:
        print(
            f"pdf2llm: wrote {result.markdown_file} "
            f"({result.pages} pages, {result.images} images)",
            file=sys.stderr,
        )
    _emit(summary, as_json=args.as_json)
    return 0


def _emit(summary: dict, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(summary), file=sys.stdout)
    else:
        print(format_human(summary), file=sys.stdout)
