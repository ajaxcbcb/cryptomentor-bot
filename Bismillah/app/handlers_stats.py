# This file contains the core logic for the bot, including user management,
# signal processing, and communication with external services like Telegram and Supabase.

import logging
import os
import time
from datetime import datetime, timedelta

import pytz
from dotenv import load_dotenv

from app.config import Config
from app.exceptions import (
    SignalProcessingError,
    TelegramError,
    SupabaseError,
    DataProcessingError,
)
from app.signals import SignalProcessor
from app.supabase_conn import SB_TABLES, sb_client, sb_list_users, sb_update_user_data
from app.users_aggregate import (
    get_eligible_recipients_for_autosignal,
    get_lifetime_user_count,
    get_users_to_notify,
)
from app.utils import (
    calculate_time_difference,
    format_signal_data,
    get_last_signal_timestamp,
    save_last_signal_timestamp,
)
from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Load environment variables from .env file
load_dotenv()

# Initialize logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Constants ---
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
SIGNAL_PROCESSING_INTERVAL = 30 * 60  # 30 minutes in seconds
# Local backup file for signals (removed as per instructions)
# LOCAL_BACKUP_FILE = "backup_signals.json"
# AutoSignal configuration
AUTOSIGNAL_RECIPIENTS = "admin_and_lifetime_users"
AUTOSIGNAL_INTERVAL = 30 * 60  # 30 minutes in seconds
AUTOSIGNAL_MIN_CONFIDENCE = 75

# --- Bot Handlers ---


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! Welcome to the Signal Bot.",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message when the /help command is issued."""
    help_text = """
    Here are the available commands:
    /start - Welcome message
    /help - Show this help message
    /stats - Display database and bot statistics
    /broadcast <message> - Send a message to all users (admin only)
    /resend_signals - Resend the last 5 signals to all premium users
    /set_interval <seconds> - Set the AutoSignal interval (admin only)
    /set_confidence <percentage> - Set the AutoSignal minimum confidence (admin only)
    /set_recipient <type> - Set AutoSignal recipients (admin only, options: all, premium, lifetime)
    """
    await update.message.reply_text(help_text)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays statistics about the database and the bot."""
    try:
        # Get user statistics from Supabase only
        try:
            from app.supabase_conn import sb_list_users
            from app.users_aggregate import get_eligible_recipients_for_autosignal, get_lifetime_user_count

            all_users = sb_list_users({}, columns="telegram_id,is_premium,banned,premium_until")
            total_users = len(all_users)
            premium_users = len([u for u in all_users if u.get('is_premium') and not u.get('banned')])
            lifetime_users = get_lifetime_user_count()
            banned_users = len([u for u in all_users if u.get('banned')])
            eligible_for_autosignal = len(get_eligible_recipients_for_autosignal())

        except Exception as e:
            logger.error(f"Error getting Supabase stats: {e}")
            total_users = "Error"
            premium_users = "Error"
            lifetime_users = "Error"
            banned_users = "Error"
            eligible_for_autosignal = "Error"

        # Get bot statistics
        last_signal_time = get_last_signal_timestamp()
        time_since_last_signal = "N/A"
        if last_signal_time:
            time_since_last_signal = calculate_time_difference(
                datetime.now(pytz.timezone(Config.TIMEZONE)), last_signal_time
            )

        # Format the statistics message
        stats_message = (
            f"📊 **Database Statistics (Supabase Only):**\n"
            f"• **Total Users**: {total_users}\n"
            f"• **Premium Users**: {premium_users}\n"
            f"• **Lifetime Users**: {lifetime_users} \n"
            f"• **Banned Users**: {banned_users}\n"
            f"• **AutoSignal Eligible**: {eligible_for_autosignal}\n"
            f"\n"
            f"🛰️ **AutoSignal Config:**\n"
            f"• **Source**: Supabase only (no local backup)\n"
            f"• **Recipients**: Admin + Lifetime premium\n"
            f"• **Interval**: 30 minutes\n"
            f"• **Min Confidence**: 75%\n"
            f"\n"
            f"🤖 **Bot Statistics:**\n"
            f"• **Time Since Last Signal**: {time_since_last_signal}\n"
        )

        await update.message.reply_text(stats_message, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Error in /stats command: {e}")
        await update.message.reply_text("An error occurred while fetching statistics.")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message to all users (admin only)."""
    user_id = update.effective_user.id
    if user_id != int(os.environ.get("ADMIN_USER_ID")):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Please provide a message to broadcast.")
        return

    message = " ".join(context.args)
    try:
        users = sb_list_users(columns="telegram_id")
        success_count = 0
        fail_count = 0
        for user in users:
            try:
                await context.bot.send_message(chat_id=user["telegram_id"], text=message)
                success_count += 1
                time.sleep(0.1)  # Small delay to avoid rate limiting
            except Exception as e:
                logger.error(
                    f"Failed to send broadcast to {user['telegram_id']}: {e}"
                )
                fail_count += 1

        await update.message.reply_text(
            f"Broadcast sent. Success: {success_count}, Failed: {fail_count}"
        )
    except SupabaseError as e:
        logger.error(f"Supabase error in /broadcast: {e}")
        await update.message.reply_text("Error fetching users from Supabase.")
    except TelegramError as e:
        logger.error(f"Telegram error in /broadcast: {e}")
        await update.message.reply_text("Error sending broadcast message.")
    except Exception as e:
        logger.error(f"Unexpected error in /broadcast: {e}")
        await update.message.reply_text("An unexpected error occurred.")


