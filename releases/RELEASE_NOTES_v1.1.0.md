# Release Notes - v1.1.0

## 🎯 Major Changes: Role-Based Roundtable System

This release completely refactors the roundtable discussion system from a model-centric to a role-centric architecture, providing more flexibility and control over how AI conversations are structured.

### ✨ New Features

#### **Role-Based Configuration**
- **New CLI Commands**: Manage roundtable roles with precision
  ```bash
  ai config roundtable --enable-role generator
  ai config roundtable --disable-role critic
  ai config roundtable --map-role generator=openai/gpt-4
  ai config roundtable --solo-model anthropic/claude-3-5-sonnet
  ```

- **Flexible Role Assignment**: Four predefined roles with intelligent fallback
  - `generator`: Creates initial responses and ideas
  - `critic`: Analyzes and provides feedback
  - `refiner`: Improves and polishes content
  - `evaluator`: Makes final assessments

- **Smart Model Mapping**: Priority-based role-to-model assignment
  1. Explicit role mapping (`role_model_mapping`)
  2. Solo model for all roles (`solo_model`)
  3. First available mapped model
  4. Default model fallback

#### **Enhanced Configuration Format**
```toml
[roundtable]
# Enable specific roles (defaults to all four roles)
enabled_roles = ["generator", "critic", "refiner", "evaluator"]

# Option 1: Map roles to specific models
[roundtable.role_model_mapping]
generator = "openai/gpt-4"
critic = "anthropic/claude-3-5-sonnet"
refiner = "gemini"

# Option 2: Use one model for all roles
# solo_model = "openai/gpt-4"
```

### 🔧 Improvements

#### **Better Config Management**
- **Enhanced Error Handling**: Robust config loading with automatic backup creation
- **Smart Defaults**: New users get sensible default configurations automatically
- **Legacy Compatibility**: Existing configurations continue to work during transition

#### **Improved User Experience**
- **Clearer CLI Output**: Role-based information display
- **Better Documentation**: Updated examples and configuration guides
- **Fixed API Keys**: Corrected Gemini API key environment variable (`GEMINI_API_KEY`)

### 🗑️ Removed (Breaking Changes)

#### **Deprecated Configuration**
- **`enabled_models`**: Replaced with role-based `enabled_roles` and `role_model_mapping`
- **CLI Commands**: Removed `--add` and `--remove` options for model management
- **Methods**: Removed `add_roundtable_model()` and `remove_roundtable_model()`

#### **Migration Guide**
**Old Configuration:**
```toml
[roundtable]
enabled_models = ["openai/gpt-4", "anthropic/claude-3-5-sonnet"]
```

**New Configuration:**
```toml
[roundtable]
enabled_roles = ["generator", "critic"]
[roundtable.role_model_mapping]
generator = "openai/gpt-4"
critic = "anthropic/claude-3-5-sonnet"
```

### 🏗️ Technical Improvements

- **Modern Pydantic**: Proper use of `Field(default_factory=...)` for mutable defaults
- **Comprehensive Tests**: 100+ tests covering new role-based system
- **Code Quality**: Enhanced type safety and validation
- **Documentation**: Updated all 10 configuration examples

### 📁 Updated Files

**Core Changes:**
- `src/ai_cli/config/models.py` - New role-based configuration models
- `src/ai_cli/config/manager.py` - Role management methods
- `src/ai_cli/cli.py` - Updated CLI commands
- `src/ai_cli/core/chat.py` - Role-based chat execution

**Documentation & Examples:**
- `README.md` - Updated configuration examples
- `config-examples/*.toml` - All 10 example files updated to new format

**Tests:**
- Comprehensive test suite updated for role-based system
- All legacy `enabled_models` references removed
- 105 tests passing with new architecture

### 🚀 Upgrade Instructions

1. **Automatic Migration**: Existing configs will continue to work
2. **New Setup**: Use `ai config roundtable --list` to see current configuration
3. **Manual Migration**: Update your config files to use the new role-based format
4. **CLI Updates**: Replace old `--add`/`--remove` commands with new role management commands

---

**Full Changelog**: [`v1.0.1...v1.1.0`](https://github.com/YusiZhang/ai-cli/compare/v1.0.1...v1.1.0)
