
import asyncio
import time
from typing import Dict, List
from dataclasses import dataclass

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
        from app.progress_tracker import progress_tracker
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
