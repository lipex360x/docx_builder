from __future__ import annotations

import argparse

from docx_builder.builder import init_project

from . import _shared

EPILOG = """\
Examples:
  docx_builder init
  docx_builder init /path/to/project
  docx_builder init --force

Writes a marker content.yaml in the target directory pointing back at the
docx_builder skill. It does not scaffold a placeholder document — author the
real content.yaml yourself. Use --force to overwrite an existing file.
"""


def handle(arguments: argparse.Namespace) -> int:
    target = _shared.resolve_directory(arguments.directory)
    try:
        content_path = init_project(target, force=arguments.force)
    except FileExistsError:
        _shared.print_content_exists(target)
        return 1
    print(f"Initialized: {content_path}")
    return 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "init",
        help="scaffold content.yaml in a directory",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=None,
        help="project directory (defaults to current working directory)",
    )
    parser.add_argument("--force", action="store_true", help="overwrite existing content.yaml")
    parser.set_defaults(func=handle)
