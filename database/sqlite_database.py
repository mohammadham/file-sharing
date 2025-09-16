"""
SQLite Database for UxB-File-Sharing Bot
Replacement for MongoDB with category management
"""
import sqlite3
import asyncio
import json
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
import os

DATABASE_PATH = os.getenv("DATABASE_PATH", "/app/data/file_sharing_bot.db")

# Ensure database directory exists
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

class SQLiteDatabase:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table (existing functionality)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                verify_status TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Categories table (new functionality)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                thumbnail_url TEXT DEFAULT '',
                parent_id TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (parent_id) REFERENCES categories (id),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # Files table (new functionality)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                original_name TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_size INTEGER DEFAULT 0,
                mime_type TEXT DEFAULT '',
                message_id INTEGER NOT NULL,
                chat_id TEXT NOT NULL,
                category_id TEXT DEFAULT NULL,
                description TEXT DEFAULT '',
                uploaded_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories (id),
                FOREIGN KEY (uploaded_by) REFERENCES users (id)
            )
        ''')
        
        # File links table (for tracking generated links)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_links (
                id TEXT PRIMARY KEY,
                file_id TEXT NOT NULL,
                link_type TEXT NOT NULL, -- 'direct', 'indirect', 'batch'
                link_code TEXT NOT NULL UNIQUE,
                expires_at TIMESTAMP,
                download_count INTEGER DEFAULT 0,
                max_downloads INTEGER DEFAULT -1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Create default categories
        self.create_default_categories()
    
    def create_default_categories(self):
        """Create default categories"""
        default_categories = [
            {
                'id': str(uuid.uuid4()),
                'name': 'عمومی',
                'description': 'فایل‌های عمومی',
                'parent_id': None
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'تصاویر',
                'description': 'تصاویر و عکس‌ها',
                'parent_id': None
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'فیلم‌ها',
                'description': 'فایل‌های ویدئویی',
                'parent_id': None
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'مستندات',
                'description': 'اسناد و فایل‌های متنی',
                'parent_id': None
            }
        ]
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for category in default_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO categories (id, name, description, parent_id, created_by)
                VALUES (?, ?, ?, ?, ?)
            ''', (category['id'], category['name'], category['description'], category['parent_id'], 1))
        
        conn.commit()
        conn.close()

# Initialize database instance
db = SQLiteDatabase()

# User management functions (existing functionality)
def new_user(id):
    return {
        'id': id,
        'verify_status': {
            'is_verified': False,
            'verified_time': "",
            'verify_token': "",
            'link': ""
        }
    }

async def present_user(user_id: int) -> bool:
    """Check if user exists"""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

async def add_user(user_id: int):
    """Add new user"""
    conn = db.get_connection()
    cursor = conn.cursor()
    default_verify = json.dumps({
        'is_verified': False,
        'verified_time': "",
        'verify_token': "",
        'link': ""
    })
    cursor.execute('INSERT OR REPLACE INTO users (id, verify_status) VALUES (?, ?)', 
                  (user_id, default_verify))
    conn.commit()
    conn.close()

async def db_verify_status(user_id: int):
    """Get user verify status"""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT verify_status FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return json.loads(result['verify_status'])
    else:
        return {
            'is_verified': False,
            'verified_time': 0,
            'verify_token': "",
            'link': ""
        }

async def db_update_verify_status(user_id: int, verify_status: dict):
    """Update user verify status"""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET verify_status = ? WHERE id = ?', 
                  (json.dumps(verify_status), user_id))
    conn.commit()
    conn.close()

async def full_userbase() -> List[int]:
    """Get all user IDs"""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users')
    results = cursor.fetchall()
    conn.close()
    return [row['id'] for row in results]

async def del_user(user_id: int):
    """Delete user"""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

# Category management functions (new functionality)
async def create_category(name: str, description: str = "", thumbnail_url: str = "", 
                         parent_id: Optional[str] = None, created_by: int = 1) -> str:
    """Create new category"""
    category_id = str(uuid.uuid4())
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO categories (id, name, description, thumbnail_url, parent_id, created_by)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (category_id, name, description, thumbnail_url, parent_id, created_by))
    conn.commit()
    conn.close()
    return category_id

async def get_category(category_id: str) -> Optional[Dict[str, Any]]:
    """Get category by ID"""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM categories WHERE id = ?', (category_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return dict(result)
    return None

