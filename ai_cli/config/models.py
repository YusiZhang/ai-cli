from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

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
    critique_mode: bool = True
    parallel_responses: bool = False
    timeout_seconds: int = 30


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
        if "anthropic/claude-3-sonnet" not in v:
            v["anthropic/claude-3-sonnet"] = {
                "provider": "anthropic",
                "model": "claude-3-sonnet-20240229",
                "api_key": "env:ANTHROPIC_API_KEY",
            }

        # Add default Ollama model if not present
        if "ollama/llama2" not in v:
            v["ollama/llama2"] = {
                "provider": "ollama",
                "model": "llama2",
                "endpoint": "http://localhost:11434",
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
