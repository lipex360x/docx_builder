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
docx_builder init             # writes a marker content.yaml in cwd (3-line comment, nothing else)
docx_builder build            # build using content.yaml in cwd
docx_builder build /path/dir  # build from another directory
docx_builder build --output Custom.docx
docx_builder build --template-dir ~/templates
docx_builder build --no-finalize  # skip the Word TOC-finalize pass (pure/fast; CI)
docx_builder build --pdf      # build then export to PDF in one shot (macOS + Word)
docx_builder build --open     # build, then open the .docx (macOS)
docx_builder build --pdf --open  # build, export, then open BOTH the .pdf and the .docx in Word (macOS)
docx_builder export pdf       # convert the built .docx to PDF (macOS + Word)
docx_builder export pdf --no-update-source  # do not write the populated TOC back over the source
docx_builder export pdf --open  # convert then open both the .pdf and the finalized .docx in Word (macOS)
```

`init` does NOT scaffold a placeholder document. It only writes a tiny marker file pointing back at this skill. You (the assistant) are expected to author the real `content.yaml` based on what the user actually wants to build — CV, report, manual, paper, contract, fiction — each gets a tailored YAML.

After every `build`, the CLI prints a short report: word count, estimated reading time (200 wpm), a page-count line (always `n/a` for a plain build — the real count is only known after the Word/PDF export), and an em-dash (`U+2014`) counter. When em-dashes are present the line is flagged `<- remove before shipping`. The user actively dislikes em-dashes: when authoring `content.yaml`, do not introduce `U+2014` characters, and if the report flags any, locate and replace them. The report only counts and flags — it never strips automatically.

`docx_builder build` uses `python-docx`, which is not a renderer and cannot populate a TOC on its own. To fill the TOC and its page numbers something must drive Microsoft Word. As of v0.4, **`build` does this automatically by default**: when the document declares a `toc` section, after writing the `.docx` `build` drives Word (macOS + Microsoft Word) to update every table of contents and all fields, then writes the populated `.docx` back over the source — no manual F9, no PDF. TOC-less documents (CVs, one-pagers) never launch Word, so they cost nothing extra. If the environment is not macOS or Word is not installed, `build` does not error: it leaves the placeholder TOC field in place, prints a short `note:` to stderr, and exits 0 — open the `.docx` in Word and press `Cmd+A` then `F9`, or run `docx_builder export pdf`. Pass `--no-finalize` to skip the Word pass entirely (useful for CI/scripting on macOS where launching Word is undesirable). The `--pdf` path finalizes via the export step (see below) and does not double-launch Word.

## PDF export (macOS + Microsoft Word)

```bash
docx_builder export pdf [DIR] [--input FILE] [--output FILE] [--no-update-source] [--open]
docx_builder build [DIR] [--no-finalize] [--pdf] [--no-update-source] [--open]
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

**Never trust `docProps/app.xml`'s `<Pages>` for the page count.** `python-docx` writes whatever was cached at the last serialisation — it is not recalculated and is routinely wrong (e.g. reports 1 page when Word renders 2). The PDF export path is the only reliable way to learn the true page count.

Errors are actionable and exit 1: non-macOS → `"PDF export requires macOS + Microsoft Word"`; Word not installed → points at the missing application; input `.docx` missing → names the resolved path.

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
