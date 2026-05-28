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
  docx_builder export pdf --no-update-source
  docx_builder export pdf --open

Converts a built .docx to PDF via Microsoft Word on macOS, refreshing the
table of contents and page fields first. By default the populated TOC is
written back over the source .docx so it ends finalized; pass
--no-update-source to leave the source byte-identical. --open opens the
resulting .pdf (macOS only). Input defaults to the filename build produces;
output defaults to <input>.pdf.
"""


def run_export(
    project_dir: Path,
    input_override: str | None,
    output_override: str | None,
    update_source: bool = True,
    open_result: bool = False,
) -> int:
    try:
        input_docx = resolve_input_path(project_dir, input_override)
        output_pdf = resolve_output_path(input_docx, output_override)
        export_pdf(input_docx, output_pdf, update_source=update_source)
    except FileNotFoundError as exception:
        _shared.print_missing_path(str(exception))
        return 1
    except ExportError as exception:
        _shared.print_export_error(str(exception))
        return 1
    if open_result:
        _shared.open_file(output_pdf)
    return 0


def handle(arguments: argparse.Namespace) -> int:
    target = _shared.resolve_directory(arguments.directory)
    return run_export(
        target,
        arguments.input,
        arguments.output,
        update_source=not arguments.no_update_source,
        open_result=arguments.open,
    )


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
    pdf_parser.add_argument(
        "--no-update-source",
        action="store_true",
        help="leave the source .docx untouched instead of writing back the populated TOC",
    )
    pdf_parser.add_argument(
        "--open",
        action="store_true",
        help="open the resulting .pdf after export (macOS only)",
    )
    pdf_parser.set_defaults(func=handle)
