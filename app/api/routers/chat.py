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
    """Chat with agent with optional dashboard context"""
    message = request.query

    # Enrich message with dashboard context if provided
    if request.context and request.context.get("dashboard_id"):
        context_info = f"""
### CONTEXTO ACTUAL
Dashboard abierto: "{request.context['dashboard_name']}" (ID: {request.context['dashboard_id']})

Visualizaciones en el dashboard:
"""
        for i, viz in enumerate(request.context['visualizations'], 1):
            context_info += f"""
{i}. "{viz['title']}" (ID: {viz['id']})
   - Tipo: {viz['chart_type']}
   - Fuente de datos: {viz['data_source']}
   - Consulta original: {viz['original_query']}
   - Ejes: X={viz['x_column']}, Y={viz['y_column']}
   - Historial de ediciones: {len(viz['edit_history'])} cambios
"""
        
        message = f"{context_info}\n\n### CONSULTA DEL USUARIO\n{request.query}"
        
    metadata_response = await ai_client.chat(
        message=message,
        conversation_id=request.conversation_id,
        agent_id=11, 
        app_id=1,
        user_id=request.user_id
    )
    
    agent_response = metadata_response["response"]
    
    edit_keywords = ["editada", "actualizada", "modificada", "ahora muestra", "han sido actualizados"]
    action_taken = "visualization_edited" if any(kw in agent_response.lower() for kw in edit_keywords) else None
    
    return ChatResponse(
        response=agent_response,
        action_taken=action_taken 
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
