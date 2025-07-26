import toml
from pathlib import Path
from typing import Optional, Dict, Any
from .models import AIConfig, ModelConfig, RoundTableConfig, UIConfig


class ConfigManager:
    """Manages loading, saving, and updating configuration."""
    
    def __init__(self):
        self._config: Optional[AIConfig] = None
        self._config_path = Path.home() / ".ai-cli" / "config.toml"
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """Ensure the configuration directory exists."""
        self._config_path.parent.mkdir(exist_ok=True)
    
    def load_config(self) -> AIConfig:
        """Load configuration from file or create default."""
        if self._config is not None:
            return self._config
            
        if self._config_path.exists():
            try:
                with open(self._config_path, 'r') as f:
                    config_data = toml.load(f)
                self._config = AIConfig(**config_data)
            except Exception as e:
                print(f"Warning: Failed to load config from {self._config_path}: {e}")
                print("Using default configuration...")
                self._config = AIConfig()
        else:
            self._config = AIConfig()
            self.save_config()  # Save default config
            
        return self._config
    
    def save_config(self, config: Optional[AIConfig] = None):
        """Save configuration to file."""
        if config is None:
            config = self._config
        if config is None:
            raise ValueError("No configuration to save")
            
        config_dict = self._config_to_dict(config)
        
        with open(self._config_path, 'w') as f:
            toml.dump(config_dict, f)
    
    def _config_to_dict(self, config: AIConfig) -> Dict[str, Any]:
        """Convert AIConfig to dictionary for TOML serialization."""
        result = {
            "default_model": config.default_model,
            "models": {},
            "roundtable": {
                "enabled_models": config.roundtable.enabled_models,
                "discussion_rounds": config.roundtable.discussion_rounds,
                "critique_mode": config.roundtable.critique_mode,
                "parallel_responses": config.roundtable.parallel_responses,
                "timeout_seconds": config.roundtable.timeout_seconds,
            },
            "ui": {
                "theme": config.ui.theme,
                "streaming": config.ui.streaming,
                "format": config.ui.format,
                "show_model_icons": config.ui.show_model_icons,
                "show_timestamps": config.ui.show_timestamps,
            }
        }
        
        # Convert model configs to dicts
        for name, model_config in config.models.items():
            if isinstance(model_config, ModelConfig):
                model_dict = {
                    "provider": model_config.provider,
                    "model": model_config.model,
                    "max_tokens": model_config.max_tokens,
                    "temperature": model_config.temperature,
                    "context_window": model_config.context_window,
                }
                # Handle API key storage - save env: references, not resolved keys
                if model_config.api_key:
                    # If it looks like a resolved API key, don't save it
                    if (model_config.api_key.startswith('sk-') or 
                        model_config.api_key.startswith('AIzaSy') or
                        len(model_config.api_key) > 50):
                        # Try to determine the original env reference
                        if name == "openai/gpt-4" or "openai" in model_config.provider:
                            model_dict["api_key"] = "env:OPENAI_API_KEY"
                        elif name == "anthropic/claude-3-sonnet" or "anthropic" in model_config.provider:
                            model_dict["api_key"] = "env:ANTHROPIC_API_KEY"
                        elif "gemini" in model_config.provider:
                            model_dict["api_key"] = "env:GOOGLE_API_KEY"
                    else:
                        # It's likely an env: reference, keep it as is
                        model_dict["api_key"] = model_config.api_key
                    
                if model_config.endpoint:
                    model_dict["endpoint"] = model_config.endpoint
                    
                result["models"][name] = model_dict
            else:
                result["models"][name] = model_config
                
        return result
    
    def update_model(self, model_name: str, **updates):
        """Update a specific model configuration."""
        config = self.load_config()
        
        if model_name not in config.models:
            # Create new model config
            # Ensure model field is set correctly, prioritizing updates over model_name
            model_config_data = {"model": model_name}
            model_config_data.update(updates)  # This will override model if specified in updates
            config.models[model_name] = ModelConfig(**model_config_data)
        else:
            # Update existing model config
            model_config = config.get_model_config(model_name)
            for key, value in updates.items():
                if hasattr(model_config, key):
                    setattr(model_config, key, value)
            config.models[model_name] = model_config
            
        self.save_config(config)
    
    def set_default_model(self, model_name: str):
        """Set the default model."""
        config = self.load_config()
        if model_name not in config.models:
            raise ValueError(f"Model '{model_name}' not found in configuration")
        config.default_model = model_name
        self.save_config(config)
    
    def add_roundtable_model(self, model_name: str):
        """Add a model to the round-table configuration."""
        config = self.load_config()
        if model_name not in config.models:
            raise ValueError(f"Model '{model_name}' not found in configuration")
        if model_name not in config.roundtable.enabled_models:
            config.roundtable.enabled_models.append(model_name)
            self.save_config(config)
    
    def remove_roundtable_model(self, model_name: str):
        """Remove a model from the round-table configuration."""
        config = self.load_config()
        if model_name in config.roundtable.enabled_models:
            config.roundtable.enabled_models.remove(model_name)
            self.save_config(config)
    
    def list_models(self) -> Dict[str, ModelConfig]:
        """List all configured models."""
        config = self.load_config()
        return {
            name: config.get_model_config(name) 
            for name in config.models.keys()
        }
    
    def get_config_path(self) -> Path:
        """Get the path to the configuration file."""
        return self._config_path