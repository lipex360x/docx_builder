from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from docx_builder.pagination import add_page_numbers
from docx_builder.styles import StyleResolver

_FOOTER_STYLE = StyleResolver().resolve("footer")


def test_single_section_has_page_field() -> None:
    document = Document()
    add_page_numbers(document, style=_FOOTER_STYLE)
    footer_xml = document.sections[0].footer._element.xml
    assert "PAGE" in footer_xml


def test_single_section_has_num_pages_field() -> None:
    document = Document()
    add_page_numbers(document, style=_FOOTER_STYLE)
    footer_xml = document.sections[0].footer._element.xml
    assert "NUMPAGES" in footer_xml


def test_single_section_footer_right_aligned() -> None:
    document = Document()
    add_page_numbers(document, style=_FOOTER_STYLE)
    assert document.sections[0].footer.paragraphs[0].alignment == WD_ALIGN_PARAGRAPH.RIGHT


def test_single_section_footer_font_size() -> None:
    document = Document()
    add_page_numbers(document, style=_FOOTER_STYLE)
    footer = document.sections[0].footer
    assert any(run.font.size == Pt(9) for run in footer.paragraphs[0].runs)


def test_skip_cover_sections_cover_has_no_page_field() -> None:
    document = Document()
    document.add_section()
    add_page_numbers(document, style=_FOOTER_STYLE, skip_cover_sections=True)
    footer_xml = document.sections[0].footer._element.xml
    assert "PAGE" not in footer_xml


def test_skip_cover_sections_content_has_page_field() -> None:
    document = Document()
    document.add_section()
    add_page_numbers(document, style=_FOOTER_STYLE, skip_cover_sections=True)
    footer_xml = document.sections[1].footer._element.xml
    assert "PAGE" in footer_xml


def test_skip_cover_sections_content_has_num_pages_field() -> None:
    document = Document()
    document.add_section()
    add_page_numbers(document, style=_FOOTER_STYLE, skip_cover_sections=True)
    footer_xml = document.sections[1].footer._element.xml
    assert "NUMPAGES" in footer_xml


def test_skip_cover_sections_content_not_linked_to_previous() -> None:
    document = Document()
    document.add_section()
    add_page_numbers(document, style=_FOOTER_STYLE, skip_cover_sections=True)
    assert not document.sections[1].footer.is_linked_to_previous


def test_skip_cover_sections_cover_footer_is_empty() -> None:
    document = Document()
    document.add_section()
    add_page_numbers(document, style=_FOOTER_STYLE, skip_cover_sections=True)
    footer_xml = document.sections[0].footer._element.xml
    assert "NUMPAGES" not in footer_xml


def test_multiple_content_sections_all_have_footer() -> None:
    document = Document()
    document.add_section()
    document.add_section()
    add_page_numbers(document, style=_FOOTER_STYLE, skip_cover_sections=True)
    for section in document.sections[1:]:
        footer_xml = section.footer._element.xml
        assert "PAGE" in footer_xml
