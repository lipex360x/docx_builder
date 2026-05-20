from __future__ import annotations

import argparse
import sys
from pathlib import Path

from docx_builder.builder import build, init_project
from docx_builder.skill_installer import SkillScope, install_skill


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="docx_builder",
        description="Generate DOCX reports from a content.yaml in any directory.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build the DOCX from content.yaml.")
    build_parser.add_argument(
        "directory",
        nargs="?",
        default=None,
        help="Project directory (defaults to current working directory).",
    )
    build_parser.add_argument("--output", help="Override output filename.")
    build_parser.add_argument("--template-dir", help="Override template directory.")

    init_parser = subparsers.add_parser("init", help="Scaffold content.yaml and images/ in a directory.")
    init_parser.add_argument(
        "directory",
        nargs="?",
        default=None,
        help="Project directory (defaults to current working directory).",
    )
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing content.yaml.")

    install_parser = subparsers.add_parser("install", help="Install bundled assets.")
    install_subparsers = install_parser.add_subparsers(dest="install_target", required=True)

    skill_parser = install_subparsers.add_parser("skill", help="Install the docx_builder skill for Claude Code.")
    skill_parser.add_argument(
        "--scope",
        choices=["local", "global", "ask"],
        default="ask",
        help="Install location: local (./.claude/skills/), global (~/.claude/skills/), or ask interactively (default).",
    )
    skill_parser.add_argument("--force", action="store_true", help="Overwrite existing SKILL.md.")

    return parser


def _resolve_dir(value: str | None) -> Path:
    return Path(value).resolve() if value else Path.cwd()


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    directory = getattr(args, "directory", None)
    target = _resolve_dir(directory)

    if args.command == "build":
        try:
            output_path = build(target, template_dir=args.template_dir, output_override=args.output)
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"Saved: {output_path}")
        return 0

    if args.command == "init":
        try:
            content_path = init_project(target, force=args.force)
        except FileExistsError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"Initialized: {content_path}")
        return 0

    if args.command == "install" and args.install_target == "skill":
        return _install_skill_command(args.scope, args.force)

    parser.error(f"unknown command: {args.command}")
    return 2


def _install_skill_command(scope_choice: str, force: bool) -> int:
    scope = _resolve_skill_scope(scope_choice)
    if scope is None:
        print("error: aborted", file=sys.stderr)
        return 1
    try:
        installed_path = install_skill(scope=scope, force=force)
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Installed: {installed_path}")
    return 0


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


if __name__ == "__main__":
    sys.exit(main())
