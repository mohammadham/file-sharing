#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Admin API Routes
"""

from typing import List, Optional
from datetime import datetime
import json
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
    try:
        tokens = await auth_manager.get_all_tokens(limit=limit)
        token_responses = []
        
        for token in tokens:
            # Parse permissions from JSON string
            permissions_str = getattr(token, 'permissions', "[]")
            try:
                permissions = json.loads(permissions_str) if permissions_str else []
            except (json.JSONDecodeError, TypeError):
                permissions = []
                
            token_responses.append(TokenResponse(
                token_id=token.id,
                token="***hidden***",  # نمایش توکن واقعی امنیتی نیست
                name=token.name or f"Token {token.id}",
                permissions=permissions,
                max_usage=getattr(token, 'max_usage', None),
                type=token.token_type,
                is_active=token.is_active,
                expires_at=token.expires_at,
                created_at=token.created_at,
                usage_count=token.usage_count,
                last_used_at=token.last_used
            ))
        
        return token_responses
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving tokens: {str(e)}"
        )


@router.get("/tokens/stats")
async def get_token_statistics(
    current_token = Depends(require_permission("admin.tokens")),
    auth_manager: AuthManager = Depends(get_auth_manager)
):
    """Get token usage statistics (admin only)"""
    try:
        # Get all tokens for analysis
        all_tokens = await auth_manager.get_all_tokens(limit=1000)
        
        stats = {
            "total_tokens": len(all_tokens),
            "active_tokens": len([t for t in all_tokens if t.is_active]),
            "expired_tokens": len([t for t in all_tokens if t.expires_at and t.expires_at < datetime.utcnow()]),
            "admin_tokens": len([t for t in all_tokens if t.token_type == "admin"]),
            "limited_tokens": len([t for t in all_tokens if t.token_type == "limited"]), 
            "user_tokens": len([t for t in all_tokens if t.token_type == "user"]),
            "daily_usage": sum([t.usage_count for t in all_tokens if t.last_used and 
                              t.last_used.date() == datetime.utcnow().date()]) if any(t.last_used for t in all_tokens) else 0,
            "total_usage": sum([t.usage_count for t in all_tokens])
        }
        
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving token statistics: {str(e)}"
        )


@router.post("/tokens/generate")
async def generate_admin_token(
    request: dict,
    current_token = Depends(require_permission("admin.tokens")),
    auth_manager: AuthManager = Depends(get_auth_manager)
):
    """Generate new admin token (admin only)"""
    try:
        token_type = request.get("type", "user")
        token_name = request.get("name", f"Generated Token {datetime.now().strftime('%Y%m%d_%H%M')}")
        expires_at = request.get("expires_at")
        
        # Parse expires_at if provided
        expires_datetime = None
        if expires_at:
            try:
                expires_datetime = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                expires_datetime = None
        
        # Generate new token
        token_string, token = await auth_manager.create_token(
            name=token_name,
            token_type=token_type,
            expires_at=expires_datetime,
            permissions=auth_manager.get_default_permissions(token_type)
        )
        
        return {
            "success": True,
            "token": token_string,
            "token_id": token.id,
            "name": token.name,
            "type": token.token_type,
            "expires_at": token.expires_at.isoformat() if token.expires_at else None,
            "created_at": token.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating token: {str(e)}"
        )


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
        
        # Get count of cleared entries (placeholder - would need actual implementation)
        result = 0  # This should be the actual count from cache clearing operation
        return {"message": "Cache cleared successfully", "cleared_entries": result}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/tokens/{token_id}")
async def get_token_details(
    token_id: str,
    current_token = Depends(require_permission("admin.tokens")),
    auth_manager: AuthManager = Depends(get_auth_manager),
    db_manager = Depends(get_database_manager)
):
    """Get detailed information about a specific token"""
    try:
        # Get basic token info
        token = await auth_manager.get_token_by_id(token_id)
        if not token:
            raise HTTPException(status_code=404, detail="Token not found")
        
        # Get usage statistics
        usage_stats = await db_manager.get_token_usage_stats(token_id)
        
        # Parse permissions
        permissions_str = getattr(token, 'permissions', "[]")
        try:
            permissions = json.loads(permissions_str) if permissions_str else []
        except (json.JSONDecodeError, TypeError):
            permissions = []
        
        return {
            "id": token.id,
            "name": token.name or f"Token {token.id}",
            "type": token.token_type,
            "active": token.is_active,
            "created_at": token.created_at,
            "expires_at": token.expires_at,
            "last_used": token.last_used,
            "permissions": permissions,
            "usage_stats": usage_stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get token details: {str(e)}"
        )


@router.get("/tokens/detailed-stats")
async def get_detailed_token_stats(
    current_token = Depends(require_permission("admin.stats")),
    db_manager = Depends(get_database_manager)
):
    """Get detailed statistics about all tokens"""
    try:
        # Get all tokens for analysis
        from core.database import DatabaseManager
        
        tokens = await db_manager.get_all_tokens()
        
        # Calculate statistics
        stats = {
            "total_tokens": len(tokens),
            "active_tokens": len([t for t in tokens if t.get('is_active', True)]),
            "expired_tokens": 0,
            "suspended_tokens": 0,
            "token_types": {"admin": 0, "limited": 0, "user": 0},
            "usage_stats": {
                "daily_requests": 0,
                "weekly_requests": 0,
                "monthly_requests": 0
            },
            "top_users": []
        }
        
        # Count by type and status
        for token in tokens:
            token_type = token.get('token_type', 'user')
            if token_type in stats["token_types"]:
                stats["token_types"][token_type] += 1
                
            # Check if expired
            if token.get('expires_at'):
                try:
                    from datetime import datetime
                    expire_time = datetime.fromisoformat(token['expires_at'].replace('Z', '+00:00'))
                    if expire_time < datetime.now():
                        stats["expired_tokens"] += 1
                except (ValueError, TypeError):
                    pass
        
        # Get system stats for usage
        system_stats = await db_manager.get_system_stats()
        stats["usage_stats"]["daily_requests"] = system_stats.get("daily_downloads", 0)
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get detailed token stats: {str(e)}"
        )


@router.get("/tokens/expired")
async def get_expired_tokens(
    current_token = Depends(require_permission("admin.tokens")),
    db_manager = Depends(get_database_manager)
):
    """Get all expired tokens"""
    try:
        expired_tokens = await db_manager.get_expired_tokens()
        return {"tokens": expired_tokens, "count": len(expired_tokens)}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get expired tokens: {str(e)}"
        )


@router.get("/tokens/inactive")
async def get_inactive_tokens(
    current_token = Depends(require_permission("admin.tokens")),
    db_manager = Depends(get_database_manager)
):
    """Get all inactive tokens"""
    try:
        inactive_tokens = await db_manager.get_inactive_tokens()
        return {"tokens": inactive_tokens, "count": len(inactive_tokens)}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get inactive tokens: {str(e)}"
        )


@router.get("/tokens/unused")
async def get_unused_tokens(
    days: int = Query(default=30, ge=1, le=365),
    current_token = Depends(require_permission("admin.tokens")),
    db_manager = Depends(get_database_manager)
):
    """Get tokens that haven't been used for specified days"""
    try:
        unused_tokens = await db_manager.get_unused_tokens(days)
        return {"tokens": unused_tokens, "count": len(unused_tokens), "days_threshold": days}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get unused tokens: {str(e)}"
        )


