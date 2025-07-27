from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import CompleteStyle, confirm
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from ..core.chat import ChatEngine


class InteractiveSession:
    """Interactive chat session with command support."""

    def __init__(self, chat_engine: ChatEngine, console: Console):
        self.chat_engine = chat_engine
        self.console = console
        self.session = self._create_session()
        self.conversation_history: list[tuple[str, str]] = []
        self.current_model = chat_engine.config.default_model

    def _create_session(self) -> PromptSession[str]:
        """Create a prompt session with auto-completion and history."""
        commands = [
            "/help",
            "/exit",
            "/quit",
            "/clear",
            "/history",
            "/model",
            "/models",
            "/roundtable",
            "/config",
        ]

        # Add model names to completion
        model_names = [
            f"/model {name}" for name in self.chat_engine.config.models.keys()
        ]
        commands.extend(model_names)

        completer = WordCompleter(commands, ignore_case=True)

        # Ensure .ai-cli directory exists and create history file path
        ai_cli_dir = Path.home() / ".ai-cli"
        ai_cli_dir.mkdir(exist_ok=True)
        history_file = ai_cli_dir / "history.txt"

        return PromptSession(
            history=FileHistory(str(history_file)),
            completer=completer,
            complete_style=CompleteStyle.COLUMN,
        )

    async def run(self) -> None:
        """Run the interactive session."""
        self.console.print("\n[bold blue]🤖 AI Interactive Session[/bold blue]")
        self.console.print(f"[dim]Current model: {self.current_model}[/dim]")
        self.console.print("[dim]Type '/help' for commands or '/exit' to quit[/dim]\n")

        while True:
            try:
                # Get user input
                user_input = await self.session.prompt_async("🤖 ai> ")

                if not user_input.strip():
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    if await self._handle_command(user_input):
                        break  # Exit if command returns True
                else:
                    # Regular chat
                    await self._handle_chat(user_input)

            except KeyboardInterrupt:
                if confirm("\nExit interactive session?"):
                    break
            except EOFError:
                break

        self.console.print("\n[dim]Goodbye! 👋[/dim]")

    async def _handle_command(self, command: str) -> bool:
        """Handle interactive commands. Returns True if session should exit."""
        parts = command.split()
        cmd = parts[0].lower()

        if cmd in ["/exit", "/quit"]:
            return True

        elif cmd == "/help":
            self._show_help()

        elif cmd == "/clear":
            self.conversation_history.clear()
            self.console.clear()
            self.console.print("[green]✓ Conversation history cleared[/green]")

        elif cmd == "/history":
            self._show_history()

        elif cmd == "/model":
            if len(parts) > 1:
                await self._change_model(parts[1])
            else:
                self._show_current_model()

        elif cmd == "/models":
            self._show_available_models()

        elif cmd == "/roundtable":
            if len(parts) > 1:
                prompt = " ".join(parts[1:])
                await self._handle_roundtable(prompt)
            else:
                self.console.print("[yellow]Usage: /roundtable <prompt>[/yellow]")

        elif cmd == "/config":
            self._show_config_info()

        else:
            self.console.print(f"[red]Unknown command: {cmd}[/red]")
            self.console.print("[dim]Type '/help' for available commands[/dim]")

        return False

    async def _handle_chat(self, prompt: str) -> None:
        """Handle regular chat input."""
        try:
            await self.chat_engine.single_chat(prompt, self.current_model)
            self.conversation_history.append(("user", prompt))
            self.conversation_history.append(("assistant", "Response received"))
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    async def _handle_roundtable(self, prompt: str) -> None:
        """Handle round-table discussion."""
        try:
            await self.chat_engine.roundtable_chat(prompt, parallel=False)
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    async def _change_model(self, model_name: str) -> None:
        """Change the current model."""
        if model_name in self.chat_engine.config.models:
            old_model = self.current_model
            self.current_model = model_name
            self.console.print(
                f"[green]✓ Switched from {old_model} to {model_name}[/green]"
            )
        else:
            self.console.print(f"[red]Model '{model_name}' not found[/red]")
            self._show_available_models()

    def _show_help(self) -> None:
        """Show help information."""
        help_text = """
**Interactive Commands:**

• `/help` - Show this help message
• `/exit` or `/quit` - Exit the interactive session
• `/clear` - Clear conversation history
• `/history` - Show conversation history
• `/model <name>` - Change current model
• `/models` - List available models
• `/roundtable <prompt>` - Start round-table discussion
• `/config` - Show current configuration

**Chat:**
Just type your message and press Enter to chat with the current model.
"""
        self.console.print(
            Panel(Markdown(help_text.strip()), title="📖 Help", border_style="cyan")
        )

    def _show_history(self) -> None:
        """Show conversation history."""
        if not self.conversation_history:
            self.console.print("[dim]No conversation history[/dim]")
            return

        self.console.print("\n[bold blue]📝 Conversation History[/bold blue]\n")
        for role, content in self.conversation_history[-10:]:
            emoji = "👤" if role == "user" else "🤖"
            self.console.print(
                f"{emoji} [{role}] {content[:100]}{'...' if len(content) > 100 else ''}"
            )

    def _show_current_model(self) -> None:
        """Show the current model."""
        model_config = self.chat_engine.config.get_model_config(self.current_model)
        self.console.print(
            f"\n[bold blue]Current Model:[/bold blue] {self.current_model}"
        )
        self.console.print(f"[dim]Provider: {model_config.provider}[/dim]")
        self.console.print(f"[dim]Model: {model_config.model}[/dim]")
        self.console.print(f"[dim]Temperature: {model_config.temperature}[/dim]\n")

    def _show_available_models(self) -> None:
        """Show available models."""
        self.console.print("\n[bold blue]📋 Available Models:[/bold blue]\n")
        for name, config in self.chat_engine.config.models.items():
            provider = config.provider
            model = config.model

            current_indicator = "→ " if name == self.current_model else "  "
            self.console.print(
                f"{current_indicator}[green]{name}[/green] ({provider}: {model})"
            )

        self.console.print("\n[dim]Use '/model <name>' to switch models[/dim]\n")

    def _show_config_info(self) -> None:
        """Show configuration information."""
        config = self.chat_engine.config

        info_text = f"""
**Configuration:**

• **Default Model:** {config.default_model}
• **Round-table Models:** {len(config.roundtable.enabled_models)} configured
• **Discussion Rounds:** {config.roundtable.discussion_rounds}
• **Parallel Mode:** {config.roundtable.parallel_responses}
• **Theme:** {config.ui.theme}
• **Streaming:** {config.ui.streaming}

Use `ai config list` from the command line for detailed configuration.
"""

        self.console.print(
            Panel(
                Markdown(info_text.strip()),
                title="⚙️ Configuration",
                border_style="green",
            )
        )
