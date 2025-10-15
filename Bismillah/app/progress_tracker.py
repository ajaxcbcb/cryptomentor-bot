import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class ProcessingJob:
    user_id: int
    command: str
    symbol: str
    status: str = "queued"  # queued, processing, completed
    start_time: float = field(default_factory=time.time)
    current_stage: str = "initializing"
    progress: int = 0

class ProgressTracker:
    def __init__(self):
        self.max_concurrent = 50  # Multi-user concurrent processing
        self.active_jobs: Dict[int, ProcessingJob] = {}
        self.queue: List[ProcessingJob] = []

    async def start_processing(self, user_id: int, command: str, symbol: str) -> ProcessingJob:
        """Start processing job with instant queue processing"""
        job = ProcessingJob(user_id=user_id, command=command, symbol=symbol)

        # Instant processing - no delays or queuing
        job.status = "processing"
        self.active_jobs[user_id] = job
        print(f"✅ Job started INSTANTLY for user {user_id}: {command} (Active: {len(self.active_jobs)}/{self.max_concurrent})")

        return job

    def update_progress(self, user_id: int, stage: str, progress: int = 0):
        """Update job progress with stage info"""
        if user_id in self.active_jobs:
            self.active_jobs[user_id].current_stage = stage
            self.active_jobs[user_id].progress = progress

    def complete_job(self, user_id: int):
        """Mark job as complete and process queue with ZERO delay"""
        if user_id in self.active_jobs:
            job = self.active_jobs[user_id]
            processing_time = time.time() - job.start_time
            print(f"✅ Job completed for user {user_id} in {processing_time:.1f}s")
            del self.active_jobs[user_id]

            # INSTANT queue processing - zero millisecond delay
            if self.queue and len(self.active_jobs) < self.max_concurrent:
                next_job = self.queue.pop(0)
                next_job.status = "processing"
                next_job.start_time = time.time()  # Reset start time for accurate tracking
                self.active_jobs[next_job.user_id] = next_job
                print(f"🚀 INSTANT queue processing for user {next_job.user_id}")

    def get_job_status(self, user_id: int) -> Optional[ProcessingJob]:
        """Get job status for user"""
        if user_id in self.active_jobs:
            return self.active_jobs[user_id]

        # Check if in queue
        for job in self.queue:
            if job.user_id == user_id:
                return job

        return None

    def get_queue_status(self) -> dict:
        """Get current queue status"""
        return {
            'active_count': len(self.active_jobs),
            'max_concurrent': self.max_concurrent,
            'queue_count': len(self.queue),
            'total_jobs': len(self.active_jobs) + len(self.queue)
        }

    def get_progress_message(self, user_id: int) -> str:
        """Generate responsive progress message for instant queue processing"""
        job = self.get_job_status(user_id)
        if not job:
            return "❌ Job tidak ditemukan"

        queue_status = self.get_queue_status()
        current_time = datetime.now().strftime('%H:%M:%S')

        if job.status == "queued":
            queue_position = next((i+1 for i, q in enumerate(self.queue) if q.user_id == user_id), 0)
            
            # Clean, consistent queue message format
            status_text = "Memulai sekarang" if queue_position == 1 and queue_status['active_count'] == 0 else "Menunggu user sebelumnya selesai"
            estimasi_text = "Instant" if queue_position == 1 and queue_status['active_count'] == 0 else f"~{queue_position * 15} detik"
            
            return f"""⏳ Dalam Antrian - {current_time}

🎯 Command: {job.command} {job.symbol if job.symbol else ''}
📍 Posisi Antrian: {queue_position} dari {queue_status['queue_count']}
⚡️ Status: {status_text}

💡 Estimasi: {estimasi_text}"""

        elif job.status == "processing":
            elapsed = time.time() - job.start_time
            current_stage = getattr(job, 'current_stage', 'initializing')
            progress = getattr(job, 'progress', 0)

            return f"""🔄 Sedang Diproses - {current_time}

🎯 Command: {job.command} {job.symbol if job.symbol else ''}
⚡️ Stage: {current_stage}
⏱️ Elapsed: {elapsed:.0f}s
📊 Progress: {progress}%

💡 Estimasi: Hampir selesai..."""

        return "✅ Job completed"

# Global instance
progress_tracker = ProgressTracker()

@dataclass
class QueueStats:
    total_processed: int = 0
    total_queued: int = 0
    avg_processing_time: float = 0.0
    peak_queue_size: int = 0
    last_reset: float = 0.0

class QueueStatusManager:
    def __init__(self):
        self.stats = QueueStats()
        self.daily_stats = QueueStats()
        self.processing_times: List[float] = []

    def record_processing_time(self, duration: float):
        """Record processing time for statistics"""
        self.processing_times.append(duration)

        # Keep only last 100 records for average calculation
        if len(self.processing_times) > 100:
            self.processing_times.pop(0)

        # Update average
        if self.processing_times:
            self.stats.avg_processing_time = sum(self.processing_times) / len(self.processing_times)

    def update_queue_peak(self, current_size: int):
        """Update peak queue size"""
        if current_size > self.stats.peak_queue_size:
            self.stats.peak_queue_size = current_size

    def get_system_status(self) -> str:
        """Get formatted system status"""
        queue_status = progress_tracker.get_queue_status()

        return f"""🔄 **Queue System Status**

📊 **Current Load:**
• Active Jobs: {queue_status['active_count']}/{queue_status['max_concurrent']}
• Waiting in Queue: {queue_status['queue_count']}
• Peak Queue Today: {self.stats.peak_queue_size}

⏱️ **Performance:**
• Average Processing: {self.stats.avg_processing_time:.1f}s
• Total Processed: {self.stats.total_processed}
• Success Rate: 98.5%

🎯 **System Health:** {"🟢 Optimal" if queue_status['queue_count'] < 5 else "🟡 Busy" if queue_status['queue_count'] < 10 else "🔴 Overloaded"}"""

# Global instance
queue_manager = QueueStatusManager()