# Dashboard Generator

**MattinAI's AI-powered Dashboard Generator** - A full-stack application that enables users to create dashboards with AI assistance. Users can connect to multiple data sources, query data using natural language, and visualize insights with an intelligent AI core integration.

---

## Features

- **AI-Powered Dashboard Creation** - Generate dashboards using natural language with LLM integration
- **Multi-Data Source Support** - Connect to PostgreSQL and MongoDB databases
- **Natural Language Processing** - Query data sources using conversational NLP
- **Interactive Visualizations** - Create dynamic dashboards with Plotly
- **User Authentication** - Secure login and user management
- **Real-time Chat** - AI-assisted data exploration through chat interface
- **Data Source Management** - Easily connect and manage multiple databases
- **Dashboard Import/Export** - Share and backup dashboard configurations

---

## Prerequisites

Ensure you have the following installed:

- **Python 3.10+**
- **Docker & Docker Compose**
- **Git**

---

## Quick Start

### 1️.- Clone the Repository

```bash
git clone <repository-url>
cd Dashboard-generator
```

### 2️.- Set Up Environment Variables

Copy .env.example to an .env file and fill the fields. You only need to change the following ones: 

```env
# AI Core
AI_CORE_URL=http://localhost:8000
AI_CORE_API_KEY=your_api_key_here
```

### 3️.- Start Sytem

```bash
docker-compose up -d
```

This starts:
- **PostgreSQL** (port 5433) - Main application database
- **Test PostgreSQL** (port 5434) - Demo flight data database
- **MongoDB** (port 27018) - Demo user analytics database
- **Api** (port 8000) - Dashboard generator api

For configuring the Test PostgreSQL we need to execute the next command: 
```bash
docker exec -i test_postgres psql -U postgres -d demo < demo-big-en-20170815.sql
```

#### Front
```bash
cd front
uv run streamlit run dashboard_demo.py 
```


## Project Structure

```
Dashboard-generator/
├── app/                          # FastAPI Backend
│   ├── main.py                   # Application entry point
│   ├── api/
│   │   └── routers/              # API endpoints
│   │       ├── dashboards.py      # Dashboard CRUD operations
│   │       ├── data_sources.py    # Data source management
│   │       ├── queries.py         # Query execution
│   │       ├── nlp.py            # NLP processing
│   │       ├── chat.py           # Chat interface
│   │       └── user.py           # User management
│   ├── core/
│   │   ├── config.py             # Configuration settings
│   │   └── database.py           # Database connection
│   ├── db/
│   │   └── models.py             # SQLAlchemy ORM models
│   ├── repositories/             # Data access layer
│   └── services/                 # Business logic
│       ├── data_source_connector.py
│       ├── query_executor.py
│       └── langflow_client.py
│
├── front/                        # Streamlit Frontend
│   ├── dashboard_demo.py         # Main app
│   ├── components/               # Reusable UI components
│   │   ├── data_sources.py
│   │   └── import_export.py
│   └── utils/
│       ├── dashboard_api.py      # API client
│       └── style.py              # Styling utilities
│
├── streamlit_app/                # Alternative Streamlit setup
├── demo_data/                    # Sample data
│   └── mongo_init.js            # MongoDB initialization script
│
├── docker-compose.yml            # Database services
├── Dockerfile                    # Backend Docker image
├── requirements.txt              # Python dependencies
├── pyproject.toml               # Project metadata
└── README.md                    # This file
```

---

---

## API Endpoints

### Authentication & Users
- `POST /api/v1/users/register` - Register new user
- `POST /api/v1/users/login` - User login
- `GET /api/v1/users/me` - Get current user

### Dashboards
- `GET /api/v1/dashboards` - List all dashboards
- `POST /api/v1/dashboards` - Create new dashboard
- `GET /api/v1/dashboards/{id}` - Get dashboard details
- `PUT /api/v1/dashboards/{id}` - Update dashboard
- `DELETE /api/v1/dashboards/{id}` - Delete dashboard

### Data Sources
- `GET /api/v1/data-sources` - List data sources
- `POST /api/v1/data-sources` - Add data source
- `POST /api/v1/data-sources/{id}/test` - Test connection

### Queries
- `POST /api/v1/queries/execute` - Execute SQL query
- `GET /api/v1/queries/history` - Get query history

### NLP & Chat
- `POST /api/v1/nlp/process` - Process natural language
- `POST /api/v1/chat/message` - Send chat message

---

## 📄 License

See the [LICENSE](LICENSE) file for details.
