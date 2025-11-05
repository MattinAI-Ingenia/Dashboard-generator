import streamlit as st

def load_style():
    """Load custom CSS styles for the dashboard generator"""
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
