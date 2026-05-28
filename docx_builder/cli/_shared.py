from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def resolve_directory(value: str | None) -> Path:
    return Path(value).resolve() if value else Path.cwd()


def _run_open(path: Path, app: str | None = None) -> None:
    command = ["open"]
    if app is not None:
        command += ["-a", app]
    command.append(str(path))
    subprocess.run(command, check=True)


def open_file(path: Path) -> None:
    if sys.platform != "darwin":
        print("note: --open is currently macOS-only")
        return
    _run_open(path)


def open_in_word(path: Path) -> None:
    if sys.platform != "darwin":
        return
    _run_open(path, app="Microsoft Word")


def print_content_not_found(project_dir: Path) -> None:
    print(
        f"content.yaml not found in {project_dir}.\n"
        "Scaffold one with: docx_builder init\n"
        "Or point at the right directory: docx_builder build /path/to/project",
        file=sys.stderr,
    )


def print_content_exists(project_dir: Path) -> None:
    print(
        f"content.yaml already exists in {project_dir}.\nOverwrite it with: docx_builder init --force",
        file=sys.stderr,
    )


def print_missing_path(message: str) -> None:
    print(message, file=sys.stderr)


def print_export_error(message: str) -> None:
    print(message, file=sys.stderr)


def print_install_aborted() -> None:
    print(
        "No scope chosen — skill not installed.\nPick one explicitly: docx_builder install skill --scope local|global",
        file=sys.stderr,
    )


def print_skill_exists(message: str) -> None:
    print(
        f"{message}\nOverwrite it with: docx_builder install skill --force",
        file=sys.stderr,
    )
