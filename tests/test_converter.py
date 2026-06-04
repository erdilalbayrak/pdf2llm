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
