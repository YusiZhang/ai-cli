"""Tests for configuration models."""

import pytest
from pydantic import ValidationError

from ai_cli.config.models import AIConfig, ModelConfig, RoundTableConfig, UIConfig


class TestModelConfig:
    """Test ModelConfig validation and functionality."""

    def test_model_config_valid(self):
        """Test valid model configuration."""
        config = ModelConfig(
            provider="openai",
            model="gpt-4",
            api_key="test-key",
            max_tokens=4000,
            temperature=0.7,
        )

        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.api_key == "test-key"
        assert config.max_tokens == 4000
        assert config.temperature == 0.7
        assert config.context_window == 4000  # Default value

    def test_model_config_defaults(self):
        """Test model configuration with defaults."""
        config = ModelConfig(provider="openai", model="gpt-4")

        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.api_key is None
        assert config.max_tokens == 4000
        assert config.temperature == 0.7
        assert config.context_window == 4000

    def test_model_config_invalid_provider(self):
        """Test model configuration with invalid provider."""
        with pytest.raises(ValidationError):
            ModelConfig(provider="invalid_provider", model="gpt-4")

    def test_model_config_missing_model(self):
        """Test model configuration missing required model field."""
        with pytest.raises(ValidationError):
            ModelConfig(provider="openai")


class TestRoundTableConfig:
    """Test RoundTableConfig validation."""

    def test_roundtable_config_defaults(self):
        """Test roundtable configuration defaults."""
        config = RoundTableConfig()

        assert config.enabled_models == []
        assert config.discussion_rounds == 2
        assert config.parallel_responses is False
        assert config.timeout_seconds == 30

    def test_roundtable_config_custom(self):
        """Test custom roundtable configuration."""
        config = RoundTableConfig(
            enabled_models=["model1", "model2"],
            discussion_rounds=3,
            parallel_responses=True,
            timeout_seconds=60,
        )

        assert config.enabled_models == ["model1", "model2"]
        assert config.discussion_rounds == 3
        assert config.parallel_responses is True
        assert config.timeout_seconds == 60


class TestUIConfig:
    """Test UIConfig validation."""

    def test_ui_config_defaults(self):
        """Test UI configuration defaults."""
        config = UIConfig()

        assert config.theme == "dark"
        assert config.streaming is True
        assert config.format == "markdown"
        assert config.show_model_icons is True
        assert config.show_timestamps is False

    def test_ui_config_custom(self):
        """Test custom UI configuration."""
        config = UIConfig(
            theme="light",
            streaming=False,
            format="plain",
            show_model_icons=False,
            show_timestamps=True,
        )

        assert config.theme == "light"
        assert config.streaming is False
        assert config.format == "plain"
        assert config.show_model_icons is False
        assert config.show_timestamps is True

    def test_ui_config_invalid_theme(self):
        """Test UI configuration with invalid theme."""
        with pytest.raises(ValidationError):
            UIConfig(theme="invalid_theme")

    def test_ui_config_invalid_format(self):
        """Test UI configuration with invalid format."""
        with pytest.raises(ValidationError):
            UIConfig(format="invalid_format")


class TestAIConfig:
    """Test AIConfig validation and functionality."""

    def test_ai_config_defaults(self):
        """Test AI configuration with defaults."""
        config = AIConfig()

        assert config.default_model == "openai/gpt-4"
        assert "openai/gpt-4" in config.models
        assert "anthropic/claude-3-5-sonnet" in config.models
        assert "ollama/llama2" in config.models
        assert isinstance(config.roundtable, RoundTableConfig)
        assert isinstance(config.ui, UIConfig)

    def test_ai_config_custom(self):
        """Test custom AI configuration."""
        model_config = ModelConfig(provider="openai", model="gpt-4", api_key="test-key")

        config = AIConfig(
            default_model="custom-model",
            models={"custom-model": model_config},
            roundtable=RoundTableConfig(discussion_rounds=3),
            ui=UIConfig(theme="light"),
        )

        assert config.default_model == "custom-model"
        assert "custom-model" in config.models
        assert config.roundtable.discussion_rounds == 3
        assert config.ui.theme == "light"

    def test_get_model_config_existing(self):
        """Test getting existing model configuration."""
        config = AIConfig()
        model_config = config.get_model_config("openai/gpt-4")

        assert isinstance(model_config, ModelConfig)
        assert model_config.provider == "openai"
        assert model_config.model == "gpt-4"

    def test_get_model_config_nonexistent(self):
        """Test getting non-existent model configuration."""
        config = AIConfig()

        with pytest.raises(ValueError, match="Model 'nonexistent' not found"):
            config.get_model_config("nonexistent")

    def test_get_model_config_dict_format(self):
        """Test getting model config when stored as dict."""
        config = AIConfig(
            models={
                "test-model": {
                    "provider": "openai",
                    "model": "gpt-4",
                    "temperature": 0.8,
                }
            }
        )

        model_config = config.get_model_config("test-model")

        assert isinstance(model_config, ModelConfig)
        assert model_config.provider == "openai"
        assert model_config.model == "gpt-4"
        assert model_config.temperature == 0.8
