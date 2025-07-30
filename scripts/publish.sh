#!/bin/bash
set -e

echo "🚀 Publishing AI CLI to PyPI..."

# Ensure we're in the project root
cd "$(dirname "$0")/.."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Run quality checks
echo "🔍 Running quality checks..."
uv run pytest --no-cov -x
uv run ruff check src/ai_cli/
uv run ruff format --check src/ai_cli/
uv run mypy src/ai_cli/

# Build the package
echo "📦 Building package..."
uv build

# Check the package
echo "✅ Checking package..."
twine check dist/*

# Upload to PyPI (requires TWINE_USERNAME and TWINE_PASSWORD env vars)
echo "🌐 Uploading to PyPI..."
if [[ "$1" == "--test" ]]; then
    echo "📤 Uploading to Test PyPI..."
    twine upload --repository testpypi dist/*
else
    echo "📤 Uploading to PyPI..."
    twine upload dist/*
fi

echo "🎉 Successfully published AI CLI!"
