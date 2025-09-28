#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Download API Routes - Core download functionality
"""

import asyncio
from datetime import datetime
from typing import Optional
from fastapi import (
    APIRouter, Depends, HTTPException, status, Request, 
    BackgroundTasks, Header, Query, Response
)
from fastapi.responses import StreamingResponse, FileResponse
import logging

from core.models import (
    DownloadLinkCreateRequest, DownloadLinkResponse, 
    DownloadProgressResponse, DownloadStatsResponse,
    DownloadType, DownloadStatus
)
from core.auth import get_current_token, require_permission
from api.dependencies import get_download_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/links/create", response_model=DownloadLinkResponse)
async def create_download_link(
    request: DownloadLinkCreateRequest,
    current_token = Depends(require_permission("links.create")),
    download_manager = Depends(get_download_manager)
):
    """Create download link"""
    
    # Verify file exists
    file_info = await download_manager.get_file_info_from_bot_db(request.file_id)
    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Create download link
    link = await download_manager.create_download_link(
        file_id=request.file_id,
        download_type=request.download_type,
        created_by_token=current_token.id,
        max_downloads=request.max_downloads,
        expires_hours=request.expires_hours,
        password=request.password if request.password_protected else None,
        allowed_ips=request.allowed_ips,
        bandwidth_limit_mbps=request.bandwidth_limit_mbps,
        webhook_url=request.webhook_url
    )
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create download link"
        )
    
    # Generate download URL
    from config.settings import settings
    download_url = f"/api/download/{request.download_type.value}/{link.link_code}"
    
    return DownloadLinkResponse(
        link_id=link.id,
        link_code=link.link_code,
        download_url=download_url,
        file_id=request.file_id,
        download_type=request.download_type,
        max_downloads=request.max_downloads,
        expires_at=link.expires_at,
        password_protected=request.password_protected,
        settings={
            "allowed_ips": request.allowed_ips,
            "bandwidth_limit_mbps": request.bandwidth_limit_mbps,
            "webhook_url": request.webhook_url
        },
        created_at=link.created_at
    )


@router.get("/stream/{link_code}")
async def stream_download(
    link_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    password: Optional[str] = Header(None, alias="X-Download-Password")
):
    """Stream download endpoint"""
    
    download_manager: DownloadManager = request.state.download_manager
    
    # Validate access
    allowed, link, error_msg = await download_manager.validate_download_access(
        link_code, request.client.host, password
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_msg
        )
    
    # Get file info
    file_info = await download_manager.get_file_info_from_bot_db(link.file_id)
    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Create download session
    session = await download_manager.create_download_session(
        link_code=link_code,
        file_id=link.file_id,
        ip_address=request.client.host,
        user_agent=request.headers.get('user-agent', ''),
        file_size=file_info['file_size'],
        download_method="telethon_stream"
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create download session"
        )
    
    try:
        # Stream download generator
        async def stream_generator():
            downloaded_bytes = 0
            
            try:
                await download_manager.update_download_progress(
                    session.id, 0, DownloadStatus.DOWNLOADING
                )
                
                async for chunk in download_manager.stream_download(
                    link.file_id,
                    file_info['storage_message_id']
                ):
                    downloaded_bytes += len(chunk)
                    
                    # Update progress periodically
                    if downloaded_bytes % (1024 * 1024) == 0:  # Every MB
                        await download_manager.update_download_progress(
                            session.id, downloaded_bytes
                        )
                    
                    yield chunk
                
                # Mark as completed
                await download_manager.finish_download_session(session.id, True)
                
            except Exception as e:
                logger.error(f"Stream download error: {e}")
                await download_manager.update_download_progress(
                    session.id, downloaded_bytes, DownloadStatus.FAILED, str(e)
                )
                raise
        
        # Set response headers
        headers = {
            'Content-Disposition': f'attachment; filename="{file_info["file_name"]}"',
            'Content-Type': file_info.get('file_type', 'application/octet-stream'),
            'Content-Length': str(file_info['file_size']),
            'Accept-Ranges': 'bytes',
            'X-Download-Session': session.id
        }
        
        return StreamingResponse(
            stream_generator(),
            headers=headers,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        # Mark session as failed
        await download_manager.finish_download_session(session.id, False)
        
        if isinstance(e, HTTPException):
            raise
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Download failed: {str(e)}"
            )


@router.get("/fast/{link_code}")
async def fast_download(
    link_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    password: Optional[str] = Header(None, alias="X-Download-Password")
):
    """Fast download with caching"""
    
    download_manager: DownloadManager = request.state.download_manager
    
    # Validate access
    allowed, link, error_msg = await download_manager.validate_download_access(
        link_code, request.client.host, password
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_msg
        )
    
    # Get file info
    file_info = await download_manager.get_file_info_from_bot_db(link.file_id)
    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Create download session
    session = await download_manager.create_download_session(
        link_code=link_code,
        file_id=link.file_id,
        ip_address=request.client.host,
        user_agent=request.headers.get('user-agent', ''),
        file_size=file_info['file_size'],
        download_method="telethon_cached"
    )
    
    try:
        # Get or create cached file
        cached_file_path = await download_manager.fast_download(
            link.file_id,
            file_info['file_name'],
            file_info['storage_message_id']
        )
        
        if not cached_file_path or not cached_file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cache file"
            )
        
        # Mark session as completed
        await download_manager.finish_download_session(session.id, True)
        
        # Update cache access in background
        background_tasks.add_task(
            download_manager.cache_manager.db.update_cache_access,
            link.file_id
        )
        
        return FileResponse(
            path=cached_file_path,
            filename=file_info['file_name'],
            media_type=file_info.get('file_type', 'application/octet-stream'),
            headers={
                'X-Download-Session': session.id,
                'X-Cache-Status': 'HIT' if cached_file_path.name.startswith(str(link.file_id)) else 'MISS'
            }
        )
        
    except Exception as e:
        # Mark session as failed
        await download_manager.finish_download_session(session.id, False)
        
        if isinstance(e, HTTPException):
            raise
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Fast download failed: {str(e)}"
            )


@router.get("/info/{link_code}")
async def get_download_info(
    link_code: str,
    download_manager = Depends(get_download_manager)
):
    """Get download link information (public endpoint)"""
    
    # Get link without validation (for info only)
    link = await download_manager.db.get_download_link(link_code)
    
    if not link or not link.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    
    # Get file info
    file_info = await download_manager.get_file_info_from_bot_db(link.file_id)
    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    from datetime import datetime
    
    return {
        "link_code": link_code,
        "file_name": file_info['file_name'],
        "file_size": file_info['file_size'],
        "file_type": file_info.get('file_type', 'unknown'),
        "download_type": link.download_type,
        "download_count": link.download_count,
        "max_downloads": link.max_downloads,
        "expires_at": link.expires_at,
        "is_expired": link.expires_at and datetime.utcnow() > link.expires_at,
        "password_protected": bool(link.password_hash),
        "created_at": link.created_at
    }


@router.get("/progress/{session_id}", response_model=DownloadProgressResponse)
async def get_download_progress(
    session_id: str,
    download_manager = Depends(get_download_manager)
):
    """Get download progress"""
    
    # Check in-memory sessions first
    if session_id in download_manager.active_downloads:
        session = download_manager.active_downloads[session_id]
        
        # Calculate progress
        progress_percentage = 0.0
        if session.file_size > 0:
            progress_percentage = (session.downloaded_bytes / session.file_size) * 100
        
        # Calculate speed (simplified)
        speed_mbps = 0.0
        if session.started_at:
            elapsed = (datetime.utcnow() - session.started_at).total_seconds()
            if elapsed > 0:
                speed_bps = session.downloaded_bytes / elapsed
                speed_mbps = speed_bps / (1024 * 1024)
        
        # Calculate ETA
        eta_seconds = None
        if speed_bps > 0:
            remaining_bytes = session.file_size - session.downloaded_bytes
            eta_seconds = int(remaining_bytes / speed_bps)
        
        return DownloadProgressResponse(
            download_id=session_id,
            file_id=session.file_id,
            status=session.status,
            progress_percentage=min(100.0, progress_percentage),
            downloaded_bytes=session.downloaded_bytes,
            total_bytes=session.file_size,
            download_speed_mbps=speed_mbps,
            eta_seconds=eta_seconds,
            error_message=session.error_message
        )
    
    # If not in memory, session might be completed or not exist
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Download session not found or completed"
    )


@router.get("/links", response_model=list[DownloadLinkResponse])
async def get_user_download_links(
    limit: int = Query(default=20, ge=1, le=100),
    current_token = Depends(require_permission("links.read")),
    download_manager = Depends(get_download_manager)
):
    """Get user's download links"""
    
    links = await download_manager.db.get_user_download_links(
        current_token.id, limit
    )
    
    result = []
    for link in links:
        # Generate download URL
        download_url = f"/api/download/{link.download_type.value}/{link.link_code}"
        
        result.append(DownloadLinkResponse(
            link_id=link.id,
            link_code=link.link_code,
            download_url=download_url,
            file_id=link.file_id,
            download_type=link.download_type,
            max_downloads=link.max_downloads,
            expires_at=link.expires_at,
            password_protected=bool(link.password_hash),
            settings={},
            created_at=link.created_at
        ))
    
    return result


