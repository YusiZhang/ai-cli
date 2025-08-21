import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class ResponseEntry(BaseModel):
    """A single response entry in the history."""

    timestamp: str
    prompt: str
    response: str
    model: str
    preview: str


class ResponseHistory:
    """Manages the history of AI responses for easy copying."""

    def __init__(self, max_responses: int = 20, preview_length: int = 50):
        self.max_responses = max_responses
        self.preview_length = preview_length
        self._history_dir = Path.home() / ".ai-cli"
        self._history_file = self._history_dir / "response_history.json"

        # Ensure directory exists
        self._history_dir.mkdir(exist_ok=True)

    def add_response(self, prompt: str, response: str, model: str) -> None:
        """Add a new response to the history."""
        # Create preview (truncated version)
        preview = self._create_preview(response)

        # Create new entry
        entry = ResponseEntry(
            timestamp=datetime.utcnow().isoformat(),
            prompt=prompt,
            response=response,
            model=model,
            preview=preview,
        )

        # Load existing history
        responses = self._load_responses()

        # Add new entry to the beginning
        responses.insert(0, entry)

        # Truncate to max responses
        if len(responses) > self.max_responses:
            responses = responses[: self.max_responses]

        # Save back to file
        self._save_responses(responses)

    def get_responses(self) -> list[ResponseEntry]:
        """Get all responses from history, most recent first."""
        return self._load_responses()

    def get_latest(self) -> Optional[ResponseEntry]:
        """Get the most recent response."""
        responses = self._load_responses()
        return responses[0] if responses else None

    def _create_preview(self, text: str) -> str:
        """Create a truncated preview of the response."""
        # Strip any leading/trailing whitespace
        text = text.strip()

        # If text is shorter than preview length, return as-is
        if len(text) <= self.preview_length:
            return text

        # Truncate and add ellipsis
        return text[: self.preview_length] + "..."

    def _load_responses(self) -> list[ResponseEntry]:
        """Load responses from the history file."""
        if not self._history_file.exists():
            return []

        try:
            with open(self._history_file, encoding="utf-8") as f:
                data = json.load(f)
                return [ResponseEntry(**entry) for entry in data]
        except (json.JSONDecodeError, KeyError, TypeError):
            # If file is corrupted, start fresh
            return []

    def _save_responses(self, responses: list[ResponseEntry]) -> None:
        """Save responses to the history file."""
        data = [entry.model_dump() for entry in responses]

        try:
            with open(self._history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError:
            # Silently fail if we can't write to disk
            pass
