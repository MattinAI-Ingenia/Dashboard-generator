# app/api/routers/queries.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import time
import json
from enum import Enum

from core.database import get_db
from repositories.data_source import data_source_repository
from schemas.query import (
    QueryExecuteRequest,
    QueryExecuteResponse,
    QueryType,
    QueryObject,
    QueryErrorResponse,
    QueryErrorCode
)
from services.query_executor import QueryExecutorService
from services.ai_core_client.ai_core_client import get_ai_client, AICoreClient

router = APIRouter()
logger = logging.getLogger(__name__)

def get_ai_client() -> AICoreClient:
    return AICoreClient()

@router.post("/execute", response_model=QueryExecuteResponse)
async def execute_query(
    request: QueryExecuteRequest,
    db: Session = Depends(get_db),
    ai_client: AICoreClient = Depends(get_ai_client)
):

    """
    Execute SQL/NoSQL query against data source and return results.
    Used by frontend for data preview and dashboard rendering.
    """
    start_time = time.time()
    logging.info(f"Executing query: {request}")
    max_retries = 2  # Original + 1 retry
    current_query = request.query.statement
    
    for attempt in range(max_retries):
        try:
            # Validate data source exists
            data_source = data_source_repository.get_by_name(db, name=request.data_source)
            logging.info(f"EXISTE DATASOURCE: {data_source}")

            if not data_source:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": f"Data source '{request.data_source}' not found",
                        "code": QueryErrorCode.DATA_SOURCE_ERROR
                    }
                )
            
            # Validate query object
            if not current_query.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Query statement cannot be empty",
                        "code": QueryErrorCode.INVALID_QUERY,
                        "details": {"field": "statement"}
                    }
                )
            
            # Apply limit validation
            if request.limit > 10000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Limit exceeds maximum allowed value of 10000",
                        "code": QueryErrorCode.LIMIT_EXCEEDED,
                        "details": {"max_limit": 10000, "requested_limit": request.limit}
                    }
                )
            
            # Initialize query executor service
            query_service = QueryExecutorService(data_source)

            # Execute query based on type
            try:
                if request.query.type == QueryType.SQL:
                    results = query_service.execute_sql(
                        statement=current_query,
                        limit=request.limit
                    )
                elif request.query.type == QueryType.MONGODB:
                    results = query_service.execute_mongodb(
                        statement=current_query,
                        limit=request.limit
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "error": f"Unsupported query type: {request.query.type}",
                            "code": QueryErrorCode.INVALID_QUERY,
                            "details": {"supported_types": ["sql", "mongodb"]}
                        }
                    )
                
                # Calculate execution time
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                # Log successful execution
                logger.info(
                    f"Query executed successfully on attempt {attempt + 1}: {request.query.type} on {request.data_source} "
                    f"({len(results)} rows, {execution_time_ms}ms)"
                )
                
                # Return response
                return QueryExecuteResponse(
                    data=results,
                    execution_time_ms=execution_time_ms,
                    row_count=len(results),
                    executed_at=datetime.now()
                )
            
            except (TimeoutError, ValueError, Exception) as execution_error:
                # If this is the last attempt, raise the error
                if attempt == max_retries - 1:
                    logger.error(f"Query execution failed after {max_retries} attempts: {str(execution_error)} \n")
                    
                    if isinstance(execution_error, TimeoutError):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail={
                                "error": "Query execution timed out",
                                "code": QueryErrorCode.TIMEOUT,
                                "details": {"timeout_seconds": query_service.timeout_seconds}
                            }
                        )
                    elif isinstance(execution_error, ValueError):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail={
                                "error": f"Invalid query: {str(execution_error)}",
                                "code": QueryErrorCode.INVALID_QUERY,
                                "details": {"query": current_query}
                            }
                        )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail={
                                "error": f"Query execution failed: {str(execution_error)}",
                                "code": QueryErrorCode.DATA_SOURCE_ERROR,
                                "details": {
                                    "data_source": request.data_source,
                                    "query_type": request.query.type
                                }
                            }
                        )
                
                # Fallback: Use AI to fix the query
                logger.warning(f"Query execution failed on attempt {attempt + 1}, activating fallback mechanism")
                logger.info(f"Error details: {str(execution_error)}")
                
                # Prepare schema for AI service
                schema = data_source.schema_data or {}
                database_type = data_source.type
                
                # Step 1: Validate the failed query and get suggestions
                if database_type.lower() == "postgresql":
                    validation_prompt = f"""
                    Analyze why this SQL query failed during execution and suggest a fix.

                    ### DATABASE SCHEMA:
                    {json.dumps(schema)}

                    ### FAILED SQL QUERY:
                    {current_query}

                    ### EXECUTION ERROR:
                    {str(execution_error)}

                    ### ORIGINAL USER INTENT:
                    {getattr(request, 'original_user_query', 'User wanted to query the database')}
                    """

                elif database_type.lower() == "mongodb":
                    validation_prompt = f"""
                    Analyze why this MongoDB query failed during execution and suggest a fix.

                    ### DATABASE SCHEMA:
                    {json.dumps(schema)}

                    ### FAILED MONGODB QUERY:
                    {current_query}

                    ### EXECUTION ERROR:
                    {str(execution_error)}

                    ### ORIGINAL USER INTENT:
                    {getattr(request, 'original_user_query', 'User wanted to query the database')}
                    """
                
                logger.info(f"Requesting query fix from validator agent (agent 6)")
                
                validation_response = await ai_client.chat(
                    message=validation_prompt,
                    app_id=1,
                    conversation_id=None,
                    user_id=None,
                    agent_id=6
                )
                
                validation_response = validation_response.get("response", "{}")
                logger.info(f"Validator response: {validation_response}")
                
                try:
                    parsed_validation = json.loads(validation_response)
                    suggested_fix = parsed_validation.get("suggested_fix")
                    
                    if not suggested_fix:
                        logger.error("Validator did not provide a suggested fix")
                        continue  # Try again without changes (will fail on last attempt)
                    
                    logger.info(f"Validator suggested fix: {suggested_fix}")
                    
                except json.JSONDecodeError:
                    logger.error("Validator response is not valid JSON")
                    continue  # Try again without changes
                
                # Step 2: Generate new query with the fix information
                if database_type.lower() == "postgresql":
                    regeneration_prompt = f"""
                    Generate a corrected SQL query based on the validation feedback.

                    ### DATABASE SCHEMA:
                    {json.dumps(schema)}

                    ### ORIGINAL FAILED QUERY:
                    {current_query}

                    ### ERROR THAT OCCURRED:
                    {str(execution_error)}

                    ### SUGGESTED FIX:
                    {suggested_fix}

                    ### USER INTENT:
                    {getattr(request, 'original_user_query', 'Query the database')}

                    Generate a new, corrected SQL query that addresses the error.
                    """
                    
                    logger.info(f"Regenerating SQL query with agent 1")
                    
                    regenerated_response = await ai_client.chat(
                        message=regeneration_prompt,
                        app_id=1,
                        conversation_id=None,
                        user_id=None,
                        agent_id=1
                    )
                    
                elif database_type.lower() == "mongodb":
                    regeneration_prompt = f"""
                    Generate a corrected MongoDB query based on the validation feedback.

                    ### DATABASE SCHEMA:
                    {json.dumps(schema)}

                    ### ORIGINAL FAILED QUERY:
                    {current_query}

                    ### ERROR THAT OCCURRED:
                    {str(execution_error)}

                    ### SUGGESTED FIX:
                    {suggested_fix}

                    ### USER INTENT:
                    {getattr(request, 'original_user_query', 'Query the database')}

                    Generate a new, corrected MongoDB query that addresses the error.
                    """
                    
                    logger.info(f"Regenerating MongoDB query with agent 5")
                    
                    regenerated_response = await ai_client.chat(
                        message=regeneration_prompt,
                        app_id=1,
                        conversation_id=None,
                        user_id=None,
                        agent_id=5
                    )
                
                regenerated_response = regenerated_response.get("response", "{}")
                logger.info(f"Regenerated query response: {regenerated_response}")
                
                try:
                    parsed_regenerated = json.loads(regenerated_response)
                    
                    if database_type.lower() == "postgresql":
                        new_query = parsed_regenerated.get("query", "")
                    elif database_type.lower() == "mongodb":
                        new_query = json.dumps({
                            "collection": parsed_regenerated.get("collection"),
                            "operation": "aggregate",
                            "pipeline": parsed_regenerated.get("pipeline", [])
                        })
                    
                    if not new_query or new_query == current_query:
                        logger.warning("Regenerated query is empty or identical to failed query")
                        continue
                    
                    logger.info(f"New query generated, retrying execution: {new_query}")
                    current_query = new_query
                    
                except json.JSONDecodeError:
                    logger.error("Regenerated query response is not valid JSON")
                    continue
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in query execution: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Internal server error during query execution",
                    "code": QueryErrorCode.DATA_SOURCE_ERROR,
                    "details": {"message": str(e)}
                }
            )
        