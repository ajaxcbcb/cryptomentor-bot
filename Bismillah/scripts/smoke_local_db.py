
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.local_db import *

async def run():
    print("🧪 Testing Local SQLite Database...")
    await init_db()
    print("✅ Database initialized")
    
    uid = "12345"
    await upsert_user(uid, "Test", "User", "tester")
    print("✅ User created")
    
    await set_premium_with_value(uid, "days", 7)
    p = await get_premium(uid)
    print("Premium:", p)
    
    await add_credits(uid, 50)
    print("✅ Added 50 credits")
    
    ok = await consume_credits(uid, 20)
    print("Consume 20:", ok)
    
    ok = await consume_credits(uid, 40)
    print("Consume 40 should fail:", ok)
    
    is_prem = await is_premium(uid)
    print("Is premium:", is_prem)
    
    credits = await get_user_credits(uid)
    print("Current credits:", credits)
    
    print("🎉 All tests passed!")

if __name__ == "__main__":
    asyncio.run(run())
