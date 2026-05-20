from docx.document import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt


def build_summary(document: Document, levels: str = "1-2") -> None:
    title_paragraph = document.add_paragraph("TABLE OF CONTENTS")
    title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_paragraph.runs[0].bold = True
    title_paragraph.runs[0].font.size = Pt(14)
    document.add_paragraph()

    toc_paragraph = document.add_paragraph()
    run = toc_paragraph.add_run()

    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    run._r.append(begin)  # noqa: SLF001

    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f' TOC \\o "{levels}" \\h \\z \\u '
    run._r.append(instr)  # noqa: SLF001

    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    run._r.append(separate)  # noqa: SLF001

    placeholder = OxmlElement("w:t")
    placeholder.text = "Right-click here and select 'Update Field' to generate the table of contents."
    run._r.append(placeholder)  # noqa: SLF001

    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(end)  # noqa: SLF001

    note_paragraph = document.add_paragraph()
    note_paragraph.paragraph_format.space_before = Pt(12)
    note_run = note_paragraph.add_run(
        "Note: open in Microsoft Word, right-click the table of contents "
        "and select ‘Update Field’, or press Ctrl+A then F9."
    )
    note_run.italic = True
    note_run.font.size = Pt(8)
