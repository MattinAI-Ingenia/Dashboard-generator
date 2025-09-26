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

dash_api = DashboardApi()

# Configure page
st.set_page_config(
    page_title="Dashboard AI Studio",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    
    def generate_visualization_simple(self, query: str, viz_id: str = None) -> Dict[str, Any]:
        """Generate fake visualization metadata - NO real query execution here"""
        if viz_id is None:
            viz_id = str(uuid.uuid4())
        
        # Return fake visualization with proper structure for saving to database
        return {
            "id": viz_id,
            "title": "Sales Revenue by Region",
            "description": "Quarterly sales breakdown by geographic region", 
            "chart_type": "bar_chart",
            "data_source": "Langflow",  
            "query": {
                "type": "sql",
                "statement": "SELECT COUNT(user_id), created_at FROM dashboard d GROUP BY created_at;",
                "parameters": {}
            },
            "original_query": query,
            "config": {
                "x_column": "created_at",
                "y_column": "count", 
                "show_legend": True
            },
            "created_at": datetime.now().isoformat() + "Z"
        }
    
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
        st.error(f"❌ {viz['title']}: {viz['description']}")
        if show_controls:
            with st.expander("📝 Failed Query", expanded=False):
                st.code(viz['generated_sql'], language='sql')
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
        st.markdown(f'<p style="color: #FFFFFF; font-weight: bold; margin-bottom: 0.5rem;">📊 {viz["title"]}</p>', unsafe_allow_html=True)
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
    if viz['type'] == 'bar_chart':
        fig = px.bar(df, x=x_col, y=y_col)
        fig.update_traces(
            marker_color='rgba(37, 99, 235, 0.8)',
            marker_line_color='rgba(37, 99, 235, 1)',
            marker_line_width=1
        )
    elif viz['type'] == 'pie_chart':
        fig = px.pie(df, names=x_col, values=y_col)
        fig.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            textfont_size=12,
            textfont_color='white',
            marker_line_color='white',
            marker_line_width=2
        )
    elif viz['type'] == 'line_chart':
        fig = px.line(df, x=x_col, y=y_col)
        fig.update_traces(
            line_color='rgba(37, 99, 235, 0.9)', 
            line_width=3,
            marker=dict(size=6, color='rgba(37, 99, 235, 1)')
        )
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
        # Create a unique container with custom CSS for this specific expander
        viz_container_key = f"viz_sql_{viz['id']}"
        
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
        with st.expander("📝 SQL Query", expanded=False):
            st.markdown(
                f'<div style="background: #f8f9fa; padding: 10px; border-radius: 5px; border: 1px solid #dee2e6;">'
                f'<code style="color: #000000 !important; font-family: monospace; font-size: 12px; background: transparent !important;">{viz["generated_sql"]}</code>'
                f'</div>', 
                unsafe_allow_html=True
            )
    
    return None

