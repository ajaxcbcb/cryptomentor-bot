
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ProcessingJob:
    user_id: int
    command: str
    symbol: str
    start_time: float
    estimated_duration: int
    current_stage: str
    progress: int
    status: str = "processing"

class ProgressTracker:
    def __init__(self):
        self.active_jobs: Dict[int, ProcessingJob] = {}
        self.queue: List[ProcessingJob] = []
        self.max_concurrent = 3  # Maximum concurrent processing
        self.stage_templates = {
            '/analyze': [
                "🔍 Mengambil data CoinAPI...",
                "📊 Memproses technical indicators...", 
                "🧠 Menganalisis sentimen pasar...",
                "💰 Menghitung SnD zones...",
                "📈 Generating trading signals...",
                "✍️ Menyusun laporan final..."
            ],
            '/futures': [
                "🔍 Fetching real-time data...",
                "📊 Calculating SnD zones...",
                "🧠 Processing market structure...",
                "⚡ Generating entry signals...",
                "💎 Calculating risk/reward...",
                "✍️ Finalizing analysis..."
            ],
            '/futures_signals': [
                "🔍 Scanning top 25 coins...",
                "📊 Multi-timeframe analysis...",
                "🧠 AI pattern recognition...",
                "💰 Supply/Demand detection...",
                "⚡ Signal validation...",
                "🎯 Confidence scoring...",
                "✍️ Compiling results..."
            ],
            '/market': [
                "🌍 Fetching global market data...",
                "📊 Processing CoinAPI metrics...",
                "🧠 Analyzing market sentiment...",
                "💰 Calculating dominance...",
                "✍️ Building market overview..."
            ]
        }
        
    def get_estimated_duration(self, command: str) -> int:
        """Get estimated duration in seconds for each command"""
        durations = {
            '/analyze': 25,
            '/futures': 20, 
            '/futures_signals': 45,
            '/market': 18
        }
        return durations.get(command, 20)
    
    def create_progress_bar(self, progress: int) -> str:
        """Create visual progress bar"""
        progress = max(0, min(100, progress))  # Ensure progress is between 0-100
        filled = int(progress / 10)  # Each block = 10%
        empty = 10 - filled
        return "🟢" * filled + "⚪" * empty
    
    def format_time(self, seconds: int) -> str:
        """Format seconds to readable time"""
        if seconds < 60:
            return f"~{seconds} seconds"
        else:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            if remaining_seconds > 0:
                return f"~{minutes}m {remaining_seconds}s"
            return f"~{minutes} minutes"
    
    async def start_processing(self, user_id: int, command: str, symbol: str = "") -> ProcessingJob:
        """Start a new processing job"""
        estimated_duration = self.get_estimated_duration(command)
        
        job = ProcessingJob(
            user_id=user_id,
            command=command,
            symbol=symbol,
            start_time=time.time(),
            estimated_duration=estimated_duration,
            current_stage=self.stage_templates[command][0],
            progress=0
        )
        
        # Check if we can process immediately or need to queue
        if len(self.active_jobs) < self.max_concurrent:
            self.active_jobs[user_id] = job
            return job
        else:
            self.queue.append(job)
            job.status = "queued"
            return job
    
    def get_queue_status(self) -> Dict:
        """Get current queue and active job status"""
        return {
            "active_count": len(self.active_jobs),
            "queue_count": len(self.queue),
            "max_concurrent": self.max_concurrent
        }
    
    def get_job_status(self, user_id: int) -> Optional[ProcessingJob]:
        """Get current job status for user"""
        if user_id in self.active_jobs:
            return self.active_jobs[user_id]
        
        for job in self.queue:
            if job.user_id == user_id:
                return job
        
        return None
    
    async def update_progress(self, user_id: int, progress: int, stage: str = None):
        """Update progress for a specific job"""
        if user_id in self.active_jobs:
            job = self.active_jobs[user_id]
            job.progress = min(100, progress)
            if stage:
                job.current_stage = stage
    
    def complete_job(self, user_id: int):
        """Mark job as complete and process queue"""
        if user_id in self.active_jobs:
            del self.active_jobs[user_id]
            
            # Process queue if available
            if self.queue and len(self.active_jobs) < self.max_concurrent:
                next_job = self.queue.pop(0)
                next_job.status = "processing"
                self.active_jobs[next_job.user_id] = next_job
    
    def get_progress_message(self, user_id: int) -> str:
        """Generate progress message for user"""
        job = self.get_job_status(user_id)
        if not job:
            return "❌ Job not found"
        
        if job.status == "queued":
            queue_position = next((i+1 for i, q in enumerate(self.queue) if q.user_id == user_id), 0)
            queue_status = self.get_queue_status()
            estimated_wait = queue_position * 15  # Rough estimate
            
            return f"""🎯 {job.command.upper()} REQUEST QUEUED

⏳ Queue Position: #{queue_position}
📊 Active Processing: {queue_status['active_count']}/{queue_status['max_concurrent']}
⏱️ Estimated Wait: {self.format_time(estimated_wait)}

🔄 Your request will be processed soon...
💡 Queue Info: {queue_status['queue_count']} waiting | {queue_status['active_count']} active"""
        
        # Active processing - ensure progress is updated
        elapsed = int(time.time() - job.start_time)
        remaining = max(0, job.estimated_duration - elapsed)
        
        # Auto-increment progress if it's stuck at 0
        if job.progress == 0 and elapsed > 2:
            job.progress = min(20, elapsed * 5)  # 5% per second for first 4 seconds
        
        progress_bar = self.create_progress_bar(job.progress)
        
        # Get queue info
        queue_status = self.get_queue_status()
        
        symbol_display = f" {job.symbol}" if job.symbol else ""
        
        return f"""🎯 {job.command.upper()} REQUEST RECEIVED{symbol_display}

⏳ Estimated Time: {job.estimated_duration} seconds  
📊 Progress: {job.progress}% {progress_bar}
⚡ Status: AI Processing Active
⏱️ Remaining: {self.format_time(remaining)}

🔄 Current Stage:  
{job.current_stage}

💡 Queue Info: {queue_status['queue_count']} waiting | {queue_status['active_count']} active"""

# Global instance
progress_tracker = ProgressTracker()
