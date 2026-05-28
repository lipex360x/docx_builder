from pathlib import Path

import pytest

from docx_builder.builder import _normalise_sections, init_project
from docx_builder.cli import main


def _flagged_sections(count: int) -> dict[str, list[dict[str, object]]]:
    return {"sections": [{"call": "body", "text": "x", "hide_page_counter": True} for _ in range(count)]}


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


def test_cli_export_pdf_help_lists_subcommand(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["export", "pdf", "--help"])

    output = capsys.readouterr().out
    assert "--input" in output
    assert "--output" in output


def test_cli_build_help_documents_pdf_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["build", "--help"])

    output = capsys.readouterr().out
    assert "--pdf" in output


def test_cli_export_pdf_non_macos_returns_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from docx_builder import export

    monkeypatch.setattr(export.sys, "platform", "linux")
    init_project(tmp_path)
    main(["build", str(tmp_path)])
    capsys.readouterr()

    exit_code = main(["export", "pdf", str(tmp_path)])

    assert exit_code == 1
    error = capsys.readouterr().err
    assert "requires macOS" in error


def test_cli_build_pdf_flag_invokes_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[tuple[Path, Path]] = []

    def fake_export(input_docx: Path, output_pdf: Path, update_source: bool = True) -> Path:
        calls.append((input_docx, output_pdf))
        return output_pdf

    monkeypatch.setattr("docx_builder.cli._export.export_pdf", fake_export)
    init_project(tmp_path)

    exit_code = main(["build", str(tmp_path), "--pdf"])

    assert exit_code == 0
    assert len(calls) == 1


def test_cli_build_open_opens_the_docx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from docx_builder.cli import _shared

    opened: list[Path] = []
    monkeypatch.setattr(_shared.sys, "platform", "darwin")
    monkeypatch.setattr(_shared, "_run_open", lambda path, app=None: opened.append(path))
    init_project(tmp_path)

    exit_code = main(["build", str(tmp_path), "--open"])

    assert exit_code == 0
    assert len(opened) == 1
    assert opened[0].suffix == ".docx"


def test_cli_build_open_non_macos_prints_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from docx_builder.cli import _shared

    opened: list[Path] = []
    monkeypatch.setattr(_shared.sys, "platform", "linux")
    monkeypatch.setattr(_shared, "_run_open", lambda path, app=None: opened.append(path))
    init_project(tmp_path)

    exit_code = main(["build", str(tmp_path), "--open"])

    assert exit_code == 0
    assert not opened
    output = capsys.readouterr().out
    assert "note: --open is currently macOS-only" in output


def test_cli_build_pdf_open_opens_pdf_and_docx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from docx_builder.cli import _shared

    opened: list[Path] = []
    monkeypatch.setattr(_shared.sys, "platform", "darwin")
    monkeypatch.setattr(_shared, "_run_open", lambda path, app=None: opened.append(path))
    monkeypatch.setattr(
        "docx_builder.cli._export.export_pdf",
        lambda input_docx, output_pdf, update_source=True: output_pdf,
    )
    init_project(tmp_path)

    exit_code = main(["build", str(tmp_path), "--pdf", "--open"])

    assert exit_code == 0
    assert {path.suffix for path in opened} == {".pdf", ".docx"}


def test_cli_export_pdf_open_opens_pdf_and_docx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from docx_builder.cli import _shared

    opened: list[Path] = []
    monkeypatch.setattr(_shared.sys, "platform", "darwin")
    monkeypatch.setattr(_shared, "_run_open", lambda path, app=None: opened.append(path))
    monkeypatch.setattr(
        "docx_builder.cli._export.export_pdf",
        lambda input_docx, output_pdf, update_source=True: output_pdf,
    )
    init_project(tmp_path)
    main(["build", str(tmp_path)])

    exit_code = main(["export", "pdf", str(tmp_path), "--open"])

    assert exit_code == 0
    assert {path.suffix for path in opened} == {".pdf", ".docx"}


