#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Core Data Models for Download System
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid
import sys
from pathlib import Path
# Add bot directory to path
sys.path.append(str(Path(__file__).parent))

class TokenType(str, Enum):
    """Token types"""
    USER = "user"
    API = "api"
    ADMIN = "admin"


class DownloadType(str, Enum):
    """Download types"""
    STREAM = "stream"
    FAST = "fast"


class LinkType(str, Enum):
    """Link types"""
    FILE = "file"
    CATEGORY = "category"
    COLLECTION = "collection"


class DownloadStatus(str, Enum):
    """Download status"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# API Request/Response Models

class TokenCreateRequest(BaseModel):
    """Request to create a new token"""
    name: str = Field(..., min_length=1, max_length=100)
    permissions: List[str] = Field(default_factory=list)
    expires_hours: Optional[int] = Field(default=24, ge=1, le=8760)  # Max 1 year
    max_usage: Optional[int] = Field(default=None, ge=1)


class TokenResponse(BaseModel):
    """Token response"""
    token_id: str
    token: str
    name: str
    permissions: List[str]
    max_usage: Optional[int]
    type: str = "user"
    is_active: bool = True
    expires_at: Optional[datetime] = None
    created_at: datetime
    usage_count: int = 0
    last_used_at: Optional[datetime] = None


class DownloadLinkCreateRequest(BaseModel):
    """Request to create download link"""
    file_id: int
    download_type: DownloadType = DownloadType.STREAM
    max_downloads: Optional[int] = Field(default=None, ge=1)
    expires_hours: Optional[int] = Field(default=None, ge=1)
    password_protected: bool = False
    password: Optional[str] = Field(default=None, min_length=4)
    allowed_ips: List[str] = Field(default_factory=list)
    bandwidth_limit_mbps: Optional[float] = Field(default=None, ge=0.1)
    webhook_url: Optional[str] = None


class DownloadLinkResponse(BaseModel):
    """Download link response"""
    link_id: str
    link_code: str
    download_url: str
    file_id: int
    download_type: DownloadType
    max_downloads: Optional[int]
    expires_at: Optional[datetime]
    password_protected: bool
    settings: Dict[str, Any]
    created_at: datetime


class FileInfoResponse(BaseModel):
    """File information response"""
    file_id: int
    file_name: str
    file_type: str
    file_size: int
    category_id: int
    category_name: str
    uploaded_at: datetime
    storage_message_id: int


class DownloadProgressResponse(BaseModel):
    """Download progress response"""
    download_id: str
    file_id: int
    status: DownloadStatus
    progress_percentage: float = Field(ge=0, le=100)
    downloaded_bytes: int
    total_bytes: int
    download_speed_mbps: float
    eta_seconds: Optional[int]
    error_message: Optional[str] = None


class DownloadStatsResponse(BaseModel):
    """Download statistics response"""
    link_code: str
    total_downloads: int
    unique_ips: int
    total_bytes_transferred: int
    average_speed_mbps: float
    created_at: datetime
    last_accessed: Optional[datetime]


class SystemHealthResponse(BaseModel):
    """System health response"""
    status: str
    timestamp: datetime
    uptime_seconds: int
    active_downloads: int
    cache_usage_bytes: int
    cache_usage_percentage: float
    available_storage_bytes: int
    telethon_clients_active: int
    error_count_last_hour: int


class SystemMetricsResponse(BaseModel):
    """System metrics response"""
    active_requests: int
    avg_download_speed_mbps: float
    memory_usage_percentage: float
    cpu_usage_percentage: float
    bandwidth_usage_mbps: float
    daily_downloads: int
    daily_active_users: int
    daily_transfer_gb: float


# Database Models (Internal)

class Token(BaseModel):
    """Token model"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    token_hash: str
    name: str
    token_type: TokenType = TokenType.USER
    user_id: Optional[int] = None
    permissions: str = "{}"  # JSON string
    expires_at: Optional[datetime] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    last_used_at: Optional[datetime] = None  # Alias for last_used
    usage_count: int = 0
    max_usage: Optional[int] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        # Sync last_used and last_used_at
        if self.last_used and not self.last_used_at:
            self.last_used_at = self.last_used
        elif self.last_used_at and not self.last_used:
            self.last_used = self.last_used_at


class DownloadLink(BaseModel):
    """Download link model"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    link_code: str
    file_id: int
    download_type: DownloadType = DownloadType.STREAM
    created_by_token: str
    max_downloads: Optional[int] = None
    expires_at: Optional[datetime] = None
    allowed_ips: str = "[]"  # JSON array
    password_hash: Optional[str] = None
    bandwidth_limit_mbps: Optional[float] = None
    webhook_url: Optional[str] = None
    download_count: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    settings: str = "{}"  # JSON string


class DownloadSession(BaseModel):
    """Download session model"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    link_code: str
    file_id: int
    ip_address: str
    user_agent: str
    download_method: str  # "bot_api" or "telethon"
    file_size: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    downloaded_bytes: int = 0
    status: DownloadStatus = DownloadStatus.PENDING
    error_message: Optional[str] = None


class CacheEntry(BaseModel):
    """Cache entry model"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    file_id: int
    cache_path: str
    file_size: int
    access_count: int = 0
    last_access: Optional[datetime] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_valid: bool = True


# Error Models

class APIError(BaseModel):
    """API Error response"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class ValidationError(BaseModel):
    """Validation error response"""
    error: str = "Validation failed"
    details: List[Dict[str, Any]]