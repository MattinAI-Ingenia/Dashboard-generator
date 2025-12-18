# main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager
from sqlalchemy import text

from core.config import settings
from api.routers import dashboards, data_sources, nlp, queries, user, chat
from db.models import Base
from core.database import engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(" Creating database tables...")
    try:
        with engine.connect() as conn:
            with conn.begin():
                # Acquire lock to prevent race condition
                conn.execute(text("LOCK TABLE pg_catalog.pg_namespace IN SHARE ROW EXCLUSIVE MODE"))
                Base.metadata.create_all(bind=conn, checkfirst=True)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise
    yield
    
    # Shutdown 
    logger.info("Application shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dashboards.router, prefix=f"{settings.API_V1_STR}/dashboards", tags=["dashboards"])

app.include_router(data_sources.router, prefix=f"{settings.API_V1_STR}/data-sources", tags=["data-sources"])

app.include_router(queries.router, prefix=f"{settings.API_V1_STR}/queries", tags=["queries"])

app.include_router(nlp.router, prefix=f"{settings.API_V1_STR}/nlp", tags=["nlp"])

app.include_router(user.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])

app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])

@app.get("/")
def root():
    return {"message": "Welcome to the Recruitment System API"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)