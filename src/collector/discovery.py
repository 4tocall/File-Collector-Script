"""File discovery: walking the tree, applying ignores, detecting binaries."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import pathspec

from .config import DEFAULT_IGNORED_DIRS, DEFAULT_IGNORED_GLOBS, CollectorConfig


@dataclass(frozen=True, slots=True)
class FileEntry:
    """A single discovered file with cached metadata."""
    path: Path
    rel_path: Path
    size: int

    @property
    def display(self) -> str:
        return str(self.rel_path)


def _load_gitignore(root: Path) -> pathspec.PathSpec | None:
    """Load .gitignore from root if present. Returns None if absent or unreadable."""
    gitignore = root / ".gitignore"
    if not gitignore.is_file():
        return None
    try:
        lines = gitignore.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    return pathspec.PathSpec.from_lines("gitwildmatch", lines)


def _make_spec(patterns: list[str] | tuple[str, ...]) -> pathspec.PathSpec | None:
    """Build a gitignore-style PathSpec from a list of patterns, or None if empty."""
    if not patterns:
        return None
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)


def _matches_name_glob(name: str, patterns: tuple[str, ...] | list[str]) -> bool:
    """Simple filename-only matching for the built-in DEFAULT_IGNORED_GLOBS."""
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def _looks_binary(path: Path, sniff_bytes: int = 8192) -> bool:
    """
    Heuristic: a file is treated as binary if its first chunk contains a NUL byte
    or fails to decode as UTF-8. Fast and good enough for source-tree scanning.
    """
    try:
        with path.open("rb") as f:
            chunk = f.read(sniff_bytes)
    except OSError:
        return True
    if b"\x00" in chunk:
        return True
    try:
        chunk.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


def walk(config: CollectorConfig) -> Iterator[FileEntry]:
    """
    Yield FileEntry objects matching the config, in deterministic (sorted) order.

    Ordering: each directory's entries are sorted alphabetically, directories
    first then files. Makes output reproducible across runs and filesystems.
    """
    root = config.root.resolve()
    gitignore = _load_gitignore(root) if config.respect_gitignore else None
    exclude_spec = _make_spec(config.exclude_globs)
    include_spec = _make_spec(config.include_globs)
    extensions = {e.lstrip(".").lower() for e in config.extensions}

    def _should_visit_dir(d: Path, rel: Path) -> bool:
        if d.name in DEFAULT_IGNORED_DIRS:
            return False
        if _matches_name_glob(d.name, DEFAULT_IGNORED_GLOBS):
            return False
        rel_posix = rel.as_posix()
        if exclude_spec is not None and exclude_spec.match_file(f"{rel_posix}/"):
            return False
        if gitignore is not None and gitignore.match_file(f"{rel_posix}/"):
            return False
        return True

    def _should_yield_file(f: Path, rel: Path) -> bool:
        if _matches_name_glob(f.name, DEFAULT_IGNORED_GLOBS):
            return False
        rel_posix = rel.as_posix()
        if exclude_spec is not None and exclude_spec.match_file(rel_posix):
            return False
        if gitignore is not None and gitignore.match_file(rel_posix):
            return False
        if extensions:
            ext = f.suffix.lstrip(".").lower()
            if ext not in extensions and f.name not in extensions:
                return False
        if include_spec is not None and not include_spec.match_file(rel_posix):
            return False
        return True

    def _recurse(current: Path) -> Iterator[FileEntry]:
        try:
            entries = sorted(
                current.iterdir(),
                key=lambda p: (p.is_file(), p.name.lower()),
            )
        except (PermissionError, OSError):
            return

        for entry in entries:
            rel = entry.relative_to(root)
            if entry.is_symlink() and not config.follow_symlinks:
                continue
            if entry.is_dir():
                if _should_visit_dir(entry, rel):
                    yield from _recurse(entry)
            elif entry.is_file():
                if not _should_yield_file(entry, rel):
                    continue
                try:
                    size = entry.stat().st_size
                except OSError:
                    continue
                if size > config.max_file_size:
                    continue
                if _looks_binary(entry):
                    continue
                yield FileEntry(path=entry, rel_path=rel, size=size)

    yield from _recurse(root)


def discover_extensions(config: CollectorConfig) -> dict[str, int]:
    """
    Survey the tree to report which extensions are present and how many files
    each has. Useful for the interactive prompt when no extensions are given.
    """
    counts: dict[str, int] = {}
    # Temporarily clear extension filter to see everything.
    survey = CollectorConfig(**{**config.__dict__, "extensions": set()})
    for entry in walk(survey):
        ext = entry.path.suffix.lstrip(".").lower() or "(no ext)"
        counts[ext] = counts.get(ext, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def read_text(path: Path) -> str:
    """Read a file as UTF-8, replacing invalid bytes. Never raises on decode errors."""
    return path.read_text(encoding="utf-8", errors="replace")
