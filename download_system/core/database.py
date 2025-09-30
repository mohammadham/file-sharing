#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database Manager for Download System
"""

import aiosqlite
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from config.settings import settings
import sys
from pathlib import Path
# Add bot directory to path
sys.path.append(str(Path(__file__).parent))
from core.models import Token, DownloadLink, DownloadSession, CacheEntry
from core.security_manager import SecurityManager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Advanced database manager for download system"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
        self.db_path = Path(self.db_path)
        self.security_manager = SecurityManager(self.db_path)
        
    async def init_database(self):
        """Initialize database with all necessary tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Enable foreign keys
            await db.execute("PRAGMA foreign_keys = ON")
            
            # Tokens table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS download_tokens (
                    id TEXT PRIMARY KEY,
                    token_hash TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    token_type TEXT NOT NULL DEFAULT 'user',
                    user_id INTEGER,
                    permissions TEXT NOT NULL DEFAULT '{}',
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    usage_count INTEGER DEFAULT 0,
                    max_usage INTEGER
                )
            ''')
            
            # Download links table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS download_links (
                    id TEXT PRIMARY KEY,
                    link_code TEXT UNIQUE NOT NULL,
                    file_id INTEGER NOT NULL,
                    download_type TEXT NOT NULL DEFAULT 'stream',
                    created_by_token TEXT NOT NULL,
                    max_downloads INTEGER,
                    expires_at TIMESTAMP,
                    allowed_ips TEXT DEFAULT '[]',
                    password_hash TEXT,
                    bandwidth_limit_mbps REAL,
                    webhook_url TEXT,
                    download_count INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    settings TEXT DEFAULT '{}',
                    FOREIGN KEY (created_by_token) REFERENCES download_tokens(id)
                )
            ''')
            
            # Download sessions table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS download_sessions (
                    id TEXT PRIMARY KEY,
                    link_code TEXT NOT NULL,
                    file_id INTEGER NOT NULL,
                    ip_address TEXT NOT NULL,
                    user_agent TEXT,
                    download_method TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    downloaded_bytes INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    FOREIGN KEY (link_code) REFERENCES download_links(link_code)
                )
            ''')
            
            # Cache entries table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS cache_entries (
                    id TEXT PRIMARY KEY,
                    file_id INTEGER UNIQUE NOT NULL,
                    cache_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_access TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_valid BOOLEAN DEFAULT 1
                )
            ''')
            
            # Create indexes for performance
            await db.execute('CREATE INDEX IF NOT EXISTS idx_download_tokens_hash ON download_tokens(token_hash)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_download_links_code ON download_links(link_code)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_download_sessions_link ON download_sessions(link_code)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_cache_entries_file ON cache_entries(file_id)')
            
            await db.commit()
            logger.info("Download system database initialized successfully")
        
        # Initialize security tables
        await self.security_manager.init_security_tables()
        logger.info("Security tables initialized successfully")
    
    # Token Management
    
    async def create_token(self, token: Token) -> bool:
        """Create a new token"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute('''
                    INSERT INTO download_tokens (
                        id, token_hash, name, token_type, user_id, permissions,
                        expires_at, max_usage
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    token.id, token.token_hash, token.name, token.token_type.value,
                    token.user_id, token.permissions, token.expires_at, token.max_usage
                ))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Error creating token: {e}")
                return False
    
    async def get_token(self, token_hash: str) -> Optional[Token]:
        """Get token by hash"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM download_tokens 
                WHERE token_hash = ? AND is_active = 1
            ''', (token_hash,))
            row = await cursor.fetchone()
            
            if row:
                return Token(**dict(row))
            return None
    
    async def update_token_usage(self, token_hash: str) -> bool:
        """Update token usage statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                UPDATE download_tokens 
                SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP
                WHERE token_hash = ? AND is_active = 1
            ''', (token_hash,))
            await db.commit()
            return cursor.rowcount > 0
    
    async def deactivate_token(self, token_id: str) -> bool:
        """Deactivate a token"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                UPDATE download_tokens SET is_active = 0 
                WHERE id = ?
            ''', (token_id,))
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_all_tokens(self, limit: int = 100) -> List[Token]:
        """Get all tokens with limit"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT id, token_hash, name, token_type, user_id, permissions,
                       expires_at, max_usage, usage_count, is_active, created_at, last_used
                FROM download_tokens 
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            
            rows = await cursor.fetchall()
            tokens = []
            
            for row in rows:
                token = Token(
                    id=row[0],
                    token_hash=row[1],
                    name=row[2],
                    token_type=row[3],
                    user_id=row[4],
                    permissions=row[5],
                    expires_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    max_usage=row[7],
                    usage_count=row[8] or 0,
                    is_active=bool(row[9]),
                    created_at=datetime.fromisoformat(row[10]) if row[10] else datetime.utcnow(),
                    last_used=datetime.fromisoformat(row[11]) if row[11] else None
                )
                tokens.append(token)
            
            return tokens
    
    # Download Links Management
    
    async def create_download_link(self, link: DownloadLink) -> bool:
        """Create a new download link"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute('''
                    INSERT INTO download_links (
                        id, link_code, file_id, download_type, created_by_token,
                        max_downloads, expires_at, allowed_ips, password_hash,
                        bandwidth_limit_mbps, webhook_url, settings
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    link.id, link.link_code, link.file_id, link.download_type.value,
                    link.created_by_token, link.max_downloads, link.expires_at,
                    link.allowed_ips, link.password_hash, link.bandwidth_limit_mbps,
                    link.webhook_url, link.settings
                ))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Error creating download link: {e}")
                return False
    
    async def get_download_link(self, link_code: str) -> Optional[DownloadLink]:
        """Get download link by code"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM download_links 
                WHERE link_code = ? AND is_active = 1
            ''', (link_code,))
            row = await cursor.fetchone()
            
            if row:
                return DownloadLink(**dict(row))
            return None
    
    async def increment_download_count(self, link_code: str) -> bool:
        """Increment download count"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                UPDATE download_links 
                SET download_count = download_count + 1
                WHERE link_code = ? AND is_active = 1
            ''', (link_code,))
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_user_download_links(self, token_id: str, limit: int = 50) -> List[DownloadLink]:
        """Get download links created by token"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM download_links 
                WHERE created_by_token = ? AND is_active = 1
                ORDER BY created_at DESC LIMIT ?
            ''', (token_id, limit))
            rows = await cursor.fetchall()
            
            return [DownloadLink(**dict(row)) for row in rows]
    
    # Download Sessions
    
    async def create_download_session(self, session: DownloadSession) -> bool:
        """Create download session"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute('''
                    INSERT INTO download_sessions (
                        id, link_code, file_id, ip_address, user_agent,
                        download_method, file_size, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session.id, session.link_code, session.file_id,
                    session.ip_address, session.user_agent, session.download_method,
                    session.file_size, session.status.value
                ))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Error creating download session: {e}")
                return False
    
    async def update_download_session(self, session_id: str, **kwargs) -> bool:
        """Update download session"""
        async with aiosqlite.connect(self.db_path) as db:
            fields = []
            values = []
            
            for key, value in kwargs.items():
                if key in ['downloaded_bytes', 'status', 'error_message', 'completed_at']:
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            if not fields:
                return False
            
            values.append(session_id)
            cursor = await db.execute(f'''
                UPDATE download_sessions 
                SET {', '.join(fields)} WHERE id = ?
            ''', values)
            await db.commit()
            return cursor.rowcount > 0
    
    # Cache Management
    
    async def create_cache_entry(self, entry: CacheEntry) -> bool:
        """Create cache entry"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute('''
                    INSERT OR REPLACE INTO cache_entries (
                        id, file_id, cache_path, file_size, expires_at
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    entry.id, entry.file_id, entry.cache_path,
                    entry.file_size, entry.expires_at
                ))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Error creating cache entry: {e}")
                return False
    
    async def get_cache_entry(self, file_id: int) -> Optional[CacheEntry]:
        """Get cache entry by file_id"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM cache_entries 
                WHERE file_id = ? AND is_valid = 1
                AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            ''', (file_id,))
            row = await cursor.fetchone()
            
            if row:
                return CacheEntry(**dict(row))
            return None
    
    async def update_cache_access(self, file_id: int) -> bool:
        """Update cache access statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                UPDATE cache_entries 
                SET access_count = access_count + 1, last_access = CURRENT_TIMESTAMP
                WHERE file_id = ?
            ''', (file_id,))
            await db.commit()
            return cursor.rowcount > 0
    
    async def cleanup_expired_cache(self) -> int:
        """Cleanup expired cache entries"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                UPDATE cache_entries SET is_valid = 0
                WHERE expires_at IS NOT NULL AND expires_at <= CURRENT_TIMESTAMP
            ''')
            await db.commit()
            return cursor.rowcount
    
    # Statistics and Analytics
    
    async def get_download_stats(self, link_code: str) -> Dict[str, Any]:
        """Get download statistics for link"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get link info
            cursor = await db.execute('''
                SELECT * FROM download_links WHERE link_code = ?
            ''', (link_code,))
            link_row = await cursor.fetchone()
            
            if not link_row:
                return {}
            
            # Get session stats
            cursor = await db.execute('''
                SELECT 
                    COUNT(*) as total_downloads,
                    COUNT(DISTINCT ip_address) as unique_ips,
                    SUM(downloaded_bytes) as total_bytes,
                    AVG(downloaded_bytes / 
                        (CASE WHEN completed_at IS NULL OR started_at IS NULL 
                         THEN 1 
                         ELSE (julianday(completed_at) - julianday(started_at)) * 86400 
                         END)
                    ) as avg_speed_bps
                FROM download_sessions 
                WHERE link_code = ? AND status = 'completed'
            ''', (link_code,))
            stats_row = await cursor.fetchone()
            
            return {
                'link_code': link_code,
                'total_downloads': stats_row[0] or 0,
                'unique_ips': stats_row[1] or 0,
                'total_bytes_transferred': stats_row[2] or 0,
                'average_speed_mbps': (stats_row[3] or 0) / (1024 * 1024),
                'created_at': link_row[14],  # created_at from link
                'last_accessed': None  # Could add this later
            }
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Active downloads
            cursor = await db.execute('''
                SELECT COUNT(*) FROM download_sessions 
                WHERE status IN ('pending', 'downloading')
            ''')
            stats['active_downloads'] = (await cursor.fetchone())[0]
            
            # Cache usage
            cursor = await db.execute('''
                SELECT COUNT(*), SUM(file_size) FROM cache_entries 
                WHERE is_valid = 1
            ''')
            cache_row = await cursor.fetchone()
            stats['cache_entries'] = cache_row[0] or 0
            stats['cache_usage_bytes'] = cache_row[1] or 0
            
            # Daily stats
            cursor = await db.execute('''
                SELECT COUNT(*), COUNT(DISTINCT ip_address), SUM(downloaded_bytes)
                FROM download_sessions 
                WHERE started_at >= datetime('now', '-1 day')
                AND status = 'completed'
            ''')
            daily_row = await cursor.fetchone()
            stats['daily_downloads'] = daily_row[0] or 0
            stats['daily_active_users'] = daily_row[1] or 0
            stats['daily_transfer_bytes'] = daily_row[2] or 0
            
            return stats
    
    # === New Missing Database Functions ===
    
    async def get_expired_tokens(self) -> List[Dict[str, Any]]:
        """Get all expired tokens"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT id, token_hash, name, token_type, user_id, expires_at, created_at,
                       last_used, usage_count, is_active
                FROM download_tokens 
                WHERE expires_at IS NOT NULL AND expires_at < datetime('now')
                ORDER BY expires_at ASC
            ''')
            rows = await cursor.fetchall()
            
            tokens = []
            for row in rows:
                tokens.append({
                    'id': row[0],
                    'token_hash': row[1],
                    'name': row[2],
                    'token_type': row[3],
                    'user_id': row[4],
                    'expires_at': row[5],
                    'created_at': row[6],
                    'last_used': row[7],
                    'usage_count': row[8],
                    'is_active': bool(row[9])
                })
            
            return tokens
    
    async def get_inactive_tokens(self) -> List[Dict[str, Any]]:
        """Get all inactive tokens"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT id, token_hash, name, token_type, user_id, expires_at, created_at,
                       last_used, usage_count, is_active
                FROM download_tokens 
                WHERE is_active = 0
                ORDER BY created_at DESC
            ''')
            rows = await cursor.fetchall()
            
            tokens = []
            for row in rows:
                tokens.append({
                    'id': row[0],
                    'token_hash': row[1], 
                    'name': row[2],
                    'token_type': row[3],
                    'user_id': row[4],
                    'expires_at': row[5],
                    'created_at': row[6],
                    'last_used': row[7],
                    'usage_count': row[8],
                    'is_active': bool(row[9])
                })
            
            return tokens
    
    async def get_unused_tokens(self, days_unused: int = 30) -> List[Dict[str, Any]]:
        """Get tokens that haven't been used for specified days"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT id, token_hash, name, token_type, user_id, expires_at, created_at,
                       last_used, usage_count, is_active
                FROM download_tokens 
                WHERE (last_used IS NULL OR last_used < datetime('now', '-{} days'))
                AND is_active = 1
                ORDER BY created_at ASC
            '''.format(days_unused))
            rows = await cursor.fetchall()
            
            tokens = []
            for row in rows:
                tokens.append({
                    'id': row[0],
                    'token_hash': row[1],
                    'name': row[2],
                    'token_type': row[3],
                    'user_id': row[4],
                    'expires_at': row[5],
                    'created_at': row[6],
                    'last_used': row[7],
                    'usage_count': row[8],
                    'is_active': bool(row[9])
                })
            
            return tokens
    
    async def get_suspicious_activity(self) -> Dict[str, Any]:
        """Detect suspicious token activity"""
        async with aiosqlite.connect(self.db_path) as db:
            suspicious_tokens = []
            
            # High usage tokens (above average)
            cursor = await db.execute('''
                SELECT t.id, t.name, t.usage_count,
                       (SELECT AVG(usage_count) FROM download_tokens WHERE is_active = 1) as avg_usage
                FROM download_tokens t
                WHERE t.is_active = 1 AND t.usage_count > (
                    SELECT AVG(usage_count) * 5 FROM download_tokens WHERE is_active = 1
                )
                ORDER BY t.usage_count DESC
            ''')
            high_usage = await cursor.fetchall()
            
            for row in high_usage:
                suspicious_tokens.append({
                    'token_id': row[0],
                    'name': row[1],
                    'reason': 'High usage pattern',
                    'usage_count': row[2],
                    'average_usage': row[3],
                    'risk_level': 'high'
                })
            
            # Multiple IP usage
            cursor = await db.execute('''
                SELECT t.id, t.name, COUNT(DISTINCT ds.ip_address) as ip_count
                FROM download_tokens t
                JOIN download_sessions ds ON t.id = ds.token_id
                WHERE ds.started_at > datetime('now', '-7 days')
                GROUP BY t.id, t.name
                HAVING COUNT(DISTINCT ds.ip_address) > 10
                ORDER BY ip_count DESC
            ''')
            multi_ip = await cursor.fetchall()
            
            for row in multi_ip:
                suspicious_tokens.append({
                    'token_id': row[0],
                    'name': row[1],
                    'reason': 'Multiple IP addresses',
                    'ip_count': row[2],
                    'risk_level': 'medium'
                })
            
            # Get security events (simplified)
            security_events = [
                {
                    'timestamp': datetime.now().isoformat(),
                    'event': 'High usage detected',
                    'token_id': suspicious_tokens[0]['token_id'] if suspicious_tokens else 'N/A',
                    'details': 'Usage 5x above average'
                }
            ]
            
            return {
                'suspicious_tokens': suspicious_tokens,
                'security_events': security_events,
                'total_suspicious': len(suspicious_tokens),
                'high_risk_count': len([t for t in suspicious_tokens if t.get('risk_level') == 'high']),
                'medium_risk_count': len([t for t in suspicious_tokens if t.get('risk_level') == 'medium'])
            }
    
    async def delete_token_permanently(self, token_id: str) -> bool:
        """Permanently delete a token and its related data"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Delete related sessions first
                await db.execute('DELETE FROM download_sessions WHERE token_id = ?', (token_id,))
                
                # Delete the token
                await db.execute('DELETE FROM download_tokens WHERE id = ?', (token_id,))
                
                await db.commit()
                return True
                
            except Exception as e:
                logger.error(f"Error deleting token permanently: {e}")
                await db.rollback()
                return False
    
    async def update_token_settings(self, token_id: str, settings: Dict[str, Any]) -> bool:
        """Update token settings"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Build dynamic update query
                set_clauses = []
                values = []
                
                if 'name' in settings:
                    set_clauses.append('name = ?')
                    values.append(settings['name'])
                
                if 'expires_at' in settings:
                    set_clauses.append('expires_at = ?')
                    values.append(settings['expires_at'])
                
                if 'is_active' in settings:
                    set_clauses.append('is_active = ?')
                    values.append(int(settings['is_active']))
                
                if 'token_type' in settings:
                    set_clauses.append('token_type = ?')
                    values.append(settings['token_type'])
                
                if 'permissions' in settings:
                    set_clauses.append('permissions = ?')
                    values.append(json.dumps(settings['permissions']))
                
                if not set_clauses:
                    return False
                
                values.append(token_id)
                query = f"UPDATE download_tokens SET {', '.join(set_clauses)} WHERE id = ?"
                
                await db.execute(query, values)
                await db.commit()
                return True
                
            except Exception as e:
                logger.error(f"Error updating token settings: {e}")
                await db.rollback()
                return False
    
    async def get_token_usage_stats(self, token_id: str) -> Dict[str, Any]:
        """Get detailed usage statistics for a specific token"""
        async with aiosqlite.connect(self.db_path) as db:
            # Basic token info
            cursor = await db.execute('''
                SELECT usage_count, last_used, created_at 
                FROM download_tokens WHERE id = ?
            ''', (token_id,))
            token_row = await cursor.fetchone()
            
            if not token_row:
                return {}
            
            # Usage by day (last 30 days)
            cursor = await db.execute('''
                SELECT DATE(started_at) as date, COUNT(*) as requests
                FROM download_sessions 
                WHERE token_id = ? AND started_at > datetime('now', '-30 days')
                GROUP BY DATE(started_at)
                ORDER BY date DESC
            ''', (token_id,))
            daily_usage = await cursor.fetchall()
            
            # Unique IPs
            cursor = await db.execute('''
                SELECT COUNT(DISTINCT ip_address) 
                FROM download_sessions 
                WHERE token_id = ?
            ''', (token_id,))
            unique_ips = (await cursor.fetchone())[0]
            
            # Total bytes transferred
            cursor = await db.execute('''
                SELECT SUM(downloaded_bytes) 
                FROM download_sessions 
                WHERE token_id = ? AND status = 'completed'
            ''', (token_id,))
            total_bytes = (await cursor.fetchone())[0] or 0
            
            return {
                'usage_count': token_row[0],
                'last_used': token_row[1],
                'created_at': token_row[2],
                'daily_usage': [{'date': row[0], 'requests': row[1]} for row in daily_usage],
                'unique_ips': unique_ips,
                'total_bytes_transferred': total_bytes,
                'average_daily_usage': sum(row[1] for row in daily_usage) / max(len(daily_usage), 1)
            }
    
    async def cleanup_expired_data(self, days_old: int = 90) -> Dict[str, int]:
        """Clean up old data from database"""
        async with aiosqlite.connect(self.db_path) as db:
            counts = {}
            
            # Clean old sessions
            cursor = await db.execute('''
                DELETE FROM download_sessions 
                WHERE started_at < datetime('now', '-{} days')
            '''.format(days_old))
            counts['sessions_deleted'] = cursor.rowcount
            
            # Clean invalid cache entries
            cursor = await db.execute('''
                DELETE FROM cache_entries 
                WHERE created_at < datetime('now', '-{} days') OR is_valid = 0
            '''.format(days_old))
            counts['cache_entries_deleted'] = cursor.rowcount
            
            await db.commit()
            return counts
    
    async def export_data_to_format(self, data_type: str, format_type: str) -> str:
        """Export data to specified format"""
        # This is a simplified implementation
        # In production, this would generate actual files
        
        if data_type == 'tokens':
            tokens = await self.get_all_tokens()
            if format_type == 'json':
                return json.dumps(tokens, indent=2, default=str)
            elif format_type == 'csv':
                import csv
                import io
                output = io.StringIO()
                if tokens:
                    fieldnames = tokens[0].keys()
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(tokens)
                return output.getvalue()
        
        return "Export not implemented for this combination"