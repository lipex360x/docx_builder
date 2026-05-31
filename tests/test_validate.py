from __future__ import annotations

from pathlib import Path

import pytest

from docx_builder import report, validate
from docx_builder.cli import main

EM_DASH = "—"
HORIZONTAL_BAR = "―"
FIGURE_DASH = "‒"
EN_DASH = "–"


def _write(directory: Path, body: str) -> None:
    (directory / "content.yaml").write_text(body, encoding="utf-8")


def test_em_dash_constant_comes_from_report() -> None:
    assert validate.EM_DASH is report.EM_DASH


def test_default_forbidden_includes_em_horizontal_figure() -> None:
    chars = set(validate.DEFAULT_FORBIDDEN)
    assert {EM_DASH, HORIZONTAL_BAR, FIGURE_DASH} <= chars
    assert EN_DASH not in chars


def test_strict_adds_en_dash() -> None:
    assert EN_DASH in validate.STRICT_FORBIDDEN
    assert {EM_DASH, HORIZONTAL_BAR, FIGURE_DASH} <= set(validate.STRICT_FORBIDDEN)


def test_forbidden_chars_picks_set_by_strict() -> None:
    assert validate.forbidden_chars(strict=False) == validate.DEFAULT_FORBIDDEN
    assert validate.forbidden_chars(strict=True) == validate.STRICT_FORBIDDEN


def test_scan_content_flags_em_dash_in_body() -> None:
    data = {"sections": [{"call": "body", "text": f"Hello {EM_DASH} world"}]}

    violations = validate.scan_content(data, validate.DEFAULT_FORBIDDEN)

    assert len(violations) == 1
    assert violations[0].char == EM_DASH
    assert "body" in violations[0].location


def test_scan_content_flags_horizontal_bar_and_figure_dash() -> None:
    data = {
        "sections": [
            {"call": "body", "text": f"a {HORIZONTAL_BAR} b"},
            {"call": "body", "text": f"c {FIGURE_DASH} d"},
        ]
    }

    violations = validate.scan_content(data, validate.DEFAULT_FORBIDDEN)

    assert {violation.char for violation in violations} == {HORIZONTAL_BAR, FIGURE_DASH}


def test_scan_content_ignores_non_prose_fields() -> None:
    data = {
        "sections": [{"call": "figure", "filename": f"a{EM_DASH}b.png", "label": f"Fig{EM_DASH}", "caption": "clean"}]
    }

    violations = validate.scan_content(data, validate.STRICT_FORBIDDEN)

    assert violations == []


def test_scan_content_flags_caption_not_filename() -> None:
    data = {"sections": [{"call": "figure", "filename": "a-b.png", "label": "Fig 1", "caption": f"see {EM_DASH} here"}]}

    violations = validate.scan_content(data, validate.DEFAULT_FORBIDDEN)

    assert len(violations) == 1
    assert "caption" in violations[0].location


def test_scan_content_flags_bold_lead_both_fields() -> None:
    data = {"sections": [{"call": "bold_lead", "bold": f"Lead {EM_DASH}", "rest": f"rest {EM_DASH} more"}]}

    violations = validate.scan_content(data, validate.DEFAULT_FORBIDDEN)

    assert len(violations) == 2
    fields = {violation.location.split(".")[-1] for violation in violations}
    assert fields == {"bold", "rest"}


def test_scan_content_covers_front_matter_and_sections() -> None:
    data = {
        "front_matter": [{"call": "h1", "text": f"Title {EM_DASH}"}],
        "sections": [{"call": "body", "text": f"Body {EM_DASH}"}],
    }

    violations = validate.scan_content(data, validate.DEFAULT_FORBIDDEN)

    locations = " ".join(violation.location for violation in violations)
    assert "front_matter" in locations
    assert "sections" in locations


def test_scan_content_skips_missing_prose_field() -> None:
    data = {"sections": [{"call": "body"}, {"call": "body", "text": f"x {EM_DASH} y"}]}

    violations = validate.scan_content(data, validate.DEFAULT_FORBIDDEN)

    assert len(violations) == 1


def test_scan_content_ignores_structural_calls() -> None:
    data = {"sections": [{"call": "page_break"}, {"call": "toc", "levels": "1-2"}]}

    assert validate.scan_content(data, validate.DEFAULT_FORBIDDEN) == []


