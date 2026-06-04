"""Core PDF-to-Markdown conversion for pdf2llm."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pymupdf
import pymupdf4llm


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


@dataclass
class ConversionResult:
    input: Path
    output_dir: Path
    markdown_file: Path
    pages: int
    images: int
    image_files: list[str]


def convert(input_pdf: Path, output_dir: Path) -> ConversionResult:
    """Convert ``input_pdf`` to a Markdown file in ``output_dir``.

    Writes ``<output_dir>/<stem>.md`` and extracted images named
    ``<stem>-p<N>-<idx>.png`` into the same directory. Overwrites silently.
    """
    input_pdf = Path(input_pdf)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = input_pdf.stem

    doc = pymupdf.open(input_pdf)
    try:
        chunks = pymupdf4llm.to_markdown(
            doc,
            page_chunks=True,
            write_images=True,
            image_path=str(output_dir),
            image_format="png",
        )
    finally:
        doc.close()

    parts: list[str] = []
    image_files: list[str] = []
    for chunk in chunks:
        page_number = chunk["metadata"]["page_number"]
        body, images = rename_page_images(
            chunk["text"], page_number, stem, output_dir
        )
        parts.append(wrap_page(page_number, body))
        image_files.extend(images)

    markdown = "\n\n".join(parts) + "\n"
    markdown_file = output_dir / f"{stem}.md"
    markdown_file.write_text(markdown)

    return ConversionResult(
        input=input_pdf,
        output_dir=output_dir,
        markdown_file=markdown_file,
        pages=len(chunks),
        images=len(image_files),
        image_files=image_files,
    )
