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


def _find_toc_page(document: Any, fitz_module: Any) -> Any | None:
    for page in document:
        goto_links = [link for link in page.get_links() if link.get("kind") == fitz_module.LINK_GOTO]
        if len(goto_links) >= MINIMUM_TOC_LINKS:
            return page
    return None


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


def _rewritten_destinations(document: Any, toc_page: Any, fitz_module: Any) -> list[tuple[fitz.Rect, int]]:
    goto_links = [link for link in toc_page.get_links() if link.get("kind") == fitz_module.LINK_GOTO]
    first_body_index = toc_page.number + 1
    rewrites: list[tuple[fitz.Rect, int]] = []
    minimum_index = first_body_index
    for link in goto_links:
        rectangle = link["from"]
        name = _heading_name(toc_page.get_textbox(rectangle))
        destination_index = _resolve_destination(document, name, first_body_index, minimum_index)
        if destination_index is None:
            destination_index = link.get("page", first_body_index)
        rewrites.append((rectangle, destination_index))
        minimum_index = destination_index
    return rewrites


def _apply_rewrites(
    document: Any,
    toc_page: Any,
    rewrites: list[tuple[fitz.Rect, int]],
    fitz_module: Any,
) -> None:
    document.xref_set_key(toc_page.xref, "Annots", "[]")
    for rectangle, destination_index in rewrites:
        toc_page.insert_link(
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
        toc_page = _find_toc_page(document, fitz_module)
        if toc_page is None:
            document.close()
            return 0

        rewrites = _rewritten_destinations(document, toc_page, fitz_module)
        _apply_rewrites(document, toc_page, rewrites, fitz_module)
        document.save(str(pdf_path))
        document.close()
        return len(rewrites)
