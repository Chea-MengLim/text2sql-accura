import httpx
from dotenv import load_dotenv
from typing import Optional 
from utils.schema_info import schema_info
from utils.get_database_schema import get_database_schema, correct_sql_parentheses
from utils.extract_last_sql_query import extract_last_sql_query
import logging

logger = logging.getLogger(__name__)

class SQLGenerator:
    """
    SQL Generator with automatic fallback
    - First tries to use model service (memory efficient)
    - Falls back to local model if service not available (standalone mode)
    """

    def __init__(self, model_service_url: str = "http://localhost:8888", use_fallback: bool = True):
        load_dotenv()
        self.model_service_url = model_service_url
        self.use_fallback = use_fallback
        self.local_model = None
        self.mode = "service"  # "service" or "local"
        
        logger.info(f"SQLGenerator initialized with model service at {model_service_url}")
        if use_fallback:
            logger.info("Fallback to local model is ENABLED")
    
    def _load_local_model(self):
        """Load model locally (fallback mode)"""
        if self.local_model is None:
            logger.warning("⚠️  Model service not available - loading model LOCALLY (uses more GPU memory)")
            from transformers import pipeline
            self.local_model = pipeline(
                task="text2text-generation",
                model="Snowflake/Arctic-Text2SQL-R1-7B"
            )
            self.mode = "local"
            logger.info("✅ Local model loaded successfully")
    
    def _generate_sql_locally(self, question: str, conversation_context: str) -> str:
        """Generate SQL using local model"""
        context_section = ""
        if conversation_context.strip():
            context_section = f"\n{conversation_context}\n"
        
        prompt = f"""### Task
Generate a PostgreSQL query to answer the following question.
{context_section}
### Current Question
{question}

### Database Schema
{schema_info}

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
        
        response = self.local_model(
            prompt, 
            max_new_tokens=1500,
            do_sample=False, 
            num_beams=1,
            early_stopping=True
        )
        
        return response[0]["generated_text"]
    
    async def generate_sql(self, question: str, conversation_context: str = "") -> str:
        """
        Convert natural language question to SQL query
        - Tries model service first (memory efficient)
        - Falls back to local model if service unavailable
        
        Args:
            question: Current user question
            conversation_context: Formatted history from previous exchanges
        
        Returns:
            Generated SQL query
        """
        
        print("my schema is:", schema_info)
        
        # Try model service first
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.model_service_url}/generate-sql",
                    json={
                        "question": question,
                        "conversation_context": conversation_context,
                        "schema_info": schema_info
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"Model service error: {response.text}")
                
                result = response.json()
                sql_query = result["generated_sql"]
                
                if self.mode != "service":
                    logger.info("✅ Model service is back online - switching to service mode")
                    self.mode = "service"
                
                print(f"Query from model service:", sql_query)
                
                # Apply post-processing
                correct_sql = correct_sql_parentheses(sql_query)
                return correct_sql
                
        except httpx.ConnectError:
            # Model service not available - try fallback
            if self.use_fallback:
                logger.warning(f"⚠️  Cannot connect to model service at {self.model_service_url}")
                logger.warning("⚠️  FALLBACK MODE: Loading model locally (uses more GPU memory)")
                
                # Load local model if not already loaded
                self._load_local_model()
                
                # Generate SQL locally
                sql_query = self._generate_sql_locally(question, conversation_context)
                print(f"Query from LOCAL model:", sql_query)
                
                # Apply post-processing
                correct_sql = correct_sql_parentheses(sql_query)
                return correct_sql
            else:
                error_msg = (
                    f"Cannot connect to model service at {self.model_service_url}. "
                    "Please ensure the model service is running: ./start_model_service.sh"
                )
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"SQL generation failed: {str(e)}")
            raise     