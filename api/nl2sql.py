from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.req_res_model import NL2SQLRequest, NL2SQLResponse, ErrorResponse
from service.sql_generator import SQLGenerator
from service.query_executor import QueryExecutor
from config.database import SessionLocal, get_database_info, get_db
import logging
import httpx
from utils.extract_sql import extract_sql
from utils.sqlite_to_postgresql import (
    convert_sqlite_to_postgresql,
    add_date_type_casts,
    fix_date_functions_on_text_columns,
    fix_extract_type_mismatches,
    handle_division_by_zero,
    fix_yyyymm_arithmetic,
    cleanup_double_casts
)
import re

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/nl2sql", tags=["nl2sql"])

# Initialize SQL generator (load model once)
sql_generator = SQLGenerator()

# --- language detection (no new dependency) ---

def looks_korean(text: str) -> bool:
    """
    Detects if the text contains any Hangul character (Korean syllables, jamo, or compatibility letters).
    Works even if mixed with English or spaces.
    """
    if not text:
        return False

    # Regex covering full Hangul ranges
    korean_pattern = re.compile(r"[\u1100-\u11FF\u3130-\u318F\uAC00-\uD7A3]")
    return bool(korean_pattern.search(text))


# --- local helper to translate KO -> EN via your Ollama model ---
async def translate_ko_to_en(text: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "timHan/llama3korean8B4QKM",   # make sure this matches `ollama list`
                    "prompt": f"Translate this Korean text into English:\n{text}",
                    "stream": False
                },
            )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        data = resp.json()
        return (data.get("response") or "").strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {e}")


