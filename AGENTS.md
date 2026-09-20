# docx_builder agent guide

This file is the Codex entry point for working in this repository. It complements
`CLAUDE.md`: keep the shared project facts and workflows aligned, but express
Codex-specific operating instructions here rather than copying Claude-only tool
names or assumptions verbatim.

## Communication and writing

- Communicate with the user in Brazilian Portuguese (PT-BR).
- Keep source code, code comments, configuration, commits, and repository
  documentation in English unless an existing artifact intentionally uses
  another language.
- Prefer Brazilian vocabulary in user-facing replies: `arquivo`, `tela`,
  `salvar`, and `você`.

## What this project is

`docx_builder` is a Python 3.11+ package and `argparse` CLI that turns a
`content.yaml` document definition into a `.docx`. It can optionally:

- scaffold a role-based document project;
- populate an optional Word cover template;
- add headings, prose, bullets, references, figures, tables, a table of
  contents, and page-number fields;
- validate prose for em/en dashes and related AI-tell characters;
- drive Microsoft Word on macOS to finalize fields or export PDF; and
- repair incorrectly shifted ToC hyperlinks in a PDF with the optional
  `pdf-links` dependency.

The package is content-agnostic. Do not add client-, assignment-, or
report-specific content or cover files to the package.

## Sources of truth

Read only as much as the task needs, using this priority when documents drift:

1. Current behavior and public interfaces: `docx_builder/` and `tests/`.
2. CLI flags and help: `docx_builder/cli/` and `uv run docx_builder <command> --help`.
3. Package metadata and current version: `pyproject.toml`.
4. User-facing overview: `README.md`.
5. Complete style schema: `docs/styles-reference.md`.
6. Operational document-authoring guide: `docx_builder/skill/SKILL.md`.
7. Development history and release notes: `CHANGELOG.md`.
8. Claude-era repository process: `CLAUDE.md` and `.claude/agents/`.

Do not trust hard-coded release numbers, test counts, or roadmap snapshots in a
long-lived document without checking the current metadata, tests, and GitHub
state. In particular, parts of `CLAUDE.md` are historical even though its
development conventions remain relevant.

## Architecture and data flow

The main flow is:

1. `docx_builder/cli/` parses a command and resolves the target directory.
2. `builder.resolve_content_dir()` uses a root `content.yaml` when present,
   otherwise it falls back to `report/content.yaml`.
3. `builder.py` loads YAML, resolves the cover and output paths, merges
   `front_matter` with `sections`, and creates the document.
4. `styles.StyleResolver` applies the cascade: bundled defaults, then the
   top-level `styles:` block, then a section's inline `style:`.
5. `renderer.py` dispatches each section by its `call` value to the paragraph,
   figure, table, ToC, or page-break implementation.
6. `pagination.py` writes Word field codes. A ToC is always treated as front
   matter for numbering, even if declared under `sections`.
7. `python-docx` saves the `.docx`. It does not render pages or populate a ToC.
8. When requested, `export.py` drives Microsoft Word with JXA on macOS to
   update fields, finalize the source, and/or render PDF.

Important modules:

- `docx_builder/builder.py`: content loading, cover/output resolution, build
  orchestration, and `init_project()`.
- `docx_builder/renderer.py`: section dispatcher and front-matter boundary.
- `docx_builder/elements.py`: headings, body, bullet, bold lead, reference,
  and page break.
- `docx_builder/figure.py`: single and paired figures plus captions.
- `docx_builder/table.py`: table shape validation, cell rendering, widths,
  borders, fills, alignment, and cell bullets.
- `docx_builder/styles.py`: defaults, parsing, cascade, and style application.
- `docx_builder/summary.py`: Word ToC field insertion.
- `docx_builder/pagination.py`: page fields and numbering restarts.
- `docx_builder/export.py`: Word/JXA finalization and PDF export.
- `docx_builder/toc_links.py`: opt-in PyMuPDF ToC-link repair.
- `docx_builder/validate.py`: prose validation.
- `docx_builder/report.py`: post-build word/read-time/em-dash report.
- `docx_builder/scaffold.py`: role-based, additive, idempotent project scaffold.
- `docx_builder/skill_installer.py`: bundled Claude Code skill installation.

## Using the CLI

For repository-local work, use `uv run docx_builder ...` so the command runs
the checked-out source. For a global development install, prefer:

```bash
uv tool install --editable .
```

A snapshot install (`uv tool install .`) must be reinstalled after source
changes. An editable install normally needs reinstalling only after dependency
or script-entry changes.

Common commands:

```bash
uv run docx_builder --version
uv run docx_builder init /path/to/project
uv run docx_builder init /path/to/project --with references,src
uv run docx_builder init /path/to/project --full --name "Annual Report"
uv run docx_builder init /path/to/project --cover
uv run docx_builder build /path/to/project
uv run docx_builder build /path/to/project --no-finalize
uv run docx_builder build /path/to/project --pdf
uv run docx_builder validate /path/to/project --strict
uv run docx_builder export pdf /path/to/project
```

Use `--force` with `init` only when overwriting scaffolded files is intended.
Without it, scaffolding is additive and leaves existing files unchanged.

The scaffold always creates `report/`, its `images/`, `assets/`, `output/`,
and `templates/` roles, `.work/`, `.gitignore`, and a generated `CLAUDE.md`.
Optional layers are `brief`, `references`, `src`, `meta`, `tools`, `monitor`,
and `ai-check`; dependencies such as `monitor -> tools` are resolved by
`scaffold.py`.

### `content.yaml` essentials

Top-level blocks are optional:

- `cover`: template, output pattern, replacement rows, and cover metadata.
- `styles`: global style overrides.
- `page_numbers`: defaults to enabled.
- `front_matter`: rendered before the numbered body.
- `sections`: the main ordered content list.

