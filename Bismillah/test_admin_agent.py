
#!/usr/bin/env python3
"""
Test Script untuk Admin Agent
"""

import json
from admin_agent import AdminAgent

def test_admin_agent():
    """Test semua fungsi admin agent"""
    
    print("🧪 Testing Admin Agent...")
    print("=" * 50)
    
    agent = AdminAgent()
    
    # 1. Test koneksi
    print("1️⃣ Test Koneksi:")
    status = agent.get_connection_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))
    
    if status["status"] != "success":
        print("❌ Koneksi gagal, test dihentikan.")
        return
    
    print("\n2️⃣ Test Commands:")
    
    # Test invalid command
    result = agent.execute_command("/invalid")
    print("Invalid command:", json.dumps(result, indent=2, ensure_ascii=False))
    
    # Test setpremium with invalid UUID
    result = agent.execute_command("/setpremium", "invalid-uuid", "month")
    print("Invalid UUID:", json.dumps(result, indent=2, ensure_ascii=False))
    
    # Test setpremium with invalid duration
    result = agent.execute_command("/setpremium", "550e8400-e29b-41d4-a716-446655440000", "invalid")
    print("Invalid duration:", json.dumps(result, indent=2, ensure_ascii=False))
    
    # Test with non-existent user
    result = agent.execute_command("/setpremium", "550e8400-e29b-41d4-a716-446655440000", "month")
    print("Non-existent user:", json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n✅ Test selesai!")

if __name__ == "__main__":
    test_admin_agent()
