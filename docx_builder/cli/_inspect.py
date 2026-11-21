from __future__ import annotations

import argparse
import sys
from pathlib import Path

from docx_builder.word_inspect import InspectionError, inspect_word


def handle(arguments: argparse.Namespace) -> int:
    try:
        print(inspect_word(Path(arguments.path)))
    except InspectionError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "inspect-word", help="inspect saved state and comments without changing a Word document (macOS)"
    )
    parser.add_argument("path", help="path of the DOCX document to inspect")
    parser.set_defaults(func=handle)
