#!/usr/bin/env python3
"""
Test script to verify the model service is working correctly
Run this AFTER starting the model service
"""

import httpx
import asyncio
import json
from utils.schema_info import schema_info


async def test_model_service():
    """Test the model service endpoint"""
    
    print("🧪 Testing Model Service...\n")
    
    model_service_url = "http://localhost:8888"
    
    # Test 1: Health check
    print("1. Testing health check...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{model_service_url}/health")
            if response.status_code == 200:
                print(f"   ✅ Health check passed: {response.json()}\n")
            else:
                print(f"   ❌ Health check failed: {response.status_code}\n")
                return
    except httpx.ConnectError:
        print(f"   ❌ Cannot connect to model service at {model_service_url}")
        print("   Please start the model service first: ./start_model_service.sh\n")
        return
    
    # Test 2: SQL generation
    print("2. Testing SQL generation...")
    test_question = "Show me total sales by customer in 2024"
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{model_service_url}/generate-sql",
                json={
                    "question": test_question,
                    "conversation_context": "",
                    "schema_info": schema_info[:500]  # Use partial schema for quick test
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ SQL generation successful!")
                print(f"   Question: {test_question}")
                print(f"   Generated SQL (first 200 chars):")
                print(f"   {result['generated_sql'][:200]}...\n")
            else:
                print(f"   ❌ SQL generation failed: {response.status_code}")
                print(f"   Error: {response.text}\n")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}\n")
    
    print("✨ Test complete!")


if __name__ == "__main__":
    asyncio.run(test_model_service())

