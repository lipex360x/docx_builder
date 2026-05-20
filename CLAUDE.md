# docx_builder

CLI tool that generates DOCX reports from a `content.yaml` file. Installable via `uv tool install`, runnable from any working directory.

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
docx_builder install skill              # install Claude Code skill
```

Re-install with `uv tool install --reinstall .` after pulling changes.

## Styles

Visual properties are controlled by the optional `styles:` block in `content.yaml`. Cascade: built-in defaults → `styles:` block → inline `style:` per section. Full schema in [`docs/styles-reference.md`](docs/styles-reference.md).

## DOCX → PDF workflow

The generated `.docx` includes a Word TOC field. To finalise:

1. Open the `.docx` in Microsoft Word.
2. `Cmd+A` then `F9` to update all fields (fills the TOC).
3. `File → Save As… → PDF`.

`libreoffice --headless --convert-to pdf` is intentionally avoided — it changes fonts, spacing and field rendering. Word's renderer matches what a marker sees.

## Development

```bash
uv sync
uv run pytest
uv run ruff check docx_builder tests
uv run mypy docx_builder
```

TDD: write failing test first, implement minimum to pass, refactor.

Quality gates:
- pytest must be green
- ruff strict ruleset must pass
- mypy strict must pass
- Bundled defaults in `default_styles.yaml` must match the values asserted in `tests/test_elements.py` (changing one without the other breaks the test suite — intentional, prevents silent drift).
