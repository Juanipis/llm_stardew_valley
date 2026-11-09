import logging
import os
from typing import List, Dict, Any

import litellm
from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        """
        Initializes the LLMService and sets API keys for LiteLLM from settings.
        """
        if settings.gemini_api_key:
            os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
        if settings.openai_api_key:
            os.environ["OPENAI_API_KEY"] = settings.openai_api_key

    def _get_model_string(self, model_name: str) -> str:
        """
        Constructs the full model string for LiteLLM, including the provider prefix.
        """
        provider = settings.LLM_PROVIDER
        if provider == "google":
            return f"gemini/{model_name}"
        return f"{provider}/{model_name}"

    async def acompletion(
        self, model: str, messages: List[Dict[str, Any]], **kwargs
    ) -> litellm.ModelResponse:
        """
        Makes an asynchronous call to the completion endpoint of the configured LLM.

        Args:
            model: The base name of the model to use (e.g., 'gpt-4o').
            messages: The list of messages for the conversation.
            **kwargs: Additional arguments for litellm.acompletion.

        Returns:
            The response from the LLM provider.
        """
        model_string = self._get_model_string(model)
        logger.debug(f"Calling acompletion with model: {model_string}")

        call_kwargs = {
            "model": model_string,
            "messages": messages,
            **kwargs,
        }

        if settings.LLM_PROVIDER == "ollama" and settings.ollama_api_base_url:
            call_kwargs["api_base"] = settings.ollama_api_base_url

        return await litellm.acompletion(**call_kwargs)

    async def aembedding(
        self, model: str, input_texts: List[str], **kwargs
    ) -> litellm.EmbeddingResponse:
        """
        Makes an asynchronous call to the embedding endpoint of the configured LLM.

        Args:
            model: The base name of the embedding model to use.
            input_texts: A list of texts to generate embeddings for.
            **kwargs: Additional arguments for litellm.aembedding.

        Returns:
            The embedding response from the LLM provider.
        """
        model_string = self._get_model_string(model)
        logger.debug(f"Calling aembedding with model: {model_string}")

        call_kwargs = {
            "model": model_string,
            "input": input_texts,
            **kwargs,
        }

        if settings.LLM_PROVIDER == "ollama" and settings.ollama_api_base_url:
            call_kwargs["api_base"] = settings.ollama_api_base_url

        return await litellm.aembedding(**call_kwargs)


llm_service = LLMService()
