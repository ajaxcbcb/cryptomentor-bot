
import asyncio
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass
from telegram import Update
from telegram.ext import ContextTypes

@dataclass
class ProgressTask:
    user_id: int
    chat_id: int
    command: str
    message_id: int
    start_time: float
    estimated_duration: int  # in seconds
    status: str  # 'queued', 'processing', 'completed', 'failed'
    progress: int  # 0-100
    queue_position: int = 0

class ProgressTracker:
    def __init__(self):
        self.active_tasks: Dict[str, ProgressTask] = {}
        self.queue: List[str] = []
        self.processing_count = 0
        self.max_concurrent = 3  # Maximum concurrent AI processing
        
        # Command duration estimates (seconds)
        self.duration_estimates = {
            '/analyze': 25,
            '/futures': 20,
            '/futures_signals': 35,
            '/market': 18,
            '/ask_ai': 15
        }
        
        # Progress stages for different commands
        self.progress_stages = {
            '/analyze': [
                (10, "🔄 Mengambil data harga real-time..."),
                (25, "📊 Menganalisis indikator teknikal..."),
                (45, "🧠 Memproses sentimen pasar..."),
                (65, "📈 Menghitung Supply & Demand zones..."),
                (85, "✨ Menyusun analisis komprehensif..."),
                (100, "✅ Analisis selesai!")
            ],
            '/futures': [
                (15, "⚡ Mengambil data futures real-time..."),
                (35, "🎯 Mengkalkulasi SnD zones..."),
                (55, "📊 Menganalisis confidence level..."),
                (75, "💰 Menghitung entry/exit points..."),
                (95, "🔥 Menyiapkan sinyal trading..."),
                (100, "✅ Sinyal futures siap!")
            ],
            '/futures_signals': [
                (8, "🔍 Scanning top 25 cryptocurrencies..."),
                (20, "📊 Menganalisis volume & momentum..."),
                (35, "🎯 Mencari setup SnD berkualitas..."),
                (50, "⚡ Filtering sinyal confidence ≥65%..."),
                (70, "💎 Menghitung risk/reward ratios..."),
                (85, "📈 Menyusun multiple signals..."),
                (100, "🚨 Futures signals ready!")
            ],
            '/market': [
                (20, "🌍 Mengumpulkan data pasar global..."),
                (40, "📊 Menganalisis dominance BTC/ETH..."),
                (60, "💰 Menghitung sentimen Fear & Greed..."),
                (80, "🔥 Menyusun overview komprehensif..."),
                (100, "🌍 Market analysis complete!")
            ],
            '/ask_ai': [
                (30, "🤖 Memproses pertanyaan AI..."),
                (70, "💡 Menyusun jawaban komprehensif..."),
                (100, "✅ AI response ready!")
            ]
        }

    def get_task_id(self, user_id: int, command: str) -> str:
        return f"{user_id}_{command}_{int(time.time())}"

    async def start_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE, command: str) -> str:
        """Start a new progress tracked task"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Create task ID
        task_id = self.get_task_id(user_id, command)
        
        # Estimate duration
        estimated_duration = self.duration_estimates.get(command, 20)
        
        # Send initial progress message
        progress_msg = await update.message.reply_text(
            f"🎯 **{command.upper()} REQUEST RECEIVED**\n\n"
            f"⏳ **Estimated Time**: {estimated_duration} seconds\n"
            f"📊 **Progress**: 0%\n"
            f"🔄 **Status**: Initializing...\n\n"
            f"⚡ CryptoMentor AI sedang memproses request Anda...",
            parse_mode='Markdown'
        )
        
        # Create task
        task = ProgressTask(
            user_id=user_id,
            chat_id=chat_id,
            command=command,
            message_id=progress_msg.message_id,
            start_time=time.time(),
            estimated_duration=estimated_duration,
            status='queued',
            progress=0
        )
        
        # Add to queue
        self.active_tasks[task_id] = task
        self.queue.append(task_id)
        
        # Update queue positions
        await self._update_queue_positions()
        
        # Try to start processing
        await self._process_queue(context)
        
        return task_id

    async def _update_queue_positions(self):
        """Update queue positions for all queued tasks"""
        queued_tasks = [tid for tid in self.queue if self.active_tasks[tid].status == 'queued']
        for i, task_id in enumerate(queued_tasks):
            self.active_tasks[task_id].queue_position = i + 1

    async def _process_queue(self, context: ContextTypes.DEFAULT_TYPE):
        """Process the queue - start tasks if under concurrent limit"""
        while self.processing_count < self.max_concurrent and self.queue:
            # Get next queued task
            queued_tasks = [tid for tid in self.queue if self.active_tasks[tid].status == 'queued']
            if not queued_tasks:
                break
                
            task_id = queued_tasks[0]
            task = self.active_tasks[task_id]
            
            # Start processing
            task.status = 'processing'
            self.processing_count += 1
            
            # Update progress message
            await self._update_progress_message(context, task_id, 5, "🚀 Starting AI processing...")
            
            break

    async def update_progress(self, context: ContextTypes.DEFAULT_TYPE, task_id: str, progress: int, custom_message: str = None):
        """Update progress for a task"""
        if task_id not in self.active_tasks:
            return
            
        task = self.active_tasks[task_id]
        task.progress = min(100, progress)
        
        # Get stage message
        stages = self.progress_stages.get(task.command, [])
        stage_message = custom_message
        
        if not stage_message:
            for stage_progress, message in stages:
                if progress >= stage_progress:
                    stage_message = message
        
        if not stage_message:
            stage_message = "🔄 Processing..."
            
        await self._update_progress_message(context, task_id, progress, stage_message)

    async def _update_progress_message(self, context: ContextTypes.DEFAULT_TYPE, task_id: str, progress: int, stage_message: str):
        """Update the progress message"""
        if task_id not in self.active_tasks:
            return
            
        task = self.active_tasks[task_id]
        
        # Calculate elapsed and remaining time
        elapsed = int(time.time() - task.start_time)
        
        if progress > 0:
            estimated_total = (elapsed / progress) * 100
            remaining = max(0, int(estimated_total - elapsed))
        else:
            remaining = task.estimated_duration
        
        # Create progress bar
        progress_bars = "🟢" * (progress // 10) + "⚪" * (10 - (progress // 10))
        
        # Build message based on status
        if task.status == 'queued':
            status_text = f"📋 **Status**: In Queue (Position #{task.queue_position})\n"
            status_text += f"⏰ **Estimated Wait**: {self._estimate_queue_wait(task_id)} seconds"
        elif task.status == 'processing':
            status_text = f"⚡ **Status**: AI Processing Active\n"
            status_text += f"⏱️ **Remaining**: ~{remaining} seconds"
        else:
            status_text = f"📊 **Status**: {task.status.title()}"
        
        message_text = f"""🎯 **{task.command.upper()} - AI PROCESSING**

