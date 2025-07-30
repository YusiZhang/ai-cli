# AI CLI Installation Guide

A complete guide for installing and setting up the AI CLI for end users.

## 📋 System Requirements

- **Python 3.9 or later**
- **Internet connection** (for API calls)
- **10-20 MB disk space**
- **API keys** for desired AI providers (OpenAI, Anthropic, etc.)

## 🚀 Installation Options

### Option 1: Install with pip (Recommended)

```bash
pip install ai-cli-chat
```

### Option 2: Install with pipx (Best for CLI tools)

```bash
# Install pipx if you don't have it
pip install pipx

# Install AI CLI with pipx
pipx install ai-cli-chat
```

### Option 3: Install in Virtual Environment

```bash
# Create and activate virtual environment
python -m venv ai-env
source ai-env/bin/activate  # On Windows: ai-env\Scripts\activate

# Install AI CLI
pip install ai-cli-chat
```

## ✅ Verify Installation

```bash
# Check if installation was successful
ai --help

# Check version
ai version
```

Expected output:
```
AI CLI version 0.1.0
Multi-model AI CLI with round-table discussions
```

## 🔧 Initial Setup

### Step 1: Create Configuration

```bash
# Create example .env file with API key placeholders
ai config env --init
```

This creates `~/.ai-cli/.env` with:
```env
# OpenAI API Key
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your-openai-key-here

# Anthropic API Key
# Get from: https://console.anthropic.com/
ANTHROPIC_API_KEY=your-anthropic-key-here

# Google API Key
# Get from: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your-google-key-here
```

### Step 2: Add Your API Keys

Choose one of these methods:

#### Method A: Edit .env file (Recommended)
```bash
# Edit the generated .env file
nano ~/.ai-cli/.env
# Or use your preferred editor
code ~/.ai-cli/.env
```

Replace the placeholder values with your actual API keys:
```env
OPENAI_API_KEY=sk-your-actual-openai-key-here
ANTHROPIC_API_KEY=your-actual-anthropic-key-here
GOOGLE_API_KEY=your-actual-google-key-here
```

#### Method B: Set Environment Variables
```bash
export OPENAI_API_KEY="sk-your-actual-openai-key"
export ANTHROPIC_API_KEY="your-actual-anthropic-key"
export GOOGLE_API_KEY="your-actual-google-key"
```

#### Method C: Project-specific .env file
```bash
# Create .env in your current project directory
ai config env --init --path ./.env
```

### Step 3: Verify Setup

```bash
# Check environment status
ai config env --show

# List available models
ai config list
```

## 🎯 First Usage

### Quick Chat
```bash
# Simple question with default model
ai chat "What is machine learning?"

# Use specific model
ai chat --model anthropic/claude-3-sonnet "Explain quantum computing"
```

### Interactive Session
```bash
# Start interactive mode
ai interactive

# Available commands in interactive mode:
# /help           - Show available commands
# /model gpt-4    - Switch to different model
# /models         - List available models
# /roundtable     - Start round-table discussion
# /clear          - Clear conversation history
# /exit           - Exit session
```

### Round-Table Discussions
```bash
# First, add models to round-table
ai config roundtable --add openai/gpt-4
ai config roundtable --add anthropic/claude-3-sonnet

# Start a round-table discussion
ai chat --roundtable "What are the pros and cons of remote work?"

# Parallel responses (all models respond simultaneously)
ai chat --roundtable --parallel "Compare Python vs JavaScript"
```

## 🛠️ Configuration

### View Current Configuration
```bash
ai config list
```

### Add New Models
```bash
# Add OpenAI model with custom settings
ai config add-model my-gpt4 \
  --provider openai \
  --model gpt-4-turbo \
  --api-key env:OPENAI_API_KEY \
  --temperature 0.3 \
  --max-tokens 8000

# Add local Ollama model (no API key needed)
ai config add-model local-llama \
  --provider ollama \
  --model llama2 \
  --endpoint http://localhost:11434
```

### Set Default Model
```bash
ai config set default_model anthropic/claude-3-sonnet
```

### Manage Round-Table Participants
```bash
# List current round-table models
ai config roundtable --list

# Add model to round-table
ai config roundtable --add my-gpt4

# Remove model from round-table
ai config roundtable --remove ollama/llama2
```

## 🔑 Getting API Keys

### OpenAI
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign up or log in
3. Create a new API key
4. Copy the key (starts with `sk-`)

### Anthropic
1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Generate an API key
4. Copy the key

### Google (Gemini)
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign up or log in
3. Create an API key
4. Copy the key

