import asyncio
from typing import Optional, Union

from rich.columns import Columns
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text


class StreamingDisplay:
    """Handles real-time streaming display of AI responses."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self.current_response = ""
        self.live_display: Optional[Live] = None
        self.model_name = ""

    async def update_response(self, response: str, model_name: str = "") -> None:
        """Update the streaming response display."""
        self.current_response = response
        self.model_name = model_name

        # Create the display content
        content = self._create_display_content()

        # If this is the first update, start the live display
        if self.live_display is None:
            self.live_display = Live(
                content, console=self.console, refresh_per_second=10, transient=False
            )
            self.live_display.start()
        else:
            # Update the existing display
            self.live_display.update(content)

        # Small delay to make streaming visible
        await asyncio.sleep(0.01)

    async def finalize_response(self) -> None:
        """Finalize the streaming display."""
        if self.live_display:
            # Final update
            final_content = self._create_display_content()
            self.live_display.update(final_content)

            # Stop the live display but keep the content
            self.live_display.stop()
            self.live_display = None

            # Print a final newline for spacing
            self.console.print()

    def _create_display_content(self) -> Panel:
        """Create the display content for the current response."""
        if not self.current_response.strip():
            # Show a thinking indicator
            return Panel(
                Text("🤔 Thinking...", style="dim"),
                title=f"🤖 {self.model_name}" if self.model_name else "🤖 AI",
                border_style="blue",
            )

        # Show the current response with markdown formatting
        return Panel(
            Markdown(self.current_response),
            title=f"🤖 {self.model_name}" if self.model_name else "🤖 AI",
            border_style="blue",
        )


class MultiStreamDisplay:
    """Handles streaming display for multiple models simultaneously."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self.model_responses: dict[str, str] = {}
        self.live_display: Optional[Live] = None

    async def update_model_response(self, model_name: str, response: str) -> None:
        """Update the response for a specific model."""
        self.model_responses[model_name] = response

        # Create the display content
        content = self._create_multi_display_content()

        # Start or update the live display
        if self.live_display is None:
            self.live_display = Live(
                content, console=self.console, refresh_per_second=10, transient=False
            )
            self.live_display.start()
        else:
            self.live_display.update(content)

        await asyncio.sleep(0.01)

    async def finalize_all_responses(self) -> None:
        """Finalize all streaming displays."""
        if self.live_display:
            final_content = self._create_multi_display_content()
            self.live_display.update(final_content)
            self.live_display.stop()
            self.live_display = None
            self.console.print()

    def _create_multi_display_content(self) -> Union[Panel, Columns]:
        """Create display content for multiple models."""
        from rich.columns import Columns

        panels = []
        colors = ["blue", "green", "magenta", "cyan", "yellow", "red"]

        for i, (model_name, response) in enumerate(self.model_responses.items()):
            color = colors[i % len(colors)]

            if not response.strip():
                content: Union[Text, Markdown] = Text("🤔 Thinking...", style="dim")
            else:
                content = Markdown(response)

            panel = Panel(content, title=f"🤖 {model_name}", border_style=color)
            panels.append(panel)

        if panels:
            return Columns(panels, equal=True)
        else:
            return Panel(
                Text("Waiting for responses..."), title="Status", border_style="dim"
            )
