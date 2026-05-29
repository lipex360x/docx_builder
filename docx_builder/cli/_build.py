from __future__ import annotations

import argparse

from docx_builder.builder import build, has_toc
from docx_builder.export import ExportError, finalize_source
from docx_builder.report import format_report, report_for

from . import _export, _shared

EPILOG = """\
Examples:
  docx_builder build
  docx_builder build /path/to/project
  docx_builder build --output Custom.docx
  docx_builder build --template-dir ~/templates
  docx_builder build --no-finalize
  docx_builder build --pdf
  docx_builder build --open
  docx_builder build --pdf --open
  docx_builder build --pdf --no-update-source

Builds the .docx described by content.yaml in the current directory (or the
given directory). If the document contains a TOC, build finalizes it by
default: on macOS with Microsoft Word it drives Word to update the table of
contents and all fields, then writes the populated .docx back over the source
(no manual F9). Off macOS or without Word it prints a note and leaves the TOC
field empty. Pass --no-finalize to skip the Word pass entirely (fast/pure,
useful for CI). --pdf chains an export to PDF via Microsoft Word, which
already finalizes the source (pass --no-update-source to skip the write-back).
--open opens the result: with --pdf, both the .pdf and the finalized .docx
(in Microsoft Word); otherwise just the .docx (macOS only).
"""


def handle(arguments: argparse.Namespace) -> int:
    target = _shared.resolve_directory(arguments.directory)
    try:
        output_path = build(target, template_dir=arguments.template_dir, output_override=arguments.output)
    except FileNotFoundError:
        _shared.print_content_not_found(target)
        return 1
    print(f"Saved: {output_path}")
    print(format_report(report_for(output_path)))
    if arguments.pdf:
        return _export.run_export(
            output_path.parent,
            str(output_path),
            None,
            update_source=not arguments.no_update_source,
            open_result=arguments.open,
        )
    if not arguments.no_finalize and has_toc(target):
        try:
            finalize_source(output_path)
        except ExportError:
            _shared.print_finalize_skipped()
    if arguments.open:
        _shared.open_file(output_path)
    return 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "build",
        help="build the DOCX from content.yaml",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=None,
        help="project directory (defaults to current working directory)",
    )
    parser.add_argument("--output", help="override output filename")
    parser.add_argument("--template-dir", help="override template directory")
    parser.add_argument(
        "--no-finalize",
        action="store_true",
        help="skip the Word finalize pass that populates the TOC (keeps build pure/fast)",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="after building, export the result to PDF (macOS + Microsoft Word)",
    )
    parser.add_argument(
        "--no-update-source",
        action="store_true",
        help="with --pdf, leave the source .docx untouched instead of writing back the populated TOC",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="open the result: with --pdf, both the .pdf and the .docx in Word; otherwise the .docx (macOS only)",
    )
    parser.set_defaults(func=handle)
