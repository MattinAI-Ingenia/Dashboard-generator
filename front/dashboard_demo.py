import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid
import json
import time
from typing import Dict, List, Any
import plotly.express as px
import re
from streamlit_float import float_init, float_parent

from utils.dashboard_api import DashboardApi
from utils.style import load_style
from components.data_sources import manage_data_sources
from components.import_export import import_export_dashboards  

dash_api = DashboardApi()

# CSS
load_style()

# Initialize float layout
float_init()

# ===== AUTHENTICATION =====
def login_page():
    """Display login form"""
    st.markdown(
        """
        <h3 style='text-align: center;'>🎨 Dashboard AI Studio</h3>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            email = st.text_input("📧 Email", placeholder="your@email.com")
            password = st.text_input("🔒 Password", type="password")
            
            col_a, col_b = st.columns(2)
            with col_a:
                login = st.form_submit_button("🚀 Login", type="primary", use_container_width=True)
            with col_b:
                signup = st.form_submit_button("✨ Sign Up", use_container_width=True)
            
            if login:
                user = dash_api.login(email, password)
                if user:
                    print(f'Created user:{user}')
                    st.session_state.authenticated = True
                    st.session_state.user_id = user.get("id")
                    st.session_state.user_email = user.get("email")
                    st.session_state.user_name = user.get("name")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
            
            if signup:
                st.session_state.show_signup = True
                st.rerun()

def signup_page():
    """Display signup form"""
    st.markdown(
        """
        <h3 style='text-align: center;'>Create Account</h3>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("signup_form"):
            name = st.text_input("👤 Full Name")
            email = st.text_input("📧 Email")
            password = st.text_input("🔒 Password", type="password")
            password2 = st.text_input("🔒 Confirm Password", type="password")
            
            col_a, col_b = st.columns(2)
            with col_a:
                signup = st.form_submit_button("✨ Sign Up", type="primary", use_container_width=True)
            with col_b:
                back = st.form_submit_button("← Back to Login", use_container_width=True)
            
            if signup:
                if password != password2:
                    st.error("Passwords don't match")
                elif len(password) < 6:
                    st.error("Password too short (min 6 chars)")
                else:
                    # Insert into database
                    try:
                        dash_api.signup(name, email, password)
                        time.sleep(2)
                        st.session_state.show_signup = False
                        st.rerun()
                    except:
                        st.error("Email already exists or DB error")
            
            if back:
                st.session_state.show_signup = False
                st.rerun()

# ===== MAIN APP =====
# Initialize auth state FIRST
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False

if not st.session_state.authenticated:
    if st.session_state.show_signup:
        signup_page()
    else:
        login_page()
    st.stop()

# Configure page
st.set_page_config(
    page_title="Dashboard AI Studio",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def init_session_state():
    if 'dashboards' not in st.session_state:
        st.session_state.dashboards = {}
        if st.session_state.get('user_id'):
            # Load saved dashboards from API on initialization
            saved_dashboards = dash_api.list_saved_dashboards(user_id=st.session_state.user_id)
            for dashboard in saved_dashboards:
                st.session_state.dashboards[str(dashboard["id"])] = dashboard
    if 'current_dashboard' not in st.session_state:
        st.session_state.current_dashboard = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "generate"
    if 'editing_viz_id' not in st.session_state:
        st.session_state.editing_viz_id = None
    if 'edit_query' not in st.session_state:
        st.session_state.edit_query = ""
    if 'show_chat' not in st.session_state:
        st.session_state.show_chat = False
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = None

init_session_state()

# Dashboard generator
class DashboardGenerator:
    def __init__(self):
        pass
    
    def create_dashboard(self, name: str, description: str = "") -> Dict[str, Any]:
        dashboard_id = str(uuid.uuid4())
        
        return {
            'id': dashboard_id,
            'name': name,
            'description': description,
            'visualizations': [],
            'metadata': {
                'created_at': datetime.now(),
                'last_modified': datetime.now()
            },
            'is_saved': False
        }

# Initialize generator
@st.cache_resource
def get_dashboard_generator():
    return DashboardGenerator()

generator = get_dashboard_generator()

# Utility functions
def render_visualization(viz: Dict[str, Any], show_controls: bool = False):
    """Render a visualization with optional controls"""
    container_class = ""
    st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)
    
    # Handle error visualizations
    if viz.get('type') == 'error':
        col1, col2 = st.columns([4, 1])
        with col1:
            st.error(f"❌ {viz['result']['title']}")
        with col2:
            if show_controls:
                if st.button("🗑️", key=f"remove_{viz['id']}", help="Remove"):
                    st.markdown('</div>', unsafe_allow_html=True)
                    return "remove"    
                    
        # if show_controls:
            # with st.expander("📝 Failed Query", expanded=False):
            #     # st.code(viz['result']['sql'], language='sql')
        st.markdown('</div>', unsafe_allow_html=True)
        return None
    
    # Check if data is available
    if viz.get('data') is None or viz['data'].empty:
        st.warning("⚠️ No data available for this visualization")
        st.markdown('</div>', unsafe_allow_html=True)
        return None
    
    # Render normal visualization
    result = _render_viz_content(viz, show_controls)
    st.markdown('</div>', unsafe_allow_html=True)
    return result

def _render_viz_content(viz: Dict[str, Any], show_controls: bool = False):
    """Render visualization content"""
    # Compact header
    col1, col2 = st.columns([4, 1])

    with col1:
        st.markdown(f'<p style="color: #FFFFFF; font-weight: bold; margin-bottom: 0.5rem;">📊 {viz["result"]["title"]}</p>', unsafe_allow_html=True)
        if show_controls:
            st.caption(viz.get('description', ''))
    
    with col2:
        if show_controls:
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🗑️", key=f"remove_{viz['id']}", help="Remove"):
                    return "remove"
            with col_b:
                if st.button("✏️", key=f"edit_{viz['id']}", help="Edit"):
                    st.session_state.editing_viz_id = viz['id']
                    st.session_state.edit_query = viz.get('user_query', '')
                    return "edit"
    
    df = viz['data']
    # Query
    x_col = viz['x_column']
    y_col = viz['y_column']
    
    # Visualization
    x_col_viz = viz['x_column_query']
    y_col_viz = viz['y_column_query']

    # After getting x_col_viz and y_col_viz, add this:
    if ',' in str(x_col_viz):
        # Combine multiple x columns into one
        x_cols = [col.strip() for col in x_col_viz.split(',')]
        df['combined_route'] = df[x_cols].apply(lambda row: ' → '.join(row.values.astype(str)), axis=1)
        x_col_viz = 'combined_route'

    # Create compact visualization
    if viz['type'] == 'barchart':
        fig = px.bar(df, x=x_col_viz, y=y_col_viz)
        fig.update_traces(
            marker_color='rgba(37, 99, 235, 0.8)',
            marker_line_color='rgba(37, 99, 235, 1)',
            marker_line_width=1
        )

    elif viz['type'] == 'piechart':
        fig = px.pie(df, names=x_col_viz, values=y_col_viz)
        fig.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            textfont_size=12,
            textfont_color='white',
            marker_line_color='white',
            marker_line_width=2
        )

    elif viz['type'] == 'timeseries':
        # Check if y_col contains multiple columns (comma-separated string)
        if ',' in str(y_col_viz):
            # Multiple series - melt the dataframe
            y_cols = [col.strip() for col in y_col_viz.split(',')]
            df_melted = df.melt(id_vars=[x_col_viz], value_vars=y_cols, 
                            var_name='series', value_name='value')
            fig = px.line(df_melted, x=x_col_viz, y='value', color='series')
        elif len(df.columns) > 2:
            # Multiple columns in dataframe
            y_cols = [col for col in df.columns if col != x_col]
            df_melted = df.melt(id_vars=[x_col], value_vars=y_cols,
                            var_name='series', value_name='value')
            fig = px.line(df_melted, x=x_col_viz, y='value', color='series')
        else:
            # Single line
            fig = px.line(df, x=x_col_viz, y=y_col_viz)
        
        fig.update_traces(line_width=3, marker=dict(size=6))

    else:
        fig = px.bar(df, x=x_col, y=y_col)
    
    # Compact styling
    fig.update_layout(
        height=280,
        font_family="Inter, sans-serif",
        font_size=11,
        font_color="#000000",  # Dark gray text
        showlegend=False,
        title=None,
        plot_bgcolor='#f8fafc',  # Light background
        paper_bgcolor='white',
        margin=dict(t=15, l=40, r=20, b=40),
        xaxis=dict(
            title=dict(
                text=x_col.replace('_', ' ').title(),
                font=dict(size=11, color="#000000")  # Black axis title
            ),
            tickfont=dict(size=10, color="#000000"),    # Black tick labels
            linecolor="#000000",  # Black axis line
            tickcolor="#000000",  # Black tick marks
            gridcolor="#e5e7eb"
        ),
        yaxis=dict(
            title=dict(
                text=y_col.replace('_', ' ').title(),
                font=dict(size=11, color="#000000")  # Black axis title
            ),
            tickfont=dict(size=10, color="#000000"),    # Black tick labels
            linecolor="#000000",  # Black axis line
            tickcolor="#000000",  # Black tick marks
            gridcolor="#e5e7eb"
        )
    )

    st.plotly_chart(fig, use_container_width=True, key=f"chart_{viz['id']}")
    
    # Compact SQL view (only when controls shown)
    if show_controls:
        
        # Add custom CSS just for this visualization's SQL expander
        st.markdown(f"""
        <style>
        div[data-testid="stExpander"][data-viz-id="{viz['id']}"] summary {{
            color: #000000 !important;
        }}
        div[data-testid="stExpander"][data-viz-id="{viz['id']}"] p {{
            color: #000000 !important;
        }}
        </style>
        """, unsafe_allow_html=True)
        
        # Use st.code for proper SQL syntax highlighting with black text
        with st.expander("👤Original User Query", expanded=False):
            user_query = viz["result"]["original_user_query"]

            st.markdown(
                f'''
                <div style="
                    background: #1e1e2f;
                    padding: 10px;
                    border-radius: 8px;
                    overflow-x: auto;
                    font-family: monospace;
                    color: #e0e0e0;
                ">
                    {user_query}
                </div>
                ''',
                unsafe_allow_html=True
            )

        with st.expander("📝 Edit History", expanded=False):
            edit_history = viz.get('result', {}).get('edit_history', [])
            if edit_history:
                for i, edit in enumerate(edit_history):
                    st.markdown(f"**Edit {i+1}**")
                    st.caption(edit['instruction'])
            else:
                st.caption("No edits yet")

        with st.expander("📝 Last Generated Query", expanded=False):
            # Get the SQL string (from list if needed)
            sql_string = viz["generated_sql"]
            if isinstance(sql_string, list):
                sql_string = sql_string[0]

            try:
                # Try parsing as MongoDB JSON
                mongo_query = json.loads(sql_string)
                
                # Pretty format with syntax highlighting
                collection = mongo_query.get("collection", "")
                operation = mongo_query.get("operation", "")
                pipeline = mongo_query.get("pipeline", [])
                
                formatted = f'<span style="color:#9333ea;">db</span>.<span style="color:#2563eb;">{collection}</span>.<span style="color:#16a34a;">{operation}</span>(\n'
                formatted += json.dumps(pipeline, indent=2).replace('"', '<span style="color:#f59e0b;">"</span>')
                formatted += '\n)'
                
                st.markdown(
                    f'''
                    <div style="background:#1e1e2f;padding:15px;border-radius:8px;border:1px solid #3f3f5f;overflow-x:auto">
                        <code style="color:#e0e0e0;font-family:monospace;font-size:13px;white-space:pre">{formatted}</code>
                    </div>
                    ''',
                    unsafe_allow_html=True
                )
            except json.JSONDecodeError:
                # Insert line breaks before common keywords for readability
                for kw in [" FROM ", " LEFT JOIN ", " WHERE ", " GROUP BY ", " ORDER BY "]:
                    sql_string = sql_string.replace(kw, f"\n{kw.strip()} ")

                # Split into lines
                lines = sql_string.split("\n")

                # Define SQL keywords for highlighting
                keywords = [
                    "SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER",
                    "ON", "GROUP BY", "ORDER BY", "LIMIT", "INSERT", "UPDATE", "DELETE"
                ]

                # Highlight each line individually
                highlighted_lines = []
                for line in lines:
                    for kw in keywords:
                        line = re.sub(
                            rf"\b{kw}\b",
                            f'<span style="color:#1d4ed8; font-weight:bold;">{kw}</span>',
                            line,
                            flags=re.IGNORECASE
                        )
                    # Strings in green
                    line = re.sub(r"('.*?')", r'<span style="color:#16a34a;">\1</span>', line)
                    # Comments in gray
                    line = re.sub(r"(--.*?$)", r'<span style="color:#6b7280;">\1</span>', line, flags=re.MULTILINE)
                    highlighted_lines.append(line)

                # Combine lines with subtle separators
                lines_html = "".join(
                    f'<div>{line}</div>'
                    for line in highlighted_lines
                )

                st.markdown(
                    f'''
                    <div style="
                        background: #1e1e2f; 
                        padding: 15px; 
                        border-radius: 8px; 
                        border: 1px solid #3f3f5f; 
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        overflow-x: auto;
                    ">
                        <code style="
                            color: #e0e0e0; 
                            font-family: monospace; 
                            font-size: 13px; 
                            background: transparent !important;
                            white-space: pre-wrap;
                        ">{lines_html}</code>
                    </div>
                    ''',
                    unsafe_allow_html=True
                )
        
        with st.expander("ℹ️ Execution Info", expanded=False):
            exec_info = viz.get('execution_info', {})
            row_count = exec_info.get('row_count', 'N/A')
            exec_time = exec_info.get('execution_time_ms', 'N/A')
            sample_data = df.head(5)
            st.write(f"**Rows Returned:** {row_count}")
            st.write(f"**Execution Time:** {exec_time} ms")
            st.write("**Sample Data:**")
            st.dataframe(sample_data)
    
    return None