async def resend_signals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Resends the last 5 signals to all premium users."""
    user_id = update.effective_user.id
    if user_id != int(os.environ.get("ADMIN_USER_ID")):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    try:
        # Fetch last 5 signals (adjust query as needed)
        signals = sb_client.table(SB_TABLES.SIGNALS).select("*").limit(5).execute()
        if signals.data:
            formatted_signals = [format_signal_data(s) for s in signals.data]
            message = "\n".join(formatted_signals)

            # Get premium users
            premium_users = sb_list_users(columns="telegram_id,is_premium")
            premium_users = [
                u["telegram_id"]
                for u in premium_users
                if u.get("is_premium") and not u.get("banned")
            ]

            success_count = 0
            fail_count = 0
            for user_id in premium_users:
                try:
                    await context.bot.send_message(
                        chat_id=user_id, text=message, parse_mode=ParseMode.MARKDOWN
                    )
                    success_count += 1
                    time.sleep(0.1)
                except Exception as e:
                    logger.error(f"Failed to resend signals to {user_id}: {e}")
                    fail_count += 1

            await update.message.reply_text(
                f"Last 5 signals resent to premium users. Success: {success_count}, Failed: {fail_count}"
            )
        else:
            await update.message.reply_text("No signals found to resend.")

    except SupabaseError as e:
        logger.error(f"Supabase error in /resend_signals: {e}")
        await update.message.reply_text("Error fetching signals or users from Supabase.")
    except Exception as e:
        logger.error(f"Unexpected error in /resend_signals: {e}")
        await update.message.reply_text("An unexpected error occurred.")


async def set_interval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets the AutoSignal interval (admin only)."""
    user_id = update.effective_user.id
    if user_id != int(os.environ.get("ADMIN_USER_ID")):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Please provide the interval in seconds.")
        return

    try:
        new_interval = int(context.args[0])
        if new_interval <= 0:
            await update.message.reply_text("Interval must be a positive number.")
            return

        # Update the global interval variable (or a more persistent storage)
        global SIGNAL_PROCESSING_INTERVAL
        SIGNAL_PROCESSING_INTERVAL = new_interval
        # Ideally, this should be saved to a configuration file or database
        await update.message.reply_text(f"AutoSignal interval set to {new_interval} seconds.")
        logger.info(f"AutoSignal interval updated to {new_interval} seconds by admin.")

    except ValueError:
        await update.message.reply_text("Invalid interval. Please enter a number.")
    except Exception as e:
        logger.error(f"Error setting interval: {e}")
        await update.message.reply_text("An error occurred while setting the interval.")


