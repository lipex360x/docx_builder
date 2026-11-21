from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from docx_builder import word_inspect
from docx_builder.cli import main


def test_cli_inspect_word_passes_full_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "Report.docx"
    target.write_bytes(b"docx")
    monkeypatch.setattr("docx_builder.cli._inspect.inspect_word", lambda path: f"Inspected: {path}")
    assert main(["inspect-word", str(target)]) == 0
    assert str(target) in capsys.readouterr().out


def test_inspect_does_not_run_on_other_platforms(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(word_inspect.sys, "platform", "linux")
    with pytest.raises(word_inspect.InspectionError, match="macOS"):
        word_inspect.inspect_word(tmp_path / "Report.docx")


def test_inspect_reports_automation_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(word_inspect.sys, "platform", "darwin")
    target = tmp_path / "Report.docx"
    target.write_bytes(b"docx")

    def fail(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.CalledProcessError(1, ["osascript"], stderr="Word unavailable")

    monkeypatch.setattr(word_inspect.subprocess, "run", fail)
    with pytest.raises(word_inspect.InspectionError, match="Word unavailable"):
        word_inspect.inspect_word(target)


def test_inspect_returns_live_word_status_and_comments(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(word_inspect.sys, "platform", "darwin")
    target = tmp_path / "Report.docx"
    target.write_bytes(b"docx")
    seen: list[list[str]] = []

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        seen.append(args)
        return subprocess.CompletedProcess(args, 0, "Status: unsaved changes\nComments: 1\nComment: review this\n", "")

    monkeypatch.setattr(word_inspect.subprocess, "run", fake_run)
    result = word_inspect.inspect_word(target)
    assert "unsaved changes" in result
    assert "review this" in result
    assert seen[0][-2:] == [str(target.resolve()), target.name]


def test_inspect_closed_document_reads_saved_comments(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from docx import Document

    monkeypatch.setattr(word_inspect.sys, "platform", "darwin")
    target = tmp_path / "Report.docx"
    document = Document()
    run = document.add_paragraph("Selected text").runs[0]
    document.add_comment(run, text="Please review\nSecond line", author="Felipe")
    document.save(target)

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 0, "NOT_OPEN\n", "")

    monkeypatch.setattr(word_inspect.subprocess, "run", fake_run)
    result = word_inspect.inspect_word(target)
    assert "Not open in Microsoft Word" in result
    assert "Saved comments: 1" in result
    assert "Felipe" in result and "Please review\nSecond line" in result
