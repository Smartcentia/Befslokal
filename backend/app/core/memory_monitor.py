"""
Memory monitoring utility for BEFS backend.

Provides memory usage tracking and warnings to prevent OOM issues on cloud instances.
"""
import psutil
import gc
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def get_memory_info() -> Dict[str, Any]:
    """
    Get current memory usage information.
    
    Returns:
        Dictionary with memory metrics in MB
    """
    process = psutil.Process()
    mem_info = process.memory_info()
    
    # Get system memory
    virtual_mem = psutil.virtual_memory()
    
    return {
        "rss_mb": round(mem_info.rss / 1024 / 1024, 2),  # Resident Set Size
        "vms_mb": round(mem_info.vms / 1024 / 1024, 2),  # Virtual Memory Size
        "percent": round(process.memory_percent(), 2),
        "available_system_mb": round(virtual_mem.available / 1024 / 1024, 2),
        "total_system_mb": round(virtual_mem.total / 1024 / 1024, 2),
        "system_percent": round(virtual_mem.percent, 2)
    }

def log_memory_usage(context: str = ""):
    """
    Log current memory usage with optional context.
    
    Args:
        context: Description of when this is being logged
    """
    mem = get_memory_info()
    prefix = f"[{context}] " if context else ""
    logger.info(
        f"{prefix}Memory: RSS={mem['rss_mb']}MB, "
        f"Process={mem['percent']}%, System={mem['system_percent']}%"
    )

def check_memory_threshold(threshold_percent: float = 80.0) -> bool:
    """
    Check if memory usage exceeds threshold.
    
    Args:
        threshold_percent: Warning threshold (default 80%)
        
    Returns:
        True if memory usage is above threshold
    """
    mem = get_memory_info()
    if mem["percent"] > threshold_percent:
        logger.warning(
            f"⚠️ Memory usage HIGH: {mem['percent']}% "
            f"({mem['rss_mb']}MB RSS). Consider running gc.collect()"
        )
        return True
    return False

def force_garbage_collection() -> Dict[str, int]:
    """
    Force garbage collection and return stats.
    
    Returns:
        Dictionary with collection statistics
    """
    before = get_memory_info()
    
    # Force full collection
    collected = gc.collect()
    
    after = get_memory_info()
    freed_mb = round(before["rss_mb"] - after["rss_mb"], 2)
    
    logger.info(f"GC: Collected {collected} objects, freed ~{freed_mb}MB")
    
    return {
        "objects_collected": collected,
        "memory_freed_mb": freed_mb,
        "before_mb": before["rss_mb"],
        "after_mb": after["rss_mb"]
    }
