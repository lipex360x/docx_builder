---
name: docx_builder
description: Generate DOCX reports (and export them to PDF) from a content.yaml file. Use this skill when the user asks to create, build, or edit a DOCX document via docx_builder, export/convert a built .docx to PDF, open the result in Word, discusses content.yaml structure, asks about styles cascade or page numbering, references heading/body/bullet/figure/toc sections, or wants to install the skill itself. Triggers on "docx_builder", "content.yaml", "build report", "scaffold report", "edit styles", "export pdf", "build --pdf", "convert to pdf", "--open".
---

# docx_builder skill

This skill helps you operate the `docx_builder` CLI tool efficiently and correctly.

## What docx_builder does

It takes a `content.yaml` describing a document (optional cover, optional front matter, sections, styles) and produces a `.docx`. Cover template is optional — when omitted, a blank `Document` is used.

Repo: <https://github.com/lipex360x/docx_builder>. Installable globally via `uv tool install`.

## When to use this skill

- The user wants to create or regenerate a `.docx` from a YAML description.
- The user is editing `content.yaml` (cover, front_matter, sections, styles).
- The user asks about heading sizes, bullet glyphs, footer format, page numbers, image captions, TOC, or any visual aspect of the generated `.docx`.

If the request is **not** about generating/editing docs through this tool, do not invoke this skill.

## Core workflow

```bash
docx_builder --version        # print the installed version and exit (-v alias)
docx_builder init             # scaffold a role-based project (report/ + CLAUDE.md + .gitignore + .work/)
docx_builder init --full      # scaffold every layer + embedded screenshot_intake.py
docx_builder init --with references,src   # base + named optional layers (deps auto-resolved)
docx_builder init --cover     # content.yaml with cover + TOC (Shape B)
docx_builder build            # build using content.yaml in cwd (falls back to report/content.yaml)
docx_builder build /path/dir  # build from another directory
docx_builder build --output Custom.docx
docx_builder build --template-dir ~/templates
docx_builder build --no-finalize  # skip the Word TOC-finalize pass (pure/fast; CI)
docx_builder build --pdf      # build then export to PDF in one shot (macOS + Word)
docx_builder build --open     # build, then open the .docx (macOS)
docx_builder build --pdf --open  # build, export, then open BOTH the .pdf and the .docx in Word (macOS)
docx_builder validate         # fail (exit 1) on em/en dash & AI-tells in content.yaml prose
docx_builder validate --strict   # also flag en-dash (U+2013)
docx_builder export pdf       # convert the built .docx to PDF (macOS + Word)
docx_builder export pdf --no-update-source  # do not write the populated TOC back over the source
docx_builder export pdf --open  # convert then open both the .pdf and the finalized .docx in Word (macOS)
docx_builder export pdf --fix-toc-links  # opt-in: repair ToC hyperlinks Word's PDF engine shifted
```

As of v0.8, `init` scaffolds a **role-based project structure**, not a marker file. Base `init` creates `report/` (with `content.yaml`, `images/`, `assets/`, `output/`, `templates/`) plus a single conditional `CLAUDE.md`, a `.gitignore` and a `.work/` scratch dir. `--with LAYERS` adds optional layers (`brief`, `references`, `src`, `meta`, `tools`, `monitor`, `ai-check`; deps auto-resolved, so `monitor`/`ai-check` pull `tools`), `--full` adds them all plus a generic embedded `screenshot_intake.py` (the `monitor` layer: a cross-platform, race-safe PNG intake; the generated `CLAUDE.md` tells you to stop its watch loop once the document is done), `--name` is injected into `CLAUDE.md` and `content.yaml` (defaulting to the directory name), and `--cover` writes Shape B. The scaffolder is **idempotent and additive**: re-running only fills gaps and never overwrites existing files without `--force`. The `ai-check` layer scaffolds the directories plus a README only (no detector scripts). The generated `content.yaml` is a Shape A (or Shape B) starter with `Replace me.` body text, so you (the assistant) still author the real content for whatever the user is building (CV, report, manual, paper, contract, fiction).

### Scaffolded project layout — what each directory is for

`init` builds a role-based project where each directory is a role in the pipeline. The base layout is always created; optional layers are added with `--with <names>` (comma-separated) or `--full`. Dependencies auto-resolve (e.g. `monitor` pulls `tools`).

