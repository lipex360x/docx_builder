from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import fitz

MINIMUM_TOC_LINKS = 3
HEADING_SEARCH_PREFIX = 28
_INSTALL_HINT = (
    "PyMuPDF is required for --fix-toc-links. Install it with "
    "uv tool install 'docx_builder[pdf-links]' or run with --with pymupdf."
)
_TRAILING_LEADER = re.compile(r"[\s.]*\d*\s*$")


def _load_fitz() -> Any:
    from docx_builder.export import ExportError

    try:
        import fitz
    except ImportError as exception:
        raise ExportError(_INSTALL_HINT) from exception
    return fitz


def _heading_name(entry_text: str) -> str:
    return _TRAILING_LEADER.sub("", entry_text).strip()


def _find_toc_pages(document: Any, fitz_module: Any) -> list[Any]:
    toc_pages: list[Any] = []
    for page in document:
        goto_links = [link for link in page.get_links() if link.get("kind") == fitz_module.LINK_GOTO]
        if not toc_pages:
            if len(goto_links) >= MINIMUM_TOC_LINKS:
                toc_pages.append(page)
        elif goto_links:
            toc_pages.append(page)
        else:
            break
    return toc_pages


def _resolve_destination(
    document: Any,
    name: str,
    first_body_index: int,
    minimum_index: int,
) -> int | None:
    needle = name[:HEADING_SEARCH_PREFIX]
    for page_index in range(max(first_body_index, minimum_index), document.page_count):
        if document[page_index].search_for(needle):
            return page_index
    return None


def _plan_rewrites(
    document: Any,
    toc_pages: list[Any],
    first_body_index: int,
    fitz_module: Any,
) -> tuple[list[tuple[int, list[tuple[fitz.Rect, int]]]], int]:
    plans: list[tuple[int, list[tuple[fitz.Rect, int]]]] = []
    corrected = 0
    minimum_index = first_body_index
    for toc_page in toc_pages:
        page_rewrites: list[tuple[fitz.Rect, int]] = []
        for link in toc_page.get_links():
            if link.get("kind") != fitz_module.LINK_GOTO:
                continue
            rectangle = link["from"]
            name = _heading_name(toc_page.get_textbox(rectangle))
            destination_index = _resolve_destination(document, name, first_body_index, minimum_index)
            if destination_index is None:
                destination_index = link.get("page", first_body_index)
            if destination_index != link.get("page"):
                corrected += 1
            page_rewrites.append((rectangle, destination_index))
            minimum_index = destination_index
        plans.append((toc_page.number, page_rewrites))
    return plans, corrected


def _apply_rewrites(
    document: Any,
    plans: list[tuple[int, list[tuple[fitz.Rect, int]]]],
    fitz_module: Any,
) -> None:
    for page_number, page_rewrites in plans:
        page = document[page_number]
        document.xref_set_key(page.xref, "Annots", "[]")
        for rectangle, destination_index in page_rewrites:
            page.insert_link(
                {
                    "kind": fitz_module.LINK_GOTO,
                    "from": rectangle,
                    "page": destination_index,
                    "to": fitz_module.Point(0, 0),
                }
            )


def fix_toc_links(pdf_path: Path) -> int:
    fitz_module = _load_fitz()
    with tempfile.TemporaryDirectory() as scratch:
        repaired_path = Path(scratch) / "repaired.pdf"
        source = fitz_module.open(str(pdf_path))
        source.save(str(repaired_path), garbage=4, clean=True)
        source.close()

        document = fitz_module.open(str(repaired_path))
        toc_pages = _find_toc_pages(document, fitz_module)
        if not toc_pages:
            document.close()
            return 0

        first_body_index = toc_pages[-1].number + 1
        plans, corrected = _plan_rewrites(document, toc_pages, first_body_index, fitz_module)
        _apply_rewrites(document, plans, fitz_module)
        document.save(str(pdf_path))
        document.close()
        return corrected
