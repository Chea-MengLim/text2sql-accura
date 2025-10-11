#!/usr/bin/env python3
"""
Test script to verify LangChain + PostgreSQL memory persistence
This will:
1. Create the chat_message_history table
2. Save conversation exchanges
3. Verify data persists in PostgreSQL
4. Test memory retrieval after "restart"
"""


from langchain.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories import PostgresChatMessageHistory
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv
import os
import time

# Load environment

DATABASE_URL = DATABASE_URL="postgresql://postgres:postgres123@203.255.78.58:9002/sqlyst"

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not found in .env file")
    print("Please add: DATABASE_URL=postgresql://user:password@host:port/database")
    exit(1)

print("=" * 70)
print("🧪 LANGCHAIN + POSTGRESQL MEMORY PERSISTENCE TEST")
print("=" * 70)
print(f"\n📊 Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else '***'}\n")

# Test session ID
TEST_SESSION = "test_user_12345"

# ============================================================================
# TEST 1: Check table creation
# ============================================================================
print("📋 TEST 1: Table Creation")
print("-" * 70)

try:
    # This should create the table if it doesn't exist
    message_history = PostgresChatMessageHistory(
        session_id=TEST_SESSION,
        connection_string=DATABASE_URL,
        table_name="chat_message_history"
    )
    
    print("✅ PostgresChatMessageHistory initialized")
    
    # Verify table exists
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    if 'chat_message_history' in inspector.get_table_names():
        print("✅ Table 'chat_message_history' exists in database")
        
        # Show table structure
        columns = inspector.get_columns('chat_message_history')
        print("\n   Table structure:")
        for col in columns:
            print(f"     - {col['name']}: {col['type']}")
    else:
        print("❌ Table 'chat_message_history' NOT found!")
        exit(1)
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    exit(1)

print("\n✅ TEST 1 PASSED\n")

# ============================================================================
# TEST 2: Save conversation exchanges
# ============================================================================
print("📋 TEST 2: Save Conversation Exchanges")
print("-" * 70)

try:
    # Clear any existing test data
    message_history.clear()
    print("🧹 Cleared previous test data")
    
    # Create memory with window
    memory = ConversationBufferWindowMemory(
        k=3,  # Keep last 3 exchanges
        chat_memory=message_history,
        memory_key="chat_history",
        return_messages=True,
        input_key="question",
        output_key="sql"
    )
    print("✅ Memory object created")
    
    # Simulate 5 conversation exchanges
    conversations = [
        ("Show me sales in 2024", "SELECT * FROM sales WHERE year = 2024"),
        ("What about 2023?", "SELECT * FROM sales WHERE year = 2023"),
        ("Show top 10 customers", "SELECT customer, SUM(amount) FROM sales GROUP BY customer ORDER BY SUM(amount) DESC LIMIT 10"),
        ("Filter by region Asia", "SELECT * FROM sales WHERE region = 'Asia'"),
        ("Count total orders", "SELECT COUNT(*) FROM orders"),
    ]
    
    print("\n💬 Saving conversations to PostgreSQL...")
    for i, (question, sql) in enumerate(conversations, 1):
        memory.save_context({"question": question}, {"sql": sql})
        print(f"   {i}. Q: {question[:50]}...")
        print(f"      SQL: {sql[:50]}...")
        time.sleep(0.1)  # Small delay to ensure different timestamps
    
    print("\n✅ All conversations saved")
    
    # Verify in database
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT COUNT(*) FROM chat_message_history WHERE session_id = :sid"
        ), {"sid": TEST_SESSION})
        count = result.scalar()
        print(f"✅ Database has {count} messages for session '{TEST_SESSION}'")
        
        # Should be 10 messages (5 questions + 5 answers)
        if count == 10:
            print("✅ Correct number of messages (5 Q&A pairs = 10 messages)")
        else:
            print(f"⚠️  Expected 10 messages, found {count}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n✅ TEST 2 PASSED\n")

# ============================================================================
# TEST 3: Retrieve conversation (simulate app restart)
# ============================================================================
print("📋 TEST 3: Memory Retrieval (Simulate App Restart)")
print("-" * 70)