def execute_visualization_query(viz_config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the query for a visualization and return it with data for rendering"""
    try:
        # Check if it's MongoDB (has pipeline in result)
        result = viz_config.get("result", {})
        print()
        print(f"Executing viz query, {result}")
        print()
        if "mongodb_query" in result:
            # MongoDB query - construct proper query format
            query_result = dash_api.execute_query(
                data_source=result["data_source"],
                query=result["mongodb_query"], 
                type="mongodb"
            )
        else:
            # SQL query
            query_result = dash_api.execute_query(
                data_source=result["data_source"],
                query=result["sql"],
                type="sql"
            )
        
        if not query_result or not query_result.get("data"):
            raise Exception("No data returned from query")
        
        df = pd.DataFrame(query_result["data"])
        
        x_column = result["config"].get("x_column")
        y_column = result["config"].get("y_column")
    
        x_column_query = result["query_config"].get("x_column")
        y_column_query = result["query_config"].get("y_column")

        return {
            **viz_config,
            "data": df,
            "x_column_query": x_column_query,
            "y_column_query": y_column_query,
            "x_column": x_column,
            "y_column": y_column,
            "type": result["chart_type"],
            "generated_sql": result.get("mongodb_query") or result.get("sql", ""),
            "user_query": result.get("original_user_query", ""),
            "execution_info": {
                "row_count": len(df),
                "execution_time_ms": query_result.get("execution_time_ms", 0)
            }
        }
        
    except Exception as e:
        return {
            **viz_config,
            "type": "error",
            "data": pd.DataFrame(),
            "error": str(e)
        }

# Function to load dashboard and execute all visualization queries
def load_dashboard_with_data(dashboard: Dict[str, Any]) -> Dict[str, Any]:
    """Load dashboard and execute all visualization queries to get live data"""
    dashboard_with_data = dashboard.copy()
    print()
    print(f"Loading dashboard with data: {dashboard}")
    print()

    # Execute each visualization query
    visualizations_with_data = []
    
    for viz_config in dashboard["visualizations"]:
        title = viz_config.get('title') or viz_config.get('result', {}).get('title', 'Visualization')
        with st.spinner(f"Loading {title}..."):
            viz_with_data = execute_visualization_query(viz_config)
            visualizations_with_data.append(viz_with_data)
    
    dashboard_with_data["visualizations"] = visualizations_with_data
    return dashboard_with_data

# Update your render_dashboard_summary_with_load function
def render_dashboard_summary_with_load(dashboard: Dict[str, Any]):
    """Render dashboard summary card with load from API capability"""
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.subheader(dashboard['name'])
            st.caption(dashboard['description'] if dashboard['description'] else "No description")
            
            # Status badge
            status = "saved" if dashboard.get('is_saved') else "draft"
            status_class = "status-active" if dashboard.get('is_saved') else "status-temporary"
            status_text = "Saved" if dashboard.get('is_saved') else "Local Draft"
            
            st.markdown(f"""
            <span class="status-badge {status_class}">
                {'💾' if dashboard.get('is_saved') else '📝'} {status_text}
            </span>
            """, unsafe_allow_html=True)
            print()
            print(f"dashboard data, {dashboard}")
            print()
            st.caption(f"📅 Modified: {dashboard['metadata']['last_modified'].strftime('%Y-%m-%d %H:%M')}")
            viz_count = len(dashboard.get('visualizations', [])) or dashboard['metadata'].get('visualization_count', 0)
            st.caption(f"📊 {viz_count} visualizations")    

        with col2:
            if st.button("👁️ View", key=f"view_{dashboard.get('id', 'temp')}"):
                with st.spinner("Loading with live data..."):
                    if dashboard.get('is_saved'):
                        # Load from API then execute queries
                        fresh_dashboard = dash_api.load_dashboard_from_api(dashboard['id'])
                        if fresh_dashboard:
                            dashboard_with_data = load_dashboard_with_data(fresh_dashboard)
                            st.session_state.current_dashboard = dashboard_with_data
                    else:
                        # Local dashboard - just execute queries
                        dashboard_with_data = load_dashboard_with_data(dashboard)
                        st.session_state.current_dashboard = dashboard_with_data
                    
                    st.session_state.current_page = "generate"
                    st.rerun()
        
        with col3:
            if st.button("📤 Export", key=f"export_{dashboard.get('id', 'temp')}"):
                # Export without the data field (just the configuration)
                export_dashboard = dashboard.copy()
                export_visualizations = []
                
                for viz in export_dashboard.get("visualizations", []):
                    export_viz = {k: v for k, v in viz.items() if k != "data"}
                    export_visualizations.append(export_viz)
                
                export_dashboard["visualizations"] = export_visualizations
                
                export_data = {
                    "version": "1.0",
                    "dashboard": export_dashboard,
                    "exported_at": datetime.now().isoformat()
                }
                st.download_button(
                    "Download",
                    data=json.dumps(export_data, indent=2, default=str),
                    file_name=f"{dashboard['name']}.json",
                    mime="application/json",
                    key=f"download_{dashboard.get('id', 'temp')}"
                )
        
        with col4:
            if st.button("🗑️ Delete", key=f"delete_{dashboard.get('id', 'temp')}", type="secondary"):
                dashboard_id = dashboard.get('id')
                
                # Delete from API if it's saved
                if dashboard.get('is_saved') and dashboard_id:
                    with st.spinner("Deleting from database..."):
                        if dash_api.delete_dashboard_from_api(dashboard_id):
                            st.success("✅ Dashboard deleted from database")
                        else:
                            st.error("❌ Failed to delete from database")
                
                # Remove from session state
                if str(dashboard_id) in st.session_state.dashboards:
                    del st.session_state.dashboards[str(dashboard_id)]
                    if st.session_state.current_dashboard and st.session_state.current_dashboard.get('id') == dashboard_id:
                        st.session_state.current_dashboard = None
                    st.rerun()

# Sidebar with enhanced navigation
with st.sidebar:

    st.markdown(f"👤 {st.session_state.user_name}")
    st.caption(st.session_state.user_email)
    
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.divider()

    if st.button("💬 Chat Assistant", use_container_width=True):
        st.session_state.show_chat = not st.session_state.show_chat
    st.divider()

    # Navigation menu
    menu_items = [
        ("🚀 Generate Dashboard", "generate", "Create and edit dashboards"),
        ("📚 My Dashboards", "dashboards", "View saved dashboards"),
        ("🔌 Data Sources", "data_sources", "Manage data connections"), 
        ("📤 Import/Export", "import_export", "Data management")
    ]
    
    st.subheader("📋 Navigation")
    
    for label, key, description in menu_items:
        is_active = st.session_state.current_page == key
    
        clicked = st.button(
            label,
            key=f"nav_{key}",
            help=description,
            type="primary" if is_active else "secondary"
        )
        
        if clicked:
            st.session_state.current_page = key
            st.rerun()
    
    st.divider()
    
    # Current dashboard info
    if st.session_state.current_dashboard:
        st.subheader("📊 Current Dashboard")
        dashboard = st.session_state.current_dashboard
        st.write(f"**{dashboard['name']}**")
        st.caption(f"{len(dashboard['visualizations'])} visualizations")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save", key="sidebar_save"):
                with st.spinner("Saving dashboard..."):
                    result = dash_api.save_dashboard_to_api(dashboard, st.session_state.user_id)
                    if result:
                        # Refresh dashboards from API after saving
                        saved_dashboards = dash_api.list_saved_dashboards(user_id=st.session_state.user_id)
                        
                        # Update session state with fresh data
                        for fresh_dashboard in saved_dashboards:
                            st.session_state.dashboards[str(fresh_dashboard["id"])] = fresh_dashboard
                        
                        st.success("✅ Dashboard saved to database!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to save dashboard")
        
        with col2:
            if st.button("🗑️ Clear", key="sidebar_clear"):
                st.session_state.current_dashboard = None
                st.rerun()
    else:
        st.info("No dashboard selected")
    
    st.divider()

# Chat modal
if st.session_state.show_chat:
    chat_container = st.container()
    with chat_container:
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            st.markdown("#### 💬 AI Assistant")
        with col2:
            if st.button("🔄", key="reset_chat", help="Reset conversation"):
                if st.session_state.conversation_id:
                    dash_api.reset_chat_session(conversation_id=st.session_state.conversation_id, app_id=1, agent_id=11)
                st.session_state.chat_messages = []
                st.session_state.conversation_id = None  # Reset to start new conversation
                st.rerun()
        with col3:
            if st.button("✕", key="close_chat"):
                st.session_state.show_chat = False
                st.rerun()
        
        msg_box = st.container(height=500)
        with msg_box:
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
        
        if prompt := st.chat_input("Ask me to create visualizations..."):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            
            # Prepare full dashboard context
            dashboard_context = None
            if st.session_state.current_dashboard:
                dashboard_context = {
                    "dashboard_id": st.session_state.current_dashboard.get("id"),
                    "dashboard_name": st.session_state.current_dashboard.get("name"),
                    "description": st.session_state.current_dashboard.get("description"),
                    "visualizations": [
                        {
                            "id": viz.get("id"),
                            "title": viz.get("result", {}).get("title"),
                            "description": viz.get("result", {}).get("description"),
                            "type": viz.get("type"),
                            "chart_type": viz.get("result", {}).get("chart_type"),
                            "data_source": viz.get("result", {}).get("data_source"),
                            "original_query": viz.get("result", {}).get("original_user_query"),
                            "x_column": viz.get("x_column"),
                            "y_column": viz.get("y_column"),
                            "edit_history": viz.get("result", {}).get("edit_history", [])
                        }
                        for viz in st.session_state.current_dashboard.get("visualizations", [])
                    ]
                }
            
            response = dash_api.chat_with_agent(
                prompt, 
                conversation_id=st.session_state.conversation_id,  # Use stored ID or None for new conversation
                user_id=st.session_state.user_id,
                dashboard_context=dashboard_context  # Pass context
            )

            # Store the conversation_id returned by the API for follow-up messages
            if response.get("conversation_id"):
                st.session_state.conversation_id = response.get("conversation_id")

            action_taken = response.get("action_taken")

            # ⭐ Recargar si hubo edición
            if action_taken in ["visualization_edited", "visualization_added"]:
                if st.session_state.current_dashboard:
                    fresh_dashboard = dash_api.load_dashboard_from_api(
                        st.session_state.current_dashboard['id']
                    )
                    if fresh_dashboard:
                        st.session_state.current_dashboard = load_dashboard_with_data(fresh_dashboard)

            assistant_message = response["response"]
            st.session_state.chat_messages.append({"role": "assistant", "content": assistant_message})
            st.rerun()
    
    chat_container.float("position: fixed; bottom: 20px; right: 20px; width: 550px; background: #1e1e2e; border-radius: 12px; padding: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.2); z-index: 9999;")
    
# Main content area
if st.session_state.current_page == "generate":
    st.title("🚀 Dashboard Generator")
    
    # Current dashboard or create new
    if not st.session_state.current_dashboard:
        # Create new dashboard section
        with st.expander("🆕 Create New Dashboard", expanded=True):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                new_name = st.text_input("Dashboard Name", placeholder="My Awesome Dashboard")
                new_desc = st.text_area("Description (optional)", placeholder="This dashboard shows...")
            
            with col2:
                st.write("**Quick Templates**")
                templates = ["Sales Analytics", "Flight Performance", "Customer Insights", "Financial Report"]
                for template in templates:
                    if st.button(template, key=f"template_{template}"):
                        new_name = template
                        new_desc = f"Auto-generated {template.lower()} dashboard"
            
            if st.button("🚀 Create Dashboard", type="primary", disabled=not new_name):
                dashboard = generator.create_dashboard(new_name, new_desc)
                dashboard['is_saved'] = False  # Mark as not saved to database
                st.session_state.current_dashboard = dashboard
                st.success(f"Dashboard '{new_name}' created locally! Click 'Save' to persist to database.")
                st.rerun()
    
    else:
        # Working with existing dashboard
        dashboard = st.session_state.current_dashboard
        
        # Dashboard header
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.title(f"📊 {dashboard['name']}")
            if dashboard['description']:
                st.caption(dashboard['description'])
        
        with col2:
            status = "Saved" if dashboard['is_saved'] else "Draft"
            st.metric("Status", status)
        
        with col3:
            st.metric("Visualizations", len(dashboard['visualizations']))
        
        st.divider()
        
        # Add visualization section
        st.subheader("✨ Add New Visualization")
        
        # Query input
        query = st.text_area(
            "Describe your visualization",
            value=st.session_state.get('viz_query', ''),
            placeholder="Example: Show me the revenue by product category as a pie chart...",
            height=100,
            key="viz_query_input"
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("➕ Add Visualization", type="primary", disabled=not query):
                with st.spinner("🤖 Generating visualization config..."):
                    progress = st.progress(0)
                    
                    # Just create the fake config (no query execution)
                    for i in range(100):
                        time.sleep(0.01)
                        progress.progress(i + 1)
                    
                    # Generate fake visualization config
                    viz_config = dash_api.generate_sql_from_nlp(query)
                    print()
                    print(f"viz_config generated: {viz_config}")
                    print()
                    if "id" not in viz_config or viz_config["id"] is None:
                        viz_config["id"] = str(uuid.uuid4())

                    viz_with_data = execute_visualization_query(viz_config)
                    print()
                    print(f"viz_with_data generated: {viz_with_data}")
                    print()
                    dashboard['visualizations'].append(viz_with_data)
                    dashboard['metadata']['last_modified'] = datetime.now()
                    
                    progress.empty()
                    st.success("✅ Visualization added to dashboard!")
                    st.session_state.viz_query = ""
                    st.rerun()
            
        st.divider()
        
        if st.session_state.editing_viz_id:
            editing_viz = next((v for v in dashboard['visualizations'] if v['id'] == st.session_state.editing_viz_id), None)
            print()
            print(f"Editing viz. {editing_viz}")
            print()
            if editing_viz:
                st.subheader("✏️ Edit Visualization")
                
                with st.container():
                    st.info(f"Editing: **{editing_viz['result']['title']}**")
                    
                    edit_query = st.text_area(
                        "Describe changes",
                        value=st.session_state.edit_query,
                        placeholder="Example: Change to a line chart and group by month instead...",
                        height=100,
                        key="edit_query_input"
                    )
                    
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        if st.button("💾 Update Visualization", type="primary", disabled=not edit_query):
                            with st.spinner("🤖 Updating visualization..."):
                                updated_config = dash_api.edit_visualization(editing_viz, edit_query)
                                print()
                                print(f"updated config: {updated_config}")
                                print()
                                if updated_config.get("success"):
                                    updated_config["id"] = editing_viz['id']
                                    updated_viz = execute_visualization_query(updated_config)
                                    
                                    viz_index = next((idx for idx, v in enumerate(dashboard['visualizations']) 
                                                    if v['id'] == editing_viz['id']), None)
                                    if viz_index is not None:
                                        dashboard['visualizations'][viz_index] = updated_viz
                                        dashboard['metadata']['last_modified'] = datetime.now()
                                    
                                    st.session_state.editing_viz_id = None
                                    st.session_state.edit_query = ""
                                    st.success("✅ Visualization updated!")
                                    st.rerun()
                    
                    with col2:
                        if st.button("❌ Cancel", key="cancel_edit"):
                            st.session_state.editing_viz_id = None
                            st.session_state.edit_query = ""
                            st.rerun()
                
                st.divider()

        # Display visualizations in grid
        if dashboard['visualizations']:
            st.subheader(f"📊 Current Visualizations ({len(dashboard['visualizations'])})")
            
            # Check if visualizations have data, if not execute queries
            visualizations_to_display = dashboard['visualizations']
            if dashboard['visualizations'] and dashboard['visualizations'][0].get('data') is None:
                with st.spinner("Loading live data..."):
                    visualizations_to_display = []
                    for viz_config in dashboard['visualizations']:
                        viz_with_data = execute_visualization_query(viz_config)
                        visualizations_to_display.append(viz_with_data)

            # Grid layout - 3 visualizations per row
            for i in range(0, len(visualizations_to_display), 3):
                cols = st.columns(3)
                
                for j, viz in enumerate(visualizations_to_display[i:i+3]):
                    with cols[j]:
                        action = render_visualization(viz, show_controls=True)
                        
                        if action == "remove":
                            viz_index = next((idx for idx, v in enumerate(dashboard['visualizations']) if v['id'] == viz['id']), None)
                            if viz_index is not None:
                                dashboard['visualizations'].pop(viz_index)
                                dashboard['metadata']['last_modified'] = datetime.now()
                                st.success("✅ Visualization removed!")
                                st.rerun()
                        elif action == "edit":
                            st.session_state.editing_viz_id = viz['id']
                            st.session_state.edit_query = viz.get('user_query', '')
                            st.rerun()

        else:
            st.info("🎯 No visualizations yet. Add your first visualization using the form above!")

elif st.session_state.current_page == "dashboards":
    st.title("📚 My Dashboards")
    
    # Refresh dashboards from API
    if st.button("🔄 Refresh from Database"):
        with st.spinner("Loading dashboards from database..."):
            print(f"Sesion de usuario: {st.session_state.user_id}")
            saved_dashboards = dash_api.list_saved_dashboards(user_id=st.session_state.user_id)
            
            # Clear all saved dashboards and reload
            st.session_state.dashboards = {
                k: v for k, v in st.session_state.dashboards.items() 
                if not v.get('is_saved')  # Keep only local drafts
            }
            
            # Add refreshed dashboards
            for dashboard in saved_dashboards:
                st.session_state.dashboards[str(dashboard["id"])] = dashboard
            
            st.success(f"Loaded {len(saved_dashboards)} dashboards from database")
            st.rerun()
    
    if not st.session_state.dashboards:
        st.markdown("""
        <div class="hero-section">
            <div class="hero-title">No Dashboards Yet</div>
            <div class="hero-subtitle">Create your first dashboard to get started</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Create First Dashboard", type="primary"):
            st.session_state.current_page = "generate"
            st.rerun()
    
    else:
        # Dashboard list
        st.subheader(f"📋 All Dashboards ({len(st.session_state.dashboards)})")
        
        # Add filter tabs for local vs saved
        tab1, tab2 = st.tabs(["All", "Saved"])
        
        with tab1:
            dashboards = list(st.session_state.dashboards.values())
        with tab2:
            dashboards = [d for d in st.session_state.dashboards.values() if d.get('is_saved')]

        # Search and filters (existing code)
        col1, col2 = st.columns([2, 1])
        with col1:
            search = st.text_input("🔍 Search dashboards", placeholder="Search by name...")
        with col2:
            sort_by = st.selectbox("Sort by", ["Last Modified", "Name", "Created Date"])

        st.divider()
        
        # Display dashboards
        dashboards = list(st.session_state.dashboards.values())
        
        if search:
            dashboards = [d for d in dashboards if search.lower() in d['name'].lower()]
        
        # Sort dashboards
        if sort_by == "Name":
            dashboards.sort(key=lambda x: x['name'])
        elif sort_by == "Created Date":
            dashboards.sort(key=lambda x: x['metadata']['created_at'], reverse=True)
        else:  # Last Modified
            dashboards.sort(key=lambda x: x['metadata']['last_modified'], reverse=True)
        
        if dashboards:
            for dashboard in dashboards:
                render_dashboard_summary_with_load(dashboard)  # New function below
                st.divider()
        else:
            st.info("No dashboards match your search criteria.")

elif st.session_state.current_page == "import_export":
    st.title("📤 Import/Export")
    
    import_export_dashboards(st.session_state.user_id)

elif st.session_state.current_page == "data_sources":
    st.title("🔌 Data Sources")
    
    manage_data_sources(st.session_state.user_id)
