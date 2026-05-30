# Styles reference

Complete schema for the `styles:` block in `content.yaml`. Every field is optional — when omitted, the built-in default (defined in `docx_builder/templates/default_styles.yaml`) is used.

## Cascade

Styles are resolved per section in this order (later wins):

1. **Built-in defaults** — bundled with the package.
2. **`styles:` block in your `content.yaml`** — applies to every section of that type.
3. **`style:` key on the section itself** — overrides only that one section.

```yaml
styles:
  h1: { font_size: 14pt }          # global default for h1

sections:
  - call: h1
    text: Normal heading              # → 14pt (from styles block)

  - call: h1
    text: Special heading
    style: { font_size: 22pt, color: "#003366" }   # → 22pt navy (inline)
```

## Value formats

### Length

Accepted units: `pt`, `in`, `cm`, `mm`. A bare number is treated as `pt` for font sizes / spacing and as `in` for indents.

| Field accepts | Examples |
|---|---|
| Font size, spacing | `"11pt"`, `"9.5pt"`, `11` |
| Indent | `"0.3in"`, `"1cm"`, `"15mm"` |

### Color

Hex RGB, with or without leading `#`:

```yaml
color: "#FF0033"
color: "003366"
```

### Alignment

One of `left`, `center`, `right`, `justify`.

### Boolean

`true` / `false`.

## Section style keys

Every paragraph-style key (h1/h2/h3/body/bullet/bold_lead/reference) supports the same base properties. Specific section types add a few extras.

### Common (all paragraph styles)

| Key | Type | Default behaviour | Notes |
|---|---|---|---|
| `font_family` | string | inherits from template | Name as registered in Word (e.g. `Aptos`, `Calibri`). |
| `font_size` | length (pt) | varies by type | See defaults below. |
| `color` | hex color | inherits | `"#000000"` for explicit black. |
| `bold` | bool | varies | `true` makes the runs bold. |
| `italic` | bool | varies | `true` makes the runs italic. |
| `align` | enum | `left` (or template default) | `left` / `center` / `right` / `justify`. |
| `space_before` | length (pt) | varies | Empty space above the paragraph. |
| `space_after` | length (pt) | varies | Empty space below the paragraph. |
| `indent_left` | length (in) | `0` | Left indent for the whole paragraph. |
| `indent_first_line` | length (in) | `0` | First-line indent. Negative values produce a hanging indent. |

### `bullet` / `bold_lead`

Inherits everything above and adds:

| Key | Type | Default | Notes |
|---|---|---|---|
| `glyph` | string | `"• "` | Marker prepended to the text. Trailing space included if you want one. |

### `figure` / `figure_pair`

| Key | Type | Default | Notes |
|---|---|---|---|
| `align` | enum | `center` | Image alignment within the paragraph. |
| `space_before` | length (pt) | `10pt` | Spacing above the image. |
| `default_width` | length (in) | `5.0in` | Used only by `figure` when YAML doesn't specify `width`. |
| `default_width_left` | length (in) | `3.0in` | `figure_pair` first image fallback. |
| `default_width_right` | length (in) | `2.5in` | `figure_pair` second image fallback. |

### `figure_caption`

| Key | Type | Default | Notes |
|---|---|---|---|
| `align` | enum | `center` | Caption alignment. |
| `font_size` | length (pt) | `9pt` | |
| `label_bold` | bool | `true` | Whether the `Figure X.Y –` prefix is bold. |
| `caption_italic` | bool | `true` | Whether the caption body is italic. |
| `space_after` | length (pt) | `16pt` | Spacing below the caption. |

### `footer`

