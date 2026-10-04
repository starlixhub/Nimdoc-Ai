import logging
from abc import ABC, abstractmethod
from typing import Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseLLMService(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response from the LLM given a user prompt and optional system prompt."""
        pass


class NebiusNvidiaLLMService(BaseLLMService):
    """
    Client for interacting with NVIDIA open-source models via Nebius Token Factory.
    Owned and customized by the RAG Developer.
    """

    def __init__(self):
        self.api_key = settings.nebius_api_key
        self.base_url = settings.nebius_api_base_url.rstrip("/")
        self.model_name = settings.llm_model_name

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        # If running in local mock mode / unconfigured key, return a mock response
        if not self.api_key or self.api_key.startswith("mock_"):
            logger.info("Using mock LLM response (Nebius API key not set or mock).")
            return "Based on the provided document context, the project submission deadline is October 15."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 1024,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error calling Nebius Token Factory: {e}")
            raise RuntimeError(f"Failed to communicate with LLM provider: {e}")


# Singleton instance
llm_service = NebiusNvidiaLLMService()
