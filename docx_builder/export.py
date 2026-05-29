from __future__ import annotations

import re
import shutil
import subprocess
import sys
from importlib.resources import as_file, files
from pathlib import Path

from docx import Document

from docx_builder.builder import resolve_output_path as resolve_build_output

TOC_NOTE_NEEDLE = "Note: open in Microsoft Word"
SCRATCH_DIRECTORY = Path.home() / "Library" / "Caches" / "docx_builder" / "exports"
_WORD_APPLICATION = "/Applications/Microsoft Word.app"
_PAGE_COUNT_PATTERN = re.compile(r"kMDItemNumberOfPages\s*=\s*(\d+)")


class ExportError(Exception):
    pass


def resolve_input_path(project_dir: str | Path, input_override: str | None) -> Path:
    if input_override:
        override_path = Path(input_override)
        return override_path if override_path.is_absolute() else Path(project_dir) / override_path
    return resolve_build_output(project_dir)


def resolve_output_path(input_docx: Path, output_override: str | None) -> Path:
    if output_override:
        override_path = Path(output_override)
        return override_path if override_path.is_absolute() else input_docx.parent / override_path
    return input_docx.with_suffix(".pdf")


def strip_toc_note(docx_path: Path) -> None:
    document = Document(str(docx_path))
    for paragraph in list(document.paragraphs):
        if TOC_NOTE_NEEDLE in paragraph.text:
            parent = paragraph._element.getparent()
            if parent is not None:
                parent.remove(paragraph._element)
    document.save(str(docx_path))


def _word_is_installed() -> bool:
    return Path(_WORD_APPLICATION).exists()


def _run_jxa(input_docx: Path, output_pdf: Path | None) -> None:
    script_resource = files("docx_builder.scripts").joinpath("docx_to_pdf.jxa")
    arguments = ["osascript", "-l", "JavaScript"]
    with as_file(script_resource) as script_path:
        arguments.append(str(script_path))
        arguments.append(str(input_docx))
        if output_pdf is not None:
            arguments.append(str(output_pdf))
        subprocess.run(arguments, check=True)


def _require_word_environment() -> None:
    if sys.platform != "darwin":
        raise ExportError("PDF export requires macOS + Microsoft Word")
    if not _word_is_installed():
        raise ExportError(f"Microsoft Word not found at {_WORD_APPLICATION}")


def _parse_page_count(mdls_output: str) -> int | None:
    match = _PAGE_COUNT_PATTERN.search(mdls_output)
    return int(match.group(1)) if match else None


def _read_page_count(pdf_path: Path) -> int | None:
    subprocess.run(["mdimport", str(pdf_path)], check=True)
    result = subprocess.run(
        ["mdls", "-name", "kMDItemNumberOfPages", str(pdf_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return _parse_page_count(result.stdout)


def export_pdf(input_docx: Path, output_pdf: Path, update_source: bool = True) -> Path:
    _require_word_environment()
    if not input_docx.exists():
        raise ExportError(f"input .docx not found: {input_docx}")

    SCRATCH_DIRECTORY.mkdir(parents=True, exist_ok=True)
    scratch_docx = SCRATCH_DIRECTORY / input_docx.name
    scratch_pdf = SCRATCH_DIRECTORY / output_pdf.name

    shutil.copyfile(input_docx, scratch_docx)
    strip_toc_note(scratch_docx)
    _run_jxa(scratch_docx, scratch_pdf)

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(scratch_pdf), str(output_pdf))
    if update_source:
        shutil.move(str(scratch_docx), str(input_docx))
    else:
        scratch_docx.unlink(missing_ok=True)

    page_count = _read_page_count(output_pdf)
    label = "page" if page_count == 1 else "pages"
    count_display = page_count if page_count is not None else "?"
    print(f"Exported: {output_pdf} ({count_display} {label})")
    return output_pdf


def finalize_source(input_docx: Path) -> Path:
    _require_word_environment()
    if not input_docx.exists():
        raise ExportError(f"input .docx not found: {input_docx}")

    SCRATCH_DIRECTORY.mkdir(parents=True, exist_ok=True)
    scratch_docx = SCRATCH_DIRECTORY / input_docx.name

    shutil.copyfile(input_docx, scratch_docx)
    strip_toc_note(scratch_docx)
    _run_jxa(scratch_docx, None)

    shutil.move(str(scratch_docx), str(input_docx))
    return input_docx
