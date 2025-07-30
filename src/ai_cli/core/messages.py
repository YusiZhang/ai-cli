from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .roles import RoundtableRole


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

    def set_roundtable_role(
        self, roundtable_role: "RoundtableRole", model_name: str
    ) -> None:
        """Set roundtable role metadata for this message."""
        self.metadata["roundtable_role"] = roundtable_role.value
        self.metadata["model"] = model_name

    def get_roundtable_role(self) -> Optional[str]:
        """Get the roundtable role for this message."""
        return self.metadata.get("roundtable_role")

    def get_model_name(self) -> Optional[str]:
        """Get the model name that generated this message."""
        return self.metadata.get("model")

    def is_from_roundtable(self) -> bool:
        """Check if this message was generated in a roundtable discussion."""
        return "roundtable_role" in self.metadata
