from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.req_res_model import NL2SQLRequest, NL2SQLResponse, ErrorResponse
from service.sql_generator import SQLGenerator
from service.query_executor import QueryExecutor
from service.conversation_memory import ConversationMemoryService 
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
    cleanup_double_casts,
    fix_complex_date_expressions, 
    fix_text_date_column_comparisons,
    fix_date_trunc_string_literals
)
import re
import uuid  
from dotenv import load_dotenv
import os
from service.ai_assistant import AIAssistant

load_dotenv()

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/nl2sql", tags=["nl2sql"])

# Initialize services
sql_generator = SQLGenerator()
ai_assistant = AIAssistant(model_name="llama3.1:8b")  # Using Ollama
memory_service = ConversationMemoryService(os.getenv("MY_POSTGRESQL"))

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

# --- local helper to translate EN -> KO via your Ollama model ---
async def translate_en_to_ko(text: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "timHan/llama3korean8B4QKM",   # make sure this matches `ollama list`
                    "prompt": f"Translate this English text into Korean:\n{text}",
                    "stream": False
                },
            )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        data = resp.json()
        return (data.get("response") or "").strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {e}")


@router.post("/query/bilingual", response_model=NL2SQLResponse)
async def query_bilingual(
    request: NL2SQLRequest,
    db: Session = Depends(get_db)
):
    """
    Bilingual endpoint with explainable natural language answers and conversation memory.
    Auto language: if Korean -> translate to English first, else query directly.
    Then: NL->SQL, normalize SQL (SQLite->Postgres fixes), execute, respond with AI explanations.
    """
    try:
        # Step 0: Get or create session ID
        session_id = request.session_id or str(uuid.uuid4())
        logger.info(f"Processing bilingual question for session: {session_id}")
        
        user_text = request.question or ""
        use_translation = looks_korean(user_text)
        
        logger.info(f"Processing question: '{user_text}'")
        logger.info(f"Korean detection result: {use_translation}")

        if use_translation:
            logger.info("Detected Korean. Translating to English before NL->SQL.")
            english_text = await translate_ko_to_en(user_text)
            print("english_text is : ", english_text)
            logger.info(f"Korean to English translation: '{user_text}' -> '{english_text}'")
            effective_question = english_text or user_text  # fallback if empty
        else:
            logger.info("English text detected, processing directly.")
            effective_question = user_text

        # Step 1: Load conversation memory from PostgreSQL
        memory = memory_service.get_memory(session_id, window_size=3)
        
        # Step 2: Format conversation context for the prompt
        conversation_context = memory_service.format_context_for_prompt(memory)
        
        if conversation_context:
            logger.info(f"Using conversation context (last 3 exchanges)")

        # Step 3: Generate SQL from (possibly translated) question with context
        raw_sql_response = await sql_generator.generate_sql(
            effective_question,
            conversation_context  # Pass context to model
        )
        sql_query = extract_sql(raw_sql_response)

        # Step 4: Normalize SQL for Postgres (your existing fix-ups)
        sql_query = convert_sqlite_to_postgresql(sql_query)
        sql_query = fix_complex_date_expressions(sql_query)
        sql_query = fix_date_trunc_string_literals(sql_query)
        sql_query = fix_yyyymm_arithmetic(sql_query)
        sql_query = fix_date_functions_on_text_columns(sql_query)
        sql_query = fix_text_date_column_comparisons(sql_query)
        sql_query = add_date_type_casts(sql_query)
        sql_query = handle_division_by_zero(sql_query)
        sql_query = fix_extract_type_mismatches(sql_query)
        sql_query = cleanup_double_casts(sql_query)

        print("Raw SQL response:", raw_sql_response)
        print("Extracted SQL query:", sql_query)

        # Step 5: Execute the SQL query
        query_executor = QueryExecutor(db)
        execution_result = query_executor.execute_sql(sql_query)

        print("Execution result:", execution_result)
        
        # Step 6: Generate AI-powered natural language explanation
        if execution_result["success"] and execution_result["data"]:
            logger.info("Generating AI explanation...")
            
            # Create context for explanation including language information
            explanation_context = f"Original question: {user_text}"
            if use_translation:
                explanation_context += f" (translated from Korean: {english_text})"
            
            nl_explanation = await ai_assistant.explain_result(
                user_question=explanation_context,
                sql_query=sql_query,
                result_data=execution_result["data"]
            )
            
            # Step 6.5: Translate explanation back to Korean if original input was Korean
            if use_translation:
                logger.info("Translating explanation back to Korean...")
                logger.info(f"Original English explanation: {nl_explanation[:100]}...")
                try:
                    korean_explanation = await translate_en_to_ko(nl_explanation)
                    logger.info(f"Korean translation result: {korean_explanation[:100]}...")
                    nl_explanation = korean_explanation
                    logger.info("Explanation successfully translated to Korean")
                except Exception as e:
                    logger.warning(f"Failed to translate explanation to Korean: {e}")
                    # Keep English explanation if translation fails
                    nl_explanation = f"[Translation failed] {nl_explanation}"
            
            # Step 7: Generate chart specification if applicable
            logger.info("Checking for chart generation...")
            chart_spec = await ai_assistant.generate_chart_spec(
                user_question=explanation_context,
                sql_query=sql_query,
                sql_result=execution_result["data"]
            )
            
            if chart_spec:
                logger.info(f"Chart generated: {chart_spec['chart_type']}")
            else:
                logger.info("No chart suitable for this data")
        else:
            # Fallback for failed queries or empty results
            nl_explanation = execution_result["summary"]
            if use_translation:
                # Try to translate the fallback message to Korean too
                try:
                    korean_fallback = await translate_en_to_ko(nl_explanation)
                    nl_explanation = korean_fallback
                except Exception as e:
                    logger.warning(f"Failed to translate fallback message to Korean: {e}")
            chart_spec = None
        
        # Step 7.5: Generate follow-up questions
        logger.info("Generating follow-up questions...")
        follow_up_questions = await ai_assistant.generate_follow_up_questions(
            user_question=explanation_context,
            sql_query=sql_query,
            result_data=execution_result["data"] if execution_result["success"] else [],
            execution_success=execution_result["success"],
            error_message=execution_result.get("error")
        )
        
        if follow_up_questions:
            logger.info(f"Generated {len(follow_up_questions)} follow-up questions")
        else:
            logger.info("No follow-up questions generated")
        
        # Step 8: Save exchange to PostgreSQL memory
        # Store both original text and effective question for context
        memory_service.save_exchange(
            memory=memory,
            question=f"Original: {user_text} | Effective: {effective_question}",
            sql=sql_query
        )
        logger.info(f"Bilingual exchange saved to session {session_id}")

        # Step 9: Build response with AI-generated content
        if execution_result.get("success"):
            # The explanation is already in the correct language (Korean if original was Korean, English if original was English)
            return NL2SQLResponse(
                sql_query=sql_query,
                natural_language_answer=nl_explanation,  # AI-generated explanation in appropriate language!
                execution_success=True,
                error_message=None,
                chart_specification=chart_spec,  # Chart data if available
                data=execution_result.get("data"),  # Include query results
                query_result=execution_result.get("data"),  # Backward compatibility
                follow_up_questions=follow_up_questions  # Include follow-up questions
            )
        else:
            # For error messages, translate to Korean if original input was Korean
            error_message = f"Query generated but execution failed: {execution_result['error']}"
            if use_translation:
                try:
                    korean_error = await translate_en_to_ko(error_message)
                    error_message = korean_error
                except Exception as e:
                    logger.warning(f"Failed to translate error message to Korean: {e}")
                
            return NL2SQLResponse(
                sql_query=sql_query,
                natural_language_answer=error_message,
                execution_success=False,
                error_message=execution_result.get("error"),
                chart_specification=None,
                data=[],
                query_result=None,
                follow_up_questions=follow_up_questions  # Include follow-up questions even for failed queries
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("query_bilingual failed")
        raise HTTPException(status_code=500, detail=f"Failed to process your bilingual question: {e}")

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
        raw_sql_response = await sql_generator.generate_sql(
            request.question,
            conversation_context  # Pass context to model
        )

        # Extract clean SQL from the response
        try:
            sql_query = extract_sql(raw_sql_response)
        except ValueError as e:
            # Handle truncated/incomplete SQL queries
            logger.error(f"SQL extraction failed: {str(e)}")
            error_msg = (
                "The generated SQL query appears to be incomplete or too complex. "
                "Please try rephrasing your question in a simpler way, or ask about a smaller time range. "
                f"Technical details: {str(e)}"
            )
            
            # Generate follow-up questions for SQL extraction failure
            logger.info("Generating follow-up questions for SQL extraction failure...")
            follow_up_questions = await ai_assistant.generate_follow_up_questions(
                user_question=request.question,
                sql_query="",
                result_data=[],
                execution_success=False,
                error_message=str(e)
            )
            
            return NL2SQLResponse(
                sql_query="",
                natural_language_answer=error_msg,
                execution_success=False,
                error_message=str(e),
                chart_specification=None,
                data=[],
                follow_up_questions=follow_up_questions
            )

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
        
        # Step 5: Generate AI-powered natural language explanation
        if execution_result["success"] and execution_result["data"]:
            logger.info("Generating AI explanation...")
            nl_explanation = await ai_assistant.explain_result(
                user_question=request.question,
                sql_query=sql_query,
                result_data=execution_result["data"]
            )
            
            # Step 6: Generate chart specification if applicable
            logger.info("Checking for chart generation...")
            chart_spec = await ai_assistant.generate_chart_spec(
                user_question=request.question,
                sql_query=sql_query,
                sql_result=execution_result["data"]
            )
            
            if chart_spec:
                logger.info(f"Chart generated: {chart_spec['chart_type']}")
            else:
                logger.info("No chart suitable for this data")
        else:
            # Fallback for failed queries or empty results
            nl_explanation = execution_result["summary"]
            chart_spec = None
        
        # Step 7: Generate follow-up questions
        logger.info("Generating follow-up questions...")
        follow_up_questions = await ai_assistant.generate_follow_up_questions(
            user_question=request.question,
            sql_query=sql_query,
            result_data=execution_result["data"] if execution_result["success"] else [],
            execution_success=execution_result["success"],
            error_message=execution_result.get("error")
        )
        
        if follow_up_questions:
            logger.info(f"Generated {len(follow_up_questions)} follow-up questions")
        else:
            logger.info("No follow-up questions generated")
        
        # Step 8: Save exchange to PostgreSQL memory
        memory_service.save_exchange(
            memory=memory,
            question=request.question,
            sql=sql_query
        )
        logger.info(f"Exchange saved to session {session_id}")

        # Step 9: Prepare response with AI-generated content
        if execution_result["success"]:
            return NL2SQLResponse(
                sql_query=sql_query,
                natural_language_answer=nl_explanation,  # AI-generated explanation!
                execution_success=True,
                error_message=None,
                chart_specification=chart_spec,  # Chart data if available
                data=execution_result["data"],  # Include query results
                follow_up_questions=follow_up_questions  # Include follow-up questions
            )
        else:
            return NL2SQLResponse(
                sql_query=sql_query,
                natural_language_answer=f"Query generated but execution failed: {execution_result['error']}",
                execution_success=False,
                error_message=execution_result["error"],
                chart_specification=None,
                data=[],
                follow_up_questions=follow_up_questions  # Include follow-up questions even for failed queries
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

@router.get("/status")
async def get_status():
    """Check the status of SQL generation (service mode or local fallback)"""
    import httpx
    
    model_service_available = False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{sql_generator.model_service_url}/health")
            model_service_available = response.status_code == 200
    except:
        model_service_available = False
    
    return {
        "model_service_url": sql_generator.model_service_url,
        "model_service_available": model_service_available,
        "current_mode": sql_generator.mode,
        "fallback_enabled": sql_generator.use_fallback,
        "recommendation": "Start model service for 70% GPU memory savings!" if not model_service_available else "Using model service - optimal memory usage!",
        "start_command": "./start_model_service.sh" if not model_service_available else None
    }

@router.get("/test")
async def test_nl2sql():
    """Test endpoint to verify NL2SQL service is working"""
    try:
        test_question = "Show me all users"
        sql_query = await sql_generator.generate_sql(test_question)
        return {
            "status": "success",
            "test_question": test_question,
            "generated_sql": sql_query,
            "message": "NL2SQL service is working",
            "mode": sql_generator.mode
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"NL2SQL service test failed: {str(e)}"
        }