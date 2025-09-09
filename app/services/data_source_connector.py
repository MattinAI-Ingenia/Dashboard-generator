# app/services/data_source_connector.py
import asyncio
from typing import Dict, Any, List, Optional
import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
import pymongo
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)

class DataSourceConnector:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.type = config.get("type")
        self.connection_info = config.get("connection_info", {})
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to the data source"""
        try:
            if self.type in ["postgresql", "mysql", "sqlite"]:
                return await self._test_sql_connection()
            elif self.type == "mongodb":
                return await self._test_mongodb_connection()
            else:
                return {
                    "success": False,
                    "error": f"Unsupported data source type: {self.type}"
                }
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _test_sql_connection(self) -> Dict[str, Any]:
        """Test SQL database connection"""
        try:
            connection_url = self._build_sql_connection_url()
            print(connection_url)
            engine = create_engine(connection_url, connect_args={"connect_timeout": 10})
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            return {
                "success": True,
                "message": "Connection successful",
                "details": {"type": self.type}
            }
        except SQLAlchemyError as e:
            return {
                "success": False,
                "error": f"Database connection failed: {str(e)}"
            }
    
    async def _test_mongodb_connection(self) -> Dict[str, Any]:
        """Test MongoDB connection"""
        try:
            connection_string = (
                self.connection_info.get("connection_string") or
                f"mongodb://{self.connection_info.get('host', 'localhost')}:"
                f"{self.connection_info.get('port', 27017)}"
            )
            
            client = pymongo.MongoClient(
                connection_string,
                serverSelectionTimeoutMS=10000
            )
            
            # Test connection
            client.admin.command('ismaster')
            
            return {
                "success": True,
                "message": "MongoDB connection successful"
            }
        except ConnectionFailure as e:
            return {
                "success": False,
                "error": f"MongoDB connection failed: {str(e)}"
            }
    
    async def get_schema(self) -> Optional[Dict[str, Any]]:
        """Get schema information from the data source"""
        try:
            if self.type in ["postgresql", "mysql", "sqlite"]:
                return await self._get_sql_schema()
            elif self.type == "mongodb":
                return await self._get_mongodb_schema()
            else:
                return None
        except Exception as e:
            logger.error(f"Schema extraction failed: {str(e)}")
            return None
    
    async def _get_sql_schema(self) -> Dict[str, Any]:
        """Get SQL database schema"""
        connection_url = self._build_sql_connection_url()
        engine = create_engine(connection_url)
        
        inspector = inspect(engine)
        tables = []
        
        for table_name in inspector.get_table_names():
            columns = []
            for column in inspector.get_columns(table_name):
                columns.append({
                    "name": column["name"],
                    "type": str(column["type"]),
                    "nullable": column.get("nullable", True),
                    "default_value": column.get("default"),
                    "is_primary_key": column.get("primary_key", False)
                })
            
            # Get row count
            try:
                with engine.connect() as conn:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    row_count = result.scalar()
            except:
                row_count = None
            
            tables.append({
                "name": table_name,
                "columns": columns,
                "row_count": row_count
            })
        
        return {"tables": tables}
    
    async def _get_mongodb_schema(self) -> Dict[str, Any]:
        """Get MongoDB schema (collection info)"""
        connection_string = (
            self.connection_info.get("connection_string") or
            f"mongodb://{self.connection_info.get('host', 'localhost')}:"
            f"{self.connection_info.get('port', 27017)}"
        )
        
        client = pymongo.MongoClient(connection_string)
        db = client[self.connection_info.get("database")]
        
        collections = []
        for collection_name in db.list_collection_names():
            collection = db[collection_name]
            
            # Get document count
            doc_count = collection.count_documents({})
            
            # Sample a document to infer schema
            sample_doc = collection.find_one()
            columns = []
            
            if sample_doc:
                for key, value in sample_doc.items():
                    columns.append({
                        "name": key,
                        "type": type(value).__name__,
                        "nullable": True
                    })
            
            collections.append({
                "name": collection_name,
                "columns": columns,
                "row_count": doc_count
            })
        
        return {"tables": collections}
    
    def _build_sql_connection_url(self) -> str:
        """Build SQL connection URL from connection info"""
        info = self.connection_info
        
        if info.get("connection_string"):
            return info["connection_string"]
        
        host = info.get("host", "localhost")
        port = info.get("port")
        database = info.get("database")
        username = info.get("username")
        password = info.get("password")
        
        if self.type == "postgresql":
            port = port or 5432
            if username and password:
                return f"postgresql://{username}:{password}@{host}:{port}/{database}"
            else:
                return f"postgresql://{host}:{port}/{database}"
        elif self.type == "mysql":
            port = port or 3306
            if username and password:
                return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
            else:
                return f"mysql+pymysql://{host}:{port}/{database}"
        elif self.type == "sqlite":
            return f"sqlite:///{database}"
        
        raise ValueError(f"Cannot build connection URL for type: {self.type}")