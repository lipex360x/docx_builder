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

## Agent delegation — non-negotiable

This repo has two specialized subagents under `.claude/agents/`. **When the user asks you to work on a GitHub issue, you do not write the work yourself — you delegate to the correct agent based on the issue's label.**

| Issue label | Agent | What it does |
|---|---|---|
| `needs-design` | `docx-builder-architect` | Drives the design pass: enumerates forks, proposes options with trade-offs, captures user decisions across rounds, publishes the final design + AC, flips the label to `enhancement`. Read-only on code. |
| `enhancement` / `bug` / `polish` (with concrete AC) | `docx-builder-implementer` | Implements end-to-end: TDD red → green → refactor, follows the quality pipeline, iterates through pre-commit failures, commits, pushes, opens the PR, writes a barriers report under `.dev-quality-logs/`. |

### Before invoking either agent

You (the main session) are responsible for:

1. **Confirming the issue label.** Fetch with `gh issue view <N> --repo lipex360x/docx_builder --json labels`. The wrong agent on the wrong label is a process violation.
2. **For implementer only — checking out the branch.** The implementer expects to start on `feat/<slug>-<N>`, `fix/<slug>-<N>`, or `chore/<slug>-<N>`. Compose the branch name from the issue title using the convention documented in the "Branch per issue" section, then:

   ```bash
   git checkout main && git pull
   git checkout -b <type>/<slug>-<N>
   ```

   The implementer verifies via `git branch --show-current` and stops if it lands on `main`.

3. **For architect — no branch prep needed.** The architect operates against `main` and only touches `.designs/` (gitignored) and the GitHub issue.

### When the agents return

- **Implementer** returns a short status block (PR url, commit count, pre-commit iterations, barriers report path). Read the barriers report yourself — it captures friction points that may signal a needed update to the agent prompt or to a `dev-quality` rule.
- **Architect** returns either `DESIGN DRAFT ready` (needs user input on the forks) or `DESIGN FINALIZED` (issue body updated, label flipped, ready for implementer). In the draft case, you ask the user the forks via `AskUserQuestion`, append decisions to `.designs/issue-<N>.md`, then re-invoke the architect.

### When NOT to delegate

The agents are for **issue-driven work**. Do not delegate when the user:

- Asks an exploratory question ("how does X work in this repo?").
- Requests a small inline change that does not correspond to an open issue (e.g. typo fix in `README.md`).
- Wants a discussion ("should we approach Y like this?").

For those, you respond directly. The agents are tools, not the default.

### What you never do

- Write production code yourself when an issue exists. Open the issue, ask for the right agent, or delegate immediately.
- Skip the label check. A `needs-design` issue is not implementer territory.
- Re-invoke the architect without updating `.designs/issue-<N>.md` first — the architect wakes blind otherwise.

## Layout

```
docx_builder/
  cli/                # argparse entry package — one module per subcommand
    __init__.py       # DESCRIPTION + EPILOG + _build_parser() + main()
    _shared.py        # structured next-step error printers + resolve_directory()
    _build.py         # build command (+ --pdf flag); register() + handle()
    _init.py          # init command; register() + handle()
    _export.py        # export pdf command; register() + handle()
    _install.py       # install skill command (interactive scope prompt)
  builder.py          # build() + init_project() + has_toc()
  export.py           # export_pdf() + finalize_source() via Word + JXA (macOS)
  report.py           # post-build report: words, reading time, em-dash counter
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
tests/                # pytest suite (163 tests)
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
uv tool install .                  # snapshot install
uv tool install --editable .       # live install — source changes propagate without reinstall
```

For active development on the package, prefer `--editable`. The global `~/.local/bin/docx_builder` then reads directly from the repo's `docx_builder/` package, so edits to `.py` files and bundled data are visible on the next invocation. Use the snapshot form only when you want a frozen copy.

Then from any directory:

```bash
docx_builder init                       # write a marker content.yaml (no images/ dir)
docx_builder build                      # build using content.yaml in cwd
docx_builder build /some/dir            # build in another dir
docx_builder build --output Custom.docx
docx_builder build --template-dir ~/templates
docx_builder install skill              # install Claude Code skill (asks scope)
docx_builder install skill --scope local|global
```

