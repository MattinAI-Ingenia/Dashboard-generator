# app/repositories/dashboard.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from db.models import Dashboard
from schemas.dashboard import DashboardCreate, DashboardUpdate
from repositories.base import BaseRepository

class DashboardRepository(BaseRepository[Dashboard, DashboardCreate, DashboardUpdate]):
    def get_by_name(self, db: Session, *, name: str, user_id: int) -> Optional[Dashboard]:
        return db.query(Dashboard).filter(
            and_(Dashboard.name == name, Dashboard.user_id == user_id)
        ).first()
    
    def get_multi_filtered(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        sort_field: str = "updated_at",
        sort_order: str = "desc",
        user_id: Optional[int] = None
    ) -> List[Dashboard]:
        query = db.query(Dashboard)
        
        if user_id:
            query = query.filter(Dashboard.user_id == user_id)
        
        if search:
            # Search in dashboard name and description within JSON data
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Dashboard.dashboard_data['name'].astext.ilike(search_term),
                    Dashboard.dashboard_data['description'].astext.ilike(search_term)
                )
            )
        
        # Apply sorting
        if sort_field == "name":
            sort_column = Dashboard.dashboard_data['name'].astext
        elif sort_field == "created_at":
            sort_column = Dashboard.created_at
        else:  # updated_at
            sort_column = Dashboard.updated_at
        
        if sort_order == "desc":
            sort_column = sort_column.desc()
        
        query = query.order_by(sort_column)
        
        return query.offset(skip).limit(limit).all()
    
    def count_filtered(
        self, 
        db: Session, 
        *, 
        search: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> int:
        query = db.query(func.count(Dashboard.id))
        
        if user_id:
            query = query.filter(Dashboard.user_id == user_id)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Dashboard.dashboard_data['name'].astext.ilike(search_term),
                    Dashboard.dashboard_data['description'].astext.ilike(search_term)
                )
            )
        
        return query.scalar() or 0
    
    def get_by_data_source(
        self, 
        db: Session, 
        *, 
        data_source_name: str,
        user_id: Optional[int] = None
    ) -> List[Dashboard]:
        """Find dashboards that use a specific data source"""
        query = db.query(Dashboard)
        
        if user_id:
            query = query.filter(Dashboard.user_id == user_id)
        
        dashboards = query.all()
        
        dependent_dashboards = []
        for dashboard in dashboards:
            dashboard_data = dashboard.dashboard_data or {}
            visualizations = dashboard_data.get("visualizations", [])
            
            for viz in visualizations:
                if viz.get("data_source") == data_source_name:
                    dependent_dashboards.append(dashboard)
                    break
        
        return dependent_dashboards

dashboard_repository = DashboardRepository(Dashboard)
