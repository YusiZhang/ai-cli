# ai-cli-chat Multi-model AI Chat at the CLI `ai` featuring round-table discussions

[![PyPI version](https://badge.fury.io/py/ai-cli-chat.svg)](https://badge.fury.io/py/ai-cli-chat)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/ai-cli/ai-cli/workflows/Tests/badge.svg)](https://github.com/ai-cli/ai-cli/actions)

A powerful command-line interface for interacting with multiple AI models, featuring round-table discussions where different AI models can collaborate and critique each other's responses.

## ✨ Features

- **🤖 Multi-Model Support**: OpenAI GPT-4, Anthropic Claude, Google Gemini, Ollama (local models)
- **💬 Three Interaction Modes**:
  - **Single Chat**: Quick one-off conversations
  - **Interactive Session**: Multi-turn conversations with history
  - **Round-Table Discussions**: Multiple AI models discussing topics together
- **⚡ Real-time Streaming**: See responses as they're generated
- **🎨 Rich Terminal UI**: Beautiful formatting with markdown support
- **⚙️ Flexible Configuration**: Per-model settings, API key management
- **🔧 Developer Friendly**: Type-safe, well-tested, extensible architecture

## 🚀 Quick Start

### Installation

```bash
pipx install ai-cli-chat
```

### Basic Setup

1. **Configure API Keys** (choose your preferred method):
   ```bash
   ai init
   ```

   This will create `~/.ai-cli/config.toml` and `~/.ai-cli/.env` template
   To get a quick start, fulfill the API key in the `~/.ai-cli/.env` file, i.e
   ```
   OPENAI_API_KEY=xxx
   ```

2. **Verify Setup**:
   ```bash
   ai version
   ai chat "Hello there!"
   ```

### Usage Examples

#### Single Chat
```bash
# Quick question
ai chat "What is machine learning?"

# Use specific model
ai chat --model anthropic/claude-3-sonnet "Explain quantum computing"
```

#### Interactive Session
```bash
# Start interactive mode
ai interactive

# Within interactive mode:
# /help           - Show available commands
# /model gpt-4    - Switch to different model
# /roundtable     - Start round-table discussion
# /exit           - Exit session
```

#### Round-Table Discussions
You need to enable at least two AI model to use this. Or create at least two `models` in the config with the same model provider.
```
[roundtable]
enabled_models = [ "openai/gpt-4", "gemini"]
...

[models."openai/gpt-4"]
provider = "openai"
model = "gpt-4"
...

[models.gemini]
provider = "gemini"
model = "gemini-2.5-flash"
...
```
```bash
# Multiple AI models discuss a topic
ai chat -rt "give me 3 domain name suggestion for a b2c saas that help user to convert their fav newsletter into podcast"

# Parallel responses (all models respond simultaneously)
ai chat --roundtable --parallel "Compare Python vs JavaScript"
```

## 🛠️ Configuration

### Model Management
```bash
# List available models
ai config list

# Add a new model
ai config add-model my-gpt4 \
  --provider openai \
  --model gpt-4 \
  --api-key env:OPENAI_API_KEY

# Set default model
ai config set default_model my-gpt4
```

### Round-Table Setup
```bash
# Add models to round-table discussions
ai config roundtable --add openai/gpt-4
ai config roundtable --add anthropic/claude-3-5-sonnet

# List round-table participants
ai config roundtable --list
```

### Environment Variables
```bash
# Check environment status
ai config env --show

# Create example .env file
ai config env --init
```

## 📋 Supported Models

| Provider | Model | Notes |
|----------|-------|-------|
| OpenAI | gpt-4, gpt-3.5-turbo | Requires `OPENAI_API_KEY` |
| Anthropic | claude-3-sonnet, claude-3-haiku | Requires `ANTHROPIC_API_KEY` |
| Google | gemini-pro | Requires `GEMINI_API_KEY` |
| Ollama | llama2, codellama, etc. | Local models, no API key needed |

## 🔧 Advanced Configuration

The CLI stores configuration in `~/.ai-cli/config.toml`. You can customize:

- **Model Settings**: Temperature, max tokens, context window
- **Round-Table Behavior**: Discussion rounds, critique mode, parallel responses
- **UI Preferences**: Theme, streaming, formatting options

Example configuration:
```toml
default_model = "openai/gpt-4"

[models.openai/gpt-4]
provider = "openai"
model = "gpt-4"
api_key = "env:OPENAI_API_KEY"
temperature = 0.7
max_tokens = 4000

[roundtable]
enabled_models = ["openai/gpt-4", "anthropic/claude-3-sonnet"]
discussion_rounds = 2
parallel_responses = false

[ui]
theme = "dark"
streaming = true
format = "markdown"
```

## 🤝 Round-Table Discussions Explained

Round-table mode is unique to AI CLI. Here's how it works:

1. **Sequential Mode** (default): Models respond one after another, building on previous responses
2. **Parallel Mode** (`--parallel`): All models respond to the original prompt simultaneously
3. **Multiple Rounds**: Configurable discussion rounds for deeper exploration

This creates fascinating conversations where models with different strengths can collaborate, disagree, and build upon each other's ideas.

## 🧪 Development

### Setup
```bash
# Clone repository
git clone https://github.com/ai-cli/ai-cli.git
cd ai-cli

# Install with uv (recommended)
uv sync --extra dev

# Or with pip
pip install -e ".[dev]"
```

### Testing
```bash
# Run tests
uv run pytest

# With coverage
uv run pytest --cov=ai_cli

# Run linting
uv run ruff check src/ai_cli/
uv run ruff format src/ai_cli/
uv run mypy src/ai_cli/
```

### Pre-commit Hooks
```bash
uv run pre-commit install
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 🙏 Acknowledgments

- Built with [Typer](https://typer.tiangolo.com/) for the CLI framework
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- [LiteLLM](https://litellm.ai/) for universal model access
- Inspired by the need for collaborative AI conversations

## 📚 Documentation

For detailed documentation, architecture details, and extension guides, see [CLAUDE.md](CLAUDE.md).
