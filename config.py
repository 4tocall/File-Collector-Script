"""Configuration: constants, language mapping, and runtime options."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# Directories we never descend into, regardless of .gitignore.
# These are environment/tooling caches that almost never contain user code.
DEFAULT_IGNORED_DIRS: frozenset[str] = frozenset({
    "__pycache__", ".git", ".hg", ".svn",
    ".idea", ".vscode", ".vs",
    "node_modules", "bower_components",
    "venv", ".venv", "env", ".env",
    "build", "dist", "target", "out",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox",
    ".ipynb_checkpoints", ".serverless", ".history",
    ".eggs",
})

# Glob patterns to ignore (files OR directories). Real glob, not just equality.
DEFAULT_IGNORED_GLOBS: tuple[str, ...] = (
    "*.egg-info",
    ".DS_Store",
    "*.lock",
    "*.min.js",
    "*.min.css",
    "*.map",
)

# Map extensions to fenced-code language hints for Markdown output.
# Missing extensions just render as a plain ``` fence.
LANGUAGE_MAP: dict[str, str] = {
    "py": "python", "pyi": "python",
    "js": "javascript", "mjs": "javascript", "cjs": "javascript",
    "jsx": "jsx", "ts": "typescript", "tsx": "tsx",
    "vue": "vue", "svelte": "svelte",
    "html": "html", "htm": "html",
    "css": "css", "scss": "scss", "sass": "sass", "less": "less",
    "json": "json", "jsonc": "jsonc", "json5": "json5",
    "xml": "xml", "yaml": "yaml", "yml": "yaml", "toml": "toml",
    "ini": "ini", "cfg": "ini", "conf": "ini",
    "md": "markdown", "mdx": "mdx", "rst": "rst",
    "sh": "bash", "bash": "bash", "zsh": "bash", "fish": "fish",
    "ps1": "powershell", "bat": "batch", "cmd": "batch",
    "sql": "sql",
    "java": "java", "kt": "kotlin", "kts": "kotlin",
    "scala": "scala", "groovy": "groovy",
    "c": "c", "h": "c", "cpp": "cpp", "cc": "cpp", "cxx": "cpp", "hpp": "cpp",
    "cs": "csharp", "fs": "fsharp",
    "rs": "rust", "go": "go", "swift": "swift",
    "rb": "ruby", "php": "php", "pl": "perl", "lua": "lua",
    "r": "r", "jl": "julia",
    "dart": "dart", "ex": "elixir", "exs": "elixir", "erl": "erlang",
    "clj": "clojure", "cljs": "clojure",
    "hs": "haskell", "ml": "ocaml", "elm": "elm",
    "tf": "hcl", "hcl": "hcl",
    "dockerfile": "dockerfile",
    "makefile": "makefile", "mk": "makefile",
    "graphql": "graphql", "gql": "graphql",
    "proto": "protobuf",
    "txt": "", "log": "", "env": "",
}

# Files commonly recognized by name (no extension, or unusual name).
FILENAME_LANGUAGE_MAP: dict[str, str] = {
    "Dockerfile": "dockerfile",
    "Makefile": "makefile",
    "GNUmakefile": "makefile",
    "Rakefile": "ruby",
    "Gemfile": "ruby",
    "Procfile": "",
    "Jenkinsfile": "groovy",
    ".gitignore": "gitignore",
    ".dockerignore": "gitignore",
    ".env": "",
    ".editorconfig": "ini",
}


class OutputFormat:
    """Allowed output formats. Plain class instead of Enum for cleaner Typer args."""
    MARKDOWN = "md"
    TEXT = "txt"
    XML = "xml"
    JSON = "json"

    ALL = ("md", "txt", "xml", "json")


@dataclass
class CollectorConfig:
    """Runtime configuration for a single collection run."""

    root: Path = field(default_factory=lambda: Path.cwd())
    extensions: set[str] = field(default_factory=set)
    exclude_globs: list[str] = field(default_factory=list)
    include_globs: list[str] = field(default_factory=list)
    respect_gitignore: bool = True
    max_file_size: int = 1_000_000  # 1 MB
    output_format: str = OutputFormat.MARKDOWN
    output_path: Path | None = None
    copy_to_clipboard: bool = False
    open_after: bool = False
    extract_all: bool = False
    show_tree: bool = True
    count_tokens: bool = False
    follow_symlinks: bool = False


def language_for(path: Path) -> str:
    """Return the Markdown fence language hint for a given file path."""
    name = path.name
    if name in FILENAME_LANGUAGE_MAP:
        return FILENAME_LANGUAGE_MAP[name]
    ext = path.suffix.lstrip(".").lower()
    return LANGUAGE_MAP.get(ext, "")
