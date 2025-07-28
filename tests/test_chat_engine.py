"""Tests for ChatEngine."""

from unittest.mock import AsyncMock, patch

import pytest

from ai_cli.core.messages import ChatMessage


class TestChatEngine:
    """Test ChatEngine functionality."""

    @pytest.mark.asyncio
    async def test_single_chat_success(
        self, mock_chat_engine, mock_provider, async_mock_response
    ):
        """Test successful single chat."""
        mock_provider.chat_stream = async_mock_response
        mock_chat_engine.provider_factory.get_provider.return_value = mock_provider

        await mock_chat_engine.single_chat("Hello", "test-model")

        # Verify provider was called
        mock_chat_engine.provider_factory.get_provider.assert_called_once_with(
            "test-model"
        )

        # Verify console output
        assert mock_chat_engine.console.print.called

    @pytest.mark.asyncio
    async def test_single_chat_provider_error(self, mock_chat_engine, mock_provider):
        """Test single chat with provider error."""

        # Create an async generator that raises an exception
        async def failing_stream(messages):
            raise Exception("API Error")
            yield  # This will never be reached

        mock_provider.chat_stream = failing_stream
        mock_chat_engine.provider_factory.get_provider.return_value = mock_provider

        with pytest.raises(Exception, match="API Error"):
            await mock_chat_engine.single_chat("Hello", "test-model")

    @pytest.mark.asyncio
    async def test_roundtable_chat_insufficient_models(self, mock_chat_engine):
        """Test roundtable chat with insufficient models."""
        mock_chat_engine.config.roundtable.enabled_models = [
            "test-model"
        ]  # Only 1 model

        await mock_chat_engine.roundtable_chat("Hello")

        # Should print warning about needing at least 2 models
        print_calls = [
            call[0][0] for call in mock_chat_engine.console.print.call_args_list
        ]
        warning_found = any(
            "Need at least 2 models" in str(call) for call in print_calls
        )
        assert warning_found

    @pytest.mark.asyncio
    async def test_roundtable_chat_sequential(
        self, mock_chat_engine, mock_provider, async_mock_response
    ):
        """Test roundtable chat in sequential mode."""
        # Setup multiple models
        mock_chat_engine.config.roundtable.enabled_models = ["model1", "model2"]
        mock_chat_engine.config.roundtable.discussion_rounds = 1

        mock_provider.chat_stream = async_mock_response
        mock_chat_engine.provider_factory.get_provider.return_value = mock_provider

        with patch.object(mock_chat_engine, "_run_sequential_round") as mock_sequential:
            mock_sequential.return_value = {
                "model1": "Response 1",
                "model2": "Response 2",
            }

            await mock_chat_engine.roundtable_chat("Hello", parallel=False)

            mock_sequential.assert_called_once()

    @pytest.mark.asyncio
    async def test_roundtable_chat_parallel(
        self, mock_chat_engine, mock_provider, async_mock_response
    ):
        """Test roundtable chat in parallel mode."""
        # Setup multiple models
        mock_chat_engine.config.roundtable.enabled_models = ["model1", "model2"]
        mock_chat_engine.config.roundtable.discussion_rounds = 1

        mock_provider.chat_stream = async_mock_response
        mock_chat_engine.provider_factory.get_provider.return_value = mock_provider

        with patch.object(mock_chat_engine, "_run_parallel_round") as mock_parallel:
            mock_parallel.return_value = {
                "model1": "Response 1",
                "model2": "Response 2",
            }

            await mock_chat_engine.roundtable_chat("Hello", parallel=True)

            mock_parallel.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_model_response(
        self, mock_chat_engine, mock_provider, async_mock_response
    ):
        """Test getting response from a specific model."""
        mock_provider.chat_stream = async_mock_response
        mock_chat_engine.provider_factory.get_provider.return_value = mock_provider

        messages = [ChatMessage("user", "Hello")]
        response = await mock_chat_engine._get_model_response("test-model", messages)

        assert response == "Hello world!"
        mock_chat_engine.provider_factory.get_provider.assert_called_with("test-model")

    @pytest.mark.asyncio
    async def test_run_sequential_round(self, mock_chat_engine, mock_provider):
        """Test running a sequential round."""
        # Add test models to the configuration
        from ai_cli.config.models import ModelConfig

        test_model_config = ModelConfig(provider="openai", model="test", api_key="test")
        mock_chat_engine.config.models["model1"] = test_model_config
        mock_chat_engine.config.models["model2"] = test_model_config

        # Mock the _get_model_response method
        with patch.object(mock_chat_engine, "_get_model_response") as mock_get_response:
            mock_get_response.side_effect = ["Response 1", "Response 2"]

            # Mock the StreamingDisplay class
            with patch("ai_cli.core.chat.StreamingDisplay") as mock_streaming_display:
                mock_display_instance = mock_streaming_display.return_value
                mock_display_instance.update_response = AsyncMock()
                mock_display_instance.finalize_response = AsyncMock()

                messages = [ChatMessage("user", "Hello")]
                models = ["model1", "model2"]

                responses = await mock_chat_engine._run_sequential_round(
                    messages, models
                )

                assert responses == {"model1": "Response 1", "model2": "Response 2"}
                assert mock_get_response.call_count == 2

    @pytest.mark.asyncio
    async def test_run_parallel_round(self, mock_chat_engine, mock_provider):
        """Test running a parallel round."""
        with patch.object(mock_chat_engine, "_get_model_response") as mock_get_response:
            mock_get_response.side_effect = ["Response 1", "Response 2"]

            # Mock the MultiStreamDisplay class
            with patch("ai_cli.core.chat.MultiStreamDisplay") as mock_multi_display:
                mock_display_instance = mock_multi_display.return_value
                mock_display_instance.update_model_response = AsyncMock()
                mock_display_instance.finalize_all_responses = AsyncMock()

                messages = [ChatMessage("user", "Hello")]
                models = ["model1", "model2"]

                responses = await mock_chat_engine._run_parallel_round(messages, models)

                assert "model1" in responses
                assert "model2" in responses

    def test_display_single_response(self, mock_chat_engine):
        """Test displaying a single response."""
        mock_chat_engine._display_single_response("test-model", "Hello world!")

        # Verify console.print was called
        assert mock_chat_engine.console.print.called

    def test_display_parallel_responses(self, mock_chat_engine):
        """Test displaying parallel responses."""
        responses = {"model1": "Response 1", "model2": "Response 2"}

        mock_chat_engine._display_parallel_responses(responses)

        # Verify console.print was called
        assert mock_chat_engine.console.print.called
