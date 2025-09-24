
from telegram import Update
from telegram.ext import ContextTypes
from app.progress_tracker import progress_tracker

async def queue_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /queue_status command - Admin only"""
    from app.lib.auth import is_admin
    
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Access denied. Admin only command.")
        return
    
    status = progress_tracker.get_queue_status()
    
    # Get detailed task info
    queued_tasks = []
    processing_tasks = []
    
    for task_id, task in progress_tracker.active_tasks.items():
        task_info = f"• {task.command} (User: {task.user_id}, Progress: {task.progress}%)"
        
        if task.status == 'queued':
            queued_tasks.append(f"{task_info} - Position #{task.queue_position}")
        elif task.status == 'processing':
            processing_tasks.append(task_info)
    
    message = f"""🔧 **AI Processing Queue Status**

📊 **Overview:**
• Queued: {status['queued']} tasks
• Processing: {status['processing']} tasks  
• Max Concurrent: {status['max_concurrent']}
• Total Active: {status['total_active']}

⚡ **Currently Processing:**
{chr(10).join(processing_tasks) if processing_tasks else "• No active processing"}

📋 **Queue:**
{chr(10).join(queued_tasks) if queued_tasks else "• Queue is empty"}

💡 **Performance:**
• Average command time: 15-35 seconds
• Queue processes automatically
• Users see real-time progress"""

    await update.message.reply_text(message, parse_mode='Markdown')
