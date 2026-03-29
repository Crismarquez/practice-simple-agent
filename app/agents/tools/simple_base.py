from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Type

from pydantic import BaseModel

from app.agents.models.simple_agent_state import SimpleAgentState


@dataclass
class ToolExecutionResult:
    """Normalized output for every tool execution."""

    content: str
    ids_content: List[str] = field(default_factory=list)
    query_data: Dict[str, Any] = field(default_factory=dict)


class BaseAgentTool(ABC):
    """Base class for tools executed through OpenAI tool calling."""

    name: str
    description: str
    args_schema: Type[BaseModel]

    def definition(self) -> Dict[str, Any]:
        schema = self.args_schema.model_json_schema()
        schema.pop("title", None)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": schema,
            },
        }

    @abstractmethod
    async def run(self, state: SimpleAgentState, **kwargs: Any) -> ToolExecutionResult:
        """Execute the tool."""


class ToolRegistry:
    """Lookup and schema exposure for agent tools."""

    def __init__(self, tools: List[BaseAgentTool]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    def definitions(self) -> List[Dict[str, Any]]:
        return [tool.definition() for tool in self._tools.values()]

    def get(self, tool_name: str) -> BaseAgentTool:
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' is not registered.")
        return self._tools[tool_name]
