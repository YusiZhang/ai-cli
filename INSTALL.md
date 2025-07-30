# Installation and Testing Guide

## Installation Options

### From PyPI (Recommended)
```bash
pip install ai-cli-chat
```

### From Source
```bash
git clone https://github.com/ai-cli/ai-cli.git
cd ai-cli
uv sync --extra dev
uv tool install .
```

### Development Installation
```bash
git clone https://github.com/ai-cli/ai-cli.git
cd ai-cli
uv sync --extra dev
```

## Verification

### Check Installation
```bash
ai --help
ai version
```

### Quick Test
```bash
# Without API keys (will show configuration help)
ai config list

# With API keys
export OPENAI_API_KEY="your-key"
ai chat "Hello, world!"
```

## Package Testing

### Local Package Testing
```bash
# Build the package
uv build

# Install locally for testing
pip install --user dist/ai_cli-*.whl

# Test the installation
ai --help
```

### Publishing to Test PyPI
```bash
# Install publishing dependencies
pip install twine

# Set credentials
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="your-test-pypi-token"

# Publish to test PyPI
./scripts/publish.sh --test

# Test installation from test PyPI
pip install --index-url https://test.pypi.org/simple/ ai-cli
```

### Publishing to PyPI
```bash
# Set production credentials
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="your-pypi-token"

# Publish to production PyPI
./scripts/publish.sh
```

## Dependencies

### Runtime Dependencies
- Python 3.9+
- typer>=0.9.0
- rich>=13.7.0
- prompt-toolkit>=3.0.0
- questionary>=2.0.0
- pydantic>=2.5.0
- pydantic-settings>=2.1.0
- httpx>=0.25.0
- litellm>=1.17.0
- toml>=0.10.0

### Development Dependencies
- pytest>=7.0
- pytest-asyncio>=0.21
- pytest-cov>=4.0
- pytest-mock>=3.10
- black>=23.0
- ruff>=0.1.0
- mypy>=1.0
- pre-commit>=3.0

## Troubleshooting

### Package Build Issues
```bash
# Clean build artifacts
rm -rf dist/ build/ *.egg-info/

# Rebuild
uv build
```

### Installation Issues
```bash
# Upgrade pip
pip install --upgrade pip

# Clear pip cache
pip cache purge

# Install with verbose output
pip install -v ai-cli
```

### Testing Issues
```bash
# Run specific test
uv run pytest tests/test_cli.py -v

# Run with full output
uv run pytest -s -v
```
