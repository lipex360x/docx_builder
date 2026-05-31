from __future__ import annotations

from typing import Any

from docx.document import Document
from docx.enum.section import WD_SECTION
from docx.shared import Pt

from docx_builder.elements import body, bold_lead, bullet, heading_1, heading_2, heading_3, page_break, reference
from docx_builder.figure import figure as _figure_base
from docx_builder.figure import figure_pair as _figure_pair_base
from docx_builder.styles import StyleResolver
from docx_builder.summary import build_summary
from docx_builder.table import table as _table_base

_TEXT_DISPATCHERS = {
    "h1": heading_1,
    "h2": heading_2,
    "h3": heading_3,
    "body": body,
    "bullet": bullet,
    "reference": reference,
}


def fill_cover(document: Document, cover: dict[str, object]) -> None:
    if not document.tables:
        return
    cover_table = document.tables[0]
    rows: list[object] = cover.get("rows", [])  # type: ignore[assignment]
    for index, value in enumerate(rows):
        if index >= len(cover_table.rows):
            break
        cover_table.rows[index].cells[1].paragraphs[0].add_run(str(value))

    ai_declaration = cover.get("ai_declaration")
    if not ai_declaration:
        return
    ai_paragraph = document.add_paragraph()
    ai_paragraph.paragraph_format.space_before = Pt(14)
    bold_run = ai_paragraph.add_run("AI Use Declaration: ")
    bold_run.bold = True
    bold_run.font.size = Pt(11)
    rest_run = ai_paragraph.add_run(str(ai_declaration))
    rest_run.font.size = Pt(11)


def _render_media(
    document: Document,
    item: dict[str, Any],
    *,
    images_dir: str,
    resolver: StyleResolver,
    inline_style: dict[str, Any] | None,
) -> bool:
    call = str(item["call"])

    if call == "figure":
        _figure_base(
            document,
            str(item["filename"]),
            str(item["label"]),
            str(item["caption"]),
            images_dir=images_dir,
            figure_style=resolver.resolve("figure", inline_style),
            caption_style=resolver.resolve("figure_caption", item.get("caption_style")),
            width=item.get("width"),
        )
        return True

    if call == "figure_pair":
        _figure_pair_base(
            document,
            str(item["filename1"]),
            str(item["filename2"]),
            str(item["label"]),
            str(item["caption"]),
            images_dir=images_dir,
            figure_style=resolver.resolve("figure_pair", inline_style),
            caption_style=resolver.resolve("figure_caption", item.get("caption_style")),
            width1=item.get("width1"),
            width2=item.get("width2"),
        )
        return True

    if call == "table":
        _table_base(
            document,
            [list(row) for row in item.get("rows", [])],
            resolver.resolve("table", inline_style),
            header=item.get("header"),
            widths=item.get("widths"),
            borders=bool(item.get("borders", True)),
            col_align=item.get("col_align"),
        )
        return True

    return False


def _render_item(
    document: Document,
    item: dict[str, Any],
    *,
    images_dir: str,
    resolver: StyleResolver,
) -> None:
    call = str(item["call"])
    inline_style = item.get("style") if isinstance(item.get("style"), dict) else None

    if call == "page_break":
        page_break(document)
        return

    if call == "toc":
        build_summary(document, levels=str(item.get("levels", "1-2")))
        return

    if call in _TEXT_DISPATCHERS:
        _TEXT_DISPATCHERS[call](document, str(item["text"]), resolver.resolve(call, inline_style))
        return

    if call == "bold_lead":
        bold_lead(document, str(item["bold"]), str(item["rest"]), resolver.resolve("bold_lead", inline_style))
        return

    if _render_media(document, item, images_dir=images_dir, resolver=resolver, inline_style=inline_style):
        return

    raise ValueError(f"unknown call: {call!r}")


def render_sections(
    document: Document,
    sections: list[dict[str, Any]],
    *,
    images_dir: str,
    resolver: StyleResolver,
) -> None:
    has_any_hidden = any(bool(item.get("hide_page_counter")) for item in sections)
    section_break_added = False

    for item in sections:
        hide = bool(item.get("hide_page_counter", False))
        call = str(item["call"])

        if has_any_hidden and not hide and not section_break_added:
            document.add_section(WD_SECTION.NEW_PAGE)
            section_break_added = True
            if call == "page_break":
                continue

        _render_item(document, item, images_dir=images_dir, resolver=resolver)
