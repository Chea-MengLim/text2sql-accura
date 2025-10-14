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
    
    return sql

def fix_date_functions_on_text_columns(sql: str) -> str:
    """
    Fixes date functions being applied to text columns that contain date values.
    Adds TO_DATE() conversion for text columns in YYYYMM or YYYYMMDD format.
    """
    if not sql:
        return sql
    
    # Common text date column patterns
    text_date_columns = [
        'sumr_ym', 'trsc_ym', 'ym', 'year_month', 'month_year',
        'sumr_dt', 'trsc_dt', 'dt', 'date_text'
    ]
    
    for col in text_date_columns:
        # Pattern: TO_CHAR(text_column, format)
        # Replace with: TO_CHAR(TO_DATE(text_column, 'YYYYMM'), format)
        # Detect if it's YYYYMM (6 chars) or YYYYMMDD (8 chars) based on common patterns
        
        # For *_ym columns (year-month), use YYYYMM format
        if col.endswith('_ym') or col in ['ym', 'year_month', 'month_year']:
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
        elif col.endswith('_dt') or col in ['dt', 'date_text']:
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
    """
    if not sql:
        return sql
    
    # Common date column name patterns (add more as needed)
    date_columns = [
        'trsc_dt', 'transaction_dt', 'date', 'created_at', 'updated_at',
        'order_date', 'purchase_date', 'sale_date', 'dt', 'datetime'
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
    
    # Common YYYYMM column patterns
    yyyymm_columns = ['trsc_ym', 'ym', 'year_month', 'month_year']
    
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