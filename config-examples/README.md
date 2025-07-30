# Example Configurations

This directory contains example configurations demonstrating different roundtable patterns for various use cases.

## Usage

1. Choose an example configuration that matches your use case
2. Copy the relevant sections to your `~/.ai-cli/config.toml` file
3. Ensure you have the required models configured and API keys set up
4. Test the configuration with `ai config roundtable --list`

## Example Files

### Basic Configurations
- [`basic-roundtable.toml`](./basic-roundtable.toml) - Simple two-model roundtable
- [`multi-model-roundtable.toml`](./multi-model-roundtable.toml) - Four-model collaborative discussion

### Role-Based Configurations
- [`domain-brainstorming.toml`](./domain-brainstorming.toml) - Specialized roles for domain name brainstorming
- [`code-review.toml`](./code-review.toml) - Code review and improvement workflow
- [`creative-writing.toml`](./creative-writing.toml) - Creative content generation and refinement

### Specialized Workflows
- [`research-analysis.toml`](./research-analysis.toml) - Research methodology with multiple perspectives
- [`problem-solving.toml`](./problem-solving.toml) - Structured problem-solving approach
- [`debate-format.toml`](./debate-format.toml) - Formal debate structure
- [`mixed-templates.toml`](./mixed-templates.toml) - Demonstrates mixed custom/default template usage

## Model Requirements

Most examples assume you have these models configured:
- `openai/gpt-4` - OpenAI GPT-4
- `anthropic/claude-3-5-sonnet` - Anthropic Claude 3.5 Sonnet
- `gemini` - Google Gemini
- `ollama/llama3` - Local Llama3 via Ollama

Adjust model names according to your specific configuration.

## Customization Tips

1. **Role Assignments**: Modify role assignments based on model strengths
2. **Discussion Rounds**: Adjust the number of rounds for your use case
3. **Custom Templates**: Add custom role templates for domain-specific prompting
4. **Timeout Settings**: Increase timeout for complex discussions

## Template Fallback Behavior

The AI CLI supports **mixed template configurations** where you can provide custom templates for some roles while others automatically use built-in defaults:

### Example: Partial Custom Templates
```toml
[roundtable.role_assignments]
"gpt-4" = ["generator", "refiner"]
"claude" = ["critic", "evaluator"]

[roundtable.custom_role_templates]
generator = "Custom generator template..."
critic = "Custom critic template..."
# refiner and evaluator will use default templates
```

In this example:
- **Generator** and **Critic** use your custom templates
- **Refiner** and **Evaluator** automatically fall back to built-in default templates
- All four roles work seamlessly together in discussions

### Benefits
- **Flexibility**: Customize only the roles you care about most
- **Gradual adoption**: Start with default templates and customize incrementally
- **No gaps**: Declared roles always work, even without custom templates
- **Consistency**: Default templates provide reliable baseline behavior

See `mixed-templates.toml` for a complete working example.

### Managing Templates via CLI

You can manage custom role templates using the CLI:

```bash
# List all custom templates
ai config templates --list

# Show default templates for all roles
ai config templates --show-defaults

# Set custom template for a role
ai config templates --role generator --set "Your custom template..."

# Load template from file
ai config templates --role critic --file my-template.txt

# Clear custom template (falls back to default)
ai config templates --clear refiner
```

## Contributing

If you create useful roundtable configurations, consider contributing them back to this collection!
