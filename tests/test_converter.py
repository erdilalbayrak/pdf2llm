from pathlib import Path

from pdf2llm.converter import (
    ConversionResult,
    convert,
    rename_page_images,
    wrap_page,
)


def test_wrap_page_adds_start_end_markers_and_heading():
    out = wrap_page(4, "Body text here.")
    assert out.startswith("<!-- page: 4 start -->\n## Page 4\n")
    assert "Body text here." in out
    assert out.rstrip().endswith("<!-- page: 4 end -->")


def test_wrap_page_strips_surrounding_whitespace_in_body():
    out = wrap_page(1, "\n\n  Spaced body  \n\n")
    assert "## Page 1\n\nSpaced body" in out
    assert "<!-- page: 1 end -->" in out


def test_rename_page_images_renames_file_and_rewrites_link(tmp_path):
    # Library-written image on disk with an arbitrary name.
    (tmp_path / "sample.pdf-0-0.png").write_bytes(b"PNGDATA")
    text = "Intro\n\n![](sample.pdf-0-0.png)\n\nOutro"

    new_text, images = rename_page_images(
        text, page_number=3, stem="sample", output_dir=tmp_path
    )

    assert images == ["sample-p3-1.png"]
    assert (tmp_path / "sample-p3-1.png").exists()
    assert not (tmp_path / "sample.pdf-0-0.png").exists()
    assert "![](sample-p3-1.png)" in new_text
    assert "sample.pdf-0-0.png" not in new_text


def test_rename_page_images_handles_absolute_path_links(tmp_path):
    src = tmp_path / "img-7.png"
    src.write_bytes(b"PNGDATA")
    text = f"![](  {src}  )"  # absolute path, with surrounding spaces

    new_text, images = rename_page_images(
        text, page_number=1, stem="doc", output_dir=tmp_path
    )

    assert images == ["doc-p1-1.png"]
    assert (tmp_path / "doc-p1-1.png").exists()
    assert "![](doc-p1-1.png)" in new_text


def test_rename_page_images_no_images_is_noop(tmp_path):
    text = "Just text, no images."
    new_text, images = rename_page_images(
        text, page_number=2, stem="doc", output_dir=tmp_path
    )
    assert images == []
    assert new_text == text


def test_rename_page_images_increments_index_per_page(tmp_path):
    (tmp_path / "a.png").write_bytes(b"A")
    (tmp_path / "b.png").write_bytes(b"B")
    text = "![](a.png)\n\n![](b.png)"

    new_text, images = rename_page_images(
        text, page_number=5, stem="doc", output_dir=tmp_path
    )

    assert images == ["doc-p5-1.png", "doc-p5-2.png"]
    assert "![](doc-p5-1.png)" in new_text
    assert "![](doc-p5-2.png)" in new_text


def test_rename_page_images_leaves_phantom_links_untouched(tmp_path):
    # Link with no corresponding file on disk: must not be rewritten or counted.
    text = "![](missing.png)"
    new_text, images = rename_page_images(
        text, page_number=1, stem="doc", output_dir=tmp_path
    )
    assert images == []
    assert new_text == text


def test_convert_writes_markdown_with_page_markers(make_pdf, tmp_path):
    pdf = make_pdf("report.pdf", pages=2, with_image=False)
    out_dir = tmp_path / "out"

    result = convert(pdf, out_dir)

    assert isinstance(result, ConversionResult)
    assert result.markdown_file == out_dir / "report.md"
    assert result.markdown_file.exists()
    md = result.markdown_file.read_text()
    assert "<!-- page: 1 start -->" in md
    assert "## Page 1" in md
    assert "<!-- page: 1 end -->" in md
    assert "<!-- page: 2 start -->" in md
    assert "<!-- page: 2 end -->" in md
    assert result.pages == 2


def test_convert_creates_missing_output_dir(make_pdf, tmp_path):
    pdf = make_pdf("a.pdf", pages=1, with_image=False)
    out_dir = tmp_path / "nested" / "out"
    assert not out_dir.exists()

    result = convert(pdf, out_dir)

    assert out_dir.is_dir()
    assert result.markdown_file.exists()


def test_convert_extracts_image_to_output_root(make_pdf, tmp_path):
    pdf = make_pdf("doc.pdf", pages=1, with_image=True)
    out_dir = tmp_path / "out"

    result = convert(pdf, out_dir)

    assert result.images >= 1
    # Image named per convention and placed in the output root.
    assert result.image_files[0] == "doc-p1-1.png"
    assert (out_dir / "doc-p1-1.png").exists()
    md = result.markdown_file.read_text()
    assert "![](doc-p1-1.png)" in md or "](doc-p1-1.png)" in md


def test_convert_extracts_image_when_output_dir_has_spaces_and_special_chars(
    make_pdf, tmp_path
):
    # pymupdf4llm's layout image writer sanitizes the *entire* save path
    # (spaces -> "_", em-dash -> "-") while only creating the unsanitized
    # directory, so writing images into a dir with spaces/special chars used
    # to fail with ENOENT. Images must still be extracted into the real dir.
    pdf = make_pdf("doc.pdf", pages=1, with_image=True)
    out_dir = tmp_path / "RFC_ Ontology Platform \u2014 High-Level Architecture"

    result = convert(pdf, out_dir)

    assert result.images >= 1
    assert result.image_files[0] == "doc-p1-1.png"
    assert (out_dir / "doc-p1-1.png").exists()
    md = result.markdown_file.read_text()
    assert "doc-p1-1.png" in md


def test_convert_overwrites_existing_markdown_silently(make_pdf, tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    stale = out_dir / "report.md"
    stale.write_text("STALE CONTENT")

    pdf = make_pdf("report.pdf", pages=1, with_image=False)
    result = convert(pdf, out_dir)

    assert result.markdown_file == stale
    assert "STALE CONTENT" not in stale.read_text()
    assert "<!-- page: 1 start -->" in stale.read_text()


def test_convert_uses_classic_extraction_and_emits_no_pua_chars(make_pdf, tmp_path):
    # pymupdf4llm's layout mode (default) mis-maps some glyphs into the Unicode
    # Private Use Area, corrupting text for LLM use. convert() must force the
    # classic path and never emit PUA codepoints.
    import pymupdf4llm

    pymupdf4llm.use_layout(True)  # simulate a prior caller enabling layout mode
    pdf = make_pdf("doc.pdf", pages=2, with_image=True)
    out_dir = tmp_path / "out"

    result = convert(pdf, out_dir)

    assert pymupdf4llm._use_layout is False
    md = result.markdown_file.read_text()
    assert not any(0xE000 <= ord(ch) <= 0xF8FF for ch in md)
