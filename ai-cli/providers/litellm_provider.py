import asyncio
from typing import AsyncIterator, List, Dict, Any
import litellm
from .base import AIProvider
from ..core.messages import ChatMessage


class LiteLLMProvider(AIProvider):
    """Provider using LiteLLM for unified model access."""
    
    def __init__(self, model_config):
        super().__init__(model_config)
        self._setup_litellm()
    
    def _setup_litellm(self):
        """Configure LiteLLM with the model settings."""
        import os
        
        # Set API keys if provided
        if self.config.api_key:
            if self.config.provider == "openai":
                os.environ["OPENAI_API_KEY"] = self.config.api_key
            elif self.config.provider == "anthropic":
                os.environ["ANTHROPIC_API_KEY"] = self.config.api_key
            elif self.config.provider == "gemini":
                os.environ["GOOGLE_API_KEY"] = self.config.api_key
        
        # Configure custom endpoints
        if self.config.endpoint and self.config.provider == "ollama":
            litellm.api_base = self.config.endpoint
    
    async def chat_stream(self, messages: List[ChatMessage]) -> AsyncIterator[str]:
        """Stream chat responses using LiteLLM."""
        try:
            # Convert messages to LiteLLM format
            litellm_messages = self._messages_to_dict(messages)
            
            # Determine the model name for LiteLLM
            model_name = self._get_litellm_model_name()
            
            # Create the completion request
            response = await litellm.acompletion(
                model=model_name,
                messages=litellm_messages,
                stream=True,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                api_base=self.config.endpoint if self.config.endpoint else None,
            )
            
            # Stream the response
            async for chunk in response:
                if hasattr(chunk, 'choices') and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        yield delta.content
                        
        except Exception as e:
            yield f"Error: {str(e)}"
    
    async def validate_config(self) -> bool:
        """Validate the provider configuration."""
        try:
            # Try a simple test completion
            test_messages = [{"role": "user", "content": "Hi"}]
            model_name = self._get_litellm_model_name()
            
            response = await litellm.acompletion(
                model=model_name,
                messages=test_messages,
                max_tokens=1,
                stream=False,
                api_base=self.config.endpoint if self.config.endpoint else None,
            )
            
            return response is not None
            
        except Exception:
            return False
    
    def _get_litellm_model_name(self) -> str:
        """Get the model name in LiteLLM format."""
        if self.config.provider == "openai":
            return self.config.model
        elif self.config.provider == "anthropic":
            # LiteLLM expects anthropic models without prefix
            return self.config.model
        elif self.config.provider == "ollama":
            return f"ollama/{self.config.model}"
        elif self.config.provider == "gemini":
            return f"gemini/{self.config.model}"
        else:
            return self.config.model