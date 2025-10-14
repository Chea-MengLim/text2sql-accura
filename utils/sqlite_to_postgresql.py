import re

def convert_sqlite_to_postgresql(sql: str) -> str:
    """
    Converts common SQLite date/time functions to PostgreSQL equivalents.
    
    Args:
        sql: SQL query string (potentially with SQLite syntax)
    
    Returns:
        SQL query with PostgreSQL syntax
    """
    if not sql:
        return sql
    
    # Convert DATE('now', 'start of year') to DATE_TRUNC('year', CURRENT_DATE)
    sql = re.sub(
        r"DATE\s*\(\s*['\"]now['\"]\s*,\s*['\"]start of year['\"]\s*\)",
        "DATE_TRUNC('year', CURRENT_DATE)",
        sql,
        flags=re.IGNORECASE
    )
    
    # Convert DATE('now', 'start of month') to DATE_TRUNC('month', CURRENT_DATE)
    sql = re.sub(
        r"DATE\s*\(\s*['\"]now['\"]\s*,\s*['\"]start of month['\"]\s*\)",
        "DATE_TRUNC('month', CURRENT_DATE)",
        sql,
        flags=re.IGNORECASE
    )
    
    # NEW: Convert DATE('now', 'start of month', '+N month') to DATE_TRUNC('month', CURRENT_DATE) + INTERVAL 'N month'
    def replace_month_start_plus(match):
        num = match.group(1)
        return f"DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '{num} month'"
    
    sql = re.sub(
        r"DATE\s*\(\s*['\"]now['\"]\s*,\s*['\"]start of month['\"]\s*,\s*['\"]\+(\d+)\s*months?['\"]\s*\)",
        replace_month_start_plus,
        sql,
        flags=re.IGNORECASE
    )
    
    # NEW: Convert DATE('now', 'start of year', '+N year') to DATE_TRUNC('year', CURRENT_DATE) + INTERVAL 'N year'
    def replace_year_start_plus(match):
        num = match.group(1)
        return f"DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '{num} year'"
    
    sql = re.sub(
        r"DATE\s*\(\s*['\"]now['\"]\s*,\s*['\"]start of year['\"]\s*,\s*['\"]\+(\d+)\s*years?['\"]\s*\)",
        replace_year_start_plus,
        sql,
        flags=re.IGNORECASE
    )
    
    # Convert DATE('now', 'start of week') to DATE_TRUNC('week', CURRENT_DATE)
    sql = re.sub(
        r"DATE\s*\(\s*['\"]now['\"]\s*,\s*['\"]start of week['\"]\s*\)",
        "DATE_TRUNC('week', CURRENT_DATE)",
        sql,
        flags=re.IGNORECASE
    )
    
    # Convert DATE('now', 'start of day') to DATE_TRUNC('day', CURRENT_DATE)
    sql = re.sub(
        r"DATE\s*\(\s*['\"]now['\"]\s*,\s*['\"]start of day['\"]\s*\)",
        "DATE_TRUNC('day', CURRENT_DATE)",
        sql,
        flags=re.IGNORECASE
    )
    
    # Convert DATE('now', '-N year', 'start of year') to DATE_TRUNC('year', CURRENT_DATE - INTERVAL 'N year')
    def replace_past_year_start(match):
        num = match.group(1)
        return f"DATE_TRUNC('year', CURRENT_DATE - INTERVAL '{num} year')"
    
    sql = re.sub(
        r"DATE\s*\(\s*['\"]now['\"]\s*,\s*['\"]-([\d]+)\s*year['\"]\s*,\s*['\"]start of year['\"]\s*\)",
        replace_past_year_start,
        sql,
        flags=re.IGNORECASE
    )
    
    # Convert DATE('now', '-N month', 'start of month') to DATE_TRUNC('month', CURRENT_DATE - INTERVAL 'N month')
    def replace_past_month_start(match):
        num = match.group(1)
        return f"DATE_TRUNC('month', CURRENT_DATE - INTERVAL '{num} month')"
    
    sql = re.sub(
        r"DATE\s*\(\s*['\"]now['\"]\s*,\s*['\"]-([\d]+)\s*month['\"]\s*,\s*['\"]start of month['\"]\s*\)",
        replace_past_month_start,
        sql,
        flags=re.IGNORECASE
    )
    
    # Convert DATE('now', '-N days') to CURRENT_DATE - INTERVAL 'N days'
    def replace_days_ago(match):
        num = match.group(1)
        return f"CURRENT_DATE - INTERVAL '{num} days'"
    
    sql = re.sub(
        r"DATE\s*\(\s*['\"]now['\"]\s*,\s*['\"]-([\d]+)\s*days?['\"]\s*\)",
        replace_days_ago,
        sql,
        flags=re.IGNORECASE
    )
    
    # Convert DATE('now', '-N months') to CURRENT_DATE - INTERVAL 'N months'
    def replace_months_ago(match):
        num = match.group(1)
        return f"CURRENT_DATE - INTERVAL '{num} months'"
    
    sql = re.sub(
        r"DATE\s*\(\s*['\"]now['\"]\s*,\s*['\"]-([\d]+)\s*months?['\"]\s*\)",
        replace_months_ago,
        sql,
        flags=re.IGNORECASE
    )
    
    # Convert DATE('now', '-N years') to CURRENT_DATE - INTERVAL 'N years'
    def replace_years_ago(match):
        num = match.group(1)
        return f"CURRENT_DATE - INTERVAL '{num} years'"
    
    sql = re.sub(
        r"DATE\s*\(\s*['\"]now['\"]\s*,\s*['\"]-([\d]+)\s*years?['\"]\s*\)",
        replace_years_ago,
        sql,
        flags=re.IGNORECASE
    )
    
    # Convert simple DATE('now') to CURRENT_DATE
    sql = re.sub(
        r"DATE\s*\(\s*['\"]now['\"]\s*\)",
        "CURRENT_DATE",
        sql,
        flags=re.IGNORECASE
    )
    
    # Convert DATETIME('now') to NOW()
    sql = re.sub(
        r"DATETIME\s*\(\s*['\"]now['\"]\s*\)",
        "NOW()",
        sql,
        flags=re.IGNORECASE
    )
    
    # === STRFTIME CONVERSIONS (specific patterns first, then general) ===
    
    # NEW: Convert strftime('%Y-%m-%d', 'now') to TO_CHAR(CURRENT_DATE, 'YYYY-MM-DD')
    sql = re.sub(
        r"strftime\s*\(\s*['\"]%Y-%m-%d['\"]\s*,\s*['\"]now['\"]\s*\)",
        "TO_CHAR(CURRENT_DATE, 'YYYY-MM-DD')",
        sql,
        flags=re.IGNORECASE
    )
    
    # NEW: Convert strftime('%Y-%m', 'now') to TO_CHAR(CURRENT_DATE, 'YYYY-MM')
    sql = re.sub(
        r"strftime\s*\(\s*['\"]%Y-%m['\"]\s*,\s*['\"]now['\"]\s*\)",
        "TO_CHAR(CURRENT_DATE, 'YYYY-MM')",
        sql,
        flags=re.IGNORECASE
    )
    
    # NEW: Convert strftime('%Y%m', 'now') to TO_CHAR(CURRENT_DATE, 'YYYYMM')
    sql = re.sub(
        r"strftime\s*\(\s*['\"]%Y%m['\"]\s*,\s*['\"]now['\"]\s*\)",
        "TO_CHAR(CURRENT_DATE, 'YYYYMM')",
        sql,
        flags=re.IGNORECASE
    )
    
    # NEW: Convert strftime('%Y', 'now') to EXTRACT(YEAR FROM CURRENT_DATE)::TEXT
    sql = re.sub(
        r"strftime\s*\(\s*['\"]%Y['\"]\s*,\s*['\"]now['\"]\s*\)",
        "EXTRACT(YEAR FROM CURRENT_DATE)::TEXT",
        sql,
        flags=re.IGNORECASE
    )
    
    # NEW: Convert strftime('%m', 'now') to EXTRACT(MONTH FROM CURRENT_DATE)::TEXT
    sql = re.sub(
        r"strftime\s*\(\s*['\"]%m['\"]\s*,\s*['\"]now['\"]\s*\)",
        "EXTRACT(MONTH FROM CURRENT_DATE)::TEXT",
        sql,
        flags=re.IGNORECASE
    )
    
    # Convert strftime('%Y-%m-%d', column) to TO_CHAR(column, 'YYYY-MM-DD')
    sql = re.sub(
        r"strftime\s*\(\s*['\"]%Y-%m-%d['\"]\s*,\s*([\w.]+)\s*\)",
        r"TO_CHAR(\1, 'YYYY-MM-DD')",
        sql,
        flags=re.IGNORECASE
    )
    
    # NEW: Convert strftime('%Y-%m', column) to TO_CHAR(column, 'YYYY-MM')
    sql = re.sub(
        r"strftime\s*\(\s*['\"]%Y-%m['\"]\s*,\s*([\w.]+)\s*\)",
        r"TO_CHAR(\1, 'YYYY-MM')",
        sql,
        flags=re.IGNORECASE
    )
    
    # NEW: Convert strftime('%Y%m', column) to TO_CHAR(column, 'YYYYMM')
    sql = re.sub(
        r"strftime\s*\(\s*['\"]%Y%m['\"]\s*,\s*([\w.]+)\s*\)",
        r"TO_CHAR(\1, 'YYYYMM')",
        sql,
        flags=re.IGNORECASE
    )
    
    # Convert strftime('%Y', column) to EXTRACT(YEAR FROM column)
    sql = re.sub(
        r"strftime\s*\(\s*['\"]%Y['\"]\s*,\s*([\w.]+)\s*\)",
        r"EXTRACT(YEAR FROM \1)",
        sql,
        flags=re.IGNORECASE
    )
    
    # Convert strftime('%m', column) to EXTRACT(MONTH FROM column)
    sql = re.sub(
        r"strftime\s*\(\s*['\"]%m['\"]\s*,\s*([\w.]+)\s*\)",
        r"EXTRACT(MONTH FROM \1)",
        sql,
        flags=re.IGNORECASE
    )
    
    # NEW: Convert strftime('%d', column) to EXTRACT(DAY FROM column)
    sql = re.sub(
        r"strftime\s*\(\s*['\"]%d['\"]\s*,\s*([\w.]+)\s*\)",
        r"EXTRACT(DAY FROM \1)",
        sql,
        flags=re.IGNORECASE
    )
    
    # NEW: Convert strftime('%H', column) to EXTRACT(HOUR FROM column)
    sql = re.sub(
        r"strftime\s*\(\s*['\"]%H['\"]\s*,\s*([\w.]+)\s*\)",
        r"EXTRACT(HOUR FROM \1)",
        sql,
        flags=re.IGNORECASE
    )
    
    # NEW: Convert strftime('%M', column) to EXTRACT(MINUTE FROM column)
    sql = re.sub(
        r"strftime\s*\(\s*['\"]%M['\"]\s*,\s*([\w.]+)\s*\)",
        r"EXTRACT(MINUTE FROM \1)",
        sql,
        flags=re.IGNORECASE
    )
    
    # NEW: Convert strftime('%S', column) to EXTRACT(SECOND FROM column)
    sql = re.sub(
        r"strftime\s*\(\s*['\"]%S['\"]\s*,\s*([\w.]+)\s*\)",
        r"EXTRACT(SECOND FROM \1)",
        sql,
        flags=re.IGNORECASE
    )
    
    # NEW: strftime('%w', col) -> day of week (0-6) -> EXTRACT(DOW FROM col)
    sql = re.sub(
        r"strftime\s*\(\s*['\"]%w['\"]\s*,\s*([\w.]+)\s*\)",
        r"EXTRACT(DOW FROM \1)",
        sql,
        flags=re.IGNORECASE
    )
    
    # NEW: strftime('%j', col) -> day of year (001-366) -> EXTRACT(DOY FROM col)
    sql = re.sub(
        r"strftime\s*\(\s*['\"]%j['\"]\s*,\s*([\w.]+)\s*\)",
        r"EXTRACT(DOY FROM \1)",
        sql,
        flags=re.IGNORECASE
    )
    
    # NEW: strftime('%W', col) -> week number -> EXTRACT(WEEK FROM col)
    sql = re.sub(
        r"strftime\s*\(\s*['\"]%W['\"]\s*,\s*([\w.]+)\s*\)",
        r"EXTRACT(WEEK FROM \1)",
        sql,
        flags=re.IGNORECASE
    )
    
    # Convert IFNULL(expr1, expr2) to COALESCE(expr1, expr2)
    sql = re.sub(
        r'\bIFNULL\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)',
        r'COALESCE(\1, \2)',
        sql,
        flags=re.IGNORECASE
    )
    
    # Convert ISNULL(expr1, expr2) to COALESCE(expr1, expr2) (SQL Server style)
    sql = re.sub(
        r'\bISNULL\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)',
        r'COALESCE(\1, \2)',
        sql,
        flags=re.IGNORECASE
    )
    
    # Convert LENGTH() to LENGTH() (PostgreSQL uses LENGTH, not LEN)
    # This is already compatible, but let's ensure consistency
    sql = re.sub(
        r'\bLEN\s*\(\s*([^)]+)\s*\)',
        r'LENGTH(\1)',
        sql,
        flags=re.IGNORECASE
    )
    
    return sql

