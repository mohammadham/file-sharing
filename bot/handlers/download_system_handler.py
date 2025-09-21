#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Download System Handler - مدیریت سیستم دانلود پیشرفته از طریق ربات تلگرام
"""

import aiohttp
import asyncio
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

from handlers.base_handler import BaseHandler
from utils.keyboard_builder import KeyboardBuilder

logger = logging.getLogger(__name__)


class DownloadSystemHandler(BaseHandler):
    """مدیریت سیستم دانلود پیشرفته"""
    
    def __init__(self, db, download_api_url: str, admin_token: str):
        super().__init__(db)
        self.api_url = download_api_url
        self.admin_token = admin_token
        self.headers = {"Authorization": f"Bearer {admin_token}"}
    
    async def show_system_control(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش پنل کنترل سیستم دانلود"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            # دریافت وضعیت سیستم از API
            system_status = await self.get_system_status()
            
            status_icon = "🟢" if system_status.get('ready', False) else "🔴"
            
            text = f"🎛 **کنترل سیستم دانلود پیشرفته**\n\n"
            text += f"{status_icon} **وضعیت:** {system_status.get('status', 'نامشخص')}\n"
            text += f"📊 **نسخه:** {system_status.get('version', '1.0.0')}\n"
            text += f"📥 **دانلودهای فعال:** {system_status.get('active_downloads', 0)}\n"
            text += f"💾 **ورودی‌های Cache:** {system_status.get('cache_entries', 0)}\n"
            text += f"📈 **دانلودهای امروز:** {system_status.get('daily_downloads', 0)}\n\n"
            
            if not system_status.get('ready', False):
                text += f"⚠️ **توجه:** سیستم دانلود در دسترس نیست\n\n"
            
            text += f"🕐 **آخرین بروزرسانی:** {datetime.now().strftime('%H:%M:%S')}"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📊 نظارت لحظه‌ای", callback_data="system_monitoring"),
                    InlineKeyboardButton("🔧 تنظیمات سیستم", callback_data="system_settings")
                ],
                [
                    InlineKeyboardButton("🧹 پاکسازی Cache", callback_data="system_cleanup"),
                    InlineKeyboardButton("📈 گزارش آمار", callback_data="download_stats")
                ],
                [
                    InlineKeyboardButton("🔗 مدیریت توکن‌ها", callback_data="token_management"),
                    InlineKeyboardButton("⚙️ تنظیمات API", callback_data="api_settings")
                ],
                [
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data="download_system_control"),
                    InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_system_control: {e}")
            await self.handle_error(update, context, e)
    
    async def show_file_download_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش گزینه‌های دانلود پیشرفته برای فایل"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            file_id = int(query.data.split('_')[3])
            file = await self.db.get_file_by_id(file_id)
            
            if not file:
                await query.edit_message_text("فایل یافت نشد!")
                return
            
            from utils.helpers import format_file_size
            
            text = f"🔗 **مدیریت لینک‌های دانلود پیشرفته**\n\n"
            text += f"📄 **فایل:** {file.file_name}\n"
            text += f"💾 **حجم:** {format_file_size(file.file_size)}\n"
            text += f"🏷 **نوع:** {file.file_type}\n\n"
            text += "انتخاب کنید:"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🌊 لینک دانلود استریم", 
                                       callback_data=f"create_stream_link_{file_id}"),
                    InlineKeyboardButton("⚡️ لینک دانلود سریع", 
                                       callback_data=f"create_fast_link_{file_id}")
                ],
                [
                    InlineKeyboardButton("⚙️ لینک با تنظیمات محدود", 
                                       callback_data=f"create_restricted_link_{file_id}")
                ],
                [
                    InlineKeyboardButton("📋 مشاهده لینک‌های موجود", 
                                       callback_data=f"view_file_links_{file_id}")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", 
                                       callback_data=f"file_{file_id}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def create_stream_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ایجاد لینک دانلود استریم"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update, "در حال ایجاد لینک استریم...")
            
            file_id = int(query.data.split('_')[3])
            user_id = update.effective_user.id
            
            # ایجاد لینک از طریق API سیستم دانلود
            link_data = {
                "file_id": file_id,
                "download_type": "stream",
                "max_downloads": 100,
                "expires_hours": 24
            }
            
            result = await self.create_download_link_via_api(link_data)
            
            if result.get('success'):
                text = f"🌊 **لینک دانلود استریم ایجاد شد**\n\n"
                text += f"🔗 **کد لینک:** `{result['link_code']}`\n"
                text += f"🌐 **URL دانلود:**\n`{result['download_url']}`\n\n"
                text += f"⏰ **انقضا:** {result.get('expires_at', 'نامحدود')}\n"
                text += f"📊 **حداکثر دانلود:** {result.get('max_downloads', 'نامحدود')}\n\n"
                text += "✨ **ویژگی‌های استریم:**\n"
                text += "• دانلود مستقیم بدون ذخیره موقت\n"
                text += "• پشتیبانی فایل‌های بزرگ\n"
                text += "• سرعت بالا\n"
                text += "• مصرف کم منابع سرور"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📋 کپی لینک", 
                                           callback_data=f"copy_stream_link_{result['link_code']}")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", 
                                           callback_data=f"file_download_links_{file_id}")
                    ]
                ])
                
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                await query.edit_message_text(f"❌ خطا در ایجاد لینک: {result.get('error', 'نامشخص')}")
                
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def create_fast_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ایجاد لینک دانلود سریع"""
        try:
            query = update.callback_query  
            await self.answer_callback_query(update, "در حال ایجاد لینک سریع...")
            
            file_id = int(query.data.split('_')[3])
            
            # ایجاد لینک از طریق API سیستم دانلود
            link_data = {
                "file_id": file_id,
                "download_type": "fast",
                "max_downloads": 50,
                "expires_hours": 12
            }
            
            result = await self.create_download_link_via_api(link_data)
            
            if result.get('success'):
                text = f"⚡️ **لینک دانلود سریع ایجاد شد**\n\n"
                text += f"🔗 **کد لینک:** `{result['link_code']}`\n"
                text += f"🌐 **URL دانلود:**\n`{result['download_url']}`\n\n"
                text += f"⏰ **انقضا:** {result.get('expires_at', 'نامحدود')}\n"
                text += f"📊 **حداکثر دانلود:** {result.get('max_downloads', 'نامحدود')}\n\n"
                text += "⚡️ **ویژگی‌های سریع:**\n"
                text += "• فایل در cache ذخیره می‌شود\n"
                text += "• دانلودهای بعدی فوری\n"
                text += "• بهینه برای فایل‌های پرتکرار\n"
                text += "• کاهش بار روی سرور تلگرام"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📋 کپی لینک", 
                                           callback_data=f"copy_fast_link_{result['link_code']}")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", 
                                           callback_data=f"file_download_links_{file_id}")
                    ]
                ])
                
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                await query.edit_message_text(f"❌ خطا در ایجاد لینک: {result.get('error', 'نامشخص')}")
                
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def system_monitoring(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نظارت لحظه‌ای بر سیستم"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            # دریافت metrics لحظه‌ای
            metrics = await self.get_real_time_metrics()
            
            text = f"📊 **نظارت لحظه‌ای سیستم دانلود**\n\n"
            text += f"🔄 **وضعیت فعلی:**\n"
            text += f"• درخواست‌های فعال: {metrics.get('active_requests', 0)}\n"
            text += f"• سرعت میانگین: {metrics.get('avg_download_speed', '0')} MB/s\n"
            text += f"• استفاده از حافظه: {metrics.get('memory_usage', '0%')}\n"
            text += f"• استفاده از CPU: {metrics.get('cpu_usage', '0%')}\n\n"
            
            text += f"📈 **آمار 24 ساعت گذشته:**\n"
            text += f"• کل دانلودها: {metrics.get('daily_downloads', 0)}\n"
            text += f"• کاربران فعال: {metrics.get('daily_active_users', 0)}\n"
            text += f"• حجم منتقل شده: {metrics.get('daily_transfer', '0 GB')}\n\n"
            
            text += f"💾 **وضعیت Cache:**\n"
            text += f"• استفاده از فضا: {metrics.get('cache_usage_percent', '0')}%\n"
            text += f"• فایل‌های Cache شده: {metrics.get('cached_files', 0)}\n"
            text += f"• Hit Rate: {metrics.get('cache_hit_rate', '0')}%"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data="system_monitoring"),
                    InlineKeyboardButton("📊 نمودارها", callback_data="system_charts")
                ],
                [
                    InlineKeyboardButton("⚠️ هشدارها", callback_data="system_alerts"),
                    InlineKeyboardButton("🔧 تنظیمات نظارت", callback_data="monitoring_settings")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="download_system_control")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def system_cleanup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پاکسازی Cache سیستم"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update, "در حال پاکسازی Cache...")
            
            # فراخوانی API پاکسازی
            cleanup_result = await self.cleanup_system_cache()
            
            if cleanup_result.get('success'):
                text = f"🧹 **پاکسازی Cache انجام شد**\n\n"
                text += f"🗑 **فایل‌های پاک شده:** {cleanup_result.get('cleaned_files', 0)}\n"
                text += f"💾 **فضای آزاد شده:** {cleanup_result.get('freed_space', '0 MB')}\n"
                text += f"⏱ **زمان پاکسازی:** {cleanup_result.get('cleanup_time', '0')} ثانیه\n\n"
                text += "✅ پاکسازی با موفقیت انجام شد!"
            else:
                text = f"❌ خطا در پاکسازی: {cleanup_result.get('error', 'نامشخص')}"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 پاکسازی دوباره", callback_data="system_cleanup"),
                    InlineKeyboardButton("📊 وضعیت Cache", callback_data="cache_status")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="download_system_control")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def get_system_status(self) -> dict:
        """دریافت وضعیت سیستم از API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/health") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {
                            'ready': False,
                            'status': f'خطا {response.status}',
                            'error': 'دسترسی به API ممکن نیست'
                        }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'ready': False,
                'status': 'خطا در اتصال',
                'error': str(e)
            }
    
    async def get_real_time_metrics(self) -> dict:
        """دریافت metrics لحظه‌ای"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/system/metrics", 
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {}
        except Exception as e:
            logger.error(f"Error getting real-time metrics: {e}")
            return {}
    
    async def create_download_link_via_api(self, link_data: dict) -> dict:
        """ایجاد لینک دانلود از طریق API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/download/links/create",
                    headers=self.headers,
                    json=link_data
                ) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Error creating download link: {e}")
            return {'success': False, 'error': str(e)}
    
    async def cleanup_system_cache(self) -> dict:
        """پاکسازی Cache سیستم از طریق API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/system/cleanup",
                    headers=self.headers
                ) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
            return {'success': False, 'error': str(e)}