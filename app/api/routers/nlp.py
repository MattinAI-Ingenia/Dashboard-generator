# app/api/routers/nlp.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import json
import datetime
import os
from pathlib import Path

from core.database import get_db
from services.ai_core_client.ai_core_client import get_ai_client, AICoreClient
# from services.nlp.datasource_selector import DatasourceSelector
from repositories.data_source import data_source_repository

router = APIRouter()
logger = logging.getLogger(__name__)

# Load prompts from external markdown files
def load_prompts():
    """Load prompts from individual markdown files in prompts/ directory"""
    prompts_dir = Path(__file__).parent.parent.parent / "prompts"
    if not prompts_dir.exists():
        logger.warning(f"Prompts directory not found at {prompts_dir}")
        return {}
    
    prompts = {}
    for prompt_file in prompts_dir.glob("*.md"):
        prompt_name = prompt_file.stem  # filename without extension
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompts[prompt_name] = f.read().strip()
        except Exception as e:
            logger.warning(f"Error loading prompt file {prompt_file}: {e}")
    
    return prompts

PROMPTS = load_prompts()

def get_prompt(prompt_name: str, **kwargs) -> str:
    """Get a prompt template and format it with provided kwargs"""
    template = PROMPTS.get(prompt_name, "")
    if not template:
        logger.warning(f"Prompt '{prompt_name}' not found")
        return ""
    
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.warning(f"Missing key in prompt template: {e}")
        return template

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
    edit_history: List[Dict[str, Any]] = []
    chart_type: Optional[str] = None
    query_config: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None

