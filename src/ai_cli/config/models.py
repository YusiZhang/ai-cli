from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator
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

    # Role-centric configuration (new approach)
    enabled_roles: list[RoundtableRole] = Field(
        default_factory=lambda: list(RoundtableRole)
    )
    role_model_mapping: dict[RoundtableRole, str] = Field(default_factory=dict)
    solo_model: Optional[str] = None

    # Discussion settings
    discussion_rounds: int = 2
    parallel_responses: bool = False
    timeout_seconds: int = 30

    # Template customization
    custom_role_templates: dict[RoundtableRole, str] = Field(default_factory=dict)

    # Legacy fields (deprecated but kept for migration)
    use_role_based_prompting: bool = True
    role_assignments: dict[str, list[RoundtableRole]] = Field(default_factory=dict)
    role_rotation: bool = True

    @field_validator("enabled_roles", mode="before")
    @classmethod
    def convert_enabled_roles(cls, v: Any) -> list[RoundtableRole]:
        """Convert string role values to RoundtableRole enum values and set defaults."""
        if not v:
            # Default to all roles if none specified
            return list(RoundtableRole)

        if isinstance(v, list):
            converted_roles = []
            for role in v:
                if isinstance(role, str):
                    try:
                        converted_roles.append(RoundtableRole(role))
                    except ValueError:
                        continue
                elif isinstance(role, RoundtableRole):
                    converted_roles.append(role)
            return converted_roles
        return list(RoundtableRole)

    @field_validator("role_model_mapping", mode="before")
    @classmethod
    def convert_role_model_mapping(cls, v: Any) -> dict[RoundtableRole, str]:
        """Convert string keys to RoundtableRole enum keys."""
        if not isinstance(v, dict):
            return {}

        result = {}
        for key, model in v.items():
            if isinstance(key, str):
                try:
                    role_key = RoundtableRole(key)
                    result[role_key] = model
                except ValueError:
                    continue
            elif isinstance(key, RoundtableRole):
                result[key] = model
        return result

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

    def get_model_for_role(self, role: RoundtableRole, default_model: str) -> str:
        """Get the model assigned to a specific role using priority fallback logic."""
        # Priority 1: explicit role_model_mapping
        if role in self.role_model_mapping:
            return self.role_model_mapping[role]

        # Priority 2: solo_model
        if self.solo_model:
            return self.solo_model

        # Priority 3: first available model from role_model_mapping
        if self.role_model_mapping:
            return next(iter(self.role_model_mapping.values()))

        # Priority 4: default_model
        return default_model

    def get_enabled_roles(self) -> list[RoundtableRole]:
        """Get the list of enabled roles in execution order."""
        if not self.enabled_roles:
            return list(RoundtableRole)

        # Return roles in fixed execution order: generator, critic, refiner, evaluator
        ordered_roles = [
            RoundtableRole.GENERATOR,
            RoundtableRole.CRITIC,
            RoundtableRole.REFINER,
            RoundtableRole.EVALUATOR,
        ]
        return [role for role in ordered_roles if role in self.enabled_roles]

    def get_role_template(self, role: RoundtableRole) -> Optional[str]:
        """Get custom template for a role, if configured."""
        return self.custom_role_templates.get(role)

    # Legacy methods for backward compatibility
    def get_available_roles_for_model(self, model_name: str) -> list[RoundtableRole]:
        """Get the roles that a specific model can play (legacy method)."""
        if model_name in self.role_assignments:
            return self.role_assignments[model_name]
        return list(RoundtableRole)

    def can_model_play_role(self, model_name: str, role: RoundtableRole) -> bool:
        """Check if a model can play a specific role (legacy method)."""
        available_roles = self.get_available_roles_for_model(model_name)
        return role in available_roles


class UIConfig(BaseModel):
    """Configuration for UI appearance and behavior."""

    theme: Literal["dark", "light"] = "dark"
    streaming: bool = True
    format: Literal["markdown", "plain"] = "markdown"
    show_model_icons: bool = True


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
        """Ensure we have some default model configurations only for completely empty configs."""
        if not v:
            # Only add defaults when models dict is completely empty (new user setup)
            v = {
                "openai/gpt-4": {
                    "provider": "openai",
                    "model": "gpt-4",
                    "api_key": "env:OPENAI_API_KEY",
                },
                "anthropic/claude-3-5-sonnet": {
                    "provider": "anthropic",
                    "model": "claude-3-5-sonnet-20241022",
                    "api_key": "env:ANTHROPIC_API_KEY",
                },
                "ollama/llama2": {
                    "provider": "ollama",
                    "model": "llama2",
                    "endpoint": "http://localhost:11434",
                },
                "gemini": {
                    "provider": "gemini",
                    "model": "gemini-2.5-flash",
                    "api_key": "env:GEMINI_API_KEY",
                },
            }

        # If user has existing models, respect their configuration completely
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
