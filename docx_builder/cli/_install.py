from __future__ import annotations

import argparse

from docx_builder.skill_installer import SkillScope, install_skill

from . import _shared

EPILOG = """\
Examples:
  docx_builder install skill
  docx_builder install skill --scope local
  docx_builder install skill --scope global --force

Installs the docx_builder skill so Claude Code can discover it. Without
--scope it asks interactively whether to install locally (this project) or
globally (all projects). Use --force to overwrite an existing SKILL.md.
"""


def _resolve_skill_scope(choice: str) -> SkillScope | None:
    if choice == "local":
        return "local"
    if choice == "global":
        return "global"
    return _ask_skill_scope()


def _ask_skill_scope() -> SkillScope | None:
    prompt = (
        "Where to install the docx_builder skill?\n"
        "  1) local  — ./.claude/skills/docx_builder/SKILL.md (this project only)\n"
        "  2) global — ~/.claude/skills/docx_builder/SKILL.md (all projects)\n"
        "Choose [1/2]: "
    )
    try:
        answer = input(prompt).strip().lower()
    except EOFError:
        return None
    if answer in {"1", "local", "l"}:
        return "local"
    if answer in {"2", "global", "g"}:
        return "global"
    return None


def handle(arguments: argparse.Namespace) -> int:
    scope = _resolve_skill_scope(arguments.scope)
    if scope is None:
        _shared.print_install_aborted()
        return 1
    try:
        installed_path = install_skill(scope=scope, force=arguments.force)
    except FileExistsError as exception:
        _shared.print_skill_exists(str(exception))
        return 1
    print(f"Installed: {installed_path}")
    return 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "install",
        help="install bundled assets",
    )
    install_subparsers = parser.add_subparsers(dest="install_target", required=True, metavar="<target>")
    skill_parser = install_subparsers.add_parser(
        "skill",
        help="install the docx_builder skill for Claude Code",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    skill_parser.add_argument(
        "--scope",
        choices=["local", "global", "ask"],
        default="ask",
        help="install location: local, global, or ask interactively (default)",
    )
    skill_parser.add_argument("--force", action="store_true", help="overwrite existing SKILL.md")
    skill_parser.set_defaults(func=handle)