def fix_complex_date_expressions(sql: str) -> str:
    """
    Fixes complex SQLite DATE expressions that weren't caught by basic patterns.
    Handles patterns like: DATE('now', 'start of month', '+1 month', '-1 day')
    """
    if not sql:
        return sql
    
    # Pattern: DATE('now', 'start of month', '+N month', '-N day')
    # Example: DATE('now', 'start of month', '+1 month', '-1 day') -> End of current month
    def replace_end_of_month_offset(match):
        month_offset = int(match.group(1)) if match.group(1) else 0
        day_offset = int(match.group(2)) if match.group(2) else 0
        
        if month_offset == 1 and day_offset == 1:
            # End of current month: start of next month - 1 day
            return "(DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month' - INTERVAL '1 day')"
        else:
            # Generic version

            return f"(DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '{month_offset} month' - INTERVAL '{day_offset} day')"
    
    sql = re.sub(
        r"DATE\s*\(\s*['\"]now['\"]\s*,\s*['\"]start of month['\"]\s*,\s*['\"]\+(\d+)\s*months?['\"]\s*,\s*['\"]-([\d]+)\s*days?['\"]\s*\)",
        replace_end_of_month_offset,
        sql,
        flags=re.IGNORECASE
    )
    
    # Pattern: Only convert DATE(...) if it contains SQLite-specific keywords
    # This is safer than converting ALL DATE() calls
    # Only convert if it has 'now', '+', or '-' which are SQLite-specific
    sql = re.sub(
        r"DATE\s*\(\s*['\"]now['\"][^)]*\)",
        "CURRENT_DATE",
        sql,
        flags=re.IGNORECASE
    )
    
    return sql

