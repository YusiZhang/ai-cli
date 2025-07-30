import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class EnvManager:
    """Manages environment variables from system and .env files."""

    def __init__(self) -> None:
        self._loaded = False
        self._env_files_loaded: list[Path] = []

    def load_env_files(self) -> None:
        """Load environment variables from various .env file locations."""
        if self._loaded:
            return

        # List of .env file locations to check (in order of priority)
        env_file_locations = [
            Path.cwd() / ".env",  # Current directory
            Path.home() / ".env",  # Home directory
            Path.home() / ".ai-cli" / ".env",  # AI CLI config directory
        ]

        for env_file in env_file_locations:
            if env_file.exists():
                load_dotenv(
                    env_file, override=False
                )  # Don't override existing env vars
                self._env_files_loaded.append(env_file)

        self._loaded = True

    def get_env_var(
        self, var_name: str, default: Optional[str] = None
    ) -> Optional[str]:
        """Get environment variable, loading .env files if needed."""
        self.load_env_files()
        return os.getenv(var_name, default)

    def resolve_env_reference(self, value: str) -> Optional[str]:
        """Resolve environment variable references like 'env:VAR_NAME'."""
        if isinstance(value, str) and value.startswith("env:"):
            env_var = value[4:]  # Remove 'env:' prefix
            return self.get_env_var(env_var)
        return value

    def get_loaded_env_files(self) -> list[Path]:
        """Get list of .env files that were loaded."""
        self.load_env_files()
        return self._env_files_loaded.copy()

    def create_example_env_file(self, target_path: Optional[Path] = None) -> Path:
        """Create an example .env file with common API keys."""
        if target_path is None:
            target_path = Path.home() / ".env"

        example_content = """# AI CLI Environment Variables
# Add your API keys here

# OpenAI API Key
# Get from: https://platform.openai.com/account/api-keys
OPENAI_API_KEY=your-openai-api-key-here

# Anthropic API Key
# Get from: https://console.anthropic.com/
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Google API Key (for Gemini)
# Get from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your-google-api-key-here

# Optional: Custom endpoints
# OLLAMA_ENDPOINT=http://localhost:11434
# CUSTOM_API_ENDPOINT=https://your-custom-endpoint.com
"""

        # Only create if it doesn't exist
        if not target_path.exists():
            target_path.write_text(example_content)
            return target_path
        else:
            # Create with .example suffix if main file exists
            example_path = target_path.with_suffix(".example")
            example_path.write_text(example_content)
            return example_path

    def create_ai_cli_env_file(self) -> Path:
        """Create an AI CLI-specific .env file in ~/.ai-cli/ directory.

        Returns:
            Path to the created .env file
        """
        target_path = Path.home() / ".ai-cli" / ".env"

        # Ensure directory exists
        target_path.parent.mkdir(exist_ok=True)

        env_content = """# AI CLI Environment Variables
# Add your API keys here - get them from the provider websites

# OpenAI API Key
# Get from: https://platform.openai.com/account/api-keys
# OPENAI_API_KEY=your-openai-api-key-here

# Anthropic API Key
# Get from: https://console.anthropic.com/
# ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Google API Key (for Gemini)
# Get from: https://makersuite.google.com/app/apikey
# GEMINI_API_KEY=your-google-api-key-here

# Optional: Custom endpoints
# OLLAMA_ENDPOINT=http://localhost:11434
# CUSTOM_API_ENDPOINT=https://your-custom-endpoint.com

# Optional: Other AI provider keys
# COHERE_API_KEY=your-cohere-api-key-here
# REPLICATE_API_TOKEN=your-replicate-token-here
"""

        # Create or overwrite the file
        target_path.write_text(env_content)
        return target_path


# Global instance
env_manager = EnvManager()
