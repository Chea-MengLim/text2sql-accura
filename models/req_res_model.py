from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Request models
class NL2SQLRequest(BaseModel):
    question: str
    session_id: Optional[str] = None  # Add this line for session tracking
    max_length: Optional[int] = 512

# Response models  
class NL2SQLResponse(BaseModel):
    sql_query: str
    natural_language_answer: str
    execution_success: bool
    error_message: Optional[str] = None
    chart_specification: Optional[Dict[str, Any]] = None  # Add this field
    data: Optional[List[Dict[str, Any]]] = None  # Optionally add actual data
    query_result: Optional[List[Dict[str, Any]]] = None  # 👈 added this for backward compatibility

class DatabaseConnectionResponse(BaseModel):
    status: str
    message: str
    database_info: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None