def fix_date_trunc_string_literals(sql: str) -> str:
    """
    Fixes DATE_TRUNC calls where the second parameter is a string literal.
    PostgreSQL's DATE_TRUNC requires the second parameter to be a DATE/TIMESTAMP, not a string.
    
    Example:
        DATE_TRUNC('month', '2023-01-01')
        becomes:
        DATE_TRUNC('month', '2023-01-01'::DATE)
    """
    if not sql:
        return sql
    
    # Pattern: DATE_TRUNC('unit', 'date-string')
    # Match string literals in the second parameter position
    def replace_date_trunc(match):
        unit = match.group(1)  # 'year', 'month', 'day', etc.
        date_str = match.group(2)  # The date string
        
        # Add ::DATE cast to the date string
        return f"DATE_TRUNC('{unit}', '{date_str}'::DATE)"
    
    # Pattern matches: DATE_TRUNC('unit', 'YYYY-MM-DD' or 'YYYYMMDD')
    sql = re.sub(
        r"DATE_TRUNC\s*\(\s*['\"](\w+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)",
        replace_date_trunc,
        sql,
        flags=re.IGNORECASE
    )
    
    return sql

def fix_date_functions_on_text_columns(sql: str) -> str:
    """
    Fixes date functions being applied to text columns that contain date values.
    Adds TO_DATE() conversion for text columns in YYYYMM or YYYYMMDD format.
    """
    if not sql:
        return sql
    
    # Common text date column patterns (specific to our schema only)
    text_date_columns = [
        'sumr_ym', 'trsc_ym',  # YYYYMM format columns
        'sumr_dt', 'trsc_dt'   # YYYYMMDD format columns
    ]
    
    for col in text_date_columns:
        # Pattern: TO_CHAR(text_column, format)
        # Replace with: TO_CHAR(TO_DATE(text_column, 'YYYYMM'), format)
        # Detect if it's YYYYMM or YYYYMMDD based on column suffix
        
        # For *_ym columns (year-month), use YYYYMM format
        if col.endswith('_ym'):
            sql = re.sub(
                rf'\bTO_CHAR\s*\(\s*({col})\s*,\s*([^)]+)\)',
                rf"TO_CHAR(TO_DATE(\1, 'YYYYMM'), \2)",
                sql,
                flags=re.IGNORECASE
            )
            
            # Pattern: EXTRACT(part FROM text_column)
            # Replace with: EXTRACT(part FROM TO_DATE(text_column, 'YYYYMM'))
            sql = re.sub(
                rf'\bEXTRACT\s*\(\s*(\w+)\s+FROM\s+({col})\s*\)',
                rf"EXTRACT(\1 FROM TO_DATE(\2, 'YYYYMM'))",
                sql,
                flags=re.IGNORECASE
            )
        
        # For *_dt columns (date), use YYYYMMDD format
        elif col.endswith('_dt'):
            sql = re.sub(
                rf'\bTO_CHAR\s*\(\s*({col})\s*,\s*([^)]+)\)',
                rf"TO_CHAR(TO_DATE(\1, 'YYYYMMDD'), \2)",
                sql,
                flags=re.IGNORECASE
            )
            
            sql = re.sub(
                rf'\bEXTRACT\s*\(\s*(\w+)\s+FROM\s+({col})\s*\)',
                rf"EXTRACT(\1 FROM TO_DATE(\2, 'YYYYMMDD'))",
                sql,
                flags=re.IGNORECASE
            )
    
    return sql

