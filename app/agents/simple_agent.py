"""
SimpleAgent — ejemplo educativo de un agente con tool calling.

Demuestra el patron minimo:
  1. El LLM recibe un mensaje del usuario + definiciones de tools.
  2. Si el LLM decide usar una tool, devuelve un tool_call.
  3. Ejecutamos la tool y le devolvemos el resultado al LLM.
  4. Repetimos hasta que el LLM responda sin tool_calls (respuesta final).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from app.agents.services.openai_client import OpenAIChatClient
from app.agents.tools.simple_base import BaseAgentTool, ToolRegistry
from app.agents.tools.simple_math_tools import (
    CosineDistanceTool,
    DotProductTool,
    EuclideanDistanceTool,
    MagnitudeTool,
    StatsTool,
    SumTool,
    ThinkTool,
)
from app.schemas.conversation import MessageItem

logger = logging.getLogger("default-logger")

SIMPLE_AGENT_PROMPT = """
Eres un asistente que puede hacer calculos matematicos usando herramientas.

Reglas:
- Usa las herramientas disponibles para hacer calculos. No hagas calculos mentalmente.
- Usa `think_tool` cuando necesites planear o reflexionar.
- Responde de forma clara y directa con el resultado.

Herramientas disponibles:
- `sum` — suma una lista de numeros.
- `stats` — calcula media, mediana, desviacion estandar, min y max de una lista.
- `dot_product` — producto punto entre dos vectores.
- `magnitude` — magnitud (norma L2) de un vector.
- `euclidean_distance` — distancia euclidiana entre dos vectores.
- `cosine_distance` — distancia coseno entre dos vectores (1 - similitud coseno).

Para operaciones compuestas, puedes encadenar varias herramientas en pasos sucesivos.
""".strip()


class SimpleAgent:
    """
    Agente minimo con tool calling.

    Ciclo:
        Usuario pregunta -> LLM decide si usar tool -> ejecutamos tool
        -> LLM recibe resultado -> responde (o usa otra tool).
    """

    def __init__(
        self,
        llm_client: Optional[OpenAIChatClient] = None,
        tools: Optional[List[BaseAgentTool]] = None,
        system_prompt: str = SIMPLE_AGENT_PROMPT,
        max_iterations: int = 5,
    ) -> None:
        # 1) Cliente LLM (Azure OpenAI o OpenAI)
        self.llm_client = llm_client or OpenAIChatClient()

        # 2) Registro de tools disponibles
        self.registry = ToolRegistry(tools or [
            ThinkTool(),
            SumTool(),
            StatsTool(),
            DotProductTool(),
            MagnitudeTool(),
            EuclideanDistanceTool(),
            CosineDistanceTool(),
        ])

        # 3) Prompt del sistema y limite de iteraciones
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations

    # ── helpers ────────────────────────────────────────────────

    @staticmethod
    def _serialize_tool_calls(tool_calls: Any) -> List[Dict[str, Any]]:
        """Convierte los tool_calls del SDK de OpenAI a dicts serializables."""
        return [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in (tool_calls or [])
        ]

    # ── loop principal ─────────────────────────────────────────

    async def run(self, history: List[MessageItem], metadata: Dict[str, Any]) -> Dict[str, Any]:
        # --- Paso 1: Construir los mensajes iniciales ---
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
        ]
        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})

        # --- Paso 2: Loop de tool calling ---
        for iteration in range(1, self.max_iterations + 1):

            # 2a. Llamar al LLM con los mensajes + definiciones de tools
            response = await self.llm_client.create_completion(
                messages=messages,
                tools=self.registry.definitions(),
            )
            assistant_msg = response.choices[0].message
            tool_calls = assistant_msg.tool_calls or []

            # 2b. Agregar la respuesta del asistente a los mensajes
            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_msg.content or "",
                    **({"tool_calls": self._serialize_tool_calls(tool_calls)} if tool_calls else {}),
                }
            )

            # 2c. Si NO hay tool_calls, el LLM ya tiene la respuesta final
            if not tool_calls:
                logger.info("SimpleAgent completed in %s iterations", iteration)
                return {
                    "messages": messages,
                    "user_id": metadata.get("user_id"),
                    "session_id": metadata.get("session_id"),
                }

            # 2d. Ejecutar cada tool y agregar el resultado como mensaje "tool"
            for tc in tool_calls:
                tool = self.registry.get(tc.function.name)
                kwargs = json.loads(tc.function.arguments or "{}")
                result = await tool.run(state=None, **kwargs)  # type: ignore[arg-type]

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result.content,
                    }
                )

        # --- Paso 3: Si se agotan las iteraciones ---
        messages.append(
            {
                "role": "assistant",
                "content": "No pude completar la respuesta dentro del limite de iteraciones.",
            }
        )
        return {
            "messages": messages,
            "user_id": metadata.get("user_id"),
            "session_id": metadata.get("session_id"),
        }
