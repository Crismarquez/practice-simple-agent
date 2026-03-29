"""
Arena-compatible endpoint for Enterprise Agent Arena platform.

Receives the platform's test case input directly and returns
the answer in the format expected by the evaluator.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.agents.sql_agent import SimpleSQLAgent
from app.schemas.conversation import MessageItem
from app.services.sql_chat_service import SQLChatService

logger = logging.getLogger("default-logger")


# --- Request/Response schemas for the Arena contract ---

class ArenaRequest(BaseModel):
    question: str = Field(..., description="Natural language question to answer")
    chat_history: Optional[List[dict]] = Field(
        default=None,
        description="Optional conversation history as list of {role, content} dicts",
    )


class ArenaResponse(BaseModel):
    answer: str = Field(..., description="The agent's answer")


# --- Dependencies ---

async def get_sql_agent(request: Request) -> SimpleSQLAgent:
    agent = getattr(request.app.state, "sql_agent", None)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SQL agent not initialized",
        )
    return agent


async def get_service(
    agent: SimpleSQLAgent = Depends(get_sql_agent),
) -> SQLChatService:
    return SQLChatService(agent)


# --- Router ---

router = APIRouter(prefix="/arena", tags=["Arena"])


@router.post("", response_model=ArenaResponse)
async def arena_evaluate(
    request: ArenaRequest,
    service: SQLChatService = Depends(get_service),
):
    """
    Arena-compatible endpoint.

    Receives: {"question": "...", "chat_history": [...]}
    Returns:  {"answer": "..."}
    """
    try:
        # Build history from chat_history or from the question directly
        if request.chat_history:
            history = [
                MessageItem(role=msg["role"], content=msg["content"])
                for msg in request.chat_history
            ]
        else:
            history = [MessageItem(role="user", content=request.question)]

        result = await service.query(
            history=history,
            user_id="arena",
            session_id="arena",
        )

        return ArenaResponse(answer=result["response"])

    except Exception as e:
        logger.error("Arena evaluation error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent failed to process the question",
        )