| Directory | Created by | Role |
|---|---|---|
| `report/` | base | the build: `content.yaml` renders into `output/` |
| `report/images/` | base | rendered figures referenced by `content.yaml` |
| `report/assets/` | base | editable figure sources (svg, xlsx, diagrams) |
| `report/output/` | base | generated `.docx` (and `.pdf` on macOS) |
| `report/templates/` | base | cover `.docx` templates, if any |
| `.work/` | base | transient scratch space (gitignored) |
| `brief/` | `--with brief` | the brief or instructions you are working from |
| `references/` | `--with references` | reference and source material you consulted |
| `src/` | `--with src` | your work product: code, data, whatever you produce |
| `meta/` | `--with meta` | checklist, notes, metadata |
| `tools/` | `--with tools` | automation scripts (pulled in by `monitor` and `ai-check`) |
| `tools/monitor/` | `--with monitor` | race-safe `screenshot_intake.py` PNG intake (pulls `tools`) |
| `tools/ai-detection/` + `report/ai-check/` | `--with ai-check` | AI-detection drivers, and where their output lands (pulls `tools`) |

The generated `CLAUDE.md` carries this same per-directory legend, so a fresh Claude Code session opened inside a scaffolded project reads the roles directly. The root `CLAUDE.md` is conditional: it documents every possible layer and tells you to check which directories are actually present.

`build`, `validate` and the export path resolve `content.yaml` from the given directory, falling back to its `report/` subdirectory, so `docx_builder build .` works on a scaffolded project (where `content.yaml` lives under `report/`). A root-level `content.yaml` still takes precedence.

After every `build`, the CLI prints a short report: word count, estimated reading time (200 wpm), a page-count line (always `n/a` for a plain build — the real count is only known after the Word/PDF export), and an em-dash (`U+2014`) counter. When em-dashes are present the line is flagged `<- remove before shipping`. The user actively dislikes em-dashes: when authoring `content.yaml`, do not introduce `U+2014` characters, and if the report flags any, locate and replace them. The report only counts and flags — it never strips automatically.

`docx_builder build` uses `python-docx`, which is not a renderer and cannot populate a TOC on its own. To fill the TOC and its page numbers something must drive Microsoft Word. As of v0.4, **`build` does this automatically by default**: when the document declares a `toc` section, after writing the `.docx` `build` drives Word (macOS + Microsoft Word) to update every table of contents and all fields, then writes the populated `.docx` back over the source — no manual F9, no PDF. TOC-less documents (CVs, one-pagers) never launch Word, so they cost nothing extra. If the environment is not macOS or Word is not installed, `build` does not error: it leaves the placeholder TOC field in place, prints a short `note:` to stderr, and exits 0 — open the `.docx` in Word and press `Cmd+A` then `F9`, or run `docx_builder export pdf`. Pass `--no-finalize` to skip the Word pass entirely (useful for CI/scripting on macOS where launching Word is undesirable). The `--pdf` path finalizes via the export step (see below) and does not double-launch Word.

## PDF export (macOS + Microsoft Word)

```bash
docx_builder export pdf [DIR] [--input FILE] [--output FILE] [--no-update-source] [--open] [--fix-toc-links]
docx_builder build [DIR] [--no-finalize] [--pdf] [--no-update-source] [--open] [--fix-toc-links]
```

- Input defaults to the same filename `build` would produce (`cover.output` template → default pattern); override with `--input`.
- Output defaults to `<input>.pdf`; override with `--output`.
- Requires macOS and Microsoft Word. Uses Word via JavaScript for Automation (JXA): it updates every table of contents and all fields, then saves, so the TOC and page numbers render correctly in the PDF.
- **By default the export finalises the source `.docx`.** Word's `document.save()` persists the populated TOC into the scratch copy, and Python then moves that scratch copy back over the source input path — so the source ends with a filled TOC and no manual F9. This is the default (no flag). Hard constraint: this is the only way the TOC gets populated; a plain `build` cannot do it because `python-docx` is not a renderer.
- `--no-update-source` opts out: the source `.docx` is left byte-identical to the pre-export input, and only the PDF is produced. Use it when `export pdf --input SomeUserFile.docx` points at a file you must not overwrite.
- `--open` opens the result when the command finishes. With `--pdf` / `export pdf` it opens **both** the `.pdf` (default viewer) and the finalized `.docx` (in Microsoft Word, via `open -a`); a plain `build --open` opens just the `.docx`. macOS-only; on other platforms it prints `note: --open is currently macOS-only` and skips without erroring.
- A defensive strip removes the legacy `"Note: open in Microsoft Word…"` paragraph from the scratch copy before conversion, so old `--input` documents that still carry it do not leak it into the PDF or the finalised source. Freshly built documents no longer emit that note at all.
- The PDF is first written to a stable scratch directory (`~/Library/Caches/docx_builder/exports/`) then moved to the requested path, so Word's Files & Folders permission prompt only fires once, ever. The write-back to the source is a plain Python move and needs no Word grant.
- After export it prints the real page count: `Exported: <path> (<N> pages)`.
- `--fix-toc-links` (opt-in, off by default) post-processes the exported PDF to correct table-of-contents hyperlinks. Word for Mac's PDF engine occasionally writes some ToC bookmark destinations shifted one entry ahead, so clicking a ToC entry in the PDF lands on the next heading (the `.docx` itself is correct). The flag repairs the PDF's xref, finds the ToC page, and rewrites each ToC link to its heading's real page, printing `Fixed N ToC link(s)`. It needs the optional `pdf-links` extra (`uv tool install 'docx_builder[pdf-links]'`); without it the command raises a clear install hint. Only suggest this flag when a user reports ToC links jumping to the wrong heading in the PDF — it is rare.

