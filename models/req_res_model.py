from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Request models
class NL2SQLRequest(BaseModel):
    question: str
    max_length: Optional[int] = 512

# Response models  
class NL2SQLResponse(BaseModel):
    sql_query: str
    natural_language_answer: str
    execution_success: bool
    query_result: Optional[List[Dict[str, Any]]] = None  # 👈 added this
    error_message: Optional[str] = None


class DatabaseConnectionResponse(BaseModel):
    status: str
    message: str
    database_info: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None