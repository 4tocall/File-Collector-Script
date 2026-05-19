"""Command-line interface."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from . import __version__
from .config import CollectorConfig


class Format(str, Enum):
    """Typer renders this as a `--format [md|txt|xml|json]` choice automatically."""
    md = "md"
    txt = "txt"
    xml = "xml"
    json = "json"
from .discovery import FileEntry, discover_extensions, walk
from .formatters import default_extension, render
from .platform_utils import ClipboardError, copy_to_clipboard, open_with_default_app
from .tokens import count_tokens

app = typer.Typer(
    name="collect",
    help="Collect and bundle source files for LLM context, sharing, or archiving.",
    no_args_is_help=False,
    rich_markup_mode="rich",
    add_completion=False,
)
console = Console(stderr=False)
err_console = Console(stderr=True)


def _format_size(size: int) -> str:
    """Human-readable file size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _print_table(entries: list[FileEntry]) -> None:
    """Pretty-print the discovered files as a Rich table."""
    table = Table(show_header=True, header_style="bold cyan", border_style="dim")
    table.add_column("#", style="dim", justify="right", width=4)
    table.add_column("Path")
    table.add_column("Size", justify="right", style="green")
    for i, entry in enumerate(entries):
        table.add_row(str(i), entry.rel_path.as_posix(), _format_size(entry.size))
    console.print(table)


def _parse_indices(raw: str, total: int) -> list[int] | None:
    """
    Parse selection strings like "0 3 5", "0-4", "0,2,5-7". Returns None on
    any malformed token so the caller can re-prompt.
    """
    if not raw.strip():
        return list(range(total))
    out: set[int] = set()
    for token in raw.replace(",", " ").split():
        if "-" in token:
            try:
                a, b = (int(x) for x in token.split("-", 1))
            except ValueError:
                return None
            if a > b or a < 0 or b >= total:
                return None
            out.update(range(a, b + 1))
        else:
            try:
                i = int(token)
            except ValueError:
                return None
            if not 0 <= i < total:
                return None
            out.add(i)
    return sorted(out)


def _prompt_extensions(root: Path) -> set[str]:
    """Interactively prompt the user to pick extensions, showing what's present."""
    survey = CollectorConfig(root=root)
    available = discover_extensions(survey)
    if not available:
        console.print("[red]No files found in this directory.[/red]")
        raise typer.Exit(code=1)

    table = Table(title="Available extensions", header_style="bold cyan")
    table.add_column("Extension")
    table.add_column("Count", justify="right", style="green")
    for ext, count in available.items():
        table.add_row(ext, str(count))
    console.print(table)

    raw = Prompt.ask(
        "[bold]Extensions to collect[/bold] (space-separated, or [italic]all[/italic])",
        default="all",
    )
    if raw.strip().lower() == "all":
        return {ext for ext in available if ext != "(no ext)"}
    return {e.strip().lstrip(".") for e in raw.split() if e.strip()}


def _resolve_output_path(
    user_supplied: Path | None, fmt: str, root: Path
) -> Path:
    """Decide the output file path, picking a sensible default and extension."""
    if user_supplied is not None:
        # Honor explicit name but ensure extension matches format.
        ext = default_extension(fmt)
        if user_supplied.suffix.lower() != ext:
            user_supplied = user_supplied.with_suffix(ext)
        return user_supplied
    return root / f"collected{default_extension(fmt)}"


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"file-collector [bold cyan]{__version__}[/bold cyan]")
        raise typer.Exit()


