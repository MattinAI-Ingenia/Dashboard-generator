# app/api/routers/nlp.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import json

from core.database import get_db
from services.ai_core_client import get_ai_client, AICoreClient
# from services.nlp.datasource_selector import DatasourceSelector
from repositories.data_source import data_source_repository

router = APIRouter()
logger = logging.getLogger(__name__)

# Schemas
class NLPQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language query")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

class DatasourceInfo(BaseModel):
    id: int
    name: str
    type: str
    schema_info: Dict[str, Any]

class SQLGenerationResult(BaseModel):
    sql: str
    datasource: DatasourceInfo
    confidence: float
    explanation: Optional[str] = None

class NLPQueryResponse(BaseModel):
    success: bool
    result: Optional[SQLGenerationResult] = None
    error: Optional[str] = None
    suggestions: Optional[List[str]] = None

def get_ai_client() -> AICoreClient:
    return AICoreClient()

@router.post("/query", response_model=NLPQueryResponse)
async def generate_sql_from_nlp(
    request: NLPQueryRequest,
    db: Session = Depends(get_db),
    ai_client: AICoreClient = Depends(get_ai_client)
):
    """
    Generate SQL from natural language query using AI service:
    1. Select appropriate datasource
    2. Generate SQL
    3. Validate 
    """
    try:
        # Step 1: Get all available datasources
        datasources = data_source_repository.get_all(db)
        logger.info(f"Found {len(datasources)} datasources in the system.")
        if not datasources:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No datasources configured"
            )
        
        # Step 2: Select appropriate datasource
        datasources_info = [
            {"name": ds.name, "schema": ds.schema_data} for ds in datasources
        ]

        prompt_message = f"""
Select the most appropriate datasource from a list for a user query.

### AVAILABLE DATASOURCES:
{json.dumps(datasources_info)}

### USER QUERY:
{request.query}
"""

        logger.info(f"Selecting datasource for query: {request.query}")
        logger.info(f"Prompt message for datasource selection: {prompt_message}")
        selected_datasource = await ai_client.chat(
            message=prompt_message,
            agent_id=2, 
            app_id=1    
        )

        selected_datasource = selected_datasource.get("response", "{}")

        try:
            parsed_selected_datasource = json.loads(selected_datasource)
        except json.JSONDecodeError:
            raise ValueError("AI response is not valid JSON")

        logger.info(f"Parsed datasource selection response: {parsed_selected_datasource}")

        # Now safely access the database_name
        database_name = parsed_selected_datasource.get("database_name")

        selected_datasource_details = data_source_repository.get_by_name(
            db, name=database_name
        )

        if not selected_datasource_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Datasource {database_name} not found"
            )
        
        # Prepare schema for AI service
        schema = selected_datasource_details.get('schema_data', {})
        
        # Step 4: Call AI service to generate SQL
        logger.info(f"Generating SQL for datasource: {datasource_details.name}")
        try:
            generated_sql = await ai_client.generate_sql(
                prompt=request.query,
                schema=schema
            )
        except httpx.HTTPError as e:
            logger.error(f"AI service error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AI service unavailable: {str(e)}"
            )
        
        # if not generated_sql:
        #     return NLPQueryResponse(
        #         success=False,
        #         error="AI service returned empty SQL",
        #         suggestions=["Try rephrasing your query", "Be more specific about what data you need"]
        #     )
        
        # # Step 5: Validate with AI service
        # try:
        #     is_valid = await ai_client.validate_query(
        #         sql_query=generated_sql,
        #         schema=schema
        #     )
        # except httpx.HTTPError as e:
        #     logger.warning(f"Validation service error: {str(e)}, skipping validation")
        #     is_valid = True  # Proceed if validation service is down
        
        # if not is_valid:
        #     logger.warning(f"Generated SQL failed validation: {generated_sql}")
        #     return NLPQueryResponse(
        #         success=False,
        #         error="Generated query failed validation",
        #         suggestions=["Try a simpler query", "Check table and column names"]
        #     )
        
        # Return successful result
        # return NLPQueryResponse(
        #     success=True,
        #     result=SQLGenerationResult(
        #         sql=generated_sql,
        #         datasource=DatasourceInfo(
        #             id=datasource_details.id,
        #             name=datasource_details.name,
        #             type=datasource_details.type,
        #             schema_info=schema
        #         ),
        #         confidence=0.8,  # Could be returned by AI service
        #         explanation=f"Query generated for {datasource_details.name} datasource"
        #     )
        # )

        return selected_datasource_details
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in NLP query processing: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing NLP query: {str(e)}"
        )
