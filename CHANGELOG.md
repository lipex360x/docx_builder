# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- Extensible section type registry — `register_section_type(name, handler)` for plugging in new section calls (quote, callout, table, code_block, …) without touching the core renderer.
- PDF-to-YAML transcription workflow — guided protocol for analysing a source PDF (text + visual styles) and emitting a matching `content.yaml`.

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

[Unreleased]: https://github.com/lipex360x/docx_builder/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/lipex360x/docx_builder/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/lipex360x/docx_builder/releases/tag/v0.1.0