📊 **Progress**: {progress}% {progress_bars}
{status_text}
⏳ **Elapsed**: {elapsed}s

🔄 **Current Stage**: 
{stage_message}

💡 **Queue Info**: {len([t for t in self.active_tasks.values() if t.status == 'queued'])} waiting | {self.processing_count} active"""

        try:
            await context.bot.edit_message_text(
                chat_id=task.chat_id,
                message_id=task.message_id,
                text=message_text,
                parse_mode='Markdown'
            )
        except Exception as e:
            # Message might be deleted or too old to edit
            print(f"Progress update failed for task {task_id}: {e}")

    def _estimate_queue_wait(self, task_id: str) -> int:
        """Estimate wait time for queued task"""
        task = self.active_tasks[task_id]
        
        # Count tasks ahead in queue
        ahead_count = 0
        for tid in self.queue:
            if tid == task_id:
                break
            if self.active_tasks[tid].status in ['queued', 'processing']:
                ahead_count += 1
        
        # Estimate based on queue position and average processing time
        avg_duration = 25  # Average command duration
        return ahead_count * (avg_duration // self.max_concurrent)

    async def complete_task(self, context: ContextTypes.DEFAULT_TYPE, task_id: str, success: bool = True, final_message: str = None):
        """Mark task as completed"""
        if task_id not in self.active_tasks:
            return
            
        task = self.active_tasks[task_id]
        task.status = 'completed' if success else 'failed'
        task.progress = 100
        
        if task.status == 'processing':
            self.processing_count -= 1
        
        # Remove from queue
        if task_id in self.queue:
            self.queue.remove(task_id)
        
        # Final progress update
        if success:
            final_msg = final_message or "✅ AI processing completed successfully!"
        else:
            final_msg = final_message or "❌ AI processing failed. Please try again."
            
        await self._update_progress_message(context, task_id, 100, final_msg)
        
        # Clean up task after 30 seconds
        await asyncio.sleep(30)
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        
        # Process next in queue
        await self._process_queue(context)

    def get_queue_status(self) -> Dict:
        """Get current queue status"""
        queued = len([t for t in self.active_tasks.values() if t.status == 'queued'])
        processing = len([t for t in self.active_tasks.values() if t.status == 'processing'])
        
        return {
            'queued': queued,
            'processing': processing,
            'total_active': len(self.active_tasks),
            'max_concurrent': self.max_concurrent
        }

# Global instance
progress_tracker = ProgressTracker()
