import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid
import json
import time
from typing import Dict, List, Any
import plotly.express as px

from utils.dashboard_api import DashboardApi
from components.data_sources import manage_data_sources

dash_api = DashboardApi()

# CSS
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Modern variables */
    :root {
        --primary: #2563eb;
        --primary-dark: #1d4ed8;
        --secondary: #f1f5f9;
        --accent: #0ea5e9;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --text: #334155;
        --text-light: #64748b;
        --border: #e2e8f0;
        --bg-card: #F8F8FF;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #1e293b 0%, #334155 100%);
    }
    
    /* Card components */
    .dashboard-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .dashboard-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px -3px rgba(0, 0, 0, 0.1);
        border-color: var(--primary);
    }
    
    /* Button styles */
    .stExpander > div > div > p {
        color: #000000 !important;
    }

    /* Hero section */
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 3rem 2rem;
        color: white;
        text-align: center;
        margin: 2rem 0;
    }
    
    .hero-title {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 1rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
        margin-bottom: 0;
    }
    
    /* Status indicators */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .status-active {
        background-color: #dcfce7;
        color: #166534;
    }
    
    .status-temporary {
        background-color: #fef3c7;
        color: #92400e;
    }
    
    /* Action buttons */
    .action-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .action-card {
        background: var(--bg-card);
        border: 2px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .action-card:hover {
        border-color: var(--primary);
        background: #fafbff;
    }
    
    /* Visualization container */
    .viz-container {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    /* Progress styles */
    .progress-container {
        background: var(--secondary);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Menu item active state */
    .menu-item-active {
        background: var(--primary) !important;
        color: white !important;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

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

        # Load saved dashboards from API on initialization
        saved_dashboards = dash_api.list_saved_dashboards()
        for dashboard in saved_dashboards:
            st.session_state.dashboards[str(dashboard["id"])] = dashboard
    if 'current_dashboard' not in st.session_state:
        st.session_state.current_dashboard = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "generate"

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
            'layout': {
                'type': 'grid',
                'responsive': True
            },
            'metadata': {
                'created_at': datetime.now(),
                'last_modified': datetime.now(),
                'queries': [],
                'version': 1
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
        st.error(f"❌ {viz['result']['title']}: {viz['result']['description']}")
        if show_controls:
            with st.expander("📝 Failed Query", expanded=False):
                st.code(viz['result']['sql'], language='sql')
        st.markdown('</div>', unsafe_allow_html=True)
        return None
    
    # Check if data is available
    print()
    print(f"New Viz, {viz}")
    print()
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
                    return "edit"
    
    df = viz['data']
    x_col = viz['x_column']
    y_col = viz['y_column']
    
    # Create compact visualization
    if viz['type'] == 'barchart':
        fig = px.bar(df, x=x_col, y=y_col)
        fig.update_traces(
            marker_color='rgba(37, 99, 235, 0.8)',
            marker_line_color='rgba(37, 99, 235, 1)',
            marker_line_width=1
        )
    elif viz['type'] == 'piechart':
        fig = px.pie(df, names=x_col, values=y_col)
        fig.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            textfont_size=12,
            textfont_color='white',
            marker_line_color='white',
            marker_line_width=2
        )
    elif viz['type'] == 'timeseries':
        y_col = viz['y_column']
        
        # Check if y_col contains multiple columns (comma-separated string)
        if ',' in str(y_col):
            # Multiple series - melt the dataframe
            y_cols = [col.strip() for col in y_col.split(',')]
            df_melted = df.melt(id_vars=[x_col], value_vars=y_cols, 
                            var_name='series', value_name='value')
            fig = px.line(df_melted, x=x_col, y='value', color='series')
        elif len(df.columns) > 2:
            # Multiple columns in dataframe
            y_cols = [col for col in df.columns if col != x_col]
            df_melted = df.melt(id_vars=[x_col], value_vars=y_cols,
                            var_name='series', value_name='value')
            fig = px.line(df_melted, x=x_col, y='value', color='series')
        else:
            # Single line
            fig = px.line(df, x=x_col, y=y_col)
        
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
        with st.expander("👤 User Query", expanded=False):
            st.markdown(
                f'<div style="background: #f8f9fa; padding: 10px; border-radius: 5px; border: 1px solid #dee2e6;">'
                f'<code style="color: #000000 !important; font-family: monospace; font-size: 12px; background: transparent !important;">{viz["result"]["original_user_query"]}</code>'
                f'</div>',
                unsafe_allow_html=True
            )

        with st.expander("📝 SQL Query", expanded=False):
            st.markdown(
                f'<div style="background: #f8f9fa; padding: 10px; border-radius: 5px; border: 1px solid #dee2e6;">'
                f'<code style="color: #000000 !important; font-family: monospace; font-size: 12px; background: transparent !important;">{viz["generated_sql"]}</code>'
                f'</div>', 
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
        # Execute the query using your API
        query_result = dash_api.execute_query(
            data_source=viz_config["result"]["data_source"],
            query=viz_config["result"]["sql"]
        )
        print()
        print(f'query_result: {query_result}')
        print()
        if not query_result or not query_result.get("data"):
            raise Exception("No data returned from query")
        
        # Convert to DataFrame
        df = pd.DataFrame(query_result["data"])
 
        # Use config columns if they exist in the data, otherwise auto-detect
        x_column = viz_config["result"]["config"].get("x_column")
        y_column = viz_config["result"]["config"].get("y_column")

        # Return visualization with data for rendering
        return {
            **viz_config,  # Keep all original config
            "data": df,    # Add actual data for rendering
            "x_column": x_column,
            "y_column": y_column,
            "type": viz_config["result"]["chart_type"],  # Map chart_type to type for render function
            "generated_sql": viz_config["result"]["sql"],  # For SQL display
            "user_query": viz_config.get("user_query", ""),  # Original user query
            "execution_info": {
                "row_count": query_result.get("row_count", len(df)),
                "execution_time_ms": query_result.get("execution_time_ms", 0)
            }
        }
        
    except Exception as e:
        # Return error visualization
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
                    result = dash_api.save_dashboard_to_api(dashboard)
                    if result:
                        # Refresh dashboards from API after saving
                        saved_dashboards = dash_api.list_saved_dashboards()
                        
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
                            st.info("✏️ Editing functionality coming soon!")

        else:
            st.info("🎯 No visualizations yet. Add your first visualization using the form above!")

elif st.session_state.current_page == "dashboards":
    st.title("📚 My Dashboards")
    
    # Refresh dashboards from API
    if st.button("🔄 Refresh from Database"):
        with st.spinner("Loading dashboards from database..."):
            saved_dashboards = dash_api.list_saved_dashboards()
            
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
    
    tab1, tab2 = st.tabs(["📤 Export", "📥 Import"])
    
    with tab1:
        st.subheader("📤 Export Dashboards")
        
        # Load saved dashboards if needed
        saved_dashboards = [d for d in st.session_state.dashboards.values() if d.get('is_saved')]
        
        if not saved_dashboards:
            if st.button("🔄 Load Dashboards from Database"):
                with st.spinner("Loading dashboards..."):
                    saved_dashboards = dash_api.list_saved_dashboards()
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
                    
                    with col2:
                        preserve_ids = st.checkbox("Preserve original IDs", value=False)
                    
                    if st.button("📥 Import Dashboard", type="primary", disabled=validate_only):
                        try:
                            result = dash_api.import_dashboard(
                                import_data, 
                                new_name if new_name else None,
                                preserve_ids
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

elif st.session_state.current_page == "data_sources":
    st.title("🔌 Data Sources")
    
    manage_data_sources()
