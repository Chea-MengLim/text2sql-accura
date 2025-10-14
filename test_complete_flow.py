#!/usr/bin/env python3
"""
Test script to verify the complete Korean explanation flow
"""

import requests
import json

# API endpoint
BASE_URL = "http://localhost:9099"  # Based on the image showing port 9099
BILINGUAL_ENDPOINT = f"{BASE_URL}/api/nl2sql/query/bilingual"

def test_complete_korean_flow():
    """Test the complete Korean explanation flow"""
    
    print("🇰🇷 Testing Complete Korean Explanation Flow")
    print("=" * 60)
    print("Flow: Korean Input → English Processing → Korean Explanation")
    print("=" * 60)
    
    # Test with the same Korean query from the image
    korean_query = {
        "question": "2023년 판매 데이터를 보여주세요",
        "session_id": "korean_flow_test"
    }
    
    print(f"📝 Korean Query: {korean_query['question']}")
    print("-" * 40)
    
    try:
        response = requests.post(
            BILINGUAL_ENDPOINT,
            json=korean_query,
            headers={"Content-Type": "application/json"},
            timeout=60  # Longer timeout for translation
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            
            answer = result.get('natural_language_answer', 'N/A')
            print(f"💬 Response: {answer}")
            
            # Check if it's a proper Korean explanation
            korean_chars = any('\uac00' <= char <= '\ud7a3' for char in answer)
            if korean_chars:
                print("🇰🇷 ✅ Korean explanation detected!")
                print("🔄 ✅ Complete translation flow working!")
            else:
                print("⚠️  Still getting English explanation")
                print("🔍 Debugging info:")
                print(f"   - SQL Query: {result.get('sql_query', 'N/A')}")
                print(f"   - Execution Success: {result.get('execution_success', False)}")
                print(f"   - Data Rows: {len(result.get('data', []))}")
                
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_english_flow():
    """Test the English flow for comparison"""
    
    print("\n🇺🇸 Testing English Flow (for comparison)")
    print("=" * 60)
    
    english_query = {
        "question": "Show me 2023 sales data",
        "session_id": "english_flow_test"
    }
    
    print(f"📝 English Query: {english_query['question']}")
    print("-" * 40)
    
    try:
        response = requests.post(
            BILINGUAL_ENDPOINT,
            json=english_query,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            
            answer = result.get('natural_language_answer', 'N/A')
            print(f"💬 Response: {answer}")
            
            # Check if it's English (should not have Korean characters)
            korean_chars = any('\uac00' <= char <= '\ud7a3' for char in answer)
            if not korean_chars:
                print("🇺🇸 ✅ English explanation detected!")
            else:
                print("⚠️  Unexpected Korean in English response")
                
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ English flow test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Complete Flow Tests")
    print("Make sure the API server is running on http://localhost:9099")
    print("Make sure Ollama is running with Korean model: timHan/llama3korean8B4QKM")
    print()
    
    # Test Korean flow
    test_complete_korean_flow()
    
    # Test English flow for comparison
    test_english_flow()
    
    print("\n🎯 Expected Results:")
    print("✅ Korean input should return Korean explanation")
    print("✅ English input should return English explanation")
    print("✅ Both should have conversation memory and chart generation")
