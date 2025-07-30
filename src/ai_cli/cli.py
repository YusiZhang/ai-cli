import asyncio
from pathlib import Path
from typing import Any, Optional

import typer
from rich.console import Console
from rich.panel import Panel

from . import __version__
from .config.manager import ConfigManager
from .core.chat import ChatEngine
from .core.roles import RolePromptTemplates, RoundtableRole
from .ui.interactive import InteractiveSession
from .utils.env import env_manager

app = typer.Typer(
    name="ai",
    help="Multi-model AI CLI with round-table discussions",
    no_args_is_help=True,
)

config_app = typer.Typer(name="config", help="Configuration management")
app.add_typer(config_app, name="config")

console = Console()
config_manager = ConfigManager()


@app.command()
def chat(
    prompt: str = typer.Argument(..., help="The prompt to send to the AI model"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use"),
    roundtable: bool = typer.Option(
        False, "--roundtable", "-rt", help="Enable round-table discussion"
    ),
    parallel: bool = typer.Option(
        False, "--parallel", "-p", help="Run round-table in parallel mode"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Start interactive session"
    ),
) -> None:
    """Chat with AI models."""
    asyncio.run(_chat_async(prompt, model, roundtable, parallel, interactive))


async def _chat_async(
    prompt: str,
    model: Optional[str],
    roundtable: bool,
    parallel: bool,
    interactive: bool,
) -> None:
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
        raise typer.Exit(1) from e


@app.command()
def interactive() -> None:
    """Start an interactive chat session."""
    asyncio.run(_interactive_async())


async def _interactive_async() -> None:
    """Async interactive session."""
    try:
        config = config_manager.load_config()
        chat_engine = ChatEngine(config, console)
        session = InteractiveSession(chat_engine, console)
        await session.run()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def init(
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing configuration"
    ),
    minimal: bool = typer.Option(
        False, "--minimal", "-m", help="Create minimal configuration"
    ),
) -> None:
    """Initialize AI CLI configuration for first-time setup."""
    try:
        config_path = Path.home() / ".ai-cli" / "config.toml"

        # Check if config already exists
        if config_path.exists() and not force:
            console.print(
                f"[yellow]⚠️  Configuration already exists at {config_path}[/yellow]"
            )
            console.print("Use --force to overwrite, or --help for more options.")
            raise typer.Exit(1)

        # Ensure config directory exists
        config_path.parent.mkdir(exist_ok=True)

        # Create default configuration
        created_config = config_manager.create_default_config(minimal=minimal)

        # Create environment file template
        created_env = env_manager.create_ai_cli_env_file()

        # Success message with next steps
        console.print()
        console.print("[bold green]✅ AI CLI initialized successfully![/bold green]")
        console.print()
        console.print("[bold]Created files:[/bold]")
        console.print(f"  📄 Config: {created_config}")
        console.print(f"  🔐 Environment: {created_env}")
        console.print()
        console.print("[bold]Next steps:[/bold]")
        console.print("  1️⃣  Add your API keys to the .env file:")
        console.print(f"     [dim]edit {created_env}[/dim]")
        console.print("  2️⃣  Test your setup:")
        console.print('     [dim]ai chat "Hello, world!"[/dim]')
        console.print("  3️⃣  Try a round-table discussion:")
        console.print(
            '     [dim]ai chat --roundtable "What are the benefits of AI?"[/dim]'
        )
        console.print()
        console.print("[bold]API Key Resources:[/bold]")
        console.print("  🔑 OpenAI: https://platform.openai.com/account/api-keys")
        console.print("  🔑 Anthropic: https://console.anthropic.com/")
        console.print("  🔑 Google (Gemini): https://makersuite.google.com/app/apikey")
        console.print()

    except Exception as e:
        console.print(f"[red]❌ Error during initialization: {e}[/red]")
        raise typer.Exit(1) from e


@config_app.command("list")
def config_list() -> None:
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

            console.print(
                Panel(
                    panel_content.strip(),
                    title=f"{is_default}{in_roundtable}{name}",
                    border_style="green" if name == config.default_model else "blue",
                )
            )

        console.print("\n[dim]⭐ = Default model, 🔄 = Round-table enabled[/dim]")
        console.print(f"[dim]Config file: {config_manager.get_config_path()}[/dim]\n")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


