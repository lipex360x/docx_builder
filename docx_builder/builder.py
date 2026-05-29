from __future__ import annotations

import os
import sys
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any

import yaml
from docx import Document
from docx.document import Document as DocumentType

from docx_builder.pagination import add_page_numbers
from docx_builder.renderer import fill_cover, render_sections
from docx_builder.styles import StyleResolver

_DEFAULT_OUTPUT_PATTERN = "Report_{number}.docx"
_FALLBACK_OUTPUT_NAME = "Report.docx"


def _resolve_template_path(
    template_name: str,
    template_dir: str | Path | None,
    project_dir: Path,
) -> Path | None:
    template_path = Path(template_name)

    if template_path.is_absolute():
        return template_path if template_path.exists() else None

    if template_path.parent != Path("."):
        candidate = (project_dir / template_path).resolve()
        return candidate if candidate.exists() else None

    if template_dir is not None:
        candidate = Path(template_dir) / template_name
        if candidate.exists():
            return candidate

    try:
        bundled = files("docx_builder.templates").joinpath(template_name)
        with as_file(bundled) as resolved:
            resolved_path = Path(resolved)
            if resolved_path.exists():
                return resolved_path
    except (FileNotFoundError, ModuleNotFoundError):
        pass

    return None


def _resolve_output_path(project_dir: Path, cover: dict[str, Any], override: str | None) -> Path:
    if override:
        return project_dir / override if not Path(override).is_absolute() else Path(override)

    pattern_value = cover.get("output") if cover else None
    pattern = str(pattern_value) if pattern_value else _DEFAULT_OUTPUT_PATTERN

    fields = {key: str(value) for key, value in (cover or {}).items() if isinstance(value, str | int)}

    try:
        filename = pattern.format(**fields)
    except KeyError:
        filename = _FALLBACK_OUTPUT_NAME

    return project_dir / filename


def _load_document(
    cover: dict[str, Any],
    template_dir: str | Path | None,
    project_dir: Path,
) -> DocumentType:
    template_name = cover.get("template") if cover else None
    if not template_name:
        return Document()

    cover_path = _resolve_template_path(str(template_name), template_dir, project_dir)
    if cover_path is None:
        raise FileNotFoundError(f"cover template not found: {template_name}")
    return Document(str(cover_path))


def _warn_if_deprecated_flag(sections: list[dict[str, Any]]) -> None:
    if os.environ.get("DOCX_BUILDER_NO_DEPRECATION"):
        return
    if any(bool(section.get("hide_page_counter")) for section in sections):
        print(
            "warning: 'hide_page_counter' is deprecated; use the top-level 'front_matter:' block instead.\n"
            "         See docs/styles-reference.md#page-numbering",
            file=sys.stderr,
        )


def _normalise_sections(data: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    front_matter: list[dict[str, Any]] = list(data.get("front_matter") or [])
    body_sections: list[dict[str, Any]] = list(data.get("sections") or [])
    _warn_if_deprecated_flag(body_sections)

    if front_matter:
        flagged_front = [{**item, "hide_page_counter": True} for item in front_matter]
        merged = flagged_front + body_sections
        return merged, bool(flagged_front)

    has_hidden = any(bool(section.get("hide_page_counter")) for section in body_sections)
    return body_sections, has_hidden


def _load_content_data(project_path: Path) -> dict[str, Any]:
    content_path = project_path / "content.yaml"
    if not content_path.exists():
        raise FileNotFoundError(f"content.yaml not found in {project_path}")

    with open(content_path) as content_file:
        data: dict[str, Any] = yaml.safe_load(content_file) or {}
    return data


def _contains_toc(items: list[dict[str, Any]]) -> bool:
    return any(item.get("call") == "toc" for item in items)


def has_toc(project_dir: str | Path) -> bool:
    project_path = Path(project_dir).resolve()
    data = _load_content_data(project_path)
    front_matter: list[dict[str, Any]] = list(data.get("front_matter") or [])
    body_sections: list[dict[str, Any]] = list(data.get("sections") or [])
    return _contains_toc(front_matter) or _contains_toc(body_sections)


def resolve_output_path(project_dir: str | Path, output_override: str | None = None) -> Path:
    project_path = Path(project_dir).resolve()
    data = _load_content_data(project_path)

    cover: dict[str, Any] = data.get("cover") or {}
    return _resolve_output_path(project_path, cover, output_override)


def build(
    project_dir: str | Path,
    *,
    template_dir: str | Path | None = None,
    output_override: str | None = None,
) -> Path:
    project_path = Path(project_dir).resolve()
    data = _load_content_data(project_path)

    cover: dict[str, Any] = data.get("cover") or {}
    styles_block: dict[str, dict[str, Any]] = data.get("styles") or {}
    page_numbers_enabled = bool(data.get("page_numbers", True))
    resolver = StyleResolver(global_overrides=styles_block)

    output_path = _resolve_output_path(project_path, cover, output_override)
    images_dir = project_path / "images"

    merged_sections, has_front_matter = _normalise_sections(data)

    document = _load_document(cover, template_dir, project_path)
    if cover:
        fill_cover(document, cover)
    render_sections(document, merged_sections, images_dir=str(images_dir), resolver=resolver)

    if page_numbers_enabled:
        footer_style = resolver.resolve("footer")
        add_page_numbers(document, style=footer_style, skip_cover_sections=has_front_matter)

    document.save(str(output_path))
    return output_path


def init_project(project_dir: str | Path, *, force: bool = False) -> Path:
    project_path = Path(project_dir).resolve()
    project_path.mkdir(parents=True, exist_ok=True)

    content_path = project_path / "content.yaml"
    if content_path.exists() and not force:
        raise FileExistsError(f"content.yaml already exists in {project_path} (use --force)")

    skeleton = files("docx_builder.templates").joinpath("content.skeleton.yaml").read_text()
    content_path.write_text(skeleton)

    return content_path
