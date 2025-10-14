
import gc
import os
import psutil
from typing import Dict, Any

class PerformanceOptimizer:
    """Ultra-fast performance optimizer for CryptoMentor AI"""
    
    def __init__(self):
        self.process = psutil.Process()
        self._optimization_enabled = True
    
    def optimize_runtime(self):
        """Apply runtime optimizations for maximum performance"""
        if not self._optimization_enabled:
            return
            
        try:
            # Memory optimization
            gc.collect()  # Force garbage collection
            
            # Process priority optimization
            if os.name != 'nt':  # Unix/Linux systems
                os.nice(-5)  # Higher priority (if permitted)
            
            # CPU affinity optimization (use all cores)
            try:
                available_cpus = list(range(psutil.cpu_count()))
                self.process.cpu_affinity(available_cpus)
            except (AttributeError, OSError):
                pass  # Skip if not supported
            
        except Exception as e:
            print(f"Performance optimization warning: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        try:
            return {
                'cpu_percent': self.process.cpu_percent(),
                'memory_percent': self.process.memory_percent(),
                'memory_mb': self.process.memory_info().rss / 1024 / 1024,
                'threads': self.process.num_threads(),
                'connections': len(self.process.connections())
            }
        except Exception:
            return {}
    
    def enable_turbo_mode(self):
        """Enable maximum performance mode"""
        self._optimization_enabled = True
        self.optimize_runtime()
        
        # Disable debug logging for performance
        import logging
        logging.getLogger().setLevel(logging.WARNING)
        
        print("🚀 TURBO MODE ENABLED - Maximum Performance Activated!")

# Global optimizer instance
performance_optimizer = PerformanceOptimizer()
