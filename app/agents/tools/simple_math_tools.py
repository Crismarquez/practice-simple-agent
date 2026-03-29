"""
Tools de ejemplo para SimpleAgent.

Cada tool necesita 3 cosas:
  1. name        — nombre que el LLM usara para invocarla
  2. description — explica al LLM cuando y como usarla
  3. args_schema — schema Pydantic que define los parametros

Y un metodo `run()` que ejecuta la logica y devuelve un ToolExecutionResult.
"""

from __future__ import annotations

import math
import statistics
from typing import Any, List

from pydantic import BaseModel, Field

from app.agents.tools.simple_base import BaseAgentTool, ToolExecutionResult


# ── Schemas de entrada (lo que el LLM envia como argumentos) ──

class ThinkToolInput(BaseModel):
    reflection: str = Field(
        description="Reflexion o plan sobre como resolver el problema.",
    )


class SumToolInput(BaseModel):
    numbers: List[float] = Field(
        description="Lista de numeros a sumar. Ejemplo: [1, 2, 3]",
    )


class StatsToolInput(BaseModel):
    numbers: List[float] = Field(
        description="Lista de numeros para calcular estadisticas. Ejemplo: [10, 20, 30]",
    )


class TwoVectorsInput(BaseModel):
    vector_a: List[float] = Field(
        description="Primer vector. Ejemplo: [1.0, 2.0, 3.0]",
    )
    vector_b: List[float] = Field(
        description="Segundo vector. Debe tener la misma dimension que vector_a.",
    )


class SingleVectorInput(BaseModel):
    vector: List[float] = Field(
        description="Vector numerico. Ejemplo: [3.0, 4.0]",
    )


# ── Implementacion de las tools ──────────────────────────────

class ThinkTool(BaseAgentTool):
    """Permite al agente pensar/planear antes de actuar."""

    name = "think_tool"
    description = "Usa esta herramienta para reflexionar o planear tu estrategia."
    args_schema = ThinkToolInput

    async def run(self, state: Any = None, **kwargs) -> ToolExecutionResult:
        reflection = kwargs["reflection"]
        return ToolExecutionResult(content=f"Reflection recorded: {reflection}")


class SumTool(BaseAgentTool):
    """Suma una lista de numeros."""

    name = "sum"
    description = "Suma una lista de numeros y devuelve el resultado. Ejemplo: sum(numbers=[1, 2, 3]) -> 6"
    args_schema = SumToolInput

    async def run(self, state: Any = None, **kwargs) -> ToolExecutionResult:
        numbers = kwargs["numbers"]
        total = sum(numbers)
        return ToolExecutionResult(
            content=f"La suma de {numbers} es {total}",
        )


class StatsTool(BaseAgentTool):
    """Calcula estadisticas descriptivas de una lista de numeros."""

    name = "stats"
    description = (
        "Calcula media, mediana, desviacion estandar, minimo y maximo de una lista de numeros. "
        "Ejemplo: stats(numbers=[10, 20, 30]) -> mean=20, median=20, std=10, min=10, max=30"
    )
    args_schema = StatsToolInput

    async def run(self, state: Any = None, **kwargs) -> ToolExecutionResult:
        numbers = kwargs["numbers"]
        if not numbers:
            return ToolExecutionResult(content="Error: la lista de numeros esta vacia.")

        mean = statistics.mean(numbers)
        median = statistics.median(numbers)
        stdev = statistics.pstdev(numbers)
        min_val = min(numbers)
        max_val = max(numbers)

        return ToolExecutionResult(
            content=(
                f"Estadisticas de {numbers}:\n"
                f"  Media:     {mean}\n"
                f"  Mediana:   {median}\n"
                f"  Desv. std: {stdev}\n"
                f"  Minimo:    {min_val}\n"
                f"  Maximo:    {max_val}"
            ),
        )


