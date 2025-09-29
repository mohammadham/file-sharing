#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token Users Handler - مدیریت کاربران و توکن‌های آن‌ها
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

from handlers.base_handler import BaseHandler

logger = logging.getLogger(__name__)


class TokenUsersHandler(BaseHandler):
    """مدیریت کاربران و توکن‌های آن‌ها"""
    
    def __init__(self, db, token_manager):
        """
        Args:
            db: دیتابیس منیجر
            token_manager: TokenManagementHandler اصلی برای API calls
        """
        super().__init__(db)
        self.token_manager = token_manager
    
    # === USERS MENU ===
    
    async def show_users_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """منوی اصلی مدیریت کاربران"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت آمار کاربران
            users_stats = await self.token_manager.get_users_statistics()
            
            text = "👥 **مدیریت کاربران سیستم**\n\n"
            
            if users_stats.get('success'):
                data = users_stats.get('data', {})
                text += f"📊 **آمار کاربران:**\n"
                text += f"• کل کاربران: {data.get('total_users', 0):,}\n"
                text += f"• کاربران فعال: {data.get('active_users', 0):,}\n"
                text += f"• کاربران جدید امروز: {data.get('new_users_today', 0)}\n"
                text += f"• کاربران با توکن فعال: {data.get('users_with_tokens', 0):,}\n\n"
                
                text += f"🔑 **آمار توکن‌های کاربران:**\n"
                text += f"• میانگین توکن هر کاربر: {data.get('avg_tokens_per_user', 0.0):.1f}\n"
                text += f"• کاربران بدون توکن: {data.get('users_without_tokens', 0)}\n"
                text += f"• کاربران با بیش از 5 توکن: {data.get('users_with_many_tokens', 0)}\n\n"
            else:
                text += "❌ خطا در دریافت آمار کاربران\n\n"
            
            text += "⚙️ **عملیات مدیریتی:**\n"
            text += "• جست‌وجو و مدیریت کاربران\n"
            text += "• مدیریت توکن‌های هر کاربر\n"
            text += "• تحلیل رفتار کاربران\n"
            text += "• واردات و صادرات کاربران"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📋 لیست کاربران", callback_data="list_users"),
                    InlineKeyboardButton("🔍 جست‌وجوی کاربر", callback_data="search_user")
                ],
                [
                    InlineKeyboardButton("📊 آمار کاربران", callback_data="users_statistics"),
                    InlineKeyboardButton("📈 تحلیل رفتار", callback_data="user_behavior_analysis")
                ],
                [
                    InlineKeyboardButton("🔒 غیرفعال‌سازی توکن‌ها", callback_data="deactivate_user_tokens"),
                    InlineKeyboardButton("⚙️ مدیریت دسته‌ای", callback_data="bulk_user_management")
                ],
                [
                    InlineKeyboardButton("📥 واردات کاربران", callback_data="import_users"),
                    InlineKeyboardButton("📤 صادرات کاربران", callback_data="export_users")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_users_menu: {e}")
            await self.handle_error(update, context, e)
    
    # === LIST USERS ===
    
    async def handle_list_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش لیست کاربران"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت لیست کاربران
            result = await self.token_manager.get_users_list()
            
            text = "📋 **لیست کاربران سیستم**\n\n"
            
            if result.get('success'):
                users = result.get('users', [])
                
                if users:
                    for i, user in enumerate(users[:10], 1):  # نمایش 10 کاربر اول
                        status_icon = "🟢" if user.get('is_active', True) else "🔴"
                        
                        text += f"{i}. {status_icon} **{user.get('username', f'کاربر {i}')}**\n"
                        text += f"   🆔 شناسه: `{user.get('user_id', 'N/A')}`\n"
                        text += f"   📧 ایمیل: {user.get('email', 'نامشخص')}\n"
                        text += f"   📅 عضویت: {user.get('created_at', 'نامشخص')[:16]}\n"
                        text += f"   🔑 تعداد توکن: {user.get('token_count', 0)}\n"
                        
                        if user.get('last_login'):
                            text += f"   🕐 آخرین ورود: {user.get('last_login')[:16]}\n"
                        
                        text += "\n"
                    
                    total_users = result.get('total_count', len(users))
                    if total_users > 10:
                        text += f"... و {total_users - 10} کاربر دیگر\n"
                        
                else:
                    text += "❌ هیچ کاربری یافت نشد!"
            else:
                text += f"❌ خطا در دریافت لیست کاربران\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data="list_users"),
                    InlineKeyboardButton("📊 مرتب‌سازی", callback_data="sort_users")
                ],
                [
                    InlineKeyboardButton("🔍 جست‌وجو", callback_data="search_user"),
                    InlineKeyboardButton("📄 صفحه بعد", callback_data="list_users_page_2")
                ],
                [
                    InlineKeyboardButton("📈 آمار کاربران", callback_data="users_statistics"),
                    InlineKeyboardButton("💾 صادرات", callback_data="export_users")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="users_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_list_users: {e}")
            await self.handle_error(update, context, e)
    
    # === SEARCH USER ===
    
    async def handle_search_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """جست‌وجوی کاربر"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔍 **جست‌وجوی کاربر**\n\n"
            text += "لطفاً نوع جست‌وجو را انتخاب کنید:\n\n"
            text += "• **بر اساس شناسه:** جست‌وجو با شناسه عددی کاربر\n"
            text += "• **بر اساس نام کاربری:** جست‌وجو با نام کاربری\n"
            text += "• **بر اساس ایمیل:** جست‌وجو با آدرس ایمیل\n"
            text += "• **بر اساس شماره تلفن:** جست‌وجو با شماره موبایل\n"
            text += "• **بر اساس توکن:** یافتن کاربر صاحب توکن خاص"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🆔 شناسه کاربر", callback_data="search_by_uid"),
                    InlineKeyboardButton("👤 نام کاربری", callback_data="search_by_username")
                ],
                [
                    InlineKeyboardButton("📧 ایمیل", callback_data="search_by_email"),
                    InlineKeyboardButton("📱 شماره تلفن", callback_data="search_by_phone")
                ],
                [
                    InlineKeyboardButton("🔑 شناسه توکن", callback_data="search_by_token_id"),
                    InlineKeyboardButton("🔍 جست‌وجوی پیشرفته", callback_data="advanced_user_search")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="users_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_search_user: {e}")
            await self.handle_error(update, context, e)
    
    # === USER DETAILS ===
    
    async def show_user_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش جزئیات کاربر"""
        try:
            query = update.callback_query
            await query.answer()
            
            # استخراج user_id از callback_data
            user_id = query.data.split('_')[-1]
            
            # دریافت اطلاعات کاربر
            result = await self.token_manager.get_user_details(user_id)
            
            if result.get('success'):
                user = result.get('user', {})
                
                text = f"👤 **جزئیات کاربر**\n\n"
                text += f"🆔 **شناسه:** `{user.get('user_id', user_id)}`\n"
                text += f"👤 **نام کاربری:** {user.get('username', 'نامشخص')}\n"
                text += f"📧 **ایمیل:** {user.get('email', 'نامشخص')}\n"
                text += f"📱 **تلفن:** {user.get('phone', 'نامشخص')}\n"
                text += f"🏷 **نقش:** {self._get_user_role_name(user.get('role', 'user'))}\n"
                text += f"📅 **تاریخ عضویت:** {user.get('created_at', 'نامشخص')[:16]}\n"
                
                if user.get('last_login'):
                    text += f"🕐 **آخرین ورود:** {user.get('last_login')[:16]}\n"
                
                text += f"🟢 **وضعیت:** {'فعال' if user.get('is_active', True) else 'غیرفعال'}\n\n"
                
                # آمار توکن‌های کاربر
                tokens_info = user.get('tokens_info', {})
                text += f"🔑 **آمار توکن‌ها:**\n"
                text += f"• کل توکن‌ها: {tokens_info.get('total', 0)}\n"
                text += f"• توکن‌های فعال: {tokens_info.get('active', 0)}\n"
                text += f"• توکن‌های منقضی: {tokens_info.get('expired', 0)}\n"
                text += f"• آخرین استفاده: {tokens_info.get('last_used', 'هرگز')}\n\n"
                
                # آمار استفاده
                usage_stats = user.get('usage_stats', {})
                text += f"📊 **آمار استفاده:**\n"
                text += f"• استفاده امروز: {usage_stats.get('today', 0):,}\n"
                text += f"• استفاده این ماه: {usage_stats.get('this_month', 0):,}\n"
                text += f"• کل استفاده: {usage_stats.get('total', 0):,}\n"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔑 توکن‌های کاربر", callback_data=f"user_tokens_{user_id}"),
                        InlineKeyboardButton("📊 فعالیت کاربر", callback_data=f"user_activity_{user_id}")
                    ],
                    [
                        InlineKeyboardButton("✏️ ویرایش کاربر", callback_data=f"edit_user_{user_id}"),
                        InlineKeyboardButton("🔒 غیرفعال‌سازی", callback_data=f"deactivate_user_{user_id}")
                    ],
                    [
                        InlineKeyboardButton("🗑 حذف کاربر", callback_data=f"delete_user_{user_id}"),
                        InlineKeyboardButton("📊 گزارش کاربر", callback_data=f"user_report_{user_id}")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="list_users")
                    ]
                ])
                
            else:
                text = f"❌ **خطا در دریافت اطلاعات کاربر**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}"
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="list_users")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_user_details: {e}")
            await self.handle_error(update, context, e)
    
    # === USER TOKENS MANAGEMENT ===
    
    async def show_user_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش توکن‌های یک کاربر"""
        try:
            query = update.callback_query
            await query.answer()
            
            # استخراج user_id از callback_data
            user_id = query.data.split('_')[-1]
            
            # دریافت توکن‌های کاربر
            result = await self.token_manager.get_user_tokens(user_id)
            
            text = f"🔑 **توکن‌های کاربر {user_id}**\n\n"
            
            if result.get('success'):
                tokens = result.get('tokens', [])
                
                if tokens:
                    for i, token in enumerate(tokens, 1):
                        status_icon = "🟢" if token.get('is_active', True) else "🔴"
                        type_icon = self._get_token_type_icon(token.get('type', 'user'))
                        
                        text += f"{i}. {type_icon} **{token.get('name', f'توکن {i}')}** {status_icon}\n"
                        text += f"   🆔 شناسه: `{token.get('token_id', 'N/A')}`\n"
                        text += f"   🏷 نوع: {self._get_token_type_name(token.get('type', 'user'))}\n"
                        text += f"   📅 ایجاد: {token.get('created_at', 'نامشخص')[:16]}\n"
                        
                        if token.get('expires_at'):
                            text += f"   ⏰ انقضا: {token.get('expires_at')[:16]}\n"
                        else:
                            text += f"   ♾ انقضا: بدون محدودیت\n"
                        
                        text += f"   📊 استفاده: {token.get('usage_count', 0)} بار\n\n"
                        
                else:
                    text += "❌ این کاربر هیچ توکنی ندارد!"
            else:
                text += f"❌ خطا در دریافت توکن‌های کاربر\n\nعلت: {result.get('error', 'نامشخص')}"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("➕ توکن جدید", callback_data=f"create_token_for_user_{user_id}"),
                    InlineKeyboardButton("🔒 غیرفعال‌سازی همه", callback_data=f"deactivate_all_user_tokens_{user_id}")
                ],
                [
                    InlineKeyboardButton("🗑 حذف منقضی‌ها", callback_data=f"delete_expired_user_tokens_{user_id}"),
                    InlineKeyboardButton("📊 آمار استفاده", callback_data=f"user_tokens_stats_{user_id}")
                ],
                [
                    InlineKeyboardButton("💾 صادرات", callback_data=f"export_user_tokens_{user_id}"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data=f"user_details_{user_id}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_user_tokens: {e}")
            await self.handle_error(update, context, e)
    
    # === DEACTIVATE USER TOKENS ===
    
    async def handle_deactivate_user_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """غیرفعال‌سازی توکن‌های کاربر"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "👤 **غیرفعال‌سازی توکن‌های کاربر**\n\n"
            text += "لطفاً روش شناسایی کاربر را انتخاب کنید:\n\n"
            text += "• **شناسه کاربر:** وارد کردن شناسه عددی کاربر\n"
            text += "• **انتخاب از لیست:** انتخاب از لیست کاربران موجود\n"
            text += "• **جست‌وجوی پیشرفته:** جست‌وجو بر اساس معیارهای مختلف"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🆔 شناسه کاربر", callback_data="deactivate_tokens_by_uid"),
                    InlineKeyboardButton("📋 لیست کاربران", callback_data="deactivate_tokens_from_list")
                ],
                [
                    InlineKeyboardButton("🔍 جست‌وجوی پیشرفته", callback_data="deactivate_tokens_advanced_search"),
                    InlineKeyboardButton("📦 انتخاب چندگانه", callback_data="deactivate_tokens_multiple_users")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="users_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_deactivate_user_tokens: {e}")
            await self.handle_error(update, context, e)
    
    async def deactivate_all_user_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """غیرفعال‌سازی همه توکن‌های یک کاربر"""
        try:
            query = update.callback_query
            await query.answer("در حال غیرفعال‌سازی توکن‌ها...")
            
            # استخراج user_id از callback_data
            user_id = query.data.split('_')[-1]
            
            # غیرفعال‌سازی همه توکن‌های کاربر
            result = await self.token_manager.deactivate_all_user_tokens(user_id)
            
            if result.get('success'):
                count = result.get('count', 0)
                text = f"✅ **توکن‌های کاربر غیرفعال شدند**\n\n"
                text += f"👤 **کاربر:** {user_id}\n"
                text += f"📊 **تعداد توکن‌های غیرفعال شده:** {count}\n"
                text += f"📅 **زمان اجرا:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                text += "✅ تمام توکن‌های کاربر با موفقیت غیرفعال شدند."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔑 مشاهده توکن‌ها", callback_data=f"user_tokens_{user_id}"),
                        InlineKeyboardButton("📋 لیست کاربران", callback_data="list_users")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="users_menu")
                    ]
                ])
            else:
                text = f"❌ **خطا در غیرفعال‌سازی توکن‌ها**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}\n\n"
                text += "لطفاً دوباره تلاش کنید."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 تلاش مجدد", callback_data=f"deactivate_all_user_tokens_{user_id}"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data="users_menu")
                    ]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in deactivate_all_user_tokens: {e}")
            await self.handle_error(update, context, e)
    
    # === IMPORT/EXPORT USERS ===
    
    async def show_import_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """واردات کاربران"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "📥 **واردات کاربران**\n\n"
            text += "این بخش در حال توسعه است...\n\n"
            text += "قابلیت‌های آینده:\n"
            text += "• واردات از فایل CSV\n"
            text += "• واردات از فایل JSON\n"
            text += "• واردات دستی\n"
            text += "• اعتبارسنجی داده‌ها"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📄 فایل CSV", callback_data="import_csv"),
                    InlineKeyboardButton("📋 فایل JSON", callback_data="import_json")
                ],
                [
                    InlineKeyboardButton("✏️ واردات دستی", callback_data="import_manual"),
                    InlineKeyboardButton("📝 راهنما", callback_data="import_guide")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="users_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_import_users: {e}")
            await self.handle_error(update, context, e)
    
    async def show_export_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """صادرات کاربران"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "📤 **صادرات کاربران**\n\n"
            text += "لطفاً فرمت صادرات را انتخاب کنید:\n\n"
            text += "• **JSON:** شامل تمام اطلاعات کاربران\n"
            text += "• **CSV:** مناسب برای Excel\n"
            text += "• **PDF:** گزارش قابل چاپ"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📄 JSON", callback_data="export_users_json"),
                    InlineKeyboardButton("📊 CSV", callback_data="export_users_csv")
                ],
                [
                    InlineKeyboardButton("📕 PDF", callback_data="export_users_pdf"),
                    InlineKeyboardButton("⚙️ تنظیمات صادرات", callback_data="export_users_settings")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="users_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_export_users: {e}")
            await self.handle_error(update, context, e)
    
    # === HELPER METHODS ===
    
    def _get_user_role_name(self, role: str) -> str:
        """نام فارسی نقش کاربر"""
        roles = {
            'admin': 'مدیر',
            'manager': 'مدیر محدود',
            'user': 'کاربر عادی',
            'api_user': 'کاربر API'
        }
        return roles.get(role, 'نامشخص')
    
    def _get_token_type_name(self, token_type: str) -> str:
        """نام فارسی نوع توکن"""
        types = {
            'admin': 'مدیر',
            'limited': 'محدود',
            'user': 'کاربر',
            'api': 'API'
        }
        return types.get(token_type, 'نامشخص')
    
    def _get_token_type_icon(self, token_type: str) -> str:
        """آیکون نوع توکن"""
        icons = {
            'admin': '🛡',
            'limited': '⚙️',
            'user': '👤',
            'api': '🔧'
        }
        return icons.get(token_type, '❓')