@router.post("/query/auto", response_model=NL2SQLResponse)
async def query_auto(
    request: NL2SQLRequest,
    db: Session = Depends(get_db)
):
    """
    Auto language: if Korean -> translate to English first, else query directly.
    Then: NL->SQL, normalize SQL (SQLite->Postgres fixes), execute, respond.
    """
    try:
        user_text = request.question or ""
        use_translation = looks_korean(user_text)

        if use_translation:
            logger.info("Detected Korean. Translating to English before NL->SQL.")
            english_text = await translate_ko_to_en(user_text)
            print("english_text is : ", english_text)
            effective_question = english_text or user_text  # fallback if empty
        else:
            effective_question = user_text

        # --- Generate SQL from (possibly translated) question ---
        raw_sql_response = sql_generator.generate_sql(effective_question)
        sql_query = extract_sql(raw_sql_response)

        # --- Normalize SQL for Postgres (your existing fix-ups) ---
        sql_query = convert_sqlite_to_postgresql(sql_query)
        sql_query = add_date_type_casts(sql_query)
        sql_query = handle_division_by_zero(sql_query)
        sql_query = fix_yyyymm_arithmetic(sql_query)
        sql_query = fix_date_functions_on_text_columns(sql_query)
        sql_query = fix_extract_type_mismatches(sql_query)
        sql_query = cleanup_double_casts(sql_query)

        # --- Execute ---
        query_executor = QueryExecutor(db)
        execution_result = query_executor.execute_sql(sql_query)

        # --- Build response ---
        if execution_result.get("success"):
            return NL2SQLResponse(
                sql_query=sql_query,
                natural_language_answer=(
                    ("[Translated from Korean] " if use_translation else "")
                    + execution_result.get("summary", "Query executed.")
                ),
                query_result=execution_result.get("data"),
                execution_success=True,
                error_message=None
            )
        else:
            return NL2SQLResponse(
                sql_query=sql_query,
                natural_language_answer=(
                    ("[Translated from Korean] " if use_translation else "")
                    + "Query generated but execution failed."
                ),
                execution_success=False,
                query_result=None,
                error_message=execution_result.get("error")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("query_auto failed")
        raise HTTPException(status_code=500, detail=f"Failed to process your question: {e}")

@router.post("/query", response_model=NL2SQLResponse)
async def convert_nl_to_sql(
    request: NL2SQLRequest,
    db: Session = Depends(get_db)
):
    """Convert natural language question to SQL and execute it"""
    try:
        # Step 1: Generate SQL from natural language
        logger.info(f"Converting question to SQL: {request.question}")
        raw_sql_response = sql_generator.generate_sql(request.question)

        # Extract clean SQL from the response (removes markdown formatting)
        sql_query = extract_sql(raw_sql_response)

        # Convert SQLite syntax to PostgreSQL
        sql_query = convert_sqlite_to_postgresql(sql_query)

        # Add type casts for date comparisons
        sql_query = add_date_type_casts(sql_query)

        # Protect against division by zero
        sql_query = handle_division_by_zero(sql_query)

        # Fix YYYYMM text column arithmetic
        sql_query = fix_yyyymm_arithmetic(sql_query)
        
        # Fix date functions on text columns (add this line)
        sql_query = fix_date_functions_on_text_columns(sql_query)
        
        # Fix EXTRACT type mismatches (add this line)
        sql_query = fix_extract_type_mismatches(sql_query)
        

        # Clean up any double casts (add this line)
        sql_query = cleanup_double_casts(sql_query)

        print("Raw SQL response:", raw_sql_response)
        print("Extracted SQL query:", sql_query)

        # Step 2: Execute the SQL query
        query_executor = QueryExecutor(db)
        execution_result = query_executor.execute_sql(sql_query)

        print("Execution result:", execution_result)

        # Step 3: Prepare response
        if execution_result["success"]:
            return NL2SQLResponse(
                sql_query=sql_query,
                natural_language_answer=execution_result["summary"],
                query_result=execution_result["data"],
                execution_success=True,
                error_message=None
            )
        else:
            return NL2SQLResponse(
                sql_query=sql_query,
                natural_language_answer=f"Query generated but execution failed: {execution_result['error']}",
                execution_success=False,
                query_result=None,
                error_message=execution_result["error"]
            )

    except Exception as e:
        logger.error(f"NL2SQL processing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process your question: {str(e)}"
        )
@router.post("/query/memory", response_model=NL2SQLResponse)
async def convert_nl_to_sql(
    request: NL2SQLRequest,
    db: Session = Depends(get_db)
):
    """Convert natural language question to SQL and execute it"""
    try:
        # Step 1: Generate SQL from natural language
        logger.info(f"Converting question to SQL: {request.question}")
        raw_sql_response = sql_generator.generate_sql(request.question)

        # Extract clean SQL from the response (removes markdown formatting)
        sql_query = extract_sql(raw_sql_response)

        # Convert SQLite syntax to PostgreSQL
        sql_query = convert_sqlite_to_postgresql(sql_query)

        # Add type casts for date comparisons
        sql_query = add_date_type_casts(sql_query)

        # Protect against division by zero
        sql_query = handle_division_by_zero(sql_query)

        # Fix YYYYMM text column arithmetic
        sql_query = fix_yyyymm_arithmetic(sql_query)
        
        # Fix date functions on text columns (add this line)
        sql_query = fix_date_functions_on_text_columns(sql_query)
        
        # Fix EXTRACT type mismatches (add this line)
        sql_query = fix_extract_type_mismatches(sql_query)
        

        # Clean up any double casts (add this line)
        sql_query = cleanup_double_casts(sql_query)

        print("Raw SQL response:", raw_sql_response)
        print("Extracted SQL query:", sql_query)

        # Step 2: Execute the SQL query
        query_executor = QueryExecutor(db)
        execution_result = query_executor.execute_sql(sql_query)

        print("Execution result:", execution_result)

        # Step 3: Prepare response
        if execution_result["success"]:
            return NL2SQLResponse(
                sql_query=sql_query,
                natural_language_answer=execution_result["summary"],
                query_result=execution_result["data"],
                execution_success=True,
                error_message=None
            )
        else:
            return NL2SQLResponse(
                sql_query=sql_query,
                natural_language_answer=f"Query generated but execution failed: {execution_result['error']}",
                execution_success=False,
                query_result=None,
                error_message=execution_result["error"]
            )

    except Exception as e:
        logger.error(f"NL2SQL processing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process your question: {str(e)}"
        )

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