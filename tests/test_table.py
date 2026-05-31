import pytest
from docx import Document
from docx.oxml.ns import qn

from docx_builder.styles import StyleResolver
from docx_builder.table import remove_table_borders, set_table_borders, table

_RESOLVER = StyleResolver()


def _cell_fill(cell: object) -> str | None:
    table_cell_properties = cell._tc.find(qn("w:tcPr"))  # type: ignore[attr-defined]
    if table_cell_properties is None:
        return None
    shading = table_cell_properties.find(qn("w:shd"))
    return None if shading is None else shading.get(qn("w:fill"))


def test_remove_table_borders_adds_borders_element() -> None:
    document = Document()
    table_element = document.add_table(rows=1, cols=2)
    remove_table_borders(table_element)
    tbl_xml = table_element._tbl
    table_properties = tbl_xml.find(qn("w:tblPr"))
    assert table_properties is not None
    table_borders = table_properties.find(qn("w:tblBorders"))
    assert table_borders is not None


def test_remove_table_borders_all_sides_none() -> None:
    document = Document()
    table_element = document.add_table(rows=1, cols=2)
    remove_table_borders(table_element)
    tbl_xml = table_element._tbl
    table_properties = tbl_xml.find(qn("w:tblPr"))
    assert table_properties is not None
    table_borders = table_properties.find(qn("w:tblBorders"))
    assert table_borders is not None
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        border_element = table_borders.find(qn(f"w:{side}"))
        assert border_element is not None
        assert border_element.get(qn("w:val")) == "none"


def test_set_table_borders_all_sides_single() -> None:
    document = Document()
    table_element = document.add_table(rows=1, cols=2)
    set_table_borders(table_element)
    table_borders = table_element._tbl.find(qn("w:tblPr")).find(qn("w:tblBorders"))
    assert table_borders is not None
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        border_element = table_borders.find(qn(f"w:{side}"))
        assert border_element is not None
        assert border_element.get(qn("w:val")) == "single"


def test_table_defaults_match_resolver() -> None:
    assert _RESOLVER.resolve("table") == {"font_size": "10pt", "header_bold": True, "align": "left"}


def test_table_dimensions_with_header() -> None:
    document = Document()
    result = table(
        document,
        [["a1", "b1"], ["a2", "b2"]],
        _RESOLVER.resolve("table"),
        header=["A", "B"],
    )
    assert len(result.rows) == 3
    assert len(result.columns) == 2
    assert result.cell(0, 0).text == "A"
    assert result.cell(1, 0).text == "a1"
    assert result.cell(2, 1).text == "b2"


def test_table_without_header_infers_columns_from_rows() -> None:
    document = Document()
    result = table(document, [["x", "y", "z"]], _RESOLVER.resolve("table"))
    assert len(result.rows) == 1
    assert len(result.columns) == 3


def test_table_header_row_is_bold() -> None:
    document = Document()
    result = table(document, [["a", "b"]], _RESOLVER.resolve("table"), header=["A", "B"])
    header_run = result.cell(0, 0).paragraphs[0].runs[0]
    body_run = result.cell(1, 0).paragraphs[0].runs[0]
    assert header_run.bold is True
    assert not body_run.bold


def test_table_header_bold_can_be_disabled_via_style() -> None:
    document = Document()
    style = {**_RESOLVER.resolve("table"), "header_bold": False}
    result = table(document, [["a", "b"]], style, header=["A", "B"])
    assert not result.cell(0, 0).paragraphs[0].runs[0].bold


def test_table_body_cell_font_size() -> None:
    from docx.shared import Pt

    document = Document()
    result = table(document, [["a", "b"]], _RESOLVER.resolve("table"))
    assert result.cell(0, 0).paragraphs[0].runs[0].font.size == Pt(10)


def test_table_borders_true_draws_single() -> None:
    document = Document()
    result = table(document, [["a", "b"]], _RESOLVER.resolve("table"), borders=True)
    table_borders = result._tbl.find(qn("w:tblPr")).find(qn("w:tblBorders"))
    assert table_borders.find(qn("w:top")).get(qn("w:val")) == "single"


def test_table_borders_false_removes() -> None:
    document = Document()
    result = table(document, [["a", "b"]], _RESOLVER.resolve("table"), borders=False)
    table_borders = result._tbl.find(qn("w:tblPr")).find(qn("w:tblBorders"))
    assert table_borders.find(qn("w:top")).get(qn("w:val")) == "none"


