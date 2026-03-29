"""Service layer for the SQL chat agent."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from app.agents.sql_agent import SimpleSQLAgent
from app.schemas.conversation import MessageItem

logger = logging.getLogger("default-logger")


class SQLChatService:
    """Thin service wrapper around `SimpleSQLAgent`."""

    def __init__(self, chat_agent: Optional[SimpleSQLAgent] = None) -> None:
        self.chat_agent = chat_agent or SimpleSQLAgent()

    async def query(
        self,
        history: List[MessageItem],
        user_id: str,
        session_id: str,
    ) -> Dict[str, Any]:
        """Execute a SQL chat query and shape the response for the API."""
        start_time = time.time()
        metadata = {
            "user_id": user_id,
            "session_id": session_id,
        }

        logger.info(
            "Processing SQL query for user %s, session %s", user_id, session_id
        )
        final_state = await self.chat_agent.run(history=history, metadata=metadata)

        messages = final_state.get("messages", [])
        assistant_response = ""
        if messages:
            last_message = messages[-1]
            if isinstance(last_message, dict):
                assistant_response = last_message.get("content", "")
            elif hasattr(last_message, "content"):
                assistant_response = last_message.content

        execution_time = time.time() - start_time
        agent_snapshot = {
            "sql_queries": final_state.get("sql_queries", []),
            "query_history": final_state.get("query_history", []),
            "execution_time_seconds": execution_time,
        }

        return {
            "response": assistant_response,
            "message_id": None,
            "agent_state": {
                "session_id": final_state.get("session_id"),
                "user_id": final_state.get("user_id"),
                **agent_snapshot,
            },
        }

    async def stream_query(
        self,
        history: List[MessageItem],
        user_id: str,
        session_id: str,
    ):
        """Stream chunks produced by the SQL chat agent."""
        metadata = {
            "user_id": user_id,
            "session_id": session_id,
        }

        logger.info(
            "Starting stream SQL query for user %s, session %s",
            user_id,
            session_id,
        )
        async for chunk in self.chat_agent.stream_run(
            history=history, metadata=metadata
        ):
            yield chunk
