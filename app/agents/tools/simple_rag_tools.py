from __future__ import annotations

import inspect
import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.agents.models.simple_agent_state import SimpleAgentState
from app.agents.tools.simple_base import BaseAgentTool, ToolExecutionResult

logger = logging.getLogger("default-logger")


class ThinkToolInput(BaseModel):
    reflection: str = Field(
        description="Strategic reflection about the question, search plan, or evidence quality.",
    )


class RetrieveDocumentsToolInput(BaseModel):
    query: str = Field(description="Search query to retrieve documents from the knowledge base.")


class ThinkTool(BaseAgentTool):
    name = "think_tool"
    description = "Use this tool to plan, reflect, and verify whether the evidence is sufficient."
    args_schema = ThinkToolInput

    async def run(self, state: SimpleAgentState, **kwargs) -> ToolExecutionResult:
        reflection = kwargs["reflection"]
        timestamp = datetime.now().isoformat()
        logger.debug("Agent reflection [%s]: %s", timestamp, reflection)
        return ToolExecutionResult(content=f"Reflection recorded: {reflection}")


class RetrieveDocumentsTool(BaseAgentTool):
    name = "retrieve_documents"
    description = "Retrieve relevant document fragments from the indexed knowledge base."
    args_schema = RetrieveDocumentsToolInput

    def __init__(self, search_service: Any | None = None) -> None:
        self.search_service = search_service

    async def run(self, state: SimpleAgentState, **kwargs) -> ToolExecutionResult:
        query = kwargs["query"]

        try:
            if self.search_service is None or not hasattr(self.search_service, "search"):
                return ToolExecutionResult(
                    content="Search service is not configured. No documents were retrieved.",
                    query_data={"query": query, "ids_retrieved": []},
                )

            results = self.search_service.search(query=query, top_k=20)
            if inspect.isawaitable(results):
                results = await results
        except Exception as exc:  # pragma: no cover - depends on external services
            logger.exception("Error retrieving documents for query '%s'", query)
            return ToolExecutionResult(content=f"Error retrieving documents: {exc}")

        if not results:
            return ToolExecutionResult(
                content=f"No documents found for query '{query}'.",
                query_data={"query": query, "ids_retrieved": []},
            )



        if isinstance(results, str):
            return ToolExecutionResult(
                content=results,
                query_data={"query": query, "ids_retrieved": []},
            )

        content_parts = [f"Found {len(results)} documents for query '{query}':"]
        ids_content = []

        for index, doc in enumerate(results, start=1):
            chunk_id = doc.get("chunk_id")
            if chunk_id is not None:
                ids_content.append(str(chunk_id))

            content_parts.append(
                "\n".join(
                    [
                        f"Document {index} (Score: {doc.get('score', 0):.4f})",
                        f"Title: {doc.get('document_name', 'Unknown')}",
                        f"Content: {doc.get('content', '')}",
                    ]
                )
            )

        return ToolExecutionResult(
            content="\n\n".join(content_parts),
            ids_content=ids_content,
            query_data={
                "query": query,
                "ids_retrieved": ids_content,
            },
        )
