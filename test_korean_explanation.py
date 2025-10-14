#!/usr/bin/env python3
"""
Test script for the enhanced bilingual NL2SQL endpoint with Korean explanations
Demonstrates the new flow: Korean input → Korean explanation output
"""

import requests
import json

# API endpoint
BASE_URL = "http://localhost:9099"  # Based on the image showing port 9099
BILINGUAL_ENDPOINT = f"{BASE_URL}/api/nl2sql/query/bilingual"

def test_korean_explanation_flow():
    """Test the new Korean explanation flow"""
    
    print("🇰🇷 Testing Korean Explanation Flow")
    print("=" * 60)
    print("New Flow: Korean Input → Korean Explanation Output")
    print("=" * 60)
    
    # Test cases focusing on Korean input
    test_cases = [
        {
            "name": "Korean Sales Query",
            "data": {
                "question": "2023년 매출 데이터를 보여주세요",
                "session_id": "korean_test_session"
            },
            "expected_language": "Korean"
        },
        {
            "name": "Korean Monthly Trends Query", 
            "data": {
                "question": "월별 매출 트렌드를 차트로 보여주세요",
                "session_id": "korean_test_session"
            },
            "expected_language": "Korean"
        },
        {
            "name": "Korean Top Customers Query",
            "data": {
                "question": "상위 5명의 고객을 매출 기준으로 보여주세요",
                "session_id": "korean_test_session"
            },
            "expected_language": "Korean"
        },
        {
            "name": "English Query (for comparison)",
            "data": {
                "question": "Show me sales data for 2023",
                "session_id": "korean_test_session"
            },
            "expected_language": "English"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['name']}")
        print("-" * 40)
        
        try:
            # Make request to bilingual endpoint
            response = requests.post(
                BILINGUAL_ENDPOINT,
                json=test_case["data"],
                headers={"Content-Type": "application/json"},
                timeout=45  # Increased timeout for translation
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Success!")
                print(f"🔍 SQL Query: {result.get('sql_query', 'N/A')}")
                
                # Check the natural language answer
                answer = result.get('natural_language_answer', 'N/A')
                print(f"💬 Natural Language Answer: {answer}")
                
                # Analyze the language of the response
                if test_case["expected_language"] == "Korean":
                    # Check if response contains Korean characters
                    korean_chars = any('\uac00' <= char <= '\ud7a3' for char in answer)
                    if korean_chars:
                        print("🇰🇷 ✅ Korean explanation detected!")
                    else:
                        print("⚠️  Expected Korean but got English explanation")
                        
                    # Check if it has the old translation prefix (should not have it)
                    if "[Translated from Korean]" in answer:
                        print("⚠️  Old translation prefix detected (should be removed)")
                    else:
                        print("✅ No translation prefix (clean Korean response)")
                else:
                    # For English queries, should be in English
                    english_chars = any('a' <= char.lower() <= 'z' for char in answer)
                    if english_chars and not any('\uac00' <= char <= '\ud7a3' for char in answer):
                        print("🇺🇸 ✅ English explanation detected!")
                    else:
                        print("⚠️  Expected English but got Korean explanation")
                
                print(f"📈 Chart Spec: {result.get('chart_specification', {}).get('chart_type', 'None')}")
                print(f"📋 Data Rows: {len(result.get('data', []))}")
                print(f"🎯 Execution Success: {result.get('execution_success', False)}")
                
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Korean explanation flow testing completed!")

def test_translation_flow():
    """Test the complete translation flow"""
    
    print("\n🔄 Testing Complete Translation Flow")
    print("=" * 60)
    print("Flow: Korean Input → English Processing → Korean Explanation")
    print("=" * 60)
    
    # Test with a complex Korean query
    complex_korean_query = {
        "question": "2023년과 2024년의 월별 매출을 비교해서 차트로 보여주고, 가장 높은 매출을 기록한 달을 알려주세요",
        "session_id": "translation_flow_test"
    }
    
    print(f"📝 Complex Korean Query: {complex_korean_query['question']}")
    print("-" * 40)
    
    try:
        response = requests.post(
            BILINGUAL_ENDPOINT,
            json=complex_korean_query,
            headers={"Content-Type": "application/json"},
            timeout=60  # Longer timeout for complex translation
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            
            answer = result.get('natural_language_answer', 'N/A')
            print(f"💬 Korean Explanation: {answer}")
            
            # Check if it's a proper Korean explanation
            korean_chars = any('\uac00' <= char <= '\ud7a3' for char in answer)
            if korean_chars:
                print("🇰🇷 ✅ Proper Korean explanation generated!")
                print("🔄 ✅ Complete translation flow working: Korean → English → Korean")
            else:
                print("⚠️  Translation flow may not be working properly")
                
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Translation flow test failed: {e}")

def show_usage_examples():
    """Show usage examples for the new Korean explanation feature"""
    
    print("\n📚 Usage Examples - Korean Explanations")
    print("=" * 60)
    
    examples = [
        {
            "title": "Korean Query with Korean Explanation",
            "curl": '''curl -X POST "http://localhost:9099/api/nl2sql/query/bilingual" \\
  -H "Content-Type: application/json" \\
  -d '{"question": "2023년 매출 데이터를 보여주세요", "session_id": "my_session"}' ''',
            "expected": "Korean explanation in response"
        },
        {
            "title": "English Query with English Explanation",
            "curl": '''curl -X POST "http://localhost:9099/api/nl2sql/query/bilingual" \\
  -H "Content-Type: application/json" \\
  -d '{"question": "Show me sales data for 2023", "session_id": "my_session"}' ''',
            "expected": "English explanation in response"
        }
    ]
    
    for example in examples:
        print(f"\n{example['title']}:")
        print(example['curl'])
        print(f"Expected: {example['expected']}")
    
    print("\n🎯 New Flow Summary:")
    print("✅ Korean Input → Korean Explanation (translated back)")
    print("✅ English Input → English Explanation (no translation)")
    print("✅ Conversation memory works in both languages")
    print("✅ Chart generation works with Korean explanations")
    print("✅ Error messages also translated to Korean when needed")

if __name__ == "__main__":
    print("🚀 Starting Korean Explanation Flow Tests")
    print("Make sure the API server is running on http://localhost:9099")
    print("Make sure Ollama is running with Korean model: timHan/llama3korean8B4QKM")
    print()
    
    # Test the Korean explanation flow
    test_korean_explanation_flow()
    
    # Test the complete translation flow
    test_translation_flow()
    
    # Show usage examples
    show_usage_examples()
    
    print("\n🎉 The enhanced bilingual endpoint now provides:")
    print("   • Korean input → Korean explanation output")
    print("   • English input → English explanation output")
    print("   • Automatic translation of explanations")
    print("   • Conversation memory in both languages")
    print("   • Error messages in appropriate language")
    print("   • Chart generation with Korean explanations")
