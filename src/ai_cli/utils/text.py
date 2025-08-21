import re

import pyperclip
from rich.console import Console
from rich.markdown import Markdown


def strip_rich_formatting(text: str) -> str:
    """Strip Rich markup and formatting from text to get plain text."""
    # Create a temporary console to render the text
    console = Console(file=None, width=80)

    # If the text looks like markdown, render it and extract plain text
    if _looks_like_markdown(text):
        try:
            # Render markdown to plain text
            markdown = Markdown(text)
            with console.capture() as capture:
                console.print(markdown, markup=False, highlight=False)
            # Get the plain text output
            plain_text = str(capture.get())
        except Exception:
            # If markdown rendering fails, fall back to basic stripping
            plain_text = _strip_basic_formatting(text)
    else:
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


def _looks_like_markdown(text: str) -> bool:
    """Check if text contains markdown formatting."""
    markdown_patterns = [
        r"#{1,6}\s",  # Headers
        r"\*\*.*?\*\*",  # Bold
        r"\*.*?\*",  # Italic
        r"`.*?`",  # Inline code
        r"```",  # Code blocks
        r"^\s*[-*+]\s",  # Lists
        r"^\s*\d+\.\s",  # Numbered lists
    ]

    for pattern in markdown_patterns:
        if re.search(pattern, text, re.MULTILINE):
            return True

    return False


def _strip_basic_formatting(text: str) -> str:
    """Strip basic Rich/ANSI formatting codes."""
    # Remove ANSI escape codes
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    text = ansi_escape.sub("", text)

    # Remove Rich markup patterns
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
