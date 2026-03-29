from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional

class MessageItem(BaseModel):
    role: Literal["user", "assistant", "system"] = Field(..., description="Message role: user, assistant or system")
    content: str = Field(..., description="Message content")

class InputChat(BaseModel):
    user_id: str = Field(default="test0001", min_length=1, max_length=10000)
    session_id: str = Field(default="convtest0001", min_length=5, max_length=10000)
    history: List[MessageItem] = Field(..., min_items=1, max_items=100, description="Conversation message history")

class ResponseRAG(BaseModel):
    response: str
    message_id: Optional[str] = None
    agent_state: dict

class FeedbackInput(BaseModel):
    message_id: str
    user_id: str
    score: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = None

class DashboardMetricsResponse(BaseModel):
    period: Dict[str, str]
    total_conversations: int
    total_messages: int
    feedback: Dict[str, Any]

class ConversationSummary(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: str
    metadata: Dict[str, Any]