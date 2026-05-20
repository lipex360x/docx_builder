from pathlib import Path

import pytest

from docx_builder.builder import init_project
from docx_builder.cli import main


def test_init_creates_content_yaml(tmp_path: Path) -> None:
    init_project(tmp_path)

    assert (tmp_path / "content.yaml").exists()


def test_init_does_not_create_images_dir(tmp_path: Path) -> None:
    init_project(tmp_path)

    assert not (tmp_path / "images").exists()


def test_init_skeleton_is_minimal(tmp_path: Path) -> None:
    init_project(tmp_path)

    content = (tmp_path / "content.yaml").read_text()
    assert "content.yaml" in content
    assert "styles-reference.md" in content


def test_init_refuses_existing_without_force(tmp_path: Path) -> None:
    (tmp_path / "content.yaml").write_text("existing")

    with pytest.raises(FileExistsError):
        init_project(tmp_path)


def test_init_overwrites_with_force(tmp_path: Path) -> None:
    (tmp_path / "content.yaml").write_text("existing")

    init_project(tmp_path, force=True)

    assert "existing" not in (tmp_path / "content.yaml").read_text()


def test_cli_build_returns_zero_on_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    init_project(tmp_path)

    exit_code = main(["build", str(tmp_path)])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Saved:" in output


def test_cli_build_missing_content_returns_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["build", str(tmp_path)])

    assert exit_code == 1
    error = capsys.readouterr().err
    assert "content.yaml not found" in error


def test_cli_init_then_build(tmp_path: Path) -> None:
    init_exit = main(["init", str(tmp_path)])
    assert init_exit == 0

    build_exit = main(["build", str(tmp_path)])
    assert build_exit == 0

    docx_files = list(tmp_path.glob("*.docx"))
    assert len(docx_files) == 1
