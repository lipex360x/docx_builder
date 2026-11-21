from __future__ import annotations

import builtins
from pathlib import Path

import pymupdf as fitz
import pytest

from docx_builder import toc_links
from docx_builder.export import ExportError

HEADINGS = ["Introduction", "Methodology", "Results"]


def _build_synthetic_pdf(destination: Path, destination_pages: list[int]) -> Path:
    document = fitz.open()
    for _ in range(len(HEADINGS) + 1):
        document.new_page()
    for index, heading in enumerate(HEADINGS):
        document[index + 1].insert_text(fitz.Point(72, 200), heading, fontsize=24)
    document[0].insert_text(fitz.Point(72, 50), "TABLE OF CONTENTS", fontsize=16)
    vertical = 100
    for index, heading in enumerate(HEADINGS):
        rectangle = fitz.Rect(72, vertical, 300, vertical + 20)
        document[0].insert_text(fitz.Point(72, vertical + 15), f"{heading} ....... {index + 1}", fontsize=12)
        document[0].insert_link(
            {
                "kind": fitz.LINK_GOTO,
                "from": rectangle,
                "page": destination_pages[index],
                "to": fitz.Point(0, max(0, document[index + 1].search_for(heading)[0].y0 - 10)),
            }
        )
        vertical += 30
    document.save(str(destination))
    document.close()
    return destination


def _destination_pages(pdf_path: Path) -> list[int | None]:
    document = fitz.open(str(pdf_path))
    pages = [link.get("page") for link in document[0].get_links() if link.get("kind") == fitz.LINK_GOTO]
    document.close()
    return pages


def _build_multipage_toc_pdf(destination: Path, destination_pages: list[int]) -> Path:
    headings = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"]
    toc_page_count = 2
    document = fitz.open()
    for _ in range(toc_page_count + len(headings)):
        document.new_page()
    for index, heading in enumerate(headings):
        document[toc_page_count + index].insert_text(fitz.Point(72, 200), heading, fontsize=24)
    document[0].insert_text(fitz.Point(72, 50), "TABLE OF CONTENTS", fontsize=16)
    half = len(headings) // 2
    for index, heading in enumerate(headings):
        toc_page_index = 0 if index < half else 1
        row = index if index < half else index - half
        vertical = 100 + row * 30
        rectangle = fitz.Rect(72, vertical, 300, vertical + 20)
        toc_page = document[toc_page_index]
        toc_page.insert_text(fitz.Point(72, vertical + 15), f"{heading} ....... {index + 1}", fontsize=12)
        toc_page.insert_link(
            {
                "kind": fitz.LINK_GOTO,
                "from": rectangle,
                "page": destination_pages[index],
                "to": fitz.Point(0, max(0, document[toc_page_count + index].search_for(heading)[0].y0 - 10)),
            }
        )
    document.save(str(destination))
    document.close()
    return destination


def _all_destination_pages(pdf_path: Path) -> list[int | None]:
    document = fitz.open(str(pdf_path))
    pages = [link.get("page") for page in document for link in page.get_links() if link.get("kind") == fitz.LINK_GOTO]
    document.close()
    return pages


def test_fix_corrects_shifted_destinations(tmp_path: Path) -> None:
    pdf_path = _build_synthetic_pdf(tmp_path / "report.pdf", destination_pages=[3, 1, 2])

    rewritten = toc_links.fix_toc_links(pdf_path)

    assert rewritten == 3
    assert _destination_pages(pdf_path) == [1, 2, 3]


def test_fix_corrects_destinations_across_multipage_toc(tmp_path: Path) -> None:
    pdf_path = _build_multipage_toc_pdf(tmp_path / "report.pdf", destination_pages=[7, 6, 5, 4, 3, 2])

    rewritten = toc_links.fix_toc_links(pdf_path)

    assert rewritten == 6
    assert _all_destination_pages(pdf_path) == [2, 3, 4, 5, 6, 7]


