from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.agents.models.sql_agent_state import SQLAgentState
from app.agents.tools.simple_base import BaseAgentTool, ToolExecutionResult

logger = logging.getLogger("default-logger")


# ── Input schemas ──────────────────────────────────────────────

class ThinkToolInput(BaseModel):
    reflection: str = Field(
        description="Strategic reflection about the question, SQL plan, or result analysis.",
    )


class GetDatabaseSchemaInput(BaseModel):
    schema_name: str = Field(
        default="public",
        description="Database schema to inspect. Defaults to 'public'.",
    )


class ExecuteSQLQueryInput(BaseModel):
    sql: str = Field(
        description="The SELECT SQL query to execute against the database.",
    )
    max_rows: int = Field(
        default=100,
        description="Maximum number of rows to return. Default 100.",
    )


# ── Tool implementations ──────────────────────────────────────

class SQLThinkTool(BaseAgentTool):
    name = "think_tool"
    description = "Use this tool to plan your SQL strategy, reflect on schema, or verify result quality."
    args_schema = ThinkToolInput

    async def run(self, state: SQLAgentState, **kwargs) -> ToolExecutionResult:  # type: ignore[override]
        reflection = kwargs["reflection"]
        timestamp = datetime.now().isoformat()
        logger.debug("SQL Agent reflection [%s]: %s", timestamp, reflection)
        return ToolExecutionResult(content=f"Reflection recorded: {reflection}")


class GetDatabaseSchemaTool(BaseAgentTool):
    name = "get_database_schema"
    description = (
        "Retrieve the database schema: tables, columns, types, primary keys and foreign keys. "
        "Use this to understand the data model before writing SQL."
    )
    args_schema = GetDatabaseSchemaInput

    def __init__(self, db_service: Any = None) -> None:
        self.db_service = db_service

    async def run(self, state: SQLAgentState, **kwargs) -> ToolExecutionResult:  # type: ignore[override]
        schema_name = kwargs.get("schema_name", "public")

        if self.db_service is None:
            return ToolExecutionResult(
                content="Database service is not configured.",
                query_data={"action": "get_schema", "schema_name": schema_name},
            )

        try:
            schema_text = self.db_service.get_schema(schema_name=schema_name)
        except Exception as exc:
            logger.exception("Error fetching schema for '%s'", schema_name)
            return ToolExecutionResult(
                content=f"Error fetching database schema: {exc}",
                query_data={"action": "get_schema", "error": str(exc)},
            )

        return ToolExecutionResult(
            content=schema_text,
            query_data={"action": "get_schema", "schema_name": schema_name},
        )


class ExecuteSQLQueryTool(BaseAgentTool):
    name = "execute_sql_query"
    description = (
        "Execute a read-only SQL query (SELECT/WITH/EXPLAIN) against the PostgreSQL database "
        "and return the results."
    )
    args_schema = ExecuteSQLQueryInput

    def __init__(self, db_service: Any = None) -> None:
        self.db_service = db_service

    async def run(self, state: SQLAgentState, **kwargs) -> ToolExecutionResult:  # type: ignore[override]
        sql = kwargs["sql"]
        max_rows = kwargs.get("max_rows", 100)

        if self.db_service is None:
            return ToolExecutionResult(
                content="Database service is not configured.",
                query_data={"sql": sql, "success": False},
            )

        try:
            result = self.db_service.execute_query(sql=sql, max_rows=max_rows)
        except Exception as exc:
            logger.exception("Unexpected error executing SQL")
            return ToolExecutionResult(
                content=f"Unexpected error: {exc}",
                query_data={"sql": sql, "success": False, "error": str(exc)},
            )

        query_record = {
            "sql": sql,
            "success": result["success"],
            "row_count": result.get("row_count", 0),
        }

        if not result["success"]:
            state.add_sql_query(query_record)
            return ToolExecutionResult(
                content=f"SQL Error: {result['error']}",
                query_data=query_record,
            )

        # Format results for the LLM
        rows = result["rows"]
        columns = result["columns"]

        if not rows:
            content = f"Query executed successfully but returned 0 rows.\nSQL: {sql}"
        else:
            # Build a readable table representation
            header = " | ".join(columns)
            separator = "-+-".join("-" * max(len(c), 5) for c in columns)
            row_lines = []
            for row in rows:
                row_lines.append(
                    " | ".join(str(row.get(c, "")) for c in columns)
                )
            table_text = f"{header}\n{separator}\n" + "\n".join(row_lines)

            truncated_note = (
                f"\n(Results truncated to {max_rows} rows)" if result.get("truncated") else ""
            )
            content = (
                f"Query returned {len(rows)} row(s):\n\n{table_text}{truncated_note}"
            )

        query_record["row_count"] = len(rows)
        state.add_sql_query(query_record)

        return ToolExecutionResult(
            content=content,
            query_data=query_record,
        )
