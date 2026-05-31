from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from docx_builder import scaffold


def test_resolve_layers_full_returns_all() -> None:
    assert scaffold.resolve_layers(full=True, with_layers=[]) == set(scaffold.ALL_LAYERS)


def test_resolve_layers_with_expands_monitor_dep() -> None:
    assert scaffold.resolve_layers(full=False, with_layers=["monitor"]) == {"monitor", "tools"}


def test_resolve_layers_with_expands_ai_check_dep() -> None:
    assert scaffold.resolve_layers(full=False, with_layers=["ai-check"]) == {"ai-check", "tools"}


def test_resolve_layers_empty() -> None:
    assert scaffold.resolve_layers(full=False, with_layers=[]) == set()


def test_resolve_layers_unknown_raises() -> None:
    with pytest.raises(ValueError, match="unknown"):
        scaffold.resolve_layers(full=False, with_layers=["bogus"])


def test_scaffold_base_creates_report_tree(tmp_path: Path) -> None:
    scaffold.scaffold(tmp_path, layers=set(), name="Demo", cover=False, force=False)

    for sub in ("images", "assets", "output", "templates"):
        assert (tmp_path / "report" / sub).is_dir()
    assert (tmp_path / "report" / "content.yaml").exists()
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / ".gitignore").exists()
    assert (tmp_path / ".work").is_dir()


def test_scaffold_base_gitkeep_in_empty_dirs(tmp_path: Path) -> None:
    scaffold.scaffold(tmp_path, layers=set(), name="Demo", cover=False, force=False)

    assert (tmp_path / "report" / "images" / ".gitkeep").exists()
    assert (tmp_path / ".work" / ".gitkeep").exists()


def test_scaffold_shape_a_by_default(tmp_path: Path) -> None:
    scaffold.scaffold(tmp_path, layers=set(), name="MyDoc", cover=False, force=False)

    data = yaml.safe_load((tmp_path / "report" / "content.yaml").read_text())
    assert "cover" not in data
    assert data["sections"][0]["text"] == "MyDoc"


def test_scaffold_shape_b_with_cover(tmp_path: Path) -> None:
    scaffold.scaffold(tmp_path, layers=set(), name="MyDoc", cover=True, force=False)

    data = yaml.safe_load((tmp_path / "report" / "content.yaml").read_text())
    assert "cover" in data
    assert any(item.get("call") == "toc" for item in data["front_matter"])


def test_scaffold_injects_name_into_claude_md(tmp_path: Path) -> None:
    scaffold.scaffold(tmp_path, layers=set(), name="Acme Report", cover=False, force=False)

    text = (tmp_path / "CLAUDE.md").read_text()
    assert "Acme Report" in text
    assert "__PROJECT_NAME__" not in text


def test_scaffold_brief_layer(tmp_path: Path) -> None:
    scaffold.scaffold(tmp_path, layers={"brief"}, name="D", cover=False, force=False)

    assert (tmp_path / "brief").is_dir()
    assert (tmp_path / "brief" / ".gitkeep").exists()


def test_scaffold_monitor_layer_writes_intake(tmp_path: Path) -> None:
    scaffold.scaffold(tmp_path, layers={"monitor", "tools"}, name="D", cover=False, force=False)

    assert (tmp_path / "tools" / "monitor" / "screenshot_intake.py").exists()
    assert not (tmp_path / "tools" / "monitor" / "watch_screenshots.sh").exists()


def test_scaffold_monitor_script_executable(tmp_path: Path) -> None:
    scaffold.scaffold(tmp_path, layers={"monitor", "tools"}, name="D", cover=False, force=False)

    script = tmp_path / "tools" / "monitor" / "screenshot_intake.py"
    assert os.access(script, os.X_OK)


def test_scaffold_ai_check_layer(tmp_path: Path) -> None:
    scaffold.scaffold(tmp_path, layers={"ai-check", "tools"}, name="D", cover=False, force=False)

    assert (tmp_path / "tools" / "ai-detection" / "README.md").exists()
    assert (tmp_path / "report" / "ai-check").is_dir()


def test_scaffold_is_idempotent_on_content(tmp_path: Path) -> None:
    scaffold.scaffold(tmp_path, layers=set(), name="D", cover=False, force=False)
    (tmp_path / "report" / "content.yaml").write_text("custom: true\n")

    result = scaffold.scaffold(tmp_path, layers=set(), name="D", cover=False, force=False)

    assert "custom: true" in (tmp_path / "report" / "content.yaml").read_text()
    assert any("content.yaml" in entry for entry in result.skipped)


def test_scaffold_additive_full_after_lean(tmp_path: Path) -> None:
    scaffold.scaffold(tmp_path, layers=set(), name="D", cover=False, force=False)
    (tmp_path / "report" / "content.yaml").write_text("custom: true\n")

    scaffold.scaffold(tmp_path, layers=set(scaffold.ALL_LAYERS), name="D", cover=False, force=False)

    assert (tmp_path / "brief").is_dir()
    assert (tmp_path / "tools" / "monitor").is_dir()
    assert "custom: true" in (tmp_path / "report" / "content.yaml").read_text()


def test_scaffold_force_overwrites(tmp_path: Path) -> None:
    scaffold.scaffold(tmp_path, layers=set(), name="D", cover=False, force=False)
    (tmp_path / "report" / "content.yaml").write_text("custom: true\n")

    scaffold.scaffold(tmp_path, layers=set(), name="D", cover=False, force=True)

    assert "custom: true" not in (tmp_path / "report" / "content.yaml").read_text()


def test_scaffold_result_tracks_created(tmp_path: Path) -> None:
    result = scaffold.scaffold(tmp_path, layers=set(), name="D", cover=False, force=False)

    joined = " ".join(result.created)
    assert "CLAUDE.md" in joined
    assert "content.yaml" in joined


def test_format_summary_lists_created(tmp_path: Path) -> None:
    result = scaffold.scaffold(tmp_path, layers=set(), name="D", cover=False, force=False)

    summary = scaffold.format_summary(result, tmp_path)
    assert "CLAUDE.md" in summary
