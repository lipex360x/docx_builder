from __future__ import annotations

import argparse
import shutil
import sys

from docx_builder.builder import init_project
from docx_builder.scaffold import ALL_LAYERS, format_summary, resolve_layers

from . import _shared

EPILOG = """\
Examples:
  docx_builder init
  docx_builder init /path/to/project
  docx_builder init --with references,src
  docx_builder init --with ai-check
  docx_builder init --full --name "Annual Report"
  docx_builder init --cover

Scaffolds a role-based project: by default the base (report/ with content.yaml,
images/, assets/, output/, templates/, plus CLAUDE.md, .gitignore and .work/).
--with adds named optional layers (deps auto-resolved); --full adds them all
plus the embedded monitor scripts. --name is injected into CLAUDE.md and
content.yaml (defaults to the directory name); --cover writes a cover + TOC
content.yaml (Shape B). The scaffolder is idempotent: it only adds what is
missing and never overwrites existing files without --force.

Layers (for --with; --full = all): brief, references, src, meta, tools,
monitor (tools/monitor/, pulls tools), ai-check (tools/ai-detection/ +
report/ai-check/, pulls tools).
"""

_TOOL_HINTS = {
    "uv": "install from https://docs.astral.sh/uv/",
    "claude": "the claude-code CLI; see https://docs.claude.com/claude-code",
}


def _warn_missing_tools() -> None:
    for tool, hint in _TOOL_HINTS.items():
        if shutil.which(tool) is None:
            print(f"note: '{tool}' not found on PATH; tools/ scripts need it ({hint})", file=sys.stderr)


def _parse_with(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def handle(arguments: argparse.Namespace) -> int:
    target = _shared.resolve_directory(arguments.directory)
    try:
        layers = resolve_layers(full=arguments.full, with_layers=_parse_with(arguments.with_layers))
    except ValueError as error:
        print(f"{error}\nValid layers: {', '.join(ALL_LAYERS)}", file=sys.stderr)
        return 1

    result = init_project(target, layers=layers, name=arguments.name, cover=arguments.cover, force=arguments.force)
    print(format_summary(result, target))
    if "tools" in layers:
        _warn_missing_tools()
    return 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "init",
        help="scaffold a role-based project structure",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=None,
        help="project directory (defaults to current working directory)",
    )
    parser.add_argument("--full", action="store_true", help="scaffold all layers plus the embedded monitor scripts")
    parser.add_argument(
        "--with",
        dest="with_layers",
        metavar="LAYERS",
        help="comma-separated optional layers to add (deps auto-resolved)",
    )
    parser.add_argument("--name", help="project name injected into CLAUDE.md and content.yaml (default: dir name)")
    parser.add_argument("--cover", action="store_true", help="write a cover + TOC content.yaml (Shape B)")
    parser.add_argument("--force", action="store_true", help="overwrite existing files instead of skipping them")
    parser.set_defaults(func=handle)
