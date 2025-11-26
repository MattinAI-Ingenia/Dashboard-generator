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
    
    async def get_schema(self, schema: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get schema information from the data source"""
        try:
            if self.type in ["postgresql", "mysql", "sqlite"]:
                return await self._get_sql_schema(schema=schema)
            elif self.type == "mongodb":
                return await self._get_mongodb_schema()
            else:
                return None
        except Exception as e:
            logger.error(f"Schema extraction failed: {str(e)}")
            return None
    
    async def _get_sql_schema(self, schema: Optional[str] = None) -> Dict[str, Any]:
        """Get SQL database schema - optimized"""
        connection_url = self._build_sql_connection_url()
        engine = create_engine(connection_url)
        inspector = inspect(engine)

         # Get all schemas or specific schema
        schemas_to_process = [schema] if schema else inspector.get_schema_names()
        system_schemas = ['information_schema', 'pg_catalog', 'mysql', 'sys']

        all_schemas = []
        for schema_name in schemas_to_process:
            if schema_name in system_schemas:
                continue

            # Extract tables
            tables = []
            with engine.connect() as conn:
                for table_name in inspector.get_table_names(schema=schema_name):                    
                    # Skip empty tables
                    result = conn.execute(text(f"SELECT 1 FROM {schema_name}.{table_name} LIMIT 1"))
                    if not result.fetchone():
                        continue 

                    pk_constraint = inspector.get_pk_constraint(table_name, schema=schema_name)
                    pk_columns = pk_constraint['constrained_columns'] if pk_constraint else []
                    
                    columns = [
                        {
                            "name": col["name"],
                            "type": str(col["type"]),
                            **({"primary_key": True} if col["name"] in pk_columns else {})
                        }
                        for col in inspector.get_columns(table_name, schema=schema_name)
                    ]
                    
                    # Get foreign keys
                    foreign_keys = [
                        {
                            "columns": fk['constrained_columns'],
                            "references": {"table": fk['referred_table'], "columns": fk['referred_columns']}
                        }
                        for fk in inspector.get_foreign_keys(table_name, schema=schema_name)
                    ]
                    
                    table_info = {"name": table_name, "columns": columns}
                    
                    if foreign_keys:
                        table_info["foreign_keys"] = foreign_keys
                        
                    tables.append(table_info)
                
            # Get views if requested
            views = []
            try:
                for view_name in inspector.get_view_names(schema=schema_name):
                    view_columns = []
                    for column in inspector.get_columns(view_name, schema=schema_name):
                        view_columns.append({
                            "name": column["name"],
                            "type": str(column["type"])
                        })
                    views.append({"name": view_name, "columns": view_columns, "is_view": True})
            except Exception:
                pass

            # Only add schema if it has tables or views
            if tables or views:
                schema_info = {"schema_name": schema_name, "tables": tables}
                if views:
                    schema_info["views"] = views
                all_schemas.append(schema_info)

        return {"schemas": all_schemas}
    
    async def _get_mongodb_schema(self) -> Dict[str, Any]:
        """Get MongoDB schema (collection info)"""
        host = self.connection_info.get('host', 'localhost')
        port = self.connection_info.get('port', 27017)
        username = self.connection_info.get('username')
        password = self.connection_info.get('password')
        database = self.connection_info.get('database')
        
        # Build connection string
        if self.connection_info.get("connection_string"):
            connection_string = self.connection_info["connection_string"]
        elif username and password:
            connection_string = f"mongodb://{username}:{password}@{host}:{port}/{database}"
        else:
            connection_string = f"mongodb://{host}:{port}"
        
        client = None
        try:
            client = pymongo.MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            db = client[database]
            
            # Test connection first
            db.command("ping")
            
            collections = []
            for collection_name in db.list_collection_names():
                collection = db[collection_name]
                doc_count = collection.count_documents({})
                
                if doc_count == 0:
                    continue
                
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
                    "fields": columns
                })
            logger.info(f"Extracted {len(collections)} collections from MongoDB database '{database}'")
            return {
                "databases": [{
                    "database_name": database,
                    "collections": collections
                }]
            }
            
        except Exception as e:
            raise Exception(f"MongoDB schema extraction failed: {str(e)}")
        finally:
            if client:
                client.close()

    def _build_sql_connection_url(self) -> str:
        """Build SQL connection URL from connection info"""
        info = self.connection_info
    
        # Parse JSON string if needed
        if isinstance(info, str):
            import json
            info = json.loads(info)
        
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
    