from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class QueryExecutor:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def execute_sql(self, sql_query: str) -> Dict[str, Any]:
        """Execute SQL query and return results with natural language summary"""
        try:
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
        
        # Basic summary based on query type
        if "SELECT" in sql_query.upper():
            if row_count == 1:
                return f"Found 1 record matching your criteria."
            else:
                return f"Found {row_count} records matching your criteria."
        elif "INSERT" in sql_query.upper():
            return f"Successfully inserted {row_count} record(s)."
        elif "UPDATE" in sql_query.upper():
            return f"Successfully updated {row_count} record(s)."
        elif "DELETE" in sql_query.upper():
            return f"Successfully deleted {row_count} record(s)."
        else:
            return f"Query executed successfully. {row_count} record(s) affected."