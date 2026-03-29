"""Database connection service for PostgreSQL via SQLAlchemy."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger("default-logger")


class DatabaseService:
    """Manages the PostgreSQL connection and provides schema introspection + query execution."""

    def __init__(self, database_url: Optional[str] = None) -> None:
        self.database_url = database_url or os.getenv("CHALLENGE_DATABASE_URL")
        if not self.database_url:
            raise ValueError(
                "CHALLENGE_DATABASE_URL is not set. "
                "Add it to .env or pass it explicitly."
            )
        self.engine: Engine = create_engine(self.database_url, pool_pre_ping=True)
        self._schema_cache: Optional[str] = None

    def get_schema(self, schema_name: str = "public") -> str:
        """Return a formatted description of all tables, columns, types and foreign keys."""
        if self._schema_cache is not None:
            return self._schema_cache

        inspector = inspect(self.engine)
        table_names = inspector.get_table_names(schema=schema_name)

        if not table_names:
            return f"No tables found in schema '{schema_name}'."

        parts: list[str] = []
        for table in sorted(table_names):
            columns = inspector.get_columns(table, schema=schema_name)
            pk = inspector.get_pk_constraint(table, schema=schema_name)
            fks = inspector.get_foreign_keys(table, schema=schema_name)

            col_lines: list[str] = []
            pk_cols = set(pk.get("constrained_columns", []))
            for col in columns:
                nullable = "NULL" if col.get("nullable", True) else "NOT NULL"
                pk_marker = " [PK]" if col["name"] in pk_cols else ""
                col_lines.append(
                    f"    {col['name']} {col['type']} {nullable}{pk_marker}"
                )

            fk_lines: list[str] = []
            for fk in fks:
                local_cols = ", ".join(fk["constrained_columns"])
                ref_table = fk["referred_table"]
                ref_cols = ", ".join(fk["referred_columns"])
                fk_lines.append(
                    f"    FK: ({local_cols}) -> {ref_table}({ref_cols})"
                )

            section = f"TABLE: {table}\n" + "\n".join(col_lines)
            if fk_lines:
                section += "\n  Foreign Keys:\n" + "\n".join(fk_lines)
            parts.append(section)

        self._schema_cache = "\n\n".join(parts)
        return self._schema_cache

    def execute_query(self, sql: str, max_rows: int = 100) -> Dict[str, Any]:
        """Execute a read-only SQL query and return results as a dict."""
        normalized = sql.strip().rstrip(";").strip()
        first_word = normalized.split()[0].upper() if normalized else ""

        if first_word not in ("SELECT", "WITH", "EXPLAIN"):
            return {
                "success": False,
                "error": f"Only SELECT/WITH/EXPLAIN queries are allowed. Got: {first_word}",
                "rows": [],
                "columns": [],
                "row_count": 0,
            }

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                columns = list(result.keys())
                rows = [dict(zip(columns, row)) for row in result.fetchmany(max_rows)]

                return {
                    "success": True,
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                    "truncated": len(rows) == max_rows,
                }
        except Exception as exc:
            logger.warning("SQL execution error: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "rows": [],
                "columns": [],
                "row_count": 0,
            }

    def test_connection(self) -> bool:
        """Return True if the database is reachable."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as exc:
            logger.error("Database connection test failed: %s", exc)
            return False
