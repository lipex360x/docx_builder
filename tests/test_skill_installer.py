from pathlib import Path

import pytest

from docx_builder.cli import main
from docx_builder.skill_installer import install_skill, resolve_skill_dir


def test_resolve_skill_dir_local(tmp_path: Path) -> None:
    target = resolve_skill_dir("local", cwd=tmp_path)
    assert target == tmp_path / ".claude" / "skills" / "docx_builder"


def test_resolve_skill_dir_global() -> None:
    target = resolve_skill_dir("global")
    assert target == Path.home() / ".claude" / "skills" / "docx_builder"


def test_install_skill_local_creates_skill_md(tmp_path: Path) -> None:
    target = install_skill(scope="local", cwd=tmp_path)

    assert target == tmp_path / ".claude" / "skills" / "docx_builder" / "SKILL.md"
    assert target.exists()
    content = target.read_text()
    assert "name: docx_builder" in content
    assert "description:" in content


def test_install_skill_refuses_existing(tmp_path: Path) -> None:
    install_skill(scope="local", cwd=tmp_path)

    with pytest.raises(FileExistsError):
        install_skill(scope="local", cwd=tmp_path)


def test_install_skill_force_overwrites(tmp_path: Path) -> None:
    target = install_skill(scope="local", cwd=tmp_path)
    target.write_text("modified")

    install_skill(scope="local", cwd=tmp_path, force=True)

    assert "name: docx_builder" in target.read_text()


def test_cli_install_skill_local(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["install", "skill", "--scope", "local"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Installed:" in out
    assert (tmp_path / ".claude" / "skills" / "docx_builder" / "SKILL.md").exists()
