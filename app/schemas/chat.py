# app/schemas/chat.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language query")
    conversation_id: Optional[str] = Field(None, description="ID of the conversation context")
    user_id: Optional[int] = Field(None, description="ID of the user making the request")
    context: Optional[Dict[str, Any]] = None

class ChatResetRequest(BaseModel):
    agent_id: int = Field(..., description="ID of the chat agent to reset")
    app_id: int = Field(..., description="ID of the application")
    conversation_id: Optional[str] = Field(None, description="ID of the conversation to reset")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Response from chat agent")
    conversation_id: Optional[str] = Field(None, description="Conversation ID to use for follow-up messages")
    action_taken: Optional[str] = None

class ChatResetResponse(BaseModel):
    message: str