def add_date_type_casts(sql: str) -> str:
    """
    Adds type casts for date comparisons to handle text columns.
    Converts patterns like: trsc_dt >= DATE_TRUNC(...)
    To: trsc_dt::DATE >= DATE_TRUNC(...)::DATE
    
    NOTE: This function is now deprecated in favor of fix_text_date_column_comparisons()
    which properly handles text date columns with TO_DATE() conversion.
    Keeping this for backward compatibility but skipping text date columns.
    """
    if not sql:
        return sql
    
    # SKIP text date columns - they should be handled by fix_text_date_column_comparisons()
    # Only handle true date/timestamp columns if we have any
    date_columns = [
        # 'trsc_dt', 'sumr_dt'  # These are TEXT columns, not DATE columns!
        # Removed - our schema only has text date columns
    ]
    
    # For each date column, add ::DATE cast when comparing with date functions
    for col in date_columns:
        # Pattern: column >= DATE_TRUNC(...) or similar date functions
        sql = re.sub(
            rf'\b({col})\s*(>=|<=|>|<|=)\s*(DATE_TRUNC\([^)]+\)|CURRENT_DATE|NOW\(\))',
            rf'\1::DATE \2 \3::DATE',
            sql,
            flags=re.IGNORECASE
        )
        
        # Pattern: DATE_TRUNC(...) >= column
        sql = re.sub(
            rf'(DATE_TRUNC\([^)]+\)|CURRENT_DATE|NOW\(\))\s*(>=|<=|>|<|=)\s*\b({col})\b',
            rf'\1::DATE \2 \3::DATE',
            sql,
            flags=re.IGNORECASE
        )
    
    return sql

