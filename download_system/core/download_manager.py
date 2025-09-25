#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Advanced Download Manager with Telethon Support
"""

import asyncio
import aiofiles
import hashlib
import logging
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, AsyncGenerator
from telethon import TelegramClient
from telethon.tl.types import DocumentAttributeFilename, Document
from telethon.errors import FloodWaitError
import sys
from pathlib import Path
# Add bot directory to path
sys.path.append(str(Path(__file__).parent))
from config.settings import settings
from core.models import (
    DownloadLink, DownloadSession, DownloadType, DownloadStatus,
    CacheEntry
)
from core.database import DatabaseManager
from core.telethon_manager import AdvancedTelethonClientManager

logger = logging.getLogger(__name__)


class CacheManager:
    """Advanced file caching system"""
    
    def __init__(self, database: DatabaseManager):
        self.db = database
        self.cache_dir = Path(settings.CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_cache_size = settings.MAX_CACHE_SIZE
    
    def _get_cache_path(self, file_id: int, file_name: str) -> Path:
        """Generate cache file path"""
        # Create hash of file_id and name for unique cache path
        hash_input = f"{file_id}_{file_name}".encode()
        file_hash = hashlib.md5(hash_input).hexdigest()[:16]
        
        # Preserve original extension
        extension = Path(file_name).suffix
        cache_filename = f"{file_id}_{file_hash}{extension}"
        
        return self.cache_dir / cache_filename
    
    async def get_cached_file(self, file_id: int) -> Optional[CacheEntry]:
        """Get cached file if available and valid"""
        cache_entry = await self.db.get_cache_entry(file_id)
        
        if cache_entry:
            cache_path = Path(cache_entry.cache_path)
            
            # Check if file exists and is valid
            if cache_path.exists() and cache_path.stat().st_size > 0:
                # Update access statistics
                await self.db.update_cache_access(file_id)
                return cache_entry
            else:
                # Mark as invalid
                cache_entry.is_valid = False
                logger.warning(f"Cache file missing or invalid: {cache_path}")
        
        return None
    
    async def cache_file(
        self, 
        file_id: int, 
        file_name: str, 
        file_data: bytes
    ) -> Optional[CacheEntry]:
        """Cache file data"""
        try:
            # Check cache space
            await self._cleanup_cache_if_needed(len(file_data))
            
            # Generate cache path
            cache_path = self._get_cache_path(file_id, file_name)
            
            # Write file to cache
            async with aiofiles.open(cache_path, 'wb') as f:
                await f.write(file_data)
            
            # Calculate expiration
            expires_at = datetime.utcnow() + timedelta(hours=settings.CACHE_TTL_HOURS)
            
            # Create cache entry
            cache_entry = CacheEntry(
                file_id=file_id,
                cache_path=str(cache_path),
                file_size=len(file_data),
                created_at=datetime.utcnow(),
                expires_at=expires_at
            )
            
            # Save to database
            success = await self.db.create_cache_entry(cache_entry)
            if success:
                logger.info(f"File cached: {file_name} ({len(file_data)} bytes)")
                return cache_entry
            
        except Exception as e:
            logger.error(f"Error caching file {file_name}: {e}")
        
        return None
    
    async def _cleanup_cache_if_needed(self, new_file_size: int):
        """Cleanup cache if needed to make space"""
        # Get current cache usage
        total_size = sum(
            Path(entry.cache_path).stat().st_size 
            for entry in await self._get_valid_cache_entries()
            if Path(entry.cache_path).exists()
        )
        
        # Check if cleanup needed
        if total_size + new_file_size > self.max_cache_size:
            await self._perform_cache_cleanup()
    
    async def _get_valid_cache_entries(self) -> list[CacheEntry]:
        """Get all valid cache entries"""
        # This would need to be implemented in database manager
        # For now, return empty list
        return []
    
    async def _perform_cache_cleanup(self):
        """Perform LRU cache cleanup"""
        logger.info("Performing cache cleanup...")
        cleaned_count = await self.db.cleanup_expired_cache()
        logger.info(f"Cleaned up {cleaned_count} expired cache entries")


class DownloadManager:
    """Advanced download manager"""
    
    def __init__(self, database: DatabaseManager):
        self.db = database
        self.telethon_manager = AdvancedTelethonClientManager()
        self.cache_manager = CacheManager(database)
        self.active_downloads: Dict[str, DownloadSession] = {}
    
    def generate_link_code(self, length: int = 12) -> str:
        """Generate unique link code"""
        return secrets.token_urlsafe(length)[:length]
    
    async def create_download_link(
        self,
        file_id: int,
        download_type: DownloadType,
        created_by_token: str,
        **settings
    ) -> Optional[DownloadLink]:
        """Create new download link"""
        
        # Generate unique link code
        link_code = self.generate_link_code()
        
        # Hash password if provided
        password_hash = None
        if settings.get('password'):
            from core.auth import pwd_context
            password_hash = pwd_context.hash(settings['password'])
        
        # Calculate expiration
        expires_at = None
        if settings.get('expires_hours'):
            expires_at = datetime.utcnow() + timedelta(hours=settings['expires_hours'])
        
        # Create download link
        link = DownloadLink(
            link_code=link_code,
            file_id=file_id,
            download_type=download_type,
            created_by_token=created_by_token,
            max_downloads=settings.get('max_downloads'),
            expires_at=expires_at,
            allowed_ips=str(settings.get('allowed_ips', [])),
            password_hash=password_hash,
            bandwidth_limit_mbps=settings.get('bandwidth_limit_mbps'),
            webhook_url=settings.get('webhook_url'),
            settings=str(settings),
            created_at=datetime.utcnow()
        )
        
        # Save to database
        success = await self.db.create_download_link(link)
        if success:
            logger.info(f"Created download link: {link_code} for file {file_id}")
            return link
        
        return None
    
    async def validate_download_access(
        self, 
        link_code: str, 
        ip_address: str,
        password: Optional[str] = None
    ) -> tuple[bool, Optional[DownloadLink], Optional[str]]:
        """Validate download access"""
        
        # Get download link
        link = await self.db.get_download_link(link_code)
        if not link:
            return False, None, "Link not found"
        
        # Check if link is active
        if not link.is_active:
            return False, link, "Link is inactive"
        
        # Check expiration
        if link.expires_at and datetime.utcnow() > link.expires_at:
            return False, link, "Link has expired"
        
        # Check download limit
        if link.max_downloads and link.download_count >= link.max_downloads:
            return False, link, "Download limit reached"
        
        # Check IP restrictions
        if link.allowed_ips and link.allowed_ips != "[]":
            import json
            allowed_ips = json.loads(link.allowed_ips)
            if ip_address not in allowed_ips:
                return False, link, "IP address not allowed"
        
        # Check password
        if link.password_hash:
            if not password:
                return False, link, "Password required"
            
            from core.auth import pwd_context
            if not pwd_context.verify(password, link.password_hash):
                return False, link, "Invalid password"
        
        return True, link, None
    
    async def get_file_info_from_bot_db(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Get file information from bot database"""
        try:
            # Connect to bot database
            bot_db_path = Path("/app/bot/bot_database.db")
            
            if not bot_db_path.exists():
                logger.error("Bot database not found")
                return None
            
            import aiosqlite
            async with aiosqlite.connect(bot_db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT f.*, c.name as category_name 
                    FROM files f
                    LEFT JOIN categories c ON f.category_id = c.id
                    WHERE f.id = ?
                ''', (file_id,))
                row = await cursor.fetchone()
                
                if row:
                    return dict(row)
        
        except Exception as e:
            logger.error(f"Error getting file info from bot DB: {e}")
        
        return None
    
    async def stream_download(
        self,
        file_id: int,
        storage_message_id: int,
        chunk_size: int = None
    ) -> AsyncGenerator[bytes, None]:
        """Stream download file using Telethon"""
        
        chunk_size = chunk_size or settings.CHUNK_SIZE
        
        try:
            # Get best available Telethon client
            client = self.telethon_manager.get_best_available_client()
            
            if not client:
                # Try to get any available client
                client = await self.telethon_manager.get_client("default")
                
                if not client:
                    raise Exception("No active Telethon clients available. Please configure and login to a Telethon client.")
            
            # Get file from storage channel
            channel_id = settings.STORAGE_CHANNEL_ID
            message = await client.get_messages(channel_id, ids=storage_message_id)
            
            if not message or not message.media:
                raise Exception("File not found in storage channel")
            
            # Stream download
            async for chunk in client.iter_download(message.media, chunk_size=chunk_size):
                yield chunk
                
        except FloodWaitError as e:
            logger.error(f"Rate limited by Telegram: {e.seconds} seconds")
            raise Exception(f"Rate limited. Please try again in {e.seconds} seconds")
        
        except Exception as e:
            logger.error(f"Error in stream download: {e}")
            raise
    
    async def fast_download(
        self,
        file_id: int,
        file_name: str,
        storage_message_id: int
    ) -> Optional[Path]:
        """Fast download with caching"""
        
        # Check cache first
        cached_file = await self.cache_manager.get_cached_file(file_id)
        if cached_file and Path(cached_file.cache_path).exists():
            logger.info(f"Serving file from cache: {file_name}")
            return Path(cached_file.cache_path)
        
        try:
            # Download file data
            file_data = b""
            async for chunk in self.stream_download(file_id, storage_message_id):
                file_data += chunk
            
            # Cache the file
            cache_entry = await self.cache_manager.cache_file(file_id, file_name, file_data)
            
            if cache_entry:
                return Path(cache_entry.cache_path)
            else:
                # Fallback: save to temp file
                temp_path = self.cache_manager.cache_dir / f"temp_{file_id}_{int(time.time())}"
                async with aiofiles.open(temp_path, 'wb') as f:
                    await f.write(file_data)
                return temp_path
                
        except Exception as e:
            logger.error(f"Error in fast download: {e}")
            raise
    
    async def create_download_session(
        self,
        link_code: str,
        file_id: int,
        ip_address: str,
        user_agent: str,
        file_size: int,
        download_method: str
    ) -> Optional[DownloadSession]:
        """Create download session for tracking"""
        
        session = DownloadSession(
            link_code=link_code,
            file_id=file_id,
            ip_address=ip_address,
            user_agent=user_agent,
            download_method=download_method,
            file_size=file_size,
            started_at=datetime.utcnow()
        )
        
        success = await self.db.create_download_session(session)
        if success:
            self.active_downloads[session.id] = session
            return session
        
        return None
    
    async def update_download_progress(
        self,
        session_id: str,
        downloaded_bytes: int,
        status: DownloadStatus = None,
        error_message: str = None
    ):
        """Update download progress"""
        
        update_data = {'downloaded_bytes': downloaded_bytes}
        
        if status:
            update_data['status'] = status.value
        
        if error_message:
            update_data['error_message'] = error_message
        
        if status == DownloadStatus.COMPLETED:
            update_data['completed_at'] = datetime.utcnow()
        
        await self.db.update_download_session(session_id, **update_data)
        
        # Update in-memory session
        if session_id in self.active_downloads:
            session = self.active_downloads[session_id]
            session.downloaded_bytes = downloaded_bytes
            if status:
                session.status = status
            if error_message:
                session.error_message = error_message
    
    async def finish_download_session(self, session_id: str, success: bool = True):
        """Finish download session"""
        
        if session_id in self.active_downloads:
            session = self.active_downloads[session_id]
            
            status = DownloadStatus.COMPLETED if success else DownloadStatus.FAILED
            await self.update_download_progress(session_id, session.downloaded_bytes, status)
            
            # Increment link download count
            await self.db.increment_download_count(session.link_code)
            
            # Remove from active downloads
            del self.active_downloads[session_id]
            
            logger.info(f"Download session finished: {session_id} (success: {success})")
    
    async def get_download_stats(self, link_code: str) -> Dict[str, Any]:
        """Get comprehensive download statistics"""
        return await self.db.get_download_stats(link_code)
    
    async def cleanup_old_sessions(self):
        """Cleanup old download sessions"""
        # This would clean up sessions older than X hours
        # Implementation depends on requirements
        pass
    
    async def shutdown(self):
        """Shutdown download manager"""
        await self.telethon_manager.disconnect_all()
        logger.info("Download manager shut down")