**Never trust `docProps/app.xml`'s `<Pages>` for the page count.** `python-docx` writes whatever was cached at the last serialisation — it is not recalculated and is routinely wrong (e.g. reports 1 page when Word renders 2). The PDF export path is the only reliable way to learn the true page count.

Errors are actionable and exit 1: non-macOS → `"PDF export requires macOS + Microsoft Word"`; Word not installed → points at the missing application; input `.docx` missing → names the resolved path.

## Validating prose (em/en dash gate)

```bash
docx_builder validate [DIR] [--strict] [--also FILE...]
```

`validate` parses `content.yaml` and scans **only the prose fields** (`h1`/`h2`/`h3`, `body`, `bullet`, figure `caption`, `bold_lead` bold + rest, `reference`), ignoring keys, paths and filenames so a hyphen in a filename or a key never trips it. It prints each hit with its section, field and position, and exits 1 if any are found (0 when clean), so it can gate a pre-commit hook or CI step. Default rules flag em-dash (`U+2014`), horizontal bar (`U+2015`) and figure dash (`U+2012`); `--strict` adds en-dash (`U+2013`), recommended for prose. `--also FILE...` runs the same check over extra plain-text/markdown files such as a brief.

This is the **gateable** counterpart to the post-build report: `build` only counts em-dashes and never fails, while `validate` exits non-zero so the no-em-dash rule can be enforced. When the user wants to keep a document clean of em-dashes, wire `docx_builder validate --strict` into their pre-commit or CI rather than relying on the build-time warning alone.

## content.yaml structure

Every top-level block is optional. The minimal valid `content.yaml` is empty (produces a blank document). Realistic shapes:

### Shape A — simple document (no cover, no page numbers)

Best for CVs, one-pagers, fliers, anything that doesn't need a cover sheet or page numbering.

```yaml
page_numbers: false

styles:
  h1: { font_size: 18pt, color: "#003366" }
  body: { align: justify }

sections:
  - call: h1
    text: Jane Doe
  - call: body
    text: Software engineer with 10 years of experience.
  - call: h2
    text: Experience
  - call: bullet
    text: Senior engineer at Acme (2022–present)
```

### Shape B — report with cover and TOC

Best for academic submissions, formal reports, anything with a cover page followed by paginated content.

```yaml
cover:
  template: ../templates/MyCover.docx     # relative to project dir, or absolute, or bare filename
  output: "Report_{number}.docx"           # placeholders: any string field under cover
  number: "0001"
  rows:                                    # one entry per row of the cover table, in order
    - Document Title
    - Author
    - "0001"
    - "Submission Date"

styles:
  h1:     { font_size: 16pt, color: "#003366" }
  body:   { align: justify }
  footer: { format: "Page {page} of {total}" }

front_matter:                              # rendered first; no page numbers on these pages
  - call: page_break
  - call: toc
    levels: 1-2

sections:                                  # rendered after; page numbers start here
  - call: h1
    text: Introduction

  - call: body
    text: Opening paragraph.

  - call: figure
    filename: diagram.png
    label: Figure 1.1
    caption: System overview
    width: 5in
```

### Shape C — fully paginated document

If you don't need a cover and you want page numbers on every section, just use `sections:` alone. No `front_matter`, no `page_numbers: false`. The footer appears on every page.

## Section types — complete list

| `call` | Required fields | Optional fields |
|---|---|---|
| `page_break` | — | — |
| `toc` | — | `levels` (default `1-2`) |
| `h1` / `h2` / `h3` | `text` | `style` |
| `body` | `text` | `style` |
| `bullet` | `text` | `style` |
| `bold_lead` | `bold`, `rest` | `style` |
| `reference` | `text` | `style` |
| `figure` | `filename`, `label`, `caption` | `width`, `style`, `caption_style` |
| `figure_pair` | `filename1`, `filename2`, `label`, `caption` | `width1`, `width2`, `style`, `caption_style` |
| `table` | `rows` (or `header`) | `header`, `widths`, `col_align`, `borders`, `style` |

