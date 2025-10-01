import os
from sqlalchemy import create_engine, text, MetaData
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
from typing import Generator, Dict, List, Any

load_dotenv()

# Build URI from env vars
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# Create engine with better configuration
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Set to True for SQL debugging
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session():
    """Get a database session for direct use (not as FastAPI dependency)"""
    return SessionLocal()

def test_connection():
    """Test database connection and return a simple status"""
    try:
        with engine.connect() as conn:
            # simple test query
            conn.execute(text("Select 1"))
            return "Database connection sucessfull"
    except Exception as e:
        return f"Database Connection failed: {str(e)}"


def get_database_schema(conn=None) -> Dict[str, Any]:
    """Get comprehensive database schema information for LLM context"""
    if conn is None:
        conn = engine.connect()
        should_close = True
    else:
        should_close = False
    
    try:
        schema_info = {}
        
        # Get all tables in public schema
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result.fetchall()]
        
        for table in tables:
            # Get columns for each table
            result = conn.execute(text(f"""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = '{table}' 
                AND table_schema = 'public'
                ORDER BY ordinal_position;
            """))
            
            columns = []
            for row in result.fetchall():
                col_info = {
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2] == 'YES',
                    "default": row[3],
                    "max_length": row[4]
                }
                columns.append(col_info)
            
            # Get foreign key relationships
            result = conn.execute(text(f"""
                SELECT 
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name = '{table}';
            """))
            
            foreign_keys = []
            for row in result.fetchall():
                fk_info = {
                    "column": row[0],
                    "references_table": row[1],
                    "references_column": row[2]
                }
                foreign_keys.append(fk_info)
            
            schema_info[table] = {
                "columns": columns,
                "foreign_keys": foreign_keys
            }
        
        return schema_info
    
    finally:
        if should_close:
            conn.close()

def get_schema_context_for_llm() -> str:
    """Generate a formatted schema description for LLM prompts"""
    schema_info = get_database_schema()
    
    context = "Database Schema:\n"
    for table_name, table_info in schema_info.items():
        context += f"\nTable: {table_name}\n"
        context += "Columns:\n"
        
        for col in table_info["columns"]:
            nullable = "NULL" if col["nullable"] else "NOT NULL"
            context += f"  - {col['name']} ({col['type']}) {nullable}\n"
        
        if table_info["foreign_keys"]:
            context += "Foreign Keys:\n"
            for fk in table_info["foreign_keys"]:
                context += f"  - {fk['column']} -> {fk['references_table']}.{fk['references_column']}\n"
    
    return context


def execute_sql_query(query: str) -> Dict[str, Any]:
    """Execute a SQL query and return results safely"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            
            # Check if it's a SELECT query
            if query.strip().upper().startswith('SELECT'):
                rows = result.fetchall()
                columns = result.keys()
                return {
                    "status": "success",
                    "data": [dict(zip(columns, row)) for row in rows],
                    "row_count": len(rows)
                }
            else:
                # For INSERT, UPDATE, DELETE
                conn.commit()
                return {
                    "status": "success",
                    "message": "Query executed successfully",
                    "row_count": result.rowcount
                }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }