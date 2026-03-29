"""Service layer for the simplified chat agent."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from app.agents.simple_agent import SimpleAgent
from app.schemas.conversation import MessageItem

logger = logging.getLogger("default-logger")


class ChatService:
    """Thin service wrapper around `SimpleRAGAgent`."""

    def __init__(self, chat_agent: Optional[SimpleAgent] = None) -> None:
        self.chat_agent = chat_agent or SimpleAgent()

    async def query(
        self,
        history: List[MessageItem],
        user_id: str,
        session_id: str,
    ) -> Dict[str, Any]:
        """Execute a chat query and shape the response for the API."""
        start_time = time.time()
        metadata = {
            "user_id": user_id,
            "session_id": session_id,
        }

        logger.info("Processing chat query for user %s, session %s", user_id, session_id)
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
        """Stream chunks produced by the simplified chat agent."""
        metadata = {
            "user_id": user_id,
            "session_id": session_id,
        }

        logger.info("Starting stream chat query for user %s, session %s", user_id, session_id)
        async for chunk in self.chat_agent.stream_run(history=history, metadata=metadata):
            yield chunk
