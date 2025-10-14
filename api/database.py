from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from config.database import get_db, test_connection, get_database_info
from models.req_res_model import DatabaseConnectionResponse, ErrorResponse

router = APIRouter(prefix="/api/database", tags=["database"])

@router.get("/connect", response_model=DatabaseConnectionResponse)
async def connect_database(db: Session = Depends(get_db)):
    """Test database connection and return status"""
    try:
        # Test the connection
        connection_result = test_connection()
        
        if connection_result["status"] == "success":
            # Get additional database info
            db_info = get_database_info()
            return DatabaseConnectionResponse(
                status="success",
                message="Database connected successfully",
                database_info=db_info
            )
        else:
            return DatabaseConnectionResponse(
                status="error",
                message=connection_result["message"]
            )
            
    except Exception as e:
        return DatabaseConnectionResponse(
            status="error",
            message=f"Database connection failed: {str(e)}"
        )

@router.get("/health")
async def database_health():
    """Simple health check for database connectivity"""
    result = test_connection()
    return {"status": result["status"], "message": result["message"]}