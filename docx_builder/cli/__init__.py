from __future__ import annotations

import argparse
import sys

from . import _build, _export, _init, _install

DESCRIPTION = "Generate DOCX reports from a content.yaml. Run 'docx_builder <command> -h' for details."

EPILOG = """\
Workflow:
  docx_builder init       scaffold a content.yaml in the current directory
  docx_builder build       build the .docx from content.yaml
  docx_builder export pdf  convert the built .docx to PDF (macOS + Word)

The tool resolves the project from the current directory (or a positional
directory argument) and works from anywhere once installed via uv tool.
"""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="docx_builder",
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="<command>")
    _build.register(subparsers)
    _init.register(subparsers)
    _export.register(subparsers)
    _install.register(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    return int(arguments.func(arguments))


if __name__ == "__main__":
    sys.exit(main())
