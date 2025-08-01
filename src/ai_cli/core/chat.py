import asyncio
from typing import Optional

from rich.columns import Columns
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from ..config.models import AIConfig
from ..providers.factory import ProviderFactory
from ..ui.streaming import MultiStreamDisplay, StreamingDisplay
from .messages import ChatMessage
from .roles import RoleAssigner, RolePromptBuilder, RoundtableRole


class ChatEngine:
    """Core chat engine that handles single and round-table discussions."""

    def __init__(self, config: AIConfig, console: Console) -> None:
        self.config = config
        self.console = console
        self.provider_factory = ProviderFactory(config)
        self.streaming_display = StreamingDisplay(console)

        # Initialize role-based components
        self.role_prompt_builder = RolePromptBuilder(
            custom_templates=config.roundtable.custom_role_templates
        )
        self.role_assigner: Optional[RoleAssigner] = (
            None  # Will be initialized when needed
        )

    async def single_chat(self, prompt: str, model_name: str) -> None:
        """Handle a single model chat."""
        try:
            # Get provider for the model
            provider = self.provider_factory.get_provider(model_name)
            model_config = self.config.get_model_config(model_name)

            # Create chat messages
            messages = [ChatMessage("user", prompt)]

            # Display model info
            self.console.print(
                f"\n[bold blue]🤖 {model_name}[/bold blue] ({model_config.provider})\n"
            )

            # Stream the response
            response = ""
            async for chunk in provider.chat_stream(messages):
                response += chunk
                await self.streaming_display.update_response(response, model_name)

            await self.streaming_display.finalize_response()

        except Exception as e:
            self.console.print(f"[red]❌ Error with {model_name}: {str(e)}[/red]")
            raise

    async def roundtable_chat(self, prompt: str, parallel: bool = False) -> None:
        """Handle a round-table discussion with role-based execution."""
        enabled_roles = self.config.roundtable.get_enabled_roles()

        if len(enabled_roles) == 0:
            self.console.print(
                "[yellow]⚠️  No roles enabled for round-table discussion.[/yellow]"
            )
            return

        # Initialize role assigner for this roundtable session
        self.role_assigner = RoleAssigner(
            roundtable_config=self.config.roundtable,
            default_model=self.config.default_model,
        )

        # Get unique models involved in this roundtable
        role_assignments = self.role_assigner.get_role_assignments_for_round(1)
        unique_models = list(set(role_assignments.values()))

        mode_text = "Parallel" if parallel else "Sequential"
        mode_text += " (Role-Based)"

        self.console.print("\n[bold magenta]🎯 Round-Table Discussion[/bold magenta]")
        self.console.print(
            f"[dim]Roles: {', '.join([role.value.title() for role in enabled_roles])}[/dim]"
        )
        self.console.print(f"[dim]Models: {', '.join(unique_models)}[/dim]")
        self.console.print(f"[dim]Mode: {mode_text}[/dim]\n")

        # Display the prompt
        self.console.print(
            Panel(Markdown(prompt), title="💭 Discussion Topic", border_style="cyan")
        )

        conversation_history = [ChatMessage("user", prompt)]

        try:
            for round_num in range(self.config.roundtable.discussion_rounds):
                self.console.print(
                    f"\n[bold yellow]📍 Round {round_num + 1}[/bold yellow]\n"
                )

                if parallel:
                    responses = await self._run_parallel_round(
                        conversation_history, enabled_roles, round_num + 1
                    )
                else:
                    responses = await self._run_sequential_round(
                        conversation_history, enabled_roles, round_num + 1
                    )

                # Add responses to conversation history for next round
                for role, response in responses.items():
                    # Get the model that played this role
                    model = self.role_assigner.get_model_for_role(role, round_num + 1)
                    message = ChatMessage("assistant", response, {"model": model})
                    message.set_roundtable_role(role, model)
                    conversation_history.append(message)

                # Show a separator between rounds
                if round_num < self.config.roundtable.discussion_rounds - 1:
                    self.console.print("\n" + "─" * 80 + "\n")

        except Exception as e:
            self.console.print(f"[red]❌ Round-table error: {str(e)}[/red]")
            raise

    async def _run_parallel_round(
        self,
        conversation_history: list[ChatMessage],
        enabled_roles: list[RoundtableRole],
        round_num: int = 1,
    ) -> dict[RoundtableRole, str]:
        """Run a round with all roles responding in parallel with streaming."""
        # Get role assignments for this round
        if not self.role_assigner:
            raise RuntimeError("Role assigner not initialized")
        role_assignments = self.role_assigner.get_role_assignments_for_round(round_num)

        # Create multi-stream display for concurrent streaming
        multi_display = MultiStreamDisplay(self.console)

        # Initialize empty responses for all roles in the display
        for role in enabled_roles:
            model = role_assignments[role]
            await multi_display.update_model_response(
                f"{model} ({role.value.title()})", ""
            )

        tasks = []
        for role in enabled_roles:
            model = role_assignments[role]
            # Build role-specific messages
            role_messages = self._build_role_messages(
                role, conversation_history, round_num
            )

            task = asyncio.create_task(
                self._get_model_response(
                    model,
                    role_messages,
                    multi_stream_display=multi_display,
                    display_name=f"{model} ({role.value.title()})",
                )
            )
            tasks.append((role, task))

        responses: dict[RoundtableRole, str] = {}

        # Wait for all tasks to complete
        for role, task in tasks:
            model = role_assignments[role]
            try:
                response = await asyncio.wait_for(
                    task, timeout=self.config.roundtable.timeout_seconds
                )
                responses[role] = response
            except asyncio.TimeoutError:
                responses[role] = f"⚠️ {model} timed out"
                await multi_display.update_model_response(
                    f"{model} ({role.value.title()})", responses[role]
                )
            except Exception as e:
                responses[role] = f"❌ {model} error: {str(e)}"
                await multi_display.update_model_response(
                    f"{model} ({role.value.title()})", responses[role]
                )

        # Finalize the multi-stream display
        await multi_display.finalize_all_responses()

        return responses

    async def _run_sequential_round(
        self,
        conversation_history: list[ChatMessage],
        enabled_roles: list[RoundtableRole],
        round_num: int = 1,
    ) -> dict[RoundtableRole, str]:
        """Run a round with roles responding sequentially in fixed order."""
        responses: dict[RoundtableRole, str] = {}

        # Get role assignments for this round
        if not self.role_assigner:
            raise RuntimeError("Role assigner not initialized")
        role_assignments = self.role_assigner.get_role_assignments_for_round(round_num)

        # Execute roles in fixed order: generator, critic, refiner, evaluator
        for role in enabled_roles:
            try:
                model = role_assignments[role]

                # Build role-specific messages
                current_messages = self._build_role_messages(
                    role, conversation_history, round_num, responses
                )

                # Display role assignment
                self.console.print(
                    f"[dim]🎭 {model} playing role: {role.value.title()}[/dim]"
                )

                # Create streaming display for this model
                model_config = self.config.get_model_config(model)
                title = f"🤖 {model} ({model_config.provider}) - {role.value.title()}"
                self.console.print(f"\n[bold blue]{title}[/bold blue]\n")

                # Create a new streaming display for this model
                streaming_display = StreamingDisplay(self.console)

                response = await self._get_model_response(
                    model, current_messages, streaming_display=streaming_display
                )
                responses[role] = response

            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                responses[role] = error_msg
                model = role_assignments.get(role, "Unknown")
                self._display_single_response(
                    model, error_msg, f" - {role.value.title()}"
                )

        return responses

    def _build_role_messages(
        self,
        role: RoundtableRole,
        conversation_history: list[ChatMessage],
        round_num: int,
        current_round_responses: Optional[dict[RoundtableRole, str]] = None,
    ) -> list[ChatMessage]:
        """Build role-specific messages for a model."""
        if current_round_responses is None:
            current_round_responses = {}

        # Build enhanced conversation history that includes current round responses
        enhanced_history = conversation_history[
            1:
        ].copy()  # Previous rounds (exclude original user prompt)

        # Add responses from roles that have already responded in this round
        for prev_role, prev_response in current_round_responses.items():
            if not self.role_assigner:
                raise RuntimeError("Role assigner not initialized")
            model = self.role_assigner.get_model_for_role(prev_role, round_num)
            response_message = ChatMessage("assistant", prev_response, {"model": model})
            response_message.set_roundtable_role(prev_role, model)
            enhanced_history.append(response_message)

        # Build role-specific prompt with enhanced history
        original_prompt = conversation_history[0].content
        role_prompt = self.role_prompt_builder.build_role_prompt(
            role=role,
            original_prompt=original_prompt,
            conversation_history=enhanced_history,
            current_round=round_num,
            total_rounds=self.config.roundtable.discussion_rounds,
        )

        # Create message list with role-based prompt
        return [ChatMessage("user", role_prompt)]

    async def _get_model_response(
        self,
        model_name: str,
        messages: list[ChatMessage],
        streaming_display: Optional[StreamingDisplay] = None,
        multi_stream_display: Optional[MultiStreamDisplay] = None,
        display_name: Optional[str] = None,
    ) -> str:
        """Get a response from a specific model, optionally with streaming display."""
        provider = self.provider_factory.get_provider(model_name)
        display_key = display_name or model_name

        response = ""
        async for chunk in provider.chat_stream(messages):
            response += chunk

            # Update streaming display if provided
            if streaming_display:
                await streaming_display.update_response(response, model_name)
            elif multi_stream_display:
                await multi_stream_display.update_model_response(display_key, response)

        # Finalize streaming display if provided
        if streaming_display:
            await streaming_display.finalize_response()

        return response.strip()

    def _display_parallel_responses(self, responses: dict[str, str]) -> None:
        """Display multiple responses side by side."""
        colors = ["blue", "green", "magenta", "cyan", "yellow", "red"]
        panels = []

        for i, (model, response) in enumerate(responses.items()):
            color = colors[i % len(colors)]
            panel = Panel(Markdown(response), title=f"🤖 {model}", border_style=color)
            panels.append(panel)

        # Show panels in columns
        self.console.print(Columns(panels, equal=True))

    def _display_single_response(
        self, model_name: str, response: str, role_info: str = ""
    ) -> None:
        """Display a single model response."""
        model_config = self.config.get_model_config(model_name)

        title = f"🤖 {model_name} ({model_config.provider}){role_info}"

        self.console.print(
            Panel(
                Markdown(response),
                title=title,
                border_style="blue",
            )
        )
        self.console.print()  # Add spacing
