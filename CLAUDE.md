# AI CLI Project Documentation

## Do and DON'ts
1. DO NOT modify ~/.ai-cli/config.toml file unless you asked me for permission
2. DO run `uv run pre-commit` before you wrap up your task

## Pitfall
1. Gemini model api key should use environment var name "GEMINI_API_KEY", NOT "GOOGLE_API_KEY"

## Project Overview

This is a multi-model AI CLI tool that provides three main interaction modes:
1. **Single Chat**: One-off conversations with a selected AI model
2. **Interactive Chat**: Multi-turn conversations in an interactive session
3. **Round-table Discussion**: Multiple AI models discussing and critiquing each other's responses

The project is built in Python using modern async patterns and provides a rich terminal experience with streaming responses, configurable models, and comprehensive CLI commands.

## Architecture

### Core Components

#### 1. CLI Layer (`ai_cli/cli.py`)
- **Technology**: Typer for CLI framework
- **Purpose**: Command-line interface and argument parsing
- **Key Commands**:
  - `ai chat "prompt"` - Single chat mode
  - `ai chat --roundtable "prompt"` - Round-table discussion
  - `ai interactive` - Interactive session
  - `ai config` - Configuration management

#### 2. Chat Engine (`ai_cli/core/chat.py`)
- **Purpose**: Core business logic for handling conversations
- **Features**:
  - Single model chat with streaming
  - Round-table discussions (sequential/parallel)
  - Rich terminal output with markdown support
  - Conversation context management

#### 3. Configuration System (`ai_cli/config/`)
- **Models** (`models.py`): Pydantic models for type-safe configuration
- **Manager** (`manager.py`): Configuration persistence and management
- **Features**:
  - TOML-based configuration files
  - Environment variable resolution
  - Model-specific settings (temperature, tokens, etc.)
  - Round-table discussion settings

#### 4. Provider Abstraction (`ai_cli/providers/`)
- **Base** (`base.py`): Abstract provider interface
- **LiteLLM Provider** (`litellm_provider.py`): Universal model access via LiteLLM
- **Factory** (`factory.py`): Provider creation and caching

#### 5. Interactive UI (`ai_cli/ui/`)
- **Interactive Session** (`interactive.py`): Multi-turn conversation interface
- **Streaming Display** (`streaming.py`): Real-time response streaming
- **Features**:
  - Command completion
  - History management
  - Model switching
  - Help system

#### 6. Utilities (`ai_cli/utils/`)
- **Environment Management** (`env.py`): API key and environment variable handling

## Configuration

### Default Models
The CLI comes pre-configured with these models:
- **OpenAI GPT-4**: `openai/gpt-4`
- **Anthropic Claude 3 Sonnet**: `anthropic/claude-3-sonnet`
- **Ollama Llama2**: `ollama/llama2` (local)

### Configuration Location
- User config file: `~/.ai-cli/config.toml`
- User environment file: `~/.ai-cli/.env` or current directory `.env`

### API Key Setup
API keys are referenced via environment variables:
```bash
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here
GOOGLE_API_KEY=your-key-here
```

## Development

### Testing Strategy
- **Unit Tests**: Core components (ChatEngine, ConfigManager, Models)
- **Integration Tests**: CLI commands and workflows
- **Test Framework**: pytest with asyncio support
- **Coverage**: Targeting 80%+ code coverage
- **Fixtures**: Comprehensive test fixtures for mocking

### Code Quality
- **Linting & Formatting**: Ruff for fast Python linting and code formatting
- **Type Checking**: MyPy for static type analysis
- **Pre-commit Hooks**: Automated quality checks

