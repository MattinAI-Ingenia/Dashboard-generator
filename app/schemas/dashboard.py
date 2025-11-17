# app/schemas/dashboard.py
from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

class VisualizationData(BaseModel):
    id: str
    chart_type: str  # bar, line, pie, table, etc.
    title: str
    data_source: str
    query: Dict[str, Any]  # e.g. {"statement": "...", "type": "sql"}
    original_query: str
    query_config: Dict[str, Any] = {}
    config: Dict[str, Any] = {}

class DashboardData(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: Optional[int] = None
    user_id: int
    name: str
    description: Optional[str] = None
    visualizations: List[VisualizationData] = []
    settings: Dict[str, Any] = {}

class DashboardCreate(BaseModel):
    user_id: int
    dashboard_data: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DashboardUpdate(BaseModel):
    dashboard_data: Optional[Dict[str, Any]] = None
    updated_at: Optional[datetime] = None

class DashboardInDB(BaseModel):
    id: int
    user_id: int
    dashboard_data: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class DashboardResponse(DashboardInDB):
    """Response model for dashboard data"""
    pass

class DashboardListItem(BaseModel):
    """Simplified dashboard info for listing"""
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    visualization_count: int
    
class DashboardList(BaseModel):
    """Paginated dashboard list response"""
    dashboards: List[DashboardListItem]
    total: int
    page: int
    limit: int
    total_pages: int
    