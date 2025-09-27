#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Advanced Telethon Client Manager with JSON Config Support
مدیریت پیشرفته کلاینت‌های Telethon با پشتیبانی کانفیگ JSON
"""

import asyncio
import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Any
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    FloodWaitError, SessionPasswordNeededError, 
    PhoneCodeInvalidError, ApiIdInvalidError
)
import sys
from pathlib import Path
# Add bot directory to path
sys.path.append(str(Path(__file__).parent))
try:
    from config.settings import settings
except ImportError:
    from download_system.config.settings import settings

logger = logging.getLogger(__name__)


class TelethonConfig:
    """مدل کانفیگ Telethon"""
    
    def __init__(self, config_data: dict):
        self.api_id = config_data.get('api_id')
        self.api_hash = config_data.get('api_hash')
        self.session_string = config_data.get('session_string', '')
        self.phone = config_data.get('phone', '')
        self.name = config_data.get('name', 'default')
        self.device_model = config_data.get('device_model', 'Download System')
        self.system_version = config_data.get('system_version', '1.0')
        self.app_version = config_data.get('app_version', '1.0.0')
        self.lang_code = config_data.get('lang_code', 'en')
        self.created_at = config_data.get('created_at', datetime.now().isoformat())
        self.is_active = config_data.get('is_active', True)
        
    def to_dict(self) -> dict:
        """تبدیل به دیکشنری"""
        return {
            'api_id': self.api_id,
            'api_hash': self.api_hash,
            'session_string': self.session_string,
            'phone': self.phone,
            'name': self.name,
            'device_model': self.device_model,
            'system_version': self.system_version,
            'app_version': self.app_version,
            'lang_code': self.lang_code,
            'created_at': self.created_at,
            'is_active': self.is_active
        }
    
    def is_valid(self) -> bool:
        """بررسی اعتبار کانفیگ"""
        return bool(self.api_id and self.api_hash)


class TelethonConfigManager:
    """مدیریت کانفیگ‌های Telethon"""
    
    def __init__(self):
        self.config_dir = Path(settings.TELETHON_SESSION_DIR) / "configs"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.configs: Dict[str, TelethonConfig] = {}
        self._load_all_configs()
    
    def _get_config_path(self, config_name: str) -> Path:
        """مسیر فایل کانفیگ"""
        safe_name = "".join(c for c in config_name if c.isalnum() or c in ('-', '_'))
        return self.config_dir / f"{safe_name}.json"
    
    def _load_all_configs(self):
        """بارگذاری تمام کانفیگ‌های موجود"""
        try:
            for config_file in self.config_dir.glob("*.json"):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    
                    config_name = config_file.stem
                    self.configs[config_name] = TelethonConfig(config_data)
                    logger.info(f"Loaded Telethon config: {config_name}")
                    
                except Exception as e:
                    logger.error(f"Error loading config {config_file}: {e}")
        
        except Exception as e:
            logger.error(f"Error loading configs directory: {e}")
    
    def add_config_from_path(self, config_path: str, config_name: str = None) -> bool:
        """افزودن کانفیگ از مسیر فایل"""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                logger.error(f"Config file not found: {config_path}")
                return False
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # اعتبارسنجی کانفیگ
            temp_config = TelethonConfig(config_data)
            if not temp_config.is_valid():
                logger.error("Invalid config: missing api_id or api_hash")
                return False
            
            # تعیین نام کانفیگ
            if not config_name:
                config_name = config_file.stem or f"config_{len(self.configs)}"
            
            # ذخیره کانفیگ
            return self.save_config(config_name, config_data)
            
        except Exception as e:
            logger.error(f"Error adding config from path {config_path}: {e}")
            return False
    
    def save_config(self, config_name: str, config_data: dict) -> bool:
        """ذخیره کانفیگ"""
        try:
            config = TelethonConfig(config_data)
            if not config.is_valid():
                logger.error("Cannot save invalid config")
                return False
            
            # ذخیره در فایل
            config_path = self._get_config_path(config_name)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
            
            # بارگذاری در حافظه
            self.configs[config_name] = config
            
            logger.info(f"Saved Telethon config: {config_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config {config_name}: {e}")
            return False
    
    def get_config(self, config_name: str) -> Optional[TelethonConfig]:
        """دریافت کانفیگ"""
        return self.configs.get(config_name)
    
    def list_configs(self) -> Dict[str, dict]:
        """لیست تمام کانفیگ‌ها"""
        return {
            name: {
                'name': config.name,
                'phone': config.phone,
                'api_id': config.api_id,
                'has_session': bool(config.session_string),
                'is_active': config.is_active,
                'created_at': config.created_at
            }
            for name, config in self.configs.items()
        }
    
    def delete_config(self, config_name: str) -> bool:
        """حذف کانفیگ"""
        try:
            if config_name in self.configs:
                config_path = self._get_config_path(config_name)
                if config_path.exists():
                    config_path.unlink()
                
                del self.configs[config_name]
                logger.info(f"Deleted Telethon config: {config_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting config {config_name}: {e}")
            return False
    
    def update_session_string(self, config_name: str, session_string: str) -> bool:
        """بروزرسانی session string"""
        try:
            if config_name not in self.configs:
                return False
            
            config = self.configs[config_name]
            config.session_string = session_string
            
            return self.save_config(config_name, config.to_dict())
            
        except Exception as e:
            logger.error(f"Error updating session for {config_name}: {e}")
            return False


class AdvancedTelethonClientManager:
    """مدیریت پیشرفته کلاینت‌های Telethon با پشتیبانی کانفیگ‌های متعدد"""
    
    def __init__(self):
        self.config_manager = TelethonConfigManager()
        self.clients: Dict[str, TelegramClient] = {}
        self.client_status: Dict[str, dict] = {}
        self._last_health_check = {}
    
    async def get_client(self, config_name: str = "default") -> Optional[TelegramClient]:
        """دریافت یا ایجاد کلاینت Telethon"""
        try:
            # بررسی کلاینت موجود
            if config_name in self.clients:
                client = self.clients[config_name]
                if client.is_connected():
                    return client
                else:
                    # تلاش برای اتصال مجدد
                    await client.connect()
                    if client.is_connected():
                        return client
            
            # ایجاد کلاینت جدید
            config = self.config_manager.get_config(config_name)
            if not config or not config.is_valid():
                logger.error(f"No valid config found for: {config_name}")
                return None
            
            # ایجاد کلاینت با session string یا جدید
            if config.session_string:
                session = StringSession(config.session_string)
            else:
                session_path = Path(settings.TELETHON_SESSION_DIR) / f"{config_name}.session"
                session = str(session_path)
            
            client = TelegramClient(
                session,
                config.api_id,
                config.api_hash,
                device_model=config.device_model,
                system_version=config.system_version,
                app_version=config.app_version,
                lang_code=config.lang_code
            )
            
            # اتصال بدون ورود تعاملی - فقط برای session های موجود
            await client.connect()
            
            # بررسی اینکه آیا وارد شده یا نه
            if not await client.is_user_authorized():
                logger.warning(f"Client {config_name} is not authorized. Need to login first.")
                self._update_client_status(config_name, "unauthorized", "Need to login first")
                await client.disconnect()
                return None
            
            # ذخیره session string اگر جدید است و وارد شده باشد
            if not config.session_string and hasattr(client.session, 'save'):
                try:
                    session_string = client.session.save()
                    self.config_manager.update_session_string(config_name, session_string)
                except Exception as e:
                    logger.error(f"Error saving session for {config_name}: {e}")
            
            self.clients[config_name] = client
            self._update_client_status(config_name, "connected", None)
            
            logger.info(f"Telethon client '{config_name}' connected successfully")
            return client
            
        except ApiIdInvalidError:
            error = "Invalid API ID or API Hash"
            logger.error(f"API credentials error for {config_name}: {error}")
            self._update_client_status(config_name, "error", error)
            return None
            
        except Exception as e:
            error = str(e)
            logger.error(f"Error creating Telethon client '{config_name}': {error}")
            self._update_client_status(config_name, "error", error)
            return None
    
    def _update_client_status(self, config_name: str, status: str, error: str = None):
        """بروزرسانی وضعیت کلاینت"""
        self.client_status[config_name] = {
            'status': status,
            'error': error,
            'last_check': datetime.now().isoformat(),
            'connected': status == "connected"
        }
    
    async def login_client_interactive(self, config_name: str, phone: str = None) -> bool:
        """ورود تعاملی به کلاینت - فقط برای استفاده در ربات"""
        try:
            config = self.config_manager.get_config(config_name)
            if not config or not config.is_valid():
                logger.error(f"No valid config found for: {config_name}")
                return False
            
            # استفاده از شماره تلفن موجود یا ورودی
            phone_number = phone or config.phone
            if not phone_number:
                logger.error(f"No phone number available for {config_name}")
                return False
            
            # ایجاد کلاینت موقت برای ورود
            session_path = Path(settings.TELETHON_SESSION_DIR) / f"{config_name}.session"
            client = TelegramClient(
                str(session_path),
                config.api_id,
                config.api_hash,
                device_model=config.device_model,
                system_version=config.system_version,
                app_version=config.app_version,
                lang_code=config.lang_code
            )
            
            # شروع فرآیند ورود تعاملی
            await client.start(phone=phone_number)
            
            # ذخیره session string
            if hasattr(client.session, 'save'):
                session_string = client.session.save()
                self.config_manager.update_session_string(config_name, session_string)
            
            await client.disconnect()
            self._update_client_status(config_name, "authorized", None)
            
            logger.info(f"Successfully logged in client: {config_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error during interactive login for {config_name}: {e}")
            self._update_client_status(config_name, "login_error", str(e))
            return False
    
    async def check_all_clients_health(self) -> Dict[str, dict]:
        """بررسی سلامت تمام کلاینت‌ها"""
        health_status = {}
        
        for config_name in self.config_manager.configs:
            try:
                client = await self.get_client(config_name)
                if client and client.is_connected():
                    # تست ساده اتصال
                    me = await client.get_me()
                    health_status[config_name] = {
                        'status': 'healthy',
                        'connected': True,
                        'user_id': me.id if me else None,
                        'phone': me.phone if me else None,
                        'error': None
                    }
                else:
                    health_status[config_name] = {
                        'status': 'disconnected',
                        'connected': False,
                        'error': 'Cannot connect to Telegram'
                    }
            except Exception as e:
                health_status[config_name] = {
                    'status': 'error',
                    'connected': False,
                    'error': str(e)
                }
        
        self._last_health_check = health_status
        return health_status
    
    async def login_with_phone(self, config_name: str, phone: str) -> dict:
        """ورود با شماره تلفن"""
        try:
            config = self.config_manager.get_config(config_name)
            if not config:
                return {'success': False, 'error': 'Config not found'}
            
            # ایجاد کلاینت موقت
            temp_client = TelegramClient(
                StringSession(),
                config.api_id,
                config.api_hash
            )
            
            await temp_client.connect()
            
            # ارسال کد
            result = await temp_client.send_code_request(phone)
            
            await temp_client.disconnect()
            
            return {
                'success': True,
                'phone_code_hash': result.phone_code_hash,
                'message': 'Verification code sent'
            }
            
        except Exception as e:
            logger.error(f"Error in login_with_phone: {e}")
            return {'success': False, 'error': str(e)}
    
    async def verify_code(self, config_name: str, phone: str, code: str, phone_code_hash: str) -> dict:
        """تأیید کد ورود"""
        try:
            config = self.config_manager.get_config(config_name)
            if not config:
                return {'success': False, 'error': 'Config not found'}
            
            # ایجاد کلاینت موقت
            temp_client = TelegramClient(
                StringSession(),
                config.api_id,
                config.api_hash
            )
            
            await temp_client.connect()
            
            try:
                # تأیید کد
                result = await temp_client.sign_in(phone, code, phone_code_hash=phone_code_hash)
                
                # ذخیره session string
                session_string = temp_client.session.save()
                config.session_string = session_string
                config.phone = phone
                
                # بروزرسانی کانفیگ
                self.config_manager.save_config(config_name, config.to_dict())
                
                await temp_client.disconnect()
                
                return {
                    'success': True,
                    'user_id': result.id,
                    'message': 'Login successful'
                }
                
            except SessionPasswordNeededError:
                await temp_client.disconnect()
                return {
                    'success': False,
                    'error': 'Two-factor authentication enabled. Password required.',
                    'needs_password': True
                }
            except PhoneCodeInvalidError:
                await temp_client.disconnect()
                return {'success': False, 'error': 'Invalid verification code'}
            
        except Exception as e:
            logger.error(f"Error in verify_code: {e}")
            return {'success': False, 'error': str(e)}
    
    async def verify_password(self, config_name: str, password: str, phone: str, phone_code_hash: str) -> dict:
        """تأیید رمز دو مرحله‌ای"""
        try:
            config = self.config_manager.get_config(config_name)
            if not config:
                return {'success': False, 'error': 'Config not found'}
            
            temp_client = TelegramClient(
                StringSession(),
                config.api_id,
                config.api_hash
            )
            
            await temp_client.connect()
            
            # تأیید رمز
            result = await temp_client.sign_in(password=password)
            
            # ذخیره session
            session_string = temp_client.session.save()
            config.session_string = session_string
            config.phone = phone
            
            self.config_manager.save_config(config_name, config.to_dict())
            
            await temp_client.disconnect()
            
            return {
                'success': True,
                'user_id': result.id,
                'message': 'Login successful with 2FA'
            }
            
        except Exception as e:
            logger.error(f"Error in verify_password: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_client_status(self, config_name: str = None) -> dict:
        """دریافت وضعیت کلاینت(ها)"""
        if config_name:
            return self.client_status.get(config_name, {
                'status': 'unknown',
                'connected': False,
                'error': 'Client not initialized'
            })
        
        return self.client_status
    
    def get_best_available_client(self) -> Optional[TelegramClient]:
        """دریافت بهترین کلاینت در دسترس"""
        for config_name, status in self.client_status.items():
            if status.get('connected', False):
                return self.clients.get(config_name)
        
        return None
    
    async def disconnect_all(self):
        """قطع اتصال تمام کلاینت‌ها"""
        for config_name, client in self.clients.items():
            try:
                await client.disconnect()
                self._update_client_status(config_name, "disconnected")
                logger.info(f"Disconnected client: {config_name}")
            except Exception as e:
                logger.error(f"Error disconnecting client {config_name}: {e}")
        
        self.clients.clear()
        
    def has_active_clients(self) -> bool:
        """بررسی وجود کلاینت فعال"""
        return any(
            status.get('connected', False) 
            for status in self.client_status.values()
        )