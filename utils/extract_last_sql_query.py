import re
def extract_last_sql_query(response):
    # Extract the generated text from the model response
    generated_text = response[0]['generated_text']
    
    # Use regular expression to find all SQL queries in the text
    sql_queries = re.findall(r'```sql\n(.*?)\n```', generated_text, re.DOTALL)

    # Return the last SQL query if any found, otherwise return a message
    if sql_queries:
        return sql_queries[-1].strip()
    else:
        return "No SQL query found in the response."