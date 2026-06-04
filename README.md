# pdf2llm

Convert a PDF into LLM-friendly Markdown. `pdf2llm` extracts the text as
Markdown (headings, lists, and tables preserved), pulls images out to disk, and
wraps every page in explicit start/end markers so a coding LLM (e.g. opencode +
Claude) can answer questions like "what's on page 4?".

The Markdown file and all extracted images are written into a single output
directory.

## Install

Requires [uv](https://docs.astral.sh/uv/) and Python 3.11+.

```bash
git clone https://github.com/erdilalbayrak/pdf2llm.git
cd pdf2llm
uv sync
```

## Usage

```bash
uv run pdf2llm <input.pdf> <output_dir> [--quiet] [--json]
```

- `input.pdf` — path to the source PDF. Must exist and end in `.pdf`.
- `output_dir` — directory for the generated `.md` and images. Created if missing.
- `-q`, `--quiet` — suppress progress output (stderr); still print the summary.
- `--json` — print the final summary as a single JSON object instead of text.
- `-h`, `--help` — show help. Invalid arguments also print help (exit code `2`).

### Examples

```bash
# Basic
uv run pdf2llm report.pdf out/

# Quiet (no progress noise), human summary
uv run pdf2llm report.pdf out/ --quiet

# Machine-readable summary for an LLM/automation
uv run pdf2llm report.pdf out/ --quiet --json
```

## Output format

For `report.pdf`, the output directory contains:

- `report.md` — the Markdown.
- `report-p<N>-<idx>.png` — each extracted image, in the same directory.

Each page in the Markdown is wrapped like this:

```markdown
<!-- page: 4 start -->
## Page 4

...page content, including ![](report-p4-1.png) image links...

<!-- page: 4 end -->
```

The `<!-- page: N start -->` / `<!-- page: N end -->` comments are stable
anchors, and the `## Page N` heading is easy for both you and an LLM to
reference.

## Summary fields

The final summary (text or `--json`) reports: `status`, `input`, `output_dir`,
`markdown_file`, `pages`, `images`, `image_files`, `elapsed_seconds`, and
`error` (on failure).

## Exit codes

- `0` — success.
- `2` — argument/validation error (help is printed).
- `1` — runtime conversion error (e.g. a corrupt PDF); the summary reports
  `status: "error"` with a message.

## LLM workflow tip

Point your coding assistant at the generated `.md` and ask page-scoped
questions: "summarize page 3" or "what does the diagram on page 7 show?". The
per-page markers make the boundaries unambiguous.

## Development

```bash
uv run pytest
```