async def set_confidence(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets the AutoSignal minimum confidence (admin only)."""
    user_id = update.effective_user.id
    if user_id != int(os.environ.get("ADMIN_USER_ID")):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Please provide the minimum confidence percentage (e.g., 75).")
        return

    try:
        new_confidence = int(context.args[0])
        if not (0 <= new_confidence <= 100):
            await update.message.reply_text("Confidence must be between 0 and 100.")
            return

        # Update the global confidence variable (or a more persistent storage)
        global AUTOSIGNAL_MIN_CONFIDENCE
        AUTOSIGNAL_MIN_CONFIDENCE = new_confidence
        # Ideally, this should be saved to a configuration file or database
        await update.message.reply_text(
            f"AutoSignal minimum confidence set to {new_confidence}%."
        )
        logger.info(
            f"AutoSignal minimum confidence updated to {new_confidence}% by admin."
        )

    except ValueError:
        await update.message.reply_text("Invalid confidence. Please enter a number.")
    except Exception as e:
        logger.error(f"Error setting confidence: {e}")
        await update.message.reply_text("An error occurred while setting the confidence.")


async def set_recipient(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets AutoSignal recipients (admin only)."""
    user_id = update.effective_user.id
    if user_id != int(os.environ.get("ADMIN_USER_ID")):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text(
            "Please specify the recipient type: 'all', 'premium', or 'lifetime'."
        )
        return

    recipient_type = context.args[0].lower()
    valid_types = ["all", "premium", "lifetime"]

    if recipient_type not in valid_types:
        await update.message.reply_text(
            f"Invalid recipient type. Please choose from: {', '.join(valid_types)}."
        )
        return

    # Update the global recipient type variable (or a more persistent storage)
    global AUTOSIGNAL_RECIPIENTS
    AUTOSIGNAL_RECIPIENTS = recipient_type
    await update.message.reply_text(
        f"AutoSignal recipients set to '{recipient_type}'."
    )
    logger.info(f"AutoSignal recipients updated to '{recipient_type}' by admin.")


# --- Signal Processing ---


async def process_signals(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Processes new signals from Supabase and sends notifications to eligible users.
    This function is intended to be run periodically.
    """
    try:
        logger.info("Starting signal processing...")
        # Get the current time
        now = datetime.now(pytz.timezone(Config.TIMEZONE))

        # Fetch signals from Supabase, ordered by timestamp
        # We fetch signals that have not been processed yet or that need re-processing.
        # For now, let's assume we process all new signals since the last check.
        # A more robust approach would involve a 'processed' flag in the database.

        # Fetch signals from Supabase
        response = sb_client.table(SB_TABLES.SIGNALS).select("*").execute()

        if response.data is None:
            logger.warning("No signals found in Supabase.")
            return

        signals_data = response.data
        logger.info(f"Fetched {len(signals_data)} signals from Supabase.")

        # Initialize SignalProcessor
        signal_processor = SignalProcessor(
            min_confidence=AUTOSIGNAL_MIN_CONFIDENCE
        )

        # Process each signal
        processed_count = 0
        for signal in signals_data:
            try:
                # Format signal data for the processor
                formatted_signal = format_signal_data(signal)
                if not formatted_signal:
                    logger.warning(f"Skipping malformed signal: {signal.get('id')}")
                    continue

                # Process the signal
                processed_signal = signal_processor.process_signal(formatted_signal)

                # If the signal meets the criteria for AutoSignal
                if processed_signal and processed_signal["send_to_autosignal"]:
                    # Determine recipients based on configuration
                    recipients = []
                    if AUTOSIGNAL_RECIPIENTS == "all":
                        recipients = sb_list_users(columns="telegram_id,banned")
                    elif AUTOSIGNAL_RECIPIENTS == "premium":
                        recipients = sb_list_users(columns="telegram_id,is_premium,banned")
                    elif AUTOSIGNAL_RECIPIENTS == "lifetime":
                        recipients = sb_list_users(columns="telegram_id,lifetime_premium,banned") # Assuming 'lifetime_premium' column exists

                    eligible_recipients = []
                    for user in recipients:
                        user_id = user.get("telegram_id")
                        banned = user.get("banned", False)
                        if user_id and not banned:
                            is_eligible = False
                            if AUTOSIGNAL_RECIPIENTS == "all":
                                is_eligible = True
                            elif AUTOSIGNAL_RECIPIENTS == "premium":
                                if user.get("is_premium", False):
                                    is_eligible = True
                            elif AUTOSIGNAL_RECIPIENTS == "lifetime":
                                if user.get("lifetime_premium", False): # Check for lifetime premium status
                                    is_eligible = True

                            if is_eligible:
                                eligible_recipients.append(user_id)

                    # Send notification to eligible recipients
                    if eligible_recipients:
                        message = (
                            f"🚨 **New Signal Alert!**\n\n"
                            f"**Pair**: {processed_signal['pair']}\n"
                            f"**Entry Price**: {processed_signal['entry_price']}\n"
                            f"**Take Profit**: {processed_signal['take_profit']}\n"
                            f"**Stop Loss**: {processed_signal['stop_loss']}\n"
                            f"**Confidence**: {processed_signal['confidence']:.2f}%\n\n"
                            f"*(This is an automated signal)*"
                        )

                        sent_count = 0
                        failed_count = 0
                        for recipient_id in eligible_recipients:
                            try:
                                await context.bot.send_message(
                                    chat_id=recipient_id,
                                    text=message,
                                    parse_mode=ParseMode.MARKDOWN,
                                )
                                sent_count += 1
                                # Save timestamp of successful send
                                save_last_signal_timestamp(datetime.now(pytz.timezone(Config.TIMEZONE)))
                            except Exception as e:
                                logger.error(
                                    f"Failed to send AutoSignal to {recipient_id}: {e}"
                                )
                                failed_count += 1
                                # Optionally, mark user as undeliverable or retry later

                        logger.info(
                            f"Sent AutoSignal for {processed_signal['pair']} to {sent_count} users. Failed: {failed_count}."
                        )
                        processed_count += 1
                    else:
                        logger.info(f"No eligible recipients for AutoSignal for {processed_signal['pair']}.")

            except (SignalProcessingError, DataProcessingError) as e:
                logger.error(f"Error processing signal {signal.get('id')}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error processing signal {signal.get('id')}: {e}")

        logger.info(f"Signal processing finished. Processed {processed_count} signals for AutoSignal.")

    except SupabaseError as e:
        logger.error(f"Supabase error during signal processing: {e}")
    except TelegramError as e:
        logger.error(f"Telegram error during signal processing: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during signal processing: {e}")


async def periodic_tasks(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Runs periodic tasks like signal processing."""
    # This function will be scheduled to run at a specific interval
    await process_signals(context)


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(os.environ.get("TELEGRAM_BOT_TOKEN")).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("resend_signals", resend_signals))
    application.add_handler(CommandHandler("set_interval", set_interval))
    application.add_handler(CommandHandler("set_confidence", set_confidence))
    application.add_handler(CommandHandler("set_recipient", set_recipient))

    # Add a message handler for general text messages (optional)
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Schedule the periodic tasks
    # Use run_repeating to execute the task at a defined interval
    # The interval is in seconds.
    job_queue = application.job_queue
    job_queue.run_repeating(
        periodic_tasks,
        interval=SIGNAL_PROCESSING_INTERVAL,
        first=10,  # Start after 10 seconds
        name="periodic_tasks_job",
    )

    # Run the bot until the user presses Ctrl-C
    logger.info("Bot started. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()