def test_table_widths_set_per_column() -> None:
    document = Document()
    result = table(
        document,
        [["a", "b", "c"]],
        _RESOLVER.resolve("table"),
        widths=[25, 50, 25],
    )
    first = result.cell(0, 0).width
    second = result.cell(0, 1).width
    assert first is not None
    assert second is not None
    assert second > first


def test_table_multiline_cell_breaks() -> None:
    document = Document()
    result = table(document, [["line one\nline two", "x"]], _RESOLVER.resolve("table"))
    cell_xml = result.cell(0, 0).paragraphs[0]._p.xml
    assert "<w:br/>" in cell_xml
    assert "line one" in result.cell(0, 0).text
    assert "line two" in result.cell(0, 0).text


def test_table_coerces_non_string_cells() -> None:
    document = Document()
    result = table(document, [[1, 2.5]], _RESOLVER.resolve("table"))
    assert result.cell(0, 0).text == "1"
    assert result.cell(0, 1).text == "2.5"


def test_table_ragged_row_raises() -> None:
    document = Document()
    with pytest.raises(ValueError, match="row 1"):
        table(document, [["a", "b"], ["c"]], _RESOLVER.resolve("table"))


def test_table_empty_raises() -> None:
    document = Document()
    with pytest.raises(ValueError, match="header or at least one row"):
        table(document, [], _RESOLVER.resolve("table"))


def test_table_zero_columns_raises() -> None:
    document = Document()
    with pytest.raises(ValueError, match="at least one column"):
        table(document, [], _RESOLVER.resolve("table"), header=[])


def test_table_no_fill_keys_no_shading() -> None:
    document = Document()
    result = table(document, [["a", "b"]], _RESOLVER.resolve("table"), header=["A", "B"])
    for row_index in range(2):
        for column_index in range(2):
            assert _cell_fill(result.cell(row_index, column_index)) is None


def test_table_header_fill_shades_header_only() -> None:
    document = Document()
    style = {**_RESOLVER.resolve("table"), "header_fill": "#003366"}
    result = table(document, [["a", "b"]], style, header=["A", "B"])
    assert _cell_fill(result.cell(0, 0)) == "003366"
    assert _cell_fill(result.cell(0, 1)) == "003366"
    assert _cell_fill(result.cell(1, 0)) is None


def test_table_fill_accepts_bare_hex() -> None:
    document = Document()
    style = {**_RESOLVER.resolve("table"), "header_fill": "AABBCC"}
    result = table(document, [["a"]], style, header=["A"])
    assert _cell_fill(result.cell(0, 0)) == "AABBCC"


def test_table_stripe_fill_zebra() -> None:
    document = Document()
    style = {**_RESOLVER.resolve("table"), "stripe_fill": "#EEEEEE"}
    result = table(document, [["r0"], ["r1"], ["r2"]], style, header=["H"])
    assert _cell_fill(result.cell(0, 0)) is None
    assert _cell_fill(result.cell(1, 0)) is None
    assert _cell_fill(result.cell(2, 0)) == "EEEEEE"
    assert _cell_fill(result.cell(3, 0)) is None


def test_table_stripe_fill_zebra_without_header() -> None:
    document = Document()
    style = {**_RESOLVER.resolve("table"), "stripe_fill": "#DDDDDD"}
    result = table(document, [["d0"], ["d1"], ["d2"], ["d3"]], style)
    assert _cell_fill(result.cell(0, 0)) is None
    assert _cell_fill(result.cell(1, 0)) == "DDDDDD"
    assert _cell_fill(result.cell(2, 0)) is None
    assert _cell_fill(result.cell(3, 0)) == "DDDDDD"


def test_table_header_and_stripe_fill_combined() -> None:
    document = Document()
    style = {**_RESOLVER.resolve("table"), "header_fill": "#112233", "stripe_fill": "#445566"}
    result = table(document, [["d0"], ["d1"]], style, header=["H"])
    assert _cell_fill(result.cell(0, 0)) == "112233"
    assert _cell_fill(result.cell(1, 0)) is None
    assert _cell_fill(result.cell(2, 0)) == "445566"


def test_table_widths_wrong_length_raises() -> None:
    document = Document()
    with pytest.raises(ValueError, match="widths"):
        table(document, [["a", "b"]], _RESOLVER.resolve("table"), widths=[100])


def test_table_widths_bad_sum_raises() -> None:
    document = Document()
    with pytest.raises(ValueError, match="sum to 100"):
        table(document, [["a", "b"]], _RESOLVER.resolve("table"), widths=[10, 20])


def test_table_header_only_no_rows() -> None:
    document = Document()
    result = table(document, [], _RESOLVER.resolve("table"), header=["A", "B"])
    assert len(result.rows) == 1
    assert result.cell(0, 1).text == "B"
