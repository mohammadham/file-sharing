#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database Models and Schemas
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import uuid
import string
import random
import json


@dataclass
class Category:
    """Category model"""
    id: Optional[int] = None
    name: str = ""
    parent_id: Optional[int] = None
    description: str = ""
    icon: str = "📁"  # Default folder icon
    thumbnail_file_id: str = ""  # Telegram file ID for thumbnail
    tags: str = ""  # JSON string for tags
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'description': self.description,
            'icon': self.icon,
            'thumbnail_file_id': self.thumbnail_file_id,
            'tags': self.tags,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Category':
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            parent_id=data.get('parent_id'),
            description=data.get('description', ''),
            icon=data.get('icon', '📁'),
            thumbnail_file_id=data.get('thumbnail_file_id', ''),
            tags=data.get('tags', ''),
            created_at=data.get('created_at')
        )
    
    @property
    def display_name(self) -> str:
        """Get display name with icon"""
        return f"{self.icon} {self.name}"
    
    @property
    def tags_list(self) -> List[str]:
        """Get tags as list"""
        try:
            return json.loads(self.tags) if self.tags else []
        except:
            return []
    
    def set_tags(self, tags: List[str]):
        """Set tags from list"""
        self.tags = json.dumps(tags, ensure_ascii=False)


@dataclass
class File:
    """File model"""
    id: Optional[int] = None
    file_name: str = ""
    file_type: str = ""
    file_size: int = 0
    category_id: int = 1
    telegram_file_id: str = ""
    storage_message_id: Optional[int] = None
    uploaded_by: Optional[int] = None
    uploaded_at: Optional[datetime] = None
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'category_id': self.category_id,
            'telegram_file_id': self.telegram_file_id,
            'storage_message_id': self.storage_message_id,
            'uploaded_by': self.uploaded_by,
            'uploaded_at': self.uploaded_at,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'File':
        return cls(
            id=data.get('id'),
            file_name=data.get('file_name', ''),
            file_type=data.get('file_type', ''),
            file_size=data.get('file_size', 0),
            category_id=data.get('category_id', 1),
            telegram_file_id=data.get('telegram_file_id', ''),
            storage_message_id=data.get('storage_message_id'),
            uploaded_by=data.get('uploaded_by'),
            uploaded_at=data.get('uploaded_at'),
            description=data.get('description', '')
        )
    
    @property
    def size_mb(self) -> float:
        """Get file size in MB"""
        return self.file_size / 1024 / 1024 if self.file_size else 0


@dataclass
class UserSession:
    """User session model"""
    user_id: int
    current_category: int = 1
    action_state: str = 'browsing'
    temp_data: Optional[str] = None
    last_activity: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'current_category': self.current_category,
            'action_state': self.action_state,
            'temp_data': self.temp_data,
            'last_activity': self.last_activity
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSession':
        return cls(
            user_id=data.get('user_id'),
            current_category=data.get('current_category', 1),
            action_state=data.get('action_state', 'browsing'),
            temp_data=data.get('temp_data'),
            last_activity=data.get('last_activity')
        )


@dataclass
class Link:
    """Share link model"""
    id: Optional[int] = None
    short_code: str = ""
    link_type: str = "file"  # "file" or "category" or "collection"
    target_id: Optional[int] = None  # file_id or category_id
    target_ids: Optional[str] = None  # JSON string for collection of file_ids
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    access_count: int = 0
    expires_at: Optional[datetime] = None
    is_active: bool = True
    title: str = ""
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'short_code': self.short_code,
            'link_type': self.link_type,
            'target_id': self.target_id,
            'target_ids': self.target_ids,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'access_count': self.access_count,
            'expires_at': self.expires_at,
            'is_active': self.is_active,
            'title': self.title,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Link':
        return cls(
            id=data.get('id'),
            short_code=data.get('short_code', ''),
            link_type=data.get('link_type', 'file'),
            target_id=data.get('target_id'),
            target_ids=data.get('target_ids'),
            created_by=data.get('created_by'),
            created_at=data.get('created_at'),
            access_count=data.get('access_count', 0),
            expires_at=data.get('expires_at'),
            is_active=data.get('is_active', True),
            title=data.get('title', ''),
            description=data.get('description', '')
        )
    
    @staticmethod
    def generate_short_code(length: int = 8) -> str:
        """Generate a random short code"""
        characters = string.ascii_letters + string.digits
        # Remove similar looking characters
        safe_chars = ''.join(c for c in characters if c not in 'il1Lo0O')
        return ''.join(random.choices(safe_chars, k=length))
    
    @property
    def full_url(self) -> str:
        """Get full share URL"""
        return f"https://t.me/your_bot?start=link_{self.short_code}"