"""Cross-platform helpers: clipboard and opening files with the default app."""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path


class ClipboardError(RuntimeError):
    """Raised when no clipboard backend is available."""


def copy_to_clipboard(text: str) -> None:
    """
    Copy text to the system clipboard. Tries pyperclip first; on Linux without
    xclip/xsel, raises ClipboardError with an actionable message.
    """
    try:
        import pyperclip
    except ImportError as e:
        raise ClipboardError(
            "pyperclip is not installed. Run: pip install pyperclip"
        ) from e
    try:
        pyperclip.copy(text)
    except pyperclip.PyperclipException as e:
        # Most common on headless Linux: no xclip/xsel/wl-clipboard.
        raise ClipboardError(
            "No clipboard backend found. On Linux install xclip, xsel, or "
            "wl-clipboard (e.g. `sudo apt install xclip`)."
        ) from e


def open_with_default_app(path: Path) -> None:
    """Open a file with the OS default application. Silent no-op on unknown platforms."""
    system = platform.system()
    path_str = str(path)
    if system == "Darwin":
        subprocess.run(["open", path_str], check=False)
    elif system == "Windows":
        # os.startfile is the canonical way on Windows.
        os.startfile(path_str)  # type: ignore[attr-defined]
    elif system == "Linux":
        subprocess.run(["xdg-open", path_str], check=False)
