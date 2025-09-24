#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Advanced Logging System for Telethon and Download Management
سیستم لاگ پیشرفته برای مدیریت Telethon و سیستم دانلود
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from enum import Enum

class LogLevel(Enum):
    """سطوح لاگ"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """دسته‌بندی لاگ‌ها"""
    TELETHON_CONFIG = "TELETHON_CONFIG"
    TELETHON_CLIENT = "TELETHON_CLIENT"
    TELETHON_LOGIN = "TELETHON_LOGIN"
    TELETHON_HEALTH = "TELETHON_HEALTH"
    DOWNLOAD_SYSTEM = "DOWNLOAD_SYSTEM"
    DOWNLOAD_LINKS = "DOWNLOAD_LINKS"
    USER_INTERACTION = "USER_INTERACTION"
    SYSTEM_PERFORMANCE = "SYSTEM_PERFORMANCE"
    ERROR_TRACKING = "ERROR_TRACKING"

class AdvancedLogger:
    """سیستم لاگ پیشرفته با قابلیت‌های تخصصی"""
    
    def __init__(self, log_dir: str = "/app/bot/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # تنظیم لاگرهای مختلف
        self.setup_loggers()
        
        # شمارنده خطاها
        self.error_counts = {}
        
        # لاگ‌های حافظه موقت برای نمایش سریع
        self.recent_logs = []
        self.max_recent_logs = 100
    
    def setup_loggers(self):
        """تنظیم لاگرهای تخصصی"""
        
        # فرمت کلی لاگ
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        formatter = logging.Formatter(log_format, date_format)
        
        # لاگر اصلی Telethon
        self.telethon_logger = logging.getLogger('telethon_advanced')
        self.telethon_logger.setLevel(logging.DEBUG)
        
        telethon_handler = logging.FileHandler(self.log_dir / 'telethon_system.log', encoding='utf-8')
        telethon_handler.setFormatter(formatter)
        self.telethon_logger.addHandler(telethon_handler)
        
        # لاگر سیستم دانلود
        self.download_logger = logging.getLogger('download_advanced')
        self.download_logger.setLevel(logging.DEBUG)
        
        download_handler = logging.FileHandler(self.log_dir / 'download_system.log', encoding='utf-8')
        download_handler.setFormatter(formatter)
        self.download_logger.addHandler(download_handler)
        
        # لاگر خطاها
        self.error_logger = logging.getLogger('system_errors')
        self.error_logger.setLevel(logging.ERROR)
        
        error_handler = logging.FileHandler(self.log_dir / 'system_errors.log', encoding='utf-8')
        error_handler.setFormatter(formatter)
        self.error_logger.addHandler(error_handler)
        
        # لاگر تعاملات کاربر
        self.user_logger = logging.getLogger('user_interactions')
        self.user_logger.setLevel(logging.INFO)
        
        user_handler = logging.FileHandler(self.log_dir / 'user_interactions.log', encoding='utf-8')
        user_handler.setFormatter(formatter)
        self.user_logger.addHandler(user_handler)
    
    def log(self, 
            level: LogLevel, 
            category: LogCategory, 
            message: str,
            user_id: Optional[int] = None,
            config_name: Optional[str] = None,
            error_details: Optional[Dict[str, Any]] = None,
            context: Optional[Dict[str, Any]] = None):
        """لاگ پیشرفته با جزئیات کامل"""
        
        # ساخت پیام ساختاریافته
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level.value,
            'category': category.value,
            'message': message,
            'user_id': user_id,
            'config_name': config_name,
            'error_details': error_details,
            'context': context
        }
        
        # افزودن به حافظه موقت
        self.recent_logs.append(log_entry)
        if len(self.recent_logs) > self.max_recent_logs:
            self.recent_logs.pop(0)
        
        # انتخاب لاگر مناسب
        if category in [LogCategory.TELETHON_CONFIG, LogCategory.TELETHON_CLIENT, 
                       LogCategory.TELETHON_LOGIN, LogCategory.TELETHON_HEALTH]:
            logger = self.telethon_logger
        elif category in [LogCategory.DOWNLOAD_SYSTEM, LogCategory.DOWNLOAD_LINKS]:
            logger = self.download_logger
        elif category == LogCategory.USER_INTERACTION:
            logger = self.user_logger
        elif category == LogCategory.ERROR_TRACKING:
            logger = self.error_logger
        else:
            logger = self.telethon_logger  # پیش‌فرض
        
        # نوشتن لاگ
        formatted_message = self._format_log_message(log_entry)
        
        if level == LogLevel.DEBUG:
            logger.debug(formatted_message)
        elif level == LogLevel.INFO:
            logger.info(formatted_message)
        elif level == LogLevel.WARNING:
            logger.warning(formatted_message)
        elif level == LogLevel.ERROR:
            logger.error(formatted_message)
            self._track_error(category.value, message)
        elif level == LogLevel.CRITICAL:
            logger.critical(formatted_message)
            self._track_error(category.value, message)
    
    def _format_log_message(self, log_entry: Dict[str, Any]) -> str:
        """فرمت کردن پیام لاگ"""
        parts = [f"[{log_entry['category']}]"]
        
        if log_entry.get('user_id'):
            parts.append(f"User:{log_entry['user_id']}")
        
        if log_entry.get('config_name'):
            parts.append(f"Config:{log_entry['config_name']}")
        
        parts.append(log_entry['message'])
        
        if log_entry.get('error_details'):
            parts.append(f"Details:{json.dumps(log_entry['error_details'], ensure_ascii=False)}")
        
        if log_entry.get('context'):
            parts.append(f"Context:{json.dumps(log_entry['context'], ensure_ascii=False)}")
        
        return " | ".join(parts)
    
    def _track_error(self, category: str, message: str):
        """ردیابی خطاها برای آمارگیری"""
        error_key = f"{category}:{message[:50]}"
        if error_key not in self.error_counts:
            self.error_counts[error_key] = 0
        self.error_counts[error_key] += 1
    
    def log_telethon_config_action(self, 
                                   action: str,
                                   config_name: str,
                                   user_id: int,
                                   success: bool,
                                   details: Optional[Dict[str, Any]] = None):
        """لاگ اقدامات کانفیگ Telethon"""
        level = LogLevel.INFO if success else LogLevel.ERROR
        message = f"Telethon config {action}: {config_name} - {'Success' if success else 'Failed'}"
        
        self.log(
            level=level,
            category=LogCategory.TELETHON_CONFIG,
            message=message,
            user_id=user_id,
            config_name=config_name,
            context=details
        )
    
    def log_telethon_client_status(self,
                                   config_name: str,
                                   status: str,
                                   error: Optional[str] = None,
                                   context: Optional[Dict[str, Any]] = None):
        """لاگ وضعیت کلاینت Telethon"""
        level = LogLevel.INFO if status == 'connected' else LogLevel.WARNING
        message = f"Telethon client '{config_name}' status: {status}"
        
        error_details = {'error': error} if error else None
        
        self.log(
            level=level,
            category=LogCategory.TELETHON_CLIENT,
            message=message,
            config_name=config_name,
            error_details=error_details,
            context=context
        )
    
    def log_telethon_login_attempt(self,
                                   config_name: str,
                                   phone: str,
                                   user_id: int,
                                   step: str,
                                   success: bool,
                                   error: Optional[str] = None):
        """لاگ تلاش‌های ورود Telethon"""
        level = LogLevel.INFO if success else LogLevel.WARNING
        message = f"Telethon login attempt - Step: {step}, Phone: {phone[-4:]} - {'Success' if success else 'Failed'}"
        
        error_details = {'error': error, 'step': step} if error else {'step': step}
        
        self.log(
            level=level,
            category=LogCategory.TELETHON_LOGIN,
            message=message,
            user_id=user_id,
            config_name=config_name,
            error_details=error_details
        )
    
    def log_download_link_creation(self,
                                   file_id: int,
                                   link_type: str,
                                   user_id: int,
                                   success: bool,
                                   link_code: Optional[str] = None,
                                   error: Optional[str] = None):
        """لاگ ایجاد لینک دانلود"""
        level = LogLevel.INFO if success else LogLevel.ERROR
        message = f"Download link creation - Type: {link_type}, File: {file_id} - {'Success' if success else 'Failed'}"
        
        context = {
            'file_id': file_id,
            'link_type': link_type,
            'link_code': link_code
        }
        
        error_details = {'error': error} if error else None
        
        self.log(
            level=level,
            category=LogCategory.DOWNLOAD_LINKS,
            message=message,
            user_id=user_id,
            error_details=error_details,
            context=context
        )
    
    def log_user_interaction(self,
                            user_id: int,
                            action: str,
                            details: Optional[Dict[str, Any]] = None):
        """لاگ تعاملات کاربر"""
        message = f"User interaction: {action}"
        
        self.log(
            level=LogLevel.INFO,
            category=LogCategory.USER_INTERACTION,
            message=message,
            user_id=user_id,
            context=details
        )
    
    def log_system_error(self,
                        error: Exception,
                        context: str,
                        user_id: Optional[int] = None,
                        additional_info: Optional[Dict[str, Any]] = None):
        """لاگ خطاهای سیستمی"""
        message = f"System error in {context}: {str(error)}"
        
        error_details = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc()
        }
        
        if additional_info:
            error_details.update(additional_info)
        
        self.log(
            level=LogLevel.ERROR,
            category=LogCategory.ERROR_TRACKING,
            message=message,
            user_id=user_id,
            error_details=error_details
        )
    
    def get_recent_logs(self, 
                       category: Optional[LogCategory] = None,
                       limit: int = 50) -> list:
        """دریافت لاگ‌های اخیر"""
        logs = self.recent_logs.copy()
        
        if category:
            logs = [log for log in logs if log['category'] == category.value]
        
        return logs[-limit:]
    
    def get_error_summary(self) -> Dict[str, int]:
        """خلاصه خطاهای رخ داده"""
        return dict(sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)[:20])
    
    def get_system_health_info(self) -> Dict[str, Any]:
        """اطلاعات سلامت سیستم بر اساس لاگ‌ها"""
        recent_errors = [log for log in self.recent_logs 
                        if log['level'] in ['ERROR', 'CRITICAL'] 
                        and datetime.fromisoformat(log['timestamp']) > 
                        datetime.now().replace(hour=datetime.now().hour-1)]  # آخرین ساعت
        
        telethon_logs = [log for log in self.recent_logs 
                        if log['category'].startswith('TELETHON')]
        
        download_logs = [log for log in self.recent_logs 
                        if log['category'].startswith('DOWNLOAD')]
        
        return {
            'recent_errors_count': len(recent_errors),
            'telethon_activity': len(telethon_logs),
            'download_activity': len(download_logs),
            'total_logs_today': len(self.recent_logs),
            'error_rate': len(recent_errors) / max(len(self.recent_logs), 1) * 100,
            'top_errors': list(self.error_counts.keys())[:5]
        }

# نمونه سراسری
advanced_logger = AdvancedLogger()