def handle_division_by_zero(sql: str) -> str:
    """
    Protects against division by zero errors in percentage calculations.
    Wraps denominators with NULLIF(denominator, 0) to return NULL instead of error.
    """
    if not sql:
        return sql
    
    # Pattern: (expression) / column_name
    # Replace with: (expression) / NULLIF(column_name, 0)
    # This catches percentage calculations like: (a - b) * 100.0 / b
    sql = re.sub(
        r'/\s*([a-zA-Z_][\w.]*)\s*(?=\s+AS\s+percentage|\s+AS\s+percent|\s+AS\s+pct|,|\)|\s*FROM)',
        r'/ NULLIF(\1, 0)',
        sql,
        flags=re.IGNORECASE
    )
    
    # Also handle more general division patterns
    # Pattern: * number / identifier (not already wrapped in NULLIF)
    sql = re.sub(
        r'\*\s*([\d.]+)\s*/\s+(?!NULLIF)([a-zA-Z_][\w.]*)',
        r'* \1 / NULLIF(\2, 0)',
        sql,
        flags=re.IGNORECASE
    )
    
    return sql

def fix_yyyymm_arithmetic(sql: str) -> str:
    """
    Fixes YYYYMM (text) column arithmetic by converting to proper date operations.
    Converts: trsc_ym + 1 or table.trsc_ym + 1
    To: TO_CHAR((TO_DATE(trsc_ym, 'YYYYMM') + INTERVAL '1 month'), 'YYYYMM')
    """
    if not sql:
        return sql
    
    # Common YYYYMM column patterns (specific to our schema only)
    yyyymm_columns = ['trsc_ym', 'sumr_ym']
    
    for col in yyyymm_columns:
        # Pattern: [alias.]column + N (add months)
        # Capture optional table alias
        def replace_add_months(match):
            alias = match.group(1) if match.group(1) else ''
            column = match.group(2)
            num = match.group(3)
            full_column = f"{alias}{column}"
            return f"TO_CHAR((TO_DATE({full_column}, 'YYYYMM') + INTERVAL '{num} month'), 'YYYYMM')"
        
        sql = re.sub(
            rf'\b([\w]+\.)?\b({col})\s*\+\s*(\d+)\b',
            replace_add_months,
            sql,
            flags=re.IGNORECASE
        )
        
        # Pattern: [alias.]column - N (subtract months)
        def replace_subtract_months(match):
            alias = match.group(1) if match.group(1) else ''
            column = match.group(2)
            num = match.group(3)
            full_column = f"{alias}{column}"
            return f"TO_CHAR((TO_DATE({full_column}, 'YYYYMM') - INTERVAL '{num} month'), 'YYYYMM')"
        
        sql = re.sub(
            rf'\b([\w]+\.)?\b({col})\s*-\s*(\d+)\b',
            replace_subtract_months,
            sql,
            flags=re.IGNORECASE
        )
    
    return sql

