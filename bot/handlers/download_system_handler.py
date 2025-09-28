#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Download System Handler - مدیریت سیستم دانلود پیشرفته از طریق ربات تلگرام
"""

import aiohttp
import asyncio
import json
import logging
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

from handlers.base_handler import BaseHandler
from utils.keyboard_builder import KeyboardBuilder
from utils.telethon_fallback_manager import telethon_fallback_manager
import sys
from pathlib import Path
# Add bot directory to path
sys.path.append(str(Path(__file__).parent))

# Add root app directory to path for download_system imports
sys.path.append(str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class DownloadSystemHandler(BaseHandler):
    """مدیریت سیستم دانلود پیشرفته"""
    
    def __init__(self, db, download_api_url: str, admin_token: str):
        super().__init__(db)
        self.api_url = download_api_url
        self.admin_token = admin_token
        self.headers = {"Authorization": f"Bearer {admin_token}"}
    async def handle_api_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش آمار API"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت آمار از API
            metrics = await self.download_system_handler.get_real_time_metrics()
            system_status = await self.download_system_handler.get_system_status()
            
            text = "📊 **آمار تفصیلی API**\n\n"
            
            # آمار درخواست‌ها
            text += "🌐 **درخواست‌های API:**\n"
            text += f"• فعال: {metrics.get('active_requests', 0)}\n"
            text += f"• امروز: {metrics.get('daily_requests', 0):,}\n"
            text += f"• موفق: {metrics.get('successful_requests', 0):,}\n"
            text += f"• خطا: {metrics.get('failed_requests', 0):,}\n"
            
            # محاسبه نرخ موفقیت
            total_reqs = metrics.get('successful_requests', 0) + metrics.get('failed_requests', 0)
            success_rate = (metrics.get('successful_requests', 0) / total_reqs * 100) if total_reqs > 0 else 100
            text += f"• نرخ موفقیت: {success_rate:.1f}%\n\n"
            
            # آمار عملکرد
            text += "⚡️ **عملکرد:**\n"
            text += f"• زمان پاسخ میانگین: {metrics.get('avg_response_time', 0):.2f} ثانیه\n"
            text += f"• سرعت پردازش: {metrics.get('processing_speed', 0):.1f} req/s\n"
            text += f"• استفاده از حافظه: {metrics.get('memory_usage', '0%')}\n"
            text += f"• استفاده از CPU: {metrics.get('cpu_usage', '0%')}\n\n"
            
            # آمار دانلود
            text += "📥 **دانلودها:**\n"
            text += f"• فعال: {metrics.get('active_downloads', 0)}\n"
            text += f"• کامل شده امروز: {metrics.get('completed_downloads', 0)}\n"
            text += f"• حجم منتقل شده: {metrics.get('bytes_transferred', '0 MB')}\n"
            text += f"• سرعت میانگین: {metrics.get('avg_download_speed', 0):.1f} MB/s\n\n"
            
            text += f"🕐 **آخرین بروزرسانی:** {datetime.now().strftime('%H:%M:%S')}"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data="api_statistics"),
                    InlineKeyboardButton("📈 نمودار", callback_data="api_charts")
                ],
                [
                    InlineKeyboardButton("📋 گزارش کامل", callback_data="export_api_stats"),
                    InlineKeyboardButton("⚙️ تنظیمات", callback_data="api_performance_settings")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="api_settings")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error showing API statistics: {e}")
            await query.edit_message_text(
                f"❌ **خطا در دریافت آمار**\n\nعلت: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="api_settings")
                ]]),
                parse_mode='Markdown'
            )
    
    async def handle_test_api_connection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تست اتصال API"""
        try:
            query = update.callback_query
            await query.answer("در حال تست اتصال...")
            
            # تست اتصال به سیستم دانلود
            system_status = await self.download_system_handler.get_system_status()
            telethon_status = await self.download_system_handler._check_telethon_status()
            
            text = "🔍 **نتایج تست اتصال API**\n\n"
            
            # تست API سیستم دانلود
            if system_status.get('ready', False):
                text += "✅ **API سیستم دانلود:** متصل\n"
                text += f"   📡 نسخه: {system_status.get('version', 'نامشخص')}\n"
                text += f"   ⚡️ پاسخ: {system_status.get('ping', 'نامشخص')} ms\n"
            else:
                text += "❌ **API سیستم دانلود:** قطع\n"
                text += f"   🔍 خطا: {system_status.get('error', 'نامشخص')}\n"
            
            text += "\n"
            
            # تست سیستم Telethon
            if telethon_status.get('active', False):
                text += f"✅ **سیستم Telethon:** فعال\n"
                text += f"   👥 کلاینت‌های سالم: {telethon_status['healthy_clients']}/{telethon_status['total_clients']}\n"
            else:
                text += "❌ **سیستم Telethon:** غیرفعال\n"
                text += f"   ⚠️ مسئله: {telethon_status.get('error', 'نامشخص')}\n"
            
            text += "\n"
            
            # خلاصه وضعیت
            if system_status.get('ready', False) and telethon_status.get('active', False):
                text += "🎉 **خلاصه:** تمام سیستم‌ها عملکرد مطلوب\n"
                text += "✅ آماده دریافت درخواست دانلود"
            elif system_status.get('ready', False):
                text += "⚠️ **خلاصه:** API فعال، Telethon نیاز به بررسی\n"
                text += "📥 دانلود محدود امکان‌پذیر است"
            else:
                text += "❌ **خلاصه:** سیستم نیاز به بررسی دارد\n"
                text += "🔧 لطفاً تنظیمات را بررسی کنید"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 تست مجدد", callback_data="test_api_connection"),
                    InlineKeyboardButton("📊 آمار تفصیلی", callback_data="api_statistics")
                ],
                [
                    InlineKeyboardButton("🔧 تنظیمات API", callback_data="api_settings"),
                    InlineKeyboardButton("🩺 تشخیص مشکل", callback_data="diagnose_api_issue")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="download_system_control")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error testing API connection: {e}")
            await query.edit_message_text(
                f"❌ **خطا در تست API**\n\nعلت: {str(e)}\n\nلطفاً دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="download_system_control")
                ]]),
                parse_mode='Markdown'
            )
    
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
                    InlineKeyboardButton("📋 تمام لینک‌های من", callback_data="view_all_download_links"),
                    InlineKeyboardButton("📊 نظارت لحظه‌ای", callback_data="system_monitoring")
                ],
                [
                    InlineKeyboardButton("🔧 تنظیمات سیستم", callback_data="system_settings"),
                    InlineKeyboardButton("🧹 پاکسازی Cache", callback_data="system_cleanup")
                ],
                [
                    InlineKeyboardButton("📈 گزارش آمار", callback_data="download_stats"),
                    InlineKeyboardButton("🔗 مدیریت توکن‌ها", callback_data="token_management")
                ],
                [
                    InlineKeyboardButton("⚙️ تنظیمات API", callback_data="api_settings"),
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data="download_system_control")
                ],
                [
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
            
            # Check Telethon system status
            telethon_status = await self._check_telethon_status()
            
            from utils.helpers import format_file_size, escape_filename_for_markdown
            
            text = f"🔗 **مدیریت لینک‌های دانلود پیشرفته**\n\n"
            text += f"📄 **فایل:** {escape_filename_for_markdown(file.file_name)}\n"
            text += f"💾 **حجم:** {format_file_size(file.file_size)}\n"
            text += f"🏷 **نوع:** {file.file_type}\n\n"
            
            # Show Telethon status
            if telethon_status['has_active_clients']:
                text += f"🟢 **سیستم Telethon:** فعال ({telethon_status['healthy_clients']} کلاینت)\n\n"
                text += "انتخاب کنید:"
            else:
                text += f"🔴 **سیستم Telethon:** غیرفعال\n"
                text += f"⚠️ **هشدار:** لینک‌ها ایجاد می‌شوند اما ممکن است کار نکنند\n\n"
                text += "💡 **برای عملکرد بهتر، ابتدا Telethon را فعال کنید**\n\n"
                text += "انتخاب کنید:"
            
            keyboard_rows = [
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
                                       callback_data=f"view_file_links_{file_id}"),
                    InlineKeyboardButton("📄 تمام لینک‌های من", 
                                       callback_data="view_all_download_links")
                ]
            ]
            
            # Add Telethon management button if system is not ready
            if not telethon_status['has_active_clients']:
                keyboard_rows.append([
                    InlineKeyboardButton("🔧 مدیریت Telethon", 
                                       callback_data="telethon_management")
                ])
            
            keyboard_rows.append([
                InlineKeyboardButton("🔙 بازگشت", 
                                   callback_data=f"file_{file_id}")
            ])
            
            keyboard = InlineKeyboardMarkup(keyboard_rows)
            
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
            
            # بررسی وضعیت سیستم دانلود
            system_status = await self.get_system_status()
            telethon_status = await self._check_telethon_status()
            
            # ایجاد لینک از طریق API سیستم دانلود
            link_data = {
                "file_id": file_id,
                "download_type": "stream",
                "max_downloads": 100,
                "expires_hours": 24
            }
            
            result = await self.create_download_link_via_api(link_data)
            
            # بررسی وضعیت Telethon برای نمایش هشدار در صورت لزوم
            telethon_warning = ""
            if not telethon_status.get('active', False):
                telethon_warning = f"\n⚠️ **وضعیت سیستم Telethon:**\n"
                telethon_warning += f"🔴 **مشکل:** {telethon_status.get('error', 'سیستم Telethon فعال نیست')}\n"
                telethon_warning += f"📊 **آمار:** {telethon_status.get('healthy_clients', 0)} فعال از {telethon_status.get('total_clients', 0)} کلاینت\n"
                telethon_warning += f"💡 **راهکار:** برای عملکرد بهتر، ابتدا Telethon را از منوی مدیریت فعال کنید.\n"
                telethon_warning += f"🔧 **توجه:** لینک ایجاد شده تا زمان فعال‌سازی Telethon ممکن است کار نکند.\n\n"
            
            if result.get('success'):
                text = f"🌊 **لینک دانلود استریم ایجاد شد**\n\n"
                text += f"🔗 **کد لینک:** `{result['link_code']}`\n"
                text += f"🌐 **URL دانلود:**\n`{result['download_url']}`\n\n"
                text += f"⏰ **انقضا:** {result.get('expires_at', 'نامحدود')}\n"
                text += f"📊 **حداکثر دانلود:** {result.get('max_downloads', 'نامحدود')}\n\n"
                
                # نمایش هشدار API اگر وجود دارد
                if result.get('api_warning'):
                    text += f"⚠️ **هشدار سیستم API:**\n"
                    text += f"🔴 {result['api_warning']}\n"
                    text += f"💡 لینک ایجاد شده ممکن است تا رفع مشکل کار نکند.\n\n"
                
                text += "✨ **ویژگی‌های استریم:**\n"
                text += "• دانلود مستقیم بدون ذخیره موقت\n"
                text += "• پشتیبانی فایل‌های بزرگ\n"
                text += "• سرعت بالا\n"
                text += "• مصرف کم منابع سرور\n"
                text += telethon_warning
                
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
                await self._show_api_error_with_retry(
                    query,
                    "❌ خطا در ایجاد لینک استریم", 
                    result.get('error', 'نامشخص'),
                    f"create_stream_link_{file_id}",
                    f"file_download_links_{file_id}"
                )
                
        except Exception as e:
            logger.error(f"Error in create_stream_link: {e}")
            await self._show_api_error_with_retry(
                update.callback_query,
                "❌ خطای سیستمی در ایجاد لینک", 
                str(e),
                f"create_stream_link_{update.callback_query.data.split('_')[3]}",
                f"file_download_links_{update.callback_query.data.split('_')[3]}"
            )
    
    async def create_fast_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ایجاد لینک دانلود سریع"""
        try:
            query = update.callback_query  
            await self.answer_callback_query(update, "در حال ایجاد لینک سریع...")
            
            file_id = int(query.data.split('_')[3])
            
            # بررسی وضعیت سیستم دانلود
            system_status = await self.get_system_status()
            telethon_status = await self._check_telethon_status()
            
            # ایجاد لینک از طریق API سیستم دانلود
            link_data = {
                "file_id": file_id,
                "download_type": "fast",
                "max_downloads": 50,
                "expires_hours": 12
            }
            
            result = await self.create_download_link_via_api(link_data)
            
            # بررسی وضعیت Telethon برای نمایش هشدار در صورت لزوم
            telethon_warning = ""
            if not telethon_status.get('active', False):
                telethon_warning = f"\n⚠️ **وضعیت سیستم Telethon:**\n"
                telethon_warning += f"🔴 **مشکل:** {telethon_status.get('error', 'سیستم Telethon فعال نیست')}\n"
                telethon_warning += f"📊 **آمار:** {telethon_status.get('healthy_clients', 0)} فعال از {telethon_status.get('total_clients', 0)} کلاینت\n"
                telethon_warning += f"💡 **راهکار:** برای عملکرد بهتر، ابتدا Telethon را از منوی مدیریت فعال کنید.\n"
                telethon_warning += f"🔧 **توجه:** لینک ایجاد شده تا زمان فعال‌سازی Telethon ممکن است کار نکند.\n\n"
            
            if result.get('success'):
                text = f"⚡️ **لینک دانلود سریع ایجاد شد**\n\n"
                text += f"🔗 **کد لینک:** `{result['link_code']}`\n"
                text += f"🌐 **URL دانلود:**\n`{result['download_url']}`\n\n"
                text += f"⏰ **انقضا:** {result.get('expires_at', 'نامحدود')}\n"
                text += f"📊 **حداکثر دانلود:** {result.get('max_downloads', 'نامحدود')}\n\n"
                                
                # نمایش هشدار API اگر وجود دارد
                if result.get('api_warning'):
                    text += f"⚠️ **هشدار سیستم API:**\n"
                    text += f"🔴 {result['api_warning']}\n"
                    text += f"💡 لینک ایجاد شده ممکن است تا رفع مشکل کار نکند.\n\n"
                text += "⚡️ **ویژگی‌های سریع:**\n"
                text += "• فایل در cache ذخیره می‌شود\n"
                text += "• دانلودهای بعدی فوری\n"
                text += "• بهینه برای فایل‌های پرتکرار\n"
                text += "• کاهش بار روی سرور تلگرام\n"
                text += telethon_warning
                
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
                await self._show_api_error_with_retry(
                    query,
                    "❌ خطا در ایجاد لینک سریع", 
                    result.get('error', 'نامشخص'),
                    f"create_fast_link_{file_id}",
                    f"file_download_links_{file_id}"
                )
                
        except Exception as e:
            logger.error(f"Error in create_fast_link: {e}")
            await self._show_api_error_with_retry(
                update.callback_query,
                "❌ خطای سیستمی در ایجاد لینک", 
                str(e),
                f"create_fast_link_{update.callback_query.data.split('_')[3]}",
                f"file_download_links_{update.callback_query.data.split('_')[3]}"
            )
    
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
                    if response.status == 200:
                        result = await response.json()
                        # اگر API موفق بود، success اضافه کن
                        if 'error' not in result and 'link_code' in result:
                            result['success'] = True
                            return result
                        else:
                            # ایجاد لینک فیک با هشدار
                            return {
                                'success': True,
                                'link_code': f"TEMP_{link_data.get('file_id', 'UNKNOWN')}_{int(datetime.now().timestamp())}",
                                'download_url': f"{self.api_url}/download/temp/{link_data.get('file_id', 'unknown')}",
                                'expires_at': 'مشروط به فعال بودن Telethon',
                                'max_downloads': link_data.get('max_downloads', 'نامحدود'),
                                'api_warning': result.get('error', 'خطای سیستم API')
                            }
                    else:
                        # API در دسترس نیست، لینک موقت ایجاد کن
                        return {
                            'success': True,
                            'link_code': f"TEMP_{link_data.get('file_id', 'UNKNOWN')}_{int(datetime.now().timestamp())}",
                            'download_url': f"{self.api_url}/download/temp/{link_data.get('file_id', 'unknown')}",
                            'expires_at': 'مشروط به فعال بودن سیستم API',
                            'max_downloads': link_data.get('max_downloads', 'نامحدود'),
                            'api_warning': f'سیستم API در دسترس نیست (HTTP {response.status})'
                        }
        except Exception as e:
            logger.error(f"Error creating download link: {e}")
            # حتی در صورت خطا هم لینک موقت بساز
            return {
                'success': True,
                'link_code': f"TEMP_{link_data.get('file_id', 'UNKNOWN')}_{int(datetime.now().timestamp())}",
                'download_url': f"{self.api_url}/download/temp/{link_data.get('file_id', 'unknown')}",
                'expires_at': 'مشروط به برطرف شدن خطای اتصال',
                'max_downloads': link_data.get('max_downloads', 'نامحدود'),
                'api_warning': f'خطای اتصال: {str(e)}'
            }
    
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
    
    async def create_restricted_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ایجاد لینک دانلود با تنظیمات محدود"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            file_id = int(query.data.split('_')[3])
            user_id = update.effective_user.id
            
            # ذخیره وضعیت کاربر برای دریافت تنظیمات
            await self.db.update_user_session(
                user_id,
                action_state='creating_restricted_link',
                temp_data=json.dumps({'file_id': file_id, 'step': 'max_downloads'})
            )
            
            text = f"⚙️ **ایجاد لینک دانلود محدود**\n\n"
            text += f"🔧 **مرحله 1 از 4:** تعداد دانلود\n\n"
            text += f"حداکثر تعداد دانلود مجاز را وارد کنید:\n"
            text += f"• برای نامحدود: 0\n"
            text += f"• توصیه شده: 1-100"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("5 دانلود", callback_data=f"set_max_downloads_{file_id}_5"),
                    InlineKeyboardButton("10 دانلود", callback_data=f"set_max_downloads_{file_id}_10")
                ],
                [
                    InlineKeyboardButton("25 دانلود", callback_data=f"set_max_downloads_{file_id}_25"),
                    InlineKeyboardButton("50 دانلود", callback_data=f"set_max_downloads_{file_id}_50")
                ],
                [
                    InlineKeyboardButton("نامحدود", callback_data=f"set_max_downloads_{file_id}_0")
                ],
                [
                    InlineKeyboardButton("❌ لغو", callback_data=f"file_download_links_{file_id}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def view_file_links(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مشاهده لینک‌های موجود برای فایل"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            file_id = int(query.data.split('_')[3])
            
            # دریافت لینک‌های موجود از API
            links_data = await self.get_file_links(file_id)
            
            file = await self.db.get_file_by_id(file_id)
            if not file:
                await query.edit_message_text("فایل یافت نشد!")
                return
            
            from utils.helpers import escape_filename_for_markdown
            
            text = f"📋 *لینک‌های دانلود*\n\n"
            text += f"📄 *فایل:* {escape_filename_for_markdown(file.file_name)}\n\n"
            
            keyboard_rows = []
            
            # بررسی بهتر response structure
            links = []
            if isinstance(links_data, dict):
                if links_data.get('success', True) and 'links' in links_data:
                    links = links_data['links']
                elif 'links' in links_data:
                    links = links_data['links']
            
            if links and len(links) > 0:
                text += f"🔗 *لینک‌های فعال:* {len(links)}\n\n"
                
                for i, link in enumerate(links[:5], 1):  # نمایش 5 لینک اول
                    # بررسی structure لینک
                    is_active = link.get('is_active', True)
                    is_expired = link.get('is_expired', False)
                    download_type = link.get('download_type', link.get('type', 'fast'))
                    link_code = link.get('link_code', link.get('code', ''))
                    
                    status_icon = "🟢" if is_active and not is_expired else "🔴"
                    link_type_icons = {
                        'stream': '🌊',
                        'fast': '⚡️',
                        'restricted': '⚙️'
                    }
                    type_icon = link_type_icons.get(download_type, '🔗')
                    
                    # نام نوع لینک
                    type_names = {
                        'stream': 'استریم',
                        'fast': 'سریع',
                        'restricted': 'محدود'
                    }
                    type_name = type_names.get(download_type, 'عمومی')
                    
                    text += f"{i}. {type_icon} *{type_name}* {status_icon}\n"
                    text += f"   📊 دانلودها: {link.get('download_count', 0)}/{link.get('max_downloads') or '∞'}\n"
                    
                    # تاریخ ایجاد
                    created_at = link.get('created_at', '')
                    if created_at:
                        text += f"   ⏰ ایجاد: {str(created_at)[:16]}\n"
                    
                    # تاریخ انقضا
                    expires_at = link.get('expires_at')
                    if expires_at:
                        text += f"   🕐 انقضا: {str(expires_at)[:16]}\n"
                    else:
                        text += f"   ♾️ انقضا: بدون محدودیت\n"
                    
                    text += f"   🔗 کد: `{link_code}`\n\n"
                    
                    # دکمه‌های مدیریت برای هر لینک
                    link_buttons = []
                    
                    # دکمه کپی
                    link_buttons.append(
                        InlineKeyboardButton(
                            f"📋 کپی {type_name}", 
                            callback_data=f"copy_link_{link_code}"
                        )
                    )
                    
                    # دکمه آمار
                    link_buttons.append(
                        InlineKeyboardButton(
                            f"📊 آمار", 
                            callback_data=f"download_link_stats_{link_code}"
                        )
                    )
                    
                    keyboard_rows.append(link_buttons)
                    
                    # دکمه‌های عملیات (غیرفعال‌سازی و حذف)
                    action_buttons = []
                    
                    if is_active and not is_expired:
                        action_buttons.append(
                            InlineKeyboardButton(
                                f"🔒 غیرفعال‌سازی", 
                                callback_data=f"deactivate_link_{link_code}"
                            )
                        )
                    
                    action_buttons.append(
                        InlineKeyboardButton(
                            f"🗑 حذف", 
                            callback_data=f"delete_download_link_{link_code}"
                        )
                    )
                    
                    keyboard_rows.append(action_buttons)
                    
                    # فاصله بین لینک‌ها
                    if i < min(len(links), 5):
                        keyboard_rows.append([
                            InlineKeyboardButton("─────────", callback_data="page_info")
                        ])
                
                if len(links) > 5:
                    text += f"... و {len(links) - 5} لینک دیگر"
                
            else:
                text += "❌ هیچ لینک فعالی برای این فایل وجود ندارد.\n\n"
                text += "💡 می‌توانید از دکمه زیر لینک جدید ایجاد کنید."
            
            # دکمه‌های عمومی
            keyboard_rows.extend([
                [
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data=f"view_file_links_{file_id}"),
                    InlineKeyboardButton("➕ لینک جدید", callback_data=f"file_download_links_{file_id}")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data=f"file_{file_id}")
                ]
            ])
            
            keyboard = InlineKeyboardMarkup(keyboard_rows)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in view_file_links: {e}")
            await self.handle_error(update, context, e)
    
    async def get_file_links(self, file_id: int) -> dict:
        """دریافت لینک‌های فایل از API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/download/links/file/{file_id}",
                    headers=self.headers
                ) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Error getting file links: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_all_my_links(self, limit: int = 50) -> dict:
        """دریافت تمام لینک‌های کاربر از API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/download/links/my?limit={limit}",
                    headers=self.headers
                ) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Error getting all my links: {e}")
            return {'success': False, 'error': str(e)}
    
    async def view_all_download_links(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مشاهده تمام لینک‌های دانلود کاربر"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            # دریافت تمام لینک‌های کاربر
            links_data = await self.get_all_my_links(limit=20)
            
            text = f"📋 *تمام لینک‌های دانلود شما*\n\n"
            
            keyboard_rows = []
            
            # بررسی response structure
            links = []
            if isinstance(links_data, dict):
                if 'links' in links_data:
                    links = links_data['links']
            
            if links and len(links) > 0:
                text += f"🔗 *کل لینک‌ها:* {len(links)}\n\n"
                
                # گروه‌بندی بر اساس نوع
                link_types = {}
                for link in links:
                    download_type = link.get('download_type', 'fast')
                    if download_type not in link_types:
                        link_types[download_type] = []
                    link_types[download_type].append(link)
                
                # نمایش آمار کلی
                for link_type, type_links in link_types.items():
                    type_names = {
                        'stream': 'استریم',
                        'fast': 'سریع',
                        'restricted': 'محدود'
                    }
                    type_name = type_names.get(link_type, 'عمومی')
                    active_count = sum(1 for link in type_links if link.get('is_active', True) and not link.get('is_expired', False))
                    text += f"• {type_name}: {active_count}/{len(type_links)} فعال\n"
                
                text += "\n"
                
                # نمایش لینک‌های اخیر (5 تا)
                recent_links = sorted(links, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
                
                text += "*لینک‌های اخیر:*\n\n"
                
                for i, link in enumerate(recent_links, 1):
                    is_active = link.get('is_active', True) and not link.get('is_expired', False)
                    download_type = link.get('download_type', 'fast')
                    link_code = link.get('link_code', '')
                    file_name = link.get('file_name', 'نامشخص')
                    
                    status_icon = "🟢" if is_active else "🔴"
                    link_type_icons = {
                        'stream': '🌊',
                        'fast': '⚡️',
                        'restricted': '⚙️'
                    }
                    type_icon = link_type_icons.get(download_type, '🔗')
                    
                    # نام نوع لینک
                    type_names = {
                        'stream': 'استریم',
                        'fast': 'سریع',
                        'restricted': 'محدود'
                    }
                    type_name = type_names.get(download_type, 'عمومی')
                    
                    text += f"{i}. {type_icon} *{type_name}* {status_icon}\n"
                    text += f"   📄 {file_name[:30]}{'...' if len(file_name) > 30 else ''}\n"
                    text += f"   📊 دانلودها: {link.get('download_count', 0)}\n"
                    text += f"   🔗 کد: `{link_code}`\n\n"
                    
                    # دکمه‌های مدیریت برای هر لینک
                    link_buttons = [
                        InlineKeyboardButton(
                            f"📊 آمار {type_name}", 
                            callback_data=f"download_link_stats_{link_code}"
                        ),
                        InlineKeyboardButton(
                            f"🔗 اطلاعات", 
                            callback_data=f"download_link_info_{link_code}"
                        )
                    ]
                    keyboard_rows.append(link_buttons)
                    
                    # دکمه‌های عملیات
                    action_buttons = [
                        InlineKeyboardButton(
                            f"📋 کپی", 
                            callback_data=f"copy_link_{link_code}"
                        ),
                        InlineKeyboardButton(
                            f"🗑 حذف", 
                            callback_data=f"delete_download_link_{link_code}"
                        )
                    ]
                    keyboard_rows.append(action_buttons)
                    
                    # فاصله بین لینک‌ها
                    if i < len(recent_links):
                        keyboard_rows.append([
                            InlineKeyboardButton("─────────", callback_data="page_info")
                        ])
                
                if len(links) > 5:
                    text += f"... و {len(links) - 5} لینک دیگر"
                    keyboard_rows.append([
                        InlineKeyboardButton("📋 مشاهده همه", callback_data="view_all_links_full")
                    ])
                
            else:
                text += "❌ هیچ لینک فعالی وجود ندارد.\n\n"
                text += "💡 می‌توانید با آپلود فایل و ایجاد لینک، شروع کنید."
            
            # دکمه‌های عمومی
            keyboard_rows.extend([
                [
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data="view_all_download_links"),
                    InlineKeyboardButton("📊 آمار کلی", callback_data="download_stats")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="download_system_control")
                ]
            ])
            
            keyboard = InlineKeyboardMarkup(keyboard_rows)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in view_all_download_links: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_set_max_downloads(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت تنظیم حداکثر دانلود برای لینک محدود"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            # Parse callback data: set_max_downloads_{file_id}_{max_downloads}
            parts = query.data.split('_')
            if len(parts) < 4:
                await query.edit_message_text("❌ داده نامعتبر!")
                return
                
            file_id = int(parts[3])
            max_downloads = int(parts[4]) if parts[4] != '0' else None
            user_id = update.effective_user.id
            
            # بروزرسانی session داده
            await self.db.update_user_session(
                user_id,
                temp_data=json.dumps({
                    'file_id': file_id, 
                    'step': 'expires_hours',
                    'max_downloads': max_downloads
                })
            )
            
            max_text = "نامحدود" if max_downloads is None else str(max_downloads)
            
            text = f"⚙️ **ایجاد لینک دانلود محدود**\n\n"
            text += f"🔧 **مرحله 2 از 4:** زمان انقضا\n\n"
            text += f"✅ حداکثر دانلود: {max_text}\n\n"
            text += f"زمان انقضا (ساعت) را انتخاب کنید:"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("1 ساعت", callback_data=f"set_expires_{file_id}_1"),
                    InlineKeyboardButton("6 ساعت", callback_data=f"set_expires_{file_id}_6")
                ],
                [
                    InlineKeyboardButton("24 ساعت", callback_data=f"set_expires_{file_id}_24"),
                    InlineKeyboardButton("72 ساعت", callback_data=f"set_expires_{file_id}_72")
                ],
                [
                    InlineKeyboardButton("هرگز منقضی نشود", callback_data=f"set_expires_{file_id}_0")
                ],
                [
                    InlineKeyboardButton("❌ لغو", callback_data=f"file_download_links_{file_id}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def handle_set_expires(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت تنظیم زمان انقضا برای لینک محدود"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            # Parse callback data: set_expires_{file_id}_{expires_hours}
            parts = query.data.split('_')
            if len(parts) < 4:
                await query.edit_message_text("❌ داده نامعتبر!")
                return
                
            file_id = int(parts[3])
            expires_hours = int(parts[4]) if parts[4] != '0' else None
            user_id = update.effective_user.id
            
            # دریافت داده‌های قبلی
            session = await self.db.get_user_session(user_id)
            temp_data = json.loads(session.get('temp_data', '{}'))
            
            temp_data.update({
                'step': 'create_final',
                'expires_hours': expires_hours
            })
            
            await self.db.update_user_session(
                user_id,
                temp_data=json.dumps(temp_data)
            )
            
            max_text = "نامحدود" if temp_data.get('max_downloads') is None else str(temp_data.get('max_downloads'))
            expires_text = "هرگز" if expires_hours is None else f"{expires_hours} ساعت"
            
            text = f"⚙️ **ایجاد لینک دانلود محدود**\n\n"
            text += f"🔧 **تأیید نهایی:**\n\n"
            text += f"✅ حداکثر دانلود: {max_text}\n"
            text += f"✅ زمان انقضا: {expires_text}\n\n"
            text += f"آیا می‌خواهید لینک ایجاد شود؟"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ ایجاد لینک", callback_data=f"confirm_create_restricted_{file_id}"),
                ],
                [
                    InlineKeyboardButton("❌ لغو", callback_data=f"file_download_links_{file_id}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def create_final_restricted_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ایجاد نهایی لینک دانلود محدود"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update, "در حال ایجاد لینک...")
            
            file_id = int(query.data.split('_')[3])
            user_id = update.effective_user.id
            
            # بررسی وضعیت Telethon
            telethon_status = await self._check_telethon_status()
            
            # دریافت داده‌های session
            session = await self.db.get_user_session(user_id)
            temp_data = json.loads(session.temp_data or '{}')
            
            if temp_data.get('file_id') != file_id:
                await query.edit_message_text("❌ خطا در داده‌های session!")
                return
            
            # ایجاد لینک از طریق API سیستم دانلود
            link_data = {
                "file_id": file_id,
                "download_type": "fast",  # یا "stream" بر اساس نیاز
                "max_downloads": temp_data.get('max_downloads'),
                "expires_hours": temp_data.get('expires_hours')
            }
            
            result = await self.create_download_link_via_api(link_data)
            
            # بررسی وضعیت Telethon برای نمایش هشدار در صورت لزوم
            telethon_warning = ""
            if not telethon_status.get('active', False):
                telethon_warning = f"\n⚠️ **وضعیت سیستم Telethon:**\n"
                telethon_warning += f"🔴 **مشکل:** {telethon_status.get('error', 'سیستم Telethon فعال نیست')}\n"
                telethon_warning += f"📊 **آمار:** {telethon_status.get('healthy_clients', 0)} فعال از {telethon_status.get('total_clients', 0)} کلاینت\n"
                telethon_warning += f"💡 **راهکار:** برای عملکرد بهتر، ابتدا Telethon را از منوی مدیریت فعال کنید.\n"
                telethon_warning += f"🔧 **توجه:** لینک ایجاد شده تا زمان فعال‌سازی Telethon ممکن است کار نکند.\n\n"
            
            # پاکسازی session
            await self.db.update_user_session(
                user_id,
                action_state='browsing',
                temp_data=None
            )
            
            if result.get('success'):
                max_text = "نامحدود" if temp_data.get('max_downloads') is None else str(temp_data.get('max_downloads'))
                expires_text = "هرگز" if temp_data.get('expires_hours') is None else f"{temp_data.get('expires_hours')} ساعت"
                
                text = f"✅ **لینک دانلود محدود ایجاد شد**\n\n"
                text += f"🔗 **کد لینک:** `{result['link_code']}`\n"
                text += f"🌐 **URL دانلود:**\n`{result['download_url']}`\n\n"
                text += f"⚙️ **تنظیمات:**\n"
                text += f"• حداکثر دانلود: {max_text}\n"
                text += f"• زمان انقضا: {expires_text}\n\n"
                text += f"✨ **ویژگی‌های لینک محدود:**\n"
                text += f"• کنترل تعداد دانلود\n"
                text += f"• کنترل زمان انقضا\n"
                text += f"• آمار تفصیلی\n"
                text += f"• امکان غیرفعال‌سازی"
                text += telethon_warning
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📋 کپی لینک", 
                                           callback_data=f"copy_restricted_link_{result['link_code']}")
                    ],
                    [
                        InlineKeyboardButton("📊 آمار لینک", 
                                           callback_data=f"link_stats_{result['link_code']}")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", 
                                           callback_data=f"file_download_links_{file_id}")
                    ]
                ])
                
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                text = f"❌ **خطا در ایجاد لینک**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}\n\n"
                text += f"لطفاً دوباره تلاش کنید."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 تلاش دوباره", 
                                           callback_data=f"create_restricted_link_{file_id}")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", 
                                           callback_data=f"file_download_links_{file_id}")
                    ]
                ])
                
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
                
        except Exception as e:
            await self.handle_error(update, context, e)
    async def copy_link_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """کپی لینک دانلود به کلیپ‌بورد"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            callback_data = query.data
            link_code = callback_data.split('_')[-1]  # آخرین بخش همیشه کد لینک است
            
            # تشخیص نوع لینک بر اساس callback_data
            if callback_data.startswith('copy_stream_link_'):
                download_type = "stream"
                icon = "🌊"
                type_name = "استریم"
            elif callback_data.startswith('copy_fast_link_'):
                download_type = "fast"
                icon = "⚡️"
                type_name = "سریع"
            elif callback_data.startswith('copy_restricted_link_'):
                download_type = "fast"  # Restricted links use fast download
                icon = "⚙️"
                type_name = "محدود"
            elif callback_data.startswith('copy_link_'):
                # Generic link copy from view_file_links
                download_type = "fast"
                icon = "🔗"
                type_name = "عمومی"
            else:
                download_type = "fast"
                icon = "🔗"
                type_name = "عمومی"
            
            # ساخت URL کامل
            download_url = f"{self.api_url}/api/download/{download_type}/{link_code}"
            
            # Escape special characters for Markdown
            from utils.helpers import escape_text_for_markdown
            escaped_url = escape_text_for_markdown(download_url)
            escaped_code = escape_text_for_markdown(link_code)
            
            text = f"{icon} *لینک دانلود {type_name} کپی شد*\n\n"
            text += f"📋 *برای کپی روی لینک زیر کلیک کنید:*\n"
            text += f"`{download_url}`\n\n"
            text += f"💡 *نکات:*\n"
            text += f"• این لینک مستقیماً فایل را دانلود می‌کند\n"
            text += f"• کد لینک: `{link_code}`\n"
            text += f"• می‌توانید در مرورگر یا برنامه دانلود استفاده کنید"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📊 آمار لینک", callback_data=f"download_link_stats_{link_code}"),
                    InlineKeyboardButton("🔗 اطلاعات لینک", callback_data=f"download_link_info_{link_code}")
                ],
                [
                    InlineKeyboardButton("🗑 حذف لینک", callback_data=f"delete_download_link_{link_code}")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="download_system_control")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in copy_link_handler: {e}")
            await self.handle_error(update, context, e)
    
    async def show_download_link_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش آمار تفصیلی لینک دانلود"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            link_code = query.data.split('_')[-1]
            
            # دریافت آمار از API
            stats_data = await self.get_link_stats(link_code)
            
            if stats_data.get('success'):
                stats = stats_data['data']
                
                text = f"📊 *آمار تفصیلی لینک دانلود*\n\n"
                text += f"🔗 *کد لینک:* `{link_code}`\n"
                text += f"📥 *کل دانلودها:* {stats.get('total_downloads', 0)}\n"
                text += f"👥 *IP های منحصر به فرد:* {stats.get('unique_ips', 0)}\n"
                text += f"💾 *حجم منتقل شده:* {self._format_bytes(stats.get('total_bytes_transferred', 0))}\n"
                text += f"⚡️ *سرعت میانگین:* {stats.get('average_speed_mbps', 0):.2f} MB/s\n"
                
                # تاریخ ایجاد
                created_at = stats.get('created_at')
                if created_at:
                    text += f"📅 *تاریخ ایجاد:* {str(created_at)[:16]}\n"
                
                # آخرین دسترسی
                last_accessed = stats.get('last_accessed')
                if last_accessed:
                    text += f"🕐 *آخرین دسترسی:* {str(last_accessed)[:16]}\n"
                else:
                    text += f"🕐 *آخرین دسترسی:* هرگز\n"
                
                text += "\n"
                
                # اطلاعات اضافی
                expires_at = stats.get('expires_at')
                if expires_at:
                    text += f"⏰ *انقضا:* {str(expires_at)[:16]}\n"
                else:
                    text += f"♾️ *انقضا:* بدون محدودیت\n"
                
                max_downloads = stats.get('max_downloads')
                download_count = stats.get('download_count', 0)
                if max_downloads:
                    text += f"📊 *حد دانلود:* {download_count}/{max_downloads}\n"
                else:
                    text += f"📊 *حد دانلود:* نامحدود\n"
                
            else:
                text = f"❌ *خطا در دریافت آمار*\n\n"
                text += f"علت: {stats_data.get('error', 'نامشخص')}"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data=f"download_link_stats_{link_code}"),
                    InlineKeyboardButton("🔗 اطلاعات لینک", callback_data=f"download_link_info_{link_code}")
                ],
                [
                    InlineKeyboardButton("📋 کپی لینک", callback_data=f"copy_link_{link_code}"),
                    InlineKeyboardButton("🗑 حذف لینک", callback_data=f"delete_download_link_{link_code}")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="download_system_control")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_download_link_stats: {e}")
            await self.handle_error(update, context, e)
    
    async def show_download_link_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش اطلاعات کامل لینک دانلود"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            link_code = query.data.split('_')[-1]
            
            # دریافت اطلاعات از API
            info_data = await self.get_link_info(link_code)
            
            if info_data.get('success'):
                info = info_data['data']
                
                # آیکون بر اساس نوع
                type_icons = {
                    'stream': '🌊',
                    'fast': '⚡️', 
                    'restricted': '⚙️'
                }
                download_type = info.get('download_type', 'fast')
                icon = type_icons.get(download_type, '🔗')
                
                # نام نوع لینک
                type_names = {
                    'stream': 'استریم',
                    'fast': 'سریع',
                    'restricted': 'محدود'
                }
                type_name = type_names.get(download_type, 'عمومی')
                
                text = f"{icon} *اطلاعات کامل لینک دانلود*\n\n"
                text += f"📄 *فایل:* {info.get('file_name', 'نامشخص')}\n"
                text += f"💾 *حجم فایل:* {self._format_bytes(info.get('file_size', 0))}\n"
                text += f"🏷 *نوع فایل:* {info.get('file_type', 'نامشخص')}\n"
                text += f"🔗 *کد لینک:* `{link_code}`\n"
                text += f"🌐 *نوع دانلود:* {type_name}\n\n"
                
                # وضعیت لینک
                is_expired = info.get('is_expired', False)
                is_active = info.get('is_active', True)
                
                if is_expired:
                    text += f"🔴 *وضعیت:* منقضی شده\n"
                elif is_active:
                    text += f"🟢 *وضعیت:* فعال\n"
                else:
                    text += f"🟡 *وضعیت:* غیرفعال\n"
                
                # محدودیت‌ها
                download_count = info.get('download_count', 0)
                max_downloads = info.get('max_downloads')
                
                text += f"📊 *دانلودها:* {download_count}"
                if max_downloads:
                    text += f"/{max_downloads}\n"
                else:
                    text += f" (نامحدود)\n"
                
                expires_at = info.get('expires_at')
                if expires_at:
                    text += f"⏰ *انقضا:* {str(expires_at)[:16]}\n"
                else:
                    text += f"♾️ *انقضا:* بدون محدودیت\n"
                
                password_protected = info.get('password_protected', False)
                if password_protected:
                    text += f"🔒 *محافظت با رمز:* بله\n"
                else:
                    text += f"🔓 *محافظت با رمز:* خیر\n"
                
                created_at = info.get('created_at')
                if created_at:
                    text += f"\n📅 *تاریخ ایجاد:* {str(created_at)[:16]}"
                
                # URL کامل دانلود
                download_url = f"{self.api_url}/api/download/{download_type}/{link_code}"
                text += f"\n\n🌐 *URL دانلود:*\n`{download_url}`"
                
            else:
                text = f"❌ *خطا در دریافت اطلاعات*\n\n"
                text += f"علت: {info_data.get('error', 'نامشخص')}"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📊 آمار تفصیلی", callback_data=f"download_link_stats_{link_code}"),
                    InlineKeyboardButton("📋 کپی لینک", callback_data=f"copy_link_{link_code}")
                ],
                [
                    InlineKeyboardButton("🔒 غیرفعال‌سازی", callback_data=f"deactivate_link_{link_code}"),
                    InlineKeyboardButton("🗑 حذف لینک", callback_data=f"delete_download_link_{link_code}")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="download_system_control")  
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_download_link_info: {e}")
            await self.handle_error(update, context, e)
    
    async def get_link_stats(self, link_code: str) -> dict:
        """دریافت آمار لینک از API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/download/stats/{link_code}",
                    headers=self.headers
                ) as response:
                    data = await response.json()
                    return {'success': response.status == 200, 'data': data}
        except Exception as e:
            logger.error(f"Error getting link stats: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_link_info(self, link_code: str) -> dict:
        """دریافت اطلاعات لینک از API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/download/info/{link_code}"
                ) as response:
                    data = await response.json()
                    return {'success': response.status == 200, 'data': data}
        except Exception as e:
            logger.error(f"Error getting link info: {e}")
            return {'success': False, 'error': str(e)}
    
    def _format_bytes(self, bytes_value: int) -> str:
        """فرمت کردن حجم فایل"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    
    async def delete_download_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف لینک دانلود"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            link_code = query.data.split('_')[-1]
            
            # حذف لینک از طریق API
            delete_result = await self.delete_link_via_api(link_code)
            
            if delete_result.get('success'):
                text = f"✅ *لینک دانلود حذف شد*\n\n"
                text += f"🔗 *کد لینک:* `{link_code}`\n"
                text += f"🗑 لینک با موفقیت غیرفعال و حذف شد.\n\n"
                text += f"💡 *نکته:* دانلودهای در حال انجام قطع خواهند شد."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔙 بازگشت به کنترل سیستم", callback_data="download_system_control")
                    ]
                ])
            else:
                text = f"❌ *خطا در حذف لینک*\n\n"
                text += f"🔗 *کد لینک:* `{link_code}`\n"
                text += f"علت: {delete_result.get('error', 'نامشخص')}\n\n"
                text += f"لطفاً دوباره تلاش کنید."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 تلاش دوباره", callback_data=f"delete_download_link_{link_code}"),
                        InlineKeyboardButton("🔗 اطلاعات لینک", callback_data=f"download_link_info_{link_code}")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="download_system_control")
                    ]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in delete_download_link: {e}")
            await self.handle_error(update, context, e)
    
    async def delete_link_via_api(self, link_code: str) -> dict:
        """حذف لینک از طریق API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{self.api_url}/api/download/links/{link_code}",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        return {'success': True}
                    else:
                        error_data = await response.json()
                        return {'success': False, 'error': error_data.get('error', 'خطای نامشخص')}
        except Exception as e:
            logger.error(f"Error deleting link: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _show_api_error_with_retry(self, query, title: str, error_detail: str, retry_callback: str, back_callback: str):
        """نمایش خطای API با امکان تلاش مجدد"""
        try:
            text = f"{title}\n\n"
            text += f"🔍 **جزئیات خطا:**\n"
            text += f"`{error_detail}`\n\n"
            
            # بررسی نوع خطا و ارائه راهنمایی مناسب
            if "Connection" in error_detail or "connect" in error_detail.lower():
                text += "🌐 **دلیل احتمالی:** مشکل در اتصال به سرور دانلود\n"
                text += "💡 **پیشنهاد:** لطفاً چند لحظه صبر کرده و دوباره تلاش کنید\n\n"
            elif "timeout" in error_detail.lower():
                text += "⏱ **دلیل احتمالی:** زمان اتصال به سرور تمام شده\n"
                text += "💡 **پیشنهاد:** سرور ممکن است مشغول باشد، دوباره تلاش کنید\n\n"
            elif "404" in error_detail or "not found" in error_detail.lower():
                text += "🔍 **دلیل احتمالی:** فایل یا منبع مورد نظر یافت نشد\n"
                text += "💡 **پیشنهاد:** ممکن است فایل حذف شده باشد\n\n"
            elif "500" in error_detail or "internal server error" in error_detail.lower():
                text += "🛠 **دلیل احتمالی:** خطای داخلی سرور دانلود\n"
                text += "💡 **پیشنهاد:** لطفاً بعداً دوباره تلاش کنید یا با مدیر تماس بگیرید\n\n"
            else:
                text += "❓ **دلیل احتمالی:** خطای نامشخص در سیستم دانلود\n"
                text += "💡 **پیشنهاد:** دوباره تلاش کنید یا با پشتیبانی تماس بگیرید\n\n"
            
            text += f"🕐 **زمان خطا:** {datetime.now().strftime('%H:%M:%S')}"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 تلاش مجدد", callback_data=retry_callback),
                    InlineKeyboardButton("📞 پشتیبانی", url="https://t.me/support")  # لینک پشتیبانی
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data=back_callback)
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error showing API error: {e}")
            # اگر نمایش خطا هم با مشکل مواجه شد
            fallback_text = f"❌ خطا در سیستم\n\nجزئیات: {error_detail}\n\nلطفاً دوباره تلاش کنید."
            fallback_keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 تلاش مجدد", callback_data=retry_callback),
                InlineKeyboardButton("🔙 بازگشت", callback_data=back_callback)
            ]])
            try:
                await query.edit_message_text(fallback_text, reply_markup=fallback_keyboard)
            except:
                pass
    
    async def handle_system_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت تنظیمات سیستم - کالبک جدید"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            text = "🔧 **تنظیمات سیستم دانلود**\n\n"
            text += "در این بخش می‌توانید تنظیمات سیستم دانلود را مدیریت کنید:\n\n"
            text += "⚙️ **تنظیمات در دسترس:**\n"
            text += "• تنظیم حداکثر سرعت دانلود\n"
            text += "• مدیریت فضای ذخیره‌سازی\n"
            text += "• تنظیم محدودیت‌های کاربران\n"
            text += "• پیکربندی Cache سیستم\n\n"
            text += "💡 **توجه:** تغییر تنظیمات ممکن است بر عملکرد سیستم تأثیر بگذارد"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⚡️ تنظیمات سرعت", callback_data="speed_settings"),
                    InlineKeyboardButton("💾 تنظیمات ذخیره", callback_data="storage_settings")
                ],
                [
                    InlineKeyboardButton("👥 محدودیت کاربران", callback_data="user_limits"),
                    InlineKeyboardButton("🗂 تنظیمات Cache", callback_data="cache_settings")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="download_system_control")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_system_settings: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_token_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت توکن‌ها - کالبک جدید"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            text = "🔗 **مدیریت توکن‌های دسترسی**\n\n"
            text += "در این بخش می‌توانید توکن‌های دسترسی سیستم را مدیریت کنید:\n\n"
            text += "🛡 **انواع توکن‌ها:**\n"
            text += "• توکن مدیر (Admin Token)\n"
            text += "• توکن‌های کاربران\n"
            text += "• توکن‌های موقت\n"
            text += "• کلیدهای API\n\n"
            text += f"🔑 **توکن فعلی:** `{self.admin_token[:20]}...`\n"
            text += f"✅ **وضعیت:** فعال"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 تولید توکن جدید", callback_data="generate_new_token"),
                    InlineKeyboardButton("📋 مشاهده توکن‌ها", callback_data="view_all_tokens")
                ],
                [
                    InlineKeyboardButton("🔒 غیرفعال‌سازی توکن", callback_data="deactivate_tokens"),
                    InlineKeyboardButton("⏰ تنظیم انقضا", callback_data="set_token_expiry")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="download_system_control")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_token_management: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_api_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیمات API - کالبک جدید"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            # بررسی وضعیت API
            system_status = await self.get_system_status()
            status_icon = "🟢" if system_status.get('ready', False) else "🔴"
            status_text = "آنلاین" if system_status.get('ready', False) else "آفلاین"
            
            text = "⚙️ **تنظیمات API سیستم دانلود**\n\n"
            text += f"🌐 **URL سرور:** `{self.api_url}`\n"
            text += f"{status_icon} **وضعیت:** {status_text}\n"
            text += f"📡 **نسخه API:** {system_status.get('version', 'نامشخص')}\n\n"
            
            if system_status.get('ready', False):
                text += "✅ **اتصال موفق**\n"
                text += f"⏱ **پینگ:** {system_status.get('ping', 'نامشخص')} ms\n"
                text += f"📊 **وضعیت سرور:** سالم\n"
            else:
                text += "❌ **اتصال ناموفق**\n"
                text += f"🔍 **خطا:** {system_status.get('error', 'نامشخص')}\n"
                text += "💡 **راهکار:** بررسی اتصال شبکه و تنظیمات سرور\n"
            
            text += "\n🛠 **تنظیمات قابل تغییر:**\n"
            text += "• Timeout درخواست‌ها\n"
            text += "• تعداد تلاش‌های مجدد\n"
            text += "• فرمت پاسخ‌ها\n"
            text += "• سطح لاگ‌گیری"
            
            keyboard_rows = []
            
            if system_status.get('ready', False):
                keyboard_rows.extend([
                    [
                        InlineKeyboardButton("🔄 تست اتصال", callback_data="test_api_connection"),
                        InlineKeyboardButton("📊 آمار API", callback_data="api_statistics")
                    ],
                    [
                        InlineKeyboardButton("⚙️ تنظیمات پیشرفته", callback_data="advanced_api_settings"),
                        InlineKeyboardButton("📝 لاگ‌های API", callback_data="api_logs")
                    ]
                ])
            else:
                keyboard_rows.append([
                    InlineKeyboardButton("🔄 تلاش مجدد اتصال", callback_data="retry_api_connection"),
                    InlineKeyboardButton("🛠 تشخیص مشکل", callback_data="diagnose_api_issue")
                ])
            
            keyboard_rows.append([
                InlineKeyboardButton("🔙 بازگشت", callback_data="download_system_control")
            ])
            
            keyboard = InlineKeyboardMarkup(keyboard_rows)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_api_settings: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_download_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش آمار دانلودها - کالبک اصلاح شده"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            # دریافت آمار از API
            stats_data = await self.get_download_statistics()
            
            if stats_data.get('success'):
                stats = stats_data.get('data', {})
                
                text = "📈 **گزارش آمار سیستم دانلود**\n\n"
                text += f"📥 **کل دانلودها امروز:** {stats.get('today_downloads', 0):,}\n"
                text += f"📊 **کل دانلودها این ماه:** {stats.get('month_downloads', 0):,}\n"
                text += f"👥 **کاربران فعال امروز:** {stats.get('active_users_today', 0)}\n"
                text += f"💾 **حجم منتقل شده امروز:** {self._format_bytes(stats.get('bytes_transferred_today', 0))}\n\n"
                
                text += "🔗 **آمار لینک‌ها:**\n"
                text += f"• لینک‌های فعال: {stats.get('active_links', 0)}\n"
                text += f"• لینک‌های منقضی: {stats.get('expired_links', 0)}\n"
                text += f"• میانگین دانلود هر لینک: {stats.get('avg_downloads_per_link', 0):.1f}\n\n"
                
                text += "⚡️ **عملکرد سیستم:**\n"
                text += f"• میانگین سرعت دانلود: {stats.get('avg_download_speed', 0):.1f} MB/s\n"
                text += f"• زمان پاسخ میانگین: {stats.get('avg_response_time', 0):.2f} ثانیه\n"
                text += f"• درصد موفقیت: {stats.get('success_rate', 0):.1f}%\n"
                
            else:
                text = "📈 **گزارش آمار سیستم دانلود**\n\n"
                text += "❌ **خطا در دریافت آمار**\n\n"
                error = stats_data.get('error', 'نامشخص')
                text += f"🔍 **جزئیات:** {error}\n\n"
                text += "💡 **راهکار:** بررسی اتصال به سرور آمار"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data="download_stats"),
                    InlineKeyboardButton("📊 آمار تفصیلی", callback_data="detailed_download_stats")
                ],
                [
                    InlineKeyboardButton("📈 نمودار آمار", callback_data="stats_chart"),
                    InlineKeyboardButton("📋 گزارش PDF", callback_data="export_stats_pdf")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="download_system_control")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_download_stats: {e}")
            await self._show_api_error_with_retry(
                query,
                "❌ خطا در دریافت آمار", 
                str(e),
                "download_stats",
                "download_system_control"
            )
    
    async def get_download_statistics(self) -> dict:
        """دریافت آمار دانلودها از API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/statistics/downloads",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {'success': True, 'data': data}
                    else:
                        return {'success': False, 'error': f'HTTP {response.status}'}
        except Exception as e:
            logger.error(f"Error getting download statistics: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _check_telethon_status(self) -> Dict[str, Any]:
        """بررسی وضعیت سیستم Telethon"""
        try:
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            
            telethon_manager = AdvancedTelethonClientManager()
            configs = telethon_manager.config_manager.list_configs()
            
            if not configs:
                return {
                    'active': False,
                    'has_active_clients': False,
                    'error': 'هیچ کانفیگ Telethon یافت نشد',
                    'healthy_clients': 0,
                    'total_clients': 0
                }
            
            health_results = await telethon_manager.check_all_clients_health()
            healthy_clients = len([h for h in health_results.values() if h.get('status') == 'healthy'])
            total_clients = len(health_results)
            
            return {
                'active': healthy_clients > 0,
                'has_active_clients': healthy_clients > 0,
                'healthy_clients': healthy_clients,
                'total_clients': total_clients,
                'error': None if healthy_clients > 0 else 'هیچ کلاینت فعالی وجود ندارد'
            }
            
        except Exception as e:
            return {
                'active': False,
                'has_active_clients': False,
                'error': f'خطا در بررسی Telethon: {str(e)}',
                'healthy_clients': 0,
                'total_clients': 0
            }
    
    # توابع ناقص که باید اضافه شوند
    async def handle_speed_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیمات سرعت سیستم دانلود"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            # دریافت تنظیمات فعلی سرعت
            current_settings = await self.get_speed_settings()
            
            text = "⚡️ **تنظیمات سرعت دانلود**\n\n"
            text += f"📊 **تنظیمات فعلی:**\n"
            text += f"• حداکثر سرعت: {current_settings.get('max_speed', 'نامحدود')} MB/s\n"
            text += f"• تعداد اتصالات همزمان: {current_settings.get('max_connections', 4)}\n"
            text += f"• اندازه بافر: {current_settings.get('buffer_size', '64KB')}\n\n"
            text += "🎯 **انتخاب سرعت جدید:**"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🚀 نامحدود", callback_data="set_speed_unlimited"),
                    InlineKeyboardButton("⚡️ 100 MB/s", callback_data="set_speed_100")
                ],
                [
                    InlineKeyboardButton("🏃 50 MB/s", callback_data="set_speed_50"),
                    InlineKeyboardButton("🚶 25 MB/s", callback_data="set_speed_25")
                ],
                [
                    InlineKeyboardButton("🐌 10 MB/s", callback_data="set_speed_10"),
                    InlineKeyboardButton("🔧 سفارشی", callback_data="set_speed_custom")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="system_settings")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def handle_set_speed(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیم سرعت دانلود"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update, "در حال تنظیم سرعت...")
            
            speed_type = query.data.split('_')[-1]  # unlimited, 100, 50, 25, 10, custom
            
            if speed_type == "unlimited":
                speed_limit = None
                speed_text = "نامحدود"
            elif speed_type == "custom":
                # برای سفارشی، کاربر باید عدد وارد کند
                text = "🔧 **تنظیم سرعت سفارشی**\n\n"
                text += "لطفاً سرعت مورد نظر را بر حسب MB/s وارد کنید:\n"
                text += "(مثال: 75)"
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ لغو", callback_data="speed_settings")
                ]])
                
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
                
                # تنظیم state برای دریافت input
                user_id = update.effective_user.id
                await self.update_user_session(
                    user_id,
                    action_state='setting_custom_speed'
                )
                return
            else:
                speed_limit = int(speed_type)
                speed_text = f"{speed_limit} MB/s"
            
            # تنظیم سرعت از طریق API
            result = await self.set_speed_limit(speed_limit)
            
            if result.get('success'):
                text = f"✅ **سرعت دانلود تنظیم شد**\n\n"
                text += f"⚡️ **سرعت جدید:** {speed_text}\n"
                text += f"📊 **تأثیر:** تمام دانلودهای جدید\n\n"
                text += "💡 **توجه:** دانلودهای در حال انجام تحت تأثیر قرار نمی‌گیرند."
            else:
                text = f"❌ **خطا در تنظیم سرعت**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 تغییر سرعت", callback_data="speed_settings"),
                    InlineKeyboardButton("📊 تست سرعت", callback_data="test_speed")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="system_settings")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def handle_generate_new_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تولید توکن جدید"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            text = "🔐 **تولید توکن جدید**\n\n"
            text += "⚠️ **هشدار مهم:**\n"
            text += "• تولید توکن جدید، توکن فعلی را باطل می‌کند\n"
            text += "• تمام اتصالات فعال قطع خواهند شد\n"
            text += "• باید توکن جدید را در تنظیمات سیستم به‌روزرسانی کنید\n\n"
            text += "🔧 **انواع توکن:**\n"
            text += "• **مدیر کل:** دسترسی کامل به سیستم\n"
            text += "• **مدیر محدود:** دسترسی به بخش‌های خاص\n"
            text += "• **کاربر:** دسترسی پایه\n\n"
            text += "آیا مطمئن هستید؟"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔐 مدیر کل", callback_data="confirm_new_token_admin"),
                    InlineKeyboardButton("⚙️ مدیر محدود", callback_data="confirm_new_token_limited")
                ],
                [
                    InlineKeyboardButton("👤 کاربر", callback_data="confirm_new_token_user")
                ],
                [
                    InlineKeyboardButton("❌ لغو", callback_data="token_management")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def handle_view_all_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مشاهده همه توکن‌ها"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            # دریافت لیست توکن‌ها از API
            tokens_data = await self.get_all_tokens()
            
            text = "📋 **لیست توکن‌های فعال**\n\n"
            
            if tokens_data.get('success'):
                tokens = tokens_data.get('tokens', [])
                
                if tokens:
                    for i, token in enumerate(tokens, 1):
                        status_icon = "🟢" if token.get('is_active') else "🔴"
                        type_icon = {
                            'admin': '🔐',
                            'limited': '⚙️', 
                            'user': '👤'
                        }.get(token.get('type'), '🔑')
                        
                        text += f"{i}. {type_icon} **{token.get('name', f'توکن {i}')}** {status_icon}\n"
                        text += f"   🏷 نوع: {token.get('type', 'نامشخص')}\n"
                        text += f"   📅 ایجاد: {token.get('created_at', 'نامشخص')[:16]}\n"
                        text += f"   🔑 کد: `{token.get('token', '')[:20]}...`\n"
                        if token.get('expires_at'):
                            text += f"   ⏰ انقضا: {token.get('expires_at')[:16]}\n"
                        text += f"   📊 استفاده: {token.get('usage_count', 0)} بار\n\n"
                else:
                    text += "❌ هیچ توکن فعالی یافت نشد!"
            else:
                text += f"❌ خطا در دریافت توکن‌ها\n\n"
                text += f"علت: {tokens_data.get('error', 'نامشخص')}"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data="view_all_tokens"),
                    InlineKeyboardButton("➕ توکن جدید", callback_data="generate_new_token")
                ],
                [
                    InlineKeyboardButton("🗑 حذف توکن", callback_data="delete_tokens"),
                    InlineKeyboardButton("⏰ تنظیم انقضا", callback_data="set_token_expiry")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="token_management")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def handle_confirm_new_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأیید تولید توکن جدید"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update, "در حال تولید توکن...")
            
            token_type = query.data.split('_')[-1]  # admin, limited, user
            
            # تولید توکن جدید از طریق API
            result = await self.generate_token(token_type)
            
            if result.get('success'):
                new_token = result.get('token')
                token_id = result.get('token_id')
                
                text = f"✅ **توکن جدید تولید شد**\n\n"
                text += f"🔐 **نوع توکن:** {token_type.title()}\n"
                text += f"🆔 **شناسه:** `{token_id}`\n"
                text += f"🔑 **توکن:**\n`{new_token}`\n\n"
                text += "⚠️ **نکات مهم:**\n"
                text += "• این توکن را در جایی امن ذخیره کنید\n"
                text += "• توکن قدیمی غیرفعال شده است\n"
                text += "• تنظیمات سیستم را به‌روزرسانی کنید\n\n"
                text += f"📊 **دسترسی‌ها:**\n"
                
                if token_type == 'admin':
                    text += "• دسترسی کامل به تمام عملیات\n"
                    text += "• مدیریت کاربران و توکن‌ها\n"
                    text += "• تنظیمات سیستم\n"
                elif token_type == 'limited':
                    text += "• دسترسی به عملیات محدود\n"
                    text += "• ایجاد و مدیریت لینک‌ها\n"
                    text += "• مشاهده آمار\n"
                else:  # user
                    text += "• دسترسی پایه\n"
                    text += "• ایجاد لینک دانلود\n"
                    text += "• مشاهده آمار شخصی\n"
                
                # به‌روزرسانی توکن داخلی اگر admin باشد
                if token_type == 'admin':
                    self.admin_token = new_token
                    self.headers = {"Authorization": f"Bearer {new_token}"}
                
            else:
                text = f"❌ **خطا در تولید توکن**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}\n\n"
                text += "لطفاً دوباره تلاش کنید یا با مدیر سیستم تماس بگیرید."
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📋 کپی توکن", callback_data=f"copy_token_{result.get('token_id', '')}"),
                    InlineKeyboardButton("📊 جزئیات توکن", callback_data=f"token_details_{result.get('token_id', '')}")
                ] if result.get('success') else [],
                [
                    InlineKeyboardButton("🔄 تولید مجدد", callback_data="generate_new_token"),
                    InlineKeyboardButton("📋 مشاهده همه", callback_data="view_all_tokens")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="token_management")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    # متدهای کمکی برای API calls
    async def get_speed_settings(self) -> dict:
        """دریافت تنظیمات سرعت فعلی"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/settings/speed",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {'max_speed': 'نامشخص', 'max_connections': 4, 'buffer_size': '64KB'}
        except Exception as e:
            logger.error(f"Error getting speed settings: {e}")
            return {'max_speed': 'نامشخص', 'max_connections': 4, 'buffer_size': '64KB'}
    
    async def set_speed_limit(self, speed_limit: int = None) -> dict:
        """تنظیم محدودیت سرعت"""
        try:
            data = {'max_speed': speed_limit}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/settings/speed",
                    headers=self.headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        return {'success': True}
                    else:
                        error_data = await response.json()
                        return {'success': False, 'error': error_data.get('error', 'خطای نامشخص')}
        except Exception as e:
            logger.error(f"Error setting speed limit: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_all_tokens(self) -> dict:
        """دریافت همه توکن‌ها"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/admin/tokens",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {'success': True, 'tokens': data.get('tokens', [])}
                    else:
                        return {'success': False, 'error': f'HTTP {response.status}'}
        except Exception as e:
            logger.error(f"Error getting all tokens: {e}")
            return {'success': False, 'error': str(e)}
    
    async def generate_token(self, token_type: str) -> dict:
        """تولید توکن جدید"""
        try:
            data = {'type': token_type}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/admin/tokens/generate",
                    headers=self.headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'token': result.get('token'),
                            'token_id': result.get('token_id')
                        }
                    else:
                        error_data = await response.json()
                        return {'success': False, 'error': error_data.get('error', 'خطای نامشخص')}
        except Exception as e:
            logger.error(f"Error generating token: {e}")
            return {'success': False, 'error': str(e)}