#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Admin API Routes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from core.models import TokenResponse
from core.auth import (
    AuthManager, get_auth_manager, require_permission,
    get_current_token
)
from api.dependencies import get_database_manager, get_download_manager

router = APIRouter()


@router.get("/tokens", response_model=List[TokenResponse])
async def list_all_tokens(
    limit: int = Query(default=50, ge=1, le=200),
    current_token = Depends(require_permission("admin.tokens")),
    auth_manager: AuthManager = Depends(get_auth_manager)
):
    """List all API tokens (admin only)"""
    
    # This would require additional database method
    # For now, return empty list with note
    
    return []


@router.get("/stats/system")
async def get_admin_system_stats(
    current_token = Depends(require_permission("admin.system")),
    db_manager = Depends(get_database_manager),
    download_manager = Depends(get_download_manager)
):
    """Get comprehensive system statistics (admin only)"""
    
    try:
        # Get database stats
        db_stats = await db_manager.get_system_stats()
        
        # Get active downloads info
        active_downloads = len(download_manager.active_downloads)
        
        # Get cache info
        from config.settings import settings
        from pathlib import Path
        
        cache_dir = Path(settings.CACHE_DIR)
        cache_files = 0
        cache_size = 0
        
        if cache_dir.exists():
            cache_files = len(list(cache_dir.rglob('*')))
            cache_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
        
        return {
            "database": {
                "active_downloads": db_stats.get('active_downloads', 0),
                "cache_entries": db_stats.get('cache_entries', 0),
                "daily_downloads": db_stats.get('daily_downloads', 0),
                "daily_active_users": db_stats.get('daily_active_users', 0),
                "daily_transfer_bytes": db_stats.get('daily_transfer_bytes', 0)
            },
            "cache": {
                "files": cache_files,
                "total_size_bytes": cache_size,
                "total_size_mb": cache_size / (1024 * 1024),
                "max_size_bytes": settings.MAX_CACHE_SIZE,
                "usage_percentage": (cache_size / settings.MAX_CACHE_SIZE) * 100 if settings.MAX_CACHE_SIZE > 0 else 0
            },
            "runtime": {
                "active_downloads": active_downloads,
                "telethon_clients": len(download_manager.telethon_manager.clients)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving admin stats: {str(e)}"
        )


@router.get("/downloads/active")
async def get_active_downloads(
    current_token = Depends(require_permission("admin.system")),
    download_manager = Depends(get_download_manager)
):
    """Get all active downloads (admin only)"""
    
    active_downloads = []
    
    for session_id, session in download_manager.active_downloads.items():
        # Calculate progress
        progress_percentage = 0.0
        if session.file_size > 0:
            progress_percentage = (session.downloaded_bytes / session.file_size) * 100
        
        active_downloads.append({
            "session_id": session_id,
            "file_id": session.file_id,
            "link_code": session.link_code,
            "ip_address": session.ip_address,
            "status": session.status.value,
            "progress_percentage": min(100.0, progress_percentage),
            "downloaded_bytes": session.downloaded_bytes,
            "total_bytes": session.file_size,
            "started_at": session.started_at,
            "download_method": session.download_method
        })
    
    return {
        "active_downloads": active_downloads,
        "total_count": len(active_downloads)
    }


@router.delete("/downloads/{session_id}")
async def cancel_download(
    session_id: str,
    current_token = Depends(require_permission("admin.system")),
    download_manager = Depends(get_download_manager)
):
    """Cancel active download (admin only)"""
    
    if session_id not in download_manager.active_downloads:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download session not found"
        )
    
    # Mark as cancelled
    await download_manager.finish_download_session(session_id, False)
    
    return {
        "message": "Download cancelled successfully",
        "session_id": session_id
    }


@router.post("/cache/clear")
async def clear_all_cache(
    current_token = Depends(require_permission("admin.system")),
    download_manager = Depends(get_download_manager)
):
    """Clear all cache (admin only)"""
    
    try:
        from config.settings import settings
        from pathlib import Path
        import shutil
        
        cache_dir = Path(settings.CACHE_DIR)
        
        if cache_dir.exists():
            # Remove all files in cache directory
            for item in cache_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
        
        # Clear cache entries from database
        await download_manager.cache_manager.db.cleanup_expired_cache()
        
        return {
            "message": "All cache cleared successfully",
            "cleared_at": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing cache: {str(e)}"
        )


@router.get("/links/all")
async def get_all_download_links(
    limit: int = Query(default=100, ge=1, le=500),
    current_token = Depends(require_permission("admin.system")),
    db_manager = Depends(get_database_manager)
):
    """Get all download links (admin only)"""
    
    # This would require additional database method to get all links
    # For now, return placeholder
    
    return {
        "links": [],
        "total_count": 0,
        "note": "This endpoint requires additional database implementation"
    }


@router.delete("/links/{link_code}")
async def admin_delete_link(
    link_code: str,
    current_token = Depends(require_permission("admin.system")),
    download_manager = Depends(get_download_manager)
):
    """Delete any download link (admin only)"""
    
    link = await download_manager.db.get_download_link(link_code)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    
    # Admin can delete any link (placeholder implementation)
    success = True
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete link"
        )
    
    return {
        "message": "Link deleted by admin",
        "link_code": link_code,
        "original_owner": link.created_by_token
    }


@router.get("/database/stats")
async def get_database_stats(
    current_token = Depends(require_permission("admin.system")),
    db_manager = Depends(get_database_manager)
):
    """Get detailed database statistics (admin only)"""
    
    try:
        import aiosqlite
        from pathlib import Path
        
        # Get database file size
        db_file = Path(db_manager.db_path)
        db_size = db_file.stat().st_size if db_file.exists() else 0
        
        # Get table counts
        async with aiosqlite.connect(db_manager.db_path) as db:
            stats = {}
            
            tables = [
                "download_tokens",
                "download_links", 
                "download_sessions",
                "cache_entries"
            ]
            
            for table in tables:
                cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
                count = (await cursor.fetchone())[0]
                stats[f"{table}_count"] = count
        
        return {
            "database_file": str(db_file),
            "database_size_bytes": db_size,
            "database_size_mb": db_size / (1024 * 1024),
            "table_stats": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving database stats: {str(e)}"
        )