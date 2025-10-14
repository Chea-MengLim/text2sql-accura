from transformers import pipeline
from dotenv import load_dotenv
from typing import Optional 
from utils.schema_info import schema_info
from utils.get_database_schema import get_database_schema, correct_sql_parentheses
from utils.extract_last_sql_query import extract_last_sql_query

class SQLGenerator:

    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        
        # Load your working model (same as your think2sql.py)
        self.model = pipeline(
            task="text2text-generation",
            model="Snowflake/Arctic-Text2SQL-R1-7B"
        )
    
    def generate_sql(self, question: str) -> str:
        
        # schema_info = get_database_schema()
        print("my scheme is : ", schema_info)
        
        """Convert natural language question to SQL query"""
        # prompt = f"Convert this to SQL: {question}"
#         prompt = f"""
# Convert this to Postgresql:
# User Question: {question}
# Database Schema: {schema_info}
# """

        prompt = f"""
Convert the following SQL query to PostgreSQL syntax:
User Question: {question}
Database Schema: {schema_info}

Please ensure compatibility with PostgreSQL, especially considering differences in functions, date formatting, and syntax conventions. For example:
- Replace SQLite-specific functions like strftime with PostgreSQL equivalents like TO_CHAR for date manipulation.
- Ensure that PostgreSQL data types are correctly referenced.
- Adjust any function or syntax differences specific to PostgreSQL.
"""
        prompt = f"""### Task
        Generate a PostgreSQL query to answer the following question.

        ### Database Schema
        {schema_info}

        ### Question
        {question}

        ### Instructions
        - Write ONLY the SQL query, nothing else
        - Use correct PostgreSQL syntax
        - Include necessary WHERE clauses for filtering
        - Use proper aggregation functions (COUNT, SUM, AVG, etc.) when needed
        - Format dates using TO_CHAR() for PostgreSQL
        - Table and column names are case-sensitive - match the schema exactly

        ### SQL Query
        """


        response = self.model(
            prompt, 
            max_new_tokens=600, 
            do_sample=False, 
            num_beams=4,
            early_stopping=True
        )
        
        # Extract the generated text (remove the prompt)
        # generated_text = response[0]['generated_text']
        # sql_query = generated_text.replace(prompt, "").strip()
        print("Query Before handle all : ", response)
        print("after calling", response[0]["generated_text"])
        
        
        # sql_query = extract_last_sql_query(response)
        sql_query = response[0]["generated_text"]
        correct_sql = correct_sql_parentheses(sql_query)
        print("schema info is : ", schema_info)
        print("len : ", len(schema_info))
        
        return correct_sql
        