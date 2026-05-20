from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Literal

SkillScope = Literal["local", "global"]

_SKILL_NAME = "docx_builder"
_SKILL_FILE = "SKILL.md"


def resolve_skill_dir(scope: SkillScope, *, cwd: Path | None = None) -> Path:
    base = (cwd or Path.cwd()) / ".claude" / "skills" if scope == "local" else Path.home() / ".claude" / "skills"
    return base / _SKILL_NAME


def install_skill(
    *,
    scope: SkillScope,
    force: bool = False,
    cwd: Path | None = None,
) -> Path:
    target_dir = resolve_skill_dir(scope, cwd=cwd)
    target_path = target_dir / _SKILL_FILE

    if target_path.exists() and not force:
        raise FileExistsError(f"{target_path} already exists (use --force to overwrite)")

    target_dir.mkdir(parents=True, exist_ok=True)
    skill_content = files("docx_builder.skill").joinpath(_SKILL_FILE).read_text()
    target_path.write_text(skill_content)
    return target_path
