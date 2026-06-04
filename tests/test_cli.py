import pytest

from pdf2llm.cli import build_parser, main, pdf_file


def test_pdf_file_rejects_missing(tmp_path):
    with pytest.raises(Exception):
        pdf_file(str(tmp_path / "nope.pdf"))


def test_pdf_file_rejects_non_pdf(tmp_path):
    f = tmp_path / "note.txt"
    f.write_text("hi")
    with pytest.raises(Exception):
        pdf_file(str(f))


def test_pdf_file_accepts_existing_pdf(make_pdf):
    pdf = make_pdf("ok.pdf", pages=1, with_image=False)
    assert pdf_file(str(pdf)) == pdf


def test_help_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "usage:" in out.lower()


def test_bad_input_prints_help_to_stderr_and_exits_2(make_pdf, tmp_path, capsys):
    out_dir = tmp_path / "out"
    code = main([str(tmp_path / "missing.pdf"), str(out_dir)])
    assert code == 2
    err = capsys.readouterr().err
    assert "usage:" in err.lower()
