---
name: docx_builder
description: Generate DOCX reports from a content.yaml file. Use this skill when the user asks to create, build, or edit a DOCX document via docx_builder, discusses content.yaml structure, asks about styles cascade, references heading/body/bullet/figure sections, or wants to install the skill itself. Triggers on "docx_builder", "content.yaml", "build report", "scaffold report", "edit styles".
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
```

`init` does NOT scaffold a placeholder document. It only writes a tiny marker file pointing back at this skill. You (the assistant) are expected to author the real `content.yaml` based on what the user actually wants to build — CV, report, manual, paper, contract, fiction — each gets a tailored YAML.

After `build`, open the `.docx` in Word, press `Cmd+A` then `F9` to update fields (fills the TOC).

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

Any section may appear in either `front_matter` or `sections`. The distinction is only about page numbering.

## Page numbering — three modes

| Goal | YAML |
|---|---|
| No page numbers anywhere | `page_numbers: false` (top-level) |
| Cover/TOC unnumbered, content numbered | Put cover/TOC items in `front_matter:`; content in `sections:` |
| Every page numbered | Use `sections:` only (no `front_matter`, no `page_numbers: false`) |

### Legacy: `hide_page_counter`

The flag `hide_page_counter: true` on individual section items still works and is supported for backward compatibility. New documents should prefer the cleaner `front_matter` block — it makes intent explicit and avoids repetition.

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
