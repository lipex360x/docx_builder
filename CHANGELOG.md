# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `docx_builder build` now prints a short post-build report: word count, estimated reading time (at 200 wpm), a page-count line, and an em-dash (`U+2014`) counter. When any em-dash is present the line is flagged `<- remove before shipping` so they are easy to spot and strip. Page count is reported as `n/a` because a plain `build` cannot know it ahead of time — only the Word/PDF export path produces the real count. The report is non-destructive: em-dashes are counted and flagged, never auto-removed. New module `docx_builder/report.py` (`analyse`, `report_for`, `format_report`).

### Fixed

- **Page counter no longer overcounts on cover+body reports.** The footer denominator now uses Word's `SECTIONPAGES` field instead of `NUMPAGES`, so it counts only the numbered body section rather than every physical page (cover and front matter included). A 24-page body that previously closed on `24 / 25` now correctly reads `24 / 24`. In single-section documents the two fields are equivalent, so there is no change there.
- **The body now starts on a fresh page and restarts numbering deterministically.** The section break between `front_matter` and `sections` changed from continuous to next-page, so the page-number restart lands on a real page boundary instead of mid-page. The body section is also given an explicit `pgNumType` restart (`start=1`), so it begins at `PAGE 1` regardless of whether the cover `.docx` carries its own page-number restart. This keeps the TOC on its own page and makes the body number cleanly from 1. A `page_break` placed as the first item of `sections` (a common way to push the body past the front matter) is absorbed by the section break instead of stacking with it, so the body no longer starts with a blank page.
- **A `call: toc` is now always treated as front matter** (footer cleared, kept out of the `PAGE` sequence) regardless of whether it sits under `front_matter:` or `sections:`. Previously a TOC placed in `sections:` was numbered as `PAGE 1`, pushing the body to start at `PAGE 2` and shifting every page number the TOC displayed.

### Planned

- Extensible section type registry — `register_section_type(name, handler)` for plugging in new section calls (quote, callout, table, code_block, …) without touching the core renderer.
- PDF-to-YAML transcription workflow — guided protocol for analysing a source PDF (text + visual styles) and emitting a matching `content.yaml`.

## [0.4.0] — 2026-05-29

### Added

- CLI: `--no-finalize` on `build` — skips the Word TOC-finalize pass entirely, keeping `build` pure and fast (useful for CI/scripting on macOS where launching Word is undesirable).

### Changed

