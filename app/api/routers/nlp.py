# app/api/routers/nlp.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import json

from core.database import get_db
from services.ai_core_client.ai_core_client import get_ai_client, AICoreClient
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
    title: str
    description: str
    data_source: str
    original_user_query: str
    chart_type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class MongodbGenerationResult(BaseModel):
    mongodb_query: str
    title: str
    description: str
    data_source: str
    original_user_query: str
    chart_type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class NLPQueryResponse(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None

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

        # Step 2: Extract metadata
        prompt_message = f"""
### USER QUERY:
{request.query}
"""
        logger.info(f"Extracting metadata for query: {request.query}")
        metadata_response = await ai_client.chat(
            message=prompt_message,
            agent_id=3, 
            app_id=1    
        )
        metadata_response = metadata_response.get("response", "{}")

        try:
            parsed_metadata = json.loads(metadata_response)
        except json.JSONDecodeError:
            raise ValueError("AI response is not valid JSON")
        
        logger.info(f"Metadata extraction response: {parsed_metadata}")

        # Step 2: Select appropriate datasource
        datasources_info = [
            {"name": ds.name, "schema": ds.schema_data} for ds in datasources
        ]

        prompt_message = f"""
Select the most appropriate datasource for a user query.

### AVAILABLE DATASOURCES:
{json.dumps(datasources_info)}

### USER QUERY:
{request.query}
"""

        logger.info(f"Selecting datasource for query: {request.query}")
        # logger.info(f"Prompt message for datasource selection: {prompt_message}")
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
        schema = selected_datasource_details.schema_data or {}
        
        # Step 4: Call AI service to generate SQL
        # logger.info(f"Generating SQL for datasource: {schema}")

        database_type = selected_datasource_details.type

        if database_type.lower() == "postgresql":

            prompt_message = f"""
    Generate a SQL query for resolving the user query.

    ### AVAILABLE DATASOURCE:
    {json.dumps(schema)}

    ### USER QUERY:
    {request.query}
    """

            logger.info(f"Prompt message for SQL generation: {prompt_message}")

            generated_sql = await ai_client.chat(
                message=prompt_message,
                app_id=1,
                agent_id=1
            )

        elif database_type.lower() == "mongodb":

            prompt_message = f"""
    Generate a MongoDB query for resolving the user query.
    
    ### AVAILABLE DATASOURCE:
    {json.dumps(schema)}

    ### USER QUERY:
    {request.query}
    """

            logger.info(f"Prompt message for MongoDB query generation: {prompt_message}")

            generated_sql = await ai_client.chat(
                message=prompt_message,
                app_id=1,
                agent_id=5
            )

        if not generated_sql:
            return NLPQueryResponse(
                success=False,
                error="AI service returned empty SQL",
                suggestions=["Try rephrasing your query", "Be more specific about what data you need"]
            )
        
        generated_sql = generated_sql.get("response", "{}")
        logger.info(f"Generated SQL/MongoDB query: {generated_sql}")
        try:
            parsed_generated_sql = json.loads(generated_sql)
        except json.JSONDecodeError:
            raise ValueError("AI response is not valid JSON")

        logger.info(f"Parsed generated SQL response: {parsed_generated_sql}")
        
        if database_type.lower() == "mongodb":
            # Return MongoDB result
            return NLPQueryResponse(
                success=True,
                result=MongodbGenerationResult(
                    mongodb_query=json.dumps({
                        "collection": parsed_generated_sql.get("collection"),
                        "operation": "aggregate",
                        "pipeline": parsed_generated_sql.get("pipeline", [])
                    }),
                    original_user_query=request.query,
                    title=parsed_metadata.get("title", ""),
                    description=parsed_metadata.get("description", ""),
                    data_source=database_name,
                    chart_type=parsed_metadata.get("chart_type"),
                    config={
                        "x_column": parsed_generated_sql.get("x_column"), 
                        "y_column": parsed_generated_sql.get("y_column")
                    }
                )
            )
        
        elif database_type.lower() == "postgresql":
            # Return successful result
            return NLPQueryResponse(
                success=True,
                result=SQLGenerationResult(
                    sql=parsed_generated_sql.get("query", ""),
                    original_user_query=request.query,
                    title=parsed_metadata.get("title", ""),
                    description=parsed_metadata.get("description", ""),
                    data_source=database_name,
                    chart_type=parsed_metadata.get("chart_type"),
                    config= {"x_column": parsed_generated_sql.get("x_column"), "y_column": parsed_generated_sql.get("y_column")}
                )
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in NLP query processing: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing NLP query: {str(e)}"
        )