### Project Structure
```
ai_cli/
├── cli.py              # Main CLI entry point
├── config/
│   ├── __init__.py
│   ├── manager.py      # Configuration management
│   └── models.py       # Pydantic configuration models
├── core/
│   ├── __init__.py
│   ├── chat.py         # Core chat engine
│   └── messages.py     # Message data structures
├── providers/
│   ├── __init__.py
│   ├── base.py         # Abstract provider interface
│   ├── factory.py      # Provider factory
│   └── litellm_provider.py  # LiteLLM implementation
├── ui/
│   ├── __init__.py
│   ├── interactive.py  # Interactive chat session
│   └── streaming.py    # Streaming response display
└── utils/
    ├── __init__.py
    └── env.py          # Environment management
```

## Usage Examples

### Single Chat
```bash
# Basic chat
ai chat "What is machine learning?"

# With specific model
ai chat --model anthropic/claude-3-sonnet "Explain quantum computing"
```

### Interactive Mode
```bash
# Start interactive session
ai interactive

# Commands within interactive mode:
/help           # Show help
/model gpt-4    # Switch model
/roundtable     # Start roundtable discussion
/exit           # Exit session
```

### Round-table Discussion
```bash
# Sequential discussion
ai chat --roundtable "What are the pros and cons of AI?"

# Parallel responses
ai chat --roundtable --parallel "Compare different programming languages"
```

### Configuration Management
```bash
# List configured models
ai config list

# Add new model
ai config add-model my-model --provider openai --model gpt-4 --api-key env:MY_API_KEY

# Configure round-table
ai config roundtable --add my-model

# Environment setup
ai config env --init    # Create example .env file
ai config env --show    # Show current environment status
```

## Key Features

### Round-table Discussions
- **Sequential Mode**: Models respond one after another, building on previous responses
- **Parallel Mode**: All models respond simultaneously to the original prompt
- **Critique Mode**: Later models can critique earlier responses
- **Configurable Rounds**: Multiple discussion rounds for deeper exploration

### Streaming Responses
- Real-time response streaming for better user experience
- Rich terminal formatting with markdown support
- Progress indicators for long operations

### Flexible Configuration
- Support for multiple AI providers (OpenAI, Anthropic, Ollama, Gemini)
- Per-model configuration (temperature, max tokens, endpoints)
- Environment-based API key management
- TOML-based configuration files

### Developer Experience
- Comprehensive test coverage
- Type-safe configuration with Pydantic
- Modern async/await patterns
- Rich error handling and user feedback

## Extension Points

### Adding New Providers
1. Inherit from `AIProvider` base class
2. Implement `chat_stream()` and `validate_config()` methods
3. Register in the provider factory

### Adding New Commands
1. Add command functions to `cli.py`
2. Follow existing patterns for async execution
3. Add comprehensive tests

### Adding New Configuration Options
1. Update Pydantic models in `config/models.py`
2. Update configuration manager serialization
3. Add CLI commands for new options

## Testing

### Running Tests
```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/test_chat_engine.py

# With coverage
uv run pytest --cov=ai_cli --cov-report=html
```

### Pre-commit Hooks
```bash
# Install hooks
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

### Code Quality
```bash
# Linting
uv run ruff check ai_cli/ tests/

# Formatting
uv run ruff format ai_cli/ tests/

# Type checking
uv run mypy ai_cli/
```

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Check environment variables are set
   - Verify .env file location and format
   - Use `ai config env --show` to debug

2. **Model Not Available**
   - Verify model configuration: `ai config list`
   - Check API key for the model's provider
   - Ensure model name is correct

3. **Round-table Not Working**
   - Need at least 2 models enabled: `ai config roundtable --list`
   - Add models: `ai config roundtable --add model-name`

4. **Import Errors**
   - Ensure all dependencies installed: `uv sync`
   - Check Python version (>=3.9 required)

### Debug Mode
Add verbose logging by setting environment variable:
```bash
export AI_CLI_DEBUG=1
```

## Future Enhancements

### Potential Extensions
- Web interface for non-terminal users
- Plugin system for custom providers
- Conversation templates and workflows
- Integration with external tools and APIs