If installed as **snapshot** (`uv tool install .`), re-run after pulling or after editing the package:

```bash
uv tool install --reinstall .
```

If installed as **editable** (`uv tool install --editable .`), source edits are picked up automatically — no reinstall needed for `.py` or bundled-data changes. Only re-run when:

- `[project.scripts]` entries change (e.g. new subcommand binary)
- Dependencies change in `pyproject.toml`
- Switching back to a snapshot install

## Styles

Visual properties are controlled by the optional `styles:` block in `content.yaml`. Cascade: built-in defaults → `styles:` block → inline `style:` per section. Full schema in [`docs/styles-reference.md`](docs/styles-reference.md).

## DOCX → PDF workflow

`docx_builder export pdf` (and `build --pdf`) drive Microsoft Word via JXA on macOS: they update every TOC and all fields, then save, and by default write the populated `.docx` back over the source. `build` alone also finalises the TOC automatically when the document declares one (no PDF needed). Shipped in v0.2.0 / v0.4.0; see [issue #1](https://github.com/lipex360x/docx_builder/issues/1).

Manual fallback (off macOS or without Word): open the `.docx` in Word, `Cmd+A` then `F9` to update fields, then `File` → `Save As…` → `PDF`.

`libreoffice --headless --convert-to pdf` is intentionally avoided: it changes fonts, spacing and field rendering. Word's renderer matches what a marker sees.

## Versioning

Semantic Versioning. Tagged releases on `main`. Tag format: `vX.Y.Z`.

Current release: **v0.4.0**.

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

- [#1](https://github.com/lipex360x/docx_builder/issues/1) — `docx_builder export pdf` + `build --pdf` (macOS + Microsoft Word). Includes Word permission-dialog workaround via scratch directory, and real page-count reporting. **Ready to implement.**
- [#2](https://github.com/lipex360x/docx_builder/issues/2) — QoL bug fix + small features: h3 colour bug, `--open` flag, deprecation warning for `hide_page_counter`, `init` message polish, Word auth doc. **Ready to implement.**
- [#3](https://github.com/lipex360x/docx_builder/issues/3) — Content reuse between `content.yaml` files (e.g. shared work history across two CVs). **Needs design** — three candidate mechanisms (`extends:` / `include:` / YAML anchors), no AC yet.
- Extensible section type registry — `register_section_type(name, handler)` for plugging in new section calls.
- PDF-to-YAML transcription workflow — guided protocol for analysing a source PDF and emitting matching `content.yaml`.

When opening a new roadmap item: create a GitHub issue, link it from `CHANGELOG.md` under `[Unreleased]`, and reference it back from this section.

**Issue maturity tags:**

- **Ready to implement** — full AC, solution shape known. Pick up and code.
- **Needs design** — captures the problem and candidate mechanisms, but no acceptance criteria yet. A design pass must precede implementation. Do not write AC until a path is chosen — see `feedback-issue-detail-strategy` memory for the rationale.

## Issue lifecycle — mandatory final-step checklist

Every issue must end with the same closure block. This keeps the docs, the skill, and the global skill copy aligned with what shipped, so future Claude Code sessions never operate on stale information.

When opening any new issue, append this section to the body verbatim (adjust the bracketed text only):

```markdown
---

## Final step — documentation and skill sync (mandatory for every issue)

Before closing this issue:

- [ ] **CHANGELOG.md** — move the entry from `[Unreleased]` into a new `[X.Y.Z]` section with the date if shipping as a tagged release. Otherwise leave under `[Unreleased]`.
- [ ] **`docx_builder/skill/SKILL.md`** — update so future Claude Code sessions know about the change.
- [ ] **`CLAUDE.md`** — update only if the change affects developer workflow, repo conventions, or available commands.
- [ ] **`README.md`** — update if the change affects user-facing commands, flags, build output, install steps, or the project structure tree.
- [ ] **`docs/styles-reference.md`** — update if any styling field gained or lost behaviour.
- [ ] **Global skill sync** — `cp docx_builder/skill/SKILL.md ~/www/claude/.brain/skills/docx_builder/SKILL.md`
- [ ] **Editable install check** — if user is on snapshot install, run `uv tool install --reinstall .` to pick up changes. Editable installs propagate automatically.
- [ ] **Tag** — only if the change is functional (see "When NOT to tag" above).
```

Implementation guideline for the assistant: do **not** declare an issue resolved until every applicable line in this block is done. The global skill sync (`cp` into `.brain`) is the easiest one to forget and the most damaging when forgotten — without it, the next Claude Code session reads the old behaviour from the global skill cache and gives wrong guidance.

### Branch per issue

Every issue with concrete acceptance criteria (i.e. not `needs-design`) is implemented on its **own branch**, not on `main`. The branch isolates the change for review via PR and keeps `main` mergeable at all times.

**Naming convention:** `<type>/<short-slug>-<issue-number>`

| Type prefix | When to use | Example |
|---|---|---|
| `feat/` | New feature | `feat/pdf-export-1` |
| `fix/` | Bug fix | `fix/h3-heading-color-2` |
| `chore/` | Polish, docs, internal | `chore/init-message-2` |
| `design/` | ADR / design pass (rare; usually goes via PR to `main`) | `design/content-reuse-3` |

The short-slug is 2–4 words, kebab-cased, from the issue title. The issue number always trails so a branch is greppable by issue.

**Workflow:**

```bash
git checkout main && git pull
git checkout -b feat/pdf-export-1
# ... work, commit, push ...
gh pr create --title "feat: PDF export (closes #1)" --body "Closes #1"
```

Multiple items from the same issue (e.g. `#2` has 5 sub-items) usually share one branch unless the items naturally split into independent shippable units — in which case open separate PRs with `feat/...-2-part1`, `feat/...-2-part2`, etc., and each PR partially closes the issue via comment, fully closing only on the last.

**Needs-design issues are different:** the design pass produces an ADR via a small PR (often direct on a `design/...` branch). Implementation only starts after the ADR merges, at which point a fresh implementation branch (`feat/...`) is opened.

### Marking progress on the checklist

Checkboxes in `## Acceptance criteria` and `## Final step — documentation and skill sync` are not decorative. They must be ticked as work progresses so the issue body reflects observable state.

**Convention:**

1. **Edit the issue body** (`gh issue edit <N> --body-file ...` or via the GitHub UI) flipping `- [ ]` to `- [x]` for each item as it is completed. Do this **before** the commit that lands the item — not in a single batch at the end. If the commit fails or the implementation gets backed out, revert the tick.
2. **PR body** references the issue with `Closes #N` so merge auto-closes it. The PR does not duplicate the checklist — reviewers click through to the issue.
3. **Before requesting merge**, scan the issue body: every applicable `- [ ]` must be `- [x]` or have an explicit rationale comment in the issue (e.g. "deferred to follow-up, see #X"). A merged PR with unchecked AC items is a process violation, not a shortcut.

Why edit the issue body rather than the PR body or just letting the merge close the issue: AI agents in fresh contexts use the issue body as the spec. If a future Claude Code re-opens the implementation (refactor, bug-fix, related feature) and the AC items still show `- [ ]`, the assistant will believe the work is incomplete and either redo it or get confused. The ticked state is the durable signal that "this AC was satisfied".

## Development

```bash
uv sync
uv run pytest
uv run ruff check docx_builder tests
uv run --with mypy mypy docx_builder
```

TDD: write failing test first, implement minimum to pass, refactor.

Quality gates (all must be green before commit):

- pytest — 163 tests, ~2s wall time
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

### Syncing the Claude Code skill

The bundled `docx_builder/skill/SKILL.md` is also installed globally under `~/.brain/skills/docx_builder/` so it surfaces in every Claude Code session (and the `.brain` sync script picks it up).

After editing `docx_builder/skill/SKILL.md` in this repo, copy it across:

```bash
cp docx_builder/skill/SKILL.md ~/www/claude/.brain/skills/docx_builder/SKILL.md
```

The global symlink `~/.claude/skills/docx_builder → ~/www/claude/.brain/skills/docx_builder` already exists; only the file content needs the manual copy.
