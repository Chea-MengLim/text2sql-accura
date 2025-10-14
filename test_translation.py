#!/usr/bin/env python3
"""
Test script to verify the translation functions work correctly
"""

import asyncio
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.nl2sql import translate_ko_to_en, translate_en_to_ko, looks_korean

async def test_translation():
    """Test the translation functions"""
    
    print("🧪 Testing Translation Functions")
    print("=" * 50)
    
    # Test Korean detection
    korean_text = "2023년 판매 데이터를 보여주세요"
    english_text = "Show me 2023 sales data"
    
    print(f"Korean detection for '{korean_text}': {looks_korean(korean_text)}")
    print(f"Korean detection for '{english_text}': {looks_korean(english_text)}")
    print()
    
    # Test Korean to English translation
    print("Testing Korean to English translation...")
    try:
        korean_to_english = await translate_ko_to_en(korean_text)
        print(f"✅ Korean to English: '{korean_text}' -> '{korean_to_english}'")
    except Exception as e:
        print(f"❌ Korean to English translation failed: {e}")
    
    print()
    
    # Test English to Korean translation
    print("Testing English to Korean translation...")
    try:
        english_to_korean = await translate_en_to_ko("The query results show daily sales data for 2023, with a total of 365 records.")
        print(f"✅ English to Korean: 'The query results show daily sales data for 2023, with a total of 365 records.' -> '{english_to_korean}'")
    except Exception as e:
        print(f"❌ English to Korean translation failed: {e}")
    
    print()
    print("=" * 50)
    print("🏁 Translation test completed!")

if __name__ == "__main__":
    print("🚀 Starting Translation Function Tests")
    print("Make sure Ollama is running with Korean model: timHan/llama3korean8B4QKM")
    print()
    
    asyncio.run(test_translation())