@router.get("/stats/{link_code}", response_model=DownloadStatsResponse)
async def get_download_stats(
    link_code: str,
    current_token = Depends(require_permission("links.stats")),
    download_manager = Depends(get_download_manager)
):
    """Get download statistics"""
    
    # Verify user owns this link
    link = await download_manager.db.get_download_link(link_code)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    
    if link.created_by_token != current_token.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get statistics
    stats = await download_manager.get_download_stats(link_code)
    
    return DownloadStatsResponse(
        link_code=link_code,
        total_downloads=stats.get('total_downloads', 0),
        unique_ips=stats.get('unique_ips', 0),
        total_bytes_transferred=stats.get('total_bytes_transferred', 0),
        average_speed_mbps=stats.get('average_speed_mbps', 0.0),
        created_at=stats.get('created_at'),
        last_accessed=stats.get('last_accessed')
    )


@router.get("/links/file/{file_id}")
async def get_file_download_links(
    file_id: int,
    current_token = Depends(require_permission("links.read")),
    download_manager = Depends(get_download_manager)
):
    """Get all download links for a specific file"""
    
    # Get all user's links and filter by file_id
    all_links = await download_manager.db.get_user_download_links(current_token.id, 100)
    file_links = [link for link in all_links if link.file_id == file_id]
    
    if not file_links:
        return {
            "file_id": file_id,
            "links": [],
            "message": "No download links found for this file"
        }
    
    result = []
    for link in file_links:
        # Generate download URL
        download_url = f"/api/download/{link.download_type.value}/{link.link_code}"
        
        # Check if expired
        is_expired = link.expires_at and datetime.utcnow() > link.expires_at
        
        result.append({
            "link_id": link.id,
            "link_code": link.link_code,
            "download_url": download_url,
            "download_type": link.download_type.value,
            "is_active": link.is_active and not is_expired,
            "is_expired": is_expired,
            "download_count": link.download_count,
            "max_downloads": link.max_downloads,
            "expires_at": link.expires_at,
            "password_protected": bool(link.password_hash),
            "created_at": link.created_at
        })
    
    return {
        "file_id": file_id,
        "links": result,
        "total_count": len(result)
    }


