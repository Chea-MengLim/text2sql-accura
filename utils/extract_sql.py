
import re

def extract_sql(text: str) -> str:
    """
    Extracts the SQL query from model-generated text.
    Handles ```sql fences, <sql> tags, or plain inline SQL.

    Args:
        text: The full model output (string)

    Returns:
        A cleaned SQL query string, or "" if nothing valid found.
    
    Raises:
        ValueError: If the extracted SQL appears to be incomplete or invalid
    """
    if not text:
        return ""

    # Try common fenced formats first
    patterns = [
        r"```sql\s*(.*?)\s*```",   # ```sql ... ```
        r"<sql>\s*(.*?)\s*</sql>", # <sql> ... </sql>
        r"```(.*?)```",            # any ``` ... ``` fallback
    ]

    sql = ""
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
        if m:
            sql = m.group(1).strip()
            break
    
    # If no code block found, try to extract SQL starting from common keywords
    if not sql:
        # Look for SQL after "Here is the final SQL query:" or "### SQL Query"
        sql_marker_patterns = [
            r"Here\s+is\s+the\s+(?:final\s+)?SQL\s+query\s*[:\n]+\s*(.*)",
            r"###\s*SQL\s*Query\s*[:\n]+(.*)",
            r"SQL\s*Query\s*[:\n]+(.*)",
        ]
        for marker_pat in sql_marker_patterns:
            m = re.search(marker_pat, text, re.IGNORECASE | re.DOTALL)
            if m:
                sql = m.group(1).strip()
                # Remove any code fence markers if present
                sql = re.sub(r"```sql\s*", "", sql, flags=re.IGNORECASE)
                sql = re.sub(r"```\s*$", "", sql)
                break
    
    # Fallback: crude heuristic—find SQL starting with common keywords
    if not sql:
        sql = text.strip()
        # remove leading non-SQL chatter - look for SQL keywords
        match = re.search(r"(?is)\b(SELECT|INSERT|UPDATE|DELETE|CREATE|WITH)\b.*", sql)
        if match:
            sql = match.group(0)
    
    # Clean up: remove any remaining schema descriptions or instructions before the SQL
    # Look for the actual SQL query starting point
    sql_start_match = re.search(r"(?is)^.*?\b(WITH|SELECT|INSERT|UPDATE|DELETE|CREATE)\b", sql)
    if sql_start_match:
        # Find where the SQL keyword actually starts
        keyword_pos = sql_start_match.end() - len(sql_start_match.group(1))
        sql = sql[keyword_pos:]
    
    # Remove markdown backticks around identifiers (MySQL style)
    # Convert `table_name` to table_name
    sql = re.sub(r'`([^`]+)`', r'\1', sql)
    
    # Stop at common text markers that indicate end of SQL
    end_markers = [
        r'\n\n(?:Explanation|Note|This query|The query|To run)',
        r'\n\d+\.\s+\*\*',  # Numbered list with markdown
    ]
    for marker in end_markers:
        match = re.search(marker, sql, re.IGNORECASE)
        if match:
            sql = sql[:match.start()]
            break
    
    # Remove anything after the last complete SQL statement
    # Handle incomplete queries (like "SELECT;")
    if sql:
        # Find the last semicolon
        if ";" in sql:
            # Split by semicolon and take everything up to the last one
            parts = sql.split(";")
            # Check if the last part (after last ;) is empty or just whitespace
            if parts[-1].strip():
                # Last part has content, might be incomplete - check if it's just a comment or text
                last_part = parts[-1].strip()
                if not re.match(r'^--', last_part):  # Not a comment
                    # Might be incomplete SQL, keep it
                    sql = ";".join(parts)
                else:
                    sql = ";".join(parts[:-1]) + ";"
            else:
                sql = ";".join(parts[:-1]) + ";"
        
        # Check for obviously incomplete queries
        sql_upper = sql.upper().strip()
        if sql_upper.endswith(("SELECT;", "FROM;", "WHERE;", "GROUP BY;", "ORDER BY;", ",")):
            # Query is incomplete
            raise ValueError(
                "Incomplete SQL detected: Query appears to be cut off. "
                "The model output may have been truncated. Try increasing max_new_tokens."
            )
    
    # normalize whitespace but preserve newlines for readability
    sql = re.sub(r"[ \t]+", " ", sql).strip()
    sql = re.sub(r"\n\s*\n", "\n", sql)  # Remove multiple blank lines
    
    # ensure ending semicolon
    if sql and not sql.endswith(";"):
        sql += ";"

    # Validate for incomplete SQL patterns
    if sql:
        # Check for unterminated quoted strings (most common truncation error)
        # Count single quotes - should be even
        single_quote_count = sql.count("'")
        if single_quote_count % 2 != 0:
            raise ValueError(
                "Incomplete SQL detected: Unterminated quoted string. "
                "The query appears to be truncated. Try increasing max_new_tokens or simplifying the query."
            )
        
        # Check for incomplete CASE statements
        case_count = len(re.findall(r'\bCASE\b', sql, re.IGNORECASE))
        end_count = len(re.findall(r'\bEND\b', sql, re.IGNORECASE))
        if case_count > end_count:
            raise ValueError(
                f"Incomplete SQL detected: {case_count} CASE statement(s) but only {end_count} END statement(s). "
                "The query appears to be truncated. Try increasing max_new_tokens or simplifying the query."
            )
        
        # Check for incomplete JOIN/WHERE/comparison conditions
        incomplete_patterns = [
            (r'\bON\s+[\w.]+\s*=\s*;', "Incomplete JOIN condition (ON ... =;)"),
            (r'\bON\s+[\w.]+\s*=\s*$', "Incomplete JOIN condition (ON ... = at end)"),
            (r'\bWHERE\s*;', "Empty WHERE clause"),
            (r'\bAND\s*;', "Empty AND condition"),
            (r'\bOR\s*;', "Empty OR condition"),
            (r'\bJOIN\s+\w+\s*;', "JOIN without ON clause"),
            (r'\bJOIN\s+\w+\s+\w+\s*;', "JOIN with alias but no ON clause"),
            (r'=\s*,', "Incomplete comparison (= followed by comma)"),
            (r'=\s*(?:FROM|WHERE|GROUP|ORDER|HAVING|LIMIT)\b', "Incomplete comparison before keyword"),
            (r'GROUP\s+BY\s+[\w.,\s]+,\s*[a-z];\s*$', "Incomplete GROUP BY (ends with single letter)"),
            (r"'\d{1,7};", "Truncated date string (ends with incomplete value like '203;)"),
        ]
        
        for pattern, error_msg in incomplete_patterns:
            match = re.search(pattern, sql, re.IGNORECASE)
            if match:
                raise ValueError(
                    f"Incomplete SQL detected: {error_msg}. "
                    f"Found pattern '{match.group(0)}' in query. "
                    "The model may have been truncated. Try increasing max_new_tokens."
                )

    return sql
