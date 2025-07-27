"""Tests for InteractiveSession."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai_cli.ui.interactive import InteractiveSession


class TestInteractiveSession:
    """Test InteractiveSession functionality."""

    def test_interactive_session_init(self, mock_chat_engine, mock_console):
        """Test InteractiveSession initialization."""
        session = InteractiveSession(mock_chat_engine, mock_console)

        assert session.chat_engine == mock_chat_engine
        assert session.console == mock_console
        assert session.conversation_history == []
        assert session.current_model == mock_chat_engine.config.default_model

    def test_create_session(self, mock_chat_engine, mock_console):
        """Test prompt session creation with completions."""
        session = InteractiveSession(mock_chat_engine, mock_console)
        prompt_session = session._create_session()

        # Verify that a PromptSession was created
        assert prompt_session is not None
        assert hasattr(prompt_session, "prompt_async")

    @pytest.mark.asyncio
    async def test_handle_exit_command(self, mock_chat_engine, mock_console):
        """Test handling exit commands."""
        session = InteractiveSession(mock_chat_engine, mock_console)

        # Test /exit command
        result = await session._handle_command("/exit")
        assert result is True

        # Test /quit command
        result = await session._handle_command("/quit")
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_help_command(self, mock_chat_engine, mock_console):
        """Test handling help command."""
        session = InteractiveSession(mock_chat_engine, mock_console)

        result = await session._handle_command("/help")
        assert result is False
        # Verify console.print was called for help
        assert mock_console.print.called

    @pytest.mark.asyncio
    async def test_handle_clear_command(self, mock_chat_engine, mock_console):
        """Test handling clear command."""
        session = InteractiveSession(mock_chat_engine, mock_console)
        session.conversation_history = [("user", "test"), ("assistant", "response")]

        result = await session._handle_command("/clear")
        assert result is False
        assert session.conversation_history == []
        assert mock_console.clear.called

    @pytest.mark.asyncio
    async def test_handle_model_command_switch(self, mock_chat_engine, mock_console):
        """Test switching models."""
        session = InteractiveSession(mock_chat_engine, mock_console)
        mock_chat_engine.config.models = {
            "test-model": MagicMock(),
            "new-model": MagicMock(),
        }

        result = await session._handle_command("/model new-model")
        assert result is False
        assert session.current_model == "new-model"

    @pytest.mark.asyncio
    async def test_handle_model_command_invalid(self, mock_chat_engine, mock_console):
        """Test switching to invalid model."""
        session = InteractiveSession(mock_chat_engine, mock_console)
        mock_chat_engine.config.models = {"test-model": MagicMock()}

        result = await session._handle_command("/model invalid-model")
        assert result is False
        assert session.current_model != "invalid-model"
        # Should print error and show available models
        assert mock_console.print.called

    @pytest.mark.asyncio
    async def test_handle_models_command(self, mock_chat_engine, mock_console):
        """Test listing available models."""
        session = InteractiveSession(mock_chat_engine, mock_console)

        result = await session._handle_command("/models")
        assert result is False
        # Should call _show_available_models
        assert mock_console.print.called

    @pytest.mark.asyncio
    async def test_handle_chat(self, mock_chat_engine, mock_console):
        """Test handling regular chat input."""
        session = InteractiveSession(mock_chat_engine, mock_console)
        mock_chat_engine.single_chat = AsyncMock()

        await session._handle_chat("Hello world")

        mock_chat_engine.single_chat.assert_called_once_with(
            "Hello world", session.current_model
        )
        assert len(session.conversation_history) == 2  # user + assistant entries

    @pytest.mark.asyncio
    async def test_handle_roundtable_command(self, mock_chat_engine, mock_console):
        """Test handling roundtable command."""
        session = InteractiveSession(mock_chat_engine, mock_console)
        mock_chat_engine.roundtable_chat = AsyncMock()

        result = await session._handle_command("/roundtable What is AI?")
        assert result is False
        mock_chat_engine.roundtable_chat.assert_called_once_with(
            "What is AI?", parallel=False
        )

    def test_show_current_model(self, mock_chat_engine, mock_console):
        """Test showing current model info."""
        session = InteractiveSession(mock_chat_engine, mock_console)

        # Just test that the method doesn't crash and prints something
        session._show_current_model()

        # Verify console output
        assert mock_console.print.called

    def test_show_available_models(self, mock_chat_engine, mock_console):
        """Test showing available models."""
        session = InteractiveSession(mock_chat_engine, mock_console)
        mock_model_config = MagicMock()
        mock_model_config.provider = "openai"
        mock_model_config.model = "gpt-4"
        mock_chat_engine.config.models = {"test-model": mock_model_config}

        session._show_available_models()

        # Verify console output
        assert mock_console.print.called

    def test_show_config_info(self, mock_chat_engine, mock_console):
        """Test showing configuration info."""
        session = InteractiveSession(mock_chat_engine, mock_console)

        session._show_config_info()

        # Verify console output for configuration panel
        assert mock_console.print.called
