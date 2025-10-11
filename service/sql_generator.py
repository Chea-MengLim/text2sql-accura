# from transformers import pipeline
# from dotenv import load_dotenv
# from typing import Optional 
# from utils.schema_info import schema_info
# from utils.get_database_schema import get_database_schema, correct_sql_parentheses
# from utils.extract_last_sql_query import extract_last_sql_query

# class SQLGenerator:

#     def __init__(self):
#         # Load environment variables from .env file
#         load_dotenv()
        
#         # Load your working model (same as your think2sql.py)
#         self.model = pipeline(
#             task="text2text-generation",
#             model="Snowflake/Arctic-Text2SQL-R1-7B"
#         )
    
#     def generate_sql(self, question: str) -> str:
        
#         # schema_info = get_database_schema()
#         print("my scheme is : ", schema_info)
        
#         """Convert natural language question to SQL query"""
#         # prompt = f"Convert this to SQL: {question}"
# #         prompt = f"""
# # Convert this to Postgresql:
# # User Question: {question}
# # Database Schema: {schema_info}
# # """

# #         prompt = f"""
# # Convert the following SQL query to PostgreSQL syntax:
# # User Question: {question}
# # Database Schema: {schema_info}

# # Please ensure compatibility with PostgreSQL, especially considering differences in functions, date formatting, and syntax conventions. For example:
# # - Replace SQLite-specific functions like strftime with PostgreSQL equivalents like TO_CHAR for date manipulation.
# # - Ensure that PostgreSQL data types are correctly referenced.
# # - Adjust any function or syntax differences specific to PostgreSQL.
# # """
#         prompt = f"""### Task
#         Generate a PostgreSQL query to answer the following question.

#         ### Question
#         {question}
        
#         ### Database Schema
#         {schema_info}

#         ### Instructions
#         - Write ONLY the SQL query, nothing else
#         - Use correct PostgreSQL syntax
#         - Include necessary WHERE clauses for filtering
#         - Use proper aggregation functions (COUNT, SUM, AVG, etc.) when needed
#         - Format dates using TO_CHAR() for PostgreSQL
#         - Table and column names are case-sensitive - match the schema exactly
#         - Limit the number of rows to 50
#         ### SQL Query
#         """


#         response = self.model(
#             prompt, 
#             max_new_tokens=600, 
#             do_sample=False, 
#             num_beams=4,
#             early_stopping=True
#         )
        
#         # Extract the generated text (remove the prompt)
#         # generated_text = response[0]['generated_text']
#         # sql_query = generated_text.replace(prompt, "").strip()
#         print("Query Before handle all : ", response)
#         print("after calling", response[0]["generated_text"])
        
        
#         # sql_query = extract_last_sql_query(response)
#         sql_query = response[0]["generated_text"]
#         correct_sql = correct_sql_parentheses(sql_query)
#         print("schema info is : ", schema_info)
#         print("len : ", len(schema_info))
        
#         return correct_sql

from transformers import pipeline
from dotenv import load_dotenv
from typing import Optional 
from utils.schema_info import schema_info
from utils.get_database_schema import get_database_schema, correct_sql_parentheses
from utils.extract_last_sql_query import extract_last_sql_query

class SQLGenerator:

    def __init__(self):
        load_dotenv()
        self.model = pipeline(
            task="text2text-generation",
            model="Snowflake/Arctic-Text2SQL-R1-7B"
        )
    
    def generate_sql(self, question: str, conversation_context: str = "") -> str:
        """
        Convert natural language question to SQL query
        
        Args:
            question: Current user question
            conversation_context: Formatted history from previous exchanges
        
        Returns:
            Generated SQL query
        """
        
        print("my schema is:", schema_info)
        
        # Include conversation context if available
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
- Start directly with SELECT, WITH
- Use correct PostgreSQL syntax
- If the current question refers to previous questions (e.g., "what about...", "how about...", "same but..."), use the conversation context above
- The most recent exchange in the context is most relevant
- Focus primarily on the CURRENT question, use context only for clarification
- Include necessary WHERE clauses for filtering
- Use proper aggregation functions (COUNT, SUM, AVG, etc.) when needed
- Format dates using TO_CHAR() for PostgreSQL
- Table and column names are case-sensitive - match the schema exactly
- Limit the number of rows to 20

### SQL Query
"""

        response = self.model(
            prompt, 
            max_new_tokens=800,  # Increased to prevent truncation
            do_sample=False, 
            num_beams=4,
            early_stopping=True
        )
        
        print("Query Before handle all:", response)
        print("after calling", response[0]["generated_text"])
        
        sql_query = response[0]["generated_text"]
        correct_sql = correct_sql_parentheses(sql_query)
        print("schema info is:", schema_info)
        print("len:", len(schema_info))
        
        return correct_sql     