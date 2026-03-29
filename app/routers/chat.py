"""
REST API endpoints for chat and knowledge base querying.

Provides endpoints for:
- Querying indexed documents with natural language

This router is a thin HTTP layer that delegates all business logic to ChatService.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Request

from app.agents.simple_agent import SimpleAgent
from app.services.chat_service import ChatService
from app.schemas.conversation import InputChat, ResponseRAG
from app.schemas.errors import ErrorResponse

logger = logging.getLogger("default-logger")


async def get_chat_agent(request: Request) -> Optional[SimpleAgent]:
    """
    Dependency to get chat agent from app state.
    """
    agent = getattr(request.app.state, "chat_agent", None)
    
    # Simple metric logging
    if agent and hasattr(request.app.state, "metrics"):
        request.app.state.metrics["chat_agent_access_count"] += 1
        
    return agent


async def get_chat_service(
    chat_agent: Optional[SimpleAgent] = Depends(get_chat_agent)
) -> ChatService:
    """
    Dependency to get chat service instance.
    Creates a new service instance with injected dependencies.
    """
    return ChatService(chat_agent)


# Create router
router = APIRouter(
    prefix="/chat",
    tags=["Chat & Knowledge Base"],
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "Not found"}
    }
)


@router.post("/agent",
             response_model=ResponseRAG,
             summary="Query knowledge base",
             description="Send a natural language query to the knowledge base")
async def query_knowledge_base(
    request: InputChat,
    service: ChatService = Depends(get_chat_service)
):
    """
    Query the knowledge base with a natural language question.
    
    Uses the simplified tool-calling chat agent to answer based on indexed documents.
    Supports multi-turn conversations using the provided history.
    """
    try:
        response = await service.query(
            history=request.history,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        return ResponseRAG(**response)
    
    except Exception as e:
        logger.error(f"Error processing chat query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process query"
        )
