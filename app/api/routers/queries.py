# app/api/routers/queries.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import time
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

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/execute", response_model=QueryExecuteResponse)
def execute_query(
    request: QueryExecuteRequest,
    db: Session = Depends(get_db)
):
    """
    Execute SQL/NoSQL query against data source and return results.
    Used by frontend for data preview and dashboard rendering.
    """
    start_time = time.time()
    logging.info(f"Executing query: {request}")
    try:
        # Validate data source exists
        data_source = data_source_repository.get_by_name(db, name=request.data_source)

        if not data_source:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"Data source '{request.data_source}' not found",
                    "code": QueryErrorCode.DATA_SOURCE_ERROR
                }
            )
        
        # Validate query object
        if not request.query.statement.strip():
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
                    statement=request.query.statement,
                    limit=request.limit
                )
            elif request.query.type == QueryType.MONGODB:
                results = query_service.execute_mongodb(
                    statement=request.query.statement,
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
        
        except TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Query execution timed out",
                    "code": QueryErrorCode.TIMEOUT,
                    "details": {"timeout_seconds": query_service.timeout_seconds}
                }
            )
        
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"Invalid query: {str(e)}",
                    "code": QueryErrorCode.INVALID_QUERY,
                    "details": {"query": request.query.statement}
                }
            )
        
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"Query execution failed: {str(e)}",
                    "code": QueryErrorCode.DATA_SOURCE_ERROR,
                    "details": {
                        "data_source": request.data_source,
                        "query_type": request.query.type
                    }
                }
            )
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Log successful execution
        logger.info(
            f"Query executed successfully: {request.query.type} on {request.data_source} "
            f"({len(results)} rows, {execution_time_ms}ms)"
        )
        
        # Return response
        return QueryExecuteResponse(
            data=results,
            execution_time_ms=execution_time_ms,
            row_count=len(results),
            executed_at=datetime.now()
        )
        
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
