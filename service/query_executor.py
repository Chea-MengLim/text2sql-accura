from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)

class QueryExecutor:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def _is_read_only_query(self, sql_query: str) -> tuple[bool, Optional[str]]:
        """
        Validate that SQL query is read-only (SELECT only)
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # Normalize query: remove comments and extra whitespace
        query_normalized = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)  # Remove single-line comments
        query_normalized = re.sub(r'/\*.*?\*/', '', query_normalized, flags=re.DOTALL)  # Remove multi-line comments
        query_normalized = query_normalized.strip().upper()
        
        # List of dangerous SQL keywords that modify data or structure
        dangerous_keywords = [
            r'\bINSERT\b',
            r'\bUPDATE\b',
            r'\bDELETE\b',
            r'\bDROP\b',
            r'\bTRUNCATE\b',
            r'\bALTER\b',
            r'\bCREATE\b',
            r'\bREPLACE\b',
            r'\bMERGE\b',
            r'\bGRANT\b',
            r'\bREVOKE\b',
            r'\bEXEC\b',
            r'\bEXECUTE\b',
            r'\bCALL\b',
        ]
        
        # Check for dangerous keywords
        for keyword_pattern in dangerous_keywords:
            if re.search(keyword_pattern, query_normalized):
                keyword = keyword_pattern.replace(r'\b', '').replace('\\', '')
                return False, f"Query contains forbidden operation: {keyword}. Only SELECT queries are allowed."
        
        # Check if query starts with SELECT or WITH (for CTEs)
        if not (query_normalized.startswith('SELECT') or query_normalized.startswith('WITH')):
            return False, "Only SELECT queries (data retrieval) are supported. Queries must start with SELECT or WITH."
        
        # Additional check for semicolons (multiple statements)
        statements = [s.strip() for s in sql_query.split(';') if s.strip()]
        if len(statements) > 1:
            return False, "Multiple SQL statements are not allowed. Only single SELECT queries are supported."
        
        return True, None
    
    def execute_sql(self, sql_query: str) -> Dict[str, Any]:
        """Execute SQL query and return results with natural language summary"""
        try:
            # SECURITY: Validate query is read-only before execution
            is_valid, error_message = self._is_read_only_query(sql_query)
            if not is_valid:
                logger.warning(f"Blocked non-SELECT query: {sql_query[:100]}")
                return {
                    "success": False,
                    "error": error_message,
                    "sql_query": sql_query,
                    "data": [],
                    "row_count": 0,
                    "summary": "⚠️ Security: " + error_message
                }
            
            # Execute the SQL query
            result = self.db.execute(text(sql_query))
            
            # Get column names
            columns = result.keys()
            
            # Fetch all rows
            rows = result.fetchall()
            
            # Convert to list of dictionaries
            data = [dict(zip(columns, row)) for row in rows]
            
            # Generate natural language summary
            summary = self._generate_summary(data, sql_query)
            
            return {
                "success": True,
                "data": data,
                "row_count": len(data),
                "summary": summary,
                "sql_query": sql_query
            }
            
        except Exception as e:
            logger.error(f"SQL execution failed: {str(e)}")
            # CRITICAL FIX: Rollback the transaction to allow retries
            self.db.rollback()
            logger.info("Transaction rolled back, ready for retry")
            
            return {
                "success": False,
                "error": str(e),
                "sql_query": sql_query,
                "data": [],
                "row_count": 0,
                "summary": f"Query failed: {str(e)}"
            }
    
    def _generate_summary(self, data: List[Dict], sql_query: str) -> str:
        """Generate natural language summary of query results"""
        if not data:
            return "No results found for your query."
        
        row_count = len(data)
        
        # Basic summary for SELECT queries (only type we allow)
        if row_count == 1:
            return f"Found 1 record matching your criteria."
        else:
            return f"Found {row_count} records matching your criteria."