class MongodbGenerationResult(BaseModel):
    mongodb_query: str
    title: str
    description: str
    data_source: str
    original_user_query: str
    edit_history: List[Dict[str, Any]] = []
    chart_type: Optional[str] = None
    query_config: Optional[Dict[str, Any]] = None
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
        prompt_message = get_prompt("metadata_extraction", user_query=request.query)
        logger.info(f"Extracting metadata for query: {request.query}")
        metadata_response = await ai_client.chat(
            message=prompt_message,
            user_id=None,
            conversation_id=None,
            agent_id=3, 
            app_id=1    
        )
        metadata_response = metadata_response.get("response", "{}")

        try:
            parsed_metadata = json.loads(metadata_response)
        except json.JSONDecodeError:
            raise ValueError("AI response is not valid JSON")
        
        logger.info(f"Metadata extraction response: {parsed_metadata} \n")

        # Step 2: Select appropriate datasource
        datasources_info = [
            {"name": ds.name, "schema": ds.schema_data} for ds in datasources
        ]

        prompt_message = get_prompt("datasource_selection", datasources_info=json.dumps(datasources_info), user_query=request.query)

        logger.info(f"Selecting datasource for query: {request.query}")
        logger.info(f"Prompt message for datasource selection: {prompt_message}")
        # generated_sql = await ai_client.chat(
        #     message=prompt_message,
        #     conversation_id=None,
        #     user_id=None,
        #     agent_id=12, 
        #     app_id=1    
        # )
        logger.info(f"AI response for SQL generation: {generated_sql}")


        logger.info(f"Selecting datasource for query: {request.query}")
        logger.info(f"Prompt message for datasource selection: {prompt_message}")
        selected_datasource = await ai_client.chat(
            message=prompt_message,
            agent_id=15, 
            app_id=1    
        )
        logger.info('--- Selected datasource response ---')
        logger.info(f"Datasource selection response: {selected_datasource} \n")
        selected_datasource = selected_datasource.get("response", "{}")
        logger.info(f"selected_datasource: {selected_datasource} \n")

        try:
            parsed_selected_datasource = json.loads(selected_datasource)
        except json.JSONDecodeError:
            raise ValueError("AI response is not valid JSON")

        logger.info(f"Parsed datasource selection response: {parsed_selected_datasource} \n")

        # Now safely access the database_name
        database_name = parsed_selected_datasource.get("database_name")
        logger.info(f"Selected database name: {database_name} \n")

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
        logger.info(f"Generating SQL for datasource: {schema}")

        database_type = selected_datasource_details.type

        if database_type.lower() == "postgresql":

            prompt_message = f"""
                Generate a SQL query for resolving the user query.

                ### AVAILABLE DATASOURCE:
                {json.dumps(schema)}

                ### METADATA
                {parsed_metadata.get("chart_type", "")}

                ### USER QUERY:
                {request.query}
                """

            # logger.info(f"Prompt message for SQL generation: {prompt_message}")
            logger.info(f"Generating SQL for PostgreSQL with prompt: {prompt_message}")

            generated_sql = await ai_client.chat(
                message=prompt_message,
                app_id=1,
                agent_id=10
            )
            logger.info(f"AI response for SQL generation: {generated_sql}")


        elif database_type.lower() == "mongodb":

            prompt_message = f"""
                Generate a MongoDB query for resolving the user query.
                
                ### AVAILABLE DATASOURCE:
                {json.dumps(schema)}

                ### METADATA
                {parsed_metadata.get("chart_type", "")}

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
        # logger.info(f"Generated SQL/MongoDB query: {generated_sql} \n")
        try:
            parsed_generated_sql = json.loads(generated_sql)
        except json.JSONDecodeError:
            raise ValueError("AI response is not valid JSON")

        logger.info(f"Parsed generated SQL response: {parsed_generated_sql} \nPreparing chat request for agent_i")
        database_type= parsed_generated_sql.get("database_type")
        parsed_generated_sql.pop('database_type', None)
        # database_type="PostgreSQL"
        print(database_type)
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
                    # data_source=database_name,
                    data_source= parsed_generated_sql.get("database_name"),
                    chart_type=parsed_metadata.get("chart_type"),
                    config= parsed_metadata.get("config"),
                    query_config={
                        "x_column": parsed_generated_sql.get("x_column"), 
                        "y_column": parsed_generated_sql.get("y_column")
                    }
                )
            )
        
        elif database_type.lower() == "postgresql":
            logger.info("ES POSTGRESQL")
            # Return successful result
            return NLPQueryResponse(
                success=True,
                result=SQLGenerationResult(
                    sql=parsed_generated_sql.get("query", ""),
                    original_user_query=request.query,
                    title=parsed_metadata.get("title", ""),
                    description=parsed_metadata.get("description", ""),
                    # data_source=database_name,
                    data_source= parsed_generated_sql.get("database_name"),
                    chart_type=parsed_metadata.get("chart_type"),
                    query_config={
                        "x_column": parsed_generated_sql.get("x_column"), 
                        "y_column": parsed_generated_sql.get("y_column")
                    }, 
                    config= parsed_metadata.get("config")
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

@router.post("/query/orchestrator", response_model=NLPQueryResponse)
async def generate_query_from_nlp(
    request: NLPQueryRequest,
    db: Session = Depends(get_db),
    ai_client: AICoreClient = Depends(get_ai_client)
) -> NLPQueryResponse:
    """Wrapper function to generate query from NLP request"""

    return await generate_sql_from_nlp(request, db, ai_client)

@router.post("/query/edit", response_model=NLPQueryResponse)
async def edit_visualization_query(
    request: dict,  # Contains: original_viz, edit_instructions
    db: Session = Depends(get_db),
    ai_client: AICoreClient = Depends(get_ai_client)
):
    """Edit existing visualization based on natural language instructions"""
    try:
        original_viz = request.get("original_visualization")
        edit_instructions = request.get("edit_instructions")
        logger.info(f"original viz: {original_viz} \n")
        logger.info(f"edit instructions: {edit_instructions} \n")

        # Get datasource
        datasource = data_source_repository.get_by_name(
            db, name=original_viz["data_source"]
        )
        
        if not datasource:
            raise HTTPException(404, "Datasource not found")
        
        database_type = datasource.type.lower()
        schema = datasource.schema_data or {}
        edit_history = original_viz.get("edit_history", [])

        logger.info(f"edit_history: {edit_history} \n")
        logger.info(f"database: {database_type} \n")
        logger.info(f"schema: {schema} \n")

        # Build context prompt
        if database_type == "mongodb":
            original_query = original_viz.get("mongodb_query", "")
        else:
            original_query = original_viz.get("sql", "")
        
        history_context = "\n".join([
            f"Edit {i+1}: {edit['instruction']}"
            for i, edit in enumerate(edit_history)
        ])

        original_user_query = original_viz.get("original_user_query")

        # Get metadata
        prompt_message = get_prompt("metadata_update", 
                                   original_user_query=original_user_query,
                                   history_context=history_context if history_context else "No previous edits",
                                   edit_instructions=edit_instructions)
        
        metadata_response = await ai_client.chat(
            message=prompt_message,
            agent_id=3,
            conversation_id=None,
            user_id=None,
            app_id=1
        )

        parsed_metadata = json.loads(metadata_response.get("response", "{}"))
        logger.info(f"parsed metadata: {parsed_metadata}")

        # Edit query
        prompt = get_prompt("query_edit",
                           title=original_viz['title'],
                           chart_type=original_viz['chart_type'],
                           data_source=original_viz['data_source'],
                           original_user_query=original_user_query,
                           last_query=original_query,
                           x_column=original_viz['query_config']['x_column'],
                           y_column=original_viz['query_config']['y_column'],
                           new_chart_type=parsed_metadata.get("chart_type"),
                           history_context=history_context if history_context else "No previous edits",
                           schema=json.dumps(schema),
                           edit_instructions=edit_instructions)
        
        # Call appropriate agent
        agent_id = 5 if database_type == "mongodb" else 1
        generated = await ai_client.chat(message=prompt, app_id=1, conversation_id=None, user_id=None, agent_id=agent_id)
        parsed = json.loads(generated.get("response", "{}"))
        logger.info(f"generated edited query: {parsed}")

        # Append to edit history
        new_edit = {
            "timestamp": datetime.datetime.now().isoformat(),
            "instruction": edit_instructions
            }
    
        edit_history.append(new_edit)

        # Return result
        if database_type == "mongodb":
            return NLPQueryResponse(
                success=True,
                result=MongodbGenerationResult(
                    mongodb_query=json.dumps({
                        "collection": parsed.get("collection"),
                        "operation": "aggregate",
                        "pipeline": parsed.get("pipeline", [])
                    }),
                    original_user_query=original_user_query,
                    title=parsed_metadata.get("title", original_viz['title']),
                    description=parsed_metadata.get("description", ""),
                    data_source=original_viz["data_source"],
                    chart_type=parsed_metadata.get("chart_type", original_viz['chart_type']),
                    config=parsed_metadata.get("config", original_viz.get('config', {})),
                    query_config={
                        "x_column": parsed.get("x_column"),
                        "y_column": parsed.get("y_column")
                    }, 
                    edit_history=edit_history
                )
            )
        
        else:
            return NLPQueryResponse(
                success=True,
                result=SQLGenerationResult(
                    sql=parsed.get("query", ""),
                    original_user_query=original_user_query,
                    title=parsed_metadata.get("title", original_viz['title']),
                    description=parsed_metadata.get("description", ""),
                    data_source=original_viz["data_source"],
                    chart_type=parsed_metadata.get("chart_type", original_viz['chart_type']),
                    query_config={
                        "x_column": parsed.get("x_column"),
                        "y_column": parsed.get("y_column")
                    },
                    config=parsed_metadata.get("config", original_viz.get('config', {})),
                    edit_history=edit_history
                )
            )
        
    except Exception as e:
        logger.error(f"Edit error: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Edit failed: {str(e)}")
