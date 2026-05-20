# docx_builder

> Assemble structured Word documents from a YAML content file and a `.docx` cover template — from any working directory.

Define headings, body text, bullet points, figures, references, and a table of contents in `content.yaml`. Install the tool once, then run `docx_builder build` from any project directory.

## Contents

- [How it works](#how-it-works)
- [Install](#install)
- [Quick start](#quick-start)
- [content.yaml reference](#contentyaml-reference)
- [Styles](#styles)
- [Project structure](#project-structure)
- [Development](#development)

---

## How it works

1. Create a directory for your document with a `content.yaml` file and an `images/` folder.
2. Run `docx_builder build` from that directory — it reads the YAML, loads a `.docx` cover template (bundled with the package by default), fills the cover table by row index, and renders every section in order.
3. Open the output `.docx` in Microsoft Word and refresh fields to finalise the TOC.

```
content.yaml + images/ ──► docx_builder build ──► <output>.docx
```

Page numbers are added automatically to all sections. Sections marked with `hide_page_counter: true` still count toward the total page count but do not display the number in the footer.

<div align="right"><a href="#docx_builder">↑ Back to top</a></div>

---

## Install

Install once as a global tool with `uv`:

```bash
uv tool install /path/to/docx_builder
```

This registers the `docx_builder` binary in `~/.local/bin/`. The package ships with `CA Cover Sheet.docx` as the default template, so it works from any directory without extra setup.

To upgrade after pulling changes:

```bash
uv tool install --reinstall /path/to/docx_builder
```

<div align="right"><a href="#docx_builder">↑ Back to top</a></div>

---

## Quick start

### 1. Create a project anywhere

```bash
mkdir -p ~/projects/my-report
cd ~/projects/my-report
docx_builder init
```

`init` scaffolds a `content.yaml` skeleton and an empty `images/` folder in the current directory.

### 2. Edit `content.yaml`

```yaml
cover:                                 # optional — omit for a sectionless document
  output: "Report_{number}.docx"       # placeholders: any string field under cover
  number: "0001"
  rows:                                # one per row of the cover table, in order
    - Project Name
    - Document Title
    - Author Name
    - "0001"
    - "2026-06-15"

styles:                                # optional — overrides built-in defaults
  h1:   { font_size: 16pt, color: "#003366" }
  body: { align: justify }

sections:
  - call: page_break
    hide_page_counter: true

  - call: toc
    levels: 1-2

  - call: page_break

  - call: h1
    text: Introduction

  - call: body
    text: This is the opening paragraph.

  - call: figure
    filename: diagram.png
    label: Figure 1.1
    caption: System architecture overview
```

### 3. Build

```bash
docx_builder build
# Saved: /Users/you/projects/my-report/Report_0001.docx
```

Or specify a directory:

```bash
docx_builder build /path/to/some-other-project
```

### 4. Finalise the TOC in Word

Open the generated `.docx`, press `Cmd+A` (or `Ctrl+A`) then `F9` to refresh fields.

<div align="right"><a href="#docx_builder">↑ Back to top</a></div>

---

## content.yaml reference

### Cover fields

| Field | Required | Description |
|-------|----------|-------------|
| `template` | yes | Filename of the `.docx` cover template. Defaults to `CA Cover Sheet.docx` (bundled). Use an absolute path, or pass `--template-dir` to point at a custom location. |
| `output` | no | Output filename pattern. Supports `{number}`, `{name}`, and any string field defined under `cover`. Defaults to `CA_Report_{number}.docx`. |
| `number` | yes | Document identifier — used in the default output filename and exposed as `{number}` to `output`. |
| `rows` | yes | Strings filled into the cover table, one per row, in order. |
| `ai_declaration` | no | When present, appended after the cover table with a bold "AI Use Declaration:" prefix. |

> [!NOTE]
> `rows` maps directly to table rows by index. Row 0 in the YAML fills row 0 in the `.docx` cover table. Adapt the list to match the number of rows in your own template.

### Section types

| `call` | Required fields | Optional fields | Description |
|--------|-----------------|-----------------|-------------|
| `toc` | — | `levels` (default `"1-2"`) | Word TOC field — update in Word with `Cmd+A` → `F9` |
| `h1` | `text` | — | Heading 1 — 14 pt, bold |
| `h2` | `text` | — | Heading 2 — 12 pt, bold |
| `h3` | `text` | — | Heading 3 — 11 pt, bold |
| `body` | `text` | — | Body paragraph — 11 pt |
| `bullet` | `text` | — | Bulleted item with `•` prefix and 0.3 in left indent |
| `bold_lead` | `bold`, `rest` | — | Bullet with a bold lead phrase followed by regular text |
| `reference` | `text` | — | Hanging-indent paragraph for bibliography entries |
| `page_break` | — | — | Inserts a hard page break |
| `figure` | `filename`, `label`, `caption` | — | Centred image with bold label and italic caption |
| `figure_pair` | `filename1`, `filename2`, `label`, `caption` | — | Two images side-by-side in a borderless table |

Every section type accepts the optional key `hide_page_counter: true`.

### Page number visibility (`hide_page_counter`)

```yaml
sections:
  - call: page_break
    hide_page_counter: true   # footer hidden — page still counted

  - call: toc
    levels: 1-2
    hide_page_counter: true

  - call: page_break          # first section without the flag — page numbers start here
  - call: h1
    text: Introduction
```

When at least one section has `hide_page_counter: true`, the renderer inserts a continuous section break at the first section without the flag. Sections before the break have an empty footer; sections after show `page / total` right-aligned at 9 pt.

> [!TIP]
> Missing image files do not crash the build — a `[IMAGE NOT FOUND: filename]` placeholder is inserted instead. This lets you draft the document before all screenshots are ready.

<div align="right"><a href="#docx_builder">↑ Back to top</a></div>

---

## Styles

Visual properties (font sizes, colors, alignment, spacing, bullet glyph, footer format, …) are controlled by an optional `styles:` block in `content.yaml`. When the block is absent, the built-in defaults are used.

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

Cascade: built-in defaults → `styles:` block → inline `style:` per section.

Full schema, accepted units, color formats, defaults, and every section type's keys are documented in [`docs/styles-reference.md`](docs/styles-reference.md).

<div align="right"><a href="#docx_builder">↑ Back to top</a></div>

---

## CLI reference

```text
docx_builder init [DIR] [--force]
docx_builder build [DIR] [--output FILE] [--template-dir DIR]
```

- `DIR` defaults to the current working directory.
- `--output` overrides both the YAML `cover.output` and the default pattern.
- `--template-dir` overrides the template lookup directory (otherwise the bundled `docx_builder/templates/` is used).

<div align="right"><a href="#docx_builder">↑ Back to top</a></div>

---

## Project structure

```
.
├── docx_builder/
│   ├── __init__.py
│   ├── cli.py             # docx_builder entry point (build / init)
│   ├── builder.py         # build() and init_project()
│   ├── elements.py        # Paragraph primitives (h1, h2, h3, body, bullet, …)
│   ├── figure.py          # figure() and figure_pair() with centred captions
│   ├── pagination.py      # PAGE / NUMPAGES footer added to content sections
│   ├── renderer.py        # Dispatches content.yaml section calls
│   ├── summary.py         # Word TOC field insertion
│   ├── table.py           # Table border utilities
│   └── templates/
│       ├── CA Cover Sheet.docx        # Default cover template
│       └── content.skeleton.yaml      # Used by `docx_builder init`
├── tests/                 # pytest suite
└── pyproject.toml
```

<div align="right"><a href="#docx_builder">↑ Back to top</a></div>

---

## Development

After cloning, bootstrap once:

```bash
uv sync
pre-commit install                       # ← activates dev-quality on every commit
```

Then standard workflow:

```bash
uv run pytest
uv run ruff check docx_builder tests
uv run mypy docx_builder
pre-commit run --all-files               # run all dev-quality checkers manually
```

The `pre-commit install` step writes `.git/hooks/pre-commit`. Without it, the hook config in `.pre-commit-config.yaml` is inert and `git commit` bypasses every quality check.

All features follow **Red → Green → Refactor** TDD. Write a failing test first, implement the minimum code to pass it, then clean up.

<div align="right"><a href="#docx_builder">↑ Back to top</a></div>
