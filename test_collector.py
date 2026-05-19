"""Tests for file discovery and CLI helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from collector.cli import _parse_indices
from collector.config import CollectorConfig, language_for
from collector.discovery import _looks_binary, walk
from collector.formatters import render


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    """Build a small realistic project tree under tmp_path."""
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "src" / "main.py").write_text("def hello(): return 'world'\n")
    (tmp_path / "src" / "utils.ts").write_text("export const x = 1;\n")
    (tmp_path / "tests" / "test_main.py").write_text("def test_x(): pass\n")
    (tmp_path / "README.md").write_text("# Demo\n")
    (tmp_path / ".gitignore").write_text("node_modules/\n*.log\n")
    (tmp_path / "debug.log").write_text("should be ignored\n")
    (tmp_path / "node_modules" / "junk.js").write_text("ignored\n")
    # Real binary file (PNG header with NUL bytes)
    (tmp_path / "src" / "icon.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00")
    return tmp_path


# ---------- Discovery ----------

def test_walk_respects_gitignore(sample_project: Path) -> None:
    cfg = CollectorConfig(root=sample_project)
    paths = {e.rel_path.as_posix() for e in walk(cfg)}
    assert "node_modules/junk.js" not in paths
    assert "debug.log" not in paths


def test_walk_skips_binary(sample_project: Path) -> None:
    cfg = CollectorConfig(root=sample_project)
    paths = {e.rel_path.as_posix() for e in walk(cfg)}
    assert "src/icon.png" not in paths


def test_walk_filters_by_extension(sample_project: Path) -> None:
    cfg = CollectorConfig(root=sample_project, extensions={"py"})
    paths = {e.rel_path.as_posix() for e in walk(cfg)}
    assert paths == {"src/main.py", "tests/test_main.py"}


def test_exclude_glob_with_double_star(sample_project: Path) -> None:
    cfg = CollectorConfig(root=sample_project, exclude_globs=["tests/**"])
    paths = {e.rel_path.as_posix() for e in walk(cfg)}
    assert not any(p.startswith("tests/") for p in paths)


def test_include_glob(sample_project: Path) -> None:
    cfg = CollectorConfig(root=sample_project, include_globs=["src/**"])
    paths = {e.rel_path.as_posix() for e in walk(cfg)}
    assert all(p.startswith("src/") for p in paths)


def test_max_size_filter(sample_project: Path) -> None:
    # Set max size below every file in our fixture
    cfg = CollectorConfig(root=sample_project, max_file_size=5)
    paths = {e.rel_path.as_posix() for e in walk(cfg)}
    assert paths == set()


def test_max_size_keeps_small_files(sample_project: Path) -> None:
    cfg = CollectorConfig(root=sample_project, max_file_size=100)
    paths = {e.rel_path.as_posix() for e in walk(cfg)}
    # README is small; main.py is small; we expect at least these
    assert "README.md" in paths
    assert "src/main.py" in paths


def test_looks_binary_detects_null(tmp_path: Path) -> None:
    binary = tmp_path / "x.bin"
    binary.write_bytes(b"hello\x00world")
    assert _looks_binary(binary)


def test_looks_binary_passes_utf8(tmp_path: Path) -> None:
    text = tmp_path / "x.txt"
    text.write_text("héllo wörld 🎉")
    assert not _looks_binary(text)


# ---------- Formatters ----------

def test_render_markdown_has_language_fence(sample_project: Path) -> None:
    cfg = CollectorConfig(root=sample_project, extensions={"py"})
    entries = list(walk(cfg))
    output = render(entries, "md")
    assert "```python" in output
    assert "## `src/main.py`" in output


def test_render_xml_is_well_formed(sample_project: Path) -> None:
    import xml.etree.ElementTree as ET
    cfg = CollectorConfig(root=sample_project, extensions={"py"})
    entries = list(walk(cfg))
    output = render(entries, "xml")
    # Should parse without errors
    root = ET.fromstring(output)
    assert root.tag == "files"
    assert len(root.findall("file")) == 2


def test_render_json_is_parseable(sample_project: Path) -> None:
    import json as _json
    cfg = CollectorConfig(root=sample_project, extensions={"py"})
    entries = list(walk(cfg))
    output = render(entries, "json")
    data = _json.loads(output)
    assert len(data) == 2
    assert all({"path", "size", "content"} <= set(d) for d in data)


def test_xml_escapes_special_chars(tmp_path: Path) -> None:
    f = tmp_path / "evil.py"
    f.write_text("x = '<script>' & 'a' > 0\n")
    cfg = CollectorConfig(root=tmp_path, extensions={"py"})
    entries = list(walk(cfg))
    output = render(entries, "xml")
    assert "&lt;script&gt;" in output
    assert "&amp;" in output


# ---------- Language detection ----------

def test_language_for_known_extensions() -> None:
    assert language_for(Path("foo.py")) == "python"
    assert language_for(Path("foo.tsx")) == "tsx"
    assert language_for(Path("foo.rs")) == "rust"


def test_language_for_special_filenames() -> None:
    assert language_for(Path("Dockerfile")) == "dockerfile"
    assert language_for(Path("Makefile")) == "makefile"


def test_language_for_unknown_extension() -> None:
    assert language_for(Path("foo.zzzz")) == ""


# ---------- CLI helpers ----------

@pytest.mark.parametrize(
    ("raw", "total", "expected"),
    [
        ("", 5, [0, 1, 2, 3, 4]),
        ("0 2 4", 5, [0, 2, 4]),
        ("0-3", 5, [0, 1, 2, 3]),
        ("0,2,4-6", 7, [0, 2, 4, 5, 6]),
        ("1 3-5 7", 8, [1, 3, 4, 5, 7]),
        ("not a number", 5, None),
        ("99", 5, None),
        ("-1", 5, None),
        ("5-3", 5, None),
    ],
)
def test_parse_indices(raw: str, total: int, expected: list[int] | None) -> None:
    assert _parse_indices(raw, total) == expected
