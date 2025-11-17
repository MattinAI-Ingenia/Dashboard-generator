import streamlit as st
import json
import time
from datetime import datetime
from utils.dashboard_api import DashboardApi

dash_api = DashboardApi()

def import_export_dashboards(user_id: int):
    """Import and export dashboards"""

    tab1, tab2 = st.tabs(["📤 Export", "📥 Import"])
        
    with tab1:
        st.subheader("📤 Export Dashboards")
        
        # Load saved dashboards if needed
        saved_dashboards = [d for d in st.session_state.dashboards.values() if d.get('is_saved')]
        
        if not saved_dashboards:
            if st.button("🔄 Load Dashboards from Database"):
                with st.spinner("Loading dashboards..."):
                    saved_dashboards = dash_api.list_saved_dashboards(user_id=user_id)
                    for dashboard in saved_dashboards:
                        st.session_state.dashboards[str(dashboard["id"])] = dashboard
                    st.rerun()
            st.info("Click 'Load Dashboards' to see available dashboards for export.")
        
        else:
            dashboard_options = {d['name']: d['id'] for d in saved_dashboards}
            selected_name = st.selectbox("Select dashboard to export", list(dashboard_options.keys()))
            
            if selected_name:
                selected_id = dashboard_options[selected_name]
                dashboard = st.session_state.dashboards[str(selected_id)]
                
                # Load full dashboard if visualizations are empty
                if not dashboard.get('visualizations'):
                    with st.spinner("Loading dashboard details..."):
                        full_dashboard = dash_api.load_dashboard_from_api(selected_id)
                        if full_dashboard:
                            st.session_state.dashboards[str(selected_id)] = full_dashboard
                            dashboard = full_dashboard
                
                # Get viz count
                viz_count = len(dashboard.get('visualizations', [])) or dashboard['metadata'].get('visualization_count', 0)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    format_type = st.selectbox("Export format", ["JSON"])
                
                with col2:
                    st.write("**Export Preview:**")
                    preview = {
                        "dashboard_name": dashboard['name'],
                        "visualizations_count": viz_count,
                        "created_at": dashboard['metadata']['created_at'].isoformat()
                    }
                    st.json(preview, expanded=False)
                
                if st.button("📤 Generate Export File", type="primary"):
                    export_data = dash_api.export_dashboard(selected_id)
                    
                    if export_data:
                        st.download_button(
                            "💾 Download Export File",
                            data=json.dumps(export_data, indent=2, default=str),
                            file_name=f"{dashboard['name']}_export.json",
                            mime="application/json"
                        )
                        st.success("✅ Export ready for download!")

    with tab2:
            st.subheader("📥 Import Dashboard")
            
            uploaded_file = st.file_uploader("Choose a dashboard JSON file", type=['json'])
            
            if uploaded_file is not None:
                try:
                    file_content = uploaded_file.read()
                    import_data = json.loads(file_content)
                    
                    # Validation
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("📋 Validation Results")
                        
                        is_valid = True
                        errors = []
                        warnings = []
                        
                        if "version" not in import_data:
                            errors.append("Missing version field")
                            is_valid = False
                        
                        if "dashboard" not in import_data:
                            errors.append("Missing dashboard data")
                            is_valid = False
                        else:
                            dashboard_data = import_data["dashboard"]
                            if "name" not in dashboard_data:
                                errors.append("Dashboard missing name")
                                is_valid = False
                            if "visualizations" not in dashboard_data:
                                errors.append("Dashboard missing visualizations")
                                is_valid = False
                        
                        if import_data.get("version") != "1.0":
                            warnings.append(f"Version {import_data.get('version')} may not be compatible")
                        
                        if is_valid:
                            st.success("✅ File is valid for import")
                        else:
                            st.error("❌ File validation failed")
                            for error in errors:
                                st.error(f"• {error}")
                        
                        if warnings:
                            for warning in warnings:
                                st.warning(f"⚠️ {warning}")
                    
                    with col2:
                        st.subheader("📄 Import Preview")
                        if "dashboard" in import_data:
                            preview = {
                                "name": import_data["dashboard"].get("name", "Unknown"),
                                "description": import_data["dashboard"].get("description", "No description"),
                                "visualizations": len(import_data["dashboard"].get("visualizations", [])),
                                "export_date": import_data.get("exported_at", "Unknown")
                            }
                            st.json(preview)
                    
                    if is_valid:
                        st.subheader("📥 Import Options")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            new_name = st.text_input("Dashboard name (optional)", 
                                                    value=import_data["dashboard"].get("name", ""))
                            validate_only = st.checkbox("Validate only (don't import)", value=False)
                        
                        if st.button("📥 Import Dashboard", type="primary", disabled=validate_only):
                            try:
                                result = dash_api.import_dashboard(
                                    import_data, 
                                    new_name if new_name else None
                                )
                                
                                if result:
                                    # Transform the imported dashboard to match frontend format
                                    imported_dashboard = {
                                        "id": result["id"],
                                        "name": result["dashboard_data"]["name"],
                                        "description": result["dashboard_data"].get("description", ""),
                                        "visualizations": result["dashboard_data"].get("visualizations", []),
                                        "layout": result["dashboard_data"].get("layout", {"type": "grid", "responsive": True}),
                                        "metadata": {
                                            "created_at": datetime.fromisoformat(result["created_at"].replace("Z", "+00:00")),
                                            "last_modified": datetime.fromisoformat(result["updated_at"].replace("Z", "+00:00")),
                                            "queries": [],
                                            "version": 1,
                                            "visualization_count": len(result["dashboard_data"].get("visualizations", []))
                                        },
                                        "is_saved": True
                                    }
                                    
                                    # Add to session state
                                    st.session_state.dashboards[str(imported_dashboard["id"])] = imported_dashboard
                                    
                                    st.success(f"✅ Dashboard '{imported_dashboard['name']}' imported successfully!")
                                    time.sleep(2)
                                    st.rerun()
                                    
                            except Exception as e:
                                st.error(f"❌ Import failed: {str(e)}")
                        
                        elif validate_only:
                            st.info("✅ Validation complete. File is ready for import.")
                
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON file. Please check the file format.")
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")