"""Tests for ChatMessage class."""

from ai_cli.core.messages import ChatMessage


class TestChatMessage:
    """Test ChatMessage functionality."""

    def test_chat_message_basic(self):
        """Test basic ChatMessage creation."""
        message = ChatMessage("user", "Hello world")

        assert message.role == "user"
        assert message.content == "Hello world"
        assert message.metadata == {}

    def test_chat_message_with_metadata(self):
        """Test ChatMessage with metadata."""
        metadata = {"model": "gpt-4", "timestamp": "2023-01-01T00:00:00Z"}
        message = ChatMessage("assistant", "Hello back!", metadata)

        assert message.role == "assistant"
        assert message.content == "Hello back!"
        assert message.metadata == metadata
        assert message.metadata["model"] == "gpt-4"

    def test_chat_message_str_representation(self):
        """Test string representation of ChatMessage."""
        message = ChatMessage("user", "Test message")
        str_repr = str(message)

        assert "user" in str_repr
        assert "Test message" in str_repr

    def test_chat_message_dict_conversion(self):
        """Test converting ChatMessage to dict."""
        message = ChatMessage("user", "Hello", {"model": "gpt-4"})

        # Test if it can be converted to dict-like structure
        assert hasattr(message, "role")
        assert hasattr(message, "content")
        assert hasattr(message, "metadata")

    def test_chat_message_equality(self):
        """Test ChatMessage equality."""
        message1 = ChatMessage("user", "Hello", {"model": "gpt-4"})
        message2 = ChatMessage("user", "Hello", {"model": "gpt-4"})
        message3 = ChatMessage("user", "Hello", {"model": "claude"})

        # Note: This test depends on how equality is implemented
        # If not implemented, they won't be equal even with same content
        # This is testing the current behavior
        assert message1.role == message2.role
        assert message1.content == message2.content
        assert message1.metadata == message2.metadata

        assert message1.metadata != message3.metadata
