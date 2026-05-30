from __future__ import annotations

import builtins
from pathlib import Path

import fitz
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
    vertical = 100
    for index, heading in enumerate(HEADINGS):
        rectangle = fitz.Rect(72, vertical, 300, vertical + 20)
        document[0].insert_text(fitz.Point(72, vertical + 15), f"{heading} ....... {index + 1}", fontsize=12)
        document[0].insert_link(
            {"kind": fitz.LINK_GOTO, "from": rectangle, "page": destination_pages[index], "to": fitz.Point(0, 0)}
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


def test_fix_corrects_shifted_destinations(tmp_path: Path) -> None:
    pdf_path = _build_synthetic_pdf(tmp_path / "report.pdf", destination_pages=[3, 1, 2])

    rewritten = toc_links.fix_toc_links(pdf_path)

    assert rewritten == 3
    assert _destination_pages(pdf_path) == [1, 2, 3]


def test_fix_is_noop_when_destinations_already_correct(tmp_path: Path) -> None:
    pdf_path = _build_synthetic_pdf(tmp_path / "report.pdf", destination_pages=[1, 2, 3])

    rewritten = toc_links.fix_toc_links(pdf_path)

    assert rewritten == 3
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
        if name == "fitz":
            raise ImportError("No module named 'fitz'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ExportError, match="pdf-links"):
        toc_links.fix_toc_links(pdf_path)
