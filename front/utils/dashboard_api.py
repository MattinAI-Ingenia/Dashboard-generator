import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import requests
import json


class DashboardApi:

    def __init__(self):
        self.API_BASE_URL = "http://localhost:8000/api/v1"  

    # API Helper functions
    def call_api(self, endpoint: str, method: str = "GET", data: dict = None):
        """Make API calls to the backend"""
        url = f"{self.API_BASE_URL}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json=data)
            elif method == "DELETE":
                response = requests.delete(url)
            
            if response.status_code < 400:
                return response.json() if response.content else {}
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            st.error(f"Connection Error: {str(e)}")
            return None

    # CHAT
    def chat_with_agent(self, query: str, conversation_id: str = None, user_id: int = None, dashboard_context: Dict = None) -> Dict[str, Any]:
        """Send chat query to backend API and get response"""
        request_payload = {
            "query": query,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "context": dashboard_context
        }
        try:
            result = self.call_api("/chat/", method="POST", data=request_payload)
            return result if result else {}
        except Exception as e:
            st.error(f"Failed to chat with agent: {str(e)}")
            return {}

    def reset_chat_session(self, agent_id: int, app_id: int, conversation_id: str = None) -> Dict[str, Any]:
        """Reset chat session via backend API"""
        request_payload = {
            "agent_id": agent_id,
            "app_id": app_id,
            "conversation_id": conversation_id
        }
        try:
            result = self.call_api("/chat/reset", method="POST", data=request_payload)
            return result if result else {}
        except Exception as e:
            st.error(f"Failed to reset chat session: {str(e)}")
            return {}

    # DASHBOARD
    def save_dashboard_to_api(self, dashboard: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Save dashboard to backend API"""
        # Convert datetime objects to ISO strings in metadata
        metadata = dashboard.get("metadata", {})
        
        if "created_at" in metadata and hasattr(metadata["created_at"], "isoformat"):
            metadata["created_at"] = metadata["created_at"].isoformat()
        if "last_modified" in metadata and hasattr(metadata["last_modified"], "isoformat"):
            metadata["last_modified"] = metadata["last_modified"].isoformat()
        
        # Convert visualizations to API format
        api_visualizations = []
        for viz in dashboard.get("visualizations", []):
            result = viz.get("result")

            # Detect MongoDB vs SQL
            if "mongodb_query" in result:
                query = {
                    "type": "mongodb",
                    "statement": result["mongodb_query"]
                }
            else:
                query = {
                    "type": "sql",
                    "statement": result.get("sql", "")
                }
            api_viz = {
                "id": viz["id"],
                "title": viz["result"]["title"],
                "description": viz["result"].get("description", ""),
                "chart_type": viz["result"].get("chart_type", "table"),
                "data_source": viz["result"].get("data_source", ""),
                "query": query,
                "original_query": viz["result"].get("original_user_query", ""),
                "query_config": viz["result"].get("query_config", {}),
                "config": viz["result"].get("config", {}),
                "edit_history": viz["result"].get("edit_history", []),
                "created_at": datetime.now().isoformat() + "Z"
            }
            api_visualizations.append(api_viz)
        
        # Format according to your API specification
        dashboard_data = {
            "user_id": user_id,
            "name": dashboard["name"],
            "description": dashboard.get("description", ""),
            "visualizations": api_visualizations
        }

        # If dashboard has an ID, it's an update
        if dashboard.get("id") and dashboard.get("is_saved"):
            dashboard_data["id"] = dashboard["id"]
        
        try:
            result = self.call_api("/dashboards/save", method="POST", data=dashboard_data)
            if result:
                # Update the dashboard with the returned data
                dashboard["id"] = result.get("id")
                dashboard["is_saved"] = True
                dashboard["metadata"]["last_modified"] = datetime.now()
                
                # Store in session state
                st.session_state.dashboards[str(dashboard["id"])] = dashboard
                
                return result
            return None
        except Exception as e:
            st.error(f"Failed to save dashboard: {str(e)}")
            return None
        
    def load_dashboard_from_api(self, dashboard_id: int) -> Dict[str, Any]:
        """Load dashboard from backend API"""
        try:
            result = self.call_api(f"/dashboards/{dashboard_id}")
            if result:
                # Transform API visualizations to frontend format
                visualizations = []
                for viz in result["dashboard_data"].get("visualizations", []):
                    query_type = viz["query"]["type"]

                    if query_type == "mongodb":
                        # Build result based on query type
                        result_data = {
                            "mongodb_query": viz["query"]["statement"],
                            "title": viz["title"],
                            "description": viz.get("description", ""),
                            "chart_type": viz.get("chart_type", "table"),
                            "data_source": viz.get("data_source", ""),
                            "original_user_query": viz.get("original_query", ""),
                            "query_config": viz.get("query_config", {}),
                            "config": viz.get("config", {}),
                            "edit_history": viz.get("edit_history", [])
                        }
                    else:
                        result_data = {
                            "sql": viz["query"]["statement"],
                            "title": viz["title"],
                            "description": viz.get("description", ""),
                            "chart_type": viz.get("chart_type", "table"),
                            "data_source": viz.get("data_source", ""),
                            "original_user_query": viz.get("original_query", ""),
                            "query_config": viz.get("query_config", {}),
                            "config": viz.get("config", {}),
                            "edit_history": viz.get("edit_history", [])

                        }

                    visualizations.append({
                        "id": viz["id"],
                        "result": result_data
                        })
                
                dashboard = {
                    "id": result["id"],
                    "name": result["dashboard_data"]["name"],
                    "description": result["dashboard_data"].get("description", ""),
                    "visualizations": visualizations,  # Use transformed visualizations
                    "layout": result["dashboard_data"].get("layout", {"type": "grid", "responsive": True}),
                    "metadata": {
                        "created_at": datetime.fromisoformat(result["created_at"].replace("Z", "+00:00")),
                        "last_modified": datetime.fromisoformat(result["updated_at"].replace("Z", "+00:00")),
                        "queries": result["dashboard_data"].get("metadata", {}).get("queries", []),
                        "version": result["dashboard_data"].get("metadata", {}).get("version", 1)
                    },
                    "is_saved": True
                }
                return dashboard
            return None
        except Exception as e:
            st.error(f"Failed to load dashboard: {str(e)}")
            return None

    def list_saved_dashboards(self, user_id: int) -> List[Dict[str, Any]]:
        """Get list of saved dashboards from API"""
        try:
            result = self.call_api(F"/dashboards/?user_id={user_id}")
            print()
            print(f"Resultado de call_api, {result}")
            print()
            if result and result.get("dashboards"):
                dashboards = []
                for dash_data in result["dashboards"]:
                    dashboard = {
                        "id": dash_data["id"],
                        "name": dash_data["name"],
                        "description": dash_data.get("description", ""),
                        "visualizations": [],  # List endpoint doesn't include full visualization data
                        "layout": {"type": "grid", "responsive": True},
                        "metadata": {
                            "created_at": datetime.fromisoformat(dash_data["created_at"].replace("Z", "+00:00")),
                            "last_modified": datetime.fromisoformat(dash_data["updated_at"].replace("Z", "+00:00")),
                            "queries": [],
                            "version": 1,
                            "visualization_count": dash_data.get("visualization_count", 0)
                        },
                        "is_saved": True
                    }
                    dashboards.append(dashboard)
                return dashboards
            return []
        except Exception as e:
            st.error(f"Failed to load dashboards: {str(e)}")
            return []

    def delete_dashboard_from_api(self, dashboard_id: int) -> bool:
        """Delete dashboard from backend API"""
        try:
            result = self.call_api(f"/dashboards/{dashboard_id}", method="DELETE")
            return result is not None
        except Exception as e:
            st.error(f"Failed to delete dashboard: {str(e)}")
            return False

    def export_dashboard(self, dashboard_id: int) -> Dict[str, Any]:
        """Export dashboard as JSON"""
        try:
            result = self.call_api(
                f"/dashboards/{dashboard_id}/export?include_data=false", 
                method="POST"
            )
            return result
        except Exception as e:
            st.error(f"Failed to export dashboard: {str(e)}")
            return None

    def import_dashboard(self, import_data: Dict[str, Any], new_name: str = None) -> Dict[str, Any]:
        """Import dashboard from JSON"""
        request_payload = import_data  # Don't wrap it, send the whole import_data
        
        # Add query parameters for new_name and preserve_ids
        params = []
        if new_name:
            params.append(f"new_name={new_name}")
        
        query_string = "?" + "&".join(params) if params else ""
        
        try:
            result = self.call_api(f"/dashboards/import{query_string}", method="POST", data=request_payload)
            return result
        except Exception as e:
            st.error(f"Failed to import dashboard: {str(e)}")
            return None

    # QUERY
    def execute_query(self, data_source: str, query: str, type: str) -> Dict[str, Any]:
        """Execute query via backend API"""
        request_payload = {
            "data_source": data_source,
            "query": {
                "type": type,
                "statement": query
            }
        }
        try:
            print()
            print(f"Executing query with payload: {request_payload}")
            print()
            result = self.call_api("/queries/execute", method="POST", data=request_payload)
            return result
        except Exception as e:
            st.error(f"Failed to execute query: {str(e)}")
            return {}

    def generate_sql_from_nlp(self, nlp_query: str) -> Dict[str, Any]:
        """Generate SQL from natural language query via backend API"""
        request_payload = {
            "query": nlp_query
        }
        try:
            result = self.call_api("/nlp/query", method="POST", data=request_payload)
            print()
            print(f"Query generation result: {result}")
            print()
            return result
        except Exception as e:
            st.error(f"Failed to generate SQL from NLP: {str(e)}")
            return {}

    def generate_query_add_visualization(self, nlp_query: str) -> Dict[str, Any]:
        """Generate SQL/MongoDB query from natural language and add visualization via backend API"""
        request_payload = {
            "query": nlp_query
        }
        try:
            result = self.call_api("/nlp/query_add_visualization", method="POST", data=request_payload)
            print()
            print(f"Query add visualization result: {result}")
            print()
            return result
        except Exception as e:
            st.error(f"Failed to generate query for visualization: {str(e)}")
            return {}

    def edit_visualization(self, original_viz: Dict[str, Any], edit_instructions: str) -> Dict[str, Any]:
        """Edit visualization via backend"""
        payload = {
            "original_visualization": original_viz["result"],
            "edit_instructions": edit_instructions
        }
        try:
            return self.call_api("/nlp/query/edit", method="POST", data=payload)
        except Exception as e:
            st.error(f"Edit failed: {str(e)}")
            return {}
    
    # USER
    def get_user_info(self) -> Dict[str, Any]:
        """Get current user info from backend API"""
        try:
            result = self.call_api("/users/me")
            return result if result else {}
        except Exception as e:
            st.error(f"Failed to get user info: {str(e)}")
            return {}
    
    def login(self, email, password):
        """Login user via backend API"""
        request_payload = {
            "email": email,
            "password": password
        }
        try:
            result = self.call_api("/auth/login", method="POST", data=request_payload)
            return result if result else {}
        except Exception as e:
            st.error(f"Failed to login: {str(e)}")
            return {}
        
    def signup(self, name, email, password):
        """Signup user via backend API"""
        request_payload = {
            "name": name,
            "email": email,
            "password": password
        }
        try:
            result = self.call_api("/auth/signup", method="POST", data=request_payload)
            return result if result else {}
        except Exception as e:
            st.error(f"Failed to signup: {str(e)}")
            return {}
    
    # DATA SOURCES
    def get_data_sources_with_schemas(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all data sources with their schemas for chat context"""
        try:
            # Get all active data sources
            data_sources = self.call_api(f"/data-sources/?user_id={user_id}&status=active")
            
            if not data_sources:
                return []
            
            # For each data source, fetch its schema
            data_sources_with_schemas = []
            for ds in data_sources:
                try:
                    schema = self.call_api(f"/data-sources/{ds['id']}/schema?refresh=false")
                    data_sources_with_schemas.append({
                        "id": ds['id'],
                        "name": ds['name'],
                        "type": ds['type'],
                        "description": ds.get('description', ''),
                        "schema": schema
                    })
                except Exception as e:
                    # If schema fetch fails, include source without schema
                    data_sources_with_schemas.append({
                        "id": ds['id'],
                        "name": ds['name'],
                        "type": ds['type'],
                        "description": ds.get('description', ''),
                        "schema": None
                    })
            
            return data_sources_with_schemas
        except Exception as e:
            st.error(f"Failed to fetch data sources: {str(e)}")
            return []