@app.command()
def main(
    extensions: Annotated[
        list[str] | None,
        typer.Argument(
            help="Extensions to collect (e.g. [cyan]py ts md[/cyan]). "
            "Omit to be prompted interactively.",
            show_default=False,
        ),
    ] = None,
    root: Annotated[
        Path,
        typer.Option(
            "--root", "-r",
            help="Directory to scan.",
            file_okay=False, dir_okay=True, exists=True, resolve_path=True,
        ),
    ] = Path.cwd(),
    all_files: Annotated[
        bool,
        typer.Option("--all", "-a", help="Select every matching file without prompting."),
    ] = False,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output file path. Defaults to ./collected.<ext>."),
    ] = None,
    fmt: Annotated[
        Format,
        typer.Option(
            "--format", "-f",
            help="Output format: md, txt, xml, json.",
        ),
    ] = Format.md,
    clipboard: Annotated[
        bool,
        typer.Option("--copy", "-c", help="Copy result to clipboard instead of writing a file."),
    ] = False,
    open_after: Annotated[
        bool,
        typer.Option("--open", help="Open the output file with the default app after writing."),
    ] = False,
    exclude: Annotated[
        list[str] | None,
        typer.Option(
            "--exclude", "-x",
            help="Glob patterns to exclude (repeatable). Example: [cyan]-x 'tests/**' -x '*.snap'[/cyan].",
        ),
    ] = None,
    include: Annotated[
        list[str] | None,
        typer.Option(
            "--include", "-i",
            help="Glob patterns to require (repeatable). Files must match at least one.",
        ),
    ] = None,
    max_size: Annotated[
        int,
        typer.Option(
            "--max-size",
            help="Skip files larger than this (bytes). Default 1 MB.",
        ),
    ] = 1_000_000,
    no_gitignore: Annotated[
        bool,
        typer.Option("--no-gitignore", help="Do not respect .gitignore rules."),
    ] = False,
    no_tree: Annotated[
        bool,
        typer.Option("--no-tree", help="Skip the file tree header in text/markdown output."),
    ] = False,
    count_tokens_flag: Annotated[
        bool,
        typer.Option("--tokens", help="Estimate token count (uses tiktoken if installed)."),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress non-essential output."),
    ] = False,
    version: Annotated[
        bool,
        typer.Option(
            "--version", "-v", callback=_version_callback, is_eager=True,
            help="Print version and exit.",
        ),
    ] = False,
) -> None:
    """
    [bold]collect[/bold] walks the current directory, finds source files matching
    the given extensions, and bundles them into a single output (file or clipboard).

    [bold]Examples[/bold]

      • [cyan]collect py ts -a -c[/cyan]          Copy all .py and .ts files to clipboard as Markdown
      • [cyan]collect -a -f xml -o ctx.xml[/cyan]  Bundle everything (gitignored excluded) into XML
      • [cyan]collect py -x 'tests/**'[/cyan]      All .py files except those under tests/
      • [cyan]collect --tokens -a -c[/cyan]        Copy everything and report token count
    """
    # Build config.
    exts: set[str] = {e.lstrip(".").lower() for e in (extensions or [])}
    if not exts and not all_files:
        exts = _prompt_extensions(root)
    if not exts and all_files:
        # --all without extensions means "every text file we can find".
        exts = set()

    config = CollectorConfig(
        root=root,
        extensions=exts,
        exclude_globs=list(exclude or []),
        include_globs=list(include or []),
        respect_gitignore=not no_gitignore,
        max_file_size=max_size,
        output_format=fmt.value,
        output_path=output,
        copy_to_clipboard=clipboard,
        open_after=open_after,
        extract_all=all_files,
        show_tree=not no_tree,
        count_tokens=count_tokens_flag,
    )

    # Discover.
    entries: list[FileEntry] = list(walk(config))
    if not entries:
        err_console.print("[red]No matching files found.[/red]")
        raise typer.Exit(code=1)

    # Show what we found.
    if not quiet:
        _print_table(entries)

    # Selection: --all skips the prompt entirely.
    if all_files or len(entries) == 1:
        selected = entries
    else:
        while True:
            raw = Prompt.ask(
                "[bold]Files to include[/bold] (e.g. '0 3 5', '0-4', '0,2,5-7'; blank = all)",
                default="",
            )
            indices = _parse_indices(raw, len(entries))
            if indices is not None:
                selected = [entries[i] for i in indices]
                break
            err_console.print("[red]Invalid selection. Try again.[/red]")

    if not selected:
        err_console.print("[yellow]Nothing selected.[/yellow]")
        raise typer.Exit(code=0)

    # Render.
    output_text = render(selected, fmt.value, include_tree=not no_tree)

    # Emit.
    if clipboard:
        try:
            copy_to_clipboard(output_text)
        except ClipboardError as e:
            err_console.print(f"[red]Clipboard error:[/red] {e}")
            raise typer.Exit(code=2) from e
        if not quiet:
            console.print(
                f"[green]✓[/green] Copied [bold]{len(selected)}[/bold] file(s) "
                f"to clipboard ({_format_size(len(output_text.encode('utf-8')))})"
            )
    else:
        out_path = _resolve_output_path(output, fmt.value, root)
        out_path.write_text(output_text, encoding="utf-8")
        if not quiet:
            console.print(
                f"[green]✓[/green] Wrote [bold]{len(selected)}[/bold] file(s) to "
                f"[cyan]{out_path}[/cyan] ({_format_size(out_path.stat().st_size)})"
            )
        if open_after:
            open_with_default_app(out_path)

    # Token report.
    if count_tokens_flag and not quiet:
        n_tokens, method = count_tokens(output_text)
        console.print(f"[dim]≈ {n_tokens:,} tokens ({method})[/dim]")


if __name__ == "__main__":
    app()
