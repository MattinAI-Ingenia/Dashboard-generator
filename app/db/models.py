# app/db/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    login = Column(DateTime(timezone=True))
    
    # Relationships
    dashboards = relationship("Dashboard", back_populates="user", cascade="all, delete-orphan")
    data_sources = relationship("DataSource", back_populates="user", cascade="all, delete-orphan")

class Dashboard(Base):
    __tablename__ = 'dashboard'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    dashboard_data = Column(JSON) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="dashboards")

class DataSource(Base):
    __tablename__ = 'data_sources'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(String(100), nullable=False) 
    connection_info = Column(JSON) 
    status = Column(String(50), default='active') 

    schema_data = Column(JSON)
    schema_updated_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="data_sources")