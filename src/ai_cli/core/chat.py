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
        """Handle a round-table discussion between multiple models."""
        enabled_models = self.config.roundtable.enabled_models

        if len(enabled_models) < 2:
            self.console.print(
                "[yellow]⚠️  Need at least 2 models enabled for round-table. Use 'ai config roundtable --add <model>' to add models.[/yellow]"
            )
            return

        # Initialize role assigner for this roundtable session
        self.role_assigner = RoleAssigner(
            enabled_models=enabled_models,
            role_assignments=self.config.roundtable.role_assignments,
            role_rotation=self.config.roundtable.role_rotation,
        )

        mode_text = "Parallel" if parallel else "Sequential"
        if self.config.roundtable.use_role_based_prompting:
            mode_text += " (Role-Based)"

        self.console.print("\n[bold magenta]🎯 Round-Table Discussion[/bold magenta]")
        self.console.print(f"[dim]Models: {', '.join(enabled_models)}[/dim]")
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
                        conversation_history, enabled_models, round_num + 1
                    )
                else:
                    responses = await self._run_sequential_round(
                        conversation_history, enabled_models, round_num + 1
                    )

                # Add responses to conversation history for next round
                for model, response in responses.items():
                    message = ChatMessage("assistant", response, {"model": model})

                    # Add role information if using role-based prompting
                    if (
                        self.config.roundtable.use_role_based_prompting
                        and self.role_assigner
                    ):
                        role = self.role_assigner.get_role_for_model_in_round(
                            model, round_num + 1
                        )
                        if role:
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
        models: list[str],
        round_num: int = 1,
    ) -> dict[str, str]:
        """Run a round with all models responding in parallel with streaming."""
        # Create multi-stream display for concurrent streaming
        multi_display = MultiStreamDisplay(self.console)

        # Initialize empty responses for all models in the display
        for model in models:
            await multi_display.update_model_response(model, "")

        tasks = []
        for model in models:
            task = asyncio.create_task(
                self._get_model_response(
                    model, conversation_history, multi_stream_display=multi_display
                )
            )
            tasks.append((model, task))

        responses: dict[str, str] = {}

        # Wait for all tasks to complete
        for model, task in tasks:
            try:
                response = await asyncio.wait_for(
                    task, timeout=self.config.roundtable.timeout_seconds
                )
                responses[model] = response
            except asyncio.TimeoutError:
                responses[model] = f"⚠️ {model} timed out"
                await multi_display.update_model_response(model, responses[model])
            except Exception as e:
                responses[model] = f"❌ {model} error: {str(e)}"
                await multi_display.update_model_response(model, responses[model])

        # Finalize the multi-stream display
        await multi_display.finalize_all_responses()

        return responses

    async def _run_sequential_round(
        self,
        conversation_history: list[ChatMessage],
        models: list[str],
        round_num: int = 1,
    ) -> dict[str, str]:
        """Run a round with models responding sequentially."""
        responses: dict[str, str] = {}

        # Get role assignments for this round if using role-based prompting
        role_assignments: dict[str, RoundtableRole] = {}
        if self.config.roundtable.use_role_based_prompting and self.role_assigner:
            role_assignments = self.role_assigner.assign_roles_for_round(
                round_num, self.config.roundtable.discussion_rounds
            )

        for model in models:
            try:
                # Determine what messages to send to this model
                if (
                    self.config.roundtable.use_role_based_prompting
                    and model in role_assignments
                ):
                    # Use role-based prompting
                    role = role_assignments[model]

                    # Build enhanced conversation history that includes current round responses
                    # This is needed for example the CRITIC role to see previous responses within the same round
                    # from the generator role
                    enhanced_history = conversation_history[
                        1:
                    ].copy()  # Previous rounds (exclude original user prompt)

                    # Add responses from models that have already responded in this round
                    for prev_model, prev_response in responses.items():
                        response_message = ChatMessage(
                            "assistant", prev_response, {"model": prev_model}
                        )
                        # Add role information if available
                        prev_role = role_assignments.get(prev_model)
                        if prev_role:
                            response_message.set_roundtable_role(prev_role, prev_model)
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
                    current_messages = [ChatMessage("user", role_prompt)]

                    # Display role assignment
                    self.console.print(
                        f"[dim]🎭 {model} playing role: {role.value.title()}[/dim]"
                    )

                else:
                    # Fall back to basic conversation history (non-role-based mode)
                    current_messages = conversation_history

                # Create streaming display for this model
                model_config = self.config.get_model_config(model)
                role_info = ""
                if model in role_assignments:
                    role_info = f" ({role_assignments[model].value.title()})"

                # Display model info before streaming starts
                title = f"🤖 {model} ({model_config.provider}){role_info}"
                self.console.print(f"\n[bold blue]{title}[/bold blue]\n")

                # Create a new streaming display for this model
                streaming_display = StreamingDisplay(self.console)

                response = await self._get_model_response(
                    model, current_messages, streaming_display=streaming_display
                )
                responses[model] = response

            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                responses[model] = error_msg
                self._display_single_response(model, error_msg)

        return responses

    async def _get_model_response(
        self,
        model_name: str,
        messages: list[ChatMessage],
        streaming_display: Optional[StreamingDisplay] = None,
        multi_stream_display: Optional[MultiStreamDisplay] = None,
    ) -> str:
        """Get a response from a specific model, optionally with streaming display."""
        provider = self.provider_factory.get_provider(model_name)

        response = ""
        async for chunk in provider.chat_stream(messages):
            response += chunk

            # Update streaming display if provided
            if streaming_display:
                await streaming_display.update_response(response, model_name)
            elif multi_stream_display:
                await multi_stream_display.update_model_response(model_name, response)

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
