import streamlit as st
import time 

from utils.dashboard_api import DashboardApi

dash_api = DashboardApi()

def manage_data_sources(user_id: int):
    """Manage data sources: list, add, test, delete"""

    # Tabs for different data source operations
    tab1, tab2, tab3 = st.tabs(["📋 My Sources", "➕ Add Source", "🧪 Test Sources"])
    
    with tab1:
        # Fetch data sources from API
        data_sources = dash_api.call_api(f"/data-sources/?user_id={user_id}")
        
        if data_sources:
            for ds in data_sources:
                with st.expander(f"📊 {ds['name']}", expanded=False):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**Type:** {ds['type']}")
                        st.write(f"**Status:** {ds['status']}")
                        if ds.get('description'):
                            st.write(f"**Description:** {ds['description']}")
                    
                    with col2:
                        if st.button("🔍 View Schema", key=f"schema_{ds['id']}"):
                            schema = dash_api.call_api(f"/data-sources/{ds['id']}/schema")
                            if schema and schema.get('tables'):
                                st.subheader("Database Schema")
                                for table in schema['tables']:
                                    st.write(f"**{table['name']}** ({table.get('row_count', 'Unknown')} rows)")
                                    cols_text = ", ".join([col['name'] for col in table['columns']])
                                    st.caption(f"Columns: {cols_text}")
                    
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{ds['id']}", type="secondary"):
                            if dash_api.call_api(f"/data-sources/{ds['id']}", method="DELETE") is not None:
                                st.success("Data source deleted!")
                                st.rerun()
        else:
            st.info("No data sources found. Add your first data source in the 'Add Source' tab.")
    
    with tab2:
        st.subheader("➕ Add New Data Source")
        
        with st.form("add_data_source"):
            # First row - basic info
            st.write("**Basic Information**")
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Name*", placeholder="My Database")
                description = st.text_area("Description", placeholder="Optional description...")
            
            with col2:
                db_type = st.selectbox("Database Type", ["postgresql", "mysql", "sqlite", "mongodb"])
                # Show default port based on database type
                default_ports = {
                    "postgresql": 5432,
                    "mysql": 3306,
                    "sqlite": 0,
                    "mongodb": 27017
                }
                port = st.number_input("Port", value=default_ports.get(db_type, 5432), min_value=0, max_value=65535)
            
            st.divider()
            
            # Second row - connection details
            st.write("**Connection Details**")
            col3, col4 = st.columns(2)
            
            with col3:
                host = st.text_input("Host", value="localhost")
                database = st.text_input("Database Name*", placeholder="mydb")
            
            with col4:
                username = st.text_input("Username", placeholder="user")
                password = st.text_input("Password", type="password", placeholder="password")
            
            st.divider()
            
            submitted = st.form_submit_button("🔗 Add Data Source", type="primary")
            
            if submitted and name and database:
                # Prepare data source config
                config = {
                    "name": name,
                    "description": description,
                    "type": db_type,
                    "connection": {
                        "host": host,
                        "port": port,
                        "database": database,
                        "username": username,
                        "password": password,
                        "schema": "public"
                    }
                }
                
                with st.spinner("Testing connection and adding data source..."):
                    result = dash_api.call_api(f"/data-sources/?user_id={user_id}", method="POST", data=config)

                if result:
                    st.success(f"Data source '{name}' added successfully!")
                    time.sleep(2)
                    st.rerun()
            elif submitted:
                st.error("Please fill in required fields (Name and Database)")
    
    with tab3:
        st.subheader("🧪 Test Connections")
        
        data_sources = dash_api.call_api(f"/data-sources/?user_id={user_id}")
        
        if data_sources:
            for ds in data_sources:
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{ds['name']}** ({ds['type']})")
                    st.caption(f"Status: {ds['status']}")
                
                with col2:
                    if st.button("🔍 Test", key=f"test_{ds['id']}"):
                        with st.spinner("Testing connection..."):
                            result = dash_api.call_api(f"/data-sources/{ds['id']}/test-connection", method="POST")
                            
                        if result:
                            if result.get('connection_successful'):
                                st.success("Connection successful!")
                            else:
                                st.error(f"Connection failed: {result.get('message', 'Unknown error')}")
                
                with col3:
                    status_color = "🟢" if ds['status'] == 'active' else "🔴"
                    st.write(f"{status_color} {ds['status'].title()}")
        else:
            st.info("No data sources to test.")