Supported `call` values are `h1`, `h2`, `h3`, `body`, `bullet`, `bold_lead`,
`reference`, `page_break`, `toc`, `figure`, `figure_pair`, and `table`. Consult
`docx_builder/skill/SKILL.md` for their fields and examples, and
`docs/styles-reference.md` for all style keys. Do not duplicate the complete
schema here.

The output filename priority is `--output`, then `cover.output`, then the
built-in pattern. Cover-template lookup is absolute path, then a path relative
to the content directory, then `--template-dir`, then package data.

### Word and PDF constraints

- PDF export and automatic ToC finalization require macOS and Microsoft Word.
- `build --no-finalize` is the pure/CI-friendly path and never launches Word.
- Off macOS or without Word, a normal build still succeeds but leaves ToC
  fields unpopulated and prints a note.
- Export updates the source `.docx` by default. Use `--no-update-source` when
  the input must remain byte-identical.
- Use `--fix-toc-links` only for Word's shifted PDF ToC-link bug; it requires
  the `pdf-links` extra.
- Do not use LibreOffice as a drop-in validation renderer. It can change fonts,
  field behavior, and pagination.
- Do not infer rendered page layout from `python-docx` or cached DOCX metadata.
  Inspect an exported PDF with PyMuPDF when layout or link destinations matter.

## Development workflow

Bootstrap a clone with:

```bash
uv sync
pre-commit install
```

Run the standard gates with:

```bash
uv run pytest
uv run ruff check docx_builder tests
uv run --with mypy mypy docx_builder
pre-commit run --all-files
```

The two Microsoft Word integration tests are opt-in with
`DOCX_BUILDER_TEST_WORD=1`; ordinary test runs skip them. Do not enable them in
an environment where launching Word would be surprising.

For behavior changes, use Red, Green, Refactor:

1. Add a focused failing test and confirm it fails for the intended reason.
2. Implement the minimum behavior needed to pass.
3. Run the focused test, then the full suite and static checks.
4. Refactor only when the green implementation introduced real duplication or
   clarity loss.

Never bypass hooks with `--no-verify`. Fix quality failures instead of hiding
them with inline `# noqa`, `# nosec`, or broad `type: ignore` escapes. Preserve
unrelated user changes in a dirty worktree.

### Change map

When adding or changing a section type, normally update:

1. its implementation module;
2. the dispatcher in `renderer.py`;
3. `templates/default_styles.yaml` if it has styles;
4. focused tests for defaults, global overrides, inline overrides, and invalid
   input as applicable;
5. `docs/styles-reference.md`;
6. `docx_builder/skill/SKILL.md`;
7. `README.md` when the user-facing surface changes; and
8. `[Unreleased]` in `CHANGELOG.md`.

The defaults in `default_styles.yaml` intentionally have test coverage; do not
change one side without the other.

When scaffold roles or generated files change, keep these aligned:

- `docx_builder/scaffold.py`;
- `docx_builder/templates/scaffold/claude.md.tmpl`;
- the Project structure sections in `README.md` and `CLAUDE.md`; and
- `docx_builder/skill/SKILL.md`.

Files under `docx_builder/templates/` and `docx_builder/skill/` are wheel data.
After changing packaging-sensitive data, verify it is present:

```bash
uv build --wheel
unzip -l dist/*.whl
```

## GitHub issue workflow

The files under `.claude/agents/` are Claude agent prompts, but they also define
the intended issue process. Treat them as workflow specifications rather than
Codex-native configuration.

Before issue-driven work, inspect the issue and its labels:

```bash
gh issue view <N> --repo lipex360x/docx_builder --json title,body,labels,url
```

- `needs-design`: do not implement. Follow
  `.claude/agents/docx-builder-architect.md`; resolve design forks, record the
  decisions, publish binary/testable acceptance criteria, then change the label
  to `enhancement`.
- `enhancement`, `bug`, or `polish` with concrete acceptance criteria: create
  an issue branch and follow `.claude/agents/docx-builder-implementer.md`.
- Exploratory questions, discussions, and small non-issue edits stay with the
  main agent and do not need delegation.

When the runtime supports subagents, use a dedicated design or implementation
subagent for issue-driven work, mirroring the two prompt files. The main agent
still owns label verification, implementation-branch preparation, user-facing
questions, and review of the returned barriers report. If subagents are not
available, follow the same workflow directly.

Implementation branches use `<type>/<short-slug>-<issue-number>` with `feat/`,
`fix/`, or `chore/`. Do not implement an issue on `main`. Keep acceptance and
closure checkboxes in the issue body current as work lands; the PR should use
`Closes #N`.

Do not create releases, bump versions, or tag without explicit user direction.
For an authorized release, use Semantic Versioning and `vX.Y.Z` annotated tags.
Documentation-only, test-only, formatting, and internal-quality changes do not
earn a release tag by themselves.

## Documentation and skill synchronization

For every issue, verify the applicable closure items before declaring it done:

- update `CHANGELOG.md`;
- update `docx_builder/skill/SKILL.md` when authoring behavior changes;
- update `CLAUDE.md` and this `AGENTS.md` when developer workflow or project
  architecture changes;
- update `README.md` for user-visible commands, flags, output, installation, or
  layout;
- update `docs/styles-reference.md` for style behavior;
- sync the Claude global skill after changing it:

  ```bash
  cp docx_builder/skill/SKILL.md /Users/lipex360/www/claude/.brain/skills/docx_builder/SKILL.md
  ```

- verify whether the user's installed CLI is editable or needs reinstalling;
- tag only when explicitly authorized and the change is release-worthy.

For a small non-issue documentation edit, update only the documents whose facts
actually changed; do not perform the whole release ritual mechanically.
