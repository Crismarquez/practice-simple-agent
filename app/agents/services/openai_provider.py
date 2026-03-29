from __future__ import annotations

import os
from typing import Literal, Optional, cast

OpenAIProvider = Literal["azure", "openai"]


def resolve_openai_provider(provider: Optional[str] = None) -> OpenAIProvider:
    """Resolve which chat provider to use from args or environment."""
    configured_provider = provider or os.getenv("OPENAI_API_PROVIDER")

    if configured_provider:
        normalized_provider = configured_provider.strip().lower()
    else:
        normalized_provider = "azure" if os.getenv("AZURE_OPENAI_ENDPOINT") else "openai"

    if normalized_provider not in {"azure", "openai"}:
        raise ValueError(
            "Unsupported OPENAI_API_PROVIDER value. Use 'azure' or 'openai'."
        )

    return cast(OpenAIProvider, normalized_provider)
