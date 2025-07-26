from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Dict, Any
from ..core.messages import ChatMessage


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, model_config):
        self.config = model_config
    
    @abstractmethod
    async def chat_stream(self, messages: List[ChatMessage]) -> AsyncIterator[str]:
        """Stream chat responses from the AI model."""
        pass
    
    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate that the provider configuration is correct."""
        pass
    
    def _messages_to_dict(self, messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        """Convert ChatMessage objects to dictionaries."""
        return [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in messages
        ]