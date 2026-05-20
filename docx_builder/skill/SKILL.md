---
name: docx_builder
description: Generate DOCX reports from a content.yaml file. Use this skill when the user asks to create, build, or edit a DOCX document via docx_builder, discusses content.yaml structure, asks about styles cascade, references heading/body/bullet/figure sections, or wants to install the skill itself. Triggers on "docx_builder", "content.yaml", "build report", "scaffold report", "edit styles".
---

# docx_builder skill

This skill helps you operate the `docx_builder` CLI tool efficiently and correctly.

## What docx_builder does

It takes a `content.yaml` describing a document (cover, sections, styles) and produces a `.docx` file. Optionally loads a `.docx` cover template; falls back to a blank document if no template is configured.

Repository: this project. Installable globally via `uv tool install`.

## When to use this skill

- The user wants to create or regenerate a `.docx` from a YAML description.
- The user is editing `content.yaml` (cover, sections, styles).
- The user asks about heading sizes, bullet glyphs, footer format, page numbers, image captions, TOC, or any visual aspect of the generated `.docx`.
- The user mentions consumer projects under `projecs/computing/`.

If the request is **not** about generating/editing docs through this tool, do not invoke this skill.

## Core workflow

```bash
docx_builder init             # scaffold content.yaml + images/ in cwd
docx_builder build            # build using content.yaml in cwd
docx_builder build /path/dir  # build from another directory
docx_builder build --output Custom.docx
docx_builder build --template-dir ~/templates
```

After `build`, open the `.docx` in Word, press `Cmd+A` then `F9` to update fields (fills the TOC).

## content.yaml structure

```yaml
cover:                                 # optional — when omitted, no cover template loaded
  template: ../templates/MyCover.docx  # relative to project dir, or absolute, or bare filename (looks in template_dir)
  output: "Report_{number}.docx"       # filename pattern; placeholders are any cover string field
  number: "2026001"
  rows:                                # one entry per row of the cover table, in order
    - Module
    - Title
    - Lecturer
    - Student
    - "2026001"
    - "Submission date"
    - "Creation date"
  ai_declaration: |-                   # optional — appended as a bold-prefixed paragraph
    Declare AI usage here.

styles:                                # optional — overrides built-in defaults
  h1:     { font_size: 16pt, color: "#003366" }
  body:   { align: justify }
  bullet: { glyph: "→ " }
  footer: { format: "Page {page} of {total}" }

sections:                              # ordered list of section calls
  - call: page_break
    hide_page_counter: true

  - call: toc
    levels: 1-2

  - call: page_break

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

## Section types — complete list

| `call` | Required fields | Optional fields |
|---|---|---|
| `page_break` | — | `hide_page_counter` |
| `toc` | — | `levels` (default `1-2`), `hide_page_counter` |
| `h1` / `h2` / `h3` | `text` | `style`, `hide_page_counter` |
| `body` | `text` | `style`, `hide_page_counter` |
| `bullet` | `text` | `style`, `hide_page_counter` |
| `bold_lead` | `bold`, `rest` | `style`, `hide_page_counter` |
| `reference` | `text` | `style`, `hide_page_counter` |
| `figure` | `filename`, `label`, `caption` | `width`, `style`, `caption_style`, `hide_page_counter` |
| `figure_pair` | `filename1`, `filename2`, `label`, `caption` | `width1`, `width2`, `style`, `caption_style`, `hide_page_counter` |

## Styles — cascade and editing

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
  text: Cover-page-style title
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

## Page numbering and `hide_page_counter`

Page numbers go on every section by default. To suppress them on early pages (cover, TOC, blank intro), set `hide_page_counter: true` on those sections. The renderer inserts a continuous section break at the first section without the flag — sections before the break have no footer, sections after show `page / total`.

```yaml
sections:
  - call: page_break
    hide_page_counter: true     # cover: no footer

  - call: toc
    hide_page_counter: true     # TOC: no footer

  - call: page_break            # no flag — footer starts here onward

  - call: h1
    text: Introduction          # this page shows "3 / N"
```

## Common errors and how to fix them

| Error | Cause | Fix |
|---|---|---|
| `content.yaml not found in <dir>` | Wrong cwd, or `init` was never run | `cd` into the project dir, or run `docx_builder init` |
| `cover template not found: <name>` | Path in `cover.template` doesn't resolve | Use an absolute path, a relative path with `/`, or place the file in `--template-dir` |
| `unknown call: '<x>'` | Section dict has an unrecognised `call` value | Use a value from the section types table above |
| TOC is empty or shows the wrong pages | Word fields not refreshed after build | Open the `.docx`, `Cmd+A` then `F9` |
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

The bundled templates intentionally do **not** contain assignment-specific covers — those live with the consumer projects (e.g. `projecs/computing/ca1/templates/CA Cover Sheet.docx`).

## Updating this skill

Reinstall after pulling new versions:

```bash
docx_builder install skill --force   # overwrite the local copy
```