def cleanup_double_casts(sql: str) -> str:
    """
    Removes redundant double type casts like ::DATE::DATE.
    Converts: column::DATE::DATE to column::DATE
    """
    if not sql:
        return sql
    
    # Remove any double (or more) consecutive ::TYPE casts
    # Pattern: ::TYPE::TYPE (same type repeated)
    sql = re.sub(
        r'::DATE\s*::DATE',
        '::DATE',
        sql,
        flags=re.IGNORECASE
    )
    
    sql = re.sub(
        r'::TIMESTAMP\s*::TIMESTAMP',
        '::TIMESTAMP',
        sql,
        flags=re.IGNORECASE
    )
    
    sql = re.sub(
        r'::INTEGER\s*::INTEGER',
        '::INTEGER',
        sql,
        flags=re.IGNORECASE
    )
    
    return sql

def safe_to_date(column: str, format_str: str) -> str:
    """
    Creates a safe TO_DATE conversion that handles invalid/corrupted data.
    Uses CASE WHEN to validate format before conversion.
    
    Args:
        column: Column name
        format_str: Date format (YYYYMMDD or YYYYMM)
    
    Returns:
        Safe TO_DATE expression
    """
    if format_str == 'YYYYMMDD':
        # Validate: must be 8 digits
        return f"CASE WHEN {column} ~ '^[0-9]{{8}}$' THEN TO_DATE({column}, 'YYYYMMDD') ELSE NULL END"
    elif format_str == 'YYYYMM':
        # Validate: must be 6 digits
        return f"CASE WHEN {column} ~ '^[0-9]{{6}}$' THEN TO_DATE({column}, 'YYYYMM') ELSE NULL END"
    else:
        return f"TO_DATE({column}, '{format_str}')"

