async def cmd_premium_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to show premium user count from Supabase"""
    try:
        from app.supabase_conn import sb_get_premium_count

        counts = sb_get_premium_count()

        await update.effective_message.reply_text(
            f"👑 **Premium Users Count** (Supabase)\n\n"
            f"🔓 **Lifetime**: {counts['lifetime']} users\n"
            f"⏰ **Timed**: {counts['timed']} users\n"
            f"📊 **Total**: {counts['total']} users\n\n"
            f"📡 **Source**: Supabase Database\n"
            f"✅ **Criteria**: is_premium=true, banned=false",
            parse_mode='Markdown'
        )

    except Exception as e:
        await update.effective_message.reply_text(
            f"❌ Error getting premium count: {str(e)}"
        )