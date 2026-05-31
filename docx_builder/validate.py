from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from docx_builder.builder import resolve_content_dir
from docx_builder.report import EM_DASH

HORIZONTAL_BAR = "―"
FIGURE_DASH = "‒"
EN_DASH = "–"

DEFAULT_FORBIDDEN: dict[str, str] = {
    EM_DASH: "em-dash (U+2014)",
    HORIZONTAL_BAR: "horizontal bar (U+2015)",
    FIGURE_DASH: "figure dash (U+2012)",
}
STRICT_FORBIDDEN: dict[str, str] = {**DEFAULT_FORBIDDEN, EN_DASH: "en-dash (U+2013)"}

_PROSE_FIELDS: dict[str, tuple[str, ...]] = {
    "h1": ("text",),
    "h2": ("text",),
    "h3": ("text",),
    "body": ("text",),
    "bullet": ("text",),
    "reference": ("text",),
    "bold_lead": ("bold", "rest"),
    "figure": ("caption",),
    "figure_pair": ("caption",),
}

_SNIPPET_RADIUS = 15


@dataclass(frozen=True)
class Violation:
    location: str
    char: str
    char_name: str
    position: int
    snippet: str


def forbidden_chars(*, strict: bool) -> dict[str, str]:
    return STRICT_FORBIDDEN if strict else DEFAULT_FORBIDDEN


def _snippet(text: str, position: int) -> str:
    start = max(0, position - _SNIPPET_RADIUS)
    end = position + _SNIPPET_RADIUS + 1
    return f"{text[start:position]}[{text[position]}]{text[position + 1 : end]}"


def scan_text(text: str, location: str, forbidden: dict[str, str]) -> list[Violation]:
    violations: list[Violation] = []
    for position, char in enumerate(text):
        name = forbidden.get(char)
        if name is None:
            continue
        violations.append(
            Violation(
                location=location,
                char=char,
                char_name=name,
                position=position,
                snippet=_snippet(text, position),
            )
        )
    return violations


def _scan_sections(sections: list[dict[str, Any]], origin: str, forbidden: dict[str, str]) -> list[Violation]:
    violations: list[Violation] = []
    for index, item in enumerate(sections):
        call = str(item.get("call", ""))
        for field in _PROSE_FIELDS.get(call, ()):
            value = item.get(field)
            if not isinstance(value, str):
                continue
            violations.extend(scan_text(value, f"{origin}[{index}].{call}.{field}", forbidden))
    return violations


def scan_content(data: dict[str, Any], forbidden: dict[str, str]) -> list[Violation]:
    front_matter = data.get("front_matter") or []
    sections = data.get("sections") or []
    return _scan_sections(front_matter, "front_matter", forbidden) + _scan_sections(sections, "sections", forbidden)


def _load_content(project_dir: Path) -> dict[str, Any]:
    content_dir = resolve_content_dir(project_dir)
    content_path = content_dir / "content.yaml"
    if not content_path.exists():
        raise FileNotFoundError(f"content.yaml not found in {content_dir}")
    with open(content_path, encoding="utf-8") as content_file:
        data: dict[str, Any] = yaml.safe_load(content_file) or {}
    return data


def validate_project(project_dir: Path, *, strict: bool, also: list[Path]) -> list[Violation]:
    forbidden = forbidden_chars(strict=strict)
    violations = scan_content(_load_content(project_dir), forbidden)
    for extra in also:
        violations.extend(scan_text(extra.read_text(encoding="utf-8"), extra.name, forbidden))
    return violations


def format_violations(violations: list[Violation]) -> str:
    lines = [f"  {item.location} (pos {item.position}): {item.char_name}  {item.snippet}" for item in violations]
    lines.append(f"\n{len(violations)} forbidden character(s) found in prose.")
    return "\n".join(lines)
