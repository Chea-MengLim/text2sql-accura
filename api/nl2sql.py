from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.req_res_model import NL2SQLRequest, NL2SQLResponse, ErrorResponse
from service.sql_generator import SQLGenerator
from service.query_executor import QueryExecutor
from service.conversation_memory import ConversationMemoryService 
from config.database import SessionLocal, get_database_info, get_db  # Add DATABASE_URL
import logging
from utils.extract_sql import extract_sql
from utils.sqlite_to_postgresql import (
    convert_sqlite_to_postgresql,
    add_date_type_casts,
    fix_date_functions_on_text_columns,
    fix_extract_type_mismatches,
    handle_division_by_zero,
    fix_yyyymm_arithmetic,
    cleanup_double_casts,
    fix_complex_date_expressions, 
    fix_text_date_column_comparisons,
    fix_date_trunc_string_literals
)
import uuid  
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/nl2sql", tags=["nl2sql"])

# Initialize services
sql_generator = SQLGenerator()
memory_service = ConversationMemoryService(os.getenv("MY_POSTGRESQL"))  # Add this

@router.post("/query", response_model=NL2SQLResponse)
async def convert_nl_to_sql(
    request: NL2SQLRequest,
    db: Session = Depends(get_db)
):
    """Convert natural language question to SQL and execute it with conversation memory"""
    try:
        # Step 0: Get or create session ID
        session_id = request.session_id or str(uuid.uuid4())
        logger.info(f"Processing question for session: {session_id}")
        
        # Step 1: Load conversation memory from PostgreSQL
        memory = memory_service.get_memory(session_id, window_size=3)
        
        # Step 2: Format conversation context for the prompt
        conversation_context = memory_service.format_context_for_prompt(memory)
        
        if conversation_context:
            logger.info(f"Using conversation context (last 3 exchanges)")
        
        # Step 3: Generate SQL from natural language with context
        logger.info(f"Converting question to SQL: {request.question}")
        raw_sql_response = sql_generator.generate_sql(
            request.question,
            conversation_context  # Pass context to model
        )

        # Extract clean SQL from the response
        sql_query = extract_sql(raw_sql_response)

        # Convert SQLite syntax to PostgreSQL
        # IMPORTANT: Order matters! Text date conversions must come before type casts
        sql_query = convert_sqlite_to_postgresql(sql_query)
        sql_query = fix_complex_date_expressions(sql_query)
        sql_query = fix_date_trunc_string_literals(sql_query)  # Fix DATE_TRUNC with string literals
        sql_query = fix_yyyymm_arithmetic(sql_query)  # Fix YYYYMM arithmetic EARLY
        sql_query = fix_date_functions_on_text_columns(sql_query)  # Convert text cols to TO_DATE() EARLY
        sql_query = fix_text_date_column_comparisons(sql_query)  # Handle text date comparisons BEFORE type casts
        sql_query = add_date_type_casts(sql_query)  # Now safe to add type casts (skips text cols)
        sql_query = handle_division_by_zero(sql_query)
        sql_query = fix_extract_type_mismatches(sql_query)
        sql_query = cleanup_double_casts(sql_query)

        print("Raw SQL response:", raw_sql_response)
        print("Extracted SQL query:", sql_query)

        # Step 4: Execute the SQL query
        query_executor = QueryExecutor(db)
        execution_result = query_executor.execute_sql(sql_query)

        print("Execution result:", execution_result)
        
        # Step 5: Save exchange to PostgreSQL memory
        memory_service.save_exchange(
            memory=memory,
            question=request.question,
            sql=sql_query
        )
        logger.info(f"Exchange saved to session {session_id}")

        # Step 6: Prepare response
        if execution_result["success"]:
            return NL2SQLResponse(
                sql_query=sql_query,
                natural_language_answer=execution_result["summary"],
                execution_success=True,
                error_message=None
            )
        else:
            return NL2SQLResponse(
                sql_query=sql_query,
                natural_language_answer=f"Query generated but execution failed: {execution_result['error']}",
                execution_success=False,
                error_message=execution_result["error"]
            )

    except Exception as e:
        logger.error(f"NL2SQL processing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process your question: {str(e)}"
        )

@router.delete("/conversation/{session_id}")
async def clear_conversation(session_id: str):
    """Clear conversation history for a session"""
    try:
        memory_service.clear_session(session_id)
        return {
            "status": "success",
            "message": f"Conversation history cleared for session: {session_id}"
        }
    except Exception as e:
        logger.error(f"Failed to clear session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversation/{session_id}/count")
async def get_conversation_count(session_id: str):
    """Get number of messages in a session"""
    try:
        count = memory_service.get_session_message_count(session_id)
        return {
            "session_id": session_id,
            "message_count": count,
            "exchange_count": count // 2
        }
    except Exception as e:
        logger.error(f"Failed to get session count: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test")
async def test_nl2sql():
    """Test endpoint to verify NL2SQL service is working"""
    try:
        test_question = "Show me all users"
        sql_query = sql_generator.generate_sql(test_question)
        return {
            "status": "success",
            "test_question": test_question,
            "generated_sql": sql_query,
            "message": "NL2SQL service is working"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"NL2SQL service test failed: {str(e)}"
        }