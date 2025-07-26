import asyncio
from typing import List, Dict, Any, AsyncIterator
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.columns import Columns

from ..config.models import AIConfig
from ..providers.factory import ProviderFactory
from ..ui.streaming import StreamingDisplay
from .messages import ChatMessage


class ChatEngine:
    """Core chat engine that handles single and round-table discussions."""
    
    def __init__(self, config: AIConfig, console: Console):
        self.config = config
        self.console = console
        self.provider_factory = ProviderFactory(config)
        self.streaming_display = StreamingDisplay(console)
    
    async def single_chat(self, prompt: str, model_name: str):
        """Handle a single model chat."""
        try:
            # Get provider for the model
            provider = self.provider_factory.get_provider(model_name)
            model_config = self.config.get_model_config(model_name)
            
            # Create chat messages
            messages = [ChatMessage("user", prompt)]
            
            # Display model info
            self.console.print(f"\n[bold blue]🤖 {model_name}[/bold blue] ({model_config.provider})\n")
            
            # Stream the response
            response = ""
            async for chunk in provider.chat_stream(messages):
                response += chunk
                await self.streaming_display.update_response(response, model_name)
            
            await self.streaming_display.finalize_response()
            
        except Exception as e:
            self.console.print(f"[red]❌ Error with {model_name}: {str(e)}[/red]")
            raise
    
    async def roundtable_chat(self, prompt: str, parallel: bool = False):
        """Handle a round-table discussion between multiple models."""
        enabled_models = self.config.roundtable.enabled_models
        
        if len(enabled_models) < 2:
            self.console.print("[yellow]⚠️  Need at least 2 models enabled for round-table. Use 'ai config roundtable --add <model>' to add models.[/yellow]")
            return
        
        self.console.print(f"\n[bold magenta]🎯 Round-Table Discussion[/bold magenta]")
        self.console.print(f"[dim]Models: {', '.join(enabled_models)}[/dim]")
        self.console.print(f"[dim]Mode: {'Parallel' if parallel else 'Sequential'}[/dim]\n")
        
        # Display the prompt
        self.console.print(Panel(
            Markdown(prompt),
            title="💭 Discussion Topic",
            border_style="cyan"
        ))
        
        conversation_history = [ChatMessage("user", prompt)]
        
        try:
            for round_num in range(self.config.roundtable.discussion_rounds):
                self.console.print(f"\n[bold yellow]📍 Round {round_num + 1}[/bold yellow]\n")
                
                if parallel:
                    responses = await self._run_parallel_round(
                        conversation_history, enabled_models
                    )
                else:
                    responses = await self._run_sequential_round(
                        conversation_history, enabled_models
                    )
                
                # Add responses to conversation history for next round
                for model, response in responses.items():
                    conversation_history.append(
                        ChatMessage("assistant", response, {"model": model})
                    )
                
                # Show a separator between rounds
                if round_num < self.config.roundtable.discussion_rounds - 1:
                    self.console.print("\n" + "─" * 80 + "\n")
        
        except Exception as e:
            self.console.print(f"[red]❌ Round-table error: {str(e)}[/red]")
            raise
    
    async def _run_parallel_round(
        self, 
        conversation_history: List[ChatMessage], 
        models: List[str]
    ) -> Dict[str, str]:
        """Run a round with all models responding in parallel."""
        tasks = []
        
        for model in models:
            task = asyncio.create_task(
                self._get_model_response(model, conversation_history)
            )
            tasks.append((model, task))
        
        responses = {}
        
        # Use progress indicator for parallel execution
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            task_id = progress.add_task("Getting responses from all models...", total=None)
            
            for model, task in tasks:
                try:
                    response = await asyncio.wait_for(
                        task, 
                        timeout=self.config.roundtable.timeout_seconds
                    )
                    responses[model] = response
                except asyncio.TimeoutError:
                    responses[model] = f"⚠️ {model} timed out"
                except Exception as e:
                    responses[model] = f"❌ {model} error: {str(e)}"
        
        # Display all responses side by side
        self._display_parallel_responses(responses)
        
        return responses
    
    async def _run_sequential_round(
        self, 
        conversation_history: List[ChatMessage], 
        models: List[str]
    ) -> Dict[str, str]:
        """Run a round with models responding sequentially."""
        responses = {}
        
        for i, model in enumerate(models):
            # For critique mode, add previous responses to context
            if i > 0 and self.config.roundtable.critique_mode:
                # Add previous model responses to the conversation
                current_history = conversation_history.copy()
                for prev_model, prev_response in list(responses.items()):
                    current_history.append(
                        ChatMessage("assistant", prev_response, {"model": prev_model})
                    )
            else:
                current_history = conversation_history
            
            try:
                response = await self._get_model_response(model, current_history)
                responses[model] = response
                
                # Display this model's response immediately
                self._display_single_response(model, response)
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                responses[model] = error_msg
                self._display_single_response(model, error_msg)
        
        return responses
    
    async def _get_model_response(
        self, 
        model_name: str, 
        messages: List[ChatMessage]
    ) -> str:
        """Get a response from a specific model."""
        provider = self.provider_factory.get_provider(model_name)
        
        response = ""
        async for chunk in provider.chat_stream(messages):
            response += chunk
        
        return response.strip()
    
    def _display_parallel_responses(self, responses: Dict[str, str]):
        """Display multiple responses side by side."""
        colors = ["blue", "green", "magenta", "cyan", "yellow", "red"]
        panels = []
        
        for i, (model, response) in enumerate(responses.items()):
            color = colors[i % len(colors)]
            panel = Panel(
                Markdown(response),
                title=f"🤖 {model}",
                border_style=color
            )
            panels.append(panel)
        
        # Show panels in columns
        self.console.print(Columns(panels, equal=True))
    
    def _display_single_response(self, model_name: str, response: str):
        """Display a single model response."""
        model_config = self.config.get_model_config(model_name)
        
        self.console.print(Panel(
            Markdown(response),
            title=f"🤖 {model_name} ({model_config.provider})",
            border_style="blue"
        ))
        self.console.print()  # Add spacing