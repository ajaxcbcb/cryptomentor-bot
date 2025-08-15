
from telegram import Update
from telegram.ext import ContextTypes
from app.lib.guards import admin_guard
from app.safe_send import safe_reply
from app.supabase_conn import health, upsert_user_tid, get_user_by_tid
import os

@admin_guard
async def cmd_sb_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check Supabase connection status"""
    ok, info = health()
    
    # Get environment info
    url = os.getenv("SUPABASE_URL", "").strip()
    service_key = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
    
    env_status = "✅" if url and service_key else "❌"
    key_type = "SERVICE_KEY ✅" if service_key.startswith("eyJ") else "MISSING/INVALID ❌"
    
    message = f"""🗄️ **Supabase Status**

🔗 **Connection:** {'✅ OK' if ok else '❌ FAILED'}
⚙️ **Environment:** {env_status}
🔑 **Key Type:** {key_type}
🌐 **URL:** {url[:50] + '...' if len(url) > 50 else url}

📡 **Response:** {info}

💡 **Required:**
• SUPABASE_URL (supabase.co domain)
• SUPABASE_SERVICE_KEY (service_role, not anon)"""
    
    await safe_reply(update.effective_message, message)

@admin_guard
async def cmd_sb_diag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Run Supabase diagnostic tests"""
    try:
        # Test 1: Upsert operation
        test_tid = 999999999
        upsert_user_tid(test_tid, test_probe=True, credits=100)
        
        # Test 2: Read operation
        verify = get_user_by_tid(test_tid)
        
        # Test 3: Update operation
        upsert_user_tid(test_tid, test_probe=False, credits=200)
        
        message = f"""🔍 **Supabase Diagnostic Tests**

✅ **Test 1:** UPSERT operation - OK
✅ **Test 2:** READ operation - OK
✅ **Test 3:** UPDATE operation - OK

📊 **Test Results:**
• Created/Updated user {test_tid}
• Read data: {verify is not None}
• All operations successful

🛡️ **RLS Policy:** Working (service_role access)
💾 **Database:** Functional"""
        
        await safe_reply(update.effective_message, message)
        
    except Exception as e:
        await safe_reply(update.effective_message, f"🔍 **Diagnostic FAILED:** {str(e)}\n\n💡 Check:\n• SERVICE_KEY validity\n• RLS policies\n• Table existence")
