#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token Management Handler - مدیریت کامل سیستم توکن‌های دسترسی
"""

import aiohttp
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta

from handlers.base_handler import BaseHandler

logger = logging.getLogger(__name__)


class TokenManagementHandler(BaseHandler):
    """مدیریت پیشرفته توکن‌های دسترسی"""
    
    def __init__(self, db, download_api_url: str, admin_token: str):
        super().__init__(db)
        self.api_url = download_api_url
        self.admin_token = admin_token
        self.headers = {"Authorization": f"Bearer {admin_token}"}
    
    async def show_token_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش داشبورد مدیریت توکن‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت آمار توکن‌ها
            stats = await self.get_token_statistics()
            
            text = "🔗 **داشبورد مدیریت توکن‌ها**\n\n"
            
            if stats.get('success'):
                data = stats.get('data', {})
                text += f"📊 **آمار کلی:**\n"
                text += f"• توکن‌های فعال: {data.get('active_tokens', 0)}\n"
                text += f"• توکن‌های منقضی: {data.get('expired_tokens', 0)}\n"
                text += f"• کل توکن‌ها: {data.get('total_tokens', 0)}\n"
                text += f"• استفاده امروز: {data.get('daily_usage', 0)} درخواست\n\n"
                
                text += f"🔑 **انواع توکن‌ها:**\n"
                text += f"• مدیر: {data.get('admin_tokens', 0)}\n"
                text += f"• محدود: {data.get('limited_tokens', 0)}\n"
                text += f"• کاربر: {data.get('user_tokens', 0)}\n\n"
            else:
                text += "❌ خطا در دریافت آمار توکن‌ها\n\n"
            
            text += f"🕐 **آخرین بروزرسانی:** {datetime.now().strftime('%H:%M:%S')}"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📋 مشاهده توکن‌ها", callback_data="list_all_tokens"),
                    InlineKeyboardButton("➕ تولید توکن", callback_data="create_new_token")
                ],
                [
                    InlineKeyboardButton("🔒 مدیریت دسترسی", callback_data="token_manage_permissions"),
                    InlineKeyboardButton("📊 گزارش استفاده", callback_data="token_usage_report")
                ],
                [
                    InlineKeyboardButton("⚙️ تنظیمات امنیتی", callback_data="token_security_settings"),
                    InlineKeyboardButton("🧹 پاکسازی", callback_data="cleanup_tokens")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="download_system_control")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_token_dashboard: {e}")
            await self.handle_error(update, context, e)
    
    async def show_create_token_wizard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """راهنمای تولید توکن جدید"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔐 **راهنمای تولید توکن جدید**\n\n"
            text += "لطفاً نوع توکن مورد نظر خود را انتخاب کنید:\n\n"
            
            text += "🛡 **توکن مدیر (Admin):**\n"
            text += "• دسترسی کامل به تمام عملیات\n"
            text += "• مدیریت کاربران و توکن‌ها\n"
            text += "• تنظیمات سیستم\n"
            text += "• گزارش‌گیری پیشرفته\n\n"
            
            text += "⚙️ **توکن محدود (Limited):**\n"
            text += "• دسترسی به عملیات محدود\n"
            text += "• ایجاد و مدیریت لینک‌ها\n"
            text += "• مشاهده آمار شخصی\n"
            text += "• دانلود فایل‌ها\n\n"
            
            text += "👤 **توکن کاربر (User):**\n"
            text += "• دسترسی پایه\n"
            text += "• ایجاد لینک دانلود\n"
            text += "• مشاهده آمار محدود\n"
            text += "• استفاده روزانه محدود\n\n"
            
            text += "⚠️ **نکته:** انتخاب نوع توکن بر اساس نیاز کاربر صورت گیرد."
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🛡 مدیر", callback_data="create_token_admin"),
                    InlineKeyboardButton("⚙️ محدود", callback_data="create_token_limited")
                ],
                [
                    InlineKeyboardButton("👤 کاربر", callback_data="create_token_user")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_create_token_wizard: {e}")
            await self.handle_error(update, context, e)
    
    async def process_token_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش درخواست تولید توکن"""
        try:
            query = update.callback_query
            await query.answer("در حال تولید توکن...")
            
            token_type = query.data.split('_')[2]  # admin, limited, user
            
            # تولید توکن از طریق API
            result = await self.create_api_token(token_type)
            
            if result.get('success'):
                token_data = result.get('data', {})
                
                text = f"✅ **توکن جدید تولید شد**\n\n"
                text += f"🔐 **نوع:** {self._get_token_type_name(token_type)}\n"
                text += f"🆔 **شناسه:** `{token_data.get('token_id', 'N/A')}`\n"
                text += f"📝 **نام:** {token_data.get('name', 'بدون نام')}\n"
                text += f"📅 **تاریخ ایجاد:** {token_data.get('created_at', 'نامشخص')[:16]}\n"
                
                if token_data.get('expires_at'):
                    text += f"⏰ **انقضا:** {token_data.get('expires_at')[:16]}\n"
                else:
                    text += f"♾ **انقضا:** بدون محدودیت\n"
                
                text += f"\n🔑 **توکن:**\n`{token_data.get('token', '')}`\n\n"
                
                text += "⚠️ **نکات مهم:**\n"
                text += "• این توکن را در جایی امن ذخیره کنید\n"
                text += "• مراقب عدم انتشار عمومی آن باشید\n"
                text += "• در صورت فراموشی قابل بازیابی نیست\n"
                text += "• می‌توانید هر زمان آن را غیرفعال کنید\n\n"
                
                text += f"📊 **دسترسی‌های این توکن:**\n"
                permissions = self._get_token_permissions(token_type)
                for perm in permissions:
                    text += f"• {perm}\n"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📋 کپی توکن", callback_data=f"copy_token_{token_data.get('token_id', '')}"),
                        InlineKeyboardButton("📊 جزئیات", callback_data=f"token_details_{token_data.get('token_id', '')}")
                    ],
                    [
                        InlineKeyboardButton("🔄 تولید مجدد", callback_data="create_new_token"),
                        InlineKeyboardButton("📋 لیست توکن‌ها", callback_data="list_all_tokens")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                    ]
                ])
                
            else:
                text = f"❌ **خطا در تولید توکن**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}\n\n"
                text += "لطفاً دوباره تلاش کنید یا با مدیر سیستم تماس بگیرید."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 تلاش مجدد", callback_data=f"create_token_{token_type}"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data="create_new_token")
                    ]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in process_token_creation: {e}")
            await self.handle_error(update, context, e)
    
    async def show_token_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش لیست توکن‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت لیست توکن‌ها
            tokens_result = await self.get_all_tokens()
            
            text = "📋 **لیست توکن‌های سیستم**\n\n"
            
            if tokens_result.get('success'):
                tokens = tokens_result.get('tokens', [])
                
                if tokens:
                    for i, token in enumerate(tokens, 1):
                        status_icon = "🟢" if token.get('is_active', True) else "🔴"
                        type_icon = self._get_token_type_icon(token.get('type', 'user'))
                        
                        text += f"{i}. {type_icon} **{token.get('name', f'توکن {i}')}** {status_icon}\n"
                        text += f"   🏷 نوع: {self._get_token_type_name(token.get('type', 'user'))}\n"
                        text += f"   🆔 شناسه: `{token.get('token_id', token.get('id', 'N/A'))}`\n"
                        text += f"   📅 ایجاد: {token.get('created_at', 'نامشخص')[:16]}\n"
                        
                        if token.get('expires_at'):
                            text += f"   ⏰ انقضا: {token.get('expires_at')[:16]}\n"
                        else:
                            text += f"   ♾ انقضا: بدون محدودیت\n"
                        
                        text += f"   📊 استفاده: {token.get('usage_count', 0)} بار\n"
                        
                        if token.get('last_used_at'):
                            text += f"   🕐 آخرین استفاده: {token.get('last_used_at')[:16]}\n"
                        
                        text += "\n"
                        
                        # محدود کردن تعداد نمایش
                        if i >= 10:
                            text += f"... و {len(tokens) - 10} توکن دیگر\n"
                            break
                else:
                    text += "❌ هیچ توکن فعالی یافت نشد!\n\n"
                    text += "💡 برای شروع، یک توکن جدید ایجاد کنید."
            else:
                text += f"❌ خطا در دریافت لیست توکن‌ها\n\n"
                text += f"علت: {tokens_result.get('error', 'نامشخص')}"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data="list_all_tokens"),
                    InlineKeyboardButton("➕ توکن جدید", callback_data="create_new_token")
                ],
                [
                    InlineKeyboardButton("🔍 جستجو", callback_data="search_tokens"),
                    InlineKeyboardButton("🗑 حذف دسته‌ای", callback_data="bulk_delete_tokens")
                ],
                [
                    InlineKeyboardButton("📊 آمار کامل", callback_data="detailed_token_stats"),
                    InlineKeyboardButton("💾 صادرات", callback_data="export_tokens")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_token_list: {e}")
            await self.handle_error(update, context, e)
    
    # Helper Methods
    
    def _get_token_type_name(self, token_type: str) -> str:
        """دریافت نام فارسی نوع توکن"""
        type_names = {
            'admin': 'مدیر کل',
            'limited': 'مدیر محدود', 
            'user': 'کاربر',
            'api': 'API',
            'service': 'سرویس'
        }
        return type_names.get(token_type, 'نامشخص')
    
    def _get_token_type_icon(self, token_type: str) -> str:
        """دریافت آیکون نوع توکن"""
        type_icons = {
            'admin': '🛡',
            'limited': '⚙️',
            'user': '👤',
            'api': '🔑',
            'service': '🔧'
        }
        return type_icons.get(token_type, '🔑')
    
    def _get_token_permissions(self, token_type: str) -> List[str]:
        """دریافت لیست دسترسی‌های توکن"""
        permissions = {
            'admin': [
                'دسترسی کامل به تمام عملیات',
                'مدیریت کاربران و توکن‌ها',
                'تنظیمات سیستم',
                'گزارش‌گیری پیشرفته',
                'نظارت بر سیستم',
                'پاکسازی و نگهداری'
            ],
            'limited': [
                'ایجاد و مدیریت لینک‌های دانلود',
                'مشاهده آمار شخصی',
                'دانلود فایل‌ها',
                'مدیریت محدود کاربران'
            ],
            'user': [
                'ایجاد لینک دانلود',
                'مشاهده آمار محدود',
                'دانلود فایل‌های شخصی'
            ]
        }
        return permissions.get(token_type, ['دسترسی پایه'])
    
    # API Methods
    
    async def get_token_statistics(self) -> Dict[str, Any]:
        """دریافت آمار توکن‌ها"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/admin/tokens/stats",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {'success': True, 'data': data}
                    else:
                        return {'success': False, 'error': f'HTTP {response.status}'}
        except Exception as e:
            logger.error(f"Error getting token statistics: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_all_tokens(self) -> Dict[str, Any]:
        """دریافت همه توکن‌ها"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/admin/tokens",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list):
                            return {'success': True, 'tokens': data}
                        else:
                            return {'success': True, 'tokens': data.get('tokens', [])}
                    else:
                        return {'success': False, 'error': f'HTTP {response.status}'}
        except Exception as e:
            logger.error(f"Error getting all tokens: {e}")
            return {'success': False, 'error': str(e)}
    
    async def create_api_token(self, token_type: str, name: str = None, expires_in_days: int = None) -> Dict[str, Any]:
        """تولید توکن جدید"""
        try:
            data = {
                'type': token_type,
                'name': name or f'توکن {token_type} - {datetime.now().strftime("%Y%m%d_%H%M")}'
            }
            
            if expires_in_days:
                data['expires_at'] = (datetime.now() + timedelta(days=expires_in_days)).isoformat()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/auth/token/create",
                    headers=self.headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'data': result
                        }
                    else:
                        error_data = await response.json()
                        return {'success': False, 'error': error_data.get('error', 'خطای نامشخص')}
        except Exception as e:
            logger.error(f"Error creating API token: {e}")
            return {'success': False, 'error': str(e)}
    
    async def show_permissions_manager(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش مدیریت دسترسی‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔒 **مدیریت دسترسی‌ها**\n\n"
            text += "این بخش در حال توسعه است...\n\n"
            text += "قابلیت‌های آینده:\n"
            text += "• تنظیم دسترسی‌های سفارشی\n"
            text += "• گروه‌بندی دسترسی‌ها\n"
            text += "• کنترل دسترسی بر اساس IP\n"
            text += "• محدودیت زمانی دسترسی"
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
            ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_permissions_manager: {e}")
            await self.handle_error(update, context, e)
    
    async def show_usage_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش گزارش استفاده از توکن‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت آمار استفاده
            stats = await self.get_token_statistics()
            
            text = "📊 **گزارش استفاده از توکن‌ها**\n\n"
            
            if stats.get('success'):
                data = stats.get('data', {})
                text += f"📈 **آمار امروز:**\n"
                text += f"• درخواست‌های کل: {data.get('daily_usage', 0)}\n"
                text += f"• توکن‌های فعال: {data.get('active_tokens', 0)}\n"
                text += f"• میانگین استفاده هر توکن: {data.get('daily_usage', 0) / max(data.get('active_tokens', 1), 1):.1f}\n\n"
                
                text += f"📊 **آمار کلی:**\n"
                text += f"• کل استفاده‌ها: {data.get('total_usage', 0):,}\n"
                text += f"• کل توکن‌ها: {data.get('total_tokens', 0)}\n"
                text += f"• توکن‌های منقضی: {data.get('expired_tokens', 0)}\n"
            else:
                text += "❌ خطا در دریافت آمار استفاده"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data="token_usage_report"),
                    InlineKeyboardButton("📈 نمودار", callback_data="usage_chart")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_usage_report: {e}")
            await self.handle_error(update, context, e)
    
    async def show_security_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش تنظیمات امنیتی"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🛡 **تنظیمات امنیتی توکن‌ها**\n\n"
            text += "🔒 **تنظیمات فعلی:**\n"
            text += "• انقضای پیش‌فرض: بدون محدودیت\n"
            text += "• حداکثر استفاده: نامحدود\n"
            text += "• محدودیت IP: غیرفعال\n"
            text += "• لاگ‌گیری: فعال\n\n"
            
            text += "⚙️ **تنظیمات قابل تغییر:**\n"
            text += "• مدت زمان انقضای پیش‌فرض\n"
            text += "• حداکثر تعداد استفاده\n"
            text += "• محدودیت‌های IP\n"
            text += "• سطح لاگ‌گیری\n"
            text += "• هشدارهای امنیتی"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⏰ تنظیم انقضا", callback_data="set_default_expiry"),
                    InlineKeyboardButton("🔢 حد استفاده", callback_data="set_usage_limit")
                ],
                [
                    InlineKeyboardButton("🌐 محدودیت IP", callback_data="ip_restrictions"),
                    InlineKeyboardButton("🔔 هشدارها", callback_data="security_alerts")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_security_settings: {e}")
            await self.handle_error(update, context, e)
    
    async def show_cleanup_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش گزینه‌های پاکسازی"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🧹 **پاکسازی توکن‌ها**\n\n"
            text += "⚠️ **هشدار:** عملیات‌های پاکسازی برگشت‌پذیر نیستند!\n\n"
            text += "🎯 **گزینه‌های پاکسازی:**\n\n"
            text += "• **توکن‌های منقضی:** حذف توکن‌هایی که تاریخ انقضایشان گذشته\n"
            text += "• **توکن‌های غیرفعال:** حذف توکن‌های غیرفعال شده\n"
            text += "• **توکن‌های بدون استفاده:** حذف توکن‌هایی که مدت طولانی استفاده نشده‌اند\n"
            text += "• **پاکسازی کامل:** حذف همه توکن‌ها به جز مدیر فعلی"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⏰ توکن‌های منقضی", callback_data="cleanup_expired"),
                    InlineKeyboardButton("🔴 توکن‌های غیرفعال", callback_data="cleanup_inactive")
                ],
                [
                    InlineKeyboardButton("💤 بدون استفاده", callback_data="cleanup_unused"),
                    InlineKeyboardButton("🗑 پاکسازی کامل", callback_data="cleanup_all")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_cleanup_options: {e}")
            await self.handle_error(update, context, e)