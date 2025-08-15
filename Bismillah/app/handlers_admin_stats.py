
import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from .lib.guards import admin_guard
from .safe_send import safe_reply
from .bot_stats import format_stats_message

logger = logging.getLogger(__name__)

@admin_guard
async def cmd_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin command to display bot statistics from Supabase
    Usage: /admin_stats
    """
    try:
        logger.info(f"Admin {update.effective_user.id} requested bot statistics")
        
        # Get formatted statistics message
        stats_message = format_stats_message()
        
        # Send the statistics
        await safe_reply(update, stats_message, parse_mode='Markdown')
        
        logger.info("Successfully sent bot statistics to admin")
        
    except Exception as e:
        logger.error(f"Error in cmd_admin_stats: {e}")
        await safe_reply(
            update, 
            f"❌ **Error fetching statistics**\n\n`{str(e)}`",
            parse_mode='Markdown'
        )

def register_admin_stats(application):
    """
    Register admin statistics handlers with the application
    """
    try:
        # Register the admin stats command
        application.add_handler(CommandHandler("admin_stats", cmd_admin_stats))
        
        logger.info("✅ Admin statistics handlers registered successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to register admin statistics handlers: {e}")
        raise e