### Ollama (Local Models)
1. Install [Ollama](https://ollama.ai/)
2. Pull a model: `ollama pull llama2`
3. No API key needed - runs locally!

## 📱 Complete User Journey Example

```bash
# 1. Install
$ pip install ai-cli-chat
Successfully installed ai-cli-chat-1.0.0

# 2. Verify installation
$ ai --help
Usage: ai [OPTIONS] COMMAND [ARGS]...
  Multi-model AI CLI with round-table discussions

# 3. Initial setup
$ ai config env --init
✓ Created example .env file: /Users/john/.ai-cli/.env
Edit the file and add your API keys

# 4. Edit .env file (add real API keys)
$ nano ~/.ai-cli/.env

# 5. Verify setup
$ ai config env --show
🔐 Environment Variable Status
✅ OPENAI_API_KEY: sk-abc123...
✅ ANTHROPIC_API_KEY: sk-ant-api...

# 6. List available models
$ ai config list
📋 Configured Models
⭐ 🔄 openai/gpt-4 (openai: gpt-4)
   🔄 anthropic/claude-3-sonnet (anthropic: claude-3-sonnet-20240229)

# 7. First chat
$ ai chat "Hello! How do you work?"
🤖 openai/gpt-4 (openai)
Hello! I'm an AI assistant...

# 8. Interactive session
$ ai interactive
🤖 AI Interactive Session
Type '/help' for commands or '/exit' to quit

🤖 ai> What's 2+2?
🤖 openai/gpt-4 (openai)
2 + 2 equals 4.

🤖 ai> /model anthropic/claude-3-sonnet
✓ Switched from openai/gpt-4 to anthropic/claude-3-sonnet

🤖 ai> /exit
Goodbye! 👋

# 9. Round-table discussion
$ ai chat --roundtable "What makes a good programming language?"
🎯 Round-Table Discussion
Models: openai/gpt-4, anthropic/claude-3-sonnet

[Models discuss and build on each other's responses]
```

## 🔧 Advanced Configuration

### Custom Model Settings
```bash
# Create a model optimized for coding
ai config add-model code-assistant \
  --provider openai \
  --model gpt-4 \
  --temperature 0.1 \
  --max-tokens 4000

# Create a model for creative writing
ai config add-model creative-writer \
  --provider anthropic \
  --model claude-3-sonnet \
  --temperature 0.9 \
  --max-tokens 8000
```

### Environment-Specific Configurations
```bash
# Work environment
export AI_CLI_DEFAULT_MODEL="code-assistant"

# Personal projects
export AI_CLI_DEFAULT_MODEL="creative-writer"
```

### Configuration File Location
The configuration is stored in: `~/.ai-cli/config.toml`

You can edit this file directly for advanced customization:
```toml
default_model = "openai/gpt-4"

[models."openai/gpt-4"]
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

## 🚨 Troubleshooting

### Installation Issues

#### Python Version Issues
```bash
# Check Python version
python --version

# If using Python 3.9+, try:
python -m pip install ai-cli-chat
```

#### Permission Issues
```bash
# Use --user flag
pip install --user ai-cli

# Or use pipx
pipx install ai-cli-chat
```

#### Package Not Found
```bash
# Update pip
pip install --upgrade pip

# Clear cache and retry
pip cache purge
pip install ai-cli-chat
```

### Configuration Issues

#### API Key Not Working
```bash
# Check environment status
ai config env --show

# Verify API key format
# OpenAI keys start with: sk-
# Anthropic keys start with: sk-ant-api
```

#### Models Not Loading
```bash
# Reset configuration
rm ~/.ai-cli/config.toml
ai config list  # Will regenerate defaults

# Check specific model
ai chat "test" --model openai/gpt-4
```

#### Network Issues
```bash
# Test connectivity
curl -I https://api.openai.com/v1/models

# For Ollama (local)
curl http://localhost:11434/api/tags
```

### Runtime Issues

#### Import Errors
```bash
# Reinstall dependencies
pip install --upgrade ai-cli-chat

# Or reinstall completely
pip uninstall ai-cli-chat
pip install ai-cli-chat
```

#### Slow Responses
This is normal for AI APIs. You can:
- Use streaming mode (enabled by default)
- Reduce max_tokens in model settings
- Use faster models (e.g., gpt-3.5-turbo)

## 🆘 Getting Help

### Built-in Help
```bash
ai --help                    # General help
ai chat --help              # Chat command help
ai config --help            # Configuration help
ai interactive --help       # Interactive mode help
```

### Documentation
- [Main Documentation](CLAUDE.md) - Complete project documentation
- [README.md](README.md) - Quick start guide
- [GitHub Issues](https://github.com/ai-cli/ai-cli/issues) - Report bugs

### Community
- Report issues on GitHub
- Check existing issues for solutions
- Contribute improvements via pull requests

## 🎉 You're Ready!

Once you've completed these steps, you can:

- ✅ Chat with multiple AI models
- ✅ Run interactive sessions
- ✅ Host round-table discussions
- ✅ Switch models on the fly
- ✅ Customize configurations
- ✅ Integrate into your workflow

Happy chatting! 🤖
