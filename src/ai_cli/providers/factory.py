from ..config.models import AIConfig, ModelConfig
from .base import AIProvider
from .litellm_provider import LiteLLMProvider


class ProviderFactory:
    """Factory for creating AI providers based on configuration."""

    def __init__(self, config: AIConfig):
        self.config = config
        self._provider_cache: dict[str, AIProvider] = {}

    def get_provider(self, model_name: str) -> AIProvider:
        """Get a provider instance for the specified model."""
        # Check cache first
        if model_name in self._provider_cache:
            return self._provider_cache[model_name]

        # Get model configuration
        model_config = self.config.get_model_config(model_name)

        # Create provider based on the provider type
        provider = self._create_provider(model_config)

        # Cache the provider
        self._provider_cache[model_name] = provider

        return provider

    def _create_provider(self, model_config: ModelConfig) -> AIProvider:
        """Create a provider instance based on the model configuration."""
        # For now, we'll use LiteLLM for all providers
        # Later we can add native providers for specific features
        return LiteLLMProvider(model_config)

    def clear_cache(self) -> None:
        """Clear the provider cache."""
        self._provider_cache.clear()

    async def validate_all_providers(self) -> dict[str, bool]:
        """Validate all configured providers."""
        results = {}

        for model_name in self.config.models.keys():
            try:
                provider = self.get_provider(model_name)
                results[model_name] = await provider.validate_config()
            except Exception:
                results[model_name] = False

        return results
