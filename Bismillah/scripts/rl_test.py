
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.utils.rate_limiter import rate_limiter

async def main():
    key = ("test", "123")
    allowed = 0
    for i in range(10):
        if await rate_limiter.allow(key):
            allowed += 1
            print(f"Request {i+1}: ✅ Allowed")
        else:
            print(f"Request {i+1}: ❌ Rate limited")
        await asyncio.sleep(0.1)
    print(f"Total allowed: {allowed}/10")

if __name__ == "__main__":
    asyncio.run(main())
