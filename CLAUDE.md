# docx_builder

CLI tool that generates DOCX reports from a `content.yaml` file. Installable via `uv tool install`, runnable from any working directory.

Repo: <https://github.com/lipex360x/docx_builder>

## Communication language

Always reply to the user in **Brazilian Portuguese (PT-BR)**, not European Portuguese (PT-PT). Use BR vocabulary and verb forms:

- "arquivo" (not "ficheiro")
- "tela" / "captura de tela" (not "ecrã" / "captura de ecrã")
- "está funcionando" (not "está a funcionar")
- "você" as the standard pronoun
- "salvar" (not "gravar"), "deletar/apagar" (not "apagar/eliminar")

Documentation files (CLAUDE.md, code comments, content) stay in English as already established.

## Layout

```
docx_builder/
  cli.py              # argparse entry — build / init / install skill
  builder.py          # build() + init_project()
  elements.py         # h1, h2, h3, body, bullet, bold_lead, reference, page_break
  figure.py           # figure(), figure_pair()
  pagination.py       # PAGE / NUMPAGES footer (style-driven)
  renderer.py         # Section dispatcher driven by content.yaml
  styles.py           # StyleResolver + length/color/align parsing
  summary.py          # Word TOC field insertion
  table.py            # Table border utilities
  skill_installer.py  # Logic for `docx_builder install skill`
  skill/
    SKILL.md          # Claude Code skill, shipped as package data
  templates/
    content.skeleton.yaml      # Used by `docx_builder init`
    default_styles.yaml        # Built-in style defaults
docs/
  styles-reference.md          # Full style schema (no-AI manual)
tests/                # pytest suite (95 tests)
conftest.py           # session-scoped cover_docx fixture
CHANGELOG.md          # Keep a Changelog format; SemVer
```

The package is fully agnostic: no bundled cover templates, no assignment-specific content. Users provide their own `content.yaml` and optionally their own cover `.docx`.

## Install and run

```bash
uv tool install git+https://github.com/lipex360x/docx_builder.git
```

Or from a local clone:

```bash
uv tool install .
```

Then from any directory:

```bash
docx_builder init                       # scaffold content.yaml + images/
docx_builder build                      # build using content.yaml in cwd
docx_builder build /some/dir            # build in another dir
docx_builder build --output Custom.docx
docx_builder build --template-dir ~/templates
docx_builder install skill              # install Claude Code skill (asks scope)
docx_builder install skill --scope local|global
```

Re-install with `uv tool install --reinstall .` after pulling changes.

## Styles

Visual properties are controlled by the optional `styles:` block in `content.yaml`. Cascade: built-in defaults → `styles:` block → inline `style:` per section. Full schema in [`docs/styles-reference.md`](docs/styles-reference.md).

## DOCX → PDF workflow

Today, finalising to PDF is manual:

1. Open the `.docx` in Microsoft Word.
2. `Cmd+A` then `F9` to update all fields (fills the TOC).
3. `File → Save As… → PDF`.

A `docx_builder export pdf` subcommand is planned — see [issue #1](https://github.com/lipex360x/docx_builder/issues/1).

`libreoffice --headless --convert-to pdf` is intentionally avoided — it changes fonts, spacing and field rendering. Word's renderer matches what a marker sees.

## Versioning

Semantic Versioning. Tagged releases on `main`. Tag format: `vX.Y.Z`.

Current release: **v0.1.0** (initial release).

Workflow for releasing:

1. Update `[Unreleased]` section in `CHANGELOG.md` — move entries into a new `[X.Y.Z]` section with the date.
2. Bump `version` in `pyproject.toml`.
3. Commit: `chore: release vX.Y.Z`.
4. Tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`.
5. Push: `git push origin main --tags`.

### When NOT to tag

Tags mark functional change. Skip the tag when a commit only:

- renames internal identifiers (no public API change)
- updates linter ignores, `.pre-commit-config.yaml`, or `.dev-quality.yaml`
- adjusts docs, comments, CHANGELOG, or `CLAUDE.md`
- reformats code (`ruff format`)
- adds/edits tests without changing behaviour they exercise

These are still committed and pushed, but the `[Unreleased]` section in `CHANGELOG.md` carries them until the next functional change earns a tag. SemVer rule of thumb: if a downstream user with the previous version installed cannot observe the change without reading the source, it does not deserve a tag.

## Roadmap

Tracked as GitHub issues. Current planned items (mirrored in `CHANGELOG.md` under `[Unreleased]`):

- [#1](https://github.com/lipex360x/docx_builder/issues/1) — `docx_builder export pdf` subcommand (macOS + Microsoft Word).
- Extensible section type registry — `register_section_type(name, handler)` for plugging in new section calls.
- PDF-to-YAML transcription workflow — guided protocol for analysing a source PDF and emitting matching `content.yaml`.

When opening a new roadmap item: create a GitHub issue, link it from `CHANGELOG.md` under `[Unreleased]`, and reference it back from this section.

## Development

```bash
uv sync
uv run pytest
uv run ruff check docx_builder tests
uv run mypy docx_builder
```

TDD: write failing test first, implement minimum to pass, refactor.

Quality gates (all must be green before commit):

- pytest — 95 tests, ~1s wall time
- ruff strict ruleset
- mypy strict
- Bundled defaults in `default_styles.yaml` must match the values asserted in `tests/test_elements.py` (changing one without the other breaks the test suite — intentional, prevents silent drift)

### Adding a new section type

1. Add a handler in the appropriate module (`elements.py`, `figure.py`, …).
2. Register it in `renderer.py`'s dispatcher (until issue for the registry pattern lands).
3. Add default styles in `default_styles.yaml`.
4. Document the call signature in `docs/styles-reference.md`.
5. Update `docx_builder/skill/SKILL.md` so the Claude Code skill knows about it.
6. Write tests covering default behaviour, global override, inline override.
7. Add an entry under `[Unreleased]` in `CHANGELOG.md`.

### Bundled package data

Anything inside `docx_builder/` that is not a `.py` file (`templates/`, `skill/`) ships with the wheel via hatchling's default packaging. Confirm with `uv build --wheel && unzip -l dist/*.whl` after changes.
