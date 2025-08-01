# ai-cli-chat Multi-model AI Chat at the CLI `ai` featuring round-table discussions

[![PyPI version](https://badge.fury.io/py/ai-cli-chat.svg)](https://badge.fury.io/py/ai-cli-chat)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/ai-cli/ai-cli/workflows/Tests/badge.svg)](https://github.com/ai-cli/ai-cli/actions)

A powerful command-line interface for interacting with multiple AI models, featuring round-table discussions where different AI models can collaborate and critique each other's responses.

## 🚀 Quick Start

### Installation

```bash
pipx install ai-cli-chat
```

### Basic Setup

**Configure API Keys** (choose your preferred method):
   ```bash
   ai init
   ```

   This will create `~/.ai-cli/config.toml` and `~/.ai-cli/.env` template
   To get a quick start, fulfill the API key in the `~/.ai-cli/.env` file, i.e
   ```
   OPENAI_API_KEY=xxx
   ```

**Verify Setup**:
   ```bash
   ai version
   ai chat "Hello there!"
   ```

## ✨ Features

- **🤖 Multi-Model Support**: OpenAI GPT-4, Anthropic Claude, Google Gemini, Ollama (local models)
- **💬 Three Interaction Modes**:
  - **Single Chat**: Quick one-off conversations
  - **Interactive Session**: Multi-turn conversations with history
  - **Round-Table Discussions**: Multiple AI models discussing topics together
- **⚡ Real-time Streaming**: See responses as they're generated
- **🎨 Rich Terminal UI**: Beautiful formatting with markdown support
- **⚙️ Flexible Configuration**: Per-model settings, API key management

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
The roundtable uses a role-based system where different roles (generator, critic, refiner, evaluator) can be assigned to different models or use a single model for all roles.
```
[roundtable]
# Enable specific roles (defaults to all roles)
enabled_roles = ["generator", "critic", "refiner"]
# Map roles to specific models
[roundtable.role_model_mapping]
generator = "openai/gpt-4"
critic = "gemini"
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

## 📄 Template Configurations

The project includes several pre-built configuration templates in `config-examples/` for common use cases:

### Available Templates
- **basic-roundtable.toml** - Simple two-model collaborative discussion
- **multi-model-roundtable.toml** - Complex discussions with multiple models and roles
- **creative-writing.toml** - Optimized for creative writing and storytelling
- **code-review.toml** - Technical code review and programming discussions
- **research-analysis.toml** - Academic research and analytical tasks
- **debate-format.toml** - Structured debates between models
- **problem-solving.toml** - Collaborative problem-solving sessions

### Using Templates
```bash
# Method 1: Copy a template to your config directory
cp config-examples/basic-roundtable.toml ~/.ai-cli/config.toml

# Method 2: Initialize base config then customize
ai init
ai config roundtable --add openai/gpt-4
ai config roundtable --add anthropic/claude-3-5-sonnet
```

### Role-based Configuration Example
```toml
[roundtable]
# Enable specific roles (defaults to all roles if not specified)
enabled_roles = ["generator", "critic", "refiner", "evaluator"]
# Map roles to specific models
[roundtable.role_model_mapping]
generator = "openai/gpt-4"
critic = "anthropic/claude-3-5-sonnet"
refiner = "gemini"
discussion_rounds = 3

# Optional: Restrict which roles specific models can play
# System uses 4 predefined roles: generator, critic, refiner, evaluator
[roundtable.role_assignments]
"openai/gpt-4" = ["generator", "refiner"]  # Best for creative generation
"anthropic/claude-3-5-sonnet" = ["critic", "evaluator"]  # Best for analysis

[models."openai/gpt-4"]
provider = "openai"
model = "gpt-4"
api_key = "env:OPENAI_API_KEY"
temperature = 0.8  # Higher creativity for generation tasks

[models."anthropic/claude-3-5-sonnet"]
provider = "anthropic"
model = "claude-3-5-sonnet"
api_key = "env:ANTHROPIC_API_KEY"
temperature = 0.3  # Lower temperature for critical analysis

[models.gemini]
provider = "gemini"
model = "gemini-2.0-flash-thinking-exp"
api_key = "env:GEMINI_API_KEY"
# No role restrictions - can play any of the 4 roles
```

## 📋 Supported Models

| Provider | Model | Notes |
|----------|-------|-------|
| OpenAI | gpt-4, gpt-3.5-turbo | Requires `OPENAI_API_KEY` |
| Anthropic | claude-3-5-sonnet, claude-3-haiku | Requires `ANTHROPIC_API_KEY` |
| Google | gemini-pro | Requires `GEMINI_API_KEY` |
| Ollama | llama2, codellama, etc. | Local models, no API key needed |

## 🔧 Advanced Configuration

The CLI stores configuration in `~/.ai-cli/config.toml`. You can customize:

- **Model Settings**: Temperature, max tokens, context window, API endpoints
- **Round-Table Behavior**: Discussion rounds, role-based prompting, parallel responses
- **UI Preferences**: Theme, streaming, formatting, model icons
- **Role Assignments**: Which models can play which of the 4 predefined roles

### Complete Configuration Example
```toml
default_model = "openai/gpt-4"

# Individual model configurations
[models."openai/gpt-4"]
provider = "openai"
model = "gpt-4"
api_key = "env:OPENAI_API_KEY"
temperature = 0.7
max_tokens = 4000
timeout_seconds = 30

[models."anthropic/claude-3-5-sonnet"]
provider = "anthropic"
model = "claude-3-5-sonnet"
api_key = "env:ANTHROPIC_API_KEY"
temperature = 0.8
max_tokens = 8000

# Additional model configurations
[models."gemini/gemini-pro"]
provider = "gemini"
model = "gemini-pro"
api_key = "env:GEMINI_API_KEY"
temperature = 0.7
max_tokens = 4000

# Round-table configuration
[roundtable]
# All roles enabled by default, or specify which ones to use
enabled_roles = ["generator", "critic", "refiner", "evaluator"]
# Option 1: Map roles to specific models
[roundtable.role_model_mapping]
generator = "openai/gpt-4"
critic = "anthropic/claude-3-5-sonnet"
# Option 2: Use one model for all roles
# solo_model = "openai/gpt-4"
discussion_rounds = 3
parallel_responses = false
use_role_based_prompting = true
role_rotation = true
timeout_seconds = 60

# UI customization
[ui]
theme = "dark"
streaming = true
format = "markdown"
show_model_icons = true
```

### Configuration Sections Explained

**Model Settings:**
- `temperature`: Creativity level (0.0-2.0)
- `max_tokens`: Response length limit
- `provider`: AI provider (openai, anthropic, gemini, ollama)
- `model`: Specific model name
- `api_key`: API key (can use env: prefix)
- `endpoint`: Custom API endpoint (optional)

**Round-table Options:**
- `use_role_based_prompting`: Enable specialized roles
- `role_rotation`: Models switch roles between rounds
- `discussion_rounds`: Number of conversation rounds

**UI Customization:**
- `show_model_icons`: Display model indicators

## 🤝 Round-Table Discussions Explained

Round-table mode is the **unique selling point** of AI CLI, featuring advanced **role-based prompting** that goes beyond simple multi-model chat:

### Core Features
1. **Sequential Mode** (default): Models respond one after another, building on previous responses
2. **Parallel Mode** (`--parallel`): All models respond to the original prompt simultaneously
3. **Role-based Prompting**: Automatic assignment of 4 predefined roles (generator, critic, refiner, evaluator)
4. **Multiple Rounds**: Configurable discussion rounds for deeper exploration
5. **Role Rotation**: Models can switch roles between rounds for diverse perspectives

### Role-based Prompting Examples

**Two-Model Roundtable (Sequential Roles):**
```bash
ai chat --roundtable "How can we reduce customer churn in our SaaS product?"
# Round 1: GPT-4 (Generator) creates initial suggestions
# Round 1: Claude (Critic) analyzes and critiques GPT-4's suggestions
# Round 2: Claude (Refiner) improves the suggestions
# Round 2: GPT-4 (Critic) provides final critique
```

**Multi-Model Roundtable (All 4 Roles):**
```bash
ai chat --roundtable "Design a comprehensive social media strategy"
# Round 1: Models A&B (Generators) create different strategy approaches
# Round 1: Models C&D (Critics) analyze and identify issues
# Round 2: Models A&B (Refiners) improve strategies based on critiques
# Round 3: Model A (Evaluator) ranks all strategies and provides final recommendation
```

**Role Rotation in Action:**
```bash
ai chat --roundtable "Compare Python vs JavaScript for web development"
# GPT-4 starts as Generator → becomes Critic in round 2
# Claude starts as Critic → becomes Refiner in round 2
# System automatically rotates roles to get diverse perspectives
```

### Why Role-based Round-tables?
- **Structured Discussions**: 4 predefined roles (generator, critic, refiner, evaluator) create organized conversations
- **Quality Improvement**: Iterative critique and refinement process enhances initial ideas
- **Multiple Perspectives**: Role rotation ensures models approach problems from different angles
- **Automatic Workflow**: System handles role assignment and prompt templating automatically
- **Reduced Bias**: Multiple models and roles minimize single-perspective limitations

This creates **structured collaborative discussions** where models systematically generate, critique, refine, and evaluate ideas - **like having a well-organized brainstorming session with clear roles**.

### How Role-based Prompting Works
**Implementation details:**
- **Role Templates**: Hardcoded prompt templates for the 4 roles (generator, critic, refiner, evaluator)
- **Automatic Assignment**: System automatically assigns roles to models based on round and model count
- **No Custom System Prompts**: Individual models cannot have custom system prompts in configuration
- **Role Behavior**: Each role uses its predefined template from the `RolePromptTemplates` class

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

### Project Structure
```
ai-cli/
├── src/ai_cli/                 # Main package source
│   ├── __init__.py            # Package initialization
│   ├── cli.py                 # CLI entry point and commands
│   ├── config/                # Configuration management
│   │   ├── manager.py         # Config file handling
│   │   └── models.py          # Pydantic data models
│   ├── core/                  # Core business logic
│   │   ├── chat.py           # Chat engine and round-table logic
│   │   ├── messages.py       # Message data structures
│   │   └── roles.py          # Role-based prompting system
│   ├── providers/            # AI provider abstractions
│   │   ├── base.py          # Abstract provider interface
│   │   ├── factory.py       # Provider factory pattern
│   │   └── litellm_provider.py  # LiteLLM implementation
│   ├── ui/                  # User interface components
│   │   ├── interactive.py   # Interactive chat session
│   │   └── streaming.py     # Real-time response streaming
│   └── utils/               # Utility functions
│       └── env.py           # Environment variable handling
├── tests/                   # Test suite
├── config-examples/         # Template configurations
├── features-doc/           # Feature documentation
├── pyproject.toml          # Project configuration
└── README.md              # This file
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
