"""Integration tests for CLI commands."""

import re
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from ai_cli.cli import app


def strip_ansi(text: str) -> str:
    """Strip ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


class TestCLI:
    """Test CLI command functionality."""

    def setup_method(self):
        """Setup test runner."""
        self.runner = CliRunner()

    def test_version_command(self):
        """Test version command."""
        result = self.runner.invoke(app, ["version"])
        clean_output = strip_ansi(result.stdout)

        assert result.exit_code == 0
        assert "AI CLI" in clean_output
        assert "version" in clean_output

    @patch("ai_cli.cli.asyncio.run")
    @patch("ai_cli.cli.ConfigManager")
    def test_chat_command_basic(self, mock_config_manager, mock_asyncio_run):
        """Test basic chat command."""
        mock_config = MagicMock()
        mock_config_manager.return_value.load_config.return_value = mock_config

        result = self.runner.invoke(app, ["chat", "Hello world"])

        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()

    @patch("ai_cli.cli.asyncio.run")
    @patch("ai_cli.cli.ConfigManager")
    def test_chat_command_with_model(self, mock_config_manager, mock_asyncio_run):
        """Test chat command with specific model."""
        mock_config = MagicMock()
        mock_config_manager.return_value.load_config.return_value = mock_config

        result = self.runner.invoke(app, ["chat", "--model", "test-model", "Hello"])

        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()

    @patch("ai_cli.cli.asyncio.run")
    @patch("ai_cli.cli.ConfigManager")
    def test_chat_command_roundtable(self, mock_config_manager, mock_asyncio_run):
        """Test chat command with roundtable flag."""
        mock_config = MagicMock()
        mock_config_manager.return_value.load_config.return_value = mock_config

        result = self.runner.invoke(app, ["chat", "--roundtable", "Hello"])

        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()

    @patch("ai_cli.cli.asyncio.run")
    @patch("ai_cli.cli.ConfigManager")
    def test_interactive_command(self, mock_config_manager, mock_asyncio_run):
        """Test interactive command."""
        mock_config = MagicMock()
        mock_config_manager.return_value.load_config.return_value = mock_config

        result = self.runner.invoke(app, ["interactive"])

        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()

    @patch("ai_cli.cli.config_manager")
    def test_config_list_command(self, mock_config_manager):
        """Test config list command."""
        mock_config_manager.list_models.return_value = {
            "test-model": MagicMock(
                provider="openai",
                model="gpt-4",
                temperature=0.7,
                max_tokens=4000,
                endpoint=None,
            )
        }
        mock_config = MagicMock()
        mock_config.default_model = "test-model"
        mock_config.roundtable.enabled_models = ["test-model"]
        mock_config_manager.load_config.return_value = mock_config

        result = self.runner.invoke(app, ["config", "list"])
        clean_output = strip_ansi(result.stdout)

        assert result.exit_code == 0
        assert "test-model" in clean_output

    @patch("ai_cli.cli.config_manager")
    def test_config_set_default_model(self, mock_config_manager):
        """Test config set default model command."""
        result = self.runner.invoke(
            app, ["config", "set", "default_model", "new-model"]
        )

        assert result.exit_code == 0
        mock_config_manager.set_default_model.assert_called_once_with("new-model")

    @patch("ai_cli.cli.config_manager")
    def test_config_add_model_command(self, mock_config_manager):
        """Test config add-model command."""

        result = self.runner.invoke(
            app,
            [
                "config",
                "add-model",
                "test-model",
                "--provider",
                "openai",
                "--model",
                "gpt-4",
                "--api-key",
                "test-key",
            ],
        )

        assert result.exit_code == 0
        mock_config_manager.update_model.assert_called_once()

    @patch("ai_cli.cli.config_manager")
    def test_config_roundtable_add(self, mock_config_manager):
        """Test config roundtable add command."""
        result = self.runner.invoke(
            app, ["config", "roundtable", "--add", "test-model"]
        )

        assert result.exit_code == 0
        mock_config_manager.add_roundtable_model.assert_called_once_with("test-model")

    @patch("ai_cli.cli.config_manager")
    def test_config_roundtable_remove(self, mock_config_manager):
        """Test config roundtable remove command."""
        result = self.runner.invoke(
            app, ["config", "roundtable", "--remove", "test-model"]
        )

        assert result.exit_code == 0
        mock_config_manager.remove_roundtable_model.assert_called_once_with(
            "test-model"
        )

    @patch("ai_cli.cli.env_manager")
    def test_config_env_show(self, mock_env_manager):
        """Test config env show command."""
        mock_env_manager.get_loaded_env_files.return_value = ["/path/to/.env"]
        mock_env_manager.get_env_var.return_value = "test-key-value"

        result = self.runner.invoke(app, ["config", "env", "--show"])
        clean_output = strip_ansi(result.stdout)

        assert result.exit_code == 0
        assert "Environment Variable Status" in clean_output

    @patch("ai_cli.cli.env_manager")
    def test_config_env_init(self, mock_env_manager):
        """Test config env init command."""
        mock_env_manager.create_example_env_file.return_value = "/path/to/.env"

        result = self.runner.invoke(app, ["config", "env", "--init"])

        assert result.exit_code == 0
        mock_env_manager.create_example_env_file.assert_called_once()

    @patch("ai_cli.cli.config_manager")
    def test_error_handling(self, mock_config_manager):
        """Test CLI error handling."""
        mock_config_manager.load_config.side_effect = Exception("Config error")

        result = self.runner.invoke(app, ["config", "list"])
        clean_output = strip_ansi(result.stdout)

        assert result.exit_code == 1
        assert "Error: Config error" in clean_output