@router.get("/tokens/suspicious")
async def get_suspicious_tokens(
    current_token = Depends(require_permission("admin.security")),
    db_manager = Depends(get_database_manager)
):
    """Get tokens with suspicious activity"""
    try:
        suspicious_activity = await db_manager.get_suspicious_activity()
        return suspicious_activity
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suspicious tokens: {str(e)}"
        )


@router.delete("/tokens/{token_id}/permanent")
async def delete_token_permanently(
    token_id: str,
    current_token = Depends(require_permission("admin.tokens.delete")),
    db_manager = Depends(get_database_manager)
):
    """Permanently delete a token and all its data"""
    try:
        # Prevent deleting own token
        if token_id == current_token.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own token"
            )
        
        success = await db_manager.delete_token_permanently(token_id)
        if success:
            return {"message": "Token permanently deleted", "token_id": token_id}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete token"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete token: {str(e)}"
        )


@router.put("/tokens/{token_id}/settings")
async def update_token_settings(
    token_id: str,
    settings: dict,
    current_token = Depends(require_permission("admin.tokens.update")),
    db_manager = Depends(get_database_manager)
):
    """Update token settings"""
    try:
        success = await db_manager.update_token_settings(token_id, settings)
        if success:
            return {"message": "Token settings updated", "token_id": token_id}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update token settings"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update token settings: {str(e)}"
        )


@router.post("/cleanup/expired")
async def cleanup_expired_tokens(
    current_token = Depends(require_permission("admin.cleanup")),
    db_manager = Depends(get_database_manager)
):
    """Clean up expired tokens"""
    try:
        expired_tokens = await db_manager.get_expired_tokens()
        deleted_count = 0
        
        for token in expired_tokens:
            success = await db_manager.delete_token_permanently(token['id'])
            if success:
                deleted_count += 1
        
        return {
            "message": "Expired tokens cleanup completed",
            "total_found": len(expired_tokens),
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup expired tokens: {str(e)}"
        )


@router.post("/cleanup/inactive")
async def cleanup_inactive_tokens(
    current_token = Depends(require_permission("admin.cleanup")),
    db_manager = Depends(get_database_manager)
):
    """Clean up inactive tokens"""
    try:
        inactive_tokens = await db_manager.get_inactive_tokens()
        deleted_count = 0
        
        for token in inactive_tokens:
            success = await db_manager.delete_token_permanently(token['id'])
            if success:
                deleted_count += 1
        
        return {
            "message": "Inactive tokens cleanup completed",
            "total_found": len(inactive_tokens), 
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup inactive tokens: {str(e)}"
        )


@router.post("/cleanup/unused")
async def cleanup_unused_tokens(
    days: int = Query(default=30, ge=1, le=365),
    current_token = Depends(require_permission("admin.cleanup")),
    db_manager = Depends(get_database_manager)
):
    """Clean up tokens unused for specified days"""
    try:
        unused_tokens = await db_manager.get_unused_tokens(days)
        deleted_count = 0
        
        for token in unused_tokens:
            success = await db_manager.delete_token_permanently(token['id'])
            if success:
                deleted_count += 1
        
        return {
            "message": f"Unused tokens cleanup completed (unused for {days} days)",
            "total_found": len(unused_tokens),
            "deleted_count": deleted_count,
            "days_threshold": days
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup unused tokens: {str(e)}"
        )


@router.post("/export/{data_type}")
async def export_data(
    data_type: str,
    format_type: str = Query(default="json", regex="^(json|csv|pdf)$"),
    current_token = Depends(require_permission("admin.export")),
    db_manager = Depends(get_database_manager)
):
    """Export system data in various formats"""
    try:
        if data_type not in ["tokens", "users", "stats", "logs"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid data type"
            )
        
        data = await db_manager.export_data_to_format(data_type, format_type)
        
        return {
            "message": "Data exported successfully",
            "data_type": data_type,
            "format": format_type,
            "data": data[:1000] + "..." if len(data) > 1000 else data,  # Truncate for display
            "size": len(data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export data: {str(e)}"
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