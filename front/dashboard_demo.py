import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import uuid
import json
import time
from typing import Dict, List, Any
import random

# Modern UI components
try:
    import streamlit_shadcn_ui as ui
    SHADCN_UI = True
except ImportError:
    SHADCN_UI = False

try:
    from streamlit_extras.stylable_container import stylable_container
    STYLABLE_CONTAINER = True
except ImportError:
    STYLABLE_CONTAINER = False

try:
    from streamlit_pills import pills
    PILLS = True
except ImportError:
    PILLS = False

ENHANCED_UI = SHADCN_UI or STYLABLE_CONTAINER or PILLS

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
    if 'current_dashboard' not in st.session_state:
        st.session_state.current_dashboard = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "generate"

init_session_state()

# Fake data generators
def generate_fake_flight_data():
    airports = ['JFK', 'LAX', 'ORD', 'DFW', 'ATL', 'SFO', 'LAS', 'SEA', 'MIA', 'BOS']
    airlines = ['American', 'Delta', 'United', 'Southwest', 'JetBlue']
    
    data = []
    for i in range(500):
        data.append({
            'flight_id': f'FL{random.randint(1000, 9999)}',
            'airport': random.choice(airports),
            'airline': random.choice(airlines),
            'delay_minutes': random.randint(0, 180) if random.random() > 0.3 else 0,
            'date': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d'),
            'passengers': random.randint(50, 300),
            'flight_type': random.choice(['Domestic', 'International']),
            'weather_delay': random.choice([True, False]) if random.random() > 0.7 else False
        })
    return pd.DataFrame(data)

