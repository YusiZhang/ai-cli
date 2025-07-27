from typing import Any, Optional


class ChatMessage:
    """Represents a chat message."""

    def __init__(
        self, role: str, content: str, metadata: Optional[dict[str, Any]] = None
    ):
        self.role = role
        self.content = content
        self.metadata = metadata or {}

    def __str__(self) -> str:
        return f"ChatMessage(role='{self.role}', content='{self.content[:50]}...', metadata={self.metadata})"
