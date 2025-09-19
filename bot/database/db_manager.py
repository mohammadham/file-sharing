#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database Manager - Handles all database operations
"""

import aiosqlite
import logging
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import shutil
from datetime import datetime

from config.settings import DB_PATH, BACKUP_PATH
from models.database_models import Category, File, UserSession, Link

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database operations manager"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.backup_path = BACKUP_PATH
        
    async def init_database(self):
        """Initialize SQLite database with necessary tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Categories table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    parent_id INTEGER,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES categories (id)
                )
            ''')
            
            # Files table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT NOT NULL,
                    file_type TEXT,
                    file_size INTEGER,
                    category_id INTEGER,
                    telegram_file_id TEXT,
                    storage_message_id INTEGER,
                    uploaded_by INTEGER,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                )
            ''')
            
            # User sessions table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    user_id INTEGER PRIMARY KEY,
                    current_category INTEGER,
                    action_state TEXT,
                    temp_data TEXT,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Links table for share links
            await db.execute('''
                CREATE TABLE IF NOT EXISTS links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    short_code TEXT UNIQUE NOT NULL,
                    link_type TEXT NOT NULL DEFAULT 'file',
                    target_id INTEGER,
                    target_ids TEXT,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    title TEXT DEFAULT '',
                    description TEXT DEFAULT ''
                )
            ''')
            
            # Create index for short_code lookup
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_links_short_code ON links(short_code)
            ''')
            
            # Create index for link_type lookup  
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_links_type ON links(link_type)
            ''')
            
            # Create default categories if not exist
            categories_count = await db.execute('SELECT COUNT(*) FROM categories')
            count = await categories_count.fetchone()
            
            if count[0] == 0:
                await self._create_default_categories(db)
            
            await db.commit()
            logger.info("Database initialized successfully")
    
    async def _create_default_categories(self, db):
        """Create default root categories"""
        await db.execute('''
            INSERT INTO categories (name, parent_id, description) 
            VALUES ('📁 فایل‌ها', NULL, 'دسته بندی اصلی فایل‌ها')
        ''')
        
        await db.execute('''
            INSERT INTO categories (name, parent_id, description) 
            VALUES ('🎵 موزیک', 1, 'فایل‌های صوتی و موزیک')
        ''')
        
        await db.execute('''
            INSERT INTO categories (name, parent_id, description) 
            VALUES ('🎬 ویدیو', 1, 'فایل‌های ویدیویی')
        ''')
        
        await db.execute('''
            INSERT INTO categories (name, parent_id, description) 
            VALUES ('📄 اسناد', 1, 'فایل‌های متنی و اسناد')
        ''')
    
    # Category operations
    async def get_categories(self, parent_id: Optional[int] = None) -> List[Category]:
        """Get categories by parent_id"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if parent_id is None:
                cursor = await db.execute('''
                    SELECT * FROM categories WHERE parent_id IS NULL ORDER BY name
                ''')
            else:
                cursor = await db.execute('''
                    SELECT * FROM categories WHERE parent_id = ? ORDER BY name
                ''', (parent_id,))
            
            rows = await cursor.fetchall()
            return [Category.from_dict(dict(row)) for row in rows]
    
    async def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Get category by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM categories WHERE id = ?
            ''', (category_id,))
            row = await cursor.fetchone()
            return Category.from_dict(dict(row)) if row else None
    
    async def create_category(self, name: str, parent_id: Optional[int] = None, description: str = "") -> int:
        """Create new category"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO categories (name, parent_id, description)
                VALUES (?, ?, ?)
            ''', (name, parent_id, description))
            await db.commit()
            return cursor.lastrowid
    
    async def delete_category(self, category_id: int) -> bool:
        """Delete category and move its files to parent category"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get category info
            category = await self.get_category_by_id(category_id)
            if not category:
                return False
            
            # Move files to parent category
            parent_id = category.parent_id or 1
            await db.execute('''
                UPDATE files SET category_id = ? WHERE category_id = ?
            ''', (parent_id, category_id))
            
            # Move subcategories to parent
            await db.execute('''
                UPDATE categories SET parent_id = ? WHERE parent_id = ?
            ''', (parent_id, category_id))
            
            # Delete the category
            await db.execute('DELETE FROM categories WHERE id = ?', (category_id,))
            await db.commit()
            return True
    
    async def update_category(self, category_id: int, name: str = None, description: str = None) -> bool:
        """Update category information"""
        async with aiosqlite.connect(self.db_path) as db:
            fields = []
            values = []
            
            if name is not None:
                fields.append("name = ?")
                values.append(name)
            
            if description is not None:
                fields.append("description = ?")
                values.append(description)
            
            if not fields:
                return False
            
            values.append(category_id)
            await db.execute(f'''
                UPDATE categories SET {', '.join(fields)} WHERE id = ?
            ''', values)
            await db.commit()
            return True
    
    # File operations
    async def get_files(self, category_id: int, limit: int = 20, offset: int = 0) -> List[File]:
        """Get files in category"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM files WHERE category_id = ? 
                ORDER BY uploaded_at DESC LIMIT ? OFFSET ?
            ''', (category_id, limit, offset))
            rows = await cursor.fetchall()
            return [File.from_dict(dict(row)) for row in rows]
    
    async def get_file_by_id(self, file_id: int) -> Optional[File]:
        """Get file by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM files WHERE id = ?
            ''', (file_id,))
            row = await cursor.fetchone()
            return File.from_dict(dict(row)) if row else None
    
    async def save_file(self, file_data: File) -> int:
        """Save file metadata"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO files (
                    file_name, file_type, file_size, category_id,
                    telegram_file_id, storage_message_id, uploaded_by, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_data.file_name,
                file_data.file_type,
                file_data.file_size,
                file_data.category_id,
                file_data.telegram_file_id,
                file_data.storage_message_id,
                file_data.uploaded_by,
                file_data.description
            ))
            await db.commit()
            return cursor.lastrowid
    
    async def delete_file(self, file_id: int) -> bool:
        """Delete file from database"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('DELETE FROM files WHERE id = ?', (file_id,))
            await db.commit()
            return cursor.rowcount > 0
    
    async def update_file(self, file_id: int, **kwargs) -> bool:
        """Update file information"""
        async with aiosqlite.connect(self.db_path) as db:
            fields = []
            values = []
            
            allowed_fields = ['file_name', 'description', 'category_id']
            for key, value in kwargs.items():
                if key in allowed_fields:
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            if not fields:
                return False
            
            values.append(file_id)
            await db.execute(f'''
                UPDATE files SET {', '.join(fields)} WHERE id = ?
            ''', values)
            await db.commit()
            return True
    
    async def search_files(self, query: str, limit: int = 10) -> List[Dict]:
        """Search files by name or description"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT f.*, c.name as category_name 
                FROM files f 
                JOIN categories c ON f.category_id = c.id
                WHERE f.file_name LIKE ? OR f.description LIKE ?
                ORDER BY f.uploaded_at DESC LIMIT ?
            ''', (f'%{query}%', f'%{query}%', limit))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # User session operations
    async def get_user_session(self, user_id: int) -> UserSession:
        """Get user session data"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM user_sessions WHERE user_id = ?
            ''', (user_id,))
            row = await cursor.fetchone()
            
            if row:
                return UserSession.from_dict(dict(row))
            else:
                # Create new session
                session = UserSession(user_id=user_id)
                session_data = session.to_dict()
                session_data.pop('user_id', None)  # Remove user_id to avoid duplicate
                await self.update_user_session(user_id, **session_data)
                return session
    
    async def update_user_session(self, user_id: int, **kwargs):
        """Update user session"""
        async with aiosqlite.connect(self.db_path) as db:
            fields = []
            values = []
            
            allowed_fields = ['current_category', 'action_state', 'temp_data']
            for key, value in kwargs.items():
                if key in allowed_fields:
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            if fields:
                values.append(user_id)
                # Use UPDATE instead of INSERT OR REPLACE to preserve existing data
                await db.execute(f'''
                    UPDATE user_sessions 
                    SET {', '.join(fields)}, last_activity = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', values)
                await db.commit()
    
    # Statistics
    async def get_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Files count
            cursor = await db.execute('SELECT COUNT(*) FROM files')
            stats['files_count'] = (await cursor.fetchone())[0]
            
            # Categories count
            cursor = await db.execute('SELECT COUNT(*) FROM categories')
            stats['categories_count'] = (await cursor.fetchone())[0]
            
            # Users count
            cursor = await db.execute('SELECT COUNT(*) FROM user_sessions')
            stats['users_count'] = (await cursor.fetchone())[0]
            
            # Total file size
            cursor = await db.execute('SELECT SUM(file_size) FROM files')
            total_size = (await cursor.fetchone())[0] or 0
            stats['total_size'] = total_size
            stats['total_size_mb'] = total_size / 1024 / 1024
            
            return stats
    
    # Backup operations
    async def create_backup(self) -> str:
        """Create database backup"""
        if not self.backup_path.exists():
            self.backup_path.mkdir(parents=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_path / f"backup_{timestamp}.db"
        
        shutil.copy2(self.db_path, backup_file)
        logger.info(f"Database backup created: {backup_file}")
        return str(backup_file)
    
    # Link operations
    async def create_link(self, link_data: Link) -> str:
        """Create a new share link"""
        async with aiosqlite.connect(self.db_path) as db:
            # Generate unique short code
            short_code = link_data.short_code
            if not short_code:
                while True:
                    short_code = Link.generate_short_code()
                    # Check if exists
                    cursor = await db.execute('SELECT id FROM links WHERE short_code = ?', (short_code,))
                    if not await cursor.fetchone():
                        break
            
            cursor = await db.execute('''
                INSERT INTO links (
                    short_code, link_type, target_id, target_ids, created_by,
                    title, description, expires_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                short_code,
                link_data.link_type,
                link_data.target_id,
                link_data.target_ids,
                link_data.created_by,
                link_data.title,
                link_data.description,
                link_data.expires_at,
                link_data.is_active
            ))
            await db.commit()
            return short_code
    
    async def get_link_by_code(self, short_code: str) -> Optional[Link]:
        """Get link by short code"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM links WHERE short_code = ? AND is_active = 1
            ''', (short_code,))
            row = await cursor.fetchone()
            return Link.from_dict(dict(row)) if row else None
    
    async def increment_link_access(self, short_code: str) -> bool:
        """Increment access count for link"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                UPDATE links SET access_count = access_count + 1 
                WHERE short_code = ? AND is_active = 1
            ''', (short_code,))
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_user_links(self, user_id: int, limit: int = 20) -> List[Link]:
        """Get links created by user"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM links WHERE created_by = ? 
                ORDER BY created_at DESC LIMIT ?
            ''', (user_id, limit))
            rows = await cursor.fetchall()
            return [Link.from_dict(dict(row)) for row in rows]
    
    async def delete_link(self, short_code: str, user_id: int) -> bool:
        """Delete link (only by creator)"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                UPDATE links SET is_active = 0 
                WHERE short_code = ? AND created_by = ?
            ''', (short_code, user_id))
            await db.commit()
            return cursor.rowcount > 0