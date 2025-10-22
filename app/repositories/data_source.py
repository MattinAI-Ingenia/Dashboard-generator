# app/repositories/data_source.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from db.models import DataSource, Dashboard
from schemas.data_source import DataSourceCreate, DataSourceUpdate
from repositories.base import BaseRepository

class DataSourceRepository(BaseRepository[DataSource, DataSourceCreate, DataSourceUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[DataSource]:
        return db.query(DataSource).filter(DataSource.name == name).first()
    
    def get_multi_filtered(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        types: Optional[List[str]] = None
    ) -> List[DataSource]:
        query = db.query(DataSource)
        
        if status:
            query = query.filter(DataSource.status == status)
        
        if types:
            query = query.filter(DataSource.type.in_(types))
        
        return query.offset(skip).limit(limit).all()
    
    def update_status(
        self, 
        db: Session, 
        *, 
        data_source_id: int, 
        status: str
    ) -> DataSource:
        data_source = self.get(db, id=data_source_id)
        if data_source:
            data_source.status = status
            data_source.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(data_source)
        return data_source
    
    def update_schema(
        self, 
        db: Session, 
        *, 
        data_source_id: int, 
        schema_data: Dict[str, Any]
    ) -> DataSource:
        data_source = self.get(db, id=data_source_id)
        if data_source:
            data_source.schema_data = schema_data
            data_source.schema_updated_at = datetime.utcnow()
            data_source.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(data_source)
        return data_source
    
    def get_dependent_dashboards(
        self, 
        db: Session, 
        *, 
        data_source_id: int
    ) -> List[Dashboard]:
        """Find dashboards that use this data source"""
        data_source = self.get(db, id=data_source_id)
        if not data_source:
            return []
        
        # Search for dashboards that reference this data source in their JSON data
        dashboards = db.query(Dashboard).filter(
            Dashboard.user_id == data_source.user_id
        ).all()
        
        dependent_dashboards = []
        for dashboard in dashboards:
            dashboard_data = dashboard.dashboard_data or {}
            visualizations = dashboard_data.get("visualizations", [])
            
            for viz in visualizations:
                if viz.get("data_source") == data_source.name:
                    dependent_dashboards.append(dashboard)
                    break
        
        return dependent_dashboards

    def get_all(self, db: Session) -> List[DataSource]:
        return db.query(DataSource).all()

data_source_repository = DataSourceRepository(DataSource)