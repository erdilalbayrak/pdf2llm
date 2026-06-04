from pathlib import Path

import pymupdf
import pytest


def _make_pdf(path: Path, pages: int = 2, with_image: bool = True) -> Path:
    """Create a small PDF with text on each page and one image on page 1."""
    doc = pymupdf.open()
    for i in range(pages):
        page = doc.new_page()  # default Letter size 612x792
        page.insert_text((72, 72), f"Hello page {i + 1}")
        if with_image and i == 0:
            # A 120x120 red raster, large enough to clear pymupdf4llm's
            # default 5%-of-page size threshold so it gets extracted.
            pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 120, 120))
            pix.set_rect(pix.irect, (255, 0, 0))
            page.insert_image(pymupdf.Rect(72, 120, 252, 300), pixmap=pix)
    doc.save(path)
    doc.close()
    return path


@pytest.fixture
def make_pdf(tmp_path):
    """Return a factory that writes a PDF into the test's tmp_path."""

    def _factory(name: str = "sample.pdf", pages: int = 2, with_image: bool = True) -> Path:
        return _make_pdf(tmp_path / name, pages=pages, with_image=with_image)

    return _factory
