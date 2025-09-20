#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Advanced Link Manager - Professional URL shortening system
"""

import logging
import json
import string
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from models.database_models import Link, File, Category

logger = logging.getLogger(__name__)


class LinkManager:
    """Professional link management system"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    async def create_file_link(
        self, 
        file_id: int, 
        user_id: int,
        title: str = "",
        description: str = "",
        expires_hours: Optional[int] = None,
        custom_code: str = ""
    ) -> Tuple[str, str]:
        """Create professional file share link"""
        try:
            file = await self.db.get_file_by_id(file_id)
            if not file:
                raise ValueError("File not found")
            
            # Generate expiration if specified
            expires_at = None
            if expires_hours:
                expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            # Auto-generate title and description if not provided
            if not title:
                title = file.file_name
            
            if not description:
                from utils.helpers import format_file_size
                description = f"📄 {file.file_name} - حجم: {format_file_size(file.file_size)}"
            
            # Create link object
            link_data = Link(
                short_code=custom_code if custom_code else "",
                link_type="file",
                target_id=file_id,
                created_by=user_id,
                title=title,
                description=description,
                expires_at=expires_at
            )
            
            # Generate and save link
            short_code = await self.db.create_link(link_data)
            
            # Generate full URL
            full_url = f"t.me/YourBotUsername?start=link_{short_code}"
            
            return short_code, full_url
            
        except Exception as e:
            logger.error(f"Error creating file link: {e}")
            raise
    
    async def create_category_link(
        self,
        category_id: int,
        user_id: int,
        title: str = "",
        description: str = "",
        expires_hours: Optional[int] = None
    ) -> Tuple[str, str]:
        """Create category share link"""
        try:
            category = await self.db.get_category_by_id(category_id)
            if not category:
                raise ValueError("Category not found")
            
            # Count files in category
            files = await self.db.get_files(category_id, limit=1000)
            files_count = len(files)
            
            # Generate expiration if specified
            expires_at = None
            if expires_hours:
                expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            # Auto-generate title and description if not provided
            if not title:
                title = f"دسته {category.name}"
            
            if not description:
                description = f"📁 دسته {category.name} شامل {files_count} فایل"
            
            # Create link object
            link_data = Link(
                link_type="category",
                target_id=category_id,
                created_by=user_id,
                title=title,
                description=description,
                expires_at=expires_at
            )
            
            # Generate and save link
            short_code = await self.db.create_link(link_data)
            
            # Generate full URL
            full_url = f"t.me/YourBotUsername?start=link_{short_code}"
            
            return short_code, full_url
            
        except Exception as e:
            logger.error(f"Error creating category link: {e}")
            raise
    
    async def create_collection_link(
        self,
        file_ids: List[int],
        user_id: int,
        title: str = "",
        description: str = "",
        expires_hours: Optional[int] = None
    ) -> Tuple[str, str]:
        """Create collection share link for multiple files"""
        try:
            if not file_ids:
                raise ValueError("No files selected")
            
            # Verify all files exist
            valid_files = []
            for file_id in file_ids:
                file = await self.db.get_file_by_id(file_id)
                if file:
                    valid_files.append(file)
            
            if not valid_files:
                raise ValueError("No valid files found")
            
            # Generate expiration if specified
            expires_at = None
            if expires_hours:
                expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            # Auto-generate title and description if not provided
            if not title:
                title = f"مجموعه {len(valid_files)} فایل"
            
            if not description:
                from utils.helpers import format_file_size
                total_size = sum(f.file_size for f in valid_files)
                description = f"📦 مجموعه شامل {len(valid_files)} فایل - حجم کل: {format_file_size(total_size)}"
            
            # Create link object
            link_data = Link(
                link_type="collection",
                target_ids=json.dumps(file_ids),
                created_by=user_id,
                title=title,
                description=description,
                expires_at=expires_at
            )
            
            # Generate and save link
            short_code = await self.db.create_link(link_data)
            
            # Generate full URL
            full_url = f"t.me/YourBotUsername?start=link_{short_code}"
            
            return short_code, full_url
            
        except Exception as e:
            logger.error(f"Error creating collection link: {e}")
            raise
    
    async def get_link_stats(self, short_code: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive link statistics"""
        try:
            link = await self.db.get_link_by_code(short_code)
            if not link:
                return None
            
            stats = {
                'short_code': link.short_code,
                'link_type': link.link_type,
                'title': link.title,
                'description': link.description,
                'access_count': link.access_count,
                'created_at': link.created_at,
                'expires_at': link.expires_at,
                'is_active': link.is_active,
                'is_expired': False
            }
            
            # Check if expired
            if link.expires_at:
                try:
                    if isinstance(link.expires_at, str):
                        expires_dt = datetime.fromisoformat(link.expires_at.replace('Z', '+00:00'))
                    else:
                        expires_dt = link.expires_at
                    
                    stats['is_expired'] = expires_dt < datetime.now()
                except:
                    pass
            
            # Add type-specific information
            if link.link_type == "file" and link.target_id:
                file = await self.db.get_file_by_id(link.target_id)
                if file:
                    stats['target_info'] = {
                        'name': file.file_name,
                        'size': file.file_size,
                        'type': file.file_type
                    }
            
            elif link.link_type == "category" and link.target_id:
                category = await self.db.get_category_by_id(link.target_id)
                if category:
                    files = await self.db.get_files(link.target_id, limit=1000)
                    stats['target_info'] = {
                        'name': category.name,
                        'files_count': len(files),
                        'description': category.description
                    }
            
            elif link.link_type == "collection" and link.target_ids:
                try:
                    file_ids = json.loads(link.target_ids)
                    files = []
                    for file_id in file_ids:
                        file = await self.db.get_file_by_id(file_id)
                        if file:
                            files.append(file)
                    
                    total_size = sum(f.file_size for f in files)
                    stats['target_info'] = {
                        'files_count': len(files),
                        'total_size': total_size,
                        'files': [{'name': f.file_name, 'size': f.file_size} for f in files]
                    }
                except:
                    pass
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting link stats: {e}")
            return None
    
    async def deactivate_link(self, short_code: str, user_id: int) -> bool:
        """Deactivate a link (only by creator)"""
        try:
            return await self.db.delete_link(short_code, user_id)
        except Exception as e:
            logger.error(f"Error deactivating link: {e}")
            return False
    
    async def get_user_links(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get all links created by user with stats"""
        try:
            links = await self.db.get_user_links(user_id, limit)
            result = []
            
            for link in links:
                stats = await self.get_link_stats(link.short_code)
                if stats:
                    result.append(stats)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting user links: {e}")
            return []
    
    @staticmethod
    def generate_custom_code(base: str, length: int = 6) -> str:
        """Generate custom short code based on text"""
        # Clean the base text
        clean_base = ''.join(c for c in base if c.isalnum())[:4]
        
        # Add random suffix
        suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=length-len(clean_base)))
        
        return (clean_base + suffix).lower()
    
    @staticmethod
    def is_valid_custom_code(code: str) -> bool:
        """Validate custom short code"""
        if not code or len(code) < 4 or len(code) > 20:
            return False
        
        # Only allow alphanumeric characters
        if not code.replace('_', '').replace('-', '').isalnum():
            return False
        
        # Avoid reserved words
        reserved = ['admin', 'api', 'www', 'start', 'help', 'bot']
        if code.lower() in reserved:
            return False
        
        return True