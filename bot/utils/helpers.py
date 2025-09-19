#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Helper Functions and Utilities
"""

import json
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from telegram import File as TelegramFile, Document, PhotoSize, Video, Audio

logger = logging.getLogger(__name__)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    size = float(size_bytes)
    i = 0
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def format_datetime(dt: datetime) -> str:
    """Format datetime for display"""
    if not dt:
        return "نامشخص"
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return dt[:16] if len(dt) > 16 else dt
    
    return dt.strftime("%Y/%m/%d %H:%M")


def extract_file_info(message) -> Optional[Tuple[TelegramFile, str, int, str]]:
    """Extract file information from telegram message"""
    file_obj = None
    file_name = "Unknown"
    file_size = 0
    file_type = "Unknown"
    
    if message.document:
        file_obj = message.document
        file_name = file_obj.file_name or "Document"
        file_size = file_obj.file_size or 0
        file_type = file_obj.mime_type or "application/octet-stream"
    elif message.photo:
        file_obj = message.photo[-1]  # Get largest photo
        file_name = f"Photo_{file_obj.file_id[:8]}.jpg"
        file_size = file_obj.file_size or 0
        file_type = "image/jpeg"
    elif message.video:
        file_obj = message.video
        file_name = file_obj.file_name or f"Video_{file_obj.file_id[:8]}.mp4"
        file_size = file_obj.file_size or 0
        file_type = file_obj.mime_type or "video/mp4"
    elif message.audio:
        file_obj = message.audio
        file_name = file_obj.file_name or f"Audio_{file_obj.file_id[:8]}.mp3"
        file_size = file_obj.file_size or 0
        file_type = file_obj.mime_type or "audio/mpeg"
    
    return (file_obj, file_name, file_size, file_type) if file_obj else None


def parse_callback_data(callback_data: str) -> Tuple[str, str]:
    """Parse callback data into action and parameters"""
    parts = callback_data.split('_', 1)
    action = parts[0]
    params = parts[1] if len(parts) > 1 else ""
    return action, params


def safe_json_loads(json_string: Optional[str], default: Dict = None) -> Dict[str, Any]:
    """Safely load JSON string"""
    if not json_string:
        return default or {}
    
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"Failed to parse JSON: {json_string}")
        return default or {}


def safe_json_dumps(data: Any) -> str:
    """Safely dump data to JSON string"""
    try:
        return json.dumps(data, ensure_ascii=False, default=str)
    except (TypeError, ValueError) as e:
        logger.warning(f"Failed to serialize to JSON: {e}")
        return "{}"


def validate_file_size(file_size: int, max_size: int = 50 * 1024 * 1024) -> bool:
    """Validate file size against maximum allowed"""
    return file_size <= max_size


def generate_file_description(file_name: str, file_type: str, file_size: int) -> str:
    """Generate automatic file description"""
    size_str = format_file_size(file_size)
    type_str = file_type.split('/')[-1].upper() if '/' in file_type else file_type.upper()
    return f"فایل {type_str} با حجم {size_str}"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def escape_markdown(text: str) -> str:
    """Escape special characters for Markdown"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def build_stats_text(stats: Dict[str, Any]) -> str:
    """Build formatted statistics text"""
    return f"""
📊 **آمار ربات**

👥 تعداد کاربران: {stats.get('users_count', 0)}
📁 تعداد فایل‌ها: {stats.get('files_count', 0)}
🗂 تعداد دسته‌ها: {stats.get('categories_count', 0)}
💾 حجم کل فایل‌ها: {stats.get('total_size_mb', 0):.1f} MB

📈 ربات در حال کار عادی است!
    """


def build_file_info_text(file_dict: Dict, category_name: str = "") -> str:
    """Build formatted file information text"""
    size_mb = file_dict.get('file_size', 0) / 1024 / 1024
    upload_date = format_datetime(file_dict.get('uploaded_at'))
    
    # Escape file name for Markdown
    file_name = file_dict.get('file_name', 'نامشخص')
    safe_file_name = file_name.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]')
    text = f"📄 **{safe_file_name}**\n"
    text += f"📁 دسته: {category_name}\n" if category_name else ""
    text += f"💾 حجم: {size_mb:.1f} MB\n"
    text += f"📅 تاریخ آپلود: {upload_date}\n"
    text += f"🏷 نوع فایل: {file_dict.get('file_type', 'نامشخص')}\n"
    
    if file_dict.get('description'):
        text += f"📝 توضیحات: {file_dict['description']}\n"
    
    return text