def execute_visualization_query(viz_config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the query for a visualization and return it with data for rendering"""
    try:
        # Execute the query using your API
        query_result = dash_api.execute_query(
            data_source=viz_config["data_source"],
            query=viz_config["query"]["statement"]
        )
        
        if not query_result or not query_result.get("data"):
            raise Exception("No data returned from query")
        
        # Convert to DataFrame
        df = pd.DataFrame(query_result["data"])
        
        # Auto-detect best columns for the chart type
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Use config columns if they exist in the data, otherwise auto-detect
        x_column = viz_config["config"].get("x_column")
        y_column = viz_config["config"].get("y_column")
        
        if x_column not in df.columns or y_column not in df.columns:
            # Fallback to auto-detection
            if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
                x_column = categorical_cols[0]
                y_column = numeric_cols[0]
            else:
                x_column = df.columns[0] if len(df.columns) > 0 else 'x'
                y_column = df.columns[1] if len(df.columns) > 1 else 'y'
        
        # Return visualization with data for rendering
        return {
            **viz_config,  # Keep all original config
            "data": df,    # Add actual data for rendering
            "x_column": x_column,
            "y_column": y_column,
            "type": viz_config["chart_type"],  # Map chart_type to type for render function
            "generated_sql": viz_config["query"]["statement"],  # For SQL display
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
            "error": str(e),
            "generated_sql": viz_config["query"]["statement"]
        }

# NEW: Function to load dashboard and execute all visualization queries
def load_dashboard_with_data(dashboard: Dict[str, Any]) -> Dict[str, Any]:
    """Load dashboard and execute all visualization queries to get live data"""
    dashboard_with_data = dashboard.copy()
    
    # Execute each visualization query
    visualizations_with_data = []
    
    for viz_config in dashboard["visualizations"]:
        with st.spinner(f"Loading {viz_config['title']}..."):
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
            st.caption(f"📊 {dashboard['metadata']['visualization_count']} visualizations")
        
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
        
        # Query suggestions
        suggestions = [
            "Show delayed flights by airport",
            "Sales revenue by region as bar chart",
            "Airline distribution pie chart",
            "Revenue trend over time",
            "Top 10 products by sales"
        ]

        st.write("💡 **Quick suggestions:**")
        cols = st.columns(len(suggestions))
        for i, suggestion in enumerate(suggestions):
            with cols[i]:
                if st.button(suggestion, key=f"suggestion_{i}"):
                    st.session_state.viz_query = suggestion
        
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
                    viz_config = generator.generate_visualization_simple(query)
                    viz_with_data = execute_visualization_query(viz_config)
                    dashboard['visualizations'].append(viz_with_data)
                    dashboard['metadata']['queries'].append(query)
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
        print(dashboards)
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
    
    tab1, tab2, tab3 = st.tabs(["📤 Export", "📥 Import", "🖼️ Export Images"])
    
    with tab1:
        st.subheader("📤 Export Dashboards")
        
        if st.session_state.dashboards:
            dashboard_options = {d['name']: d_id for d_id, d in st.session_state.dashboards.items()}
            selected_name = st.selectbox("Select dashboard to export", list(dashboard_options.keys()))
            
            if selected_name:
                selected_id = dashboard_options[selected_name]
                dashboard = st.session_state.dashboards[selected_id]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    include_data = st.checkbox("Include actual data", value=False)
                    format_type = st.selectbox("Export format", ["JSON"])
                
                with col2:
                    st.write("**Export Preview:**")
                    preview = {
                        "dashboard_name": dashboard['name'],
                        "visualizations_count": len(dashboard['visualizations']),
                        "created_at": dashboard['metadata']['created_at'].isoformat(),
                        "include_data": include_data
                    }
                    st.json(preview, expanded=False)
                
                if st.button("📤 Generate Export File", type="primary"):
                    export_data = {
                        "version": "1.0",
                        "dashboard": dashboard.copy(),
                        "exported_at": datetime.now().isoformat(),
                        "metadata": {
                            "include_data": include_data,
                            "export_format": format_type
                        }
                    }
                    
                    if not include_data:
                        for viz in export_data["dashboard"]["visualizations"]:
                            viz["data"] = f"<data_placeholder_for_{viz['type']}>"
                    
                    st.download_button(
                        "💾 Download Export File",
                        data=json.dumps(export_data, indent=2, default=str),
                        file_name=f"{dashboard['name']}_export.json",
                        mime="application/json"
                    )
        else:
            st.info("📋 No dashboards available for export. Create some dashboards first!")
    
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
                            dashboard_to_import = import_data["dashboard"].copy()
                            
                            if not preserve_ids:
                                dashboard_to_import["id"] = str(uuid.uuid4())
                                for viz in dashboard_to_import["visualizations"]:
                                    viz["id"] = str(uuid.uuid4())
                            
                            if new_name:
                                dashboard_to_import["name"] = new_name
                            
                            dashboard_to_import["metadata"]["last_modified"] = datetime.now()
                            dashboard_to_import["is_saved"] = False
                            
                            # Handle data placeholders
                            for viz in dashboard_to_import["visualizations"]:
                                if isinstance(viz.get("data"), str) and "placeholder" in viz["data"]:
                                    new_viz = generator.generate_visualization_simple("regenerate data")
                                    viz["data"] = new_viz["data"]
                            
                            dashboard_id = dashboard_to_import["id"]
                            st.session_state.dashboards[dashboard_id] = dashboard_to_import
                            
                            st.success(f"✅ Dashboard imported successfully!")
                            
                        except Exception as e:
                            st.error(f"❌ Import failed: {str(e)}")
                    
                    elif validate_only:
                        st.info("✅ Validation complete. File is ready for import.")
            
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON file. Please check the file format.")
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
    
    with tab3:
        st.subheader("🖼️ Export Visualizations as Images")
        
        if st.session_state.dashboards:
            dashboard_options = {d['name']: d_id for d_id, d in st.session_state.dashboards.items()}
            selected_dashboard = st.selectbox("Select dashboard", list(dashboard_options.keys()))
            
            if selected_dashboard:
                dashboard_id = dashboard_options[selected_dashboard]
                dashboard = st.session_state.dashboards[dashboard_id]
                
                if dashboard['visualizations']:
                    viz_options = {f"{viz['title']}": i for i, viz in enumerate(dashboard['visualizations'])}
                    selected_viz = st.selectbox("Select visualization", list(viz_options.keys()))
                    
                    if selected_viz:
                        viz_index = viz_options[selected_viz]
                        viz = dashboard['visualizations'][viz_index]
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            img_format = st.selectbox("Format", ["PNG", "PDF"])
                            width = st.number_input("Width (px)", value=800, min_value=100, max_value=4000)
                        
                        with col2:
                            height = st.number_input("Height (px)", value=600, min_value=100, max_value=4000)
                            dpi = st.number_input("DPI", value=300, min_value=72, max_value=600)
                        
                        with col3:
                            include_title = st.checkbox("Include title", value=True)
                            transparent_bg = st.checkbox("Transparent background", value=False)
                        
                        st.subheader("🖼️ Preview")
                        render_visualization(viz)
                        
                        if st.button("🖼️ Generate Image Export", type="primary"):
                            with st.spinner("Generating image..."):
                                time.sleep(2)
                                
                            st.success("✅ Image generated successfully!")
                            st.info(f"📁 Would generate {img_format} file: {width}x{height} at {dpi} DPI")
                            
                            st.download_button(
                                f"💾 Download {img_format}",
                                data=b"mock_image_data",
                                file_name=f"{viz['title']}.{img_format.lower()}",
                                mime=f"image/{img_format.lower()}"
                            )
                else:
                    st.info("Selected dashboard has no visualizations to export.")
        else:
            st.info("📋 No dashboards available. Create some dashboards first!")

elif st.session_state.current_page == "data_sources":
    st.title("🔌 Data Sources")
    
    # Tabs for different data source operations
    tab1, tab2, tab3 = st.tabs(["📋 My Sources", "➕ Add Source", "🧪 Test Sources"])
    
    with tab1:
        st.subheader("📋 Your Data Sources")
        
        # Fetch data sources from API
        data_sources = dash_api.call_api("/data-sources/")
        
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
                    result = dash_api.call_api("/data-sources/", method="POST", data=config)
                    
                if result:
                    st.success(f"Data source '{name}' added successfully!")
                    st.rerun()
            elif submitted:
                st.error("Please fill in required fields (Name and Database)")
    
    with tab3:
        st.subheader("🧪 Test Connections")
        
        data_sources = dash_api.call_api("/data-sources/")
        
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