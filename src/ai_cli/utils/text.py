import re

import pyperclip
from rich.console import Console


def strip_rich_formatting(text: str) -> str:
    """Strip Rich markup and formatting from text to get plain text."""
    # Bypass Rich markdown rendering entirely to avoid ANSI corruption
    # Go directly to comprehensive pattern-based stripping
    plain_text = _strip_basic_formatting(text)

    # Clean up any remaining artifacts
    plain_text = _clean_text(plain_text)

    return plain_text


def copy_to_clipboard(text: str, console: Console) -> bool:
    """Copy text to clipboard and show confirmation message."""
    try:
        # Strip Rich formatting before copying
        plain_text = strip_rich_formatting(text)

        # Copy to clipboard
        pyperclip.copy(plain_text)

        # Show confirmation
        char_count = len(plain_text)
        console.print(
            f"[green]✓ Response copied to clipboard ({char_count} characters)[/green]"
        )
        return True

    except Exception:
        # Handle cases where clipboard is not available (headless systems, etc.)
        console.print("[yellow]⚠️ Clipboard not available, printing to stdout:[/yellow]")
        console.print(text)
        return False


def _strip_basic_formatting(text: str) -> str:
    """Strip basic Rich/ANSI formatting codes."""
    # FIRST: Remove proper ANSI escape sequences (with \x1B)
    ansi_escape_patterns = [
        r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])",
        r"\x1B\[[0-9;]*[mGKH]",
        r"\x1B\[[\d;]*m",
        r"\x1b\[[0-9;]*[a-zA-Z]",  # Any remaining escape-like sequences
    ]

    for pattern in ansi_escape_patterns:
        text = re.sub(pattern, "", text)

    # SECOND: Process specific user-reported malformed cases (with content extraction)

    # Handle the <0x1b>[1m...<0x1b>0m pattern
    text = re.sub(r"<0x1b>\[1m(.*?)<0x1b>0m", r"\1", text)

    # Handle all [Xm...[0m and [X;Ym...[0m patterns (only when no \x1B prefix)
    text = re.sub(r"(?<!\x1B)\[\d+(?:;\d+)*m(.*?)\[0m", r"\1", text)

    # Handle the mWashington, D.C.0m pattern
    text = re.sub(r"m([^m]*?)0m", r"\1", text)

    # Handle **bold** markdown
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)

    # THIRD: Remove any remaining malformed ANSI-like sequences
    malformed_patterns = [
        r"\[1;33m",  # Exact match for [1;33m
        r"\[1m",  # Exact match for [1m
        r"\[0m",  # Exact match for [0m
        r"\[\d+;\d+m",  # General [1;33m pattern
        r"\[\d+m",  # General [0m, [1m, [33m etc.
        # Hex representations of escape sequences
        r"<ox1b>\[[0-9;]*m",
        r"<0x1b>\[[0-9;]*m",
        r"<ox1b>",  # Remove standalone <ox1b>
        r"<0x1b>",  # Remove standalone <0x1b>
    ]

    for pattern in malformed_patterns:
        text = re.sub(pattern, "", text)

    # FOURTH: Remove Rich markup patterns
    rich_patterns = [
        r"\[/?[a-zA-Z0-9_#\s]*\]",  # Rich markup like [bold], [red], etc.
        r"\[/?[a-zA-Z0-9_#\s=]*\]",  # Rich markup with attributes
    ]

    for pattern in rich_patterns:
        text = re.sub(pattern, "", text)

    return text


def _clean_text(text: str) -> str:
    """Clean up text artifacts and normalize whitespace."""
    # Remove excessive whitespace
    text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)  # Max 2 consecutive newlines
    text = re.sub(r"[ \t]+", " ", text)  # Normalize spaces and tabs

    # Strip leading/trailing whitespace
    text = text.strip()

    return text
