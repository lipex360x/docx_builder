from __future__ import annotations

from typing import Any

from docx.document import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Emu, RGBColor
from docx.table import Table, _Cell

from docx_builder.styles import apply_paragraph_style, apply_run_style, parse_align, parse_color

_WIDTH_TOLERANCE = 0.5
_VALIGN = ("top", "center", "bottom")


def remove_table_borders(table: Table) -> None:
    _set_all_borders(table, "none")


def set_table_borders(table: Table, *, size: int = 4, color: str = "000000") -> None:
    _set_all_borders(table, "single", size=size, color=color)


def _set_all_borders(table: Table, value: str, *, size: int = 4, color: str = "000000") -> None:
    tbl_xml = table._tbl
    table_properties = tbl_xml.find(qn("w:tblPr"))
    if table_properties is None:
        table_properties = OxmlElement("w:tblPr")
        tbl_xml.insert(0, table_properties)
    table_borders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        border_element = OxmlElement(f"w:{side}")
        border_element.set(qn("w:val"), value)
        if value != "none":
            border_element.set(qn("w:sz"), str(size))
            border_element.set(qn("w:space"), "0")
            border_element.set(qn("w:color"), color)
        table_borders.append(border_element)
    table_properties.append(table_borders)


def _validate_shape(
    rows: list[list[Any]],
    header: list[Any] | None,
    widths: list[float] | None,
    col_align: list[str] | None,
) -> int:
    if header is None and not rows:
        raise ValueError("table requires header or at least one row")
    column_count = len(header) if header is not None else len(rows[0])
    if column_count == 0:
        raise ValueError("table requires at least one column")
    for row_index, row in enumerate(rows):
        if len(row) != column_count:
            raise ValueError(f"table row {row_index} has {len(row)} cell(s), expected {column_count}")
    if widths is not None:
        if len(widths) != column_count:
            raise ValueError(f"table widths has {len(widths)} entry(ies), expected {column_count}")
        total = sum(widths)
        if abs(total - 100) > _WIDTH_TOLERANCE:
            raise ValueError(f"table widths must sum to 100, got {total}")
    if col_align is not None and len(col_align) != column_count:
        raise ValueError(f"table col_align has {len(col_align)} entry(ies), expected {column_count}")
    return column_count


def table(
    document: Document,
    rows: list[list[Any]],
    style: dict[str, Any],
    *,
    header: list[Any] | None = None,
    widths: list[float] | None = None,
    borders: bool = True,
    col_align: list[str] | None = None,
) -> Table:
    column_count = _validate_shape(rows, header, widths, col_align)

    body_rows: list[tuple[list[Any], bool]] = []
    if header is not None:
        body_rows.append((header, True))
    body_rows.extend((row, False) for row in rows)

    table_element: Table = document.add_table(rows=len(body_rows), cols=column_count)
    table_element.autofit = False
    if borders:
        set_table_borders(table_element)
    else:
        remove_table_borders(table_element)

    _populate(table_element, body_rows, style, column_count, col_align=col_align)

    if widths is not None:
        _apply_widths(document, table_element, widths)
    return table_element


def _fill_hex(value: object) -> str | None:
    color = parse_color(value)
    return str(color) if color is not None else None


def _row_fills(
    body_rows: list[tuple[list[Any], bool]], header_fill: str | None, stripe_fill: str | None
) -> list[str | None]:
    fills: list[str | None] = []
    data_index = 0
    for _values, is_header in body_rows:
        if is_header:
            fills.append(header_fill)
            continue
        fills.append(stripe_fill if data_index % 2 == 1 else None)
        data_index += 1
    return fills


def _shade_cell(cell: _Cell, fill_hex: str) -> None:
    shading = OxmlElement("w:shd")
    shading.set(qn("w:val"), "clear")
    shading.set(qn("w:color"), "auto")
    shading.set(qn("w:fill"), fill_hex)
    cell._tc.get_or_add_tcPr().append(shading)


def _set_valign(cell: _Cell, value: str) -> None:
    vertical = OxmlElement("w:vAlign")
    vertical.set(qn("w:val"), value)
    cell._tc.get_or_add_tcPr().append(vertical)


