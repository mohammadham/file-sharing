#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enterprise Download System Settings
"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Basic App Settings
    APP_NAME: str = "Enterprise Telegram Download System"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # API Settings
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8001, env="API_PORT")
    API_PREFIX: str = "/api"
    
    # Security
    SECRET_KEY: str = Field(default="your-super-secret-key-change-this", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, env="ACCESS_TOKEN_EXPIRE_MINUTES")  # 24 hours
    
    # Database
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./download_system.db", env="DATABASE_URL")
    
    # Redis Cache
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Telegram Settings (from bot)
    BOT_TOKEN: str = Field(default="",env="BOT_TOKEN")
    STORAGE_CHANNEL_ID: int = Field(default=0,env="STORAGE_CHANNEL_ID")
    
    # Telethon Settings
    TELETHON_API_ID: int = Field(default=0,env="TELETHON_API_ID")
    TELETHON_API_HASH: str = Field(default="",env="TELETHON_API_HASH")
    TELETHON_SESSION_DIR: str = Field(default="./sessions", env="TELETHON_SESSION_DIR")
    
    # File Download Settings
    MAX_FILE_SIZE_BOT_API: int = Field(default=50 * 1024 * 1024)  # 50MB
    MAX_FILE_SIZE_TELETHON: int = Field(default=2 * 1024 * 1024 * 1024)  # 2GB
    CHUNK_SIZE: int = Field(default=1024 * 1024)  # 1MB chunks
    
    # Cache Settings
    CACHE_DIR: str = Field(default="./cache", env="CACHE_DIR")
    MAX_CACHE_SIZE: int = Field(default=5 * 1024 * 1024 * 1024)  # 5GB
    CACHE_TTL_HOURS: int = Field(default=24, env="CACHE_TTL_HOURS")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    MAX_CONCURRENT_DOWNLOADS: int = Field(default=10, env="MAX_CONCURRENT_DOWNLOADS")
    
    # Monitoring
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: Optional[str] = Field(default="logs/download_system.log", env="LOG_FILE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True


# Global settings instance
settings = Settings()

# Create necessary directories
Path(settings.CACHE_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.TELETHON_SESSION_DIR).mkdir(parents=True, exist_ok=True)
if settings.LOG_FILE:
    Path(settings.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)