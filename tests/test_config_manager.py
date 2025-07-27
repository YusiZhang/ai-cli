"""Tests for ConfigManager."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from ai_cli.config.manager import ConfigManager
from ai_cli.config.models import AIConfig, ModelConfig


class TestConfigManager:
    """Test ConfigManager functionality."""

    def test_init_creates_config_dir(self):
        """Test that ConfigManager creates config directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".ai-cli" / "config.toml"

            with patch.object(Path, "home", return_value=Path(tmpdir)):
                manager = ConfigManager()
                assert manager._config_path == config_path
                assert config_path.parent.exists()

    def test_load_config_creates_default_when_missing(self, temp_config_dir):
        """Test loading config creates default when file doesn't exist."""
        manager = ConfigManager()
        manager._config_path = temp_config_dir / "config.toml"

        config = manager.load_config()

        assert isinstance(config, AIConfig)
        assert config.default_model == "openai/gpt-4"
        assert "openai/gpt-4" in config.models
        assert manager._config_path.exists()

    def test_load_config_from_existing_file(self, temp_config_dir):
        """Test loading config from existing file."""
        config_file = temp_config_dir / "config.toml"
        config_content = """
default_model = "test-model"

[models.test-model]
provider = "openai"
model = "gpt-4"
api_key = "test-key"

[roundtable]
enabled_models = ["test-model"]
discussion_rounds = 3

[ui]
theme = "light"
streaming = false
"""
        config_file.write_text(config_content)

        manager = ConfigManager()
        manager._config_path = config_file

        config = manager.load_config()

        assert config.default_model == "test-model"
        assert config.roundtable.discussion_rounds == 3
        assert config.ui.theme == "light"
        assert not config.ui.streaming

    def test_save_config(self, temp_config_dir, sample_ai_config):
        """Test saving configuration to file."""
        config_file = temp_config_dir / "config.toml"
        manager = ConfigManager()
        manager._config_path = config_file

        manager.save_config(sample_ai_config)

        assert config_file.exists()
        content = config_file.read_text()
        assert "default_model" in content
        assert "test-model" in content

    def test_update_model_new(self, mock_config_manager):
        """Test updating a model that doesn't exist creates new one."""
        mock_config_manager.update_model(
            "new-model",
            provider="anthropic",
            model="claude-3-sonnet",
            api_key="new-key",
        )

        config = mock_config_manager.load_config()
        assert "new-model" in config.models
        model_config = config.get_model_config("new-model")
        assert model_config.provider == "anthropic"
        assert model_config.model == "claude-3-sonnet"

    def test_update_model_existing(self, mock_config_manager):
        """Test updating an existing model."""
        mock_config_manager.update_model("test-model", temperature=0.9, max_tokens=8000)

        config = mock_config_manager.load_config()
        model_config = config.get_model_config("test-model")
        assert model_config.temperature == 0.9
        assert model_config.max_tokens == 8000

    def test_set_default_model_valid(self, mock_config_manager):
        """Test setting default model to valid model."""
        mock_config_manager.set_default_model("test-model")

        config = mock_config_manager.load_config()
        assert config.default_model == "test-model"

    def test_set_default_model_invalid(self, mock_config_manager):
        """Test setting default model to invalid model raises error."""
        with pytest.raises(ValueError, match="Model 'invalid-model' not found"):
            mock_config_manager.set_default_model("invalid-model")

    def test_add_roundtable_model(self, mock_config_manager):
        """Test adding model to roundtable."""
        # Ensure test-model is not in roundtable initially
        config = mock_config_manager.load_config()
        config.roundtable.enabled_models = []

        mock_config_manager.add_roundtable_model("test-model")

        config = mock_config_manager.load_config()
        assert "test-model" in config.roundtable.enabled_models

    def test_add_roundtable_model_invalid(self, mock_config_manager):
        """Test adding invalid model to roundtable raises error."""
        with pytest.raises(ValueError, match="Model 'invalid-model' not found"):
            mock_config_manager.add_roundtable_model("invalid-model")

    def test_remove_roundtable_model(self, mock_config_manager):
        """Test removing model from roundtable."""
        mock_config_manager.remove_roundtable_model("test-model")

        config = mock_config_manager.load_config()
        assert "test-model" not in config.roundtable.enabled_models

    def test_list_models(self, mock_config_manager):
        """Test listing all models."""
        models = mock_config_manager.list_models()

        assert isinstance(models, dict)
        assert "test-model" in models
        assert isinstance(models["test-model"], ModelConfig)

    def test_get_config_path(self, mock_config_manager, temp_config_dir):
        """Test getting config path."""
        mock_config_manager._config_path = temp_config_dir / "config.toml"
        path = mock_config_manager.get_config_path()

        assert path == temp_config_dir / "config.toml"
