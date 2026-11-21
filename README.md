# docx_builder

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Version](https://img.shields.io/badge/version-0.10.0-blue)

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

Requirements:

- Python 3.11 or newer and `uv` for the installation commands below.
- macOS and Microsoft Word for PDF export and automatic table-of-contents updates. Building a DOCX without those steps also works on Windows and Linux.
- On first use, Word may ask for access to the fixed temporary DOCX and PDF files; later exports can reuse those grants.

The installer automatically installs `python-docx`, `PyYAML` and `PyMuPDF`. No separate PDF repair extra is required.

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

PyMuPDF is included for automatic PDF table-of-contents link repair.

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

`init` scaffolds a **role-based project structure**: a `report/` directory (with `content.yaml`, `images/`, `assets/`, `output/`, `templates/`), a single conditional `CLAUDE.md`, a `.gitignore` and a `.work/` scratch dir. Add optional layers with `--with brief,references,src,meta,tools,monitor,ai-check` (dependencies auto-resolved), or `--full` for all of them plus the embedded, race-safe `screenshot_intake.py` (the `monitor` layer). `--name` is injected into `CLAUDE.md` and `content.yaml` (it defaults to the directory name); `--cover` writes a cover + TOC `content.yaml` (Shape B). The scaffolder is **idempotent**: re-running only adds what is missing and never overwrites existing files without `--force`. The generated `content.yaml` is a starter with `Replace me.` body text, so you still author the real content for whatever you are building: CV, report, manual, paper, contract, or fiction. `build` resolves `content.yaml` from the project root, falling back to `report/`, so `docx_builder build .` works on a scaffolded project.

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
> **Word PDF ToC hyperlinks.** PDF export checks the generated table of contents and repairs shifted or missing destinations by default. Existing non-ToC links are preserved. Pass `--no-fix-toc-links` to skip this post-processing; `--fix-toc-links` remains supported for compatibility.

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
| `table` | `rows` (or `header`) | `header`, `widths`, `col_align`, `borders`, `style` | Tabular grid; bold header row, per-column `%` widths and alignment, cell shading, bullets-in-cell |

A `table` takes a list of `rows` (each a list of cell values) and an optional bold `header` row:

```yaml
- call: table
  header: [Mês, Vendas, Custos]
  rows:
    - [Janeiro, "10.000", "6.000"]
    - [Fevereiro, "12.500", "7.200"]
  widths: [40, 30, 30]          # optional, % per column, must sum to 100
  col_align: [left, right, right]  # optional, horizontal align per column
  borders: true                  # optional, default true
  style:
    header_fill: "#003366"       # header background
    header_color: "#FFFFFF"      # header text colour (header only)
    stripe_fill: "#EEF3FA"       # zebra background on alternate data rows
    valign: center               # vertical align of every cell
```

All rows must have the same number of cells as the column count. `widths` are percentages of the usable page width (so the table never overflows the margins) and must sum to 100. A cell value with `\n` becomes a line break inside the cell. Set `borders: false` for a borderless grid.

Styling notes:

- **Shading:** `header_fill` paints the header row, `stripe_fill` zebra-stripes alternate data rows (both accept `#RRGGBB` or `RRGGBB`, off by default).
- **Header text:** `header_color` colours the header text only (pair it with a dark `header_fill`); the general `color` key paints every cell.
- **Alignment:** `col_align` overrides alignment per column (great for numbers), `valign` (`top`/`center`/`bottom`) sets the vertical anchor of every cell.
- **Font:** a table has no font of its own — cells inherit the document **body** font (the same one `call: body` uses), so the table always matches the running text. A document built without a cover template uses the blank `python-docx` theme, whose body font is **Cambria (serif)** while headings are Calibri (sans) — so `body`, `bullet` and the table all render serif there (not a table-specific issue). Set `font_family` on the `table` style to override the table's font only, or on `body`/`bullet`/etc. (or start from a modern cover template) to change the whole body.
- **Bullets in a cell:** make a cell a `{bullets: [...]}` mapping and each item becomes a bulleted paragraph inside that cell:

  ```yaml
  rows:
    - ["Features", { bullets: ["fast", "safe", "tested"] }]
  ```

Painting one specific cell, and merging cells, are not supported yet.

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

### Repository layout

The package source tree:

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
│   │   ├── _install.py       # install skill command
│   │   └── _validate.py      # validate command (em/en dash gate)
│   ├── builder.py            # build(), init_project(), has_toc()
│   ├── export.py             # export_pdf() and finalize_source() via Word + JXA (macOS)
│   ├── toc_links.py          # automatic PDF ToC-hyperlink repair via PyMuPDF
│   ├── report.py             # post-build report: words, reading time, em-dash counter
│   ├── validate.py           # content.yaml prose check: em/en dash & other AI-tells
│   ├── scaffold.py           # role-based init scaffolder: layers, idempotence, .gitkeep
│   ├── elements.py           # paragraph primitives (h1, h2, h3, body, bullet, …)
│   ├── figure.py             # figure() and figure_pair() with centred captions
│   ├── pagination.py         # PAGE / NUMPAGES footer
│   ├── renderer.py           # dispatches content.yaml section calls
│   ├── styles.py             # StyleResolver + length/color/align parsing
│   ├── summary.py            # Word TOC field insertion
│   ├── table.py              # table() builder + border utilities
│   ├── skill_installer.py    # logic for `docx_builder install skill`
│   ├── skill/
│   │   └── SKILL.md          # Claude Code skill, shipped as package data
│   └── templates/
│       ├── content.skeleton.yaml      # legacy starter (kept for reference)
│       ├── default_styles.yaml        # built-in style defaults
│       └── scaffold/                  # init templates: CLAUDE.md, .gitignore, content shapes, screenshot_intake
├── docs/
│   └── styles-reference.md   # full style schema (no-AI manual)
├── tests/                    # pytest suite
└── pyproject.toml
```

### A scaffolded project (`docx_builder init`)

`init` creates a **role-based project** where each directory is a role in the pipeline. The base layout is always created:

```
.
├── CLAUDE.md             # context for Claude Code working in this project
├── .gitignore
├── report/               # the build: content.yaml renders into output/
│   ├── content.yaml      #   the document definition (starter, with "Replace me." body)
│   ├── images/           #   rendered figures referenced by content.yaml
│   ├── assets/           #   editable figure sources (svg, xlsx, diagrams)
│   ├── output/           #   generated .docx (and .pdf on macOS)
│   └── templates/        #   cover .docx templates, if any
└── .work/                # transient scratch space (gitignored)
```

Optional layers are added with `--with <names>` (comma-separated) or all at once with `--full`. Dependencies are auto-resolved (e.g. `monitor` pulls in `tools`):

| Layer | Directory | Role |
|-------|-----------|------|
| `brief` | `brief/` | the brief or instructions you are working from |
| `references` | `references/` | reference and source material you consulted |
| `src` | `src/` | your work product: code, data, whatever you produce |
| `meta` | `meta/` | checklist, notes, metadata |
| `tools` | `tools/` | automation scripts (pulled in by `monitor` and `ai-check`) |
| `monitor` | `tools/monitor/` | race-safe `screenshot_intake.py` (pulls `tools`) |
| `ai-check` | `tools/ai-detection/` + `report/ai-check/` | AI-detection drivers, and where their output lands (pulls `tools`) |

Empty directories get a `.gitkeep`. The scaffolder is **idempotent**: re-running only adds what is missing and never overwrites existing files without `--force`. See [Quick start](#quick-start) for `--name` and `--cover`.

<div align="right"><a href="#docx_builder">↑ Back to top</a></div>

---

## CLI reference

```text
docx_builder --version | -v
docx_builder init [DIR] [--full] [--with LAYERS] [--name NAME] [--cover] [--force]
docx_builder build [DIR] [--output FILE] [--template-dir DIR] [--no-finalize] [--pdf] [--no-update-source] [--open] [--fix-toc-links]
docx_builder validate [DIR] [--strict] [--also FILE...]
docx_builder export pdf [DIR] [--input FILE] [--output FILE] [--no-update-source] [--open] [--fix-toc-links]
docx_builder install skill [--scope local|global]
```

- `--version` / `-v` prints the installed version and exits.
- `DIR` defaults to the current working directory.
- `init` scaffolds a role-based project (see [Quick start](#quick-start)). `--full` adds every layer plus the embedded `screenshot_intake.py`; `--with a,b,c` adds named optional layers (deps auto-resolved); `--name` sets the project name; `--cover` writes Shape B; `--force` overwrites existing files instead of skipping them. It is idempotent and never clobbers existing files without `--force`.
- `--output` overrides the YAML `cover.output` and the default pattern (for `build`); for `export pdf` it overrides the destination `.pdf` path.
- `--template-dir` overrides the template lookup directory.
- `validate` parses `content.yaml` and scans only the prose fields (`h1`/`h2`/`h3`, `body`, `bullet`, `caption`, `bold_lead`, `reference`), ignoring keys, paths and filenames. It prints each hit with its section, field and position, and exits 1 when any forbidden character is found (0 when clean), so it can gate a pre-commit hook or CI step. Default rules flag em-dash (`U+2014`), horizontal bar (`U+2015`) and figure dash (`U+2012`); `--strict` adds en-dash (`U+2013`). `--also FILE...` scans extra plain-text/markdown files with the same rules.
- `--no-finalize` (on `build`) skips the Word pass that populates the TOC, keeping `build` pure and fast (useful for CI or scripting on macOS).
- `--pdf` (on `build`) builds then exports to PDF in one shot. Requires macOS + Microsoft Word.
- `export pdf` converts a built `.docx` to PDF via Microsoft Word (macOS only). Input defaults to `build`'s filename resolution; `--input` overrides it. The PDF reports its real page count.
- `--no-update-source` (on `export pdf`, honoured by `build --pdf`) leaves the source `.docx` byte-identical instead of writing back the populated TOC.
- `--open` opens the result after the command finishes: with `--pdf` both the `.pdf` and the finalised `.docx` (in Word), otherwise the `.docx`. macOS-only; elsewhere it prints a note and skips.
- PDF ToC links are repaired by default. `--no-fix-toc-links` skips repair; `--fix-toc-links` is retained for compatibility.

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