- **`docx_builder build` now finalizes the TOC by default.** When the document declares a `toc` section (in `front_matter:` or `sections:`), after writing the `.docx` `build` drives Microsoft Word to update every table of contents and all fields, then writes the populated `.docx` back over the source — no manual F9, no PDF. TOC-less documents never launch Word, so they cost nothing extra. Off macOS or without Word, `build` does not error: it leaves the placeholder TOC field in place, prints a short `note:` to stderr, and exits 0. The shared Word-driving core was extracted into `finalize_source()` (the `export_pdf` path minus the PDF save); `--pdf` finalizes via the export step and does not double-launch Word. Pass `--no-finalize` to opt out.
- `--open` with `--pdf` (and `export pdf --open`) now opens **both** the resulting `.pdf` and the finalized `.docx` (the latter in Microsoft Word via `open -a`), instead of only the `.pdf`. Plain `build --open` still opens just the `.docx`. Closes the last gap versus a hand-rolled export script.
- `docx_builder init` success message reworded from `Initialized: <path>` to `Created: <path>. Edit it directly, or ask Claude Code (docx_builder skill).` (issue #2, item 4)
- `docs/styles-reference.md` gained a `## Known macOS Word quirks` section documenting Word's per-directory permission prompt, the broken AppleScript `save as`, and the unreliable cached `<Pages>` count. (issue #2, item 5)

### Fixed

- Headings (`h1`/`h2`/`h3`) no longer inherit Word's built-in blue theme colour. The bundled defaults now set `color: "#000000"` for all three, applied as direct run formatting so it overrides the `Heading N` style colour. Override per-heading via `styles:` as before. (issue #2, item 1)

### Deprecated

- `hide_page_counter: true` on individual sections now prints a one-time `warning:` to stderr per build (suppress with `DOCX_BUILDER_NO_DEPRECATION=1`). Use the `front_matter:` block instead; the flag is scheduled for removal in v0.5. (issue #2, item 3)

## [0.3.0] — 2026-05-28

### Added

- CLI: `--open` on `build` and `export pdf` — opens the result after the command finishes (the `.pdf` with `--pdf` / `export pdf`, otherwise the `.docx` on a plain `build`). macOS-only; on other platforms it prints `note: --open is currently macOS-only` and skips without erroring. (issue #2, item 2)
- CLI: `--no-update-source` on `export pdf` (honoured by `build --pdf`) — leaves the source `.docx` byte-identical to the pre-export input instead of writing back the populated TOC. Useful when `export pdf --input SomeUserFile.docx` points at a file that must not be overwritten.

### Changed

- **PDF export now finalises the source `.docx` by default.** The JXA calls `document.save()` to persist the Word-populated TOC into the scratch copy, and Python then moves that scratch copy back over the source input path. The source ends with a filled TOC and no manual F9. This reverses the v0.2.0 behaviour (source left untouched); opt back out with `--no-update-source`. The PDF still moves to its destination as before, and Word still writes only inside the scratch directory, so the permission prompt fires only once — the write-back is a plain Python move.
- `build_summary()` no longer emits the italic F9 instruction note paragraph (`"Note: open in Microsoft Word … press Ctrl+A then F9."`). The TOC field and its in-field placeholder (`"Right-click here and select 'Update Field' …"`) are kept — that placeholder is the field's display text. `strip_toc_note` is retained as a defensive strip on the scratch copy for legacy `--input` documents that still carry the old note.

### Changed (CLI structure, carried from prior unreleased work)

- CLI internals refactored from a single `docx_builder/cli.py` into a modular `docx_builder/cli/` package (one module per subcommand, mirroring the sibling `web-view` layout). Pure UX + structure change — no behavioural change to any command's flags, defaults, exit codes, or success-path output. `docx_builder.cli:main` still resolves, so the installed binary is unaffected.
- `docx_builder --help` and every `docx_builder <command> --help` now show a concrete `Examples:` block plus short prose, and error messages on stderr give actionable next-step guidance (e.g. missing `content.yaml` → suggests `docx_builder init`; `init` on an existing file → suggests `--force`) instead of bare `error: <exception>`.

## [0.2.0] — 2026-05-28

### Added

- CLI: `docx_builder export pdf [DIR]` — convert a built `.docx` to PDF via Microsoft Word and JavaScript for Automation (macOS only). Flags: `--input FILE`, `--output FILE`. Input defaults to `build`'s own filename resolution; output defaults to `<input>.pdf`.
- CLI: `docx_builder build [DIR] --pdf` — build then export to PDF in one shot.
- PDF export updates each `tablesOfContents` entry and all fields in Word before saving, so the TOC and page-count placeholders resolve in the PDF.
- PDF export strips the redundant TOC instruction note (`"Note: open in Microsoft Word…"`) from a scratch copy of the `.docx` before conversion; the source `.docx` is never mutated.
- PDF export writes to a stable scratch directory (`~/Library/Caches/docx_builder/exports/`) then moves the result to the requested path, so Word's Files & Folders permission prompt only ever fires once.
- PDF export reports the real page count via `mdimport` + `mdls kMDItemNumberOfPages`, printed as `Exported: <path> (<N> pages)`. The cached `<Pages>` value in `docProps/app.xml` is not trusted — it reflects the last serialisation, not actual pagination.
- Top-level `page_numbers: false` toggle in `content.yaml` — disables the footer counter across every page. Use for CVs, one-pagers, and any document without pagination.
- Top-level `front_matter:` block — sections rendered first, without page numbers, for cover sheets and TOCs. The footer starts on `sections:`. Replaces the per-section `hide_page_counter` flag with a declarative, repetition-free alternative.

### Changed

- `docx_builder init` now writes a 3-line marker `content.yaml` (just a comment pointing at the docs and skill). No more CCT-flavoured placeholder (Module/Lecturer/Student/References/AI declaration). Real content is authored on demand by the user or by Claude with the `docx_builder` skill loaded.
- `init` no longer creates an empty `images/` directory. Add images when you reference them.

- Refactor identifiers to satisfy dev-quality v0.11.0: rename single/two-character locals (`p`→`paragraph`, `t`→`text`, `exc`→`exception`, `pf`→`paragraph_format`, `err`→`error`) and internal heading helpers (`h1`/`h2`/`h3`→`heading_1`/`heading_2`/`heading_3`). YAML `call:` values are unchanged (`h1`/`h2`/`h3` still accepted).
- Strip inline `# noqa: SLF001` comments in favour of `per-file-ignores` entries in `pyproject.toml`. dev-quality forbids inline noqa.
- Document the `pre-commit install` bootstrap step in `README.md` so cloned repos activate the hook before the first commit.

## [0.1.0] — 2026-05-20

Initial release.

### Added

- CLI: `docx_builder build [DIR]` — builds the DOCX from `content.yaml` in the target directory (default: cwd). Flags: `--output FILE`, `--template-dir DIR`.
- CLI: `docx_builder init [DIR]` — scaffolds `content.yaml` skeleton + `images/` folder. Flag: `--force`.
- CLI: `docx_builder install skill [--scope local|global|ask]` — installs the Claude Code skill from bundled package data.
- YAML-driven document structure: optional `cover` block, optional `styles` block, ordered `sections` list.
- Section types: `h1`, `h2`, `h3`, `body`, `bullet`, `bold_lead`, `reference`, `page_break`, `toc`, `figure`, `figure_pair`.
- Style cascade: built-in defaults (`default_styles.yaml`) → top-level `styles:` block → inline `style:` per section.
- Style fields supported: `font_family`, `font_size`, `color`, `bold`, `italic`, `align`, `space_before`, `space_after`, `indent_left`, `indent_first_line`, `glyph` (bullets), `format` (footer), `label_bold`, `caption_italic`.
- Length units: `pt`, `in`, `cm`, `mm`. Colors: `#RRGGBB`. Alignment: `left`/`center`/`right`/`justify`.
- Cover template resolution: absolute path → relative path (anchored at project dir) → `--template-dir` lookup → bundled package templates. Cover is fully optional; when absent, a blank Document is used.
- Output filename: `cover.output` template (`{number}`, plus any string field under `cover`) → `--output` flag → default `Report_{number}.docx`.
- Page numbering: PAGE / NUMPAGES footer driven by `styles.footer.format` (e.g. `"{page} / {total}"`). Sections with `hide_page_counter: true` are excluded from the footer but still counted in the total.
- Documentation: `docs/styles-reference.md` — complete schema for hand-editing without AI assistance.
- Bundled Claude Code skill (`SKILL.md`) describing efficient/correct usage of the tool.
- Tests: 95 pytest covering build, CLI, styles, elements, figure, pagination, renderer, summary, table, skill installer.
- Quality: ruff strict + mypy strict — both clean.

[Unreleased]: https://github.com/lipex360x/docx_builder/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/lipex360x/docx_builder/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/lipex360x/docx_builder/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/lipex360x/docx_builder/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/lipex360x/docx_builder/releases/tag/v0.1.0