### `table` section

A tabular grid. `rows` is a list of rows, each a list of cell values; `header` (optional) is a single bold header row.

```yaml
- call: table
  header: [Column A, Column B, Column C]   # optional bold header row
  rows:
    - [a1, b1, c1]
    - [a2, b2, c2]
  widths: [25, 45, 30]                      # optional, % per column, must sum to 100
  col_align: [left, right, right]           # optional, horizontal align per column
  borders: true                            # optional, default true
  style:                                    # optional style overrides
    header_fill: "#003366"                  # header background colour
    header_color: "#FFFFFF"                 # header text colour (header only)
    stripe_fill: "#EEF3FA"                  # zebra background on alternate data rows
    valign: center                          # vertical align of every cell
```

Rules to honour when authoring a `table`:

- Every row must have the same number of cells as the column count (the count comes from `header` when present, else from the first row). A ragged row raises a build error.
- `widths` (optional) are percentages of the **usable page width** (page width minus margins), so the table can never overflow the margins. They must have one entry per column and sum to 100.
- `borders` defaults to `true` (single-line borders, drawn via OXML so it does not depend on a "Table Grid" style in the cover template). Set `false` for a borderless grid.
- A cell value containing `\n` becomes a line break inside that cell.
- The `table` style key defaults to `font_size: 10pt`, `header_bold: true`, `align: left`. Set `header_bold: false` to keep the header plain.
- **Font — important, read this before "fixing" a serif table.** A table has **no font of its own**: its cells inherit the document **body** font, i.e. the exact same font a `call: body` paragraph uses. The table is therefore always consistent with the running text. Two consequences:
  - A document built **without a cover template** uses `python-docx`'s blank template, whose theme sets the **body font to Cambria (serif)** and the **heading font to Calibri (sans)**. So `body`, `bullet` **and** the table all render serif, while `h1`/`h2`/`h3` render sans. The table looking serif next to a sans heading is **not** a table bug — the whole body is serif. (Verify with `export pdf` + PyMuPDF: `body`, `bullet` and table cells all report `Cambria`.)
  - A document built **with a cover template** inherits that template's theme, so if the cover was made in modern Word the body (and the table) are sans.
  - To force a specific font for the table only, set `font_family` on the `table` style (e.g. `style: { font_family: "Arial" }` → the whole table renders Arial). To change the font of the **whole document body**, set `font_family` on `body`/`bullet`/etc. in the `styles:` block, or start from a cover template with the theme you want. Do not try to "fix" only the table when the real cause is the document's body font.
- **Cell shading:** `header_fill` paints the header row, `stripe_fill` zebra-stripes alternate data rows (the 2nd, 4th, … data row; the header is never striped). Both are style keys, opt-in (no fill by default), and accept `#RRGGBB` or `RRGGBB`. Painting one specific cell, and merging cells, are not supported yet.
- **Header text colour:** `header_color` (style key) sets the text colour of the header row only — use it with a dark `header_fill` so the header text stays legible (e.g. white on navy) while the body keeps the normal `color`. Do not set `color` to white expecting only the header to change — `color` paints every cell.
- **Alignment:** `col_align` (section-level list, one entry per column, `left`/`center`/`right`/`justify`) overrides the style `align` column by column — ideal for right-aligning numeric columns. `valign` (style key, `top`/`center`/`bottom`) sets the vertical anchor of every cell; it is only visible when a row is taller than its content (e.g. a multiline cell next to short ones).
- **Bullets inside a cell:** a cell value may be a `{bullets: [...]}` mapping instead of a string; each list item becomes its own bulleted paragraph inside that cell (glyph from the `glyph` style key, default `"• "`). Example: `rows: [["Features", { bullets: ["fast", "safe", "tested"] }]]`. `validate` scans bullet item text for forbidden characters just like normal cells.
- `docx_builder validate` scans table cell prose (header + every row cell) for em/en-dashes and AI-tells, just like `body`/`caption`. Do not introduce `U+2014` in table cells.

Any section may appear in either `front_matter` or `sections`. The distinction is only about page numbering. **Exception:** a `toc` is always treated as front matter (footer cleared, kept out of the `PAGE` sequence) wherever you place it, so the body always starts at `PAGE 1` even if you list the `toc` under `sections:`.

## Page numbering — three modes