async def get_categories(parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get categories by parent ID"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    if parent_id is None:
        cursor.execute('SELECT * FROM categories WHERE parent_id IS NULL ORDER BY name')
    else:
        cursor.execute('SELECT * FROM categories WHERE parent_id = ? ORDER BY name', (parent_id,))
    
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

async def update_category(category_id: str, name: Optional[str] = None, 
                         description: Optional[str] = None, thumbnail_url: Optional[str] = None):
    """Update category"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    update_fields = []
    params = []
    
    if name is not None:
        update_fields.append("name = ?")
        params.append(name)
    if description is not None:
        update_fields.append("description = ?")
        params.append(description)
    if thumbnail_url is not None:
        update_fields.append("thumbnail_url = ?")
        params.append(thumbnail_url)
    
    if update_fields:
        params.append(category_id)
        query = f"UPDATE categories SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    
    conn.close()

async def delete_category(category_id: str):
    """Delete category and move its files to parent category"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get category info
    cursor.execute('SELECT parent_id FROM categories WHERE id = ?', (category_id,))
    result = cursor.fetchone()
    
    if result:
        parent_id = result['parent_id']
        
        # Move files to parent category (or set to None if no parent)
        cursor.execute('UPDATE files SET category_id = ? WHERE category_id = ?', 
                      (parent_id, category_id))
        
        # Move subcategories to parent
        cursor.execute('UPDATE categories SET parent_id = ? WHERE parent_id = ?', 
                      (parent_id, category_id))
        
        # Delete the category
        cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        conn.commit()
    
    conn.close()

# File management functions (new functionality)
async def add_file(original_name: str, file_name: str, message_id: int, chat_id: str,
                  file_size: int = 0, mime_type: str = "", category_id: Optional[str] = None,
                  description: str = "", uploaded_by: int = 1) -> str:
    """Add new file"""
    file_id = str(uuid.uuid4())
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO files (id, original_name, file_name, file_size, mime_type, 
                          message_id, chat_id, category_id, description, uploaded_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (file_id, original_name, file_name, file_size, mime_type, 
          message_id, chat_id, category_id, description, uploaded_by))
    conn.commit()
    conn.close()
    return file_id

async def get_file(file_id: str) -> Optional[Dict[str, Any]]:
    """Get file by ID"""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM files WHERE id = ?', (file_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return dict(result)
    return None

async def get_files_by_category(category_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get files by category"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    if category_id is None:
        cursor.execute('SELECT * FROM files WHERE category_id IS NULL ORDER BY created_at DESC')
    else:
        cursor.execute('SELECT * FROM files WHERE category_id = ? ORDER BY created_at DESC', (category_id,))
    
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

async def search_files(query: str, category_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search files by name or description"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    search_pattern = f"%{query}%"
    
    if category_id is None:
        cursor.execute('''
            SELECT f.*, c.name as category_name FROM files f
            LEFT JOIN categories c ON f.category_id = c.id
            WHERE f.original_name LIKE ? OR f.description LIKE ?
            ORDER BY f.created_at DESC
        ''', (search_pattern, search_pattern))
    else:
        # Search in category and its subcategories
        cursor.execute('''
            WITH RECURSIVE subcategories AS (
                SELECT id FROM categories WHERE id = ?
                UNION ALL
                SELECT c.id FROM categories c
                INNER JOIN subcategories s ON c.parent_id = s.id
            )
            SELECT f.*, c.name as category_name FROM files f
            LEFT JOIN categories c ON f.category_id = c.id
            WHERE f.category_id IN (SELECT id FROM subcategories)
            AND (f.original_name LIKE ? OR f.description LIKE ?)
            ORDER BY f.created_at DESC
        ''', (category_id, search_pattern, search_pattern))
    
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

# File link management
async def create_file_link(file_id: str, link_type: str, link_code: str, 
                          expires_at: Optional[datetime] = None, max_downloads: int = -1) -> str:
    """Create file download link"""
    link_id = str(uuid.uuid4())
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO file_links (id, file_id, link_type, link_code, expires_at, max_downloads)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (link_id, file_id, link_type, link_code, expires_at, max_downloads))
    conn.commit()
    conn.close()
    return link_id

async def get_file_by_link_code(link_code: str) -> Optional[Dict[str, Any]]:
    """Get file by link code"""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT f.*, fl.link_type, fl.download_count, fl.max_downloads, fl.expires_at
        FROM files f
        JOIN file_links fl ON f.id = fl.file_id
        WHERE fl.link_code = ?
    ''', (link_code,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return dict(result)
    return None