@router.delete("/links/{link_code}")
async def delete_download_link(
    link_code: str,
    current_token = Depends(require_permission("links.delete")),
    download_manager = Depends(get_download_manager)
):
    """Delete download link"""
    
    # Verify user owns this link
    link = await download_manager.db.get_download_link(link_code)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    
    if link.created_by_token != current_token.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Deactivate link (for now just mark it as inactive)
    # This would need a database method implementation
    success = True  # Placeholder
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete link"
        )
    
    return {"message": "Download link deleted successfully"}


@router.get("/links/my")
async def get_my_download_links(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_token = Depends(require_permission("links.read")),
    download_manager = Depends(get_download_manager)
):
    """Get all user's download links"""
    
    # Get user's links
    all_links = await download_manager.db.get_user_download_links(current_token.id, limit)
    
    if not all_links:
        return {
            "links": [],
            "total_count": 0,
            "message": "No download links found"
        }
    
    result = []
    for link in all_links:
        # Get file info
        file_info = await download_manager.get_file_info_from_bot_db(link.file_id)
        
        # Generate download URL
        download_url = f"/api/download/{link.download_type.value}/{link.link_code}"
        
        # Check if expired
        is_expired = link.expires_at and datetime.utcnow() > link.expires_at
        
        result.append({
            "link_id": link.id,
            "link_code": link.link_code,
            "download_url": download_url,
            "file_id": link.file_id,
            "file_name": file_info['file_name'] if file_info else "Unknown",
            "file_size": file_info['file_size'] if file_info else 0,
            "download_type": link.download_type.value,
            "is_active": link.is_active and not is_expired,
            "is_expired": is_expired,
            "download_count": link.download_count,
            "max_downloads": link.max_downloads,
            "expires_at": link.expires_at,
            "password_protected": bool(link.password_hash),
            "created_at": link.created_at
        })
    
    return {
        "links": result,
        "total_count": len(result),
        "limit": limit,
        "offset": offset
    }