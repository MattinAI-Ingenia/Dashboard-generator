# app/api/routers/data_sources.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging
from typing import List, Optional, Dict, Any
import asyncio
import json
from datetime import datetime

from core.database import get_db
from repositories.data_source import data_source_repository
from schemas.data_source import (
    DataSourceCreate, 
    DataSourceUpdate, 
    DataSourceInDB, 
    DataSourceResponse,
    DataSourceSchema,
    DataSourceConfig
)
from services.data_source_connector import DataSourceConnector

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[DataSourceResponse])
def list_data_sources(
    status: Optional[str] = Query("active", enum=["all", "active", "inactive", "error"]),
    type: Optional[str] = Query(None, enum=["sql", "nosql"]),
    user_id: str = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    List available data sources for frontend dropdowns and selection.
    
    - **status**: Filter by connection status
    - **type**: Filter by data source type (sql/nosql)
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    """
    try:
        # Apply filters
        filters = {"user_id": user_id}
        if status != "all":
            filters["status"] = status
        if type:
            # Map type to actual database types
            type_mapping = {
                "sql": ["postgresql", "mysql", "sqlite", "bigquery"],
                "nosql": ["mongodb"]
            }
            filters["types"] = type_mapping.get(type, [])
        
        data_sources = data_source_repository.get_multi_filtered(
            db, 
            skip=skip, 
            limit=limit,
            **filters
        )
        
        return data_sources
    except Exception as e:
        logger.error(f"Error listing data sources: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving data sources: {str(e)}"
        )

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=DataSourceResponse)
async def add_data_source(
    data_source_config: DataSourceConfig,
    db: Session = Depends(get_db),
    user_id: int = Query(...)
):
    """
    Connect new data source to the system.
    
    Creates a new data source connection and tests connectivity.
    """
    try:
        print(data_source_config)
        # Test connection before creating
        connector = DataSourceConnector({
            "type": data_source_config.type.value,  
            "connection_info": data_source_config.connection.model_dump()
        })     

        logger.info(f"Testing connection for data source: {data_source_config.name}")
        connection_test = await connector.test_connection()
        
        if not connection_test.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Connection test failed",
                    "details": connection_test.get("error", "Unknown connection error")
                }
            )
        
        # Prepare data source creation data
        create_data = {
            "user_id": user_id,
            "name": data_source_config.name,
            "description": data_source_config.description,
            "type": data_source_config.type.value,
            "connection_info": data_source_config.connection.model_dump(),
            "status": "active"
        }
        print(f'Create data: {create_data}')

        # Create data source
        data_source = data_source_repository.create(
            db, 
            obj_in=DataSourceCreate(**create_data)
        )
        
        # Get initial schema information
        try:
            schema_info = await connector.get_schema()
            print(schema_info)
            if schema_info:
                # Update with schema information
                data_source = data_source_repository.update_schema(
                    db,
                    data_source_id=data_source.id,
                    schema_data=schema_info
                )
        except Exception as schema_error:
            logger.warning(f"Could not fetch schema for new data source: {schema_error}")
        
        logger.info(f"Data source created successfully: {data_source.name} (ID: {data_source.id})")
        
        return data_source
    
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data source with this name already exists"
        )
    except Exception as e:
        logger.error(f"Error creating data source: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating data source: {str(e)}"
        )

@router.get("/{data_source_id}", response_model=DataSourceResponse)
def get_data_source(
    data_source_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific data source.
    """
    data_source = data_source_repository.get(db, id=data_source_id)
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data source with ID {data_source_id} not found"
        )
    
    return data_source

@router.delete("/{data_source_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_data_source(
    data_source_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove a data source from the system.
    
    This will also remove any dashboards that depend on this data source.
    """
    data_source = data_source_repository.get(db, id=data_source_id)
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data source with ID {data_source_id} not found"
        )
    
    try:
        # Check for dependent dashboards
        dependent_dashboards = data_source_repository.get_dependent_dashboards(
            db, 
            data_source_id=data_source_id
        )
        
        if dependent_dashboards:
            dashboard_names = [d.dashboard_data.get("name", f"Dashboard {d.id}") for d in dependent_dashboards]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Cannot delete data source with dependent dashboards",
                    "dependent_dashboards": dashboard_names,
                    "suggestion": "Delete or modify dependent dashboards first"
                }
            )
        
        # Remove the data source
        data_source_repository.remove(db, id=data_source_id)
        logger.info(f"Data source removed: {data_source.name} (ID: {data_source_id})")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing data source: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing data source: {str(e)}"
        )

@router.get("/{data_source_id}/schema", response_model=DataSourceSchema)
async def get_data_source_schema(
    data_source_id: int,
    refresh: bool = Query(False, description="Refresh schema cache"),
    db: Session = Depends(get_db)
):
    """
    Get schema information (tables, columns) for the data source.
    
    - **refresh**: If true, fetches fresh schema from the data source
    """
    data_source = data_source_repository.get(db, id=data_source_id)
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data source with ID {data_source_id} not found"
        )
    
    try:
        # Check if we need to refresh or if cached schema is recent enough
        should_refresh = (
            refresh or 
            not hasattr(data_source, 'schema_data') or 
            not data_source.schema_data or
            data_source.schema_updated_at is None
        )
        
        if should_refresh:
            logger.info(f"Refreshing schema for data source: {data_source.name}")
            
            # Create connector and fetch fresh schema
            connection_info = data_source.connection_info
            if isinstance(connection_info, str):
                import json
                connection_info = json.loads(connection_info)

            connector = DataSourceConnector({
                "type": data_source.type,
                "connection_info": connection_info
            })
            
            schema_info = await connector.get_schema()
            
            if schema_info:
                # Update the data source with fresh schema
                data_source = data_source_repository.update_schema(
                    db,
                    data_source_id=data_source_id,
                    schema_data=schema_info
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Could not fetch schema information"
                )
        
        # Return schema information
        schema_data = data_source.schema_data or {}
        
        return DataSourceSchema(
            last_updated=data_source.schema_updated_at,
            tables=schema_data.get("tables", [])
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting schema for data source {data_source_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving schema: {str(e)}"
        )

@router.post("/{data_source_id}/test-connection")
async def test_data_source_connection(
    data_source_id: int,
    db: Session = Depends(get_db)
):
    """
    Test connection to a specific data source and update its status.
    """
    data_source = data_source_repository.get(db, id=data_source_id)
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data source with ID {data_source_id} not found"
        )
    
    try:
        # Create connector and test connection
        connection_info = data_source.connection_info
        if isinstance(connection_info, str):
            import json
            connection_info = json.loads(connection_info)

        connector = DataSourceConnector({
            "type": data_source.type,
            "connection_info": connection_info
        })
        
        logger.info(f"Testing connection for data source: {data_source.name}")
        connection_result = await connector.test_connection()
        
        # Update status based on test result
        new_status = "active" if connection_result.get("success", False) else "error"
        
        data_source = data_source_repository.update_status(
            db,
            data_source_id=data_source_id,
            status=new_status
        )
        
        return {
            "data_source_id": data_source_id,
            "connection_successful": connection_result.get("success", False),
            "status": new_status,
            "message": connection_result.get("message", "Connection test completed"),
            "details": connection_result.get("details", {}),
            "tested_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error testing connection for data source {data_source_id}: {str(e)}")
        
        # Update status to error
        data_source_repository.update_status(
            db,
            data_source_id=data_source_id,
            status="error"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connection test failed: {str(e)}"
        )
    