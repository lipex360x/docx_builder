from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from types import ModuleType

import pytest

from docx_builder import scaffold


def _load_intake(tmp_path: Path) -> ModuleType:
    scaffold.scaffold(tmp_path, layers={"monitor", "tools"}, name="D", cover=False, force=False)
    script = tmp_path / "tools" / "monitor" / "screenshot_intake.py"
    spec = importlib.util.spec_from_file_location("screenshot_intake", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _png(directory: Path, name: str, size: int = 16, mtime: float | None = None) -> Path:
    path = directory / name
    path.write_bytes(b"\x89PNG\r\n" + b"\x00" * size)
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


def test_pending_pngs_fifo_oldest_first(tmp_path: Path) -> None:
    intake = _load_intake(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    _png(source, "c.png", mtime=300)
    _png(source, "a.png", mtime=100)
    _png(source, "b.png", mtime=200)

    assert [png.name for png in intake.pending_pngs(source)] == ["a.png", "b.png", "c.png"]


def test_pending_pngs_missing_source_is_empty(tmp_path: Path) -> None:
    intake = _load_intake(tmp_path)

    assert intake.pending_pngs(tmp_path / "nope") == []


def test_drain_requires_two_stable_samples(tmp_path: Path) -> None:
    intake = _load_intake(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    inbox = tmp_path / "inbox"
    _png(source, "shot.png")
    cache: dict[str, int] = {}

    assert intake.drain(source, inbox, size_cache=cache) == []
    moved = intake.drain(source, inbox, size_cache=cache)

    assert [png.name for png in moved] == ["shot.png"]
    assert (inbox / "shot.png").exists()
    assert not (source / "shot.png").exists()


def test_drain_skips_growing_file(tmp_path: Path) -> None:
    intake = _load_intake(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    inbox = tmp_path / "inbox"
    shot = _png(source, "shot.png", size=10)
    cache: dict[str, int] = {}

    intake.drain(source, inbox, size_cache=cache)
    shot.write_bytes(b"\x89PNG\r\n" + b"\x00" * 80)
    moved = intake.drain(source, inbox, size_cache=cache)

    assert moved == []
    assert (source / "shot.png").exists()


def test_drain_fifo_order(tmp_path: Path) -> None:
    intake = _load_intake(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    inbox = tmp_path / "inbox"
    _png(source, "c.png", mtime=300)
    _png(source, "a.png", mtime=100)
    _png(source, "b.png", mtime=200)
    cache: dict[str, int] = {}

    intake.drain(source, inbox, size_cache=cache)
    moved = intake.drain(source, inbox, size_cache=cache)

    assert [png.name for png in moved] == ["a.png", "b.png", "c.png"]


def test_two_phase_leaves_no_partial(tmp_path: Path) -> None:
    intake = _load_intake(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    inbox = tmp_path / "inbox"
    _png(source, "shot.png")

    intake.run_once(source, inbox, settle=0.0)

    leftovers = [entry.name for entry in inbox.iterdir() if not entry.name.endswith(".png")]
    assert leftovers == []
    assert (inbox / "shot.png").exists()


def test_run_once_drains_backlog(tmp_path: Path) -> None:
    intake = _load_intake(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    inbox = tmp_path / "inbox"
    for name in ("a.png", "b.png", "c.png"):
        _png(source, name)

    moved = intake.run_once(source, inbox, settle=0.0)

    assert {png.name for png in moved} == {"a.png", "b.png", "c.png"}


def test_moved_file_clears_cache_and_does_not_reprocess(tmp_path: Path) -> None:
    intake = _load_intake(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    inbox = tmp_path / "inbox"
    _png(source, "shot.png")
    cache: dict[str, int] = {}

    intake.drain(source, inbox, size_cache=cache)
    intake.drain(source, inbox, size_cache=cache)

    assert not (source / "shot.png").exists()
    assert "shot.png" not in cache
    assert intake.drain(source, inbox, size_cache=cache) == []


def test_main_once_smoke(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    intake = _load_intake(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    inbox = tmp_path / "inbox"
    _png(source, "shot.png")

    code = intake.main([str(source), str(inbox), "--once", "--settle", "0"])

    assert code == 0
    assert (inbox / "shot.png").exists()
    assert "intake shot.png" in capsys.readouterr().out
