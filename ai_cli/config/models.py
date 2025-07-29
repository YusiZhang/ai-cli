from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..core.roles import RoundtableRole
from ..utils.env import env_manager


class ModelConfig(BaseModel):
    """Configuration for a specific AI model."""

    provider: Literal["openai", "anthropic", "ollama", "gemini"] = "openai"
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    model: str
    max_tokens: int = 4000
    temperature: float = 0.7
    context_window: int = 4000

    @field_validator("api_key", mode="before")
    @classmethod
    def resolve_env_var(cls, v: str) -> str:
        """Resolve environment variables in API keys."""
        result = env_manager.resolve_env_reference(v)
        return result if result is not None else v


class RoundTableConfig(BaseModel):
    """Configuration for round-table discussions."""

    enabled_models: list[str] = []
    discussion_rounds: int = 2
    parallel_responses: bool = False
    timeout_seconds: int = 30

    # Enhanced role-based configuration
    use_role_based_prompting: bool = True
    role_assignments: dict[str, list[RoundtableRole]] = {}
    role_rotation: bool = True
    preserve_original_context: bool = True
    custom_role_templates: dict[RoundtableRole, str] = {}

    @field_validator("role_assignments", mode="before")
    @classmethod
    def convert_role_assignment_strings(cls, v: Any) -> dict[str, list[RoundtableRole]]:
        """Convert string role values to RoundtableRole enum values."""
        if not isinstance(v, dict):
            return {}

        result = {}
        for model, roles in v.items():
            if isinstance(roles, list):
                converted_roles = []
                for role in roles:
                    if isinstance(role, str):
                        try:
                            converted_roles.append(RoundtableRole(role))
                        except ValueError:
                            # Invalid role string, skip it
                            continue
                    elif isinstance(role, RoundtableRole):
                        converted_roles.append(role)
                result[model] = converted_roles
            else:
                result[model] = roles
        return result

    @field_validator("custom_role_templates", mode="before")
    @classmethod
    def convert_role_template_keys(cls, v: Any) -> dict[RoundtableRole, str]:
        """Convert string keys to RoundtableRole enum keys."""
        if not isinstance(v, dict):
            return {}

        result = {}
        for key, template in v.items():
            if isinstance(key, str):
                try:
                    role_key = RoundtableRole(key)
                    result[role_key] = template
                except ValueError:
                    # Invalid role string, skip it
                    continue
            elif isinstance(key, RoundtableRole):
                result[key] = template
        return result

    def get_available_roles_for_model(self, model_name: str) -> list[RoundtableRole]:
        """Get the roles that a specific model can play."""
        if model_name in self.role_assignments:
            return self.role_assignments[model_name]
        # Default: all models can play all roles
        return list(RoundtableRole)

    def can_model_play_role(self, model_name: str, role: RoundtableRole) -> bool:
        """Check if a model can play a specific role."""
        available_roles = self.get_available_roles_for_model(model_name)
        return role in available_roles

    def get_role_template(self, role: RoundtableRole) -> Optional[str]:
        """Get custom template for a role, if configured."""
        return self.custom_role_templates.get(role)


class UIConfig(BaseModel):
    """Configuration for UI appearance and behavior."""

    theme: Literal["dark", "light"] = "dark"
    streaming: bool = True
    format: Literal["markdown", "plain"] = "markdown"
    show_model_icons: bool = True
    show_timestamps: bool = False


class AIConfig(BaseSettings):
    """Main configuration class for the AI CLI."""

    default_model: str = "openai/gpt-4"
    models: dict[str, ModelConfig] = {}
    roundtable: RoundTableConfig = RoundTableConfig()
    ui: UIConfig = UIConfig()

    model_config = SettingsConfigDict(
        env_prefix="AI_CLI_", case_sensitive=False, extra="ignore"
    )

    @field_validator("models", mode="before")
    @classmethod
    def ensure_default_models(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure we have some default model configurations."""
        if not v:
            v = {}

        # Add default OpenAI model if not present
        if "openai/gpt-4" not in v:
            v["openai/gpt-4"] = {
                "provider": "openai",
                "model": "gpt-4",
                "api_key": "env:OPENAI_API_KEY",
            }

        # Add default Claude model if not present
        if "anthropic/claude-3-5-sonnet" not in v:
            v["anthropic/claude-3-5-sonnet"] = {
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-20241022",
                "api_key": "env:ANTHROPIC_API_KEY",
            }

        # Add default Ollama model if not present
        if "ollama/llama2" not in v:
            v["ollama/llama2"] = {
                "provider": "ollama",
                "model": "llama2",
                "endpoint": "http://localhost:11434",
            }

        # Add default Gemini model if not present
        if "gemini" not in v:
            v["gemini"] = {
                "provider": "gemini",
                "model": "gemini-2.5-flash",
                "api_key": "env:GEMINI_API_KEY",
            }

        return v

    def get_config_path(self) -> Path:
        """Get the path to the configuration file."""
        config_dir = Path.home() / ".ai-cli"
        config_dir.mkdir(exist_ok=True)
        return config_dir / "config.toml"

    def get_model_config(self, model_name: str) -> ModelConfig:
        """Get configuration for a specific model."""
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found in configuration")

        return self.models[model_name]
