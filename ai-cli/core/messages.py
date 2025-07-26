from typing import Dict, Any


class ChatMessage:
    """Represents a chat message."""
    def __init__(self, role: str, content: str, metadata: Dict[str, Any] = None):
        self.role = role
        self.content = content
        self.metadata = metadata or {}