# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- `docx_builder export pdf [DIR]` — convert generated `.docx` to PDF via Microsoft Word + JXA (macOS-only, requires Word).
- Extensible section type registry — `register_section_type(name, handler)` for plugging in new section calls (quote, callout, table, code_block, …) without touching the core renderer.
- PDF-to-YAML transcription workflow — guided protocol for analysing a source PDF (text + visual styles) and emitting a matching `content.yaml`.

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

[Unreleased]: https://github.com/lipex360x/docx_builder/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/lipex360x/docx_builder/releases/tag/v0.1.0
