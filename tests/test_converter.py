from pdf2llm.converter import wrap_page


def test_wrap_page_adds_start_end_markers_and_heading():
    out = wrap_page(4, "Body text here.")
    assert out.startswith("<!-- page: 4 start -->\n## Page 4\n")
    assert "Body text here." in out
    assert out.rstrip().endswith("<!-- page: 4 end -->")


def test_wrap_page_strips_surrounding_whitespace_in_body():
    out = wrap_page(1, "\n\n  Spaced body  \n\n")
    assert "## Page 1\n\nSpaced body" in out
    assert "<!-- page: 1 end -->" in out


from pathlib import Path

from pdf2llm.converter import rename_page_images


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
