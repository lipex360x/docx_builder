from __future__ import annotations

import argparse
from pathlib import Path

from docx_builder.export import ExportError, export_pdf, resolve_input_path, resolve_output_path

from . import _shared

EPILOG = """\
Examples:
  docx_builder export pdf
  docx_builder export pdf /path/to/project
  docx_builder export pdf --input Report.docx
  docx_builder export pdf --output Final.pdf

Converts a built .docx to PDF via Microsoft Word on macOS, refreshing the
table of contents and page fields first. The source .docx is left untouched.
Input defaults to the filename build produces; output defaults to <input>.pdf.
"""


def run_export(project_dir: Path, input_override: str | None, output_override: str | None) -> int:
    try:
        input_docx = resolve_input_path(project_dir, input_override)
        output_pdf = resolve_output_path(input_docx, output_override)
        export_pdf(input_docx, output_pdf)
    except FileNotFoundError as exception:
        _shared.print_missing_path(str(exception))
        return 1
    except ExportError as exception:
        _shared.print_export_error(str(exception))
        return 1
    return 0


def handle(arguments: argparse.Namespace) -> int:
    target = _shared.resolve_directory(arguments.directory)
    return run_export(target, arguments.input, arguments.output)


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "export",
        help="export a built document to another format",
    )
    export_subparsers = parser.add_subparsers(dest="export_format", required=True, metavar="<format>")
    pdf_parser = export_subparsers.add_parser(
        "pdf",
        help="export a .docx to PDF via Microsoft Word (macOS only)",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    pdf_parser.add_argument(
        "directory",
        nargs="?",
        default=None,
        help="project directory (defaults to current working directory)",
    )
    pdf_parser.add_argument("--input", help="explicit source .docx (defaults to build's resolution)")
    pdf_parser.add_argument("--output", help="explicit destination .pdf (defaults to <input>.pdf)")
    pdf_parser.set_defaults(func=handle)
