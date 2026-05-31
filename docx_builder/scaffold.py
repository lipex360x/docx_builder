from __future__ import annotations

import stat
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

_PLACEHOLDER = "__PROJECT_NAME__"
_EXECUTABLE_SUFFIXES = (".sh", ".py")

BASE_DIRS: tuple[str, ...] = (
    "report",
    "report/images",
    "report/assets",
    "report/output",
    "report/templates",
    ".work",
)


@dataclass(frozen=True)
class Layer:
    dirs: tuple[str, ...]
    pulls: tuple[str, ...] = ()
    files: tuple[tuple[str, str], ...] = ()


LAYERS: dict[str, Layer] = {
    "brief": Layer(("brief",)),
    "references": Layer(("references",)),
    "src": Layer(("src",)),
    "meta": Layer(("meta",)),
    "tools": Layer(("tools",)),
    "monitor": Layer(
        ("tools/monitor",),
        pulls=("tools",),
        files=(
            ("monitor/watch_screenshots.sh.tmpl", "tools/monitor/watch_screenshots.sh"),
            ("monitor/move_screenshot.py.tmpl", "tools/monitor/move_screenshot.py"),
        ),
    ),
    "ai-check": Layer(
        ("tools/ai-detection", "report/ai-check"),
        pulls=("tools",),
        files=(("ai-detection/README.md.tmpl", "tools/ai-detection/README.md"),),
    ),
}

ALL_LAYERS: tuple[str, ...] = tuple(LAYERS)


@dataclass
class ScaffoldResult:
    created: list[str]
    skipped: list[str]


def resolve_layers(*, full: bool, with_layers: list[str]) -> set[str]:
    requested = set(ALL_LAYERS) if full else set(with_layers)
    unknown = requested - set(LAYERS)
    if unknown:
        raise ValueError(f"unknown layer(s): {', '.join(sorted(unknown))}")
    expanded = set(requested)
    for layer in requested:
        expanded.update(LAYERS[layer].pulls)
    return expanded


def _read_template(relative: str) -> str:
    resource = files("docx_builder.templates").joinpath("scaffold").joinpath(relative)
    return resource.read_text(encoding="utf-8")


def _render(relative: str, name: str) -> str:
    return _read_template(relative).replace(_PLACEHOLDER, name)


def _ensure_dir(project_dir: Path, relative: str, result: ScaffoldResult) -> None:
    target = project_dir / relative
    if target.exists():
        return
    target.mkdir(parents=True, exist_ok=True)
    result.created.append(f"{relative}/")


def _write_file(project_dir: Path, relative: str, content: str, *, force: bool, result: ScaffoldResult) -> None:
    target = project_dir / relative
    if target.exists() and not force:
        result.skipped.append(relative)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    if target.suffix in _EXECUTABLE_SUFFIXES:
        target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    result.created.append(relative)


def _add_gitkeep(project_dir: Path, relative: str, result: ScaffoldResult) -> None:
    target = project_dir / relative
    if not target.is_dir() or any(target.iterdir()):
        return
    (target / ".gitkeep").write_text("", encoding="utf-8")
    result.created.append(f"{relative}/.gitkeep")


def scaffold(project_dir: Path, *, layers: set[str], name: str, cover: bool, force: bool) -> ScaffoldResult:
    result = ScaffoldResult(created=[], skipped=[])
    project_dir.mkdir(parents=True, exist_ok=True)

    all_dirs = list(BASE_DIRS)
    for layer in sorted(layers):
        all_dirs.extend(LAYERS[layer].dirs)
    for relative in all_dirs:
        _ensure_dir(project_dir, relative, result)

    content_template = "content_b.yaml.tmpl" if cover else "content_a.yaml.tmpl"
    _write_file(project_dir, "report/content.yaml", _render(content_template, name), force=force, result=result)
    _write_file(project_dir, "CLAUDE.md", _render("claude.md.tmpl", name), force=force, result=result)
    _write_file(project_dir, ".gitignore", _read_template("gitignore.tmpl"), force=force, result=result)

    for layer in sorted(layers):
        for template_relative, destination in LAYERS[layer].files:
            _write_file(project_dir, destination, _render(template_relative, name), force=force, result=result)

    for relative in all_dirs:
        _add_gitkeep(project_dir, relative, result)

    return result


def format_summary(result: ScaffoldResult, project_dir: Path) -> str:
    lines = [f"Scaffolded into {project_dir}:"]
    lines.extend(f"  + {entry}" for entry in sorted(result.created))
    lines.extend(f"  = {entry} (exists, left unchanged)" for entry in sorted(result.skipped))
    return "\n".join(lines)
