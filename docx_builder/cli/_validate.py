from __future__ import annotations

import argparse
from pathlib import Path

from docx_builder.validate import format_violations, validate_project

from . import _shared

EPILOG = """\
Examples:
  docx_builder validate
  docx_builder validate /path/to/project
  docx_builder validate --strict
  docx_builder validate --also brief.md notes.md

Scans the prose fields of content.yaml (h1/h2/h3, body, bullet, caption,
bold_lead, reference) for forbidden characters: em-dash (U+2014), horizontal
bar (U+2015) and figure dash (U+2012) always, plus en-dash (U+2013) under
--strict. Keys, paths and filenames are ignored. Exits 1 if any are found
(0 when clean), so it can gate a pre-commit hook or CI step.
"""


def handle(arguments: argparse.Namespace) -> int:
    target = _shared.resolve_directory(arguments.directory)
    also = [Path(item) for item in arguments.also or []]
    try:
        violations = validate_project(target, strict=arguments.strict, also=also)
    except FileNotFoundError:
        _shared.print_content_not_found(target)
        return 1
    if not violations:
        print("validate: clean. No forbidden characters in prose.")
        return 0
    print(format_violations(violations))
    return 1


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "validate",
        help="check content.yaml prose for em/en dash and other AI-tells",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=None,
        help="project directory (defaults to current working directory)",
    )
    parser.add_argument("--strict", action="store_true", help="also flag en-dash (U+2013)")
    parser.add_argument("--also", nargs="*", help="extra plain-text/markdown files to scan with the same rules")
    parser.set_defaults(func=handle)
