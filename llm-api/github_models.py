import httpx
from typing import List, Dict, Any, Optional
from config import settings
import logging
import json

logger = logging.getLogger(__name__)


class GitHubModelsClient:
    """Client for GitHub Models API (Azure OpenAI compatible)"""

    def __init__(self):
        self.base_url = settings.GITHUB_API_BASE
        self.token = settings.GITHUB_TOKEN
        self.default_model = settings.GITHUB_DEFAULT_MODEL
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to GitHub Models

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (defaults to GITHUB_DEFAULT_MODEL)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate

        Returns:
            Response dict with 'content', 'model', 'tokens_in', 'tokens_out'
        """
        model = model or self.default_model

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                logger.info(
                    f"Sending chat request to GitHub Models with model {model}")

                payload = {
                    "messages": messages,
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }

                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )

                logger.info(
                    f"GitHub Models response status: {response.status_code}")
                response.raise_for_status()

                data = response.json()

                # GitHub Models (Azure OpenAI) response format:
                # {
                #   "id": "chatcmpl-...",
                #   "object": "chat.completion",
                #   "created": 1234567890,
                #   "model": "gpt-4o-mini",
                #   "choices": [{
                #     "index": 0,
                #     "message": {
                #       "role": "assistant",
                #       "content": "Hello! How can I help you?"
                #     },
                #     "finish_reason": "stop"
                #   }],
                #   "usage": {
                #     "prompt_tokens": 10,
                #     "completion_tokens": 20,
                #     "total_tokens": 30
                #   }
                # }

                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})
                usage = data.get("usage", {})

                return {
                    "content": message.get("content", ""),
                    "model": data.get("model", model),
                    "tokens_in": usage.get("prompt_tokens", 0),
                    "tokens_out": usage.get("completion_tokens", 0)
                }

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"GitHub Models HTTP error: {e.response.status_code} - {e.response.text}")
                raise Exception(
                    f"GitHub Models API error: {e.response.status_code} - {e.response.text}")
            except httpx.ConnectError as e:
                logger.error(f"GitHub Models connection error: {str(e)}")
                raise Exception(
                    f"Cannot connect to GitHub Models at {self.base_url}: {str(e)}")
            except httpx.TimeoutException as e:
                logger.error(f"GitHub Models timeout error: {str(e)}")
                raise Exception(f"GitHub Models request timed out: {str(e)}")
            except Exception as e:
                logger.error(
                    f"GitHub Models unexpected error: {type(e).__name__} - {str(e)}")
                raise Exception(
                    f"Failed to communicate with GitHub Models: {type(e).__name__} - {str(e)}")

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models in GitHub Models"""
        # GitHub Models available models
        return [
            {"name": "gpt-4o", "description": "GPT-4 Omni - Most capable model"},
            {"name": "gpt-4o-mini", "description": "GPT-4 Omni Mini - Fast and efficient"},
            {"name": "gpt-4", "description": "GPT-4 - High capability model"},
            {"name": "gpt-3.5-turbo",
                "description": "GPT-3.5 Turbo - Fast and affordable"},
            {"name": "Meta-Llama-3.1-405B-Instruct",
                "description": "Meta Llama 3.1 405B"},
            {"name": "Meta-Llama-3.1-70B-Instruct",
                "description": "Meta Llama 3.1 70B"},
            {"name": "Meta-Llama-3-70B-Instruct",
                "description": "Meta Llama 3 70B"},
            {"name": "Mistral-large", "description": "Mistral Large"},
            {"name": "Mistral-small", "description": "Mistral Small"},
            {"name": "Cohere-command-r-plus", "description": "Cohere Command R+"},
            {"name": "AI21-Jamba-Instruct", "description": "AI21 Jamba Instruct"}
        ]


# Global GitHub Models client instance
github_client = GitHubModelsClient()
