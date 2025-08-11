async def cmd_premium_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to show premium user count from Supabase"""
    try:
        from app.supabase_conn import sb_get_premium_count

        counts = sb_get_premium_count()
        
        if "error" in counts:
            await update.effective_message.reply_text(
                f"❌ **Error getting premium count**\n\n"
                f"Error: {counts['error']}\n\n"
                f"Please check Supabase connection.",
                parse_mode='Markdown'
            )
            return

        await update.effective_message.reply_text(
            f"👑 **Premium Users Count** (Supabase)\n\n"
            f"🔓 **Lifetime**: {counts['lifetime']} users\n"
            f"⏰ **Active Timed**: {counts['timed']} users\n"
            f"📊 **Total Active**: {counts['total']} users\n\n"
            f"📡 **Source**: Supabase Database\n"
            f"✅ **Criteria**: is_premium=true, banned=false, not expired\n"
            f"🕐 **Last Updated**: Now",
            parse_mode='Markdown'
        )

    except Exception as e:
        await update.effective_message.reply_text(
            f"❌ **Error getting premium count**\n\n"
            f"Exception: {str(e)}\n\n"
            f"Please check logs for details.",
            parse_mode='Markdown'str(e)}"
        )