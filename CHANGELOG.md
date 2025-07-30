# Changelog

All notable changes to AI CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-07-26

### Added
- Initial release of AI CLI
- Multi-model support for OpenAI, Anthropic, Google Gemini, and Ollama
- Three interaction modes: single chat, interactive session, and round-table discussions
- Real-time streaming responses with rich terminal UI
- Comprehensive configuration system with TOML files
- Environment variable support for API keys
- Round-table discussions with sequential and parallel modes
- Interactive session with command completion and history
- CLI commands for configuration management
- Type-safe configuration with Pydantic models
- Comprehensive test suite with 69+ tests
- Pre-commit hooks for code quality
- Full documentation and project context

### Features
- **Chat Modes**:
  - `ai chat "prompt"` - Single chat with any configured model
  - `ai interactive` - Multi-turn interactive session
  - `ai chat --roundtable "prompt"` - Multiple models discussing together

- **Configuration**:
  - `ai config list` - View all configured models
  - `ai config add-model` - Add new AI models
  - `ai config roundtable` - Manage round-table participants
  - `ai config env` - Environment and API key management

- **Interactive Commands**:
  - `/help` - Show available commands
  - `/model <name>` - Switch between models
  - `/roundtable <prompt>` - Start round-table discussion
  - `/exit` - Exit interactive session

- **Supported Providers**:
  - OpenAI (GPT-4, GPT-3.5-turbo)
  - Anthropic (Claude-3-sonnet, Claude-3-haiku)
  - Google (Gemini-pro)
  - Ollama (Local models: llama2, codellama, etc.)

- **Quality Assurance**:
  - 69 comprehensive tests covering all core functionality
  - Pre-commit hooks with ruff (linting and formatting) and mypy
  - Type-safe codebase with strict mypy configuration
  - 80%+ test coverage

### Technical Details
- Built with Python 3.9+ using modern async/await patterns
- Rich terminal UI with markdown support and streaming
- LiteLLM for universal model access
- Pydantic for type-safe configuration
- Typer for CLI framework
- pytest for comprehensive testing
