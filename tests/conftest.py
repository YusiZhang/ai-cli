"""Test configuration and fixtures."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from rich.console import Console

from ai_cli.config.manager import ConfigManager
from ai_cli.config.models import AIConfig, ModelConfig, RoundTableConfig, UIConfig
from ai_cli.core.chat import ChatEngine
from ai_cli.providers.base import AIProvider


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_console():
    """Mock Rich console for testing."""
    console = MagicMock(spec=Console)
    # Add get_time method that Progress expects
    console.get_time = MagicMock(return_value=0.0)
    return console


@pytest.fixture
def sample_model_config():
    """Sample model configuration for testing."""
    return ModelConfig(
        provider="openai",
        model="gpt-4",
        api_key="test-key",
        max_tokens=4000,
        temperature=0.7,
    )


@pytest.fixture
def sample_ai_config(sample_model_config):
    """Sample AI configuration for testing."""
    return AIConfig(
        default_model="test-model",
        models={"test-model": sample_model_config},
        roundtable=RoundTableConfig(enabled_models=["test-model"], discussion_rounds=2),
        ui=UIConfig(theme="dark", streaming=True, format="markdown"),
    )


@pytest.fixture
def mock_config_manager(sample_ai_config, temp_config_dir):
    """Mock ConfigManager for testing."""
    manager = ConfigManager()
    manager._config_path = temp_config_dir / "config.toml"
    manager._config = sample_ai_config
    return manager


@pytest.fixture
def mock_provider():
    """Mock AI provider for testing."""
    provider = MagicMock(spec=AIProvider)
    provider.chat_stream = AsyncMock()
    provider.validate_config = AsyncMock(return_value=True)
    return provider


@pytest.fixture
def mock_chat_engine(sample_ai_config, mock_console):
    """Mock ChatEngine for testing."""
    engine = ChatEngine(sample_ai_config, mock_console)
    # Mock the provider factory
    engine.provider_factory.get_provider = MagicMock()
    # Mock the streaming display
    engine.streaming_display.update_response = AsyncMock()
    engine.streaming_display.finalize_response = AsyncMock()
    return engine


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def async_mock_response():
    """Helper to create async mock responses."""

    async def _mock_stream(messages):
        yield "Hello"
        yield " world"
        yield "!"

    return _mock_stream
