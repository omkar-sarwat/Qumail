"""
Quick check to see what the KME status endpoints return
"""
import asyncio
import aiohttp

async def check_status():
    async with aiohttp.ClientSession() as session:
        # Check KME1
        print("Checking KME1...")
        async with session.get("https://qumail-kme1-xujk.onrender.com/api/v1/kme/status") as resp:
            print(f"Status: {resp.status}")
            text = await resp.text()
            print(f"Response: {text}\n")
        
        # Check KME2
        print("Checking KME2...")
        async with session.get("https://qumail-kme2-c341.onrender.com/api/v1/kme/status") as resp:
            print(f"Status: {resp.status}")
            text = await resp.text()
            print(f"Response: {text}\n")

asyncio.run(check_status())
