"""Command-line interface for pdf2llm."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


class HelpOnErrorParser(argparse.ArgumentParser):
    """Argparse parser that prints full help (not just usage) on error."""

    def error(self, message: str):  # noqa: D401
        self.print_help(sys.stderr)
        sys.stderr.write(f"\nerror: {message}\n")
        self.exit(2)


def pdf_file(value: str) -> Path:
    """Argparse ``type`` validator for the input PDF path."""
    p = Path(value)
    if not p.exists():
        raise argparse.ArgumentTypeError(f"input file does not exist: {value}")
    if not p.is_file():
        raise argparse.ArgumentTypeError(f"input is not a file: {value}")
    if p.suffix.lower() != ".pdf":
        raise argparse.ArgumentTypeError(f"input is not a .pdf file: {value}")
    return p


def build_parser() -> argparse.ArgumentParser:
    parser = HelpOnErrorParser(
        prog="pdf2llm",
        description=(
            "Convert a PDF into LLM-friendly Markdown with per-page markers. "
            "The Markdown file and all extracted images are written into a "
            "single output directory."
        ),
    )
    parser.add_argument(
        "input",
        type=pdf_file,
        help="path to the input .pdf file",
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="directory for the .md file and extracted images (created if missing)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="suppress progress output; still print the final summary",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="emit the final summary as a single JSON object",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse exits 0 for --help, 2 for arg errors; surface as return code.
        return int(exc.code or 0)

    # Conversion + summary wiring is added in Task 7.
    from pdf2llm.runner import run

    return run(args)
