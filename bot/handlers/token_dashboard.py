#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token Dashboard Handler - مدیریت داشبورد و عملیات اصلی توکن‌ها
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

from handlers.base_handler import BaseHandler

logger = logging.getLogger(__name__)


class TokenDashboardHandler(BaseHandler):
    """مدیریت داشبورد توکن‌ها و عملیات اصلی"""
    
    def __init__(self, db, token_manager):
        """
        Args:
            db: دیتابیس منیجر
            token_manager: TokenManagementHandler اصلی برای API calls
        """
        super().__init__(db)
        self.token_manager = token_manager
    
    # === DASHBOARD METHODS ===
    
    async def show_token_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """داشبورد اصلی مدیریت توکن‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت آمار توکن‌ها
            stats = await self.token_manager.get_token_statistics()
            
            text = "🔗 **داشبورد مدیریت توکن‌ها**\n\n"
            
            if stats.get('success'):
                data = stats.get('data', {})
                text += f"📊 **آمار خلاصه:**\n"
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
                    InlineKeyboardButton("🔐 مدیریت توکن‌ها", callback_data="manage_tokens"),
                    InlineKeyboardButton("🔒 امنیت", callback_data="security_menu")
                ],
                [
                    InlineKeyboardButton("📈 گزارش‌ها", callback_data="reports_menu"),
                    InlineKeyboardButton("🧹 پاک‌سازی", callback_data="cleanup_menu")
                ],
                [
                    InlineKeyboardButton("👥 کاربران", callback_data="users_menu"),
                    InlineKeyboardButton("⚙️ تنظیمات", callback_data="system_settings")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="download_system_control")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_token_dashboard: {e}")
            await self.handle_error(update, context, e)
    
    # === TOKEN MANAGEMENT MENU ===
    
    async def show_manage_tokens_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """منوی مدیریت توکن‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔐 **مدیریت توکن‌ها**\n\n"
            text += "گزینه‌های مدیریتی:\n"
            text += "• **ایجاد توکن:** تولید توکن جدید با انواع مختلف دسترسی\n"
            text += "• **لیست توکن‌ها:** مشاهده و مدیریت توکن‌های موجود\n"
            text += "• **جستجو:** یافتن توکن‌های خاص\n"
            text += "• **غیرفعال‌سازی:** مدیریت وضعیت توکن‌ها"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("➕ ایجاد توکن جدید", callback_data="create_new_token"),
                    InlineKeyboardButton("📋 لیست توکن‌ها", callback_data="list_all_tokens")
                ],
                [
                    InlineKeyboardButton("🔍 جستجو و فیلتر", callback_data="search_tokens"),
                    InlineKeyboardButton("✏️ ویرایش توکن‌ها", callback_data="edit_tokens_menu")
                ],
                [
                    InlineKeyboardButton("🔒 غیرفعال‌سازی", callback_data="deactivate_tokens"),
                    InlineKeyboardButton("🗑 حذف", callback_data="delete_tokens_menu")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_manage_tokens_menu: {e}")
            await self.handle_error(update, context, e)
    
    # === TOKEN CREATION ===
    
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
            text += "• تنظیمات سیستم\n\n"
            
            text += "⚙️ **توکن محدود (Limited):**\n"
            text += "• دسترسی به عملیات محدود\n"
            text += "• ایجاد و مدیریت لینک‌ها\n"
            text += "• مشاهده آمار شخصی\n\n"
            
            text += "👤 **توکن کاربر (User):**\n"
            text += "• دسترسی پایه\n"
            text += "• ایجاد لینک دانلود\n"
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
                    InlineKeyboardButton("🔙 بازگشت", callback_data="manage_tokens")
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
            result = await self.token_manager.create_api_token(token_type)
            
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
    
    # === TOKEN LIST ===
    
    async def show_token_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش لیست توکن‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت لیست توکن‌ها
            tokens_result = await self.token_manager.get_all_tokens()
            
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
                        
                        text += f"   📊 استفاده: {token.get('usage_count', 0)} بار\n\n"
                        
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
                    InlineKeyboardButton("📦 عملیات گروهی", callback_data="bulk_actions")
                ],
                [
                    InlineKeyboardButton("📊 آمار کامل", callback_data="detailed_token_stats"),
                    InlineKeyboardButton("💾 صادرات", callback_data="export_tokens")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="manage_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_token_list: {e}")
            await self.handle_error(update, context, e)
    
    # === HELPER METHODS ===
    
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
    
    def _get_token_permissions(self, token_type: str) -> list:
        """لیست دسترسی‌های نوع توکن"""
        permissions = {
            'admin': [
                'دسترسی کامل به تمام عملیات',
                'مدیریت کاربران و توکن‌ها', 
                'تنظیمات سیستم',
                'گزارش‌گیری پیشرفته',
                'مدیریت امنیتی'
            ],
            'limited': [
                'ایجاد و مدیریت لینک‌ها',
                'مشاهده آمار شخصی',
                'دانلود فایل‌ها',
                'دسترسی محدود به API'
            ],
            'user': [
                'ایجاد لینک دانلود',
                'مشاهده آمار محدود',
                'استفاده روزانه محدود',
                'دسترسی پایه'
            ]
        }
        return permissions.get(token_type, ['دسترسی پایه'])
    
    # === PLACEHOLDER METHODS ===
    
    async def handle_search_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """جستجوی توکن‌ها - placeholder"""
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
    
    async def show_permissions_manager(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت دسترسی‌ها - placeholder"""
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
    
    async def handle_copy_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """کپی توکن"""
        try:
            query = update.callback_query
            await query.answer("✅ توکن کپی شد!")
            
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
            
            token_id = query.data.split('_')[2]
            
            # دریافت اطلاعات توکن از API
            result = await self.token_manager.get_token_details(token_id)
            
            if result.get('success'):
                token = result.get('token', {})
                
                text = f"📊 **جزئیات توکن**\n\n"
                text += f"🆔 **شناسه:** `{token.get('token_id', token_id)}`\n"
                text += f"🏷 **نوع:** {self._get_token_type_name(token.get('type', 'user'))}\n"
                text += f"📝 **نام:** {token.get('name', 'بدون نام')}\n"
                text += f"📅 **تاریخ ایجاد:** {token.get('created_at', 'نامشخص')[:16]}\n"
                
                if token.get('expires_at'):
                    text += f"⏰ **انقضا:** {token.get('expires_at')[:16]}\n"
                else:
                    text += f"♾ **انقضا:** بدون محدودیت\n"
                
                text += f"📊 **تعداد استفاده:** {token.get('usage_count', 0)}\n"
                
                if token.get('last_used_at'):
                    text += f"🕐 **آخرین استفاده:** {token.get('last_used_at')[:16]}\n"
                
                text += f"🟢 **وضعیت:** {'فعال' if token.get('is_active', True) else 'غیرفعال'}\n\n"
                
                text += f"🔑 **توکن کامل:**\n"
                text += f"`{token.get('token', 'نامشخص')}`\n\n"
                
                text += f"📊 **دسترسی‌ها:**\n"
                permissions = self._get_token_permissions(token.get('type', 'user'))
                for perm in permissions:
                    text += f"• {perm}\n"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_token_{token_id}"),
                        InlineKeyboardButton("📊 آمار", callback_data=f"token_stats_{token_id}")
                    ],
                    [
                        InlineKeyboardButton("📋 کپی توکن", callback_data=f"copy_token_{token_id}"),
                        InlineKeyboardButton("🔒 غیرفعال‌سازی", callback_data=f"deactivate_token_{token_id}")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="list_all_tokens")
                    ]
                ])
            else:
                text = f"❌ **خطا در دریافت اطلاعات توکن**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}"
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="list_all_tokens")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_token_details: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_confirm_new_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأیید نهایی توکن جدید"""
        # این متد در کد اصلی وجود ندارد، placeholder اضافه می‌کنم
        try:
            query = update.callback_query
            await query.answer()
            
            text = "✅ **تأیید توکن جدید**\n\n"
            text += "این بخش در حال توسعه است..."
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
            ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_confirm_new_token: {e}")
            await self.handle_error(update, context, e)