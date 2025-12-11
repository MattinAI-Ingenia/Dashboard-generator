# app/api/routers/nlp.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import json
import datetime

from core.database import get_db
from services.ai_core_client.ai_core_client import get_ai_client, AICoreClient
# from services.nlp.datasource_selector import DatasourceSelector
from schemas.chat import ChatRequest, ChatResponse, ChatResetRequest, ChatResetResponse

router = APIRouter()
logger = logging.getLogger(__name__)


def get_ai_client() -> AICoreClient:
    return AICoreClient()


@router.post("/", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    ai_client: AICoreClient = Depends(get_ai_client)
) -> ChatResponse:
    """Wrapper function to generate query from NLP request"""

    logger.info(f"Chat with this payload: {request.query}")
    metadata_response = await ai_client.chat(
        message=request.query,
        conversation_id=request.conversation_id if request.conversation_id else None,
        agent_id=11, 
        app_id=1,
        user_id=request.user_id if request.user_id else None
    )
    print("Metadata response:", metadata_response)
    # Extract just the response text
    agent_response = metadata_response["response"]
    
    return ChatResponse(
        response=agent_response
    )

@router.post("/reset", response_model=ChatResetResponse)
async def reset_chat_session(
    request: ChatResetRequest,
    ai_client: AICoreClient = Depends(get_ai_client)
) -> ChatResetResponse:
    """Reset chat session"""

    logger.info(f"Resetting chat session for context: {request.conversation_id}")
    reset_response = await ai_client.reset_chat(
        app_id=request.app_id,
        agent_id=request.agent_id,
        conversation_id=request.conversation_id   
    )
    logger.info(f"Chat session reset response: {reset_response}")

    return ChatResetResponse(message=reset_response["message"])
