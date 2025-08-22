# Release Notes - v1.2.0

## 🚀 New Features

### **Enhanced Response Copying with `ai cp` Command**
A powerful new feature that allows users to easily copy AI responses to their clipboard with interactive selection capabilities.

#### ✨ Key Features:
- **`ai cp`**: Instantly copy the latest AI response to clipboard
- **`ai cp --show`**: Interactive selection from response history with arrow key navigation
- **Response History**: Automatically stores the last 20 responses (configurable)
- **Smart Previews**: Shows truncated previews (50 characters + "...") for easy identification
- **Cross-platform Clipboard**: Works on Windows, macOS, and Linux
- **Rich Text Processing**: Automatically strips formatting for clean plain text copying

#### 🎯 User Experience:
```bash
# Copy latest response instantly
ai cp
# ✓ Response copied to clipboard (245 characters)

# Interactive selection from history
ai cp --show
```
```
Select response to copy:
❯ 1. Here's a Python function that reverses a str...
  2. The capital of France is Paris.
  3. 2 + 2 = 4

↑↓ Navigate, Enter to copy, Ctrl+C to cancel
```

#### ⚙️ Configuration Options:
New UI configuration options in `~/.ai-cli/config.toml`:
- `response_history_limit`: Number of responses to keep (default: 20)
- `response_preview_length`: Characters shown in previews (default: 50)

### **Documentation Improvements**
- **Added PyPI Downloads Badge**: README now displays download statistics from PyPI

## 🔧 Bug Fixes

### **Fixed ANSI Color Code Stripping**
- **Issue**: ANSI color codes like `[1;33m` were not being properly removed when copying text to clipboard
- **Fix**: Enhanced text processing to handle malformed ANSI sequences without escape characters
- **Impact**: Clipboard text is now clean and free of formatting artifacts

## 🔧 Technical Implementation

### 📁 New Files Added:
- `src/ai_cli/core/history.py` - Response history management
- `src/ai_cli/ui/selector.py` - Interactive response selection interface
- `src/ai_cli/utils/text.py` - Text processing and clipboard utilities
- `tests/test_cp_command.py` - Comprehensive test coverage for new functionality

### 📁 Updated Files:
- `src/ai_cli/cli.py` - Added `cp` command implementation
- `src/ai_cli/core/chat.py` - Integrated response history saving
- `src/ai_cli/config/models.py` - Added response history configuration
- `pyproject.toml` - Added `pyperclip` dependency for clipboard support
- `tests/conftest.py` - Enhanced test fixtures for new components

### 🧪 Testing:
- **119 total tests** (14 new tests for cp functionality and text processing)
- Full test coverage for new features including ANSI stripping
- Proper async test support
- Mocked file operations to avoid side effects

### 🛠️ Dependencies:
- **Added**: `pyperclip>=1.8.0` for cross-platform clipboard functionality
- **Uses existing**: `questionary>=2.0.0` for beautiful interactive selection

## 💾 Storage:
Response history is stored in `~/.ai-cli/response_history.json` with the following format:
- Timestamp, prompt, full response, model name, and preview
- Automatic cleanup when limit is exceeded
- Graceful handling of corrupted files

---

**Full Changelog**: [`v1.1.1...v1.2.0`](https://github.com/YusiZhang/ai-cli/compare/v1.1.1...v1.2.0)
