# docx_builder

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Version](https://img.shields.io/badge/version-0.4.0-blue)

> Assemble structured Word documents from a YAML content file (and an optional `.docx` cover template), runnable from any working directory.

Define headings, body text, bullet points, figures, references, and a table of contents in `content.yaml`. Install the tool once, then run `docx_builder build` from any project directory. The package is content-agnostic: it ships no cover templates and no sample content. You bring your own.

## Contents

- [How it works](#how-it-works)
- [Install](#install)
- [Quick start](#quick-start)
- [content.yaml reference](#contentyaml-reference)
- [Styles](#styles)
- [Project structure](#project-structure)
- [CLI reference](#cli-reference)
- [Development](#development)

---

## How it works

1. Create a directory for your document with a `content.yaml` file (and an `images/` folder if you use figures).
2. Run `docx_builder build` from that directory. It reads the YAML, optionally loads a `.docx` cover template (only when `cover.template` is set; nothing is bundled), fills the cover table by row index, and renders every section in order.
3. On macOS with Microsoft Word, `build` finalises the table of contents for you when the document declares one. On Windows or Linux the `.docx` is still generated normally, but the TOC stays as a placeholder — open it in Word and refresh fields (`Ctrl+A`, then `F9`) to populate it. Automatic TOC finalisation and PDF export are macOS-only.

```
content.yaml + images/ ──► docx_builder build ──► <output>.docx
```

Page numbers are added automatically to the `sections:` block. Items in `front_matter:` (cover sheet, TOC) are excluded from the footer counter but still count toward the total.

<div align="right"><a href="#docx_builder">↑ Back to top</a></div>

---

## Install

Install once as a global tool with `uv`, straight from the repository:

```bash
uv tool install git+https://github.com/lipex360x/docx_builder.git
```

Or from a local clone:

```bash
uv tool install .                  # snapshot install
uv tool install --editable .       # live install, source edits propagate without reinstall
```

This registers the `docx_builder` binary in `~/.local/bin/`. Because the package is content-agnostic, provide your own cover `.docx` through `cover.template` or `--template-dir` when you want a cover sheet.

The core install has no PDF post-processing dependency. The opt-in `--fix-toc-links` flag needs the `pdf-links` extra, which adds [PyMuPDF](https://pymupdf.readthedocs.io/):

```bash
uv tool install 'git+https://github.com/lipex360x/docx_builder.git[pdf-links]'
```

To upgrade a **snapshot** install after pulling changes:

```bash
uv tool install --reinstall .
```

> [!TIP]
> An **editable** install (`uv tool install --editable .`) picks up `.py` and bundled-data edits automatically. Reinstall only when `[project.scripts]` entries or dependencies change.

<div align="right"><a href="#docx_builder">↑ Back to top</a></div>

---

## Quick start

### 1. Create a project anywhere

```bash
mkdir -p ~/projects/my-report
cd ~/projects/my-report
docx_builder init
```

`init` writes a tiny marker `content.yaml` (a short comment pointing at the docs and the Claude Code skill). It does **not** scaffold a placeholder document and does **not** create an `images/` folder. You author the real `content.yaml` for whatever you are building: CV, report, manual, paper, contract, or fiction.

### 2. Edit `content.yaml`

```yaml
cover:                                 # optional, omit for a sectionless document
  template: ../templates/MyCover.docx  # your own .docx, nothing is bundled
  output: "Report_{number}.docx"       # placeholders: any string field under cover
  number: "0001"
  rows:                                # one per row of the cover table, in order
    - Project Name
    - Document Title
    - Author Name
    - "0001"
    - "2026-06-15"

styles:                                # optional, overrides built-in defaults
  h1:   { font_size: 16pt, color: "#003366" }
  body: { align: justify }

front_matter:                          # rendered first, no page numbers
  - call: page_break
  - call: toc
    levels: 1-2

sections:                              # rendered after, page numbers start here
  - call: h1
    text: Introduction

  - call: body
    text: This is the opening paragraph.

  - call: figure
    filename: diagram.png
    label: Figure 1.1
    caption: System overview
    width: 5in
```

### 3. Build

```bash
docx_builder build
# Saved: /Users/you/projects/my-report/Report_0001.docx
# Report:
#   Words: 1240
#   Reading time: ~6 min
#   Pages: n/a (known only after export to PDF)
#   Em-dashes (U+2014): 0
```

After saving, `build` prints a short report: word count, estimated reading time (at 200 wpm), a page-count line, and an em-dash (`U+2014`) counter. When em-dashes are present the line is flagged `<- remove before shipping`. The page count is `n/a` for a plain build because only the Word/PDF export path can determine the real count.

Or specify a directory:

```bash
docx_builder build /path/to/some-other-project
```

### 4. The table of contents

When your document declares a `toc` section, `build` finalises it automatically on macOS with Microsoft Word: it drives Word to update every table of contents and all fields, then writes the populated `.docx` back over the source. No manual `F9`, no PDF required.

```bash
docx_builder build --no-finalize    # skip the Word pass, keep build pure and fast
```

> [!NOTE]
> Off macOS or without Word installed, `build` cannot fill the TOC (it is a Word field that only Word can repaginate). It leaves a placeholder, prints a short note, and exits cleanly. On Windows, open the `.docx` in Word and press `Ctrl+A` then `F9` to populate it (`Cmd+A` on macOS). PDF export is macOS-only.

For PDF, the export drives Word for you on macOS:

```bash
docx_builder export pdf
# Exported: /Users/you/projects/my-report/Report_0001.pdf (2 pages)

docx_builder build --pdf            # build then export in one command
docx_builder build --pdf --open     # and open both the PDF and the finalised .docx in Word
```

> [!WARNING]
> The reported page count is read from the actual PDF. The cached `<Pages>` value inside the `.docx` is unreliable and is never trusted.

By default the export also writes the populated TOC back over the source `.docx`, so the source ends finalised. Pass `--no-update-source` to leave it byte-identical, useful when `export pdf --input SomeFile.docx` points at a file you do not want overwritten. `--open` is macOS-only; elsewhere it prints a note and skips.

> [!NOTE]
> **Known Word limitation: ToC hyperlinks in the PDF.** In the exported PDF, the clickable table-of-contents entries can occasionally jump to the heading one entry ahead of the target (clicking an entry lands on the next heading). This is a bug in Word for Mac's Save-as-PDF engine: the generated `.docx` bookmarks are correct, and page numbers and content are unaffected. The bug is rare, so the fix is opt-in: pass `--fix-toc-links` to `export pdf` or `build --pdf` to post-process the PDF and rewrite each ToC link to its heading's real page (it prints `Fixed N ToC link(s)`). This requires the optional `pdf-links` extra (`uv tool install 'docx_builder[pdf-links]'`); the default export path is unchanged and gains no new dependency.

<div align="right"><a href="#docx_builder">↑ Back to top</a></div>

---

## content.yaml reference

Every top-level block is optional. The minimal valid `content.yaml` produces a blank document. Realistic shapes:

### Top-level blocks

| Block | Type | Description |
|-------|------|-------------|
| `cover` | mapping | Optional cover sheet. When omitted, no template is loaded and a blank document is used. |
| `styles` | mapping | Optional visual overrides, see [Styles](#styles). |
| `page_numbers` | bool | Default `true`. Set `false` to disable the footer counter everywhere. |
| `front_matter` | list | Sections rendered first, **without** page numbers (cover sheet items, TOC). |
| `sections` | list | Sections rendered after `front_matter`, **with** page numbers (unless `page_numbers: false`). |

### Cover fields

| Field | Required | Description |
|-------|----------|-------------|
| `template` | no | `.docx` cover template. Absolute path, relative path with separators (anchored at project dir), or bare filename (looked up in `--template-dir`). Omit for a blank document. |
| `output` | no | Output filename pattern. Placeholders are any string field defined under `cover` (e.g. `{number}`, `{name}`). Defaults to `Report_{number}.docx`. |
| `number` | no | Document identifier, exposed as `{number}` to `output`. |
| `rows` | no | Strings filled into the cover table by row index. Row 0 maps to row 0 of the `.docx` table, into the second column. |
| `ai_declaration` | no | Optional paragraph appended after the cover table with a bold "AI Use Declaration:" prefix. |

### Section types

| `call` | Required fields | Optional fields | Description |
|--------|-----------------|-----------------|-------------|
| `page_break` | (none) | (none) | Hard page break |
| `toc` | (none) | `levels` (default `"1-2"`) | Word TOC field, populated by `build` on macOS+Word or via `Cmd+A` then `F9` |
| `h1` / `h2` / `h3` | `text` | `style` | Headings 1 to 3 (default colour is black) |
| `body` | `text` | `style` | Body paragraph |
| `bullet` | `text` | `style` | Bulleted item with configurable glyph |
| `bold_lead` | `bold`, `rest` | `style` | Bullet with bold lead phrase followed by regular text |
| `reference` | `text` | `style` | Hanging-indent paragraph for bibliography entries |
| `figure` | `filename`, `label`, `caption` | `width`, `style`, `caption_style` | Centred image with caption |
| `figure_pair` | `filename1`, `filename2`, `label`, `caption` | `width1`, `width2`, `style`, `caption_style` | Two images side by side |

Any section type may appear in either `front_matter` or `sections`. The distinction is only about page numbering. A `toc` is the exception: it is always unnumbered (kept out of the `PAGE` sequence) wherever you place it, so the body always starts at `PAGE 1`.

### Page numbering, three modes

```yaml
# Mode A: no page numbers anywhere (CVs, one-pagers, fliers)
page_numbers: false

sections:
  - call: h1
    text: Jane Doe
```

```yaml
# Mode B: cover/TOC unnumbered, content numbered (reports)
front_matter:
  - call: page_break
  - call: toc

sections:
  - call: h1
    text: Introduction
```

```yaml
# Mode C: every page numbered (simple paginated docs)
sections:
  - call: h1
    text: Chapter 1
```

> [!NOTE]
> The footer `{total}` placeholder counts the pages of the **numbered body section**, not the whole document, so a report with an unnumbered cover and TOC closes on `N / N` (not `N / N+front-matter`). The body begins on a new page at `PAGE 1`.

> [!NOTE]
> The legacy flag `hide_page_counter: true` on individual sections is **deprecated**: `build` prints a one-time warning when it sees it, and it is scheduled for removal in v0.5. New documents should use the `front_matter:` block instead.

> [!TIP]
> Missing image files do not crash the build. A `[IMAGE NOT FOUND: filename]` placeholder is inserted instead, so you can draft the document before all screenshots are ready.

<div align="right"><a href="#docx_builder">↑ Back to top</a></div>

---

## Styles

Visual properties (font sizes, colors, alignment, spacing, bullet glyph, footer format, and more) are controlled by an optional `styles:` block in `content.yaml`. When the block is absent, the built-in defaults are used.

```yaml
styles:
  h1:     { font_size: 16pt, color: "#003366", bold: true }
  body:   { font_size: 11pt, align: justify }
  bullet: { glyph: "→ " }
  footer: { format: "Page {page} of {total}", align: center }

sections:
  - call: h1
    text: Special heading
    style: { font_size: 20pt }   # inline override wins over the block above
```

Cascade (later wins): built-in defaults, then the `styles:` block, then inline `style:` per section.

Full schema, accepted units, color formats, defaults, and every section type's keys are documented in [`docs/styles-reference.md`](docs/styles-reference.md).

<div align="right"><a href="#docx_builder">↑ Back to top</a></div>

---

## Project structure

```
.
├── docx_builder/
│   ├── __init__.py
│   ├── cli/                  # argparse entry package, one module per subcommand
│   │   ├── __init__.py       # DESCRIPTION + EPILOG + _build_parser() + main()
│   │   ├── _shared.py        # next-step error printers + resolve_directory()
│   │   ├── _build.py         # build command (+ --pdf / --open / --no-finalize / --fix-toc-links)
│   │   ├── _init.py          # init command
│   │   ├── _export.py        # export pdf command (+ --fix-toc-links)
│   │   └── _install.py       # install skill command
│   ├── builder.py            # build(), init_project(), has_toc()
│   ├── export.py             # export_pdf() and finalize_source() via Word + JXA (macOS)
│   ├── toc_links.py          # opt-in PDF ToC-hyperlink repair via PyMuPDF (pdf-links extra)
│   ├── report.py             # post-build report: words, reading time, em-dash counter
│   ├── elements.py           # paragraph primitives (h1, h2, h3, body, bullet, …)
│   ├── figure.py             # figure() and figure_pair() with centred captions
│   ├── pagination.py         # PAGE / NUMPAGES footer
│   ├── renderer.py           # dispatches content.yaml section calls
│   ├── styles.py             # StyleResolver + length/color/align parsing
│   ├── summary.py            # Word TOC field insertion
│   ├── table.py              # table border utilities
│   ├── skill_installer.py    # logic for `docx_builder install skill`
│   ├── skill/
│   │   └── SKILL.md          # Claude Code skill, shipped as package data
│   └── templates/
│       ├── content.skeleton.yaml      # used by `docx_builder init`
│       └── default_styles.yaml        # built-in style defaults
├── docs/
│   └── styles-reference.md   # full style schema (no-AI manual)
├── tests/                    # pytest suite
└── pyproject.toml
```

<div align="right"><a href="#docx_builder">↑ Back to top</a></div>

---

## CLI reference

```text
docx_builder init [DIR] [--force]
docx_builder build [DIR] [--output FILE] [--template-dir DIR] [--no-finalize] [--pdf] [--no-update-source] [--open] [--fix-toc-links]
docx_builder export pdf [DIR] [--input FILE] [--output FILE] [--no-update-source] [--open] [--fix-toc-links]
docx_builder install skill [--scope local|global]
```

- `DIR` defaults to the current working directory.
- `--output` overrides the YAML `cover.output` and the default pattern (for `build`); for `export pdf` it overrides the destination `.pdf` path.
- `--template-dir` overrides the template lookup directory.
- `--no-finalize` (on `build`) skips the Word pass that populates the TOC, keeping `build` pure and fast (useful for CI or scripting on macOS).
- `--pdf` (on `build`) builds then exports to PDF in one shot. Requires macOS + Microsoft Word.
- `export pdf` converts a built `.docx` to PDF via Microsoft Word (macOS only). Input defaults to `build`'s filename resolution; `--input` overrides it. The PDF reports its real page count.
- `--no-update-source` (on `export pdf`, honoured by `build --pdf`) leaves the source `.docx` byte-identical instead of writing back the populated TOC.
- `--open` opens the result after the command finishes: with `--pdf` both the `.pdf` and the finalised `.docx` (in Word), otherwise the `.docx`. macOS-only; elsewhere it prints a note and skips.
- `--fix-toc-links` (on `export pdf`, honoured by `build --pdf`) post-processes the PDF to repair ToC hyperlinks that Word's PDF engine shifted. Off by default; needs the optional `pdf-links` extra (`uv tool install 'docx_builder[pdf-links]'`).

<div align="right"><a href="#docx_builder">↑ Back to top</a></div>

---

## Development

After cloning, bootstrap once:

```bash
uv sync
pre-commit install                       # activates dev-quality on every commit
```

Then the standard workflow:

```bash
uv run pytest
uv run ruff check docx_builder tests
uv run --with mypy mypy docx_builder
pre-commit run --all-files               # run all dev-quality checkers manually
```

> [!IMPORTANT]
> The `pre-commit install` step writes `.git/hooks/pre-commit`. Without it, the hook config in `.pre-commit-config.yaml` is inert and `git commit` bypasses every quality check. Never bypass the hooks with `--no-verify`.

All features follow **Red, Green, Refactor** TDD. Write a failing test first, implement the minimum code to pass it, then clean up.

<div align="right"><a href="#docx_builder">↑ Back to top</a></div>
