from __future__ import annotations

import argparse

from docx_builder.builder import build

from . import _export, _shared

EPILOG = """\
Examples:
  docx_builder build
  docx_builder build /path/to/project
  docx_builder build --output Custom.docx
  docx_builder build --template-dir ~/templates
  docx_builder build --pdf

Builds the .docx described by content.yaml in the current directory (or the
given directory). --pdf chains an export to PDF via Microsoft Word on macOS.
Open the result in Word and press Cmd+A then F9 to refresh the table of
contents unless you used --pdf, which refreshes fields for you.
"""


def handle(arguments: argparse.Namespace) -> int:
    target = _shared.resolve_directory(arguments.directory)
    try:
        output_path = build(target, template_dir=arguments.template_dir, output_override=arguments.output)
    except FileNotFoundError:
        _shared.print_content_not_found(target)
        return 1
    print(f"Saved: {output_path}")
    if arguments.pdf:
        return _export.run_export(output_path.parent, str(output_path), None)
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
        "--pdf",
        action="store_true",
        help="after building, export the result to PDF (macOS + Microsoft Word)",
    )
    parser.set_defaults(func=handle)
