#!/usr/bin/env python3
"""
Test script for the enhanced bilingual NL2SQL endpoint
Demonstrates the new explainable natural language answers and conversation memory
"""

import requests
import json

# API endpoint
BASE_URL = "http://localhost:9099"  # Based on the image showing port 9099
BILINGUAL_ENDPOINT = f"{BASE_URL}/api/nl2sql/query/bilingual"

def test_enhanced_bilingual_endpoint():
    """Test the enhanced bilingual endpoint with explainable answers and memory"""
    
    print("🌐 Testing Enhanced Bilingual NL2SQL Endpoint")
    print("=" * 60)
    print("Features: Explainable answers + Conversation memory")
    print("=" * 60)
    
    # Test cases with session tracking for memory
    test_cases = [
        {
            "name": "Korean Query with Memory",
            "data": {
                "question": "2023년 매출 데이터를 보여주세요",
                "session_id": "test_bilingual_session"
            }
        },
        {
            "name": "English Query with Memory", 
            "data": {
                "question": "Show me sales data for 2023",
                "session_id": "test_bilingual_session"
            }
        },
        {
            "name": "Follow-up Korean Query (using memory)",
            "data": {
                "question": "월별로 그룹화해서 보여주세요",
                "session_id": "test_bilingual_session"
            }
        },
        {
            "name": "English Follow-up (using memory)",
            "data": {
                "question": "Show me the top 5 months",
                "session_id": "test_bilingual_session"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['name']}")
        print("-" * 40)
        
        try:
            # Make request to enhanced bilingual endpoint
            response = requests.post(
                BILINGUAL_ENDPOINT,
                json=test_case["data"],
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Success!")
                print(f"🔍 SQL Query: {result.get('sql_query', 'N/A')}")
                print(f"💬 Natural Language Answer: {result.get('natural_language_answer', 'N/A')}")
                print(f"📈 Chart Spec: {result.get('chart_specification', {}).get('chart_type', 'None')}")
                print(f"📋 Data Rows: {len(result.get('data', []))}")
                print(f"🎯 Execution Success: {result.get('execution_success', False)}")
                
                # Check if it's a translated response
                if "[Translated from Korean]" in result.get('natural_language_answer', ''):
                    print("🌐 Translation detected in response")
                
                # Check if it has explainable content (not just basic summary)
                answer = result.get('natural_language_answer', '')
                if len(answer) > 50 and any(word in answer.lower() for word in ['explanation', 'shows', 'data', 'results', 'insights']):
                    print("🤖 AI-generated explainable answer detected")
                
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Enhanced bilingual endpoint testing completed!")
    
    # Test memory functionality
    print("\n🧠 Testing Conversation Memory")
    print("-" * 30)
    
    try:
        # Check conversation count
        memory_url = f"{BASE_URL}/api/nl2sql/conversation/test_bilingual_session/count"
        response = requests.get(memory_url)
        
        if response.status_code == 200:
            memory_data = response.json()
            print(f"✅ Memory working: {memory_data.get('message_count', 0)} messages stored")
            print(f"📊 Exchange count: {memory_data.get('exchange_count', 0)}")
        else:
            print(f"⚠️  Memory check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Memory test failed: {e}")

def show_usage_examples():
    """Show usage examples for the enhanced endpoint"""
    
    print("\n📚 Usage Examples for Enhanced Bilingual Endpoint")
    print("=" * 60)
    
    examples = [
        {
            "title": "Korean Query with Explainable Answer",
            "curl": '''curl -X POST "http://localhost:9099/api/nl2sql/query/bilingual" \\
  -H "Content-Type: application/json" \\
  -d '{"question": "2023년 매출 데이터를 보여주세요", "session_id": "my_session"}' '''
        },
        {
            "title": "English Query with Memory",
            "curl": '''curl -X POST "http://localhost:9099/api/nl2sql/query/bilingual" \\
  -H "Content-Type: application/json" \\
  -d '{"question": "Show me monthly sales trends", "session_id": "my_session"}' '''
        },
        {
            "title": "Follow-up Query (uses conversation memory)",
            "curl": '''curl -X POST "http://localhost:9099/api/nl2sql/query/bilingual" \\
  -H "Content-Type: application/json" \\
  -d '{"question": "상위 5개월을 보여주세요", "session_id": "my_session"}' '''
        }
    ]
    
    for example in examples:
        print(f"\n{example['title']}:")
        print(example['curl'])
    
    print("\n🎯 Expected Response Features:")
    print("✅ AI-generated explainable natural_language_answer")
    print("✅ [Translated from Korean] prefix for Korean queries")
    print("✅ Chart specification for visualizable data")
    print("✅ Conversation memory for context-aware responses")
    print("✅ Detailed SQL query with PostgreSQL optimization")

if __name__ == "__main__":
    print("🚀 Starting Enhanced Bilingual NL2SQL Endpoint Tests")
    print("Make sure the API server is running on http://localhost:9099")
    print()
    
    # Test the enhanced functionality
    test_enhanced_bilingual_endpoint()
    
    # Show usage examples
    show_usage_examples()
    
    print("\n🎉 The enhanced bilingual endpoint now provides:")
    print("   • Explainable natural language answers (like /query)")
    print("   • Conversation memory and context awareness")
    print("   • AI-powered explanations of query results")
    print("   • Automatic chart generation")
    print("   • Korean translation with tracking")
    print("   • Comprehensive error handling")
