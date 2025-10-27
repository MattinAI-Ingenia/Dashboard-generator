# schemas/query.py
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class QueryType(str, Enum):
    SQL = "sql"
    MONGODB = "mongodb"

class QueryErrorCode(str, Enum):
    INVALID_QUERY = "INVALID_QUERY"
    DATA_SOURCE_ERROR = "DATA_SOURCE_ERROR"
    TIMEOUT = "TIMEOUT"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"

class QueryObject(BaseModel):
    type: QueryType = Field(..., description="Type of query to execute")
    statement: str = Field(..., description="The query statement to execute")
    
    @validator('statement')
    def statement_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Query statement cannot be empty")
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "type": "sql",
                "statement": "SELECT region, SUM(revenue) FROM sales WHERE date >= ? GROUP BY region"
            }
        }

class QueryExecuteRequest(BaseModel):
    query: QueryObject = Field(..., description="Query to execute")
    data_source: str = Field(..., description="Name of the data source to query")
    limit: int = Field(
        default=1000,
        ge=1,
        le=10000,
        description="Maximum number of rows to return"
    )

class QueryExecuteResponse(BaseModel):
    data: List[Dict[str, Any]] = Field(..., description="Query result data")
    execution_time_ms: int = Field(..., description="Query execution time in milliseconds")
    row_count: int = Field(..., description="Number of rows returned")
    executed_at: datetime = Field(..., description="Timestamp when query was executed")
    
    class Config:
        schema_extra = {
            "example": {
                "data": [
                    {"region": "North", "revenue": 150000},
                    {"region": "South", "revenue": 120000},
                    {"region": "East", "revenue": 180000},
                    {"region": "West", "revenue": 95000}
                ],
                "execution_time_ms": 245,
                "row_count": 4,
                "executed_at": "2025-09-22T10:30:45.123456Z"
            }
        }

class QueryErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    code: QueryErrorCode = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "error": "Invalid SQL syntax near 'SELCT'",
                "code": "INVALID_QUERY",
                "details": {
                    "line": 1,
                    "column": 1,
                    "suggestion": "Did you mean 'SELECT'?"
                }
            }
        }

class QueryValidationResult(BaseModel):
    is_valid: bool = Field(..., description="Whether the query is valid")
    message: str = Field(..., description="Validation message")
    suggestions: Optional[List[str]] = Field(
        default=None,
        description="Suggestions for improving the query"
    )

class QueryValidationResponse(BaseModel):
    valid: bool = Field(..., description="Whether the query is valid")
    message: str = Field(..., description="Validation message")
    suggestions: Optional[List[str]] = Field(
        default=None,
        description="Suggestions for improving the query"
    )