def test_cli_export_pdf_no_update_source_threads_through(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []

    def fake_export(input_docx: Path, output_pdf: Path, update_source: bool = True) -> Path:
        calls.append(update_source)
        return output_pdf

    monkeypatch.setattr("docx_builder.cli._export.export_pdf", fake_export)
    init_project(tmp_path)
    main(["build", str(tmp_path)])

    exit_code = main(["export", "pdf", str(tmp_path), "--no-update-source"])

    assert exit_code == 0
    assert calls == [False]


def test_cli_build_pdf_no_update_source_threads_through(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []

    def fake_export(input_docx: Path, output_pdf: Path, update_source: bool = True) -> Path:
        calls.append(update_source)
        return output_pdf

    monkeypatch.setattr("docx_builder.cli._export.export_pdf", fake_export)
    init_project(tmp_path)

    exit_code = main(["build", str(tmp_path), "--pdf", "--no-update-source"])

    assert exit_code == 0
    assert calls == [False]


def test_cli_export_pdf_help_documents_new_flags(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["export", "pdf", "--help"])

    output = capsys.readouterr().out
    assert "--no-update-source" in output
    assert "--open" in output


def test_cli_build_help_documents_open_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["build", "--help"])

    output = capsys.readouterr().out
    assert "--open" in output
    assert "--no-update-source" in output


def test_cli_init_then_build(tmp_path: Path) -> None:
    init_exit = main(["init", str(tmp_path)])
    assert init_exit == 0

    build_exit = main(["build", str(tmp_path)])
    assert build_exit == 0

    docx_files = list(tmp_path.glob("*.docx"))
    assert len(docx_files) == 1


def test_root_help_exits_zero_with_description(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])

    assert exit_info.value.code == 0
    output = capsys.readouterr().out
    assert "docx_builder" in output


def test_build_help_has_examples_block(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["build", "--help"])

    assert exit_info.value.code == 0
    output = capsys.readouterr().out
    assert "Examples:" in output
    assert "docx_builder build" in output


def test_init_help_has_examples_block(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["init", "--help"])

    assert exit_info.value.code == 0
    output = capsys.readouterr().out
    assert "Examples:" in output
    assert "docx_builder init" in output


def test_export_pdf_help_has_examples_block(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["export", "pdf", "--help"])

    assert exit_info.value.code == 0
    output = capsys.readouterr().out
    assert "Examples:" in output
    assert "docx_builder export pdf" in output


def test_install_skill_help_has_examples_block(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["install", "skill", "--help"])

    assert exit_info.value.code == 0
    output = capsys.readouterr().out
    assert "Examples:" in output
    assert "docx_builder install skill" in output


def test_build_missing_content_suggests_init(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["build", str(tmp_path)])

    assert exit_code == 1
    error = capsys.readouterr().err
    assert "docx_builder init" in error


def test_init_existing_suggests_force(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "content.yaml").write_text("existing")

    exit_code = main(["init", str(tmp_path)])

    assert exit_code == 1
    error = capsys.readouterr().err
    assert "--force" in error


def test_init_prints_created_message(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["init", str(tmp_path)])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert output.startswith("Created:")
    assert "Initialized" not in output


def test_deprecation_warning_fires_once_for_many_flagged_sections(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _normalise_sections(_flagged_sections(5))

    error = capsys.readouterr().err
    assert error.count("'hide_page_counter' is deprecated") == 1


def test_deprecation_warning_suppressed_by_env(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("DOCX_BUILDER_NO_DEPRECATION", "1")

    _normalise_sections(_flagged_sections(3))

    assert "deprecated" not in capsys.readouterr().err


def test_no_deprecation_warning_without_flag(capsys: pytest.CaptureFixture[str]) -> None:
    _normalise_sections({"sections": [{"call": "body", "text": "x"}]})

    assert "deprecated" not in capsys.readouterr().err


def test_open_in_word_invokes_microsoft_word(monkeypatch: pytest.MonkeyPatch) -> None:
    from docx_builder.cli import _shared

    commands: list[tuple[list[str], bool]] = []
    monkeypatch.setattr(_shared.sys, "platform", "darwin")
    monkeypatch.setattr(_shared.subprocess, "run", lambda command, check: commands.append((command, check)))

    _shared.open_in_word(Path("/report.docx"))

    assert commands == [(["open", "-a", "Microsoft Word", "/report.docx"], True)]
