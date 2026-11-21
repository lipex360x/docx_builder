from __future__ import annotations

import subprocess
import sys
import zipfile
from importlib.resources import as_file, files
from pathlib import Path

from lxml import etree


class InspectionError(Exception):
    pass


def _saved_comments(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as document:
            if "word/comments.xml" not in document.namelist():
                return "Saved comments: 0"
            root = etree.fromstring(
                document.read("word/comments.xml"), etree.XMLParser(resolve_entities=False, no_network=True)
            )
    except (OSError, zipfile.BadZipFile, etree.XMLSyntaxError) as error:
        raise InspectionError(f"Could not read saved Word comments: {error}") from error
    namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    comments = root.findall("w:comment", namespaces)
    lines = [f"Saved comments: {len(comments)}"]
    for comment in comments:
        author = comment.get(f"{{{namespaces['w']}}}author", "")
        paragraphs = []
        for paragraph in comment.findall(".//w:p", namespaces):
            pieces = []
            for node in paragraph.iter():
                if node.tag == f"{{{namespaces['w']}}}t":
                    pieces.append(node.text or "")
                elif node.tag in {f"{{{namespaces['w']}}}br", f"{{{namespaces['w']}}}cr"}:
                    pieces.append("\n")
                elif node.tag == f"{{{namespaces['w']}}}tab":
                    pieces.append("\t")
            paragraphs.append("".join(pieces))
        comment_text = "\n".join(paragraphs)
        lines.extend((f"Author: {author}", f"Comment: {comment_text}"))
    return "\n".join(lines)


def inspect_word(path: Path) -> str:
    if sys.platform != "darwin":
        raise InspectionError("Word inspection requires macOS and Microsoft Word")
    target = path.expanduser().resolve()
    if not target.is_file():
        raise InspectionError(f"Document not found: {target}")
    script = files("docx_builder.scripts").joinpath("inspect_word.applescript")
    try:
        with as_file(script) as script_path:
            result = subprocess.run(
                ["/usr/bin/osascript", str(script_path), str(target), target.name],
                capture_output=True,
                text=True,
                check=True,
            )
    except (OSError, subprocess.CalledProcessError) as error:
        details = getattr(error, "stderr", "") or str(error)
        raise InspectionError(f"Could not inspect Microsoft Word: {details.strip()}") from error
    output = result.stdout.strip()
    if output == "NOT_OPEN":
        return f"Not open in Microsoft Word: {target}\n{_saved_comments(target)}"
    if not output.startswith("Status:"):
        raise InspectionError("Word returned an unexpected inspection result")
    return f"Open document: {target}\n{output}"
