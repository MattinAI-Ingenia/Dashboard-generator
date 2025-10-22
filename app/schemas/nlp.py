# app/schemas/nlp.py
from pydantic import BaseModel, field_validator, ConfigDict, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

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

