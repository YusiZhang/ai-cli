# Quick Start Guide for Example Configurations

## How to Use These Examples

### 1. Choose Your Configuration
Pick an example that matches your use case:

- **Basic discussions**: `basic-roundtable.toml`
- **Domain brainstorming**: `domain-brainstorming.toml`
- **Code review**: `code-review.toml`
- **Creative writing**: `creative-writing.toml`
- **Research analysis**: `research-analysis.toml`
- **Problem solving**: `problem-solving.toml`
- **Formal debates**: `debate-format.toml`

### 2. Copy Configuration Sections

Copy the relevant sections from the example file to your `~/.ai-cli/config.toml`:

```bash
# View your current config
ai config list

# Check your config file location
ls ~/.ai-cli/config.toml
```

### 3. Update Model Names

Make sure the model names in the example match your configured models:

```bash
# See your configured models
ai config list

# Update model names in the config file if needed
```

### 4. Test the Configuration

```bash
# Check roundtable settings
ai config roundtable --list

# Test with a simple prompt
ai chat --roundtable "Test the configuration with this simple prompt"
```

## Quick Commands for Role Management

```bash
# Enable role-based prompting
ai config roundtable --enable-roles

# Assign specific roles to a model
ai config roles --model "openai/gpt-4" --assign "generator,critic"

# View role assignments
ai config roles --list

# Clear role assignments (allow all roles)
ai config roles --clear "openai/gpt-4"

# See available roles
ai config roles --list-roles
```

## Tips for Best Results

1. **Start Simple**: Begin with `basic-roundtable.toml` to test your setup
2. **Adjust Timeouts**: Increase timeout for complex topics (60-90 seconds)
3. **Model Selection**: Use 2-3 models for focused discussions, 4+ for comprehensive analysis
4. **Role Assignment**: Match model strengths to roles (e.g., Claude for creative content)
5. **Discussion Rounds**: 2-3 rounds for quick topics, 4-5 for complex analysis

## Common Use Cases

### Domain Name Brainstorming
```bash
# Copy domain-brainstorming.toml settings
ai chat --roundtable "I need domain names for a sustainable food delivery app"
```

### Code Review
```bash
# Copy code-review.toml settings
ai chat --roundtable "Review this Python function: [paste code here]"
```

### Creative Writing
```bash
# Copy creative-writing.toml settings
ai chat --roundtable "Write a compelling product description for smart home devices"
```

### Problem Solving
```bash
# Copy problem-solving.toml settings
ai chat --roundtable "How can we improve team communication in a distributed company?"
```

## Troubleshooting

### Models Not Responding
- Check API keys: `ai config env --show`
- Verify model names: `ai config list`
- Increase timeout: Edit `timeout_seconds` in config

### Role Assignment Issues
- Check role syntax: `ai config roles --list-roles`
- Verify model exists: `ai config list`
- Clear and reassign: `ai config roles --clear "model-name"`

### Configuration Problems
- Validate TOML syntax in your config file
- Check file permissions on `~/.ai-cli/config.toml`
- Restart CLI after major config changes
