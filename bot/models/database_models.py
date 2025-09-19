#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database Models and Schemas
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Category:
    """Category model"""
    id: Optional[int] = None
    name: str = ""
    parent_id: Optional[int] = None
    description: str = ""
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'description': self.description,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Category':
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            parent_id=data.get('parent_id'),
            description=data.get('description', ''),
            created_at=data.get('created_at')
        )


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