class DotProductTool(BaseAgentTool):
    """Calcula el producto punto entre dos vectores."""

    name = "dot_product"
    description = (
        "Calcula el producto punto (dot product) entre dos vectores de la misma dimension. "
        "Ejemplo: dot_product(vector_a=[1,2,3], vector_b=[4,5,6]) -> 32"
    )
    args_schema = TwoVectorsInput

    async def run(self, state: Any = None, **kwargs) -> ToolExecutionResult:
        a = kwargs["vector_a"]
        b = kwargs["vector_b"]
        if len(a) != len(b):
            return ToolExecutionResult(
                content=f"Error: los vectores deben tener la misma dimension. vector_a tiene {len(a)}, vector_b tiene {len(b)}."
            )

        result = sum(x * y for x, y in zip(a, b))
        return ToolExecutionResult(
            content=f"Producto punto de {a} y {b} = {result}",
        )


class MagnitudeTool(BaseAgentTool):
    """Calcula la magnitud (norma L2) de un vector."""

    name = "magnitude"
    description = (
        "Calcula la magnitud (norma euclidiana / norma L2) de un vector. "
        "Ejemplo: magnitude(vector=[3, 4]) -> 5.0"
    )
    args_schema = SingleVectorInput

    async def run(self, state: Any = None, **kwargs) -> ToolExecutionResult:
        vector = kwargs["vector"]
        mag = math.sqrt(sum(x * x for x in vector))
        return ToolExecutionResult(
            content=f"Magnitud de {vector} = {mag}",
        )


class EuclideanDistanceTool(BaseAgentTool):
    """Calcula la distancia euclidiana entre dos vectores."""

    name = "euclidean_distance"
    description = (
        "Calcula la distancia euclidiana entre dos vectores de la misma dimension. "
        "Ejemplo: euclidean_distance(vector_a=[1,0], vector_b=[0,1]) -> 1.4142"
    )
    args_schema = TwoVectorsInput

    async def run(self, state: Any = None, **kwargs) -> ToolExecutionResult:
        a = kwargs["vector_a"]
        b = kwargs["vector_b"]
        if len(a) != len(b):
            return ToolExecutionResult(
                content=f"Error: los vectores deben tener la misma dimension. vector_a tiene {len(a)}, vector_b tiene {len(b)}."
            )

        dist = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
        return ToolExecutionResult(
            content=f"Distancia euclidiana entre {a} y {b} = {dist}",
        )


class CosineDistanceTool(BaseAgentTool):
    """Calcula la distancia coseno entre dos vectores."""

    name = "cosine_distance"
    description = (
        "Calcula la distancia coseno entre dos vectores: 1 - similitud_coseno. "
        "Devuelve un valor entre 0 (identicos) y 2 (opuestos). "
        "Ejemplo: cosine_distance(vector_a=[1,0], vector_b=[0,1]) -> 1.0"
    )
    args_schema = TwoVectorsInput

    async def run(self, state: Any = None, **kwargs) -> ToolExecutionResult:
        a = kwargs["vector_a"]
        b = kwargs["vector_b"]
        if len(a) != len(b):
            return ToolExecutionResult(
                content=f"Error: los vectores deben tener la misma dimension. vector_a tiene {len(a)}, vector_b tiene {len(b)}."
            )

        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))

        if mag_a == 0 or mag_b == 0:
            return ToolExecutionResult(
                content="Error: no se puede calcular la distancia coseno con un vector nulo (magnitud 0)."
            )

        cosine_similarity = dot / (mag_a * mag_b)
        cosine_dist = 1.0 - cosine_similarity

        return ToolExecutionResult(
            content=(
                f"Distancia coseno entre {a} y {b}:\n"
                f"  Producto punto:      {dot}\n"
                f"  Magnitud A:          {mag_a}\n"
                f"  Magnitud B:          {mag_b}\n"
                f"  Similitud coseno:    {cosine_similarity}\n"
                f"  Distancia coseno:    {cosine_dist}"
            ),
        )
