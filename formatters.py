"""Output formatters: Markdown, plain text, XML, JSON."""

from __future__ import annotations

import json
from collections.abc import Iterable
from io import StringIO

from .config import OutputFormat, language_for
from .discovery import FileEntry, read_text


def _tree(entries: Iterable[FileEntry]) -> str:
    """Render the list of paths as a simple file tree, preserving caller's order."""
    out = StringIO()
    out.write("# Files\n\n")
    for entry in entries:
        out.write(f"- `{entry.rel_path.as_posix()}`\n")
    return out.getvalue()


def _render_markdown(entries: list[FileEntry], include_tree: bool) -> str:
    """Render entries as a Markdown document with fenced code blocks."""
    out = StringIO()
    if include_tree:
        out.write(_tree(entries))
        out.write("\n---\n\n")
    for entry in entries:
        lang = language_for(entry.path)
        out.write(f"## `{entry.rel_path.as_posix()}`\n\n")
        out.write(f"```{lang}\n")
        content = read_text(entry.path)
        out.write(content)
        if not content.endswith("\n"):
            out.write("\n")
        out.write("```\n\n")
    return out.getvalue()


def _render_text(entries: list[FileEntry], include_tree: bool) -> str:
    """Render entries as plain text with simple separators."""
    out = StringIO()
    if include_tree:
        for e in entries:
            out.write(f"// {e.rel_path.as_posix()}\n")
        out.write("\n" + ("=" * 72) + "\n\n")
    for entry in entries:
        sep = "=" * 72
        out.write(f"{sep}\n// {entry.rel_path.as_posix()}\n{sep}\n\n")
        content = read_text(entry.path)
        out.write(content)
        if not content.endswith("\n"):
            out.write("\n")
        out.write("\n")
    return out.getvalue()


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _render_xml(entries: list[FileEntry]) -> str:
    """
    Render entries as XML — the format LLMs like Claude tend to parse most
    cleanly when the prompt mixes multiple files.
    """
    out = StringIO()
    out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    out.write("<files>\n")
    for entry in entries:
        path = _xml_escape(entry.rel_path.as_posix())
        content = read_text(entry.path)
        # CDATA-style is fragile if content contains "]]>"; escape instead.
        out.write(f'  <file path="{path}" size="{entry.size}">\n')
        out.write(_xml_escape(content))
        if not content.endswith("\n"):
            out.write("\n")
        out.write("  </file>\n")
    out.write("</files>\n")
    return out.getvalue()


def _render_json(entries: list[FileEntry]) -> str:
    """Render entries as a JSON array of {path, size, content} objects."""
    payload = [
        {
            "path": entry.rel_path.as_posix(),
            "size": entry.size,
            "content": read_text(entry.path),
        }
        for entry in entries
    ]
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def render(entries: list[FileEntry], fmt: str, include_tree: bool = True) -> str:
    """Dispatch to the right renderer."""
    if fmt == OutputFormat.MARKDOWN:
        return _render_markdown(entries, include_tree)
    if fmt == OutputFormat.TEXT:
        return _render_text(entries, include_tree)
    if fmt == OutputFormat.XML:
        return _render_xml(entries)
    if fmt == OutputFormat.JSON:
        return _render_json(entries)
    raise ValueError(f"Unknown output format: {fmt!r}")


def default_extension(fmt: str) -> str:
    """File extension for a given format, including the leading dot."""
    return {
        OutputFormat.MARKDOWN: ".md",
        OutputFormat.TEXT: ".txt",
        OutputFormat.XML: ".xml",
        OutputFormat.JSON: ".json",
    }[fmt]
