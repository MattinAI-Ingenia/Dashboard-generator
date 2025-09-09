# app/schemas/data_source.py
from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class DataSourceType(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"

class DataSourceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"

class ConnectionConfig(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    database: str
    username: Optional[str] = None
    password: Optional[str] = None
    # Additional fields for different connection types
    schema: Optional[str] = "public"

class DataSourceConfig(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str
    description: Optional[str] = None
    type: DataSourceType
    connection: ConnectionConfig

class DataSourceCreate(BaseModel):
    user_id: int
    name: str
    description: Optional[str] = None
    type: DataSourceType
    connection_info: Dict[str, Any]
    status: DataSourceStatus = DataSourceStatus.ACTIVE

class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    connection_info: Optional[Dict[str, Any]] = None
    status: Optional[DataSourceStatus] = None

class TableColumn(BaseModel):
    name: str
    type: str
    nullable: bool = True
    default_value: Optional[str] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False

class TableInfo(BaseModel):
    name: str
    columns: List[TableColumn]
    row_count: Optional[int] = None
    description: Optional[str] = None

class DataSourceSchema(BaseModel):
    last_updated: Optional[datetime] = None
    tables: List[TableInfo] = []

class DataSourceInDB(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    type: DataSourceType
    connection_info: Dict[str, Any]
    status: DataSourceStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    schema_data: Optional[Dict[str, Any]] = None
    schema_updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class DataSourceResponse(DataSourceInDB):
    """Response model that hides sensitive connection details"""
    connection_info: Dict[str, Any] = {}
    
    @field_validator('connection_info', mode='before')
    @classmethod
    def hide_sensitive_info(cls, v) -> Dict[str, Any]:
        if not v:
            return {}
        
        # Handle case where v is a JSON string
        if isinstance(v, str):
            try:
                import json
                v = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return {}
        
        # Handle case where v is not a dict
        if not isinstance(v, dict):
            return {}
        
        safe_info = v.copy()
        sensitive_keys = ['password', 'secret', 'key', 'token']
        
        for key in list(safe_info.keys()):
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                safe_info[key] = "***"
        
        return safe_info
