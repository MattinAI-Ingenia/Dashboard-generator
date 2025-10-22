# app/repositories/datasource.py
from typing import List, Optional
from sqlalchemy.orm import Session
from models.datasource import Datasource

class DatasourceRepository:
    """Repository for datasource operations"""
    
    def get(self, db: Session, id: int) -> Optional[Datasource]:
        """Get datasource by ID"""
        return db.query(Datasource).filter(Datasource.id == id).first()
    
    def get_all(self, db: Session) -> List[Datasource]:
        """Get all datasources"""
        return db.query(Datasource).all()
    
    def get_with_schema(self, db: Session, id: int) -> Optional[Datasource]:
        """Get datasource with full schema information"""
        # In production, this could fetch and parse schema metadata
        return self.get(db, id)
    
    def create(self, db: Session, datasource_data: dict) -> Datasource:
        """Create new datasource"""
        datasource = Datasource(**datasource_data)
        db.add(datasource)
        db.commit()
        db.refresh(datasource)
        return datasource

datasource_repository = DatasourceRepository()