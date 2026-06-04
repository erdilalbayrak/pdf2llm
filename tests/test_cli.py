import argparse
import json

import pytest

from pdf2llm.cli import build_parser, main, pdf_file
from pdf2llm.cli import main as cli_main


def test_pdf_file_rejects_missing(tmp_path):
    with pytest.raises(argparse.ArgumentTypeError):
        pdf_file(str(tmp_path / "nope.pdf"))


def test_pdf_file_rejects_non_pdf(tmp_path):
    f = tmp_path / "note.txt"
    f.write_text("hi")
    with pytest.raises(argparse.ArgumentTypeError):
        pdf_file(str(f))


def test_pdf_file_rejects_directory(tmp_path):
    d = tmp_path / "adir.pdf"
    d.mkdir()
    with pytest.raises(argparse.ArgumentTypeError):
        pdf_file(str(d))


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


def test_json_summary_on_stdout(make_pdf, tmp_path, capsys):
    pdf = make_pdf("report.pdf", pages=2, with_image=False)
    out_dir = tmp_path / "out"

    code = cli_main([str(pdf), str(out_dir), "--json"])
    assert code == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)  # stdout must be valid JSON
    assert payload["status"] == "ok"
    assert payload["pages"] == 2
    assert payload["markdown_file"].endswith("report.md")
    assert payload["input"].endswith("report.pdf")
    assert "elapsed_seconds" in payload
    assert payload["images"] == 0
    assert payload["image_files"] == []


def test_quiet_suppresses_stderr_but_keeps_summary(make_pdf, tmp_path, capsys):
    pdf = make_pdf("a.pdf", pages=1, with_image=False)
    out_dir = tmp_path / "out"

    code = cli_main([str(pdf), str(out_dir), "--quiet"])
    assert code == 0

    captured = capsys.readouterr()
    assert captured.err == ""  # no progress on stderr
    assert "pdf2llm" in captured.out  # human summary still printed


def test_quiet_json_emits_only_json(make_pdf, tmp_path, capsys):
    pdf = make_pdf("a.pdf", pages=1, with_image=False)
    out_dir = tmp_path / "out"

    code = cli_main([str(pdf), str(out_dir), "--quiet", "--json"])
    assert code == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    json.loads(captured.out)  # stdout is pure JSON, nothing else


def test_default_run_prints_progress_to_stderr(make_pdf, tmp_path, capsys):
    pdf = make_pdf("a.pdf", pages=1, with_image=False)
    out_dir = tmp_path / "out"

    code = cli_main([str(pdf), str(out_dir)])
    assert code == 0

    captured = capsys.readouterr()
    assert captured.err != ""  # progress went to stderr
    assert "pages" in captured.out.lower()  # human summary on stdout


def test_corrupt_pdf_reports_error_and_exits_1(tmp_path, capsys):
    # Passes the .pdf-extension arg validator but is not a valid PDF, so
    # conversion raises and the runner must report status=error / exit 1.
    bad = tmp_path / "broken.pdf"
    bad.write_bytes(b"not a real pdf")
    out_dir = tmp_path / "out"

    code = cli_main([str(bad), str(out_dir), "--json"])
    assert code == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert payload["error"]
    assert payload["pages"] == 0
