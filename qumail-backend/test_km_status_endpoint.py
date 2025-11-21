"""
Test script to test the /api/v1/encryption/km-status endpoint
"""
import os
import sys
import asyncio
import json
import httpx
from pathlib import Path

# Make sure Python can find the app module
sys.path.append(str(Path(__file__).parent))

async def test_km_status_endpoint():
    """Test the KM status endpoint"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/v1/encryption/km-status", 
                json={}
            )
            
            if response.status_code == 200:
                print("KM status endpoint successful!")
                print(json.dumps(response.json(), indent=2))
                return True
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"Error accessing KM status endpoint: {e}")
            return False

if __name__ == "__main__":
    asyncio.run(test_km_status_endpoint())