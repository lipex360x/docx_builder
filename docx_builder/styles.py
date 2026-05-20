from __future__ import annotations

import re
from importlib.resources import files
from typing import Any

import yaml
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

_ALIGN_MAP = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}

_LENGTH_RE = re.compile(r"^(-?\d+(?:\.\d+)?)\s*(pt|in|cm|mm)?$", re.IGNORECASE)
_HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")


def parse_length_pt(value: object) -> Pt | None:
    if value is None:
        return None
    if isinstance(value, Pt):
        return value
    if isinstance(value, int | float):
        return Pt(float(value))
    if isinstance(value, str):
        match = _LENGTH_RE.match(value.strip())
        if match is None:
            raise ValueError(f"invalid length: {value!r}")
        number, unit = match.groups()
        unit = (unit or "pt").lower()
        if unit == "pt":
            return Pt(float(number))
        raise ValueError(f"expected pt for this field, got {value!r}")
    raise TypeError(f"unsupported length type: {type(value).__name__}")


_INCH_FACTORS = {"in": 1.0, "pt": 1.0 / 72.0, "cm": 1.0 / 2.54, "mm": 1.0 / 25.4}


def parse_length_inches(value: object) -> Inches | None:
    if value is None:
        return None
    if isinstance(value, Inches):
        return value
    if isinstance(value, int | float):
        return Inches(float(value))
    if not isinstance(value, str):
        raise TypeError(f"unsupported length type: {type(value).__name__}")
    match = _LENGTH_RE.match(value.strip())
    if match is None:
        raise ValueError(f"invalid length: {value!r}")
    number, unit = match.groups()
    unit = (unit or "in").lower()
    factor = _INCH_FACTORS.get(unit)
    if factor is None:
        raise ValueError(f"unsupported unit for inches: {value!r}")
    return Inches(float(number) * factor)


def parse_color(value: object) -> RGBColor | None:
    if value is None:
        return None
    if isinstance(value, RGBColor):
        return value
    if isinstance(value, str):
        match = _HEX_RE.match(value.strip())
        if match is None:
            raise ValueError(f"invalid color (use #RRGGBB): {value!r}")
        hex_digits = match.group(1)
        return RGBColor(int(hex_digits[0:2], 16), int(hex_digits[2:4], 16), int(hex_digits[4:6], 16))
    raise TypeError(f"unsupported color type: {type(value).__name__}")


def parse_align(value: object) -> WD_ALIGN_PARAGRAPH | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"align must be a string, got {type(value).__name__}")
    key = value.strip().lower()
    if key not in _ALIGN_MAP:
        raise ValueError(f"invalid align (use left/center/right/justify): {value!r}")
    return _ALIGN_MAP[key]


def _load_defaults() -> dict[str, dict[str, Any]]:
    text = files("docx_builder.templates").joinpath("default_styles.yaml").read_text()
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise TypeError("default_styles.yaml must be a mapping")
    return {key: dict(value) for key, value in data.items()}


def _merge(*dicts: dict[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for source in dicts:
        if source:
            merged.update(source)
    return merged


class StyleResolver:
    def __init__(self, global_overrides: dict[str, dict[str, Any]] | None = None) -> None:
        self._defaults = _load_defaults()
        self._global = global_overrides or {}

    def resolve(self, section_type: str, inline: dict[str, Any] | None = None) -> dict[str, Any]:
        defaults = self._defaults.get(section_type, {})
        global_override = self._global.get(section_type, {})
        return _merge(defaults, global_override, inline)


def apply_paragraph_style(paragraph: Any, style: dict[str, Any]) -> None:
    pf = paragraph.paragraph_format

    align = parse_align(style.get("align"))
    if align is not None:
        paragraph.alignment = align

    space_before = parse_length_pt(style.get("space_before"))
    if space_before is not None:
        pf.space_before = space_before

    space_after = parse_length_pt(style.get("space_after"))
    if space_after is not None:
        pf.space_after = space_after

    indent_left = parse_length_inches(style.get("indent_left"))
    if indent_left is not None:
        pf.left_indent = indent_left

    indent_first = parse_length_inches(style.get("indent_first_line"))
    if indent_first is not None:
        pf.first_line_indent = indent_first


def apply_run_style(run: Any, style: dict[str, Any]) -> None:
    font_size = parse_length_pt(style.get("font_size"))
    if font_size is not None:
        run.font.size = font_size

    font_family = style.get("font_family")
    if isinstance(font_family, str):
        run.font.name = font_family

    color = parse_color(style.get("color"))
    if color is not None:
        run.font.color.rgb = color

    bold = style.get("bold")
    if isinstance(bold, bool):
        run.bold = bold

    italic = style.get("italic")
    if isinstance(italic, bool):
        run.italic = italic
