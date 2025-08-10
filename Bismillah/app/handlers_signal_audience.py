
#!/usr/bin/env python3
"""
Signal Audience Inspector - Admin command to check AutoSignal recipients
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.lib.guards import admin_guard
from app.safe_send import safe_reply

@admin_guard
async def cmd_signal_audience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to check current AutoSignal audience"""
    try:
        # Import here to avoid circular imports
        from snd_auto_signals import list_recipients
        from app.users_aggregate import aggregated_lifetime
        from app.lib.auth import _resolve_admin_ids
        
        # Get data
        recs = list_recipients()
        lif = aggregated_lifetime()
        admin_ids = []
        
        # Get admin IDs as integers
        for s in _resolve_admin_ids():
            try:
                admin_ids.append(int(s))
            except:
                pass
        
        # Build response
        lines = [
            "🛰️ **AutoSignal Audience**",
            "",
            f"👑 **Admins:** {admin_ids}",
            f"♾️ **Lifetime Users:** {len(lif)}",
            f"📧 **Total Recipients:** {len(recs)}",
            "",
            "📋 **Sample Recipients:**"
        ]
        
        # Show sample recipients
        sample = recs[:20] if len(recs) > 20 else recs
        for i, recipient_id in enumerate(sample, 1):
            user_type = "👑 Admin" if recipient_id in admin_ids else "♾️ Lifetime"
            lines.append(f"{i}. {recipient_id} ({user_type})")
        
        if len(recs) > 20:
            lines.append(f"... and {len(recs) - 20} more")
        
        lines.extend([
            "",
            "ℹ️ **Note:** Only users who have started private chat (/start) will receive signals."
        ])
        
        message = "\n".join(lines)
        await safe_reply(update.effective_message, message, parse_mode='Markdown')
        
    except Exception as e:
        await safe_reply(update.effective_message, f"❌ Error checking audience: {str(e)}")
