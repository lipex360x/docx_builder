from pathlib import Path

import pytest
from docx import Document


@pytest.fixture(scope="session")
def cover_docx(tmp_path_factory: pytest.TempPathFactory) -> Path:
    target_dir = tmp_path_factory.mktemp("cover")
    cover_path = target_dir / "Cover.docx"
    document = Document()
    table = document.add_table(rows=7, cols=2)
    for row in table.rows:
        for cell in row.cells:
            cell.text = ""
    document.save(str(cover_path))
    return cover_path


@pytest.fixture(scope="session")
def cover_dir(cover_docx: Path) -> Path:
    return cover_docx.parent
