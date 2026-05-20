from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.table import Table


def remove_table_borders(table: Table) -> None:
    tbl_xml = table._tbl
    table_properties = tbl_xml.find(qn("w:tblPr"))
    if table_properties is None:
        table_properties = OxmlElement("w:tblPr")
        tbl_xml.insert(0, table_properties)
    table_borders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        border_element = OxmlElement(f"w:{side}")
        border_element.set(qn("w:val"), "none")
        table_borders.append(border_element)
    table_properties.append(table_borders)
