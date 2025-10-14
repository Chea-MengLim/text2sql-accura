import psycopg2

DB_CONFIG = {
    'host': '203.255.78.58',
    'database': 'dataset',
    'user': 'postgres',
    'password': 'postgres123',
    'port': 9002
}

def get_database_schema():
    """Get database schema from PostgreSQL"""
    try:
        conn = get_database_connection()
        if not conn:
            return "Unable to connect to database"
        
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if not tables:
            schema_info = "Database Schema:\n\nNo tables found in the 'public' schema.\n"
            schema_info += "Your database is connected but appears to be empty.\n"
            schema_info += "You can create tables and start querying your data!"
        else:
            schema_info = "\n\n"
            
            for table in tables:
                table_name = table[0]
                schema_info += f"Table: {table_name}\n"
                
                # Get column information
                cursor.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public'
                    ORDER BY ordinal_position;
                """, (table_name,))
                
                columns = cursor.fetchall()
                for col in columns:
                    col_name, data_type = col
                    schema_info += f"- {col_name} ({data_type})\n"
                
                schema_info += "\n"
        
        conn.close()
        return schema_info
        
    except psycopg2.Error as e:
        return f"PostgreSQL error retrieving schema: {e}"
    except Exception as e:
        return f"Error retrieving schema: {e}"
    
    
def get_database_connection():
    """Get PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"Database connection failed: {e}")
        print("Please check if PostgreSQL is running and the connection details are correct.")
        return None
    except psycopg2.Error as e:
        print(f"PostgreSQL error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error connecting to database: {e}")
        return None
    

import re

def correct_sql_parentheses(query: str) -> str:
    # Count the number of opening and closing parentheses
    open_count = query.count('(')
    close_count = query.count(')')
    
    # If there are more closing parentheses, add the missing opening parenthesis
    if close_count > open_count:
        # Find the position where the closing parenthesis is placed incorrectly
        corrected_query = re.sub(r'\)\s*$', '(', query)
        corrected_query += '(' * (close_count - open_count)
        return corrected_query
    
    # If there are no issues with the parentheses, return the query as is
    return query

