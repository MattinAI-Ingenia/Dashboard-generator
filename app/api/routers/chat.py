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


# @router.post("/", response_model=ChatResponse)
# async def chat_with_agent(
#     request: ChatRequest,
#     ai_client: AICoreClient = Depends(get_ai_client)
# ) -> ChatResponse:
#     """Chat with agent with optional dashboard context"""
#     message = request.query

#     # Enrich message with dashboard context if provided
#     if request.context and request.context.get("dashboard_id"):
#         context_info = f"""
# ### CONTEXTO ACTUAL
# Dashboard abierto: "{request.context['dashboard_name']}" (ID: {request.context['dashboard_id']})

# Visualizaciones en el dashboard:
# """
#         for i, viz in enumerate(request.context['visualizations'], 1):
#             context_info += f"""
# {i}. "{viz['title']}" (ID: {viz['id']})
#    - Tipo: {viz['chart_type']}
#    - Fuente de datos: {viz['data_source']}
#    - Consulta original: {viz['original_query']}
#    - Ejes: X={viz['x_column']}, Y={viz['y_column']}
#    - Historial de ediciones: {len(viz['edit_history'])} cambios
# """
        
#         message = f"{context_info}\n\n### CONSULTA DEL USUARIO\n{request.query}"
        
#     metadata_response = await ai_client.chat(
#         message=message,
#         conversation_id=request.conversation_id,
#         agent_id=11, 
#         app_id=1,
#         user_id=request.user_id
#     )
    
#     agent_response = metadata_response["response"]
    
#     edit_keywords = ["editada", "actualizada", "modificada", "ahora muestra", "han sido actualizados", "transformada"]
#     action_taken = "visualization_edited" if any(kw in agent_response.lower() for kw in edit_keywords) else None
    
#     return ChatResponse(
#         response=agent_response,
#         action_taken=action_taken 
#     )

@router.post("/", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    ai_client: AICoreClient = Depends(get_ai_client)
) -> ChatResponse:
    """Chat with agent with optional dashboard and data sources context"""
    message = request.query
    context_info = ""

    # Handle new context structure: {dashboard: {...}, data_sources: [...]}
    dashboard_context = None
    data_sources_context = None
    
    if request.context:
        # New structure with separate dashboard and data_sources
        if "dashboard" in request.context:
            dashboard_context = request.context["dashboard"]
        # Legacy support: direct dashboard_id in context
        elif "dashboard_id" in request.context:
            dashboard_context = request.context
            
        if "data_sources" in request.context:
            data_sources_context = request.context["data_sources"]

    # Add dashboard context if available
    if dashboard_context and dashboard_context.get("dashboard_id"):
        context_info += f"""
### DASHBOARD ACTUAL
Dashboard abierto: "{dashboard_context['dashboard_name']}" (ID: {dashboard_context['dashboard_id']})
Descripción: {dashboard_context.get('description', 'N/A')}

Visualizaciones en el dashboard:
"""
        for i, viz in enumerate(dashboard_context['visualizations'], 1):
            context_info += f"""
{i}. "{viz['title']}" (ID: {viz['id']})
   - Tipo: {viz['chart_type']}
   - Fuente de datos: {viz['data_source']}
   - Consulta original: {viz['original_query']}
   - Ejes: X={viz['x_column']}, Y={viz['y_column']}
   - Historial de ediciones: {len(viz['edit_history'])} cambios
"""

    # Add data sources context if available
    if data_sources_context:
        context_info += f"""

### FUENTES DE DATOS DISPONIBLES
"""
        for ds in data_sources_context:
            context_info += f"""
📊 {ds['name']} (ID: {ds['id']})
   - Tipo: {ds['type']}
   - Descripción: {ds.get('description', 'N/A')}
"""
            # Add schema information
            if ds.get('schema'):
                schema = ds['schema']
                # SQL databases
                if schema.get('schemas'):
                    for schema_info in schema['schemas']:
                        context_info += f"\n   Schema: {schema_info['schema_name']}\n"
                        if schema_info.get('tables'):
                            context_info += "   Tablas:\n"
                            for table in schema_info['tables'][:5]:  # Limit to first 5 tables
                                cols = ', '.join([col['name'] for col in table['columns'][:10]])  # First 10 columns
                                context_info += f"     - {table['name']}: {cols}\n"
                
                # MongoDB databases
                if schema.get('databases'):
                    for db_info in schema['databases']:
                        context_info += f"\n   Database: {db_info['database_name']}\n"
                        if db_info.get('collections'):
                            context_info += "   Colecciones:\n"
                            for collection in db_info['collections'][:5]:  # Limit to first 5 collections
                                fields = ', '.join([field['name'] for field in collection['fields'][:10]])
                                context_info += f"     - {collection['name']}: {fields}\n"
        
    if context_info:
        message = f"{context_info}\n\n### CONSULTA DEL USUARIO\n{request.query}"
        
    metadata_response = await ai_client.chat(
        message=message,
        conversation_id=request.conversation_id,
        agent_id=11, 
        app_id=1,
        user_id=request.user_id
    )
    
    agent_response = metadata_response["response"]
    returned_conversation_id = metadata_response.get("conversation_id")
    
    # Detect action type
    edit_keywords = ["editada", "actualizada", "modificada", "ahora muestra", "han sido actualizados", "transformada"]
    add_keywords = ["añadida", "agregada", "creada", "nueva visualización", "he añadido", "he agregado"]
    
    action_taken = None
    if any(kw in agent_response.lower() for kw in edit_keywords):
        action_taken = "visualization_edited"
    elif any(kw in agent_response.lower() for kw in add_keywords):
        action_taken = "visualization_added"
    
    return ChatResponse(
        response=agent_response,
        conversation_id=returned_conversation_id,
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
