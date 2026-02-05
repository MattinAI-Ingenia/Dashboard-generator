# app/services/ai_core_client.py
from pyexpat.errors import messages
import httpx
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

from core.config import settings

logger = logging.getLogger(__name__)


class SQLGenerationRequest(BaseModel):
    prompt: str
    schema: Dict[str, Any]
    datasource_type: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class SQLGenerationResponse(BaseModel):
    sql_query: str
    confidence: Optional[float] = None
    explanation: Optional[str] = None


class QueryValidationRequest(BaseModel):
    sql_query: str
    schema: Dict[str, Any]
    datasource_type: Optional[str] = None


class QueryValidationResponse(BaseModel):
    is_valid: bool
    errors: Optional[list] = None
    warnings: Optional[list] = None
    suggestions: Optional[list] = None


class AICoreClient:
    """Client for external AI service that generates and validates SQL"""
    
    def __init__(self, base_url: str = None, timeout: int = 30):
        self.base_url = "http://172.16.59.1:8083"
        self.timeout = settings.AI_CORE_TIMEOUT or timeout
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "X-API-KEY": settings.AI_CORE_API_KEY
            }
        )

    async def chat(self, message: str, conversation_id: str, agent_id: int, app_id: int, user_id: int = None) -> str:
        """
        Send chat messages to AI service and get response
       
        Args:
            message: Message content to send
           
        Returns:
            AI-generated response string
           
        Raises:
            httpx.HTTPError: If request fails
        """
        import uuid
       
        enriched_message = f"[USER_ID: {user_id}] {message}" if user_id else message
 
        # Use form data as expected by the server
        # Always provide a conversation_id (server requires it)
        form_data = {
            "message": enriched_message,
            "conversation_id": conversation_id or str(uuid.uuid4()),
        }
 
        logger.info(f"Preparing chat request for agent_id={agent_id}, app_id={app_id}")
        logger.info(f"Chat payload being sent: {form_data}")
 
        try:
            response = await self.client.post(
                f"/public/v1/app/{app_id}/chat/{agent_id}/call",
                data=form_data
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"Received chat response from AI service {data}.")
            return data
           
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from AI service: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error to AI service: {str(e)}")
            raise

    async def chat_memory(self, message: str, agent_id: int, app_id: int) -> str:
        """
        Send chat messages to AI service and get response
        
        Args:
            message: Message content to send
            
        Returns:
            AI-generated response string
            
        Raises:
            httpx.HTTPError: If request fails
        """
        payload = {"message": message}
        logger.info(f"Preparing chat request for agent_id={agent_id}, app_id={app_id} \n")
        # logger.info(f"Payload: {payload}")

        try:
            # Use files parameter to send as multipart/form-data
            multipart_data = {
                "message": (None, message),
            }
            response = await self.client.post(
                f"/public/v1/app/{app_id}/chat/{agent_id}/call",
                files=multipart_data
            )
            response.raise_for_status()
            data = response.json()
            logger.info("Received chat response from AI service.")
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from AI service: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error to AI service: {str(e)}")
            raise

    async def reset_chat(self, conversation_id: str, agent_id: int, app_id: int) -> str:
        """
        Reset chat session in AI service
        
        Args:
            conversation_id: ID of the conversation to reset
            
        Returns:
            Confirmation message from AI service
            
        Raises:
            httpx.HTTPError: If request fails
        """
        params = {}
        if conversation_id:
            params["conversation_id"] = conversation_id
            
        logger.info(f"Preparing reset chat request for agent_id={agent_id}, app_id={app_id} \n")

        try:
            response = await self.client.post(f"/public/v1/app/{app_id}/chat/{agent_id}/reset", params=params)
            response.raise_for_status()
            data = response.json()
            logger.info("Chat session reset successfully in AI service.")
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from AI service: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error to AI service: {str(e)}")
            raise

    async def generate_sql(
        self, 
        prompt: str, 
        schema: Dict[str, Any],
        datasource_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> SQLGenerationResponse:
        """
        Generate SQL from natural language prompt
        
        Args:
            prompt: Natural language query
            schema: Database schema information
            datasource_type: Type of datasource (postgres, mysql, mongodb, etc.)
            context: Additional context for generation
            
        Returns:
            SQLGenerationResponse with generated SQL and metadata
            
        Raises:
            httpx.HTTPError: If request fails
        """
        print('ENTRA AQUI 2')
        payload = SQLGenerationRequest(
            prompt=prompt,
            schema=schema,
            datasource_type=datasource_type,
            context=context
        )
        
        logger.info(f"Requesting SQL generation for prompt: {prompt[:100]}...")
        
        try:
            response = await self.client.post(
                "/generate-sql", 
                json=payload.model_dump(exclude_none=True)
            )
            response.raise_for_status()
            data = response.json()
            
            result = SQLGenerationResponse(**data)
            logger.info(f"SQL generated successfully (confidence: {result.confidence})")
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from AI service: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error to AI service: {str(e)}")
            raise

    async def validate_query(
        self, 
        sql_query: str, 
        schema: Dict[str, Any],
        datasource_type: Optional[str] = None
    ) -> QueryValidationResponse:
        """
        Validate SQL query
        
        Args:
            sql_query: SQL query to validate
            schema: Database schema information
            datasource_type: Type of datasource
            
        Returns:
            QueryValidationResponse with validation results
            
        Raises:
            httpx.HTTPError: If request fails
        """
        payload = QueryValidationRequest(
            sql_query=sql_query,
            schema=schema,
            datasource_type=datasource_type
        )
        
        logger.info(f"Validating SQL query: {sql_query[:100]}...")
        
        try:
            response = await self.client.post(
                "/validate-query",
                json=payload.model_dump(exclude_none=True)
            )
            response.raise_for_status()
            data = response.json()
            
            result = QueryValidationResponse(**data)
            logger.info(f"Validation complete: valid={result.is_valid}")
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from validation service: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error to validation service: {str(e)}")
            raise

    async def health_check(self) -> bool:
        """Check if AI service is available"""
        try:
            response = await self.client.get("/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed: {str(e)}")
            return False

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# Singleton instance
_ai_client: Optional[AICoreClient] = None

def get_ai_client() -> AICoreClient:
    """Get or create AI client singleton"""
    global _ai_client
    if _ai_client is None:
        _ai_client = AICoreClient()
    return _ai_client