def _parse_valign(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or value.strip().lower() not in _VALIGN:
        raise ValueError(f"invalid valign (use top/center/bottom): {value!r}")
    return value.strip().lower()


def _resolve_col_aligns(col_align: list[str] | None, column_count: int) -> list[WD_ALIGN_PARAGRAPH | None]:
    if col_align is None:
        return [None] * column_count
    return [parse_align(value) for value in col_align]


def _populate(
    table_element: Table,
    body_rows: list[tuple[list[Any], bool]],
    style: dict[str, Any],
    column_count: int,
    *,
    col_align: list[str] | None,
) -> None:
    header_bold = bool(style.get("header_bold", True))
    header_color = parse_color(style.get("header_color"))
    fills = _row_fills(body_rows, _fill_hex(style.get("header_fill")), _fill_hex(style.get("stripe_fill")))
    col_aligns = _resolve_col_aligns(col_align, column_count)
    valign = _parse_valign(style.get("valign"))
    for row_index, ((values, is_header), fill) in enumerate(zip(body_rows, fills, strict=True)):
        color = header_color if is_header else None
        for column_index in range(column_count):
            cell = table_element.cell(row_index, column_index)
            value = values[column_index] if column_index < len(values) else ""
            _render_cell(
                cell, value, style, bold=is_header and header_bold, align=col_aligns[column_index], color=color
            )
            if fill is not None:
                _shade_cell(cell, fill)
            if valign is not None:
                _set_valign(cell, valign)


def _usable_width(document: Document) -> int:
    section = document.sections[-1]
    page_width = int(section.page_width or 0)
    left_margin = int(section.left_margin or 0)
    right_margin = int(section.right_margin or 0)
    return page_width - left_margin - right_margin


def _render_cell(
    cell: _Cell,
    value: Any,
    style: dict[str, Any],
    *,
    bold: bool,
    align: WD_ALIGN_PARAGRAPH | None,
    color: RGBColor | None,
) -> None:
    if isinstance(value, dict) and "bullets" in value:
        items = value["bullets"]
        if not isinstance(items, list):
            raise ValueError(f"table cell bullets must be a list, got {type(items).__name__}")
        _fill_cell_bullets(cell, items, style, bold=bold, align=align, color=color)
        return
    _fill_cell(cell, str(value), style, bold=bold, align=align, color=color)


def _style_run(run: Any, style: dict[str, Any], *, bold: bool, color: RGBColor | None) -> None:
    apply_run_style(run, style)
    if bold:
        run.bold = True
    if color is not None:
        run.font.color.rgb = color


def _fill_cell(
    cell: _Cell,
    text: str,
    style: dict[str, Any],
    *,
    bold: bool,
    align: WD_ALIGN_PARAGRAPH | None = None,
    color: RGBColor | None = None,
) -> None:
    paragraph = cell.paragraphs[0]
    apply_paragraph_style(paragraph, style)
    if align is not None:
        paragraph.alignment = align
    for line_index, line in enumerate(text.split("\n")):
        if line_index > 0:
            paragraph.add_run().add_break()
        _style_run(paragraph.add_run(line), style, bold=bold, color=color)


def _fill_cell_bullets(
    cell: _Cell,
    items: list[Any],
    style: dict[str, Any],
    *,
    bold: bool,
    align: WD_ALIGN_PARAGRAPH | None,
    color: RGBColor | None,
) -> None:
    glyph = str(style.get("glyph", "• "))
    for index, item in enumerate(items):
        paragraph = cell.paragraphs[0] if index == 0 else cell.add_paragraph()
        apply_paragraph_style(paragraph, style)
        if align is not None:
            paragraph.alignment = align
        _style_run(paragraph.add_run(glyph + str(item)), style, bold=bold, color=color)


def _apply_widths(document: Document, table_element: Table, widths: list[float]) -> None:
    usable = _usable_width(document)
    table_element.autofit = False
    for column_index, percent in enumerate(widths):
        column_width = Emu(int(usable * percent / 100))
        for row in table_element.rows:
            row.cells[column_index].width = column_width
