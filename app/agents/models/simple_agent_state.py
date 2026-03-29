from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class SimpleAgentState:
    """Conversation state for the OpenAI tool-calling agent."""

    user_id: str
    session_id: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    ids_content: List[List[str]] = field(default_factory=list)
    query_history: List[Dict[str, Any]] = field(default_factory=list)

    def add_message(self, message: Dict[str, Any]) -> None:
        self.messages.append(message)

    def add_ids_content(self, ids_content: List[str]) -> None:
        if ids_content:
            self.ids_content.append(ids_content)

    def add_query_history(self, query_data: Dict[str, Any]) -> None:
        if query_data:
            self.query_history.append(query_data)

    def to_response(self) -> Dict[str, Any]:
        return {
            "messages": self.messages,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "ids_content": self.ids_content,
            "query_history": self.query_history,
        }
