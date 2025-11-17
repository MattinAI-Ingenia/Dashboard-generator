# app/services/query_executor.py
import logging
import re
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import signal
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import pymongo
from pymongo.errors import PyMongoError
import json

from db.models import DataSource
from schemas.query import QueryType, QueryValidationResult
from services.data_source_connector import DataSourceConnector
from core.config import settings

logger = logging.getLogger(__name__)

class QueryTimeoutError(Exception):
    """Raised when query execution exceeds timeout"""
    pass

class QueryValidationError(Exception):
    """Raised when query validation fails"""
    pass

class QueryExecutorService:
    def __init__(self, data_source: DataSource):
        self.data_source = data_source
        self.timeout_seconds = getattr(settings, 'QUERY_TIMEOUT_SECONDS', 300)  # 5 minutes default
        
        # Create connector using existing DataSourceConnector
        self.connector = DataSourceConnector({
            "type": data_source.type,
            "connection_info": data_source.connection_info
        })
    
    @contextmanager
    def _timeout_handler(self):
        """Context manager for handling query timeouts"""
        def timeout_handler(signum, frame):
            raise QueryTimeoutError(f"Query execution timed out after {self.timeout_seconds} seconds")
        
        # Set up timeout signal
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.timeout_seconds)
        
        try:
            yield
        finally:
            # Clean up
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    
    def execute_sql(
        self, 
        statement: str, 
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Execute SQL query and return results"""
        try:
            # Validate SQL statement
            self._validate_sql_statement(statement)
            
            # Add limit to query if not present
            limited_statement = self._add_limit_to_sql(statement, limit)
            
            # Use connector's connection URL builder
            connection_url = self.connector._build_sql_connection_url()
            print(f"Connection url: {connection_url}")
            engine = create_engine(connection_url, pool_pre_ping=True)

            with engine.connect() as connection:
                # Execute query with parameters
                result = connection.execute(
                    text(limited_statement)
                )
                
                # Convert to list of dictionaries
                columns = list(result.keys())
                rows = result.fetchall()
                
                return [
                    {columns[i]: self._serialize_value(row[i]) for i in range(len(columns))}
                    for row in rows
                ]
        
        except QueryTimeoutError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"SQL execution error: {str(e)}")
            raise ValueError(f"SQL execution failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in SQL execution: {str(e)}")
            raise
    
    def execute_mongodb(
        self, 
        statement: str, 
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Execute MongoDB query and return results"""
        try:
            logging.info(f"Executing MongoDB query: {statement}")
            # Parse MongoDB query (expecting JSON-like syntax)
            query_dict = json.loads(statement)
            
            connection_info = self.data_source.connection_info
            username = connection_info.get('username')
            password = connection_info.get('password')
            host = connection_info.get('host', 'localhost')
            port = connection_info.get('port', 27017)
            database = connection_info.get('database')

            if connection_info.get("connection_string"):
                connection_string = connection_info["connection_string"]
            elif username and password:
                connection_string = f"mongodb://{username}:{password}@{host}:{port}/{database}"
            else:
                connection_string = f"mongodb://{host}:{port}"

            client = pymongo.MongoClient(
                connection_string,
                serverSelectionTimeoutMS=30000,
                socketTimeoutMS=300000
            )
            
            db = client[connection_info.get('database')]
            
            # Execute query based on operation type
            if 'collection' not in query_dict:
                raise ValueError("MongoDB query must specify a collection")
            
            collection = db[query_dict['collection']]
            operation = query_dict.get('operation', 'find')
            
            if operation == 'find':
                cursor = collection.find(
                    query_dict.get('filter', {}),
                    query_dict.get('projection')
                )
                
                if 'sort' in query_dict:
                    cursor = cursor.sort(query_dict['sort'])
                
                cursor = cursor.limit(limit)
                results = list(cursor)
            
            elif operation == 'aggregate':
                pipeline = query_dict.get('pipeline', [])
                # Add limit stage if not present in pipeline
                if not any('$limit' in stage for stage in pipeline):
                    pipeline.append({'$limit': limit})
                
                cursor = collection.aggregate(pipeline)
                results = list(cursor)
            
            else:
                raise ValueError(f"Unsupported MongoDB operation: {operation}")
            
            # Convert ObjectId and other MongoDB types to JSON serializable
            return [self._serialize_mongodb_document(doc) for doc in results]
        
        except PyMongoError as e:
            logger.error(f"MongoDB execution error: {str(e)}")
            raise ValueError(f"MongoDB execution failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in MongoDB execution: {str(e)}")
            raise
        finally:
            if 'client' in locals():
                client.close()
    
    def validate_query(
        self, 
        query_type: QueryType, 
        statement: str, 
        parameters: Dict[str, Any]
    ) -> QueryValidationResult:
        """Validate query without executing it"""
        try:
            if query_type == QueryType.SQL:
                return self._validate_sql_query(statement, parameters)
            elif query_type == QueryType.MONGODB:
                return self._validate_mongodb_query(statement, parameters)
            else:
                return QueryValidationResult(
                    is_valid=False,
                    message=f"Unsupported query type: {query_type}",
                    suggestions=["Use 'sql' or 'mongodb' as query type"]
                )
        
        except Exception as e:
            logger.error(f"Query validation error: {str(e)}")
            return QueryValidationResult(
                is_valid=False,
                message=f"Validation error: {str(e)}",
                suggestions=[]
            )
    
    def _validate_sql_statement(self, statement: str) -> None:
        """Validate SQL statement for security and syntax"""
        # logger.info(f"sql statement, {statement}")
        # Remove comments and normalize whitespace
        cleaned = re.sub(r'--.*?\n|/\*.*?\*/', '', statement, flags=re.DOTALL)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip().upper()
        
        # Check for dangerous operations
        dangerous_keywords = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'ALTER', 
            'TRUNCATE', 'EXEC', 'EXECUTE', 'XP_', 'SP_'
        ]
        
        for keyword in dangerous_keywords:
            if re.search(rf'\b{keyword}\b', cleaned):
                raise QueryValidationError(
                    f"Operation '{keyword}' is not allowed. Only SELECT queries are permitted."
                )
        
        # Ensure it's a SELECT statement
        if not (cleaned.startswith('SELECT') or cleaned.startswith('WITH')):
            raise QueryValidationError("Only SELECT/WITH queries are allowed")
    
    def _add_limit_to_sql(self, statement: str, limit: int) -> str:
        """Add LIMIT clause to SQL if not present"""
        if re.search(r'\bLIMIT\s+\d+', statement, re.IGNORECASE):
            return statement
        
        return f"{statement.rstrip(';')} LIMIT {limit}"
    
    def _parse_mongodb_query(self, statement: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Parse MongoDB query string into executable format"""
        try:
            # Replace parameter placeholders
            for key, value in parameters.items():
                placeholder = f"${key}"
                if placeholder in statement:
                    statement = statement.replace(
                        placeholder, 
                        json.dumps(value) if not isinstance(value, str) else f'"{value}"'
                    )
            
            # Parse JSON-like query
            query_dict = json.loads(statement)
            return query_dict
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid MongoDB query format: {str(e)}")
    
    def _validate_sql_query(self, statement: str, parameters: Dict[str, Any]) -> QueryValidationResult:
        """Validate SQL query"""
        try:
            self._validate_sql_statement(statement)
            
            # Try to create a prepared statement to check syntax
            connection_url = self.connector._build_sql_connection_url()
            engine = create_engine(connection_url)
            
            with engine.connect() as connection:
                # Use EXPLAIN to validate without executing
                explain_query = f"EXPLAIN {statement}"
                connection.execute(text(explain_query), parameters)
            
            return QueryValidationResult(
                is_valid=True,
                message="SQL query is valid",
                suggestions=[]
            )
        
        except Exception as e:
            suggestions = []
            error_msg = str(e).lower()
            
            if "syntax error" in error_msg:
                suggestions.append("Check SQL syntax and keywords")
            if "table" in error_msg and "exist" in error_msg:
                suggestions.append("Verify table names exist in the database")
            if "column" in error_msg:
                suggestions.append("Check column names and aliases")
            
            return QueryValidationResult(
                is_valid=False,
                message=str(e),
                suggestions=suggestions
            )
    
    def _validate_mongodb_query(self, statement: str, parameters: Dict[str, Any]) -> QueryValidationResult:
        """Validate MongoDB query"""
        try:
            query_dict = self._parse_mongodb_query(statement, parameters)
            
            # Basic validation
            if 'collection' not in query_dict:
                return QueryValidationResult(
                    is_valid=False,
                    message="MongoDB query must specify a collection",
                    suggestions=["Add 'collection' field to your query"]
                )
            
            # Validate operation type
            operation = query_dict.get('operation', 'find')
            valid_operations = ['find', 'aggregate']
            
            if operation not in valid_operations:
                return QueryValidationResult(
                    is_valid=False,
                    message=f"Unsupported operation: {operation}",
                    suggestions=[f"Use one of: {', '.join(valid_operations)}"]
                )
            
            return QueryValidationResult(
                is_valid=True,
                message="MongoDB query is valid",
                suggestions=[]
            )
        
        except Exception as e:
            return QueryValidationResult(
                is_valid=False,
                message=str(e),
                suggestions=["Check JSON syntax and MongoDB query structure"]
            )
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize database values to JSON-compatible format"""
        if value is None:
            return None
        elif isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, bytes):
            return value.decode('utf-8', errors='ignore')
        elif hasattr(value, '__dict__'):
            return str(value)
        else:
            return value
    
    def _serialize_mongodb_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize MongoDB document to JSON-compatible format"""
        from bson import ObjectId
        
        result = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, dict):
                result[key] = self._serialize_mongodb_document(value)
            elif isinstance(value, list):
                result[key] = [
                    self._serialize_mongodb_document(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
        
        return result
    