from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import fitz

RECT_COORDINATES = 4
HEADING_SEARCH_PREFIX = 28
_INSTALL_HINT = "PyMuPDF is required for PDF link repair. Reinstall docx_builder with its dependencies."
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
            if "TABLE OF CONTENTS" in page.get_text().upper() and page.annot_xrefs():
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
) -> tuple[int, float] | None:
    needle = name[:HEADING_SEARCH_PREFIX]
    if not needle:
        return None
    for page_index in range(max(first_body_index, minimum_index), document.page_count):
        matches = document[page_index].search_for(needle)
        if matches:
            return page_index, max(0.0, matches[0].y0 - 10.0)
    return None


def _plan_rewrites(
    document: Any,
    toc_pages: list[Any],
    first_body_index: int,
    fitz_module: Any,
) -> tuple[list[tuple[int, list[tuple[fitz.Rect, int, float]]]], int]:
    plans: list[tuple[int, list[tuple[fitz.Rect, int, float]]]] = []
    corrected = 0
    minimum_index = first_body_index
    for toc_page in toc_pages:
        page_rewrites: list[tuple[fitz.Rect, int, float]] = []
        for link in toc_page.get_links():
            if link.get("kind") != fitz_module.LINK_GOTO:
                continue
            rectangle = link["from"]
            name = _heading_name(toc_page.get_textbox(rectangle))
            destination = _resolve_destination(document, name, first_body_index, minimum_index)
            if destination is None:
                continue
            destination_index, top = destination
            point = link.get("to")
            if destination_index != link.get("page") or point is None or abs(point.y - top) > 1:
                corrected += 1
                page_rewrites.append((rectangle, destination_index, top))
            minimum_index = destination_index
        plans.append((toc_page.number, page_rewrites))
    return plans, corrected


def _apply_rewrites(
    document: Any,
    plans: list[tuple[int, list[tuple[fitz.Rect, int, float]]]],
    fitz_module: Any,
) -> None:
    for page_number, page_rewrites in plans:
        page = document[page_number]
        links = page.get_links()
        for rectangle, destination_index, top in page_rewrites:
            link = next(
                (item for item in links if item.get("kind") == fitz_module.LINK_GOTO and item.get("from") == rectangle),
                None,
            )
            if link is not None:
                if not link.get("xref"):
                    for xref, annotation_type, _ in page.annot_xrefs():
                        if annotation_type != 1:
                            continue
                        kind, raw = document.xref_get_key(xref, "Rect")
                        values = re.findall(r"-?\d+(?:\.\d+)?", raw)
                        if kind == "array" and len(values) == RECT_COORDINATES:
                            annotation_rect = fitz_module.Rect(*(float(value) for value in values))
                            if annotation_rect * page.transformation_matrix == rectangle:
                                link["xref"] = xref
                                break
                if not link.get("xref"):
                    from docx_builder.export import ExportError

                    raise ExportError("Could not locate a ToC link annotation for safe repair")
                link["page"] = destination_index
                link["to"] = fitz_module.Point(0, top)
                page.update_link(link)


def _repair_unresolved(document: Any, toc_pages: list[Any], first_body_index: int, fitz_module: Any) -> int:
    corrected = 0
    for page in toc_pages:
        for xref, annotation_type, _ in page.annot_xrefs():
            if annotation_type != 1 or document.xref_get_key(xref, "Dest")[0] != "null":
                continue
            if document.xref_get_key(xref, "A")[0] != "null":
                continue
            kind, raw = document.xref_get_key(xref, "Rect")
            values = re.findall(r"-?\d+(?:\.\d+)?", raw)
            if kind != "array" or len(values) != RECT_COORDINATES:
                continue
            rectangle = fitz_module.Rect(*(float(value) for value in values)) * page.transformation_matrix
            name = _heading_name(page.get_textbox(rectangle))
            if not name:
                continue
            destination = _resolve_destination(document, name, first_body_index, first_body_index)
            if destination is None:
                continue
            page.update_link(
                {
                    "kind": fitz_module.LINK_GOTO,
                    "xref": xref,
                    "from": rectangle,
                    "page": destination[0],
                    "to": fitz_module.Point(0, destination[1]),
                }
            )
            corrected += 1
    return corrected


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
        corrected += _repair_unresolved(document, toc_pages, first_body_index, fitz_module)
        document.save(str(pdf_path))
        document.close()
        return corrected
