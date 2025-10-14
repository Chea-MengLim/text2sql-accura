"""
Model Service - Single instance that loads Snowflake model once
Run this service on a dedicated port (e.g., 8888)
All other application instances will call this service via HTTP
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline
from dotenv import load_dotenv
from typing import Optional
import logging
import uvicorn
import torch

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="SQL Model Service", version="1.0.0")

# Load model ONCE when service starts
logger.info("Loading Snowflake Arctic-Text2SQL-R1-7B model...")
sql_model = pipeline(
    task="text2text-generation",
    model="Snowflake/Arctic-Text2SQL-R1-7B",
    device="cuda",
    model_kwargs={
        "low_cpu_mem_usage": True
    }
)
logger.info("Model loaded successfully!")


class SQLGenerationRequest(BaseModel):
    question: str
    conversation_context: str = ""
    schema_info: str


class SQLGenerationResponse(BaseModel):
    generated_sql: str


@app.post("/generate-sql", response_model=SQLGenerationResponse)
async def generate_sql(request: SQLGenerationRequest):
    """Generate SQL from natural language using the shared model"""
    try:
        # Include conversation context if available
        context_section = ""
        if request.conversation_context.strip():
            context_section = f"\n{request.conversation_context}\n"
        
        prompt = f"""### Task
Generate a PostgreSQL query to answer the following question.
{context_section}
### Current Question
{request.question}

### Database Schema
{request.schema_info}

### Instructions
- Write ONLY the SQL query, nothing else
- Do NOT include any explanations, descriptions, or markdown
- Do NOT number steps or explain your approach
- Start directly with SELECT or WITH (for CTEs)
- Use correct PostgreSQL syntax

### SECURITY RULES (CRITICAL):
- ONLY generate SELECT queries (data retrieval)
- NEVER generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or any data-modifying statements
- If the user asks to modify, delete, or insert data, respond with: "Data modification is not supported. Only data retrieval is allowed."
- Only read data, never write or modify

### Query Guidelines:
- If the current question refers to previous questions (e.g., "what about...", "how about...", "same but..."), use the conversation context above
- The most recent exchange in the context is most relevant
- Focus primarily on the CURRENT question, use context only for clarification
- Include necessary WHERE clauses for filtering
- Use proper aggregation functions (COUNT, SUM, AVG, etc.) when needed
- For date/year extraction, use PostgreSQL functions like SUBSTRING(column, 1, 4) or LEFT(column, 4) for YYYYMMDD format
- AVOID long CASE statements with many WHEN clauses - use simpler approaches
- Table and column names are case-sensitive - match the schema exactly
- Limit the number of rows to 100

### Date Handling Best Practices:
- For YYYYMMDD text columns: Use SUBSTRING(trsc_dt, 1, 4) to extract year
- For grouping by year: GROUP BY SUBSTRING(trsc_dt, 1, 4)
- For grouping by month: GROUP BY SUBSTRING(trsc_dt, 1, 6)
- Keep queries simple and efficient

### SQL Query
"""

        response = sql_model(
            prompt, 
            max_new_tokens=1500, 
            do_sample=False, 
            num_beams=1,
            early_stopping=True
        )
        
        generated_sql = response[0]["generated_text"]
        
        logger.info(f"Generated SQL for question: {request.question[:50]}...")
        
        return SQLGenerationResponse(generated_sql=generated_sql)
        
    except Exception as e:
        logger.error(f"SQL generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate SQL: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model": "Snowflake/Arctic-Text2SQL-R1-7B",
        "service": "SQL Model Service"
    }


if __name__ == "__main__":
    # Run the model service on port 8888
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8888,
        log_level="info"
    )

