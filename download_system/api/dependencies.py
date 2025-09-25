#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastAPI Dependencies
"""

from fastapi import Request, HTTPException, status
import sys
from pathlib import Path
# Add bot directory to path
sys.path.append(str(Path(__file__).parent))
from core.database import DatabaseManager
from core.download_manager import DownloadManager
from core.auth import AuthManager


async def get_database_manager(request: Request) -> DatabaseManager:
    """Get database manager from request state"""
    if not hasattr(request.state, 'db_manager') or not request.state.db_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database manager not available"
        )
    return request.state.db_manager


async def get_download_manager(request: Request) -> DownloadManager:
    """Get download manager from request state"""
    if not hasattr(request.state, 'download_manager') or not request.state.download_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Download manager not available"
        )
    return request.state.download_manager


async def get_auth_manager_from_request(request: Request) -> AuthManager:
    """Get auth manager from request state"""
    if not hasattr(request.state, 'auth_manager') or not request.state.auth_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth manager not available"
        )
    return request.state.auth_manager


async def check_system_ready(request: Request):
    """Check if system is ready to serve requests"""
    if not hasattr(request.state, 'system_ready') or not request.state.system_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System is starting up, please try again later"
        )