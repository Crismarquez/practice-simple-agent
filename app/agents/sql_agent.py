from __future__ import annotations

import json
import logging
from typing import Any, Dict, Iterable, List, Optional

from app.agents.models.sql_agent_state import SQLAgentState
from app.agents.prompts.simple_sql_agent import SIMPLE_SQL_AGENT_PROMPT
from app.agents.services.openai_client import OpenAIChatClient
from app.agents.tools.simple_base import BaseAgentTool, ToolRegistry
from app.agents.tools.simple_sql_tools import (
    ExecuteSQLQueryTool,
    GetDatabaseSchemaTool,
    SQLThinkTool,
)
from app.schemas.conversation import MessageItem
from app.services.db_service import DatabaseService

logger = logging.getLogger("default-logger")


class SimpleSQLAgent:
    """Minimal Text-to-SQL agent implemented with OpenAI tool calling."""

    def __init__(
        self,
        llm_client: Optional[OpenAIChatClient] = None,
        tools: Optional[List[BaseAgentTool]] = None,
        db_service: Optional[DatabaseService] = None,
        system_prompt: str = SIMPLE_SQL_AGENT_PROMPT,
        max_iterations: int = 10,
    ) -> None:
        self.llm_client = llm_client or OpenAIChatClient()
        self.db_service = db_service

        default_tools: List[BaseAgentTool] = [
            SQLThinkTool(),
            GetDatabaseSchemaTool(db_service=db_service),
            ExecuteSQLQueryTool(db_service=db_service),
        ]
        self.registry = ToolRegistry(tools or default_tools)
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations

    def _build_state(
        self, history: Iterable[MessageItem], metadata: Dict[str, Any]
    ) -> SQLAgentState:
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
        ]

        for message in history:
            messages.append(
                {
                    "role": message.role,
                    "content": message.content,
                }
            )

        return SQLAgentState(
            user_id=metadata["user_id"],
            session_id=metadata["session_id"],
            messages=messages,
        )

    @staticmethod
    def _serialize_tool_calls(tool_calls: Any) -> List[Dict[str, Any]]:
        serialized_tool_calls = []
        for tool_call in tool_calls or []:
            serialized_tool_calls.append(
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
            )
        return serialized_tool_calls

    async def _execute_tool_calls(
        self, state: SQLAgentState, tool_calls: Any
    ) -> None:
        for tool_call in tool_calls or []:
            tool = self.registry.get(tool_call.function.name)
            arguments = json.loads(tool_call.function.arguments or "{}")

            result = await tool.run(state=state, **arguments)

            state.add_query_history(result.query_data)
            state.add_message(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result.content,
                }
            )

    async def run(
        self, history: List[MessageItem], metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        state = self._build_state(history=history, metadata=metadata)

        for iteration in range(1, self.max_iterations + 1):
            response = await self.llm_client.create_completion(
                messages=state.messages,
                tools=self.registry.definitions(),
            )
            assistant_message = response.choices[0].message
            tool_calls = assistant_message.tool_calls or []

            state.add_message(
                {
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    **(
                        {"tool_calls": self._serialize_tool_calls(tool_calls)}
                        if tool_calls
                        else {}
                    ),
                }
            )

            if not tool_calls:
                logger.info("SimpleSQLAgent completed in %s iterations", iteration)
                return state.to_response()

            await self._execute_tool_calls(state=state, tool_calls=tool_calls)

        logger.warning("SimpleSQLAgent reached max iterations without final answer")
        state.add_message(
            {
                "role": "assistant",
                "content": (
                    "No pude completar la respuesta dentro del limite de iteraciones. "
                    "Intenta reformular la pregunta."
                ),
            }
        )
        return state.to_response()

    async def stream_run(
        self, history: List[MessageItem], metadata: Dict[str, Any]
    ):
        final_state = await self.run(history=history, metadata=metadata)
        final_message = final_state["messages"][-1]
        yield {"type": "messages", "data": final_message}
