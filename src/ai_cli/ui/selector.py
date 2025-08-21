from typing import Optional

import questionary
from rich.console import Console

from ..core.history import ResponseEntry


class ResponseSelector:
    """Interactive selector for choosing responses to copy."""

    def __init__(self, console: Console):
        self.console = console

    def select_response(self, responses: list[ResponseEntry]) -> Optional[str]:
        """Show interactive selection and return the chosen response text."""
        if not responses:
            self.console.print("[yellow]No response history found[/yellow]")
            return None

        # Create choices for questionary
        choices = []
        for i, response in enumerate(responses, 1):
            # Format: "1. Here's a Python function that reverses a str..."
            choice_text = f"{i}. {response.preview}"
            choices.append(choice_text)

        try:
            # Show interactive selection
            selected = questionary.select(
                "Select response to copy:",
                choices=choices,
                instruction="↑↓ Navigate, Enter to copy, Ctrl+C to cancel",
            ).ask()

            if selected is None:  # User cancelled with Ctrl+C
                return None

            # Extract index from selected choice (format: "1. preview...")
            index = int(selected.split(".")[0]) - 1
            return responses[index].response

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            return None
        except (ValueError, IndexError):
            # Handle unexpected format issues
            self.console.print("[red]Error: Invalid selection[/red]")
            return None
