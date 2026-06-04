# pdf2llm — Design

## Purpose

A small Python CLI that converts a PDF into LLM-friendly Markdown. It extracts
text as Markdown (headings, lists, tables preserved), pulls images out to disk,
and inserts explicit per-page start/end markers so a coding LLM (e.g. opencode +
Claude) can be asked things like "what's on page 4?".

## Scope

- Single PDF in, single Markdown file + extracted images out.
- One command, two positional args, two flags.
- Not in scope: batch/multi-file conversion, OCR of scanned images, PDF
  generation, configurable templates.

## Stack & Layout (uv-managed)

- Initialized and managed with `uv` (`uv init`, `uv add`, `uv run`).
- Dependencies: `pymupdf4llm` (pulls in `PyMuPDF`).
- Dev dependencies: `pytest`.

```
pdf2llm/
  pdf2llm/
    __init__.py
    cli.py          # arg parsing, output streams, exit codes, summary
    converter.py    # core conversion logic
  tests/
    test_cli.py
    test_converter.py
  docs/superpowers/specs/
    2026-06-04-pdf2llm-design.md
  pyproject.toml
  README.md
```

- Console script: `pdf2llm = "pdf2llm.cli:main"`.
- Invoked as `uv run pdf2llm <input.pdf> <output_dir> [--quiet] [--json]`.

## CLI

```
pdf2llm <input.pdf> <output_dir> [--quiet] [--json] [-h/--help]
```

- `input.pdf` (positional): validated by an argparse `type=` function — must
  exist, be a file, and have a `.pdf` extension. Failure raises
  `ArgumentTypeError`.
- `output_dir` (positional): created recursively if missing.
- `--quiet`: suppress progress output; still emit the final summary.
- `--json`: emit the final summary as a single JSON object instead of human text.
- `--help`/`-h`: full usage (argparse default).
- **Bad/missing/wrong-type args**: a custom `ArgumentParser.error()` override
  prints the *full help* (not just the usage line) to stderr and exits with
  code `2`.

### Output streams

- Progress/info → **stderr**.
- Final summary → **stdout** (keeps stdout clean and pipe-friendly for `--json`).
- `--quiet`: no stderr progress; summary still printed to stdout.
- `--quiet --json`: stdout contains only the JSON object.

### Exit codes

- `0` — success.
- `2` — argument/validation error (help printed).
- `1` — runtime conversion error (e.g. corrupt PDF); summary reports
  `status: "error"` with the message.

## Conversion Flow (`converter.py`)

1. Open the PDF and run:
   ```python
   pymupdf4llm.to_markdown(
       doc,
       page_chunks=True,
       write_images=True,
       image_path=<output_dir>,
       image_format="png",
   )
   ```
   This returns one chunk per page and writes images into the output dir root.
2. For each page (1-based `N`):
   - Normalize every extracted image for that page to
     `<pdfstem>-p<N>-<idx>.png` in the output root (`idx` is 1-based per page).
   - Rewrite that page's Markdown image links to the bare filename (md and
     images share the directory, so no path prefix is needed).
   - Wrap the page body with explicit markers:
     ```
     <!-- page: N start -->
     ## Page N

     <page markdown>

     <!-- page: N end -->
     ```
3. Concatenate all pages and write `<output_dir>/<pdfstem>.md`.
4. Overwrite the `.md` and any same-named images silently.

### Image naming rationale

`pymupdf4llm`'s built-in image names are not `<pdfstem>-p<N>-<idx>.png`, so step
2 performs a rename + link-rewrite pass to satisfy the naming convention and the
"images in the output root" requirement. Page-tagged names make it obvious which
image belongs to which page.

## Summary

Emitted at the end of every run (human text by default, JSON with `--json`).

Fields:

- `input` — input PDF path.
- `output_dir` — output directory.
- `markdown_file` — written `.md` path.
- `pages` — page count.
- `images` — extracted image count.
- `image_files` — list of image filenames.
- `elapsed_seconds` — wall-clock duration.
- `status` — `"ok"` or `"error"`.
- `error` — message when `status == "error"` (omitted/empty otherwise).

## Error Handling

- Missing input / not a file / non-`.pdf` → help printed to stderr, exit `2`.
- Corrupt/unreadable PDF → readable error message; summary `status: "error"`;
  exit `1`.
- Output directory creation failures (permissions) → reported as a runtime
  error, exit `1`.

## README.md

Thorough user-facing doc containing:

- What it does and why (PDF → LLM-friendly Markdown with page markers).
- Install via `uv` (`uv sync`, `uv run pdf2llm ...`).
- Usage, all flags, exit codes.
- Examples: basic, `--quiet`, `--json`, `--quiet --json`.
- Output format explained: page start/end markers, `## Page N` headings, image
  naming (`<stem>-p<N>-<idx>.png`) placed in the output root.
- LLM workflow tip ("ask what's on page 4").

## Testing (pytest)

Tests generate a tiny PDF in-process with PyMuPDF (two pages of text + one
embedded image) — no fixtures committed.

`test_converter.py`:
- `.md` is written and contains `<!-- page: 1 start -->` … `<!-- page: 1 end -->`
  and `## Page 1` / `## Page 2`.
- Image file `<stem>-p<page>-1.png` exists in the output root.
- The Markdown image link is a bare filename and resolves to an existing file.
- Missing output directory is created.

`test_cli.py`:
- `--help` exits `0` and prints usage.
- Missing file / non-`.pdf` input prints help to stderr and exits `2`.
- `--json` emits valid, parseable JSON on stdout with correct counts/paths.
- `--quiet` produces no stderr progress but still emits the summary on stdout.
- `--quiet --json` emits only JSON on stdout.

## Decisions (resolved)

- Engine: `pymupdf4llm`.
- Page markers: `<!-- page: N start -->` + `## Page N` … `<!-- page: N end -->`.
- Image names: `<pdfstem>-p<N>-<idx>.png`, in the output root.
- Output arg is a directory; `.md` named from the PDF stem.
- Overwrite silently.
- Project/package/script name: `pdf2llm`.