def fix_text_date_column_comparisons(sql: str) -> str:
    """
    Fixes type mismatches when text date columns are compared with date functions.
    Adds TO_DATE() conversion for text columns in BETWEEN, WHERE, and JOIN conditions.
    Now includes data validation to handle corrupted/invalid date strings.
    
    Example:
        trsc_dt BETWEEN DATE_TRUNC(...) AND CURRENT_DATE
        becomes:
        CASE WHEN trsc_dt ~ '^[0-9]{8}$' THEN TO_DATE(trsc_dt, 'YYYYMMDD') ELSE NULL END::DATE 
        BETWEEN DATE_TRUNC(...)::DATE AND CURRENT_DATE::DATE
    """
    if not sql:
        return sql
    
    # Text date columns mapping to their format (specific to our schema only)
    text_date_patterns = {
        'trsc_dt': 'YYYYMMDD',  # Transaction date (daily tables)
        'sumr_dt': 'YYYYMMDD',  # Summary date (daily tables)
        'trsc_ym': 'YYYYMM',    # Transaction year-month (monthly tables)
        'sumr_ym': 'YYYYMM',    # Summary year-month (monthly tables)
    }
    
    for column, format_str in text_date_patterns.items():
        # First, handle any existing ::DATE casts on the column itself (remove them so we can add TO_DATE properly)
        # Pattern: column::DATE (without TO_DATE wrapper) -> just column
        sql = re.sub(
            rf'\b({column})::DATE\b(?!\s*\()',  # Match column::DATE but not if followed by (
            rf'\1',
            sql,
            flags=re.IGNORECASE
        )
        
        # Pattern 1: column BETWEEN expression AND expression
        # Match any BETWEEN clause for our date columns and check if expressions are date-related
        # Use a simpler pattern that captures everything between BETWEEN and AND, then AND to end of clause
        
        def replace_between_for_column(sql_text):
            # Find all BETWEEN clauses for this column
            # Pattern: column BETWEEN <expr1> AND <expr2>
            # We need to handle nested parentheses properly
            pattern = rf'\b({column})\s+BETWEEN\s+(.+?)\s+AND\s+(.+?)(?=\s+(?:GROUP|ORDER|LIMIT|HAVING|WHERE|FROM|;|\))|\s*$)'
            
            def replace_match(match):
                col = match.group(1)
                start_expr = match.group(2).strip()
                end_expr = match.group(3).strip()
                
                # Only convert if expressions contain date functions/keywords or DATE() function
                combined_expr = start_expr + end_expr
                is_date_expr = (
                    any(keyword in combined_expr.upper() for keyword in ['DATE_TRUNC', 'CURRENT_DATE', 'NOW', 'INTERVAL', 'TIMESTAMP'])
                    or re.search(r'\bDATE\s*\(', combined_expr, re.IGNORECASE)  # Matches DATE(...)
                )
                
                if not is_date_expr:
                    return match.group(0)  # Don't convert non-date expressions
                
                # Convert column to date with validation
                col_converted = f"{safe_to_date(col, format_str)}::DATE"
                
                # Add ::DATE cast to expressions if they're date functions
                if any(keyword in start_expr.upper() for keyword in ['DATE_TRUNC', 'CURRENT_DATE', 'NOW', 'INTERVAL']):
                    # Handle nested parentheses by counting
                    if start_expr.startswith('(') and start_expr.count('(') == start_expr.count(')'):
                        start_expr = f"{start_expr}::DATE"
                    elif not start_expr.startswith('('):
                        start_expr = f"{start_expr}::DATE"
                
                if any(keyword in end_expr.upper() for keyword in ['DATE_TRUNC', 'CURRENT_DATE', 'NOW', 'INTERVAL']):
                    # Handle nested parentheses by counting
                    if end_expr.startswith('(') and end_expr.count('(') == end_expr.count(')'):
                        end_expr = f"{end_expr}::DATE"
                    elif not end_expr.startswith('('):
                        end_expr = f"{end_expr}::DATE"
                
                return f"{col_converted} BETWEEN {start_expr} AND {end_expr}"
            
            return re.sub(pattern, replace_match, sql_text, flags=re.IGNORECASE)
        
        sql = replace_between_for_column(sql)
        
        # Pattern 2: column comparison date_func (>=, <=, >, <, =, !=, <>)
        for operator in ['>=', '<=', '>', '<', '=', '!=', '<>']:
            # Column on left: trsc_dt >= DATE(...) or DATE_TRUNC(...) or CURRENT_DATE
            # More flexible pattern that handles parentheses better
            pattern_left = rf'\b({column})\s*({re.escape(operator)})\s*(DATE\([^)]+\)|DATE_TRUNC\([^)]+\)|CURRENT_DATE|NOW\(\)|\([^)]+(?:\([^)]*\))*[^)]*\))'
            
            def replace_left_comparison(match):
                col = match.group(1)
                op = match.group(2)
                expr = match.group(3).strip()
                
                # Only convert if expression contains date keywords or DATE() function
                is_date_function = (
                    any(keyword in expr.upper() for keyword in ['DATE_TRUNC', 'CURRENT_DATE', 'NOW', 'INTERVAL', 'TIMESTAMP'])
                    or re.search(r'\bDATE\s*\(', expr, re.IGNORECASE)  # Matches DATE(...)
                )
                
                if not is_date_function:
                    return match.group(0)  # Don't convert non-date expressions
                
                col_converted = f"{safe_to_date(col, format_str)}::DATE"
                
                if any(keyword in expr.upper() for keyword in ['DATE_TRUNC', 'CURRENT_DATE', 'NOW', 'INTERVAL']):
                    # Add ::DATE cast
                    if expr.startswith('(') and expr.endswith(')'):
                        expr = f"{expr}::DATE"
                    else:
                        expr = f"{expr}::DATE"
                
                return f"{col_converted} {op} {expr}"
            
            sql = re.sub(pattern_left, replace_left_comparison, sql, flags=re.IGNORECASE)
            
            # Column on right: DATE(...) >= trsc_dt or DATE_TRUNC(...) >= trsc_dt
            pattern_right = rf'(DATE\([^)]+\)|DATE_TRUNC\([^)]+\)|CURRENT_DATE|NOW\(\)|\([^)]+(?:\([^)]*\))*[^)]*\))\s*({re.escape(operator)})\s*\b({column})\b'
            
            def replace_right_comparison(match):
                expr = match.group(1).strip()
                op = match.group(2)
                col = match.group(3)
                
                # Only convert if expression contains date keywords or DATE() function
                is_date_function = (
                    any(keyword in expr.upper() for keyword in ['DATE_TRUNC', 'CURRENT_DATE', 'NOW', 'INTERVAL', 'TIMESTAMP'])
                    or re.search(r'\bDATE\s*\(', expr, re.IGNORECASE)  # Matches DATE(...)
                )
                
                if not is_date_function:
                    return match.group(0)  # Don't convert non-date expressions
                
                col_converted = f"{safe_to_date(col, format_str)}::DATE"
                
                if any(keyword in expr.upper() for keyword in ['DATE_TRUNC', 'CURRENT_DATE', 'NOW', 'INTERVAL']):
                    # Add ::DATE cast
                    if expr.startswith('(') and expr.endswith(')'):
                        expr = f"{expr}::DATE"
                    else:
                        expr = f"{expr}::DATE"
                
                return f"{expr} {op} {col_converted}"
            
            sql = re.sub(pattern_right, replace_right_comparison, sql, flags=re.IGNORECASE)
    
    return sql