def generate_fake_sales_data():
    regions = ['North', 'South', 'East', 'West', 'Central']
    products = ['Product A', 'Product B', 'Product C', 'Product D', 'Product E']
    
    data = []
    for i in range(300):
        data.append({
            'sale_id': f'S{random.randint(10000, 99999)}',
            'region': random.choice(regions),
            'product': random.choice(products),
            'revenue': random.randint(1000, 50000),
            'quantity': random.randint(1, 100),
            'date': (datetime.now() - timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d'),
            'salesperson': f'Sales Rep {random.randint(1, 20)}',
            'customer_type': random.choice(['Enterprise', 'SMB', 'Individual'])
        })
    return pd.DataFrame(data)

# Mock NLP processor
class MockNLPProcessor:
    def __init__(self):
        self.query_patterns = {
            'flights': ['flight', 'airplane', 'airport', 'delay', 'aviation'],
            'sales': ['sales', 'revenue', 'product', 'region', 'selling'],
            'users': ['user', 'customer', 'client', 'subscriber'],
            'time_series': ['over time', 'trend', 'evolution', 'monthly', 'daily'],
            'comparison': ['compare', 'vs', 'versus', 'between'],
            'top': ['top', 'best', 'highest', 'maximum'],
            'pie': ['pie', 'distribution', 'breakdown', 'proportion'],
            'bar': ['bar', 'column', 'compare'],
            'line': ['line', 'trend', 'over time', 'evolution']
        }
    
    def process_query(self, query: str) -> Dict[str, Any]:
        query_lower = query.lower()
        
        data_source = 'flights'
        if any(word in query_lower for word in self.query_patterns['sales']):
            data_source = 'sales'
        
        viz_type = 'bar_chart'
        if any(word in query_lower for word in self.query_patterns['pie']):
            viz_type = 'pie_chart'
        elif any(word in query_lower for word in self.query_patterns['line']):
            viz_type = 'line_chart'
        
        if data_source == 'flights':
            sql = "SELECT airport, COUNT(*) as delayed_flights FROM flights WHERE delay_minutes > 0 GROUP BY airport"
            if 'airline' in query_lower:
                sql = "SELECT airline, AVG(delay_minutes) as avg_delay FROM flights GROUP BY airline"
        else:
            sql = "SELECT region, SUM(revenue) as total_revenue FROM sales GROUP BY region"
            if 'product' in query_lower:
                sql = "SELECT product, SUM(revenue) as total_revenue FROM sales GROUP BY product"
        
        return {
            'data_source': data_source,
            'visualization_type': viz_type,
            'generated_sql': sql,
            'confidence': random.uniform(0.8, 0.95),
            'suggestions': [
                "Try being more specific with date ranges",
                "Consider adding filters for better insights"
            ]
        }

# Dashboard generator
class DashboardGenerator:
    def __init__(self):
        self.nlp = MockNLPProcessor()
        self.flight_data = generate_fake_flight_data()
        self.sales_data = generate_fake_sales_data()
    
    def generate_visualization(self, query: str, viz_id: str = None) -> Dict[str, Any]:
        if viz_id is None:
            viz_id = str(uuid.uuid4())
        
        interpretation = self.nlp.process_query(query)
        
        if interpretation['data_source'] == 'flights':
            df = self.flight_data
        else:
            df = self.sales_data
        
        if interpretation['visualization_type'] == 'bar_chart':
            if interpretation['data_source'] == 'flights':
                if 'airline' in query.lower():
                    chart_data = df.groupby('airline')['delay_minutes'].mean().reset_index()
                    title = "Average Delay by Airline"
                    x_col, y_col = 'airline', 'delay_minutes'
                else:
                    delayed_flights = df[df['delay_minutes'] > 0]
                    chart_data = delayed_flights.groupby('airport').size().reset_index(name='delayed_flights')
                    title = "Delayed Flights by Airport"
                    x_col, y_col = 'airport', 'delayed_flights'
            else:
                if 'product' in query.lower():
                    chart_data = df.groupby('product')['revenue'].sum().reset_index()
                    title = "Revenue by Product"
                    x_col, y_col = 'product', 'revenue'
                else:
                    chart_data = df.groupby('region')['revenue'].sum().reset_index()
                    title = "Revenue by Region"
                    x_col, y_col = 'region', 'revenue'
        
        elif interpretation['visualization_type'] == 'pie_chart':
            if interpretation['data_source'] == 'flights':
                chart_data = df.groupby('airline').size().reset_index(name='flights')
                title = "Flight Distribution by Airline"
                x_col, y_col = 'airline', 'flights'
            else:
                chart_data = df.groupby('region')['revenue'].sum().reset_index()
                title = "Revenue Distribution by Region"
                x_col, y_col = 'region', 'revenue'
        
        else:  # line_chart
            if interpretation['data_source'] == 'flights':
                df['date'] = pd.to_datetime(df['date'])
                chart_data = df.groupby('date')['delay_minutes'].mean().reset_index()
                title = "Average Delay Trend Over Time"
                x_col, y_col = 'date', 'delay_minutes'
            else:
                df['date'] = pd.to_datetime(df['date'])
                chart_data = df.groupby('date')['revenue'].sum().reset_index()
                title = "Revenue Trend Over Time"
                x_col, y_col = 'date', 'revenue'
        
        return {
            'id': viz_id,
            'type': interpretation['visualization_type'],
            'title': title,
            'description': f"Generated from query: {query}",
            'data': chart_data,
            'x_column': x_col,
            'y_column': y_col,
            'generated_sql': interpretation['generated_sql'],
            'config': {
                'color_scheme': 'viridis',
                'show_legend': True,
                'height': 400
            }
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
    container_class = "viz-container" if not STYLABLE_CONTAINER else ""
    
    if STYLABLE_CONTAINER:
        with stylable_container(
            key=f"viz_{viz['id']}",
            css_styles="""
            {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            }
            """,
        ):
            _render_viz_content(viz, show_controls)
    else:
        st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)
        _render_viz_content(viz, show_controls)
        st.markdown('</div>', unsafe_allow_html=True)

def _render_viz_content(viz: Dict[str, Any], show_controls: bool = False):
    """Render visualization content"""
    # Compact header
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown(f'<p style="color: #000000; font-weight: bold; margin-bottom: 0.5rem;">📊 {viz["title"]}</p>', unsafe_allow_html=True)
        if show_controls:
            st.caption(viz['description'])
    
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

def render_dashboard_summary(dashboard: Dict[str, Any]):
    """Render dashboard summary card"""
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.subheader(dashboard['name'])
            st.caption(dashboard['description'] if dashboard['description'] else "No description")
            
            # Status badge
            status = "saved" if dashboard['is_saved'] else "draft"
            status_class = "status-active" if dashboard['is_saved'] else "status-temporary"
            status_text = "Saved" if dashboard['is_saved'] else "Draft"
            
            st.markdown(f"""
            <span class="status-badge {status_class}">
                {'💾' if dashboard['is_saved'] else '📝'} {status_text}
            </span>
            """, unsafe_allow_html=True)
            
            st.caption(f"📅 Modified: {dashboard['metadata']['last_modified'].strftime('%Y-%m-%d %H:%M')}")
            st.caption(f"📊 {len(dashboard['visualizations'])} visualizations")
        
        with col2:
            if st.button("👁️ View", key=f"view_{dashboard['id']}"):
                st.session_state.current_dashboard = dashboard
                st.session_state.current_page = "generate"
                st.rerun()
        
        with col3:
            if st.button("📤 Export", key=f"export_{dashboard['id']}"):
                export_data = {
                    "version": "1.0",
                    "dashboard": dashboard,
                    "exported_at": datetime.now().isoformat()
                }
                st.download_button(
                    "Download",
                    data=json.dumps(export_data, indent=2, default=str),
                    file_name=f"{dashboard['name']}.json",
                    mime="application/json",
                    key=f"download_{dashboard['id']}"
                )
        
        with col4:
            if st.button("🗑️ Delete", key=f"delete_{dashboard['id']}", type="secondary"):
                if dashboard['id'] in st.session_state.dashboards:
                    del st.session_state.dashboards[dashboard['id']]
                    if st.session_state.current_dashboard and st.session_state.current_dashboard['id'] == dashboard['id']:
                        st.session_state.current_dashboard = None
                    st.success(f"✅ Dashboard '{dashboard['name']}' deleted")
                    st.rerun()

# Sidebar with enhanced navigation
with st.sidebar:
    # Navigation menu
    menu_items = [
        ("🚀 Generate Dashboard", "generate", "Create and edit dashboards"),
        ("📚 My Dashboards", "dashboards", "View saved dashboards"),
        ("🔧 Settings", "settings", "System configuration"),
        ("📤 Import/Export", "import_export", "Data management")
    ]
    
    st.subheader("📋 Navigation")
    
    for label, key, description in menu_items:
        is_active = st.session_state.current_page == key
        
        if SHADCN_UI:
            clicked = ui.button(
                text=label,
                key=f"nav_{key}",
                variant="default" if is_active else "ghost",
                size="sm"
            )
        else:
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
            if st.button("💾 Save", key="sidebar_save", disabled=dashboard['is_saved']):
                dashboard['is_saved'] = True
                dashboard['metadata']['last_modified'] = datetime.now()
                st.session_state.dashboards[dashboard['id']] = dashboard
                st.success("✅ Dashboard saved!")
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear", key="sidebar_clear"):
                st.session_state.current_dashboard = None
                st.rerun()
    else:
        st.info("No dashboard selected")
    
    st.divider()
    
    # Quick stats
    st.subheader("📈 Quick Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Saved", len(st.session_state.dashboards))
    with col2:
        current = "Yes" if st.session_state.current_dashboard else "No"
        st.metric("Current", current)

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
                st.session_state.current_dashboard = dashboard
                st.success(f"✅ Dashboard '{new_name}' created!")
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
        
        if PILLS:
            selected = pills("Quick suggestions", suggestions, key="viz_suggestions")
            if selected:
                st.session_state.viz_query = selected
        else:
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
                with st.spinner("🤖 Generating visualization..."):
                    progress = st.progress(0)
                    for i in range(100):
                        time.sleep(0.01)
                        progress.progress(i + 1)
                    
                    viz = generator.generate_visualization(query)
                    dashboard['visualizations'].append(viz)
                    dashboard['metadata']['queries'].append(query)
                    dashboard['metadata']['last_modified'] = datetime.now()
                    
                    progress.empty()
                    st.success("✅ Visualization added!")
                    st.session_state.viz_query = ""
                    st.rerun()
        
        st.divider()
        
        # Display visualizations in grid
        if dashboard['visualizations']:
            st.subheader(f"📊 Current Visualizations ({len(dashboard['visualizations'])})")
            
            # Grid layout - 3 visualizations per row
            visualizations = dashboard['visualizations']
            
            for i in range(0, len(visualizations), 3):
                cols = st.columns(3)
                
                for j, viz in enumerate(visualizations[i:i+3]):
                    with cols[j]:
                        action = render_visualization(viz, show_controls=True)
                        
                        if action == "remove":
                            # Find and remove the visualization
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
        
        # Search and filters
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search = st.text_input("🔍 Search dashboards", placeholder="Search by name...")
        with col2:
            sort_by = st.selectbox("Sort by", ["Last Modified", "Name", "Created Date"])
        with col3:
            filter_status = st.selectbox("Filter", ["All", "Saved", "Drafts"])
        
        st.divider()
        
        # Display dashboards
        dashboards = list(st.session_state.dashboards.values())
        
        # Apply filters
        if filter_status == "Saved":
            dashboards = [d for d in dashboards if d['is_saved']]
        elif filter_status == "Drafts":
            dashboards = [d for d in dashboards if not d['is_saved']]
        
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
                render_dashboard_summary(dashboard)
                st.divider()
        else:
            st.info("No dashboards match your search criteria.")

elif st.session_state.current_page == "settings":
    st.title("🔧 System Settings")
    
    # Database schemas
    st.subheader("🗄️ Available Data Sources")
    
    schemas = {
        "flights_db": {
            "description": "Commercial flights database",
            "tables": {
                "flights": ["flight_id", "airport", "airline", "delay_minutes", "date", "passengers"],
                "airports": ["airport_code", "name", "city", "country"],
                "airlines": ["airline_code", "name", "country"]
            },
            "status": "active"
        },
        "sales_db": {
            "description": "Sales and revenue database", 
            "tables": {
                "sales": ["sale_id", "region", "product", "revenue", "quantity", "date"],
                "products": ["product_id", "name", "category", "price"],
                "customers": ["customer_id", "name", "region", "type"]
            },
            "status": "active"
        }
    }
    
    for schema_name, schema_info in schemas.items():
        with st.expander(f"📊 {schema_name.replace('_', ' ').title()}", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Description:** {schema_info['description']}")
                st.write("**Available Tables:**")
                
                for table_name, columns in schema_info['tables'].items():
                    st.write(f"• **{table_name}**: {', '.join(columns)}")
            
            with col2:
                status_class = "status-active" if schema_info['status'] == 'active' else "status-offline"
                st.markdown(f'<span class="status-badge {status_class}">🟢 Active</span>', unsafe_allow_html=True)
    
    st.divider()
    
    # Visualization types
    st.subheader("📈 Available Visualization Types")
    
    viz_types = {
        "bar_chart": {
            "name": "Bar Chart",
            "description": "Compare categorical values",
            "use_cases": ["Regional comparisons", "Product sales", "Airport traffic"],
            "icon": "📊"
        },
        "line_chart": {
            "name": "Line Chart", 
            "description": "Show trends over time",
            "use_cases": ["Time series", "Performance trends", "Growth patterns"],
            "icon": "📈"
        },
        "pie_chart": {
            "name": "Pie Chart",
            "description": "Show proportions and distributions", 
            "use_cases": ["Market share", "Distribution breakdown", "Category proportions"],
            "icon": "🥧"
        }
    }
    
    cols = st.columns(len(viz_types))
    for i, (viz_id, viz_info) in enumerate(viz_types.items()):
        with cols[i]:
            st.markdown(f"""
            <div class="dashboard-card" style="text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 1rem;">{viz_info['icon']}</div>
                <h4 style="color: #64748b;">{viz_info['name']}</h4>
                <p style="color: #64748b; margin-bottom: 1rem;">{viz_info['description']}</p>
                <div style="font-size: 0.875rem; color: #64748b;">
                    <strong>Use cases:</strong><br>
                    {', '.join(viz_info['use_cases'])}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # System metrics
    st.subheader("📊 System Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Dashboards", len(st.session_state.dashboards), delta="↗️")
    
    with col2:
        total_viz = sum(len(d['visualizations']) for d in st.session_state.dashboards.values())
        st.metric("Total Visualizations", total_viz, delta="↗️")
    
    with col3:
        st.metric("Data Sources", len(schemas), delta="Stable")
    
    with col4:
        st.metric("Viz Types", len(viz_types), delta="Stable")

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
                                    new_viz = generator.generate_visualization("regenerate data")
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

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 2rem;'>
    <p style="margin: 0; font-weight: 600;">🎨 Dashboard AI Studio</p>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.875rem;">
        Built with Streamlit • Powered by AI • Made with ❤️
    </p>
</div>
""", unsafe_allow_html=True)