def test_fix_is_noop_when_destinations_already_correct(tmp_path: Path) -> None:
    pdf_path = _build_synthetic_pdf(tmp_path / "report.pdf", destination_pages=[1, 2, 3])

    rewritten = toc_links.fix_toc_links(pdf_path)

    assert rewritten == 0
    assert _destination_pages(pdf_path) == [1, 2, 3]


def test_fix_returns_zero_when_no_toc_page(tmp_path: Path) -> None:
    pdf_path = tmp_path / "plain.pdf"
    document = fitz.open()
    document.new_page()
    document.new_page()
    document.save(str(pdf_path))
    document.close()

    rewritten = toc_links.fix_toc_links(pdf_path)

    assert rewritten == 0


def test_fix_raises_export_error_when_fitz_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pdf_path = _build_synthetic_pdf(tmp_path / "report.pdf", destination_pages=[3, 1, 2])
    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "pymupdf":
            raise ImportError("No module named 'pymupdf'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ExportError, match="PyMuPDF"):
        toc_links.fix_toc_links(pdf_path)


def test_preserves_external_links_on_toc_page(tmp_path: Path) -> None:
    pdf_path = _build_synthetic_pdf(tmp_path / "report.pdf", destination_pages=[3, 1, 2])
    document = fitz.open(str(pdf_path))
    document[0].insert_link({"kind": fitz.LINK_URI, "from": fitz.Rect(72, 300, 300, 320), "uri": "https://example.com"})
    document.saveIncr()
    document.close()

    toc_links.fix_toc_links(pdf_path)

    document = fitz.open(str(pdf_path))
    assert any(link.get("uri") == "https://example.com" for link in document[0].get_links())
    document.close()


def test_repairs_toc_link_with_null_destination(tmp_path: Path) -> None:
    pdf_path = _build_synthetic_pdf(tmp_path / "report.pdf", destination_pages=[1, 2, 3])
    document = fitz.open(str(pdf_path))
    xref = document[0].get_links()[-1]["xref"]
    document.xref_set_key(xref, "A", "null")
    document.xref_set_key(xref, "Dest", "null")
    document.saveIncr()
    document.close()

    toc_links.fix_toc_links(pdf_path)

    assert _destination_pages(pdf_path) == [1, 2, 3]


def test_does_not_rewrite_links_on_page_without_toc_title(tmp_path: Path) -> None:
    pdf_path = _build_synthetic_pdf(tmp_path / "report.pdf", destination_pages=[3, 1, 2])
    document = fitz.open(str(pdf_path))
    document[0].add_redact_annot(fitz.Rect(70, 30, 260, 55), fill=(1, 1, 1))
    document[0].apply_redactions()
    document.saveIncr()
    document.close()

    assert toc_links.fix_toc_links(pdf_path) == 0
    assert _destination_pages(pdf_path) == [3, 1, 2]


def test_repairs_toc_when_every_link_has_null_destination(tmp_path: Path) -> None:
    pdf_path = _build_synthetic_pdf(tmp_path / "report.pdf", destination_pages=[1, 2, 3])
    document = fitz.open(str(pdf_path))
    for link in document[0].get_links():
        document.xref_set_key(link["xref"], "A", "null")
        document.xref_set_key(link["xref"], "Dest", "null")
    document.saveIncr()
    document.close()

    assert toc_links.fix_toc_links(pdf_path) == 3
    assert _destination_pages(pdf_path) == [1, 2, 3]


def test_repairs_wrong_heading_on_correct_page(tmp_path: Path) -> None:
    pdf_path = _build_synthetic_pdf(tmp_path / "report.pdf", destination_pages=[1, 2, 3])
    document = fitz.open(str(pdf_path))
    link = document[0].get_links()[0]
    link["to"] = fitz.Point(0, 0)
    document[0].update_link(link)
    document.saveIncr()
    document.close()

    assert toc_links.fix_toc_links(pdf_path) == 1
    document = fitz.open(str(pdf_path))
    assert document[0].get_links()[0]["to"].y > 100
    document.close()
