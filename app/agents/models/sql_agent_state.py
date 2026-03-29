from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class SQLAgentState:
    """Conversation state for the SQL tool-calling agent."""

    user_id: str
    session_id: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    sql_queries: List[Dict[str, Any]] = field(default_factory=list)
    query_history: List[Dict[str, Any]] = field(default_factory=list)

    def add_message(self, message: Dict[str, Any]) -> None:
        self.messages.append(message)

    def add_sql_query(self, query_data: Dict[str, Any]) -> None:
        if query_data:
            self.sql_queries.append(query_data)

    def add_query_history(self, query_data: Dict[str, Any]) -> None:
        if query_data:
            self.query_history.append(query_data)

    def to_response(self) -> Dict[str, Any]:
        return {
            "messages": self.messages,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "sql_queries": self.sql_queries,
            "query_history": self.query_history,
        }