def fix_extract_type_mismatches(sql: str) -> str:
    """
    Fixes type mismatches in EXTRACT comparisons.
    EXTRACT returns numeric, so ensure both sides of comparison are numeric.
    Removes inappropriate ::TEXT casts on EXTRACT results in comparisons.
    """
    if not sql:
        return sql
    
    # Pattern: EXTRACT(...) = EXTRACT(...)::TEXT
    # Remove the ::TEXT cast since both EXTRACTs return numeric
    sql = re.sub(
        r'\bEXTRACT\s*\([^)]+\)\s*(=|!=|<>|>=|<=|>|<)\s*EXTRACT\s*\([^)]+\)::TEXT\b',
        lambda m: m.group(0).replace('::TEXT', ''),
        sql,
        flags=re.IGNORECASE
    )
    
    # Pattern: EXTRACT(...)::TEXT = EXTRACT(...)
    # Remove the ::TEXT cast from the left side
    sql = re.sub(
        r'\bEXTRACT\s*\([^)]+\)::TEXT\s*(=|!=|<>|>=|<=|>|<)\s*EXTRACT\s*\([^)]+\)\b',
        lambda m: m.group(0).replace('::TEXT', ''),
        sql,
        flags=re.IGNORECASE
    )
    
    # Pattern: column = EXTRACT(...)::TEXT or EXTRACT(...)::TEXT = column
    # Remove ::TEXT from EXTRACT when comparing with numeric columns
    sql = re.sub(
        r'\bEXTRACT\s*\([^)]+\)::TEXT\b',
        lambda m: m.group(0).replace('::TEXT', ''),
        sql,
        flags=re.IGNORECASE
    )
    
    return sql