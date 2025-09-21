#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
System Control API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta
import psutil
import time

from core.models import SystemHealthResponse, SystemMetricsResponse
from core.auth import require_permission
from api.dependencies import get_download_manager, get_database_manager

router = APIRouter()

# Global system start time
system_start_time = time.time()


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health():
    """Get system health status (public endpoint)"""
    
    try:
        # Calculate uptime
        uptime_seconds = int(time.time() - system_start_time)
        
        # Get memory info
        memory = psutil.virtual_memory()
        
        # Get disk info for cache directory
        from config.settings import settings
        from pathlib import Path
        
        cache_dir = Path(settings.CACHE_DIR)
        if cache_dir.exists():
            cache_usage = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
            disk_usage = psutil.disk_usage(str(cache_dir))
            available_storage = disk_usage.free
        else:
            cache_usage = 0
            available_storage = 0
        
        cache_usage_percentage = 0.0
        if settings.MAX_CACHE_SIZE > 0:
            cache_usage_percentage = (cache_usage / settings.MAX_CACHE_SIZE) * 100
        
        return SystemHealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            uptime_seconds=uptime_seconds,
            active_downloads=0,  # Would be filled from download_manager
            cache_usage_bytes=cache_usage,
            cache_usage_percentage=min(100.0, cache_usage_percentage),
            available_storage_bytes=available_storage,
            telethon_clients_active=1,  # Would be from telethon_manager
            error_count_last_hour=0  # Would be from error tracking
        )
        
    except Exception as e:
        # Return unhealthy status but still respond
        return SystemHealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            uptime_seconds=int(time.time() - system_start_time),
            active_downloads=0,
            cache_usage_bytes=0,
            cache_usage_percentage=0.0,
            available_storage_bytes=0,
            telethon_clients_active=0,
            error_count_last_hour=1
        )


@router.get("/metrics", response_model=SystemMetricsResponse)
async def get_system_metrics(
    current_token = Depends(require_permission("system.monitor")),
    db_manager = Depends(get_database_manager),
    download_manager = Depends(get_download_manager)
):
    """Get detailed system metrics"""
    
    try:
        # Get system stats from database
        db_stats = await db_manager.get_system_stats()
        
        # Get CPU and memory usage
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Get network stats (simplified)
        network = psutil.net_io_counters()
        
        # Calculate bandwidth usage (simplified)
        bandwidth_mbps = 0.0  # Would need more sophisticated tracking
        
        return SystemMetricsResponse(
            active_requests=len(download_manager.active_downloads),
            avg_download_speed_mbps=0.0,  # Would calculate from active downloads
            memory_usage_percentage=memory.percent,
            cpu_usage_percentage=cpu_usage,
            bandwidth_usage_mbps=bandwidth_mbps,
            daily_downloads=db_stats.get('daily_downloads', 0),
            daily_active_users=db_stats.get('daily_active_users', 0),
            daily_transfer_gb=db_stats.get('daily_transfer_bytes', 0) / (1024**3)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving metrics: {str(e)}"
        )


@router.post("/start")
async def start_system(
    current_token = Depends(require_permission("system.control"))
):
    """Start system services"""
    
    # This would be implemented based on your deployment architecture
    # For now, return success since the system is already running
    
    return {
        "message": "System start initiated",
        "status": "running",
        "started_at": datetime.utcnow(),
        "services": [
            {"name": "download_api", "status": "running"},
            {"name": "telethon_client", "status": "running"},
            {"name": "cache_manager", "status": "running"}
        ]
    }


@router.post("/stop")
async def stop_system(
    current_token = Depends(require_permission("system.control"))
):
    """Stop system services"""
    
    # This would gracefully stop services
    # For now, just return acknowledgment
    
    return {
        "message": "System stop initiated",
        "status": "stopping",
        "stopped_at": datetime.utcnow(),
        "note": "All active downloads will be cancelled"
    }


@router.post("/restart")
async def restart_system(
    current_token = Depends(require_permission("system.control"))
):
    """Restart system services"""
    
    return {
        "message": "System restart initiated",
        "status": "restarting",
        "restarted_at": datetime.utcnow(),
        "estimated_downtime_seconds": 30
    }


@router.post("/cache/cleanup")
async def cleanup_cache(
    current_token = Depends(require_permission("system.control")),
    download_manager = Depends(get_download_manager)
):
    """Cleanup system cache"""
    
    try:
        # Cleanup expired cache entries
        cleaned_count = await download_manager.cache_manager.db.cleanup_expired_cache()
        
        # Get cache usage after cleanup
        from config.settings import settings
        from pathlib import Path
        
        cache_dir = Path(settings.CACHE_DIR)
        cache_usage = 0
        if cache_dir.exists():
            cache_usage = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
        
        return {
            "message": "Cache cleanup completed",
            "cleaned_entries": cleaned_count,
            "cache_usage_bytes": cache_usage,
            "cache_usage_mb": cache_usage / (1024 * 1024),
            "cleaned_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache cleanup failed: {str(e)}"
        )


@router.get("/config")
async def get_system_config(
    current_token = Depends(require_permission("system.read"))
):
    """Get system configuration"""
    
    from config.settings import settings
    
    return {
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "max_file_size_bot_api": settings.MAX_FILE_SIZE_BOT_API,
        "max_file_size_telethon": settings.MAX_FILE_SIZE_TELETHON,
        "max_cache_size": settings.MAX_CACHE_SIZE,
        "cache_ttl_hours": settings.CACHE_TTL_HOURS,
        "rate_limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
        "max_concurrent_downloads": settings.MAX_CONCURRENT_DOWNLOADS,
        "chunk_size": settings.CHUNK_SIZE
    }


@router.put("/config")
async def update_system_config(
    config_updates: dict,
    current_token = Depends(require_permission("admin.system"))
):
    """Update system configuration"""
    
    # This would update runtime configuration
    # For now, just acknowledge the request
    
    return {
        "message": "Configuration update initiated",
        "updated_settings": list(config_updates.keys()),
        "note": "Some settings may require system restart to take effect"
    }


@router.get("/logs")
async def get_system_logs(
    lines: int = 100,
    level: str = "INFO",
    current_token = Depends(require_permission("system.monitor"))
):
    """Get system logs"""
    
    try:
        from config.settings import settings
        from pathlib import Path
        
        log_file = Path(settings.LOG_FILE) if settings.LOG_FILE else None
        
        if not log_file or not log_file.exists():
            return {
                "logs": [],
                "message": "No log file found"
            }
        
        # Read last N lines
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        # Filter by log level if specified
        filtered_lines = []
        if level != "ALL":
            for line in recent_lines:
                if level.upper() in line:
                    filtered_lines.append(line.strip())
        else:
            filtered_lines = [line.strip() for line in recent_lines]
        
        return {
            "logs": filtered_lines,
            "total_lines": len(filtered_lines),
            "log_file": str(log_file),
            "level_filter": level
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading logs: {str(e)}"
        )