| Key | Type | Default | Notes |
|---|---|---|---|
| `format` | string | `"{page} / {total}"` | Placeholders `{page}` and `{total}` are required if you customise. `{total}` counts the pages of the numbered body section (Word's `SECTIONPAGES`), not the whole document, so an unnumbered cover/TOC is excluded and the footer closes on `N / N`. |
| `align` | enum | `right` | |
| `font_size` | length (pt) | `9pt` | |

## Built-in defaults

These are the exact values shipped in `default_styles.yaml`. Override any field via the `styles:` block in your `content.yaml`.

```yaml
h1:
  font_size: 14pt
  bold: true
  color: "#000000"
  align: left
  space_before: 14pt
  space_after: 6pt

h2:
  font_size: 12pt
  bold: true
  color: "#000000"
  align: left
  space_before: 10pt
  space_after: 3pt

h3:
  font_size: 11pt
  bold: true
  color: "#000000"
  align: left
  space_before: 8pt
  space_after: 3pt

body:
  font_size: 11pt
  space_after: 8pt

bullet:
  glyph: "• "
  font_size: 11pt
  indent_left: 0.3in
  space_after: 3pt

bold_lead:
  glyph: "• "
  font_size: 11pt
  indent_left: 0.3in
  space_after: 6pt

reference:
  font_size: 11pt
  indent_left: 0.3in
  indent_first_line: -0.3in
  space_after: 6pt

figure:
  align: center
  space_before: 10pt
  default_width: 5.0in

figure_pair:
  align: center
  space_before: 10pt
  default_width_left: 3.0in
  default_width_right: 2.5in

figure_caption:
  align: center
  label_bold: true
  caption_italic: true
  font_size: 9pt
  space_after: 16pt

footer:
  format: "{page} / {total}"
  align: right
  font_size: 9pt
```

## Page numbering

Three top-level modes, configured outside the `sections:` list:

```yaml
# Mode A — disable everywhere
page_numbers: false

# Mode B — front_matter unnumbered, sections numbered
front_matter: [...]
sections: [...]

# Mode C — every page numbered (default; no extra config)
sections: [...]
```

The legacy `hide_page_counter: true` flag on individual section items still works but is **deprecated** — `build` now prints a one-time `warning:` to stderr when it is present, and the flag is scheduled for removal in v0.5. New documents should use `front_matter:` instead — it is declarative, free of repetition, and surfaces intent at the top of the file.

The numbered body section starts on a new page (the break between `front_matter` and `sections` is a next-page section break), so the page-number restart lands on a real page boundary and the body begins at `PAGE 1`. A `page_break` placed as the first item of `sections` is absorbed by that section break, so the body never starts with a blank page. A `toc` is always pulled into the unnumbered front matter regardless of whether you list it under `front_matter:` or `sections:`; this keeps the table of contents out of the `PAGE` sequence so the body still starts at `PAGE 1`.

## Section type reference

| `call` | Required fields | Optional fields | Style key consumed |
|---|---|---|---|
| `h1`, `h2`, `h3` | `text` | `style` | `h1` / `h2` / `h3` |
| `body` | `text` | `style` | `body` |
| `bullet` | `text` | `style` | `bullet` |
| `bold_lead` | `bold`, `rest` | `style` | `bold_lead` |
| `reference` | `text` | `style` | `reference` |
| `page_break` | — | — | — |
| `toc` | — | `levels` | — |
| `figure` | `filename`, `label`, `caption` | `width`, `style`, `caption_style` | `figure`, `figure_caption` |
| `figure_pair` | `filename1`, `filename2`, `label`, `caption` | `width1`, `width2`, `style`, `caption_style` | `figure_pair`, `figure_caption` |

Any section type may appear in either `front_matter` or `sections`. A `toc` is always treated as front matter (unnumbered) wherever you place it.

### Inline overrides

Every section accepts a `style:` key for paragraph-level overrides. Figure-type sections additionally accept `caption_style:` for the caption.

```yaml
- call: figure
  filename: chart.png
  label: Figure 2.1
  caption: Quarterly results
  width: 4in
  style: { space_before: 20pt }
  caption_style: { font_size: 11pt, caption_italic: false }
```

## Editing by hand

This file is the complete reference. To restyle a document without any tooling:

1. Open the `content.yaml`.
2. Add or edit the top-level `styles:` block.
3. For one-off changes, add `style:` directly under the section dictionary.
4. Run `docx_builder build` from the project directory.

Field names and value formats are stable — anything documented here is supported by the current version.

## Known macOS Word quirks

These only matter if you bypass the CLI and drive Microsoft Word yourself (custom scripts). `docx_builder export pdf` and `docx_builder build` (when finalizing a TOC) already handle them for you. Note that a plain `build` of a TOC document now also drives Word by default, so it can trigger the same one-time permission prompt described below; pass `--no-finalize` to keep `build` from launching Word.

- **Per-directory permission prompt.** macOS asks Word for Files & Folders access the first time it writes to a directory it has not been authorised for. A script that writes PDFs into many different project directories triggers the prompt once per directory. `docx_builder export pdf` sidesteps this by always letting Word write inside a single stable scratch directory (`~/Library/Caches/docx_builder/exports/`) — authorised once — then moving the result to its destination with a plain file move, which needs no Word grant.
- **`save as` is broken in Word 16.70+.** The AppleScript `save as` verb fails on recent Word. The supported path is JavaScript for Automation (JXA) via `osascript -l JavaScript`, which is what the export subcommand uses.
- **Cached `<Pages>` is unreliable.** `python-docx` writes a `<Pages>` value into `docProps/app.xml` at save time, but it is not recalculated against real pagination — only a renderer (Word) repaginating the document yields a true page count. `export pdf` reports the real count from the produced PDF via `mdls kMDItemNumberOfPages`.
- **ToC hyperlinks can shift in the exported PDF.** Word's `saveAs … format PDF` engine occasionally writes some table-of-contents bookmark destinations one entry ahead, so clicking a ToC entry in the PDF lands on the next heading. The `.docx` itself is correct, and page numbers are unaffected. The bug is rare, so the remedy is opt-in: pass `--fix-toc-links` to `export pdf` or `build --pdf` to post-process the PDF and rewrite each ToC link to its heading's real page. It needs the optional `pdf-links` extra (`uv tool install 'docx_builder[pdf-links]'`).
