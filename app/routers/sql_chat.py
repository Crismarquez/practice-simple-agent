"""
REST API endpoints for the SQL chat agent.

Provides endpoints for:
- Querying a PostgreSQL database using natural language (Text-to-SQL)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.agents.sql_agent import SimpleSQLAgent
from app.schemas.conversation import InputChat, ResponseRAG
from app.schemas.errors import ErrorResponse
from app.services.sql_chat_service import SQLChatService

logger = logging.getLogger("default-logger")


async def get_sql_agent(request: Request) -> Optional[SimpleSQLAgent]:
    """Dependency to get SQL agent from app state."""
    agent = getattr(request.app.state, "sql_agent", None)

    if agent and hasattr(request.app.state, "metrics"):
        request.app.state.metrics["sql_agent_access_count"] = (
            request.app.state.metrics.get("sql_agent_access_count", 0) + 1
        )

    return agent


async def get_sql_chat_service(
    sql_agent: Optional[SimpleSQLAgent] = Depends(get_sql_agent),
) -> SQLChatService:
    """Dependency to get SQL chat service instance."""
    return SQLChatService(sql_agent)


router = APIRouter(
    prefix="/sql",
    tags=["SQL Agent"],
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "Not found"},
    },
)


@router.post(
    "/agent",
    response_model=ResponseRAG,
    summary="Query database with natural language",
    description="Convert a natural language question to SQL and execute it against the database.",
)
async def query_database(
    request: InputChat,
    service: SQLChatService = Depends(get_sql_chat_service),
):
    """
    Query the PostgreSQL database with a natural language question.

    The SQL agent will:
    1. Inspect the database schema
    2. Generate an appropriate SQL query
    3. Execute the query
    4. Return a human-readable answer
    """
    try:
        response = await service.query(
            history=request.history,
            user_id=request.user_id,
            session_id=request.session_id,
        )

        return ResponseRAG(**response)

    except Exception as e:
        logger.error("Error processing SQL query: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process SQL query",
        )
