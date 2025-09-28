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
                text += f"🆔 **شناسه:** {token_data.get('token_id', 'N/A')}\n"
                text += f"📝 **نام:** {token_data.get('name', 'بدون نام')}\n"
                text += f"📅 **تاریخ ایجاد:** {token_data.get('created_at', 'نامشخص')[:16]}\n"
                
                if token_data.get('expires_at'):
                    text += f"⏰ **انقضا:** {token_data.get('expires_at')[:16]}\n"
                else:
                    text += f"♾ **انقضا:** بدون محدودیت\n"
                
                text += f"\n🔑 **توکن:**\n{token_data.get('token', '')}\n\n"
                
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
                        text += f"   🆔 شناسه: {token.get('token_id', token.get('id', 'N/A'))}\n"
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
    
    # متدهای جدید برای تکمیل توکن منیجر
    
    async def handle_deactivate_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش گزینه‌های غیرفعال‌سازی توکن‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔒 **غیرفعال‌سازی توکن‌ها**\n\n"
            text += "لطفاً نوع غیرفعال‌سازی را انتخاب کنید:\n\n"
            
            text += "• **غیرفعال‌سازی تک:** غیرفعال کردن یک توکن خاص\n"
            text += "• **غیرفعال‌سازی دسته‌ای:** غیرفعال کردن چندین توکن به صورت همزمان\n"
            text += "• **غیرفعال‌سازی منقضی‌ها:** غیرفعال کردن همه توکن‌های منقضی شده\n"
            text += "• **غیرفعال‌سازی مشکوک:** غیرفعال کردن توکن‌های با فعالیت مشکوک"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔒 غیرفعال‌سازی تک", callback_data="deactivate_single_token"),
                    InlineKeyboardButton("📦 غیرفعال‌سازی دسته‌ای", callback_data="deactivate_bulk_tokens")
                ],
                [
                    InlineKeyboardButton("⏰ غیرفعال‌سازی منقضی‌ها", callback_data="deactivate_expired_tokens"),
                    InlineKeyboardButton("⚠️ غیرفعال‌سازی مشکوک", callback_data="deactivate_suspicious_tokens")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_deactivate_tokens: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_set_token_expiry(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش گزینه‌های تنظیم انقضای توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "⏰ **تنظیم انقضای توکن**\n\n"
            text += "لطفاً نوع تنظیم انقضا را انتخاب کنید:\n\n"
            
            text += "• **انقضای پیش‌فرض:** تنظیم زمان انقضای پیش‌فرض برای توکن‌های جدید\n"
            text += "• **انقضای دسته‌ای:** تنظیم انقضا برای چندین توکن به صورت همزمان\n"
            text += "• **انقضای سفارشی:** تنظیم انقضای سفارشی برای یک توکن خاص"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⏰ انقضای پیش‌فرض", callback_data="set_default_expiry"),
                    InlineKeyboardButton("📦 انقضای دسته‌ای", callback_data="set_bulk_expiry")
                ],
                [
                    InlineKeyboardButton("🎯 انقضای سفارشی", callback_data="set_custom_expiry")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_set_token_expiry: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_deactivate_current_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """غیرفعال‌سازی توکن فعلی"""
        try:
            query = update.callback_query
            await query.answer("در حال غیرفعال‌سازی توکن...")
            
            # دریافت توکن فعلی از session
            user_id = update.effective_user.id
            session = await self.db.get_user_session(user_id)
            
            if not session or not session.get('current_token_id'):
                await query.edit_message_text(
                    "❌ **خطا:** هیچ توکن فعلی یافت نشد.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                    ]])
                )
                return
            
            token_id = session.get('current_token_id')
            
            # غیرفعال‌سازی توکن از طریق API
            result = await self.deactivate_token(token_id)
            
            if result.get('success'):
                text = f"✅ **توکن غیرفعال شد**\n\n"
                text += f"🆔 **شناسه توکن:** `{token_id}`\n"
                text += f"📅 **زمان غیرفعال‌سازی:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                text += "⚠️ این توکن دیگر قابل استفاده نیست."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📋 لیست توکن‌ها", callback_data="list_all_tokens"),
                        InlineKeyboardButton("➕ توکن جدید", callback_data="create_new_token")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                    ]
                ])
            else:
                text = f"❌ **خطا در غیرفعال‌سازی توکن**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}\n\n"
                text += "لطفاً دوباره تلاش کنید."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 تلاش مجدد", callback_data="deactivate_current_token"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                    ]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_deactivate_current_token: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_deactivate_expired_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """غیرفعال‌سازی توکن‌های منقضی شده"""
        try:
            query = update.callback_query
            await query.answer("در حال غیرفعال‌سازی توکن‌های منقضی...")
            
            # غیرفعال‌سازی توکن‌های منقضی از طریق API
            result = await self.deactivate_expired_tokens()
            
            if result.get('success'):
                count = result.get('count', 0)
                text = f"✅ **توکن‌های منقضی غیرفعال شدند**\n\n"
                text += f"📊 **تعداد توکن‌های غیرفعال شده:** {count}\n"
                text += f"📅 **زمان اجرا:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                text += "✅ تمام توکن‌های منقضی با موفقیت غیرفعال شدند."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📋 لیست توکن‌ها", callback_data="list_all_tokens"),
                        InlineKeyboardButton("🔄 بروزرسانی", callback_data="deactivate_expired_tokens")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                    ]
                ])
            else:
                text = f"❌ **خطا در غیرفعال‌سازی توکن‌های منقضی**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}\n\n"
                text += "لطفاً دوباره تلاش کنید."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 تلاش مجدد", callback_data="deactivate_expired_tokens"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                    ]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_deactivate_expired_tokens: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_deactivate_user_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """غیرفعال‌سازی توکن‌های کاربر"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "👤 **غیرفعال‌سازی توکن‌های کاربر**\n\n"
            text += "لطفاً شناسه کاربر را وارد کنید:\n\n"
            text += "• برای غیرفعال‌سازی توکن‌های یک کاربر خاص\n"
            text += "• شناسه کاربر باید عددی باشد\n"
            text += "• می‌توانید از لیست کاربران انتخاب کنید"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📋 لیست کاربران", callback_data="list_users"),
                    InlineKeyboardButton("🔍 جستجوی کاربر", callback_data="search_user")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_deactivate_user_tokens: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_deactivate_suspicious_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """غیرفعال‌سازی توکن‌های مشکوک"""
        try:
            query = update.callback_query
            await query.answer("در حال بررسی توکن‌های مشکوک...")
            
            # دریافت توکن‌های مشکوک از طریق API
            result = await self.get_suspicious_tokens()
            
            if result.get('success') and result.get('tokens'):
                tokens = result.get('tokens', [])
                
                text = f"⚠️ **توکن‌های مشکوک شناسایی شدند**\n\n"
                text += f"📊 **تعداد:** {len(tokens)} توکن\n\n"
                
                for i, token in enumerate(tokens, 1):
                    text += f"{i}. 🔍 **توکن مشکوک**\n"
                    text += f"   🆔 شناسه: `{token.get('token_id', 'N/A')}`\n"
                    text += f"   🏷 نوع: {self._get_token_type_name(token.get('type', 'user'))}\n"
                    text += f"   ⚠️ دلیل: {token.get('suspicion_reason', 'نامشخص')}\n"
                    text += f"   📊 استفاده: {token.get('usage_count', 0)} بار\n\n"
                
                text += "آیا می‌خواهید این توکن‌ها را غیرفعال کنید؟"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ غیرفعال‌سازی همه", callback_data="confirm_deactivate_suspicious"),
                        InlineKeyboardButton("🔍 بررسی دقیق‌تر", callback_data="inspect_suspicious_tokens")
                    ],
                    [
                        InlineKeyboardButton("❌ انصراف", callback_data="token_dashboard")
                    ]
                ])
            else:
                text = "✅ **هیچ توکن مشکوکی یافت نشد**\n\n"
                text += "تمام توکن‌ها در حالت عادی هستند."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 بررسی مجدد", callback_data="deactivate_suspicious_tokens"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                    ]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_deactivate_suspicious_tokens: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_set_expiry_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیم انقضای توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            # استخراج اطلاعات از callback_data
            callback_data = query.data
            parts = callback_data.split('_')
            
            if len(parts) < 4:
                await query.edit_message_text(
                    "❌ **خطا:** اطلاعات ناقص است.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                    ]])
                )
                return
            
            action = parts[3]  # default, bulk, custom
            token_id = parts[4] if len(parts) > 4 else None
            
            text = f"⏰ **تنظیم انقضای توکن**\n\n"
            
            if action == 'default':
                text += "لطفاً مدت زمان انقضای پیش‌فرض را انتخاب کنید:\n\n"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("1 روز", callback_data=f"set_default_expiry_1"),
                        InlineKeyboardButton("7 روز", callback_data=f"set_default_expiry_7")
                    ],
                    [
                        InlineKeyboardButton("30 روز", callback_data=f"set_default_expiry_30"),
                        InlineKeyboardButton("90 روز", callback_data=f"set_default_expiry_90")
                    ],
                    [
                        InlineKeyboardButton("نامحدود", callback_data=f"set_default_expiry_0"),
                        InlineKeyboardButton("سفارشی", callback_data=f"set_default_expiry_custom")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                    ]
                ])
            elif action == 'bulk':
                text += "لطفاً مدت زمان انقضای دسته‌ای را انتخاب کنید:\n\n"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("1 روز", callback_data=f"set_bulk_expiry_1"),
                        InlineKeyboardButton("7 روز", callback_data=f"set_bulk_expiry_7")
                    ],
                    [
                        InlineKeyboardButton("30 روز", callback_data=f"set_bulk_expiry_30"),
                        InlineKeyboardButton("90 روز", callback_data=f"set_bulk_expiry_90")
                    ],
                    [
                        InlineKeyboardButton("نامحدود", callback_data=f"set_bulk_expiry_0"),
                        InlineKeyboardButton("سفارشی", callback_data=f"set_bulk_expiry_custom")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                    ]
                ])
            elif action == 'custom' and token_id:
                text += f"لطفاً مدت زمان انقضای توکن `{token_id}` را انتخاب کنید:\n\n"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("1 روز", callback_data=f"set_custom_expiry_{token_id}_1"),
                        InlineKeyboardButton("7 روز", callback_data=f"set_custom_expiry_{token_id}_7")
                    ],
                    [
                        InlineKeyboardButton("30 روز", callback_data=f"set_custom_expiry_{token_id}_30"),
                        InlineKeyboardButton("90 روز", callback_data=f"set_custom_expiry_{token_id}_90")
                    ],
                    [
                        InlineKeyboardButton("نامحدود", callback_data=f"set_custom_expiry_{token_id}_0"),
                        InlineKeyboardButton("سفارشی", callback_data=f"set_custom_expiry_{token_id}_custom")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                    ]
                ])
            else:
                text = "❌ **خطا:** درخواست نامعتبر است."
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_set_expiry_action: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_search_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """جستجوی توکن‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔍 **جستجوی توکن‌ها**\n\n"
            text += "این بخش در حال توسعه است...\n\n"
            text += "قابلیت‌های آینده:\n"
            text += "• جستجو بر اساس نام\n"
            text += "• جستجو بر اساس نوع\n"
            text += "• جستجو بر اساس تاریخ ایجاد\n"
            text += "• فیلتر بر اساس وضعیت"
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="list_all_tokens")
            ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_search_tokens: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_bulk_delete_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف دسته‌ای توکن‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🗑 **حذف دسته‌ای توکن‌ها**\n\n"
            text += "⚠️ **هشدار:** این عملیات برگشت‌پذیر نیست!\n\n"
            text += "گزینه‌های حذف:\n"
            text += "• حذف توکن‌های منقضی شده\n"
            text += "• حذف توکن‌های غیرفعال\n"
            text += "• حذف توکن‌های بدون استفاده\n"
            text += "• حذف بر اساس نوع توکن"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⏰ توکن‌های منقضی", callback_data="bulk_delete_expired"),
                    InlineKeyboardButton("🔴 توکن‌های غیرفعال", callback_data="bulk_delete_inactive")
                ],
                [
                    InlineKeyboardButton("💤 بدون استفاده", callback_data="bulk_delete_unused"),
                    InlineKeyboardButton("🎯 بر اساس نوع", callback_data="bulk_delete_by_type")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="list_all_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_bulk_delete_tokens: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_detailed_token_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """آمار کامل توکن‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت آمار دقیق
            stats = await self.get_token_statistics()
            
            text = "📊 **آمار کامل توکن‌ها**\n\n"
            
            if stats.get('success'):
                data = stats.get('data', {})
                text += f"📈 **آمار عمومی:**\n"
                text += f"• کل توکن‌ها: {data.get('total_tokens', 0)}\n"
                text += f"• توکن‌های فعال: {data.get('active_tokens', 0)}\n"
                text += f"• توکن‌های منقضی: {data.get('expired_tokens', 0)}\n"
                text += f"• توکن‌های غیرفعال: {data.get('inactive_tokens', 0)}\n\n"
                
                text += f"🏷 **تفکیک بر اساس نوع:**\n"
                text += f"• مدیر: {data.get('admin_tokens', 0)}\n"
                text += f"• محدود: {data.get('limited_tokens', 0)}\n"
                text += f"• کاربر: {data.get('user_tokens', 0)}\n"
                text += f"• API: {data.get('api_tokens', 0)}\n\n"
                
                text += f"📊 **آمار استفاده:**\n"
                text += f"• استفاده امروز: {data.get('daily_usage', 0)}\n"
                text += f"• استفاده هفته: {data.get('weekly_usage', 0)}\n"
                text += f"• استفاده ماه: {data.get('monthly_usage', 0)}\n"
                text += f"• کل استفاده‌ها: {data.get('total_usage', 0):,}\n\n"
                
                text += f"📅 **آمار زمانی:**\n"
                text += f"• ایجاد شده امروز: {data.get('tokens_created_today', 0)}\n"
                text += f"• منقضی شده امروز: {data.get('tokens_expired_today', 0)}\n"
                text += f"• آخرین فعالیت: {data.get('last_activity', 'نامشخص')}\n"
            else:
                text += "❌ خطا در دریافت آمار کامل"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data="detailed_token_stats"),
                    InlineKeyboardButton("📈 نمودار", callback_data="token_stats_chart")
                ],
                [
                    InlineKeyboardButton("💾 صادرات", callback_data="export_tokens"),
                    InlineKeyboardButton("📧 ارسال ایمیل", callback_data="email_token_stats")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="list_all_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_detailed_token_stats: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_set_default_expiry(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیم انقضای پیش‌فرض"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "⏰ **تنظیم انقضای پیش‌فرض**\n\n"
            text += "لطفاً مدت زمان انقضای پیش‌فرض را برای توکن‌های جدید انتخاب کنید:\n\n"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("1 روز", callback_data="set_default_expiry_1"),
                    InlineKeyboardButton("7 روز", callback_data="set_default_expiry_7")
                ],
                [
                    InlineKeyboardButton("30 روز", callback_data="set_default_expiry_30"),
                    InlineKeyboardButton("90 روز", callback_data="set_default_expiry_90")
                ],
                [
                    InlineKeyboardButton("365 روز", callback_data="set_default_expiry_365"),
                    InlineKeyboardButton("نامحدود", callback_data="set_default_expiry_0")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="token_security_settings")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_set_default_expiry: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_set_usage_limit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیم حد استفاده"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔢 **تنظیم حد استفاده**\n\n"
            text += "لطفاً حداکثر تعداد استفاده روزانه را برای توکن‌ها تعیین کنید:\n\n"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("100 درخواست", callback_data="set_usage_limit_100"),
                    InlineKeyboardButton("500 درخواست", callback_data="set_usage_limit_500")
                ],
                [
                    InlineKeyboardButton("1000 درخواست", callback_data="set_usage_limit_1000"),
                    InlineKeyboardButton("5000 درخواست", callback_data="set_usage_limit_5000")
                ],
                [
                    InlineKeyboardButton("10000 درخواست", callback_data="set_usage_limit_10000"),
                    InlineKeyboardButton("نامحدود", callback_data="set_usage_limit_0")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="token_security_settings")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_set_usage_limit: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_ip_restrictions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """محدودیت‌های IP"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🌐 **محدودیت‌های IP**\n\n"
            text += "🔒 **وضعیت فعلی:** غیرفعال\n\n"
            text += "گزینه‌های دسترسی:\n"
            text += "• **فعال‌سازی محدودیت IP:** تنها IP های مجاز دسترسی داشته باشند\n"
            text += "• **لیست سفید IP:** اضافه کردن IP های مجاز\n"
            text += "• **لیست سیاه IP:** مسدود کردن IP های خاص\n"
            text += "• **محدودیت جغرافیایی:** محدودیت بر اساس کشور"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🟢 فعال‌سازی", callback_data="enable_ip_restrictions"),
                    InlineKeyboardButton("🔴 غیرفعال‌سازی", callback_data="disable_ip_restrictions")
                ],
                [
                    InlineKeyboardButton("📝 لیست سفید", callback_data="manage_whitelist_ip"),
                    InlineKeyboardButton("❌ لیست سیاه", callback_data="manage_blacklist_ip")
                ],
                [
                    InlineKeyboardButton("🌍 محدودیت جغرافیایی", callback_data="geo_restrictions"),
                    InlineKeyboardButton("📊 آمار IP", callback_data="ip_statistics")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="token_security_settings")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_ip_restrictions: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_security_alerts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """هشدارهای امنیتی"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔔 **هشدارهای امنیتی**\n\n"
            text += "🟢 **وضعیت:** فعال\n\n"
            text += "نوع هشدارها:\n"
            text += "• **توکن جدید:** اطلاع از ایجاد توکن جدید\n"
            text += "• **دسترسی مشکوک:** هشدار فعالیت غیرعادی\n"
            text += "• **تلاش ورود ناموفق:** تلاش‌های دسترسی غیرمجاز\n"
            text += "• **انقضای توکن:** یادآوری انقضای توکن‌ها\n"
            text += "• **حد استفاده:** هشدار رسیدن به حد مجاز استفاده"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📧 هشدار ایمیل", callback_data="email_alerts_toggle"),
                    InlineKeyboardButton("📱 هشدار تلگرام", callback_data="telegram_alerts_toggle")
                ],
                [
                    InlineKeyboardButton("⚙️ تنظیمات هشدار", callback_data="alert_settings"),
                    InlineKeyboardButton("📊 تاریخچه هشدارها", callback_data="alert_history")
                ],
                [
                    InlineKeyboardButton("🔕 غیرفعال کردن همه", callback_data="disable_all_alerts"),
                    InlineKeyboardButton("🔔 فعال کردن همه", callback_data="enable_all_alerts")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="token_security_settings")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_security_alerts: {e}")
            await self.handle_error(update, context, e)

    async def handle_copy_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """کپی توکن"""
        try:
            query = update.callback_query
            await query.answer("✅ توکن کپی شد!")
            
            # Extract token_id from callback_data
            token_id = query.data.split('_')[2]
            
            text = f"📋 **کپی توکن**\n\n"
            text += f"🆔 **شناسه:** {token_id}\n\n"
            text += "⚠️ **نکته:** توکن به کلیپ‌برد شما کپی نشده است.\n"
            text += "لطفاً از منوی جزئیات توکن استفاده کنید تا توکن کامل را مشاهده کنید."
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="list_all_tokens")
            ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_copy_token: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_token_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش جزئیات توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            # Extract token_id from callback_data
            token_id = query.data.split('_')[2]
            
            text = f"📊 **جزئیات توکن**\n\n"
            text += f"🆔 **شناسه:** {token_id}\n\n"
            text += "این بخش در حال توسعه است...\n\n"
            text += "قابلیت‌های آینده:\n"
            text += "• نمایش کامل اطلاعات توکن\n"
            text += "• تاریخچه استفاده\n"
            text += "• آمار عملکرد\n"
            text += "• لاگ‌های دسترسی"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data=f"token_details_{token_id}"),
                    InlineKeyboardButton("🗑 حذف", callback_data=f"delete_token_{token_id}")
                ],
                [
                    InlineKeyboardButton("🔒 غیرفعال‌سازی", callback_data=f"deactivate_token_{token_id}"),
                    InlineKeyboardButton("⏰ تنظیم انقضا", callback_data=f"set_token_expiry_{token_id}")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="list_all_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_token_details: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_cleanup_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عملیات پاکسازی"""
        try:
            query = update.callback_query
            await query.answer()
            
            action = query.data.split('_')[1]  # expired, inactive, unused, all
            
            text = f"🧹 **پاکسازی توکن‌ها**\n\n"
            
            if action == 'expired':
                text += "⏰ **پاکسازی توکن‌های منقضی**\n\n"
                text += "این عملیات تمام توکن‌های منقضی شده را حذف می‌کند.\n"
            elif action == 'inactive':
                text += "🔴 **پاکسازی توکن‌های غیرفعال**\n\n"
                text += "این عملیات تمام توکن‌های غیرفعال را حذف می‌کند.\n"
            elif action == 'unused':
                text += "💤 **پاکسازی توکن‌های بدون استفاده**\n\n"
                text += "این عملیات توکن‌های بدون استفاده را حذف می‌کند.\n"
            elif action == 'all':
                text += "🗑 **پاکسازی کامل**\n\n"
                text += "⚠️ **هشدار:** این عملیات همه توکن‌ها را حذف می‌کند!\n"
            
            text += "\n⚠️ **توجه:** این عملیات برگشت‌پذیر نیست!"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ تأیید", callback_data=f"confirm_cleanup_{action}"),
                    InlineKeyboardButton("❌ انصراف", callback_data="cleanup_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_cleanup_action: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_bulk_delete_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عملیات حذف دسته‌ای"""
        try:
            query = update.callback_query
            await query.answer()
            
            parts = query.data.split('_')
            action = '_'.join(parts[2:])  # expired, inactive, unused, by_type
            
            text = f"🗑 **حذف دسته‌ای توکن‌ها**\n\n"
            
            if action == 'expired':
                text += "⏰ **حذف توکن‌های منقضی**\n\n"
                text += "این عملیات تمام توکن‌های منقضی شده را حذف می‌کند.\n"
            elif action == 'inactive': 
                text += "🔴 **حذف توکن‌های غیرفعال**\n\n"
                text += "این عملیات تمام توکن‌های غیرفعال را حذف می‌کند.\n"
            elif action == 'unused':
                text += "💤 **حذف توکن‌های بدون استفاده**\n\n"
                text += "این عملیات توکن‌های بدون استفاده را حذف می‌کند.\n"
            elif action == 'by_type':
                text += "🎯 **حذف بر اساس نوع**\n\n"
                text += "لطفاً نوع توکن‌هایی که می‌خواهید حذف کنید را انتخاب کنید:\n"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🛡 مدیر", callback_data="bulk_delete_type_admin"),
                        InlineKeyboardButton("⚙️ محدود", callback_data="bulk_delete_type_limited")
                    ],
                    [
                        InlineKeyboardButton("👤 کاربر", callback_data="bulk_delete_type_user"),
                        InlineKeyboardButton("🔑 API", callback_data="bulk_delete_type_api")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_delete_tokens")
                    ]
                ])
                
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
                return
            
            text += "\n⚠️ **توجه:** این عملیات برگشت‌پذیر نیست!"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ تأیید", callback_data=f"confirm_bulk_delete_{action}"),
                    InlineKeyboardButton("❌ انصراف", callback_data="bulk_delete_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_bulk_delete_action: {e}")
            await self.handle_error(update, context, e)

    async def handle_export_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """صادرات اطلاعات توکن‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "💾 **صادرات اطلاعات توکن‌ها**\n\n"
            text += "لطفاً فرمت صادرات را انتخاب کنید:\n\n"
            text += "• **JSON:** فرمت ساده و قابل خواندن\n"
            text += "• **CSV:** قابل باز کردن در Excel\n"
            text += "• **PDF:** گزارش کامل و آماده چاپ\n"
            text += "• **XML:** فرمت استاندارد تبادل داده"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📄 JSON", callback_data="export_tokens_json"),
                    InlineKeyboardButton("📊 CSV", callback_data="export_tokens_csv")
                ],
                [
                    InlineKeyboardButton("📑 PDF", callback_data="export_tokens_pdf"),
                    InlineKeyboardButton("🔗 XML", callback_data="export_tokens_xml")
                ],
                [
                    InlineKeyboardButton("📧 ارسال ایمیل", callback_data="export_tokens_email"),
                    InlineKeyboardButton("☁️ ذخیره ابری", callback_data="export_tokens_cloud")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="list_all_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_export_tokens: {e}")
            await self.handle_error(update, context, e)

    async def handle_confirm_new_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأیید ایجاد توکن جدید"""
        try:
            query = update.callback_query
            await query.answer("در حال تأیید ایجاد توکن...")
            
            # استخراج اطلاعات از callback_data
            callback_data = query.data
            parts = callback_data.split('_')
            
            if len(parts) < 4:
                await query.edit_message_text(
                    "❌ **خطا:** اطلاعات ناقص است.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                    ]])
                )
                return
            
            token_type = parts[3]  # admin, limited, user
            
            # دریافت اطلاعات توکن از session
            user_id = update.effective_user.id
            session = await self.db.get_user_session(user_id)
            
            if not session or not session.get('temp_data'):
                await query.edit_message_text(
                    "❌ **خطا:** اطلاعات جلسه یافت نشد.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                    ]])
                )
                return
            
            temp_data = json.loads(session.get('temp_data', '{}'))
            
            # ایجاد توکن از طریق API
            result = await self.create_api_token(
                token_type=token_type,
                name=temp_data.get('name', f'توکن {token_type}'),
                expires_in_days=temp_data.get('expires_in_days')
            )
            
            if result.get('success'):
                token_data = result.get('data', {})
                
                text = f"✅ **توکن جدید با موفقیت ایجاد شد**\n\n"
                text += f"🔐 **نوع:** {self._get_token_type_name(token_type)}\n"
                text += f"🆔 **شناسه:** {token_data.get('token_id', 'N/A')}\n"
                text += f"📝 **نام:** {token_data.get('name', 'بدون نام')}\n"
                text += f"📅 **تاریخ ایجاد:** {token_data.get('created_at', 'نامشخص')[:16]}\n"
                
                if token_data.get('expires_at'):
                    text += f"⏰ **انقضا:** {token_data.get('expires_at')[:16]}\n"
                else:
                    text += f"♾ **انقضا:** بدون محدودیت\n"
                
                text += f"\n🔑 **توکن:**\n{token_data.get('token', '')}\n\n"
                
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
                text = f"❌ **خطا در ایجاد توکن**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}\n\n"
                text += "لطفاً دوباره تلاش کنید یا با مدیر سیستم تماس بگیرید."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 تلاش مجدد", callback_data=f"create_token_{token_type}"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                    ]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_confirm_new_token: {e}")
            await self.handle_error(update, context, e)
    
    # متدهای کمکی
    
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
    
    # متدهای API
    
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
    
    async def deactivate_token(self, token_id: str) -> Dict[str, Any]:
        """غیرفعال‌سازی یک توکن"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/admin/tokens/{token_id}/deactivate",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        return {'success': True}
                    else:
                        error_data = await response.json()
                        return {'success': False, 'error': error_data.get('error', 'خطای نامشخص')}
        except Exception as e:
            logger.error(f"Error deactivating token: {e}")
            return {'success': False, 'error': str(e)}
    
    async def deactivate_expired_tokens(self) -> Dict[str, Any]:
        """غیرفعال‌سازی توکن‌های منقضی شده"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/admin/tokens/deactivate-expired",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {'success': True, 'count': data.get('count', 0)}
                    else:
                        error_data = await response.json()
                        return {'success': False, 'error': error_data.get('error', 'خطای نامشخص')}
        except Exception as e:
            logger.error(f"Error deactivating expired tokens: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_suspicious_tokens(self) -> Dict[str, Any]:
        """دریافت توکن‌های مشکوک"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/admin/tokens/suspicious",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {'success': True, 'tokens': data.get('tokens', [])}
                    else:
                        return {'success': False, 'error': f'HTTP {response.status}'}
        except Exception as e:
            logger.error(f"Error getting suspicious tokens: {e}")
            return {'success': False, 'error': str(e)}
    
    async def set_token_expiry(self, token_id: str, expires_in_days: int) -> Dict[str, Any]:
        """تنظیم انقضای توکن"""
        try:
            data = {
                'expires_in_days': expires_in_days
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/admin/tokens/{token_id}/set-expiry",
                    headers=self.headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        return {'success': True}
                    else:
                        error_data = await response.json()
                        return {'success': False, 'error': error_data.get('error', 'خطای نامشخص')}
        except Exception as e:
            logger.error(f"Error setting token expiry: {e}")
            return {'success': False, 'error': str(e)}