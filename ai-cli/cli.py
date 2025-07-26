import typer
import asyncio
from typing import Optional, List
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from .config.manager import ConfigManager
from .core.chat import ChatEngine
from .ui.interactive import InteractiveSession
from .utils.env import env_manager

app = typer.Typer(
    name="ai",
    help="Multi-model AI CLI with round-table discussions",
    no_args_is_help=True
)

config_app = typer.Typer(name="config", help="Configuration management")
app.add_typer(config_app, name="config")

console = Console()
config_manager = ConfigManager()


@app.command()
def chat(
    prompt: str = typer.Argument(..., help="The prompt to send to the AI model"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use"),
    roundtable: bool = typer.Option(False, "--roundtable", "-rt", help="Enable round-table discussion"),
    parallel: bool = typer.Option(False, "--parallel", "-p", help="Run round-table in parallel mode"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Start interactive session"),
):
    """Chat with AI models."""
    asyncio.run(_chat_async(prompt, model, roundtable, parallel, interactive))


async def _chat_async(
    prompt: str, 
    model: Optional[str], 
    roundtable: bool, 
    parallel: bool, 
    interactive: bool
):
    """Async chat implementation."""
    try:
        config = config_manager.load_config()
        chat_engine = ChatEngine(config, console)
        
        if interactive:
            session = InteractiveSession(chat_engine, console)
            await session.run()
        elif roundtable:
            await chat_engine.roundtable_chat(prompt, parallel=parallel)
        else:
            selected_model = model or config.default_model
            await chat_engine.single_chat(prompt, selected_model)
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def interactive():
    """Start an interactive chat session."""
    asyncio.run(_interactive_async())


async def _interactive_async():
    """Async interactive session."""
    try:
        config = config_manager.load_config()
        chat_engine = ChatEngine(config, console)
        session = InteractiveSession(chat_engine, console)
        await session.run()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("list")
def config_list():
    """List all configured models."""
    try:
        models = config_manager.list_models()
        config = config_manager.load_config()
        
        console.print("\n[bold blue]📋 Configured Models[/bold blue]\n")
        
        for name, model_config in models.items():
            is_default = "⭐ " if name == config.default_model else "   "
            in_roundtable = "🔄 " if name in config.roundtable.enabled_models else "   "
            
            panel_content = f"""
**Provider:** {model_config.provider}
**Model:** {model_config.model}
**Temperature:** {model_config.temperature}
**Max Tokens:** {model_config.max_tokens}
"""
            if model_config.endpoint:
                panel_content += f"**Endpoint:** {model_config.endpoint}\n"
                
            console.print(Panel(
                panel_content.strip(),
                title=f"{is_default}{in_roundtable}{name}",
                border_style="green" if name == config.default_model else "blue"
            ))
        
        console.print(f"\n[dim]⭐ = Default model, 🔄 = Round-table enabled[/dim]")
        console.print(f"[dim]Config file: {config_manager.get_config_path()}[/dim]\n")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key (e.g., 'default_model', 'model.openai/gpt-4.temperature')"),
    value: str = typer.Argument(..., help="Configuration value"),
):
    """Set a configuration value."""
    try:
        if key == "default_model":
            config_manager.set_default_model(value)
            console.print(f"[green]✓ Set default model to: {value}[/green]")
        elif key.startswith("model."):
            # Handle model-specific settings: model.openai/gpt-4.temperature
            parts = key.split(".", 2)
            if len(parts) != 3:
                raise ValueError("Model setting format: model.<model_name>.<setting>")
            
            model_name = parts[1]
            setting = parts[2]
            
            # Convert value to appropriate type
            if setting in ["temperature"]:
                value = float(value)
            elif setting in ["max_tokens", "context_window"]:
                value = int(value)
            elif setting in ["streaming", "critique_mode", "parallel_responses"]:
                value = value.lower() in ["true", "1", "yes", "on"]
            
            config_manager.update_model(model_name, **{setting: value})
            console.print(f"[green]✓ Updated {model_name}.{setting} = {value}[/green]")
        else:
            raise ValueError(f"Unknown configuration key: {key}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("add-model")
def config_add_model(
    name: str = typer.Argument(..., help="Model name (e.g., 'my-custom/gpt-4')"),
    provider: str = typer.Option(..., "--provider", "-p", help="Provider (openai, anthropic, ollama, gemini)"),
    model: str = typer.Option(..., "--model", "-m", help="Model identifier"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="API key or env:VAR_NAME"),
    endpoint: Optional[str] = typer.Option(None, "--endpoint", "-e", help="Custom endpoint URL"),
    temperature: float = typer.Option(0.7, "--temperature", "-t", help="Temperature (0.0-2.0)"),
    max_tokens: int = typer.Option(4000, "--max-tokens", help="Maximum tokens"),
):
    """Add a new model configuration."""
    try:
        updates = {
            "provider": provider,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if api_key:
            updates["api_key"] = api_key
        if endpoint:
            updates["endpoint"] = endpoint
            
        config_manager.update_model(name, **updates)
        console.print(f"[green]✓ Added model configuration: {name}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("roundtable")
def config_roundtable(
    add: Optional[str] = typer.Option(None, "--add", "-a", help="Add model to round-table"),
    remove: Optional[str] = typer.Option(None, "--remove", "-r", help="Remove model from round-table"),
    list_models: bool = typer.Option(False, "--list", "-l", help="List round-table models"),
):
    """Manage round-table configuration."""
    try:
        if add:
            config_manager.add_roundtable_model(add)
            console.print(f"[green]✓ Added {add} to round-table[/green]")
        elif remove:
            config_manager.remove_roundtable_model(remove)
            console.print(f"[green]✓ Removed {remove} from round-table[/green]")
        elif list_models:
            config = config_manager.load_config()
            console.print("\n[bold blue]🔄 Round-table Models[/bold blue]\n")
            for model in config.roundtable.enabled_models:
                console.print(f"  • {model}")
            console.print(f"\n[dim]Discussion rounds: {config.roundtable.discussion_rounds}[/dim]")
            console.print(f"[dim]Parallel mode: {config.roundtable.parallel_responses}[/dim]\n")
        else:
            console.print("[yellow]Please specify --add, --remove, or --list[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("env")
def config_env(
    init: bool = typer.Option(False, "--init", help="Create example .env file"),
    show: bool = typer.Option(False, "--show", help="Show .env file status"),
    path: Optional[str] = typer.Option(None, "--path", help="Custom path for .env file"),
):
    """Manage environment variables and .env files."""
    try:
        if init:
            target_path = Path(path) if path else None
            created_file = env_manager.create_example_env_file(target_path)
            console.print(f"[green]✓ Created example .env file: {created_file}[/green]")
            console.print("[dim]Edit the file and add your API keys[/dim]")
            
        elif show:
            # Force load env files to get current status
            env_manager.load_env_files()
            loaded_files = env_manager.get_loaded_env_files()
            
            console.print("\n[bold blue]🔐 Environment Variable Status[/bold blue]\n")
            
            if loaded_files:
                console.print("[green]📁 Loaded .env files:[/green]")
                for file_path in loaded_files:
                    console.print(f"  • {file_path}")
            else:
                console.print("[yellow]⚠️  No .env files found[/yellow]")
                console.print("[dim]Use --init to create one[/dim]")
            
            console.print("\n[blue]🗝️  API Key Status:[/blue]")
            api_keys = {
                "OPENAI_API_KEY": env_manager.get_env_var("OPENAI_API_KEY"),
                "ANTHROPIC_API_KEY": env_manager.get_env_var("ANTHROPIC_API_KEY"), 
                "GOOGLE_API_KEY": env_manager.get_env_var("GOOGLE_API_KEY"),
            }
            
            for key, value in api_keys.items():
                if value:
                    # Show first 8 chars and mask the rest
                    masked_value = value[:8] + "..." if len(value) > 8 else "***"
                    console.print(f"  ✅ {key}: {masked_value}")
                else:
                    console.print(f"  ❌ {key}: Not set")
            
            console.print(f"\n[dim]Checked locations:[/dim]")
            console.print(f"[dim]  • Current directory: {Path.cwd() / '.env'}[/dim]")
            console.print(f"[dim]  • Home directory: {Path.home() / '.env'}[/dim]")
            console.print(f"[dim]  • AI CLI config: {Path.home() / '.ai-cli' / '.env'}[/dim]")
            
        else:
            console.print("[yellow]Please specify --init or --show[/yellow]")
            console.print("[dim]Use 'ai config env --help' for more options[/dim]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("version")
def version():
    """Show version information."""
    console.print("[bold blue]AI CLI[/bold blue] version [green]0.1.0[/green]")
    console.print("Multi-model AI CLI with round-table discussions")


if __name__ == "__main__":
    app()