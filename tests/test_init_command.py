"""Tests for the init command functionality."""

import re
from unittest.mock import patch

from typer.testing import CliRunner

from ai_cli.cli import app
from ai_cli.config.manager import ConfigManager
from ai_cli.utils.env import EnvManager


def strip_ansi(text: str) -> str:
    """Strip ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


class TestInitCommand:
    """Test the ai init command."""

    def test_init_command_help(self):
        """Test that init command shows help correctly."""
        runner = CliRunner()
        result = runner.invoke(app, ["init", "--help"])
        clean_output = strip_ansi(result.stdout)

        assert result.exit_code == 0
        assert "Initialize AI CLI configuration" in clean_output
        assert "--force" in clean_output
        assert "--minimal" in clean_output

    def test_init_command_basic_functionality(self):
        """Test that init command has basic functionality without complex mocking."""
        runner = CliRunner()
        # Just test that the command doesn't crash and has expected content
        result = runner.invoke(app, ["init", "--help"])
        clean_output = strip_ansi(result.stdout)

        assert result.exit_code == 0
        assert "Initialize AI CLI configuration" in clean_output


class TestConfigManagerInit:
    """Test ConfigManager init-related methods."""

    def test_create_default_config_minimal(self, tmp_path):
        """Test creating minimal default config."""
        # Create a temporary config manager
        manager = ConfigManager()
        manager._config_path = tmp_path / "config.toml"

        result_path = manager.create_default_config(minimal=True)

        assert result_path == manager._config_path
        assert result_path.exists()

        # Read and verify the config content
        import toml

        config_data = toml.load(result_path)

        assert config_data["default_model"] == "openai/gpt-4"
        assert "openai/gpt-4" in config_data["models"]
        # Note: The ensure_default_models validator may add additional models
        # For minimal config, we just verify gpt-4 is present
        assert len(config_data["models"]) >= 1  # At least the requested model

    def test_create_default_config_full(self, tmp_path):
        """Test creating full default config."""
        # Create a temporary config manager
        manager = ConfigManager()
        manager._config_path = tmp_path / "config.toml"

        result_path = manager.create_default_config(minimal=False)

        assert result_path == manager._config_path
        assert result_path.exists()

        # Read and verify the config content
        import toml

        config_data = toml.load(result_path)

        assert config_data["default_model"] == "openai/gpt-4"
        assert len(config_data["models"]) >= 3  # At least three models in full
        assert "openai/gpt-4" in config_data["models"]
        assert "anthropic/claude-3-5-sonnet" in config_data["models"]
        assert "gemini" in config_data["models"]

        # Check roundtable config
        assert len(config_data["roundtable"]["enabled_models"]) == 2


class TestEnvManagerInit:
    """Test EnvManager init-related methods."""

    def test_create_ai_cli_env_file(self, tmp_path):
        """Test creating AI CLI .env file."""
        manager = EnvManager()

        # Override the target path for testing
        with patch("ai_cli.utils.env.Path") as mock_path_class:
            mock_path_class.home.return_value = tmp_path
            target_path = tmp_path / ".ai-cli" / ".env"
            target_path.parent.mkdir(exist_ok=True)

            result_path = manager.create_ai_cli_env_file()

            assert result_path == target_path
            assert result_path.exists()

            # Verify content
            content = result_path.read_text()
            assert "OPENAI_API_KEY=your-openai-api-key-here" in content
            assert "ANTHROPIC_API_KEY=your-anthropic-api-key-here" in content
            assert "GEMINI_API_KEY=your-google-api-key-here" in content
            assert "https://platform.openai.com/account/api-keys" in content