| Goal | YAML |
|---|---|
| No page numbers anywhere | `page_numbers: false` (top-level) |
| Cover/TOC unnumbered, content numbered | Put cover/TOC items in `front_matter:`; content in `sections:` (a `toc` is unnumbered automatically wherever you put it) |
| Every page numbered | Use `sections:` only (no `front_matter`, no `page_numbers: false`) |

The footer reads `{page} / {total}` where `{total}` is the count of pages in the **numbered body section** (Word's `SECTIONPAGES` field), not the whole document. So a report with an unnumbered cover and TOC closes on `N / N`, not `N / N+front-matter`. The body always begins on a new page at `PAGE 1`. If the first item of `sections` is a `page_break` (a common idiom to push the body past the front matter), it is absorbed by the section break — the body does not start with a blank page.

### Legacy: `hide_page_counter`

The flag `hide_page_counter: true` on individual section items still works but is **deprecated**: `build` prints a one-time `warning:` to stderr when it sees it, and it is scheduled for removal in v0.5. Use the `front_matter` block instead — it makes intent explicit and avoids repetition. (The undocumented `DOCX_BUILDER_NO_DEPRECATION=1` env var silences the warning for advanced users.)

## Styles — cascade and editing

> Headings (`h1`/`h2`/`h3`) default to black (`color: "#000000"`) — they no longer inherit Word's built-in blue. Do **not** suggest `color: "#000000"` as a workaround; it is already the default. Override to another colour via `styles:` as usual.

Order of precedence (later wins):

1. Built-in defaults — `docx_builder/templates/default_styles.yaml`
2. `styles:` block in user's `content.yaml`
3. `style:` key inline on a single section

Length units accepted: `pt`, `in`, `cm`, `mm`. Colors: `#RRGGBB` (with or without `#`). Alignment: `left` / `center` / `right` / `justify`.

For the complete schema of every style key, see [`docs/styles-reference.md`](../../docs/styles-reference.md). When editing styles, always reference that file — it is the authoritative no-AI manual.

### Common style adjustments

```yaml
# Change global heading size and color
styles:
  h1: { font_size: 18pt, color: "#003366" }

# One-off override on a single heading
- call: h1
  text: Hero title
  style: { font_size: 28pt, align: center }

# Different bullet marker
styles:
  bullet: { glyph: "– " }

# Footer that says "Page X of Y"
styles:
  footer: { format: "Page {page} of {total}" }

# Justified body, sans-serif font
styles:
  body: { font_family: "Arial", align: justify }
```

## Common errors and how to fix them

| Error | Cause | Fix |
|---|---|---|
| `content.yaml not found in <dir>` | Wrong cwd, or `init` was never run | `cd` into the project dir, or run `docx_builder init` |
| `cover template not found: <name>` | Path in `cover.template` doesn't resolve | Use an absolute path, a relative path with `/`, or place the file in `--template-dir` |
| `unknown call: '<x>'` | Section dict has an unrecognised `call` value | Use a value from the section types table above |
| TOC is empty or shows the wrong pages | `build` finalizes the TOC by default, but the pass was skipped: `--no-finalize` was passed, or the environment is not macOS + Microsoft Word (a `note:` was printed to stderr) | Re-run `build` on macOS with Word and without `--no-finalize`, or open the `.docx`, `Cmd+A` then `F9`, or run `docx_builder export pdf` / `build --pdf` |
| Image missing in output | `figure.filename` not under `<project_dir>/images/` | Place the image under `images/`, or rename to match |

## Output filename pattern

The output filename comes from one of these, in priority:

1. `--output FILE` CLI flag
2. `cover.output` template string (e.g. `"Report_{number}.docx"`) — placeholders are any string field under `cover`
3. Default: `Report_{number}.docx` (or `Report.docx` if no `number`)

## Working from any directory

The tool resolves the project from `cwd` (or the positional `DIR` argument). The template file is resolved as:

1. Absolute path in `cover.template` → use as-is
2. Relative path with separators → resolved relative to project dir (e.g. `../templates/Cover.docx`)
3. Bare filename → looks in `--template-dir`, then in the package's bundled templates (`docx_builder/templates/`)

The bundled templates intentionally do **not** contain assignment-specific covers — they ship `content.skeleton.yaml` and `default_styles.yaml` only. Provide your own cover `.docx` via `cover.template` or `--template-dir`.

## Updating this skill

The skill source lives in this repo at `docx_builder/skill/SKILL.md`. The global copy at `~/www/claude/.brain/skills/docx_builder/SKILL.md` is a real file that must be re-synced after edits:

```bash
cp docx_builder/skill/SKILL.md ~/www/claude/.brain/skills/docx_builder/SKILL.md
```

Or for a local-project install:

```bash
docx_builder install skill --scope local --force
```