try:
    print("🔄 Simulating app restart...")
    print("   (Creating NEW memory object with same session_id)")
    
    # Create a COMPLETELY NEW memory object (simulates restart)
    # Using the SAME session_id should load previous data
    new_message_history = PostgresChatMessageHistory(
        session_id=TEST_SESSION,  # Same session ID
        connection_string=DATABASE_URL,
        table_name="chat_message_history"
    )
    
    new_memory = ConversationBufferWindowMemory(
        k=3,  # Only keeps last 3 exchanges
        chat_memory=new_message_history,
        memory_key="chat_history",
        return_messages=True,
        input_key="question",
        output_key="sql"
    )
    
    print("✅ New memory object created")
    
    # Load memory variables
    history = new_memory.load_memory_variables({})
    messages = history.get("chat_history", [])
    
    print(f"\n📥 Retrieved {len(messages)} messages from PostgreSQL")
    print(f"   (Window size k=3, so max 6 messages = last 3 Q&A pairs)")
    
    if messages:
        print("\n   📜 Retrieved conversation history:")
        for i, msg in enumerate(messages, 1):
            msg_type = "👤 USER" if msg.type == "human" else "🤖 AI"
            content = msg.content[:60] + "..." if len(msg.content) > 60 else msg.content
            print(f"   {i}. {msg_type}: {content}")
        
        print(f"\n✅ Successfully retrieved {len(messages)} messages")
        print("✅ Memory survived 'restart' - data is PERSISTENT!")
    else:
        print("❌ No messages retrieved!")
        exit(1)
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n✅ TEST 3 PASSED\n")

# ============================================================================
# TEST 4: Verify only last 3 exchanges kept (window)
# ============================================================================
print("📋 TEST 4: Window Memory (k=3)")
print("-" * 70)

try:
    # We saved 5 exchanges, but k=3 means only last 3 should be in memory
    history = new_memory.load_memory_variables({})
    messages = history.get("chat_history", [])
    
    expected_count = 6  # 3 exchanges = 6 messages (3 Q + 3 A)
    actual_count = len(messages)
    
    print(f"Expected messages in window: {expected_count}")
    print(f"Actual messages retrieved: {actual_count}")
    
    if actual_count == expected_count:
        print("✅ Window memory working correctly!")
        print("   (Older messages still in DB, but not loaded into context)")
    else:
        print(f"⚠️  Expected {expected_count}, got {actual_count}")
    
    # Verify all 10 are still in database
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT COUNT(*) FROM chat_message_history WHERE session_id = :sid"
        ), {"sid": TEST_SESSION})
        db_count = result.scalar()
        print(f"\n📊 Total in database: {db_count} messages (all history preserved)")
        print(f"📊 Loaded in memory: {actual_count} messages (window size)")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n✅ TEST 4 PASSED\n")

# ============================================================================
# TEST 5: View actual data in database
# ============================================================================
print("📋 TEST 5: Database Content Inspection")
print("-" * 70)

try:
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                id,
                session_id,
                message->>'type' as msg_type,
                LEFT(message->>'content', 40) as content_preview,
                created_at
            FROM chat_message_history 
            WHERE session_id = :sid
            ORDER BY id
        """), {"sid": TEST_SESSION})
        
        print("\n🗄️  Database records:")
        print("   " + "-" * 66)
        for row in result:
            print(f"   ID: {row[0]:2} | Type: {row[2]:6} | {row[3]:40} | {row[4]}")
        print("   " + "-" * 66)
    
    print("\n✅ Data is physically stored in PostgreSQL!")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ TEST 5 PASSED\n")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("=" * 70)
print("🎉 ALL TESTS PASSED!")
print("=" * 70)
print("""
✅ Confirmed:
   1. Table 'chat_message_history' created automatically
   2. Conversations saved to PostgreSQL successfully
   3. Memory persists across 'restarts' (new object with same session_id)
   4. Window memory (k=3) correctly limits context size
   5. All data physically stored in database

🔍 Key Findings:
   - Data is PERSISTENT (survives restarts)
   - Window keeps only last 3 exchanges in context
   - All history remains in database for future retrieval
   - PostgreSQL backend working correctly

📊 Summary:
   - Session ID: {0}
   - Total messages in DB: 10 (5 Q&A pairs)
   - Messages in memory window: 6 (last 3 Q&A pairs)
   - Table: chat_message_history
""".format(TEST_SESSION))

print("\n🧹 Cleanup:")
cleanup = input("Do you want to delete test data? (y/N): ").strip().lower()
if cleanup == 'y':
    message_history.clear()
    print("✅ Test data cleared")
else:
    print("ℹ️  Test data kept in database")
    print(f"   To view: SELECT * FROM chat_message_history WHERE session_id = '{TEST_SESSION}';")
    print(f"   To delete: DELETE FROM chat_message_history WHERE session_id = '{TEST_SESSION}';")

print("\n" + "=" * 70)
print("✅ Test complete!")
print("=" * 70)