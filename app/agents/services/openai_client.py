from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional

from openai import AzureOpenAI, OpenAI

from app.agents.services.openai_provider import OpenAIProvider, resolve_openai_provider


class OpenAIChatClient:
    """Thin wrapper around Azure OpenAI or OpenAI chat completions."""

    def __init__(
        self,
        provider: Optional[OpenAIProvider] = None,
        model: Optional[str] = None,
        deployment_name: Optional[str] = None,
        base_url: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        api_version: str = "2025-04-01-preview",
        temperature: float = 0.0,
        seed: int = 42,
        max_retries: int = 10,
    ) -> None:
        self.provider = resolve_openai_provider(provider)
        self.temperature = temperature
        self.seed = seed

        if self.provider == "azure":
            self.model = deployment_name or model or os.getenv("AZURE_OPENAI_DEPLOYMENT")
            self.client = AzureOpenAI(
                azure_endpoint=azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=api_key or os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=api_version,
                max_retries=max_retries,
            )
        else:
            self.model = model or deployment_name or os.getenv("OPENAI_MODEL")
            self.client = OpenAI(
                api_key=api_key or os.getenv("OPENAI_API_KEY"),
                base_url=base_url or os.getenv("OPENAI_BASE_URL"),
                max_retries=max_retries,
            )

    async def create_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Any:
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "seed": self.seed,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        return await asyncio.to_thread(
            self.client.chat.completions.create,
            **kwargs,
        )


# Backward-compatible alias for existing imports.
AzureOpenAIChatClient = OpenAIChatClient
