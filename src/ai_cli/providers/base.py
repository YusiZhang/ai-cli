from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from ..config.models import ModelConfig
from ..core.messages import ChatMessage


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(self, model_config: ModelConfig) -> None:
        self.config = model_config

    @abstractmethod
    def chat_stream(self, messages: list[ChatMessage]) -> AsyncGenerator[str, None]:
        """Stream chat responses from the AI model."""
        pass

    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate that the provider configuration is correct."""
        pass

    def _messages_to_dict(self, messages: list[ChatMessage]) -> list[dict[str, Any]]:
        """Convert ChatMessage objects to dictionaries."""
        return [{"role": msg.role, "content": msg.content} for msg in messages]