def test_scan_content_flags_table_header_cell() -> None:
    data = {"sections": [{"call": "table", "header": [f"Col {EM_DASH}"], "rows": [["clean"]]}]}

    violations = validate.scan_content(data, validate.DEFAULT_FORBIDDEN)

    assert len(violations) == 1
    assert "header" in violations[0].location


def test_scan_content_flags_table_body_cell() -> None:
    data = {"sections": [{"call": "table", "rows": [["clean", f"bad {EM_DASH} cell"]]}]}

    violations = validate.scan_content(data, validate.DEFAULT_FORBIDDEN)

    assert len(violations) == 1
    assert "rows" in violations[0].location


def test_scan_content_table_ignores_non_prose_keys() -> None:
    data = {"sections": [{"call": "table", "rows": [["clean"]], "widths": [100], "borders": True, "style": "table"}]}

    assert validate.scan_content(data, validate.STRICT_FORBIDDEN) == []


def test_en_dash_only_flagged_in_strict() -> None:
    data = {"sections": [{"call": "body", "text": f"range 1{EN_DASH}2"}]}

    assert validate.scan_content(data, validate.DEFAULT_FORBIDDEN) == []
    assert len(validate.scan_content(data, validate.STRICT_FORBIDDEN)) == 1


def test_violation_reports_position_and_snippet() -> None:
    data = {"sections": [{"call": "body", "text": f"Hello {EM_DASH} world"}]}

    violation = validate.scan_content(data, validate.DEFAULT_FORBIDDEN)[0]

    assert violation.position == 6
    assert EM_DASH in violation.snippet


def test_validate_project_reads_content_yaml(tmp_path: Path) -> None:
    _write(tmp_path, f'sections:\n  - call: body\n    text: "x {EM_DASH} y"\n')

    violations = validate.validate_project(tmp_path, strict=False, also=[])

    assert len(violations) == 1


def test_validate_project_missing_content_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        validate.validate_project(tmp_path, strict=False, also=[])


def test_validate_project_falls_back_to_report_dir(tmp_path: Path) -> None:
    report_dir = tmp_path / "report"
    report_dir.mkdir()
    (report_dir / "content.yaml").write_text(
        f'sections:\n  - call: body\n    text: "x {EM_DASH} y"\n', encoding="utf-8"
    )

    violations = validate.validate_project(tmp_path, strict=False, also=[])

    assert len(violations) == 1


def test_validate_project_scans_also_files(tmp_path: Path) -> None:
    _write(tmp_path, 'sections:\n  - call: body\n    text: "clean"\n')
    brief = tmp_path / "brief.md"
    brief.write_text(f"intro {EM_DASH} outro", encoding="utf-8")

    violations = validate.validate_project(tmp_path, strict=False, also=[brief])

    assert len(violations) == 1
    assert "brief.md" in violations[0].location


def test_format_violations_lists_each() -> None:
    violation = validate.Violation(
        location="sections[0].body",
        char=EM_DASH,
        char_name="em-dash (U+2014)",
        position=6,
        snippet=f"Hello [{EM_DASH}] world",
    )

    rendered = validate.format_violations([violation])

    assert "sections[0].body" in rendered
    assert "em-dash (U+2014)" in rendered


def test_cli_validate_clean_returns_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(tmp_path, 'sections:\n  - call: body\n    text: "all clean here"\n')

    code = main(["validate", str(tmp_path)])

    assert code == 0
    assert "clean" in capsys.readouterr().out.lower()


def test_cli_validate_flags_returns_one(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(tmp_path, f'sections:\n  - call: body\n    text: "bad {EM_DASH} dash"\n')

    code = main(["validate", str(tmp_path)])

    assert code == 1
    assert "em-dash" in capsys.readouterr().out.lower()


def test_cli_validate_strict_flags_en_dash(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(tmp_path, f'sections:\n  - call: body\n    text: "range 1{EN_DASH}2"\n')

    assert main(["validate", str(tmp_path)]) == 0
    assert main(["validate", str(tmp_path), "--strict"]) == 1


def test_cli_validate_missing_content_returns_one(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["validate", str(tmp_path)])

    assert code == 1
    assert "content.yaml not found" in capsys.readouterr().err


def test_cli_validate_also_flag(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(tmp_path, 'sections:\n  - call: body\n    text: "clean"\n')
    extra = tmp_path / "notes.md"
    extra.write_text(f"note {EM_DASH} here", encoding="utf-8")

    code = main(["validate", str(tmp_path), "--also", str(extra)])

    assert code == 1
    assert "notes.md" in capsys.readouterr().out


def test_cli_validate_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["validate", "--help"])