@config_app.command("set")
def config_set(
    key: str = typer.Argument(
        ...,
        help="Configuration key (e.g., 'default_model', 'model.openai/gpt-4.temperature')",
    ),
    value: str = typer.Argument(..., help="Configuration value"),
) -> None:
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
            converted_value: Any
            if setting in ["temperature"]:
                converted_value = float(value)
            elif setting in ["max_tokens", "context_window"]:
                converted_value = int(value)
            elif setting in ["streaming", "parallel_responses"]:
                converted_value = value.lower() in ["true", "1", "yes", "on"]
            else:
                converted_value = value

            config_manager.update_model(model_name, **{setting: converted_value})
            console.print(f"[green]✓ Updated {model_name}.{setting} = {value}[/green]")
        else:
            raise ValueError(f"Unknown configuration key: {key}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


@config_app.command("add-model")
def config_add_model(
    name: str = typer.Argument(..., help="Model name (e.g., 'my-custom/gpt-4')"),
    provider: str = typer.Option(
        ..., "--provider", "-p", help="Provider (openai, anthropic, ollama, gemini)"
    ),
    model: str = typer.Option(..., "--model", "-m", help="Model identifier"),
    api_key: Optional[str] = typer.Option(
        None, "--api-key", "-k", help="API key or env:VAR_NAME"
    ),
    endpoint: Optional[str] = typer.Option(
        None, "--endpoint", "-e", help="Custom endpoint URL"
    ),
    temperature: float = typer.Option(
        0.7, "--temperature", "-t", help="Temperature (0.0-2.0)"
    ),
    max_tokens: int = typer.Option(4000, "--max-tokens", help="Maximum tokens"),
) -> None:
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
        raise typer.Exit(1) from e


@config_app.command("roundtable")
def config_roundtable(
    add: Optional[str] = typer.Option(
        None, "--add", "-a", help="Add model to round-table"
    ),
    remove: Optional[str] = typer.Option(
        None, "--remove", "-r", help="Remove model from round-table"
    ),
    list_models: bool = typer.Option(
        False, "--list", "-l", help="List round-table models"
    ),
    enable_roles: bool = typer.Option(
        False, "--enable-roles", help="Enable role-based prompting"
    ),
    disable_roles: bool = typer.Option(
        False, "--disable-roles", help="Disable role-based prompting"
    ),
    enable_rotation: bool = typer.Option(
        False, "--enable-rotation", help="Enable role rotation"
    ),
    disable_rotation: bool = typer.Option(
        False, "--disable-rotation", help="Disable role rotation"
    ),
) -> None:
    """Manage round-table configuration."""
    try:
        if add:
            config_manager.add_roundtable_model(add)
            console.print(f"[green]✓ Added {add} to round-table[/green]")
        elif remove:
            config_manager.remove_roundtable_model(remove)
            console.print(f"[green]✓ Removed {remove} from round-table[/green]")
        elif enable_roles:
            config_manager.set_role_based_prompting(True)
            console.print("[green]✓ Role-based prompting enabled[/green]")
        elif disable_roles:
            config_manager.set_role_based_prompting(False)
            console.print("[green]✓ Role-based prompting disabled[/green]")
        elif enable_rotation:
            config_manager.set_role_rotation(True)
            console.print("[green]✓ Role rotation enabled[/green]")
        elif disable_rotation:
            config_manager.set_role_rotation(False)
            console.print("[green]✓ Role rotation disabled[/green]")
        elif list_models:
            config = config_manager.load_config()
            console.print("\n[bold blue]🔄 Round-table Configuration[/bold blue]\n")

            console.print("[cyan]Models:[/cyan]")
            for model in config.roundtable.enabled_models:
                console.print(f"  • {model}")

            console.print("\n[cyan]Settings:[/cyan]")
            console.print(f"  Discussion rounds: {config.roundtable.discussion_rounds}")
            console.print(f"  Parallel mode: {config.roundtable.parallel_responses}")
            console.print(
                f"  Role-based prompting: {config.roundtable.use_role_based_prompting}"
            )
            console.print(f"  Role rotation: {config.roundtable.role_rotation}")

            if config.roundtable.role_assignments:
                console.print("\n[cyan]Role Assignments:[/cyan]")
                for model, roles in config.roundtable.role_assignments.items():
                    role_names = [role.value.title() for role in roles]
                    console.print(f"  {model}: {', '.join(role_names)}")

            if config.roundtable.custom_role_templates:
                console.print("\n[cyan]Custom Role Templates:[/cyan]")
                for role, template in config.roundtable.custom_role_templates.items():
                    preview = template[:50] + "..." if len(template) > 50 else template
                    console.print(f"  {role.value.title()}: {preview}")

            console.print()
        else:
            console.print(
                "[yellow]Please specify an option (--add, --remove, --list, --enable-roles, --disable-roles, --enable-rotation, --disable-rotation)[/yellow]"
            )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


@config_app.command("roles")
def config_roles(
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Model to configure roles for"
    ),
    assign: Optional[str] = typer.Option(
        None,
        "--assign",
        "-a",
        help="Assign roles (comma-separated: generator,critic,refiner,evaluator)",
    ),
    clear: Optional[str] = typer.Option(
        None, "--clear", "-c", help="Clear role assignments for model"
    ),
    list_assignments: bool = typer.Option(
        False, "--list", "-l", help="List all role assignments"
    ),
    list_roles: bool = typer.Option(False, "--list-roles", help="List available roles"),
) -> None:
    """Manage role assignments for roundtable models."""
    try:
        if list_roles:
            console.print("\n[bold blue]🎭 Available Roundtable Roles[/bold blue]\n")
            for role in RoundtableRole:
                console.print(
                    f"[cyan]{role.value}[/cyan]: {_get_role_description(role)}"
                )
            console.print()
        elif list_assignments:
            assignments = config_manager.get_role_assignments()
            console.print("\n[bold blue]🎭 Role Assignments[/bold blue]\n")
            if assignments:
                for model_name, roles in assignments.items():
                    role_names = [role.value.title() for role in roles]
                    console.print(f"[cyan]{model_name}[/cyan]: {', '.join(role_names)}")
                console.print(
                    "\n[dim]Models without assignments can play all roles[/dim]"
                )
            else:
                console.print("[dim]No specific role assignments configured[/dim]")
                console.print("[dim]All models can play all roles[/dim]")
            console.print()
        elif model and assign:
            # Parse roles from comma-separated string
            role_names = [name.strip().lower() for name in assign.split(",")]
            roles = []
            for role_name in role_names:
                try:
                    role = RoundtableRole(role_name)
                    roles.append(role)
                except ValueError as err:
                    console.print(
                        f"[red]Error: Invalid role '{role_name}'. Use --list-roles to see available roles.[/red]"
                    )
                    raise typer.Exit(1) from err

            config_manager.assign_roles_to_model(model, roles)
            role_names_display = [role.value.title() for role in roles]
            console.print(
                f"[green]✓ Assigned roles to {model}: {', '.join(role_names_display)}[/green]"
            )
        elif clear:
            config_manager.remove_role_assignments(clear)
            console.print(f"[green]✓ Cleared role assignments for {clear}[/green]")
        else:
            console.print(
                "[yellow]Please specify an option (--list, --list-roles, --model with --assign, or --clear)[/yellow]"
            )
            console.print("[dim]Examples:[/dim]")
            console.print("[dim]  ai config roles --list-roles[/dim]")
            console.print(
                "[dim]  ai config roles --model gpt-4 --assign generator,critic[/dim]"
            )
            console.print("[dim]  ai config roles --clear gpt-4[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


def _get_role_description(role: RoundtableRole) -> str:
    """Get a description for a role."""
    descriptions = {
        RoundtableRole.GENERATOR: "Creates initial ideas, suggestions, or solutions",
        RoundtableRole.CRITIC: "Analyzes and critiques previous responses",
        RoundtableRole.REFINER: "Improves and builds upon existing ideas",
        RoundtableRole.EVALUATOR: "Evaluates final outcomes and provides summaries",
    }
    return descriptions.get(role, "No description available")


@config_app.command("templates")
def config_templates(
    role: Optional[str] = typer.Option(
        None, "--role", "-r", help="Role to configure template for"
    ),
    set_template: Optional[str] = typer.Option(
        None, "--set", "-s", help="Set custom template for role"
    ),
    file: Optional[str] = typer.Option(
        None, "--file", "-f", help="Load template from file"
    ),
    clear: Optional[str] = typer.Option(
        None, "--clear", "-c", help="Clear custom template for role"
    ),
    list_templates: bool = typer.Option(
        False, "--list", "-l", help="List all custom templates"
    ),
    show_defaults: bool = typer.Option(
        False, "--show-defaults", help="Show default templates for all roles"
    ),
) -> None:
    """Manage custom role templates for roundtable discussions."""
    try:
        if show_defaults:
            console.print("\n[bold blue]🎭 Default Role Templates[/bold blue]\n")
            for role_enum in RoundtableRole:
                template = RolePromptTemplates.get_template(role_enum)
                console.print(f"[cyan]{role_enum.value.title()}:[/cyan]")
                console.print(f"[dim]{template}[/dim]\n")
        elif list_templates:
            templates = config_manager.get_custom_role_templates()
            console.print("\n[bold blue]🎭 Custom Role Templates[/bold blue]\n")
            if templates:
                for role_enum, template in templates.items():
                    preview = (
                        template[:100] + "..." if len(template) > 100 else template
                    )
                    console.print(f"[cyan]{role_enum.value.title()}:[/cyan]")
                    console.print(f"[dim]{preview}[/dim]\n")
                console.print(
                    "[dim]Note: Other roles use default templates unless customized[/dim]"
                )
            else:
                console.print("[dim]No custom templates configured[/dim]")
                console.print("[dim]All roles use default templates[/dim]")
            console.print()
        elif role and set_template:
            # Parse role name
            try:
                role_enum = RoundtableRole(role.lower())
            except ValueError as err:
                console.print(
                    f"[red]Error: Invalid role '{role}'. Available roles: {', '.join([r.value for r in RoundtableRole])}[/red]"
                )
                raise typer.Exit(1) from err

            config_manager.set_custom_role_template(role_enum, set_template)
            console.print(
                f"[green]✓ Set custom template for {role_enum.value.title()}[/green]"
            )
        elif role and file:
            # Parse role name
            try:
                role_enum = RoundtableRole(role.lower())
            except ValueError as err:
                console.print(
                    f"[red]Error: Invalid role '{role}'. Available roles: {', '.join([r.value for r in RoundtableRole])}[/red]"
                )
                raise typer.Exit(1) from err

            # Load template from file
            try:
                template_path = Path(file)
                if not template_path.exists():
                    console.print(f"[red]Error: Template file '{file}' not found[/red]")
                    raise typer.Exit(1)

                template_content = template_path.read_text(encoding="utf-8")
                config_manager.set_custom_role_template(role_enum, template_content)
                console.print(
                    f"[green]✓ Loaded custom template for {role_enum.value.title()} from {file}[/green]"
                )
            except Exception as e:
                console.print(f"[red]Error reading template file: {e}[/red]")
                raise typer.Exit(1) from e
        elif clear:
            # Parse role name
            try:
                role_enum = RoundtableRole(clear.lower())
            except ValueError as err:
                console.print(
                    f"[red]Error: Invalid role '{clear}'. Available roles: {', '.join([r.value for r in RoundtableRole])}[/red]"
                )
                raise typer.Exit(1) from err

            config_manager.remove_custom_role_template(role_enum)
            console.print(
                f"[green]✓ Cleared custom template for {role_enum.value.title()} (will use default)[/green]"
            )
        else:
            console.print(
                "[yellow]Please specify an option (--list, --show-defaults, --role with --set/--file, or --clear)[/yellow]"
            )
            console.print("[dim]Examples:[/dim]")
            console.print("[dim]  ai config templates --list[/dim]")
            console.print("[dim]  ai config templates --show-defaults[/dim]")
            console.print(
                '[dim]  ai config templates --role generator --set "Custom template..."[/dim]'
            )
            console.print(
                "[dim]  ai config templates --role critic --file template.txt[/dim]"
            )
            console.print("[dim]  ai config templates --clear refiner[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


@config_app.command("env")
def config_env(
    init: bool = typer.Option(False, "--init", help="Create example .env file"),
    show: bool = typer.Option(False, "--show", help="Show .env file status"),
    path: Optional[str] = typer.Option(
        None, "--path", help="Custom path for .env file"
    ),
) -> None:
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

            console.print("\n[dim]Checked locations:[/dim]")
            console.print(f"[dim]  • Current directory: {Path.cwd() / '.env'}[/dim]")
            console.print(f"[dim]  • Home directory: {Path.home() / '.env'}[/dim]")
            console.print(
                f"[dim]  • AI CLI config: {Path.home() / '.ai-cli' / '.env'}[/dim]"
            )

        else:
            console.print("[yellow]Please specify --init or --show[/yellow]")
            console.print("[dim]Use 'ai config env --help' for more options[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


@app.command("version")
def version() -> None:
    """Show version information."""
    console.print(f"[bold blue]AI CLI[/bold blue] version [green]{__version__}[/green]")
    console.print("Multi-model AI CLI with round-table discussions")


if __name__ == "__main__":
    app()
