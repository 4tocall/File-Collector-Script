"""Optional token counting via tiktoken, with a graceful fallback."""

from __future__ import annotations


def count_tokens(text: str) -> tuple[int, str]:
    """
    Return (token_count, method). Uses tiktoken's cl100k_base if available,
    otherwise falls back to a chars/4 heuristic which is roughly accurate
    for English/code (overestimates for CJK).
    """
    try:
        import tiktoken
    except ImportError:
        return (len(text) // 4, "heuristic (~chars/4)")
    enc = tiktoken.get_encoding("cl100k_base")
    return (len(enc.encode(text, disallowed_special=())), "tiktoken cl100k_base")
