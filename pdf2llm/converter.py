"""Core PDF-to-Markdown conversion for pdf2llm."""

from __future__ import annotations

import re
from pathlib import Path


def wrap_page(page_number: int, body: str) -> str:
    """Wrap one page's Markdown body in explicit start/end markers."""
    body = body.strip()
    return (
        f"<!-- page: {page_number} start -->\n"
        f"## Page {page_number}\n\n"
        f"{body}\n\n"
        f"<!-- page: {page_number} end -->"
    )


# Matches Markdown image syntax: ![alt](path)
_IMAGE_LINK = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<path>[^)]*)\)")


def rename_page_images(
    text: str, page_number: int, stem: str, output_dir: Path
) -> tuple[str, list[str]]:
    """Rename a page's extracted images to ``<stem>-p<N>-<idx>.png`` in
    ``output_dir`` and rewrite the Markdown links to bare filenames.

    Assumes each image link on the page refers to a distinct written file.
    """
    images: list[str] = []
    counter = 0

    def _replace(match: re.Match) -> str:
        nonlocal counter
        ref = match.group("path").strip()
        if not ref:
            return match.group(0)
        counter += 1
        new_name = f"{stem}-p{page_number}-{counter}.png"
        src = output_dir / Path(ref).name
        dst = output_dir / new_name
        if src.resolve() != dst.resolve() and src.exists():
            src.replace(dst)
        images.append(new_name)
        return f"![{match.group('alt')}]({new_name})"

    new_text = _IMAGE_LINK.sub(_replace, text)
    return new_text, images
