from __future__ import annotations

from typing import Any

from docx.document import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Emu
from docx.table import Table, _Cell

from docx_builder.styles import apply_paragraph_style, apply_run_style, parse_color

_WIDTH_TOLERANCE = 0.5


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


def _validate_shape(rows: list[list[Any]], header: list[Any] | None, widths: list[float] | None) -> int:
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
    return column_count


def table(
    document: Document,
    rows: list[list[Any]],
    style: dict[str, Any],
    *,
    header: list[Any] | None = None,
    widths: list[float] | None = None,
    borders: bool = True,
) -> Table:
    column_count = _validate_shape(rows, header, widths)

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

    _populate(table_element, body_rows, style, column_count)

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


def _populate(
    table_element: Table, body_rows: list[tuple[list[Any], bool]], style: dict[str, Any], column_count: int
) -> None:
    header_bold = bool(style.get("header_bold", True))
    fills = _row_fills(body_rows, _fill_hex(style.get("header_fill")), _fill_hex(style.get("stripe_fill")))
    for row_index, ((values, is_header), fill) in enumerate(zip(body_rows, fills, strict=True)):
        for column_index in range(column_count):
            cell = table_element.cell(row_index, column_index)
            text = str(values[column_index]) if column_index < len(values) else ""
            _fill_cell(cell, text, style, bold=is_header and header_bold)
            if fill is not None:
                _shade_cell(cell, fill)


def _usable_width(document: Document) -> int:
    section = document.sections[-1]
    page_width = int(section.page_width or 0)
    left_margin = int(section.left_margin or 0)
    right_margin = int(section.right_margin or 0)
    return page_width - left_margin - right_margin


def _fill_cell(cell: _Cell, text: str, style: dict[str, Any], *, bold: bool) -> None:
    paragraph = cell.paragraphs[0]
    apply_paragraph_style(paragraph, style)
    for line_index, line in enumerate(text.split("\n")):
        if line_index > 0:
            paragraph.add_run().add_break()
        run = paragraph.add_run(line)
        apply_run_style(run, style)
        if bold:
            run.bold = True


def _apply_widths(document: Document, table_element: Table, widths: list[float]) -> None:
    usable = _usable_width(document)
    table_element.autofit = False
    for column_index, percent in enumerate(widths):
        column_width = Emu(int(usable * percent / 100))
        for row in table_element.rows:
            row.cells[column_index].width = column_width
