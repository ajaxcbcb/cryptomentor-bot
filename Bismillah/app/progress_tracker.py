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
        self.active_jobs = {}
        self.update_interval = 0.1  # Update every 0.1 seconds for instant feel
        self._cache = {}  # Cache progress messages

    def get_estimated_duration(self, command: str) -> int:
        """Get estimated duration in seconds for each command - optimized for heavy VPS"""
        durations = {
            '/analyze': 10,          # Exactly 10 seconds with heavy performance
            '/futures': 10,          # Exactly 10 seconds with aggressive processing
            '/futures_signals': 10,  # Optimized to 10 seconds using VPS power
            '/market': 10            # Consistent 10 seconds across all commands
        }
        return durations.get(command, 10)

    def create_progress_bar(self, progress: int) -> str:
        """Create numeric progress display"""
        progress = max(0, min(100, progress))  # Ensure progress is between 0-100
        return f"{progress}%"

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
            # Invalidate cache for this user to force regeneration
            if user_id in self._cache:
                del self._cache[user_id]

    def complete_job(self, user_id: int):
        """Mark job as complete and process queue"""
        if user_id in self.active_jobs:
            # Clear cache for completed job
            if user_id in self._cache:
                del self._cache[user_id]
            del self.active_jobs[user_id]

            # Process queue if available
            if self.queue and len(self.active_jobs) < self.max_concurrent:
                next_job = self.queue.pop(0)
                next_job.status = "processing"
                self.active_jobs[next_job.user_id] = next_job

    def get_progress_message(self, user_id: int) -> str:
        """Generate progress message for user"""
        # Check cache first
        if user_id in self._cache:
            return self._cache[user_id]

        job = self.get_job_status(user_id)
        if not job:
            return "❌ Job not found"

        if job.status == "queued":
            queue_position = next((i+1 for i, q in enumerate(self.queue) if q.user_id == user_id), 0)
            queue_status = self.get_queue_status()
            estimated_wait = queue_position * 15  # Rough estimate

            message = f"""🎯 {job.command.upper()} REQUEST QUEUED

⏳ Queue Position: #{queue_position}
📊 Active Processing: {queue_status['active_count']}/{queue_status['max_concurrent']}
⏱️ Estimated Wait: {self.format_time(estimated_wait)}

🔄 Your request will be processed soon...
💡 Queue Info: {queue_status['queue_count']} waiting | {queue_status['active_count']} active"""
        else:
            # Active processing - ensure progress is updated
            elapsed = int(time.time() - job.start_time)
            remaining = max(0, job.estimated_duration - elapsed)

            # Auto-increment progress if it's stuck at 0 and elapsed time is significant
            if job.progress == 0 and elapsed > 1: # Increased threshold to 1 second
                job.progress = min(20, elapsed * 10) # Faster initial progress

            progress_display = self.create_progress_bar(job.progress)

            # Get queue info
            queue_status = self.get_queue_status()

            symbol_display = f" {job.symbol}" if job.symbol else ""

            message = f"""🎯 {job.command.upper()} REQUEST RECEIVED{symbol_display}

⏳ Estimated Time: {job.estimated_duration} seconds
📊 Progress: {progress_display}
⚡ Status: AI Processing Active
⏱️ Remaining: {self.format_time(remaining)}

🔄 Current Stage:
{job.current_stage}

💡 Queue Info: {queue_status['queue_count']} waiting | {queue_status['active_count']} active"""

        # Cache the generated message
        self._cache[user_id] = message
        return message


# Global instance
progress_tracker = ProgressTracker()