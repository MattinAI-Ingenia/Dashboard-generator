# app/api/routers/dashboards.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from core.database import get_db
from repositories.dashboard import dashboard_repository
from schemas.dashboard import (
    DashboardCreate,
    DashboardUpdate, 
    DashboardInDB,
    DashboardResponse,
    DashboardData,
    DashboardList,
    DashboardListItem
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=DashboardList)
def list_dashboards(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort: str = Query("updated_at", enum=["name", "created_at", "updated_at"]),
    order: str = Query("desc", enum=["asc", "desc"]),
    user_id: str = Query(...),
    db: Session = Depends(get_db)
):
    try:
        skip = (page - 1) * limit
        
        filters = {"user_id": user_id}
        if search:
            filters["search"] = search
        
        dashboard_objects = dashboard_repository.get_multi_filtered(
            db,
            skip=skip,
            limit=limit,
            sort_field=sort,
            sort_order=order,
            **filters
        )
        print(f"Dashboard objects: {dashboard_objects}")
        # Convert Dashboard objects to DashboardListItem
        dashboards = []
        for db_dashboard in dashboard_objects:
            dashboard_data = db_dashboard.dashboard_data
            visualization_count = len(dashboard_data.get('visualizations', []))
            print(f"visualization_count: {visualization_count}")
            item = DashboardListItem(
                id=db_dashboard.id,
                name=dashboard_data.get('name', 'Untitled Dashboard'),
                description=dashboard_data.get('description'),
                created_at=db_dashboard.created_at,
                updated_at=db_dashboard.updated_at,
                visualization_count=visualization_count
            )
            print(f"Dashboard item: {item}")
            dashboards.append(item)
        
        total = dashboard_repository.count_filtered(db, **filters)
        print(dashboards)
        return DashboardList(
            dashboards=dashboards,
            total=total,
            page=page,
            limit=limit,
            total_pages=(total + limit - 1) // limit
        )
        
    except Exception as e:
        logger.error(f"Error listing dashboards: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving dashboards: {str(e)}"
        )

@router.post("/save", status_code=status.HTTP_201_CREATED, response_model=DashboardResponse)
def save_dashboard(
    dashboard_data: DashboardData,
    db: Session = Depends(get_db)
):
    """
    Save dashboard to database.
    
    Creates new dashboard or updates existing one based on presence of ID.
    """
    try:
        # Check if this is an update (has ID) or create (no ID)
        if hasattr(dashboard_data, 'id') and dashboard_data.id:
            # Update existing dashboard
            existing_dashboard = dashboard_repository.get(db, id=dashboard_data.id)
            if not existing_dashboard:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Dashboard with ID {dashboard_data.id} not found"
                )
            
            update_data = {
                "dashboard_data": dashboard_data.model_dump(),
                "updated_at": datetime.now()
            }
            
            dashboard = dashboard_repository.update(
                db,
                db_obj=existing_dashboard,
                obj_in=DashboardUpdate(**update_data)
            )
            
            logger.info(f"Dashboard updated: {dashboard_data.name} (ID: {dashboard.id})")
            
        else:
            # Create new dashboard
            create_data = {
                "user_id": 1,  # Placeholder
                "dashboard_data": dashboard_data.model_dump(),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            dashboard = dashboard_repository.create(
                db,
                obj_in=DashboardCreate(**create_data)
            )
            
            logger.info(f"Dashboard created: {dashboard_data.name} (ID: {dashboard.id})")
        
        return dashboard
        
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dashboard with this name already exists"
        )
    except Exception as e:
        logger.error(f"Error saving dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving dashboard: {str(e)}"
        )

@router.get("/{dashboard_id}", response_model=DashboardResponse)
def get_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db)
):
    """
    Load complete dashboard with all visualizations.
    """
    dashboard = dashboard_repository.get(db, id=dashboard_id)
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dashboard with ID {dashboard_id} not found"
        )
    
    return dashboard

@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db)
):
    """
    Permanently delete dashboard.
    """
    dashboard = dashboard_repository.get(db, id=dashboard_id)
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dashboard with ID {dashboard_id} not found"
        )
    
    try:
        dashboard_repository.remove(db, id=dashboard_id)
        logger.info(f"Dashboard deleted: ID {dashboard_id}")
        
    except Exception as e:
        logger.error(f"Error deleting dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting dashboard: {str(e)}"
        )
    
@router.post("/{dashboard_id}/export", response_model=Dict[str, Any])
def export_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db)
):
    """Export dashboard as JSON."""
    dashboard = dashboard_repository.get(db, id=dashboard_id)
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dashboard with ID {dashboard_id} not found"
        )
    
    export_data = {
        "version": "1.0",
        "dashboard": dashboard.dashboard_data,
        "exported_at": datetime.now().isoformat(),
        "metadata": {
            "export_format": "JSON"
        }
    }
    
    return export_data

@router.post("/import", status_code=status.HTTP_201_CREATED, response_model=DashboardResponse)
def import_dashboard(
    import_data: Dict[str, Any],
    new_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Import dashboard from JSON."""
    try:
        # Validate structure
        if "version" not in import_data or "dashboard" not in import_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid import file structure"
            )
        
        dashboard_data = import_data["dashboard"]
        
        # Validate required fields
        if "name" not in dashboard_data or "visualizations" not in dashboard_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dashboard missing required fields"
            )
        
        # Clean up - remove fields that don't belong in dashboard_data
        if "id" in dashboard_data:
            del dashboard_data["id"]
        
        if new_name:
            dashboard_data["name"] = new_name
        
        # Create dashboard
        create_data = {
            "user_id": 1,  # Update with actual user
            "dashboard_data": dashboard_data,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        dashboard = dashboard_repository.create(
            db,
            obj_in=DashboardCreate(**create_data)
        )
        
        logger.info(f"Dashboard imported: {dashboard_data['name']} (ID: {dashboard.id})")
        return dashboard
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing dashboard: {str(e)}"
        )
    