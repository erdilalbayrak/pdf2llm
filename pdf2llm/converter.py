"""Core PDF-to-Markdown conversion for pdf2llm."""

from __future__ import annotations


def wrap_page(page_number: int, body: str) -> str:
    """Wrap one page's Markdown body in explicit start/end markers."""
    body = body.strip()
    return (
        f"<!-- page: {page_number} start -->\n"
        f"## Page {page_number}\n\n"
        f"{body}\n\n"
        f"<!-- page: {page_number} end -->"
    )
