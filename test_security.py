"""
Test script to verify SQL security validation
Tests that only SELECT queries are allowed
"""

from service.query_executor import QueryExecutor
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Create test database session
DATABASE_URL = os.getenv("MY_POSTGRESQL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

executor = QueryExecutor(db)

# Test cases
test_cases = [
    # ALLOWED queries
    {
        "query": "SELECT * FROM selr_daly_sumr LIMIT 10",
        "should_pass": True,
        "description": "Simple SELECT query"
    },
    {
        "query": "WITH cte AS (SELECT * FROM selr_daly_sumr) SELECT * FROM cte LIMIT 5",
        "should_pass": True,
        "description": "SELECT with CTE (WITH clause)"
    },
    {
        "query": """
        SELECT use_intt_id, SUM(sale_amt) 
        FROM selr_daly_sumr 
        WHERE trsc_dt >= '20240101' 
        GROUP BY use_intt_id
        """,
        "should_pass": True,
        "description": "Complex SELECT with GROUP BY"
    },
    
    # FORBIDDEN queries
    {
        "query": "DELETE FROM selr_daly_sumr WHERE use_intt_id = 'TEST'",
        "should_pass": False,
        "description": "DELETE query (should be blocked)"
    },
    {
        "query": "UPDATE selr_daly_sumr SET sale_amt = 0 WHERE use_intt_id = 'TEST'",
        "should_pass": False,
        "description": "UPDATE query (should be blocked)"
    },
    {
        "query": "INSERT INTO selr_daly_sumr (use_intt_id) VALUES ('TEST')",
        "should_pass": False,
        "description": "INSERT query (should be blocked)"
    },
    {
        "query": "DROP TABLE selr_daly_sumr",
        "should_pass": False,
        "description": "DROP TABLE (should be blocked)"
    },
    {
        "query": "CREATE TABLE test_table (id INT)",
        "should_pass": False,
        "description": "CREATE TABLE (should be blocked)"
    },
    {
        "query": "ALTER TABLE selr_daly_sumr ADD COLUMN test VARCHAR(10)",
        "should_pass": False,
        "description": "ALTER TABLE (should be blocked)"
    },
    {
        "query": "TRUNCATE TABLE selr_daly_sumr",
        "should_pass": False,
        "description": "TRUNCATE (should be blocked)"
    },
    {
        "query": "SELECT * FROM selr_daly_sumr; DROP TABLE selr_daly_sumr;",
        "should_pass": False,
        "description": "Multiple statements (SQL injection attempt)"
    },
    {
        "query": "SELECT * FROM selr_daly_sumr; -- comment\nDELETE FROM selr_daly_sumr",
        "should_pass": False,
        "description": "Hidden DELETE with comment"
    },
]

print("=" * 80)
print("SQL SECURITY VALIDATION TEST")
print("=" * 80)
print()

passed = 0
failed = 0

for i, test in enumerate(test_cases, 1):
    query = test["query"]
    should_pass = test["should_pass"]
    description = test["description"]
    
    # Test validation (not execution)
    is_valid, error_msg = executor._is_read_only_query(query)
    
    # Check if result matches expectation
    test_passed = (is_valid == should_pass)
    
    if test_passed:
        status = "✅ PASS"
        passed += 1
    else:
        status = "❌ FAIL"
        failed += 1
    
    print(f"Test {i}: {status}")
    print(f"  Description: {description}")
    print(f"  Expected: {'ALLOW' if should_pass else 'BLOCK'}")
    print(f"  Result: {'ALLOWED' if is_valid else 'BLOCKED'}")
    if error_msg:
        print(f"  Error: {error_msg}")
    print(f"  Query: {query[:80]}...")
    print()

print("=" * 80)
print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
print("=" * 80)

# Close database connection
db.close()

if failed > 0:
    exit(1)
else:
    print("\n✅ All security tests passed! Only SELECT queries are allowed.")
    exit(0)

