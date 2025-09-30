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
                text += "📊 **آمار خلاصه:**\n"
                text += f"• توکن‌های فعال: {data.get('active_tokens', 0)}\n"
                text += f"• توکن‌های منقضی: {data.get('expired_tokens', 0)}\n"
                text += f"• کل توکن‌ها: {data.get('total_tokens', 0)}\n"
                text += f"• استفاده امروز: {data.get('daily_usage', 0)} درخواست\n\n"
                
                text += "🔑 **انواع توکن‌ها:**\n"
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
                
                text = "✅ **توکن جدید تولید شد**\n\n"
                text += f"🔐 **نوع:** {self._get_token_type_name(token_type)}\n"
                text += f"🆔 **شناسه:** `{token_data.get('token_id', 'N/A')}`\n"
                text += f"📝 **نام:** {token_data.get('name', 'بدون نام')}\n"
                text += f"📅 **تاریخ ایجاد:** {token_data.get('created_at', 'نامشخص')[:16]}\n"
                
                if token_data.get('expires_at'):
                    text += f"⏰ **انقضا:** {token_data.get('expires_at')[:16]}\n"
                else:
                    text += "♾ **انقضا:** بدون محدودیت\n"
                
                text += f"\n🔑 **توکن:**\n`{token_data.get('token', '')}`\n\n"
                
                text += "⚠️ **نکات مهم:**\n"
                text += "• این توکن را در جایی امن ذخیره کنید\n"
                text += "• مراقب عدم انتشار عمومی آن باشید\n"
                text += "• در صورت فراموشی قابل بازیابی نیست\n"
                text += "• می‌توانید هر زمان آن را غیرفعال کنید\n\n"
                
                text += "📊 **دسترسی‌های این توکن:**\n"
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
                text = "❌ **خطا در تولید توکن**\n\n"
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
                            text += "   ♾ انقضا: بدون محدودیت\n"
                        
                        text += f"   📊 استفاده: {token.get('usage_count', 0)} بار\n\n"
                        
                        # محدود کردن تعداد نمایش
                        if i >= 10:
                            text += f"... و {len(tokens) - 10} توکن دیگر\n"
                            break
                else:
                    text += "❌ هیچ توکن فعالی یافت نشد!\n\n"
                    text += "💡 برای شروع، یک توکن جدید ایجاد کنید."
            else:
                text += "❌ خطا در دریافت لیست توکن‌ها\n\n"
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
    
    # === TOKEN EDIT OPERATIONS ===
    
    async def show_edit_tokens_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """منوی ویرایش توکن‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "✏️ **ویرایش توکن‌ها**\n\n"
            text += "🔧 **عملیات ویرایش:**\n"
            text += "• **ویرایش نام:** تغییر نام نمایشی توکن\n"
            text += "• **تمدید انقضا:** افزایش یا تغییر زمان انقضا\n"
            text += "• **تغییر نوع:** ارتقا یا کاهش سطح دسترسی\n"
            text += "• **تنظیم کوتا:** تعیین حد استفاده\n"
            text += "• **ویرایش دسته‌ای:** تغییر چندین توکن همزمان\n\n"
            
            text += "⚠️ **نکات مهم:**\n"
            text += "• تغییرات فوری اعمال می‌شود\n"
            text += "• کاهش سطح دسترسی نیاز به تأیید دارد\n"
            text += "• تمدید انقضا برگشت‌پذیر نیست"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📝 ویرایش نام", callback_data="edit_token_name"),
                    InlineKeyboardButton("⏰ تمدید انقضا", callback_data="edit_token_expiry")
                ],
                [
                    InlineKeyboardButton("🔄 تغییر نوع", callback_data="edit_token_type"),
                    InlineKeyboardButton("📊 تنظیم کوتا", callback_data="edit_token_quota")
                ],
                [
                    InlineKeyboardButton("🎯 ویرایش خاص", callback_data="edit_specific_token"),
                    InlineKeyboardButton("📦 ویرایش دسته‌ای", callback_data="bulk_edit_tokens")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="manage_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_edit_tokens_menu: {e}")
            await self.handle_error(update, context, e)
    
    async def show_delete_tokens_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """منوی حذف توکن‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🗑 **حذف توکن‌ها**\n\n"
            text += "⚠️ **هشدار جدی:** حذف توکن‌ها برگشت‌پذیر نیست!\n\n"
            text += "🎯 **روش‌های حذف:**\n"
            text += "• **حذف تکی:** انتخاب دقیق یک توکن\n"
            text += "• **حذف دسته‌ای:** حذف چندین توکن همزمان\n"
            text += "• **حذف بر اساس معیار:** منقضی، غیرفعال، بدون استفاده\n"
            text += "• **حذف همه:** حذف تمام توکن‌ها به جز مدیر فعلی\n\n"
            
            text += "💡 **توصیه:** به جای حذف، توکن‌ها را غیرفعال کنید"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🗑 حذف تکی", callback_data="delete_single_token"),
                    InlineKeyboardButton("📦 حذف دسته‌ای", callback_data="delete_bulk_tokens")
                ],
                [
                    InlineKeyboardButton("⏰ حذف منقضی‌ها", callback_data="delete_expired_tokens"),
                    InlineKeyboardButton("🔴 حذف غیرفعال‌ها", callback_data="delete_inactive_tokens")
                ],
                [
                    InlineKeyboardButton("💤 حذف بدون استفاده", callback_data="delete_unused_tokens"),
                    InlineKeyboardButton("🚨 حذف همه", callback_data="delete_all_tokens")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="manage_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_delete_tokens_menu: {e}")
            await self.handle_error(update, context, e)
    
    async def show_bulk_actions_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """منوی عملیات گروهی"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "📦 **عملیات گروهی توکن‌ها**\n\n"
            text += "⚡ **عملیات سریع:**\n"
            text += "• انتخاب چندین توکن همزمان\n"
            text += "• اعمال تغییرات یکجا\n"
            text += "• صرفه‌جویی در زمان\n\n"
            
            text += "🎯 **انواع عملیات:**\n"
            text += "• غیرفعال‌سازی چندگانه\n"
            text += "• تمدید دسته‌ای\n"
            text += "• تغییر نوع گروهی\n"
            text += "• حذف انتخابی"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔒 غیرفعال‌سازی گروهی", callback_data="bulk_deactivate_tokens"),
                    InlineKeyboardButton("⏰ تمدید گروهی", callback_data="bulk_extend_tokens")
                ],
                [
                    InlineKeyboardButton("🔄 تغییر نوع گروهی", callback_data="bulk_change_type"),
                    InlineKeyboardButton("🗑 حذف انتخابی", callback_data="bulk_delete_selected")
                ],
                [
                    InlineKeyboardButton("✏️ ویرایش گروهی", callback_data="bulk_edit_properties"),
                    InlineKeyboardButton("📋 انتخاب از لیست", callback_data="select_tokens_for_bulk")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="list_all_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_bulk_actions_menu: {e}")
            await self.handle_error(update, context, e)
    
    async def show_advanced_search_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """منوی جستجوی پیشرفته"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔍 **جستجوی پیشرفته توکن‌ها**\n\n"
            text += "🎯 **معیارهای جستجو:**\n"
            text += "• **نام توکن:** جستجو در نام‌ها\n"
            text += "• **نوع توکن:** فیلتر بر اساس نوع\n"
            text += "• **وضعیت:** فعال، غیرفعال، منقضی\n"
            text += "• **تاریخ ایجاد:** بازه زمانی خاص\n"
            text += "• **آخرین استفاده:** بازه زمانی استفاده\n"
            text += "• **میزان استفاده:** بر اساس تعداد استفاده\n\n"
            
            text += "⚙️ **فیلترهای ترکیبی:**\n"
            text += "امکان ترکیب چندین معیار برای جستجوی دقیق‌تر"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📝 جستجوی نام", callback_data="search_by_name"),
                    InlineKeyboardButton("🏷 جستجوی نوع", callback_data="search_by_type")
                ],
                [
                    InlineKeyboardButton("📊 جستجوی وضعیت", callback_data="search_by_status"),
                    InlineKeyboardButton("📅 جستجوی تاریخ", callback_data="search_by_date")
                ],
                [
                    InlineKeyboardButton("🕐 آخرین استفاده", callback_data="search_by_last_used"),
                    InlineKeyboardButton("📈 میزان استفاده", callback_data="search_by_usage")
                ],
                [
                    InlineKeyboardButton("🔄 فیلتر ترکیبی", callback_data="combined_search"),
                    InlineKeyboardButton("💾 ذخیره جستجو", callback_data="save_search")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="list_all_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_advanced_search_menu: {e}")
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
    
    # === ADVANCED SEARCH OPERATIONS ===
    
    async def handle_advanced_search_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش اقدامات جستجوی پیشرفته"""
        try:
            query = update.callback_query
            await query.answer()
            
            action = query.data.replace('search_by_', '')
            
            if action == 'name':
                text = "📝 **جستجو بر اساس نام**\n\n"
                text += "لطفاً نام یا بخشی از نام توکن را وارد کنید:\n\n"
                text += "• جستجو حساس به حروف کوچک و بزرگ نیست\n"
                text += "• می‌توانید بخشی از نام را وارد کنید\n"
                text += "• حداقل 2 کاراکتر لازم است"
                
            elif action == 'type':
                text = "🏷 **جستجو بر اساس نوع**\n\n"
                text += "نوع توکن مورد نظر را انتخاب کنید:"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🛡 مدیر", callback_data="filter_type_admin"),
                        InlineKeyboardButton("⚙️ محدود", callback_data="filter_type_limited")
                    ],
                    [
                        InlineKeyboardButton("👤 کاربر", callback_data="filter_type_user"),
                        InlineKeyboardButton("🔧 API", callback_data="filter_type_api")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                    ]
                ])
                
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
                return
                
            elif action == 'status':
                text = "📊 **جستجو بر اساس وضعیت**\n\n"
                text += "وضعیت مورد نظر را انتخاب کنید:"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🟢 فعال", callback_data="filter_status_active"),
                        InlineKeyboardButton("🔴 غیرفعال", callback_data="filter_status_inactive")
                    ],
                    [
                        InlineKeyboardButton("⏰ منقضی", callback_data="filter_status_expired"),
                        InlineKeyboardButton("⚠️ نزدیک به انقضا", callback_data="filter_status_expiring")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                    ]
                ])
                
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
                return
                
            elif action == 'date':
                text = "📅 **جستجو بر اساس تاریخ ایجاد**\n\n"
                text += "بازه زمانی مورد نظر را انتخاب کنید:"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📅 امروز", callback_data="filter_date_today"),
                        InlineKeyboardButton("📊 این هفته", callback_data="filter_date_week")
                    ],
                    [
                        InlineKeyboardButton("📆 این ماه", callback_data="filter_date_month"),
                        InlineKeyboardButton("📈 3 ماه اخیر", callback_data="filter_date_3months")
                    ],
                    [
                        InlineKeyboardButton("🎯 بازه سفارشی", callback_data="filter_date_custom"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                    ]
                ])
                
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
                return
                
            else:
                text = f"🔍 **جستجوی {action}**\n\n"
                text += "این بخش در حال توسعه است..."
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
            ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_advanced_search_action: {e}")
            await self.handle_error(update, context, e)
    
    async def show_combined_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """جستجوی ترکیبی"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔄 **فیلتر ترکیبی**\n\n"
            text += "امکان ترکیب چندین معیار برای جستجوی دقیق‌تر:\n\n"
            text += "🔧 **معیارهای فعلی:**\n"
            text += "• نوع: همه\n"
            text += "• وضعیت: همه\n"
            text += "• تاریخ: همه\n\n"
            
            text += "لطفاً معیارها را یکی یکی اضافه کنید:"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🏷 افزودن نوع", callback_data="add_type_filter"),
                    InlineKeyboardButton("📊 افزودن وضعیت", callback_data="add_status_filter")
                ],
                [
                    InlineKeyboardButton("📅 افزودن تاریخ", callback_data="add_date_filter"),
                    InlineKeyboardButton("🔢 افزودن استفاده", callback_data="add_usage_filter")
                ],
                [
                    InlineKeyboardButton("🔍 اجرای جستجو", callback_data="execute_combined_search"),
                    InlineKeyboardButton("🗑 پاک کردن فیلترها", callback_data="clear_filters")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_combined_search: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_save_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ذخیره جستجو"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "💾 **ذخیره جستجو**\n\n"
            text += "این بخش در حال توسعه است...\n\n"
            text += "قابلیت‌های آینده:\n"
            text += "• ذخیره معیارهای جستجو\n"
            text += "• جستجوهای ذخیره شده\n"
            text += "• اشتراک‌گذاری جستجو\n"
            text += "• جستجوی خودکار"
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
            ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_save_search: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_bulk_operation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش عملیات گروهی"""
        try:
            query = update.callback_query
            await query.answer()
            
            operation = query.data.replace('bulk_', '')
            
            if operation == 'deactivate_tokens':
                text = "🔒 **غیرفعال‌سازی گروهی**\n\n"
                text += "روش انتخاب توکن‌ها را مشخص کنید:\n\n"
                text += "• **انتخاب از لیست:** انتخاب دستی توکن‌ها\n"
                text += "• **بر اساس معیار:** انتخاب خودکار بر اساس شرایط\n"
                text += "• **همه توکن‌های نوع خاص:** انتخاب بر اساس نوع"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📋 انتخاب از لیست", callback_data="select_from_list_deactivate"),
                        InlineKeyboardButton("🎯 بر اساس معیار", callback_data="criteria_based_deactivate")
                    ],
                    [
                        InlineKeyboardButton("🏷 بر اساس نوع", callback_data="type_based_deactivate"),
                        InlineKeyboardButton("📅 بر اساس تاریخ", callback_data="date_based_deactivate")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_actions")
                    ]
                ])
                
            elif operation == 'extend_tokens':
                text = "⏰ **تمدید گروهی**\n\n"
                text += "مدت زمان تمدید را انتخاب کنید:"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("7 روز", callback_data="extend_bulk_7d"),
                        InlineKeyboardButton("30 روز", callback_data="extend_bulk_30d")
                    ],
                    [
                        InlineKeyboardButton("90 روز", callback_data="extend_bulk_90d"),
                        InlineKeyboardButton("365 روز", callback_data="extend_bulk_365d")
                    ],
                    [
                        InlineKeyboardButton("🎯 سفارشی", callback_data="extend_bulk_custom"),
                        InlineKeyboardButton("♾ نامحدود", callback_data="extend_bulk_unlimited")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_actions")
                    ]
                ])
                
            else:
                text = f"📦 **عملیات {operation}**\n\n"
                text += "این بخش در حال توسعه است..."
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_actions")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_bulk_operation: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_token_edit_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش اقدامات ویرایش توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            action = query.data.replace('edit_token_', '')
            
            text = f"✏️ **ویرایش {action}**\n\n"
            text += "این بخش در حال توسعه است..."
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="edit_tokens_menu")
            ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_token_edit_action: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_token_delete_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش اقدامات حذف توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            action = query.data.replace('delete_', '')
            
            text = f"🗑 **حذف {action}**\n\n"
            text += "این بخش در حال توسعه است..."
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="delete_tokens_menu")
            ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_token_delete_action: {e}")
            await self.handle_error(update, context, e)
    
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
            
            text = "📋 **کپی توکن**\n\n"
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
                
                text = "📊 **جزئیات توکن**\n\n"
                text += f"🆔 **شناسه:** `{token.get('token_id', token_id)}`\n"
                text += f"🏷 **نوع:** {self._get_token_type_name(token.get('type', 'user'))}\n"
                text += f"📝 **نام:** {token.get('name', 'بدون نام')}\n"
                text += f"📅 **تاریخ ایجاد:** {token.get('created_at', 'نامشخص')[:16]}\n"
                
                if token.get('expires_at'):
                    text += f"⏰ **انقضا:** {token.get('expires_at')[:16]}\n"
                else:
                    text += "♾ **انقضا:** بدون محدودیت\n"
                
                text += f"📊 **تعداد استفاده:** {token.get('usage_count', 0)}\n"
                
                if token.get('last_used_at'):
                    text += f"🕐 **آخرین استفاده:** {token.get('last_used_at')[:16]}\n"
                
                text += f"🟢 **وضعیت:** {'فعال' if token.get('is_active', True) else 'غیرفعال'}\n\n"
                
                text += "🔑 **توکن کامل:**\n"
                text += f"`{token.get('token', 'نامشخص')}`\n\n"
                
                text += "📊 **دسترسی‌ها:**\n"
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
                text = "❌ **خطا در دریافت اطلاعات توکن**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}"
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="list_all_tokens")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_token_details: {e}")
            await self.handle_error(update, context, e)
    
    # === TOKEN EDIT OPERATIONS - DETAILED ===
    
    async def handle_edit_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """منوی ویرایش توکن خاص"""
        try:
            query = update.callback_query
            await query.answer()
            
            token_id = query.data.split('_')[2]
            
            # دریافت اطلاعات فعلی توکن
            result = await self.token_manager.get_token_details(token_id)
            
            if result.get('success'):
                token = result.get('token', {})
                
                text = "✏️ **ویرایش توکن**\n\n"
                text += f"🆔 **شناسه:** `{token_id}`\n"
                text += f"📝 **نام فعلی:** {token.get('name', 'بدون نام')}\n"
                text += f"🏷 **نوع فعلی:** {self._get_token_type_name(token.get('type', 'user'))}\n"
                text += f"⏰ **انقضای فعلی:** {token.get('expires_at', 'نامحدود')[:16] if token.get('expires_at') else 'نامحدود'}\n"
                text += f"📊 **کوتای فعلی:** {token.get('usage_quota', 'نامحدود')}\n\n"
                
                text += "لطفاً بخش مورد نظر برای ویرایش را انتخاب کنید:"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📝 ویرایش نام", callback_data=f"edit_name_{token_id}"),
                        InlineKeyboardButton("⏰ ویرایش انقضا", callback_data=f"edit_expiry_{token_id}")
                    ],
                    [
                        InlineKeyboardButton("🏷 تغییر نوع", callback_data=f"edit_type_{token_id}"),
                        InlineKeyboardButton("📊 تنظیم کوتا", callback_data=f"edit_quota_{token_id}")
                    ],
                    [
                        InlineKeyboardButton("💾 اعمال تغییرات", callback_data=f"save_changes_{token_id}"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data=f"token_details_{token_id}")
                    ]
                ])
                
            else:
                text = f"❌ **خطا در دریافت اطلاعات توکن**\n\nعلت: {result.get('error', 'نامشخص')}"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="list_all_tokens")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_edit_token: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_edit_token_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ویرایش نام توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            token_id = query.data.split('_')[2]
            
            text = "📝 **ویرایش نام توکن**\n\n"
            text += f"🆔 **شناسه توکن:** `{token_id}`\n\n"
            text += "لطفاً نام جدید توکن را انتخاب کنید یا نام سفارشی وارد نمایید:\n\n"
            text += "💡 **نکات:**\n"
            text += "• نام باید بین 3 تا 50 کاراکتر باشد\n"
            text += "• از کاراکترهای فارسی، انگلیسی و اعداد استفاده کنید\n"
            text += "• نام توکن در لیست‌ها نمایش داده می‌شود"
            
            # ذخیره token_id در context برای استفاده در مرحله بعد
            context.user_data[f'editing_token_{update.effective_user.id}'] = {
                'token_id': token_id,
                'field': 'name',
                'awaiting_input': True
            }
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🏢 توکن اداری", callback_data=f"set_name_{token_id}_admin_token"),
                    InlineKeyboardButton("🔧 توکن API", callback_data=f"set_name_{token_id}_api_token")
                ],
                [
                    InlineKeyboardButton("👤 توکن کاربری", callback_data=f"set_name_{token_id}_user_token"),
                    InlineKeyboardButton("🛡 توکن امنیتی", callback_data=f"set_name_{token_id}_security_token")
                ],
                [
                    InlineKeyboardButton("✏️ نام سفارشی", callback_data=f"custom_name_{token_id}"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data=f"edit_token_{token_id}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_edit_token_name: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_edit_token_expiry(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ویرایش انقضای توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            token_id = query.data.split('_')[2]
            
            text = "⏰ **ویرایش انقضای توکن**\n\n"
            text += f"🆔 **شناسه توکن:** `{token_id}`\n\n"
            text += "لطفاً زمان انقضای جدید را انتخاب کنید:\n\n"
            text += "⚠️ **نکات مهم:**\n"
            text += "• تغییر انقضا فوری اعمال می‌شود\n"
            text += "• کاهش زمان انقضا ممکن است توکن را غیرفعال کند\n"
            text += "• انتخاب \"نامحدود\" توکن را بدون انقضا می‌کند"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("1 روز", callback_data=f"set_expiry_{token_id}_1"),
                    InlineKeyboardButton("7 روز", callback_data=f"set_expiry_{token_id}_7"),
                    InlineKeyboardButton("30 روز", callback_data=f"set_expiry_{token_id}_30")
                ],
                [
                    InlineKeyboardButton("90 روز", callback_data=f"set_expiry_{token_id}_90"),
                    InlineKeyboardButton("365 روز", callback_data=f"set_expiry_{token_id}_365"),
                    InlineKeyboardButton("♾ نامحدود", callback_data=f"set_expiry_{token_id}_0")
                ],
                [
                    InlineKeyboardButton("📅 تاریخ سفارشی", callback_data=f"custom_expiry_{token_id}"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data=f"edit_token_{token_id}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_edit_token_expiry: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_edit_token_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تغییر نوع توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            token_id = query.data.split('_')[2]
            
            # دریافت نوع فعلی توکن
            result = await self.token_manager.get_token_details(token_id)
            current_type = result.get('token', {}).get('type', 'user') if result.get('success') else 'user'
            
            text = "🏷 **تغییر نوع توکن**\n\n"
            text += f"🆔 **شناسه توکن:** `{token_id}`\n"
            text += f"🔹 **نوع فعلی:** {self._get_token_type_name(current_type)}\n\n"
            text += "لطفاً نوع جدید توکن را انتخاب کنید:\n\n"
            text += "⚠️ **هشدارهای مهم:**\n"
            text += "• تغییر نوع توکن دسترسی‌ها را تغییر می‌دهد\n"
            text += "• کاهش سطح دسترسی فوری اعمال می‌شود\n"
            text += "• این عمل برگشت‌پذیر است"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        f"🛡 مدیر {'✅' if current_type == 'admin' else ''}",
                        callback_data=f"set_type_{token_id}_admin"
                    ),
                    InlineKeyboardButton(
                        f"⚙️ محدود {'✅' if current_type == 'limited' else ''}",
                        callback_data=f"set_type_{token_id}_limited"
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"👤 کاربر {'✅' if current_type == 'user' else ''}",
                        callback_data=f"set_type_{token_id}_user"
                    ),
                    InlineKeyboardButton(
                        f"🔧 API {'✅' if current_type == 'api' else ''}",
                        callback_data=f"set_type_{token_id}_api"
                    )
                ],
                [
                    InlineKeyboardButton("ℹ️ مقایسه دسترسی‌ها", callback_data=f"compare_types_{token_id}"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data=f"edit_token_{token_id}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_edit_token_type: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_edit_token_quota(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیم کوتای توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            token_id = query.data.split('_')[2]
            
            # دریافت کوتای فعلی
            result = await self.token_manager.get_token_details(token_id)
            current_quota = result.get('token', {}).get('usage_quota', 0) if result.get('success') else 0
            quota_text = f"{current_quota:,}" if current_quota > 0 else "نامحدود"
            
            text = "📊 **تنظیم کوتای استفاده توکن**\n\n"
            text += f"🆔 **شناسه توکن:** `{token_id}`\n"
            text += f"📈 **کوتای فعلی:** {quota_text}\n\n"
            text += "لطفاً کوتای جدید (حد مجاز استفاده روزانه) را انتخاب کنید:\n\n"
            text += "💡 **توضیحات:**\n"
            text += "• کوتا بر اساس تعداد درخواست در 24 ساعت محاسبه می‌شود\n"
            text += "• رسیدن به کوتا باعث قطع دسترسی موقت می‌شود\n"
            text += "• کوتا هر روز به صورت خودکار بازنشانی می‌شود"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("100 درخواست", callback_data=f"set_quota_{token_id}_100"),
                    InlineKeyboardButton("500 درخواست", callback_data=f"set_quota_{token_id}_500")
                ],
                [
                    InlineKeyboardButton("1K درخواست", callback_data=f"set_quota_{token_id}_1000"),
                    InlineKeyboardButton("5K درخواست", callback_data=f"set_quota_{token_id}_5000")
                ],
                [
                    InlineKeyboardButton("10K درخواست", callback_data=f"set_quota_{token_id}_10000"),
                    InlineKeyboardButton("50K درخواست", callback_data=f"set_quota_{token_id}_50000")
                ],
                [
                    InlineKeyboardButton("♾ نامحدود", callback_data=f"set_quota_{token_id}_0"),
                    InlineKeyboardButton("🎯 کوتای سفارشی", callback_data=f"custom_quota_{token_id}")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data=f"edit_token_{token_id}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_edit_token_quota: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_save_token_changes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """اعمال و ذخیره تغییرات توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            token_id = query.data.split('_')[2]
            
            # بررسی وجود تغییرات در انتظار
            user_data = context.user_data.get(f'token_changes_{token_id}', {})
            
            if not user_data:
                text = "ℹ️ **هیچ تغییری در انتظار اعمال نیست**\n\n"
                text += "برای ویرایش توکن، ابتدا یکی از گزینه‌های ویرایش را انتخاب کنید."
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("✏️ ویرایش توکن", callback_data=f"edit_token_{token_id}"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data=f"token_details_{token_id}")
                ]])
            else:
                # اعمال تغییرات از طریق API
                result = await self.token_manager.update_token_settings(token_id, user_data)
                
                if result.get('success'):
                    text = "✅ **تغییرات با موفقیت اعمال شد**\n\n"
                    text += f"🆔 **شناسه توکن:** `{token_id}`\n\n"
                    text += "📝 **تغییرات اعمال شده:**\n"
                    
                    for field, value in user_data.items():
                        if field == 'name':
                            text += f"• نام: {value}\n"
                        elif field == 'expires_at':
                            text += f"• انقضا: {value if value else 'نامحدود'}\n"
                        elif field == 'type':
                            text += f"• نوع: {self._get_token_type_name(value)}\n"
                        elif field == 'usage_quota':
                            text += f"• کوتا: {f'{value:,}' if value > 0 else 'نامحدود'}\n"
                    
                    text += f"\n📅 **زمان اعمال:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    
                    # پاک کردن تغییرات موقت
                    if f'token_changes_{token_id}' in context.user_data:
                        del context.user_data[f'token_changes_{token_id}']
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("📊 مشاهده جزئیات", callback_data=f"token_details_{token_id}"),
                            InlineKeyboardButton("✏️ ویرایش مجدد", callback_data=f"edit_token_{token_id}")
                        ],
                        [
                            InlineKeyboardButton("📋 لیست توکن‌ها", callback_data="list_all_tokens")
                        ]
                    ])
                else:
                    text = "❌ **خطا در اعمال تغییرات**\n\n"
                    text += f"علت: {result.get('error', 'نامشخص')}\n\n"
                    text += "لطفاً دوباره تلاش کنید یا با مدیر سیستم تماس بگیرید."
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("🔄 تلاش مجدد", callback_data=f"save_changes_{token_id}"),
                            InlineKeyboardButton("✏️ ویرایش مجدد", callback_data=f"edit_token_{token_id}")
                        ],
                        [
                            InlineKeyboardButton("🔙 بازگشت", callback_data=f"token_details_{token_id}")
                        ]
                    ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_save_token_changes: {e}")
            await self.handle_error(update, context, e)
    
    # === TOKEN DEACTIVATION ===
    
    async def handle_deactivate_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """غیرفعال‌سازی توکن با تأیید"""
        try:
            query = update.callback_query
            await query.answer()
            
            token_id = query.data.split('_')[2]
            
            # دریافت اطلاعات توکن برای نمایش
            result = await self.token_manager.get_token_details(token_id)
            
            if result.get('success'):
                token = result.get('token', {})
                
                text = "🔒 **غیرفعال‌سازی توکن**\n\n"
                text += f"🆔 **شناسه:** `{token_id}`\n"
                text += f"📝 **نام:** {token.get('name', 'بدون نام')}\n"
                text += f"🏷 **نوع:** {self._get_token_type_name(token.get('type', 'user'))}\n"
                text += f"📊 **تعداد استفاده:** {token.get('usage_count', 0)}\n\n"
                
                text += "⚠️ **هشدار:**\n"
                text += "• این توکن قابل استفاده نخواهد بود\n"
                text += "• تمام درخواست‌های آن رد می‌شود\n"
                text += "• امکان فعال‌سازی مجدد وجود دارد\n"
                text += "• آمار و تاریخچه حفظ می‌شود\n\n"
                text += "آیا از غیرفعال‌سازی این توکن اطمینان دارید؟"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ بله، غیرفعال کن", callback_data=f"confirm_deactivate_{token_id}"),
                        InlineKeyboardButton("❌ خیر، انصراف", callback_data=f"token_details_{token_id}")
                    ]
                ])
            else:
                text = f"❌ **خطا در دریافت اطلاعات توکن**\n\nعلت: {result.get('error', 'نامشخص')}"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="list_all_tokens")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_deactivate_token: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_confirm_deactivate_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأیید نهایی غیرفعال‌سازی توکن"""
        try:
            query = update.callback_query
            await query.answer("در حال غیرفعال‌سازی توکن...")
            
            token_id = query.data.split('_')[2]
            
            # غیرفعال‌سازی توکن از طریق API
            result = await self.token_manager.deactivate_token(token_id)
            
            if result.get('success'):
                text = "✅ **توکن غیرفعال شد**\n\n"
                text += f"🆔 **شناسه توکن:** `{token_id}`\n"
                text += f"📅 **زمان غیرفعال‌سازی:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                text += "این توکن دیگر قابل استفاده نیست.\n"
                text += "در صورت نیاز می‌توانید آن را مجدداً فعال کنید."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 فعال‌سازی مجدد", callback_data=f"reactivate_token_{token_id}"),
                        InlineKeyboardButton("📊 مشاهده جزئیات", callback_data=f"token_details_{token_id}")
                    ],
                    [
                        InlineKeyboardButton("📋 لیست توکن‌ها", callback_data="list_all_tokens"),
                        InlineKeyboardButton("➕ توکن جدید", callback_data="create_new_token")
                    ]
                ])
            else:
                text = "❌ **خطا در غیرفعال‌سازی توکن**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}\n\n"
                text += "لطفاً دوباره تلاش کنید."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 تلاش مجدد", callback_data=f"deactivate_token_{token_id}"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data=f"token_details_{token_id}")
                    ]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_confirm_deactivate_token: {e}")
            await self.handle_error(update, context, e)
    
    # === TOKEN STATISTICS ===
    
    async def handle_token_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش آمار کامل توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            token_id = query.data.split('_')[2]
            
            # دریافت آمار کامل توکن
            result = await self.token_manager.get_token_statistics_detailed(token_id)
            
            if result.get('success'):
                stats = result.get('data', {})
                token_info = stats.get('token_info', {})
                usage_stats = stats.get('usage_stats', {})
                
                text = "📊 **آمار کامل توکن**\n\n"
                text += f"🆔 **شناسه:** `{token_id}`\n"
                text += f"📝 **نام:** {token_info.get('name', 'بدون نام')}\n"
                text += f"🏷 **نوع:** {self._get_token_type_name(token_info.get('type', 'user'))}\n\n"
                
                text += "📈 **آمار استفاده:**\n"
                text += f"• کل استفاده‌ها: {usage_stats.get('total_requests', 0):,}\n"
                text += f"• استفاده امروز: {usage_stats.get('today_requests', 0):,}\n"
                text += f"• استفاده این هفته: {usage_stats.get('week_requests', 0):,}\n"
                text += f"• استفاده این ماه: {usage_stats.get('month_requests', 0):,}\n\n"
                
                text += "🕐 **آمار زمانی:**\n"
                text += f"• آخرین استفاده: {usage_stats.get('last_used_at', 'هرگز')[:16] if usage_stats.get('last_used_at') else 'هرگز'}\n"
                text += f"• میانگین استفاده روزانه: {usage_stats.get('daily_average', 0):.1f}\n"
                text += f"• روزهای فعالیت: {usage_stats.get('active_days', 0)}\n\n"
                
                text += "🌐 **آمار شبکه:**\n"
                text += f"• IP های مختلف: {usage_stats.get('unique_ips', 0)}\n"
                text += f"• کشورهای مختلف: {usage_stats.get('unique_countries', 0)}\n"
                text += f"• پربازدیدترین IP: {usage_stats.get('top_ip', 'نامشخص')}\n\n"
                
                if usage_stats.get('quota_limit', 0) > 0:
                    quota_used = usage_stats.get('quota_used', 0)
                    quota_limit = usage_stats.get('quota_limit', 0)
                    quota_percent = (quota_used / quota_limit) * 100 if quota_limit > 0 else 0
                    text += "📊 **وضعیت کوتا:**\n"
                    text += f"• استفاده شده: {quota_used:,} از {quota_limit:,} ({quota_percent:.1f}%)\n"
                    text += f"• باقی‌مانده: {quota_limit - quota_used:,}\n\n"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📋 لاگ دسترسی", callback_data=f"token_access_log_{token_id}"),
                        InlineKeyboardButton("⚠️ تحلیل ناهنجاری", callback_data=f"token_anomaly_{token_id}")
                    ],
                    [
                        InlineKeyboardButton("📊 نمودار استفاده", callback_data=f"token_usage_chart_{token_id}"),
                        InlineKeyboardButton("📈 تحلیل ترند", callback_data=f"token_trend_analysis_{token_id}")
                    ],
                    [
                        InlineKeyboardButton("📄 صادرات گزارش", callback_data=f"export_token_report_{token_id}_pdf"),
                        InlineKeyboardButton("🔄 بروزرسانی", callback_data=f"token_stats_{token_id}")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data=f"token_details_{token_id}")
                    ]
                ])
            else:
                text = f"❌ **خطا در دریافت آمار توکن**\n\nعلت: {result.get('error', 'نامشخص')}"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data=f"token_details_{token_id}")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_token_stats: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_token_access_log(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش لاگ دسترسی‌های توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            token_id = query.data.split('_')[3]  # token_access_log_{id}
            
            # دریافت لاگ دسترسی‌ها
            result = await self.token_manager.get_token_access_log(token_id, limit=10)
            
            if result.get('success'):
                logs = result.get('data', [])
                
                text = "📋 **لاگ دسترسی‌های توکن**\n\n"
                text += f"🆔 **شناسه توکن:** `{token_id}`\n\n"
                
                if logs:
                    text += f"🕐 **آخرین {len(logs)} دسترسی:**\n\n"
                    for i, log in enumerate(logs, 1):
                        status_icon = "✅" if log.get('success', True) else "❌"
                        text += f"{i}. {status_icon} **{log.get('timestamp', '')[:16]}**\n"
                        text += f"   🌐 IP: {log.get('ip_address', 'نامشخص')}\n"
                        text += f"   🔗 عملیات: {log.get('operation', 'نامشخص')}\n"
                        text += f"   📊 پاسخ: {log.get('response_code', 'N/A')}\n"
                        if log.get('user_agent'):
                            text += f"   🖥 UA: {log.get('user_agent', '')[:30]}...\n"
                        text += "\n"
                else:
                    text += "ℹ️ **هیچ لاگ دسترسی یافت نشد**\n\n"
                    text += "این توکن هنوز استفاده نشده است."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📄 لاگ کامل", callback_data=f"full_access_log_{token_id}"),
                        InlineKeyboardButton("📊 تحلیل دسترسی", callback_data=f"analyze_access_{token_id}")
                    ],
                    [
                        InlineKeyboardButton("📤 صادرات لاگ", callback_data=f"export_access_log_{token_id}"),
                        InlineKeyboardButton("🔄 بروزرسانی", callback_data=f"token_access_log_{token_id}")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data=f"token_stats_{token_id}")
                    ]
                ])
            else:
                text = f"❌ **خطا در دریافت لاگ دسترسی**\n\nعلت: {result.get('error', 'نامشخص')}"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data=f"token_stats_{token_id}")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_token_access_log: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_token_anomaly(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تحلیل ناهنجاری‌های توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            token_id = query.data.split('_')[2]
            
            # دریافت تحلیل ناهنجاری
            result = await self.token_manager.get_token_anomaly_analysis(token_id)
            
            if result.get('success'):
                analysis = result.get('data', {})
                anomalies = analysis.get('anomalies', [])
                score = analysis.get('risk_score', 0)
                
                text = "⚠️ **تحلیل ناهنجاری توکن**\n\n"
                text += f"🆔 **شناسه توکن:** `{token_id}`\n"
                text += f"📊 **امتیاز ریسک:** {score}/100\n\n"
                
                # تعیین سطح ریسک
                if score >= 80:
                    risk_level = "🔴 بالا"
                elif score >= 50:
                    risk_level = "🟠 متوسط"
                elif score >= 20:
                    risk_level = "🟡 پایین"
                else:
                    risk_level = "🟢 عادی"
                
                text += f"🎯 **سطح ریسک:** {risk_level}\n\n"
                
                if anomalies:
                    text += "🚨 **ناهنجاری‌های شناسایی شده:**\n\n"
                    for i, anomaly in enumerate(anomalies, 1):
                        severity_icon = {"high": "🔴", "medium": "🟠", "low": "🟡"}.get(anomaly.get('severity', 'low'), "🟡")
                        text += f"{i}. {severity_icon} **{anomaly.get('type', 'نامشخص')}**\n"
                        text += f"   📝 توضیح: {anomaly.get('description', 'توضیح موجود نیست')}\n"
                        text += f"   📅 زمان شناسایی: {anomaly.get('detected_at', '')[:16]}\n"
                        text += f"   💡 توصیه: {anomaly.get('recommendation', 'بررسی دقیق‌تر')}\n\n"
                else:
                    text += "✅ **هیچ ناهنجاری مشکوکی شناسایی نشد**\n\n"
                    text += "این توکن در حالت عادی و امن قرار دارد."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🛡 اقدامات امنیتی", callback_data=f"security_actions_{token_id}"),
                        InlineKeyboardButton("📊 تحلیل عمیق", callback_data=f"deep_analysis_{token_id}")
                    ],
                    [
                        InlineKeyboardButton("🔒 قرنطینه توکن", callback_data=f"quarantine_token_{token_id}") if score >= 80 else None,
                        InlineKeyboardButton("⚠️ اخطار به مدیر", callback_data=f"alert_admin_{token_id}") if score >= 50 else None
                    ],
                    [
                        InlineKeyboardButton("📄 گزارش کامل", callback_data=f"full_anomaly_report_{token_id}"),
                        InlineKeyboardButton("🔄 بروزرسانی", callback_data=f"token_anomaly_{token_id}")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data=f"token_stats_{token_id}")
                    ]
                ])
                
                # حذف دکمه‌های None
                keyboard.inline_keyboard = [
                    [btn for btn in row if btn is not None] 
                    for row in keyboard.inline_keyboard
                ]
                keyboard.inline_keyboard = [row for row in keyboard.inline_keyboard if row]
                
            else:
                text = f"❌ **خطا در تحلیل ناهنجاری**\n\nعلت: {result.get('error', 'نامشخص')}"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data=f"token_stats_{token_id}")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_token_anomaly: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_export_token_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """صادرات گزارش توکن"""
        try:
            query = update.callback_query
            await query.answer("در حال تهیه گزارش...")
            
            # استخراج token_id و format از callback_data
            parts = query.data.split('_')
            token_id = parts[3]  # export_token_report_{id}_{format}
            report_format = parts[4] if len(parts) > 4 else 'pdf'
            
            # تولید گزارش از طریق API
            result = await self.token_manager.generate_token_report(token_id, report_format)
            
            if result.get('success'):
                text = "✅ **گزارش توکن تولید شد**\n\n"
                text += f"🆔 **شناسه توکن:** `{token_id}`\n"
                text += f"📄 **فرمت گزارش:** {report_format.upper()}\n"
                text += f"📅 **تاریخ تولید:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                
                report_info = result.get('data', {})
                text += "📊 **مشخصات گزارش:**\n"
                text += f"• حجم فایل: {report_info.get('file_size', 'نامشخص')}\n"
                text += f"• تعداد صفحات: {report_info.get('pages', 'نامشخص')}\n"
                text += f"• شامل: {report_info.get('includes', 'آمار کامل')}\n\n"
                
                if report_info.get('download_url'):
                    text += f"🔗 **لینک دانلود:** [کلیک کنید]({report_info.get('download_url')})\n\n"
                    text += "⏰ **نکته:** لینک دانلود تا 24 ساعت معتبر است."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📧 ارسال ایمیل", callback_data=f"email_report_{token_id}_{report_format}"),
                        InlineKeyboardButton("💬 ارسال در چت", callback_data=f"send_report_{token_id}_{report_format}")
                    ],
                    [
                        InlineKeyboardButton("📄 فرمت دیگر", callback_data=f"choose_report_format_{token_id}"),
                        InlineKeyboardButton("🔄 تولید مجدد", callback_data=f"export_token_report_{token_id}_{report_format}")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data=f"token_stats_{token_id}")
                    ]
                ])
            else:
                text = "❌ **خطا در تولید گزارش**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}\n\n"
                text += "لطفاً دوباره تلاش کنید یا فرمت دیگری انتخاب نمایید."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 تلاش مجدد", callback_data=f"export_token_report_{token_id}_{report_format}"),
                        InlineKeyboardButton("📄 فرمت دیگر", callback_data=f"choose_report_format_{token_id}")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data=f"token_stats_{token_id}")
                    ]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_export_token_report: {e}")
            await self.handle_error(update, context, e)
    
    # === TOKEN SET OPERATIONS ===
    
    async def handle_set_token_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیم نام جدید برای توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            # استخراج اطلاعات از callback_data: set_name_{token_id}_{name_type}
            parts = query.data.split('_')
            token_id = parts[2]
            name_type = parts[3] if len(parts) > 3 else "custom"
            
            # نام‌های از پیش تعریف شده
            predefined_names = {
                'admin': 'توکن اداری',
                'api': 'توکن API',
                'user': 'توکن کاربری',
                'security': 'توکن امنیتی'
            }
            
            new_name = predefined_names.get(name_type, f"توکن جدید {token_id}")
            
            # ذخیره تغییرات در context برای اعمال بعدی
            if f'token_changes_{token_id}' not in context.user_data:
                context.user_data[f'token_changes_{token_id}'] = {}
            
            context.user_data[f'token_changes_{token_id}']['name'] = new_name
            
            text = "✅ **نام جدید تنظیم شد**\n\n"
            text += f"🆔 **شناسه توکن:** `{token_id}`\n"
            text += f"📝 **نام جدید:** {new_name}\n\n"
            text += "⚠️ **توجه:** برای اعمال تغییرات روی دکمه \"💾 اعمال تغییرات\" کلیک کنید."
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("💾 اعمال تغییرات", callback_data=f"save_changes_{token_id}"),
                    InlineKeyboardButton("✏️ ویرایش بیشتر", callback_data=f"edit_token_{token_id}")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data=f"token_details_{token_id}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_set_token_name: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_set_token_expiry(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیم انقضای جدید برای توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            # استخراج اطلاعات از callback_data: set_expiry_{token_id}_{days}
            parts = query.data.split('_')
            token_id = parts[2]
            days = int(parts[3])
            
            # محاسبه تاریخ انقضای جدید
            from datetime import datetime, timedelta
            
            if days > 0:
                new_expiry = datetime.now() + timedelta(days=days)
                expiry_text = new_expiry.strftime('%Y-%m-%d %H:%M')
                expiry_persian = f"{days} روز از الان"
            else:
                new_expiry = None
                expiry_text = None
                expiry_persian = "نامحدود"
            
            # ذخیره تغییرات در context
            if f'token_changes_{token_id}' not in context.user_data:
                context.user_data[f'token_changes_{token_id}'] = {}
            
            context.user_data[f'token_changes_{token_id}']['expires_at'] = expiry_text
            
            text = "⏰ **انقضای جدید تنظیم شد**\n\n"
            text += f"🆔 **شناسه توکن:** `{token_id}`\n"
            text += f"📅 **انقضای جدید:** {expiry_persian}\n"
            if expiry_text:
                text += f"🕐 **تاریخ دقیق:** {expiry_text}\n"
            text += "\n⚠️ **توجه:** برای اعمال تغییرات روی دکمه \"💾 اعمال تغییرات\" کلیک کنید."
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("💾 اعمال تغییرات", callback_data=f"save_changes_{token_id}"),
                    InlineKeyboardButton("✏️ ویرایش بیشتر", callback_data=f"edit_token_{token_id}")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data=f"token_details_{token_id}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_set_token_expiry: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_set_token_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیم نوع جدید برای توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            # استخراج اطلاعات از callback_data: set_type_{token_id}_{type}
            parts = query.data.split('_')
            token_id = parts[2]
            new_type = parts[3]
            
            # ذخیره تغییرات در context
            if f'token_changes_{token_id}' not in context.user_data:
                context.user_data[f'token_changes_{token_id}'] = {}
            
            context.user_data[f'token_changes_{token_id}']['type'] = new_type
            
            text = "🏷 **نوع جدید تنظیم شد**\n\n"
            text += f"🆔 **شناسه توکن:** `{token_id}`\n"
            text += f"🔹 **نوع جدید:** {self._get_token_type_name(new_type)}\n\n"
            
            text += "📊 **دسترسی‌های جدید:**\n"
            permissions = self._get_token_permissions(new_type)
            for perm in permissions:
                text += f"• {perm}\n"
            
            text += "\n⚠️ **توجه:** برای اعمال تغییرات روی دکمه \"💾 اعمال تغییرات\" کلیک کنید."
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("💾 اعمال تغییرات", callback_data=f"save_changes_{token_id}"),
                    InlineKeyboardButton("✏️ ویرایش بیشتر", callback_data=f"edit_token_{token_id}")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data=f"token_details_{token_id}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_set_token_type: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_set_token_quota(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیم کوتای جدید برای توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            # استخراج اطلاعات از callback_data: set_quota_{token_id}_{amount}
            parts = query.data.split('_')
            token_id = parts[2]
            quota_amount = int(parts[3])
            
            # ذخیره تغییرات در context
            if f'token_changes_{token_id}' not in context.user_data:
                context.user_data[f'token_changes_{token_id}'] = {}
            
            context.user_data[f'token_changes_{token_id}']['usage_quota'] = quota_amount
            
            quota_text = f"{quota_amount:,} درخواست در روز" if quota_amount > 0 else "نامحدود"
            
            text = "📊 **کوتای جدید تنظیم شد**\n\n"
            text += f"🆔 **شناسه توکن:** `{token_id}`\n"
            text += f"📈 **کوتای جدید:** {quota_text}\n\n"
            
            if quota_amount > 0:
                text += "💡 **توضیحات:**\n"
                text += f"• حداکثر {quota_amount:,} درخواست در هر 24 ساعت\n"
                text += "• پس از رسیدن به کوتا، توکن موقتاً غیرفعال می‌شود\n"
                text += "• کوتا هر روز در ساعت 00:00 بازنشانی می‌شود\n"
            else:
                text += "♾ **بدون محدودیت** - توکن می‌تواند نامحدود استفاده شود"
            
            text += "\n⚠️ **توجه:** برای اعمال تغییرات روی دکمه \"💾 اعمال تغییرات\" کلیک کنید."
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("💾 اعمال تغییرات", callback_data=f"save_changes_{token_id}"),
                    InlineKeyboardButton("✏️ ویرایش بیشتر", callback_data=f"edit_token_{token_id}")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data=f"token_details_{token_id}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_set_token_quota: {e}")
            await self.handle_error(update, context, e)
    
    # === TOKEN OPERATIONS - EXTENDED ===
    
    async def handle_compare_token_types(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مقایسه انواع دسترسی‌های توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            token_id = query.data.split('_')[2]
            
            text = "ℹ️ **مقایسه انواع توکن‌ها**\n\n"
            text += f"🆔 **برای توکن:** `{token_id}`\n\n"
            
            # مقایسه انواع مختلف
            types_info = {
                'admin': {
                    'name': '🛡 مدیر',
                    'level': 'بالاترین سطح دسترسی',
                    'features': [
                        'مدیریت تمام توکن‌ها',
                        'مشاهده آمار کامل',
                        'تنظیمات سیستم',
                        'مدیریت کاربران',
                        'دسترسی به لاگ‌ها'
                    ]
                },
                'limited': {
                    'name': '⚙️ محدود',
                    'level': 'سطح متوسط دسترسی', 
                    'features': [
                        'مدیریت لینک‌های شخصی',
                        'مشاهده آمار محدود',
                        'ایجاد و حذف لینک‌ها',
                        'تنظیمات حساب شخصی'
                    ]
                },
                'user': {
                    'name': '👤 کاربر',
                    'level': 'سطح پایه دسترسی',
                    'features': [
                        'ایجاد لینک دانلود',
                        'مشاهده آمار شخصی',
                        'استفاده محدود روزانه'
                    ]
                },
                'api': {
                    'name': '🔧 API',
                    'level': 'دسترسی برنامه‌نویسی',
                    'features': [
                        'فراخوانی API ها',
                        'ایجاد لینک از طریق کد',
                        'دسترسی محدود به endpoint ها'
                    ]
                }
            }
            
            for type_key, info in types_info.items():
                text += f"{info['name']}\n"
                text += f"📋 {info['level']}\n"
                text += "🔹 ویژگی‌ها:\n"
                for feature in info['features']:
                    text += f"  • {feature}\n"
                text += "\n"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🛡 انتخاب مدیر", callback_data=f"set_type_{token_id}_admin"),
                    InlineKeyboardButton("⚙️ انتخاب محدود", callback_data=f"set_type_{token_id}_limited")
                ],
                [
                    InlineKeyboardButton("👤 انتخاب کاربر", callback_data=f"set_type_{token_id}_user"),
                    InlineKeyboardButton("🔧 انتخاب API", callback_data=f"set_type_{token_id}_api")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data=f"edit_type_{token_id}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_compare_token_types: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_custom_token_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """وارد کردن نام سفارشی توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            token_id = query.data.split('_')[2]
            
            text = "✏️ **نام سفارشی توکن**\n\n"
            text += f"🆔 **شناسه توکن:** `{token_id}`\n\n"
            text += "لطفاً نام جدید توکن را در پیام بعدی ارسال کنید:\n\n"
            text += "📋 **شرایط نام:**\n"
            text += "• حداقل 3 کاراکتر، حداکثر 50 کاراکتر\n"
            text += "• استفاده از حروف فارسی، انگلیسی و اعداد\n"
            text += "• بدون استفاده از کاراکترهای خاص\n\n"
            text += "💡 **مثال:** `توکن مدیریت API`، `Marketing Token`"
            
            # تنظیم حالت انتظار ورودی
            context.user_data[f'awaiting_custom_name_{token_id}'] = True
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("❌ انصراف", callback_data=f"edit_name_{token_id}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_custom_token_name: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_custom_token_expiry(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیم انقضای سفارشی توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            token_id = query.data.split('_')[2]
            
            text = "📅 **تاریخ انقضای سفارشی**\n\n"
            text += f"🆔 **شناسه توکن:** `{token_id}`\n\n"
            text += "لطفاً تاریخ انقضا را در یکی از فرمت‌های زیر ارسال کنید:\n\n"
            text += "📅 **فرمت‌های مجاز:**\n"
            text += "• `YYYY-MM-DD` (مثال: 2024-12-31)\n"
            text += "• `YYYY-MM-DD HH:MM` (مثال: 2024-12-31 23:59)\n"
            text += "• `+N days` (مثال: +45 days)\n"
            text += "• `never` برای نامحدود\n\n"
            text += "💡 **نکته:** تاریخ باید در آینده باشد"
            
            # تنظیم حالت انتظار ورودی
            context.user_data[f'awaiting_custom_expiry_{token_id}'] = True
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("❌ انصراف", callback_data=f"edit_expiry_{token_id}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_custom_token_expiry: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_custom_token_quota(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیم کوتای سفارشی توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            token_id = query.data.split('_')[2]
            
            text = "📊 **کوتای سفارشی**\n\n"
            text += f"🆔 **شناسه توکن:** `{token_id}`\n\n"
            text += "لطفاً تعداد درخواست مجاز در روز را ارسال کنید:\n\n"
            text += "🔢 **فرمت‌های مجاز:**\n"
            text += "• عدد صحیح (مثال: 2500)\n"
            text += "• عدد با واحد K (مثال: 2.5K = 2500)\n"
            text += "• عدد با واحد M (مثال: 1.5M = 1500000)\n"
            text += "• `unlimited` برای نامحدود\n\n"
            text += "💡 **محدودیت:** حداقل 1، حداکثر 10,000,000 در روز"
            
            # تنظیم حالت انتظار ورودی
            context.user_data[f'awaiting_custom_quota_{token_id}'] = True
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("❌ انصراف", callback_data=f"edit_quota_{token_id}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_custom_token_quota: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_reactivate_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """فعال‌سازی مجدد توکن"""
        try:
            query = update.callback_query
            await query.answer("در حال فعال‌سازی مجدد توکن...")
            
            token_id = query.data.split('_')[2]
            
            # فعال‌سازی مجدد توکن از طریق API
            result = await self.token_manager.reactivate_token(token_id)
            
            if result.get('success'):
                text = "✅ **توکن مجدداً فعال شد**\n\n"
                text += f"🆔 **شناسه توکن:** `{token_id}`\n"
                text += f"📅 **زمان فعال‌سازی:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                text += "این توکن اکنون دوباره قابل استفاده است."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📊 مشاهده جزئیات", callback_data=f"token_details_{token_id}"),
                        InlineKeyboardButton("✏️ ویرایش توکن", callback_data=f"edit_token_{token_id}")
                    ],
                    [
                        InlineKeyboardButton("📋 لیست توکن‌ها", callback_data="list_all_tokens")
                    ]
                ])
            else:
                text = "❌ **خطا در فعال‌سازی مجدد توکن**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}\n\n"
                text += "لطفاً دوباره تلاش کنید."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 تلاش مجدد", callback_data=f"reactivate_token_{token_id}"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data=f"token_details_{token_id}")
                    ]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_reactivate_token: {e}")
            await self.handle_error(update, context, e)
    
    # === BULK DEACTIVATE OPERATIONS ===
    
    async def handle_select_from_list_deactivate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتخاب دستی توکن‌ها برای غیرفعال‌سازی"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت لیست تمام توکن‌های فعال
            result = await self.token_manager.get_active_tokens_list()
            
            if result.get('success'):
                tokens = result.get('data', [])
                
                if not tokens:
                    text = "ℹ️ **هیچ توکن فعالی یافت نشد**\n\n"
                    text += "در حال حاضر توکن فعالی برای غیرفعال‌سازی وجود ندارد."
                    
                    keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_actions")
                    ]])
                else:
                    text = "📋 **انتخاب توکن‌ها برای غیرفعال‌سازی**\n\n"
                    text += f"تعداد کل توکن‌های فعال: {len(tokens)}\n\n"
                    text += "روی توکن‌هایی که می‌خواهید غیرفعال کنید کلیک کنید:\n\n"
                    
                    # نمایش لیست توکن‌ها با checkbox
                    selected_tokens = context.user_data.get('bulk_deactivate_selected', [])
                    
                    keyboard_rows = []
                    for i, token in enumerate(tokens[:20]):  # حداکثر 20 توکن در هر صفحه
                        token_id = token.get('id')
                        token_name = token.get('name', f'توکن {token_id}')
                        is_selected = token_id in selected_tokens
                        
                        checkbox = "☑️" if is_selected else "☐"
                        keyboard_rows.append([
                            InlineKeyboardButton(
                                f"{checkbox} {token_name} ({token_id})",
                                callback_data=f"toggle_deactivate_{token_id}"
                            )
                        ])
                    
                    # دکمه‌های کنترل
                    control_row = []
                    if selected_tokens:
                        control_row.extend([
                            InlineKeyboardButton(f"✅ غیرفعال‌سازی ({len(selected_tokens)})", callback_data="confirm_bulk_deactivate"),
                            InlineKeyboardButton("❌ پاک کردن انتخاب‌ها", callback_data="clear_deactivate_selection")
                        ])
                    
                    keyboard_rows.extend([
                        control_row,
                        [
                            InlineKeyboardButton("🔄 انتخاب همه", callback_data="select_all_deactivate"),
                            InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_deactivate_tokens")
                        ]
                    ])
                    
                    keyboard = InlineKeyboardMarkup([row for row in keyboard_rows if row])
            else:
                text = f"❌ **خطا در دریافت توکن‌ها**\n\nعلت: {result.get('error', 'نامشخص')}"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_deactivate_tokens")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_select_from_list_deactivate: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_toggle_deactivate_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تغییر وضعیت انتخاب توکن برای غیرفعال‌سازی"""
        try:
            query = update.callback_query
            await query.answer()
            
            token_id = query.data.replace('toggle_deactivate_', '')
            
            # مدیریت لیست انتخاب شده
            if 'bulk_deactivate_selected' not in context.user_data:
                context.user_data['bulk_deactivate_selected'] = []
            
            selected = context.user_data['bulk_deactivate_selected']
            if token_id in selected:
                selected.remove(token_id)
            else:
                selected.append(token_id)
            
            # بازنمایی صفحه با وضعیت جدید
            await self.handle_select_from_list_deactivate(update, context)
            
        except Exception as e:
            logger.error(f"Error in handle_toggle_deactivate_token: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_confirm_bulk_deactivate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأیید غیرفعال‌سازی دسته‌ای"""
        try:
            query = update.callback_query
            await query.answer()
            
            selected_tokens = context.user_data.get('bulk_deactivate_selected', [])
            
            if not selected_tokens:
                text = "⚠️ **هیچ توکنی انتخاب نشده**\n\nلطفاً ابتدا توکن‌هایی را برای غیرفعال‌سازی انتخاب کنید."
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="select_from_list_deactivate")
                ]])
            else:
                text = "🔒 **تأیید غیرفعال‌سازی دسته‌ای**\n\n"
                text += f"تعداد توکن‌های انتخاب شده: {len(selected_tokens)}\n\n"
                text += "⚠️ **هشدار:**\n"
                text += "• تمام توکن‌های انتخاب شده غیرفعال خواهند شد\n"
                text += "• درخواست‌های آن‌ها رد خواهد شد\n"
                text += "• امکان فعال‌سازی مجدد وجود دارد\n\n"
                text += f"آیا از غیرفعال‌سازی {len(selected_tokens)} توکن اطمینان دارید؟"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ بله، غیرفعال کن", callback_data="execute_bulk_deactivate"),
                        InlineKeyboardButton("❌ خیر، انصراف", callback_data="select_from_list_deactivate")
                    ]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_confirm_bulk_deactivate: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_execute_bulk_deactivate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """اجرای عملیات غیرفعال‌سازی دسته‌ای"""
        try:
            query = update.callback_query
            await query.answer("در حال غیرفعال‌سازی توکن‌ها...")
            
            selected_tokens = context.user_data.get('bulk_deactivate_selected', [])
            
            if not selected_tokens:
                text = "⚠️ **خطا: هیچ توکنی انتخاب نشده**"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_actions")
                ]])
            else:
                # اجرای غیرفعال‌سازی دسته‌ای
                result = await self.token_manager.bulk_deactivate_tokens(selected_tokens)
                
                if result.get('success'):
                    successful_count = result.get('successful_count', 0)
                    failed_count = result.get('failed_count', 0)
                    failed_tokens = result.get('failed_tokens', [])
                    
                    text = "✅ **غیرفعال‌سازی دسته‌ای تکمیل شد**\n\n"
                    text += "📊 **نتایج:**\n"
                    text += f"• موفق: {successful_count} توکن\n"
                    text += f"• ناموفق: {failed_count} توکن\n"
                    text += f"• زمان اجرا: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    
                    if failed_tokens:
                        text += "❌ **توکن‌های ناموفق:**\n"
                        for token_id, error in failed_tokens.items():
                            text += f"• {token_id}: {error}\n"
                    
                    # پاک کردن انتخاب‌ها
                    if 'bulk_deactivate_selected' in context.user_data:
                        del context.user_data['bulk_deactivate_selected']
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("📋 مشاهده توکن‌ها", callback_data="list_all_tokens"),
                            InlineKeyboardButton("🔄 غیرفعال‌سازی بیشتر", callback_data="bulk_deactivate_tokens")
                        ],
                        [
                            InlineKeyboardButton("📊 آمار کلی", callback_data="token_dashboard"),
                            InlineKeyboardButton("🔙 منوی اصلی", callback_data="bulk_actions")
                        ]
                    ])
                else:
                    text = "❌ **خطا در غیرفعال‌سازی دسته‌ای**\n\n"
                    text += f"علت: {result.get('error', 'نامشخص')}\n\n"
                    text += "لطفاً دوباره تلاش کنید یا تک تک توکن‌ها را غیرفعال کنید."
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("🔄 تلاش مجدد", callback_data="execute_bulk_deactivate"),
                            InlineKeyboardButton("🔙 بازگشت", callback_data="select_from_list_deactivate")
                        ]
                    ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_execute_bulk_deactivate: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_select_all_deactivate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتخاب همه توکن‌ها برای غیرفعال‌سازی"""
        try:
            query = update.callback_query
            await query.answer("در حال انتخاب همه توکن‌ها...")
            
            # دریافت لیست تمام توکن‌های فعال
            result = await self.token_manager.get_active_tokens_list()
            
            if result.get('success'):
                tokens = result.get('data', [])
                token_ids = [token.get('id') for token in tokens]
                
                # انتخاب همه توکن‌ها
                context.user_data['bulk_deactivate_selected'] = token_ids
                
                # بازنمایی صفحه با وضعیت جدید
                await self.handle_select_from_list_deactivate(update, context)
            else:
                text = f"❌ **خطا در دریافت توکن‌ها**\n\nعلت: {result.get('error', 'نامشخص')}"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_deactivate_tokens")
                ]])
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_select_all_deactivate: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_clear_deactivate_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پاک کردن تمام انتخاب‌ها"""
        try:
            query = update.callback_query
            await query.answer("انتخاب‌ها پاک شد")
            
            # پاک کردن لیست انتخاب شده
            if 'bulk_deactivate_selected' in context.user_data:
                context.user_data['bulk_deactivate_selected'] = []
            
            # بازنمایی صفحه با وضعیت جدید
            await self.handle_select_from_list_deactivate(update, context)
            
        except Exception as e:
            logger.error(f"Error in handle_clear_deactivate_selection: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_criteria_based_deactivate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """غیرفعال‌سازی بر اساس معیار"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🎯 **غیرفعال‌سازی بر اساس معیار**\n\n"
            text += "معیار مورد نظر برای انتخاب خودکار توکن‌ها را انتخاب کنید:\n\n"
            text += "💡 **انواع معیارها:**\n"
            text += "• **منقضی شده:** توکن‌هایی که انقضا گذشته‌اند\n"
            text += "• **غیرفعال طولانی:** توکن‌هایی که 30+ روز استفاده نشده‌اند\n"
            text += "• **استفاده کم:** توکن‌هایی با کمتر از 10 استفاده\n"
            text += "• **تکراری:** توکن‌های یک کاربر که بیش از 5 توکن دارد"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📅 منقضی شده", callback_data="criteria_deactivate_expired"),
                    InlineKeyboardButton("💤 غیرفعال طولانی", callback_data="criteria_deactivate_inactive")
                ],
                [
                    InlineKeyboardButton("📉 استفاده کم", callback_data="criteria_deactivate_lowusage"),
                    InlineKeyboardButton("👥 تکراری", callback_data="criteria_deactivate_duplicate")
                ],
                [
                    InlineKeyboardButton("🔧 معیار سفارشی", callback_data="criteria_deactivate_custom"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_deactivate_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_criteria_based_deactivate: {e}")
            await self.handle_error(update, context, e)
    
    # === BULK EXTEND OPERATIONS ===
    
    async def handle_bulk_extend_7d(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تمدید دسته‌ای 7 روزه"""
        try:
            query = update.callback_query
            await query.answer()
            
            # نمایش مرحله انتخاب توکن‌ها برای تمدید
            result = await self.token_manager.get_extendable_tokens()
            
            if result.get('success'):
                tokens = result.get('data', [])
                
                text = "⏰ **تمدید دسته‌ای 7 روزه**\n\n"
                text += f"تعداد توکن‌های قابل تمدید: {len(tokens)}\n\n"
                text += "روش انتخاب توکن‌ها را انتخاب کنید:\n\n"
                text += "💡 **گزینه‌ها:**\n"
                text += "• **انتخاب دستی:** خودتان توکن‌ها را انتخاب کنید\n"
                text += "• **همه:** تمام توکن‌های قابل تمدید\n"
                text += "• **منقضی شدنی:** توکن‌هایی که تا 3 روز دیگر منقضی می‌شوند"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📋 انتخاب دستی", callback_data="select_tokens_extend_7d"),
                        InlineKeyboardButton("🔄 همه توکن‌ها", callback_data="extend_all_7d")
                    ],
                    [
                        InlineKeyboardButton("⚠️ منقضی شدنی", callback_data="extend_expiring_7d"),
                        InlineKeyboardButton("🎯 بر اساس نوع", callback_data="extend_by_type_7d")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_extend_tokens")
                    ]
                ])
            else:
                text = f"❌ **خطا در دریافت توکن‌ها**\n\nعلت: {result.get('error', 'نامشخص')}"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_extend_tokens")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_bulk_extend_7d: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_select_tokens_extend(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتخاب دستی توکن‌ها برای تمدید"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت تعداد روز از callback data
            callback_data = query.data
            days = int(callback_data.split('_')[-1].replace('d', ''))
            
            # ذخیره تعداد روز در context
            context.user_data['extend_days'] = days
            
            # دریافت لیست توکن‌های قابل تمدید
            result = await self.token_manager.get_extendable_tokens()
            
            if result.get('success'):
                tokens = result.get('data', [])
                
                if not tokens:
                    text = "ℹ️ **هیچ توکن قابل تمدیدی یافت نشد**"
                    keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_extend_tokens")
                    ]])
                else:
                    text = f"📋 **انتخاب توکن‌ها برای تمدید {days} روزه**\n\n"
                    text += f"تعداد کل توکن‌های قابل تمدید: {len(tokens)}\n\n"
                    text += "روی توکن‌هایی که می‌خواهید تمدید کنید کلیک کنید:\n\n"
                    
                    # نمایش لیست توکن‌ها با checkbox
                    selected_tokens = context.user_data.get('bulk_extend_selected', [])
                    
                    keyboard_rows = []
                    for i, token in enumerate(tokens[:20]):
                        token_id = token.get('id')
                        token_name = token.get('name', f'توکن {token_id}')
                        is_selected = token_id in selected_tokens
                        
                        checkbox = "☑️" if is_selected else "☐"
                        keyboard_rows.append([
                            InlineKeyboardButton(
                                f"{checkbox} {token_name} ({token_id[:8]})",
                                callback_data=f"toggle_extend_{token_id}"
                            )
                        ])
                    
                    # دکمه‌های کنترل
                    control_row = []
                    if selected_tokens:
                        control_row.extend([
                            InlineKeyboardButton(f"✅ تمدید ({len(selected_tokens)})", callback_data="confirm_bulk_extend"),
                            InlineKeyboardButton("❌ پاک کردن", callback_data="clear_extend_selection")
                        ])
                    
                    keyboard_rows.extend([
                        control_row,
                        [
                            InlineKeyboardButton("🔄 انتخاب همه", callback_data="select_all_extend"),
                            InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_extend_tokens")
                        ]
                    ])
                    
                    keyboard = InlineKeyboardMarkup([row for row in keyboard_rows if row])
            else:
                text = f"❌ **خطا در دریافت توکن‌ها**\n\nعلت: {result.get('error', 'نامشخص')}"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_extend_tokens")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_select_tokens_extend: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_toggle_extend_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تغییر وضعیت انتخاب توکن برای تمدید"""
        try:
            query = update.callback_query
            await query.answer()
            
            token_id = query.data.replace('toggle_extend_', '')
            
            # مدیریت لیست انتخاب شده
            if 'bulk_extend_selected' not in context.user_data:
                context.user_data['bulk_extend_selected'] = []
            
            selected = context.user_data['bulk_extend_selected']
            if token_id in selected:
                selected.remove(token_id)
            else:
                selected.append(token_id)
            
            # بازنمایی صفحه با وضعیت جدید
            await self.handle_select_tokens_extend(update, context)
            
        except Exception as e:
            logger.error(f"Error in handle_toggle_extend_token: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_confirm_bulk_extend(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأیید تمدید دسته‌ای"""
        try:
            query = update.callback_query
            await query.answer()
            
            selected_tokens = context.user_data.get('bulk_extend_selected', [])
            extend_days = context.user_data.get('extend_days', 7)
            
            if not selected_tokens:
                text = "⚠️ **هیچ توکنی انتخاب نشده**"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_extend_tokens")
                ]])
            else:
                text = "⏰ **تأیید تمدید دسته‌ای**\n\n"
                text += f"تعداد توکن‌های انتخاب شده: {len(selected_tokens)}\n"
                text += f"مدت تمدید: {extend_days} روز\n\n"
                text += f"آیا از تمدید {len(selected_tokens)} توکن اطمینان دارید؟"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ بله، تمدید کن", callback_data="execute_bulk_extend"),
                        InlineKeyboardButton("❌ خیر، انصراف", callback_data="bulk_extend_tokens")
                    ]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_confirm_bulk_extend: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_execute_bulk_extend(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """اجرای عملیات تمدید دسته‌ای"""
        try:
            query = update.callback_query
            await query.answer("در حال تمدید توکن‌ها...")
            
            selected_tokens = context.user_data.get('bulk_extend_selected', [])
            extend_days = context.user_data.get('extend_days', 7)
            
            if not selected_tokens:
                text = "⚠️ **خطا: هیچ توکنی انتخاب نشده**"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_extend_tokens")
                ]])
            else:
                # اجرای تمدید دسته‌ای
                result = await self.token_manager.bulk_extend_expiry(selected_tokens, extend_days)
                
                if result.get('success'):
                    successful_count = result.get('successful_count', 0)
                    failed_count = result.get('failed_count', 0)
                    
                    text = "✅ **تمدید دسته‌ای تکمیل شد**\n\n"
                    text += "📊 **نتایج:**\n"
                    text += f"• موفق: {successful_count} توکن\n"
                    text += f"• ناموفق: {failed_count} توکن\n"
                    text += f"• مدت تمدید: {extend_days} روز\n"
                    
                    # پاک کردن انتخاب‌ها
                    if 'bulk_extend_selected' in context.user_data:
                        del context.user_data['bulk_extend_selected']
                    if 'extend_days' in context.user_data:
                        del context.user_data['extend_days']
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("📋 مشاهده توکن‌ها", callback_data="list_all_tokens"),
                            InlineKeyboardButton("🔄 تمدید بیشتر", callback_data="bulk_extend_tokens")
                        ],
                        [
                            InlineKeyboardButton("🔙 منوی اصلی", callback_data="bulk_actions")
                        ]
                    ])
                else:
                    text = f"❌ **خطا در تمدید دسته‌ای**\n\nعلت: {result.get('error', 'نامشخص')}"
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("🔄 تلاش مجدد", callback_data="execute_bulk_extend"),
                            InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_extend_tokens")
                        ]
                    ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_execute_bulk_extend: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_select_all_extend(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتخاب همه توکن‌ها برای تمدید"""
        try:
            query = update.callback_query
            await query.answer("در حال انتخاب همه توکن‌ها...")
            
            # دریافت لیست تمام توکن‌های قابل تمدید
            result = await self.token_manager.get_extendable_tokens()
            
            if result.get('success'):
                tokens = result.get('data', [])
                token_ids = [token.get('id') for token in tokens]
                
                # انتخاب همه توکن‌ها
                context.user_data['bulk_extend_selected'] = token_ids
                
                # بازنمایی صفحه با وضعیت جدید
                await self.handle_select_tokens_extend(update, context)
            else:
                text = f"❌ **خطا در دریافت توکن‌ها**\n\nعلت: {result.get('error', 'نامشخص')}"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_extend_tokens")
                ]])
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_select_all_extend: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_clear_extend_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پاک کردن تمام انتخاب‌های تمدید"""
        try:
            query = update.callback_query
            await query.answer("انتخاب‌ها پاک شد")
            
            # پاک کردن لیست انتخاب شده
            if 'bulk_extend_selected' in context.user_data:
                context.user_data['bulk_extend_selected'] = []
            
            # بازنمایی صفحه با وضعیت جدید
            await self.handle_select_tokens_extend(update, context)
            
        except Exception as e:
            logger.error(f"Error in handle_clear_extend_selection: {e}")
            await self.handle_error(update, context, e)
    
    # === EXTEND HANDLERS FOR DIFFERENT DURATIONS ===
    
    async def handle_bulk_extend_30d(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تمدید دسته‌ای 30 روزه"""
        try:
            query = update.callback_query
            await query.answer()
            
            context.user_data['extend_days'] = 30
            await self._show_extend_selection_menu(update, context, 30)
            
        except Exception as e:
            logger.error(f"Error in handle_bulk_extend_30d: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_bulk_extend_90d(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تمدید دسته‌ای 90 روزه"""
        try:
            query = update.callback_query
            await query.answer()
            
            context.user_data['extend_days'] = 90
            await self._show_extend_selection_menu(update, context, 90)
            
        except Exception as e:
            logger.error(f"Error in handle_bulk_extend_90d: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_bulk_extend_365d(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تمدید دسته‌ای 365 روزه"""
        try:
            query = update.callback_query
            await query.answer()
            
            context.user_data['extend_days'] = 365
            await self._show_extend_selection_menu(update, context, 365)
            
        except Exception as e:
            logger.error(f"Error in handle_bulk_extend_365d: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_bulk_extend_unlimited(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تمدید دسته‌ای نامحدود"""
        try:
            query = update.callback_query
            await query.answer()
            
            context.user_data['extend_days'] = 0  # 0 = unlimited
            await self._show_extend_selection_menu(update, context, 0)
            
        except Exception as e:
            logger.error(f"Error in handle_bulk_extend_unlimited: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_bulk_extend_custom(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تمدید دسته‌ای با مدت سفارشی"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🎯 **تمدید سفارشی**\n\n"
            text += "لطفاً تعداد روزهای دلخواه برای تمدید را وارد کنید:\n\n"
            text += "💡 **نکات:**\n"
            text += "• عدد باید بین 1 تا 3650 باشد (10 سال)\n"
            text += "• برای نامحدود، عدد 0 را وارد کنید\n"
            text += "• فقط عدد وارد کنید (بدون کلمه یا علامت)\n\n"
            text += "📝 **مثال:** برای تمدید 45 روزه، عدد `45` را بنویسید"
            
            # Set flag for awaiting custom days input
            context.user_data['awaiting_custom_extend_days'] = True
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("❌ انصراف", callback_data="bulk_extend_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_bulk_extend_custom: {e}")
            await self.handle_error(update, context, e)
    
    async def _show_extend_selection_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, days: int):
        """نمایش منوی انتخاب توکن‌ها برای تمدید"""
        try:
            query = update.callback_query
            
            result = await self.token_manager.get_extendable_tokens()
            
            if result.get('success'):
                tokens = result.get('data', [])
                
                days_text = "نامحدود" if days == 0 else f"{days} روز"
                
                text = f"⏰ **تمدید دسته‌ای {days_text}**\n\n"
                text += f"تعداد توکن‌های قابل تمدید: {len(tokens)}\n\n"
                text += "روش انتخاب توکن‌ها را انتخاب کنید:\n\n"
                text += "💡 **گزینه‌ها:**\n"
                text += "• **انتخاب دستی:** خودتان توکن‌ها را انتخاب کنید\n"
                text += "• **همه:** تمام توکن‌های قابل تمدید\n"
                text += "• **منقضی شدنی:** توکن‌هایی که تا 7 روز دیگر منقضی می‌شوند"
                
                callback_suffix = f"_{days}d" if days > 0 else "_unlimited"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📋 انتخاب دستی", callback_data=f"select_tokens_extend{callback_suffix}"),
                        InlineKeyboardButton("🔄 همه توکن‌ها", callback_data=f"extend_all{callback_suffix}")
                    ],
                    [
                        InlineKeyboardButton("⚠️ منقضی شدنی", callback_data=f"extend_expiring{callback_suffix}"),
                        InlineKeyboardButton("🎯 بر اساس نوع", callback_data=f"extend_by_type{callback_suffix}")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_extend_tokens")
                    ]
                ])
            else:
                text = f"❌ **خطا در دریافت توکن‌ها**\n\nعلت: {result.get('error', 'نامشخص')}"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_extend_tokens")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in _show_extend_selection_menu: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_custom_extend_days_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش ورودی تعداد روزهای سفارشی"""
        try:
            if not context.user_data.get('awaiting_custom_extend_days'):
                return False
            
            user_input = update.message.text.strip()
            
            # Validate input
            try:
                days = int(user_input)
                if days < 0 or days > 3650:
                    await update.message.reply_text(
                        "❌ **عدد نامعتبر!**\n\n"
                        "لطفاً عددی بین 0 تا 3650 وارد کنید.\n"
                        "0 = نامحدود، 1-3650 = تعداد روز",
                        parse_mode='Markdown'
                    )
                    return True
                
                # Valid input
                context.user_data['extend_days'] = days
                context.user_data['awaiting_custom_extend_days'] = False
                
                # Show selection menu
                days_text = "نامحدود" if days == 0 else f"{days} روز"
                
                result = await self.token_manager.get_extendable_tokens()
                
                if result.get('success'):
                    tokens = result.get('data', [])
                    
                    text = f"⏰ **تمدید سفارشی {days_text}**\n\n"
                    text += f"تعداد توکن‌های قابل تمدید: {len(tokens)}\n\n"
                    text += "روش انتخاب توکن‌ها را انتخاب کنید:"
                    
                    callback_suffix = f"_{days}d" if days > 0 else "_unlimited"
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("📋 انتخاب دستی", callback_data=f"select_tokens_extend{callback_suffix}"),
                            InlineKeyboardButton("🔄 همه توکن‌ها", callback_data=f"extend_all{callback_suffix}")
                        ],
                        [
                            InlineKeyboardButton("⚠️ منقضی شدنی", callback_data=f"extend_expiring{callback_suffix}"),
                            InlineKeyboardButton("🎯 بر اساس نوع", callback_data=f"extend_by_type{callback_suffix}")
                        ],
                        [
                            InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_extend_tokens")
                        ]
                    ])
                    
                    await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')
                else:
                    await update.message.reply_text(
                        f"❌ **خطا در دریافت توکن‌ها**\n\nعلت: {result.get('error', 'نامشخص')}",
                        parse_mode='Markdown'
                    )
                
                return True
                
            except ValueError:
                await update.message.reply_text(
                    "❌ **ورودی نامعتبر!**\n\n"
                    "لطفاً فقط عدد وارد کنید (مثال: 45)",
                    parse_mode='Markdown'
                )
                return True
            
        except Exception as e:
            logger.error(f"Error in handle_custom_extend_days_input: {e}")
            await update.message.reply_text("❌ خطایی رخ داد! لطفاً دوباره تلاش کنید.")
            return True
    
    # === BULK EXPORT OPERATIONS ===
    
    async def handle_bulk_export(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """منوی صادرات دسته‌ای"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "📤 **صادرات دسته‌ای توکن‌ها**\n\n"
            text += "فرمت مورد نظر برای صادرات را انتخاب کنید:\n\n"
            text += "📋 **فرمت‌های موجود:**\n"
            text += "• **JSON:** مناسب برای استفاده برنامه‌نویسی\n"
            text += "• **CSV:** مناسب برای Excel و تحلیل داده\n"
            text += "• **PDF:** مناسب برای ارائه و چاپ\n"
            text += "• **Excel:** مناسب برای گزارش‌گیری پیشرفته\n\n"
            text += "⚙️ **قابلیت‌ها:**\n"
            text += "• انتخاب ستون‌های مورد نظر\n"
            text += "• فیلتر بر اساس معیار\n"
            text += "• آمار و نمودار (PDF/Excel)\n"
            text += "• رمزگذاری فایل (اختیاری)"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📄 JSON", callback_data="export_format_json"),
                    InlineKeyboardButton("📊 CSV", callback_data="export_format_csv")
                ],
                [
                    InlineKeyboardButton("📋 PDF", callback_data="export_format_pdf"),
                    InlineKeyboardButton("📈 Excel", callback_data="export_format_excel")
                ],
                [
                    InlineKeyboardButton("⚙️ تنظیمات پیشرفته", callback_data="export_advanced_settings"),
                    InlineKeyboardButton("📅 زمان‌بندی صادرات", callback_data="schedule_export")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_actions")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_bulk_export: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_export_format_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتخاب فرمت صادرات"""
        try:
            query = update.callback_query
            await query.answer()
            
            # Extract format from callback_data
            format_type = query.data.replace('export_format_', '')
            context.user_data['export_format'] = format_type
            
            # Show token selection menu
            result = await self.token_manager.get_active_tokens_list()
            
            if result.get('success'):
                tokens = result.get('data', [])
                
                format_names = {
                    'json': 'JSON',
                    'csv': 'CSV',
                    'pdf': 'PDF',
                    'excel': 'Excel'
                }
                
                text = f"📤 **صادرات {format_names.get(format_type, format_type.upper())}**\n\n"
                text += f"تعداد کل توکن‌ها: {len(tokens)}\n\n"
                text += "روش انتخاب توکن‌ها را مشخص کنید:\n\n"
                text += "💡 **گزینه‌ها:**\n"
                text += "• **انتخاب دستی:** خودتان توکن‌ها را انتخاب کنید\n"
                text += "• **همه توکن‌ها:** صادرات تمام توکن‌ها\n"
                text += "• **بر اساس نوع:** فیلتر بر اساس نوع توکن\n"
                text += "• **بر اساس وضعیت:** فعال/غیرفعال/منقضی"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📋 انتخاب دستی", callback_data=f"export_select_manual_{format_type}"),
                        InlineKeyboardButton("🔄 همه توکن‌ها", callback_data=f"export_all_{format_type}")
                    ],
                    [
                        InlineKeyboardButton("🏷 بر اساس نوع", callback_data=f"export_by_type_{format_type}"),
                        InlineKeyboardButton("📊 بر اساس وضعیت", callback_data=f"export_by_status_{format_type}")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_export")
                    ]
                ])
            else:
                text = f"❌ **خطا در دریافت توکن‌ها**\n\nعلت: {result.get('error', 'نامشخص')}"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_export")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_export_format_selection: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_export_all_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """صادرات همه توکن‌ها"""
        try:
            query = update.callback_query
            await query.answer("در حال آماده‌سازی فایل...")
            
            # Extract format from callback_data
            format_type = query.data.split('_')[-1]
            
            # Get all tokens
            result = await self.token_manager.get_all_tokens()
            
            if result.get('success'):
                tokens = result.get('data', [])
                token_ids = [token.get('id') for token in tokens]
                
                # Request export
                export_result = await self.token_manager.bulk_export_tokens(
                    token_ids=token_ids,
                    format_type=format_type,
                    include_stats=True
                )
                
                if export_result.get('success'):
                    text = "✅ **صادرات موفق**\n\n"
                    text += "📊 **جزئیات:**\n"
                    text += f"• تعداد توکن‌ها: {len(token_ids)}\n"
                    text += f"• فرمت: {format_type.upper()}\n"
                    text += f"• حجم فایل: {export_result.get('file_size', 'نامشخص')}\n"
                    text += f"• تاریخ انقضا: {export_result.get('expires_at', '24 ساعت')}\n\n"
                    text += f"🔗 **لینک دانلود:**\n{export_result.get('download_url', 'در حال تولید...')}\n\n"
                    text += "⚠️ لینک دانلود پس از 24 ساعت منقضی می‌شود."
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("📤 صادرات جدید", callback_data="bulk_export"),
                            InlineKeyboardButton("📋 لیست توکن‌ها", callback_data="list_all_tokens")
                        ],
                        [
                            InlineKeyboardButton("🔙 منوی اصلی", callback_data="bulk_actions")
                        ]
                    ])
                else:
                    text = f"❌ **خطا در صادرات**\n\nعلت: {export_result.get('error', 'نامشخص')}"
                    keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔄 تلاش مجدد", callback_data=f"export_all_{format_type}"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_export")
                    ]])
            else:
                text = f"❌ **خطا در دریافت توکن‌ها**\n\nعلت: {result.get('error', 'نامشخص')}"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_export")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_export_all_tokens: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_export_manual_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتخاب دستی توکن‌ها برای صادرات"""
        try:
            query = update.callback_query
            await query.answer()
            
            # Extract format from callback_data
            format_type = query.data.split('_')[-1]
            context.user_data['export_format'] = format_type
            
            # Get all tokens
            result = await self.token_manager.get_all_tokens()
            
            if result.get('success'):
                tokens = result.get('data', [])
                
                if not tokens:
                    text = "ℹ️ **هیچ توکنی یافت نشد**"
                    keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_export")
                    ]])
                else:
                    text = "📋 **انتخاب توکن‌ها برای صادرات**\n\n"
                    text += f"تعداد کل توکن‌ها: {len(tokens)}\n"
                    text += f"فرمت: {format_type.upper()}\n\n"
                    text += "روی توکن‌هایی که می‌خواهید صادر کنید کلیک کنید:\n\n"
                    
                    # Show checkbox list
                    selected_tokens = context.user_data.get('bulk_export_selected', [])
                    
                    keyboard_rows = []
                    for i, token in enumerate(tokens[:20]):  # Show first 20
                        token_id = token.get('id')
                        token_name = token.get('name', f'توکن {token_id[:8]}')
                        is_selected = token_id in selected_tokens
                        
                        checkbox = "☑️" if is_selected else "☐"
                        keyboard_rows.append([
                            InlineKeyboardButton(
                                f"{checkbox} {token_name}",
                                callback_data=f"toggle_export_{token_id}"
                            )
                        ])
                    
                    # Control buttons
                    control_row = []
                    if selected_tokens:
                        control_row.extend([
                            InlineKeyboardButton(f"✅ صادرات ({len(selected_tokens)})", callback_data="confirm_export"),
                            InlineKeyboardButton("❌ پاک کردن", callback_data="clear_export_selection")
                        ])
                    
                    keyboard_rows.extend([
                        control_row,
                        [
                            InlineKeyboardButton("🔄 انتخاب همه", callback_data="select_all_export"),
                            InlineKeyboardButton("🔙 بازگشت", callback_data=f"export_format_{format_type}")
                        ]
                    ])
                    
                    keyboard = InlineKeyboardMarkup([row for row in keyboard_rows if row])
            else:
                text = f"❌ **خطا در دریافت توکن‌ها**\n\nعلت: {result.get('error', 'نامشخص')}"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_export")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_export_manual_selection: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_toggle_export_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تغییر وضعیت انتخاب توکن برای صادرات"""
        try:
            query = update.callback_query
            await query.answer()
            
            token_id = query.data.replace('toggle_export_', '')
            
            # Manage selection list
            if 'bulk_export_selected' not in context.user_data:
                context.user_data['bulk_export_selected'] = []
            
            selected = context.user_data['bulk_export_selected']
            if token_id in selected:
                selected.remove(token_id)
            else:
                selected.append(token_id)
            
            # Refresh page
            format_type = context.user_data.get('export_format', 'json')
            query.data = f"export_select_manual_{format_type}"
            await self.handle_export_manual_selection(update, context)
            
        except Exception as e:
            logger.error(f"Error in handle_toggle_export_token: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_select_all_export(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتخاب همه توکن‌ها برای صادرات"""
        try:
            query = update.callback_query
            await query.answer("در حال انتخاب همه توکن‌ها...")
            
            result = await self.token_manager.get_all_tokens()
            
            if result.get('success'):
                tokens = result.get('data', [])
                token_ids = [token.get('id') for token in tokens]
                
                context.user_data['bulk_export_selected'] = token_ids
                
                # Refresh page
                format_type = context.user_data.get('export_format', 'json')
                query.data = f"export_select_manual_{format_type}"
                await self.handle_export_manual_selection(update, context)
            else:
                text = f"❌ **خطا در دریافت توکن‌ها**\n\nعلت: {result.get('error', 'نامشخص')}"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_export")
                ]])
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_select_all_export: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_clear_export_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پاک کردن انتخاب‌های صادرات"""
        try:
            query = update.callback_query
            await query.answer("انتخاب‌ها پاک شد")
            
            if 'bulk_export_selected' in context.user_data:
                context.user_data['bulk_export_selected'] = []
            
            # Refresh page
            format_type = context.user_data.get('export_format', 'json')
            query.data = f"export_select_manual_{format_type}"
            await self.handle_export_manual_selection(update, context)
            
        except Exception as e:
            logger.error(f"Error in handle_clear_export_selection: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_confirm_export(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأیید و اجرای صادرات"""
        try:
            query = update.callback_query
            await query.answer("در حال آماده‌سازی فایل...")
            
            selected_tokens = context.user_data.get('bulk_export_selected', [])
            format_type = context.user_data.get('export_format', 'json')
            
            if not selected_tokens:
                text = "⚠️ **هیچ توکنی انتخاب نشده**"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_export")
                ]])
            else:
                # Request export
                export_result = await self.token_manager.bulk_export_tokens(
                    token_ids=selected_tokens,
                    format_type=format_type,
                    include_stats=True
                )
                
                if export_result.get('success'):
                    text = "✅ **صادرات موفق**\n\n"
                    text += "📊 **جزئیات:**\n"
                    text += f"• تعداد توکن‌ها: {len(selected_tokens)}\n"
                    text += f"• فرمت: {format_type.upper()}\n"
                    text += f"• حجم فایل: {export_result.get('file_size', 'نامشخص')}\n"
                    text += f"• تاریخ انقضا: {export_result.get('expires_at', '24 ساعت')}\n\n"
                    text += f"🔗 **لینک دانلود:**\n{export_result.get('download_url', 'در حال تولید...')}\n\n"
                    text += "⚠️ لینک دانلود پس از 24 ساعت منقضی می‌شود."
                    
                    # Clear selections
                    if 'bulk_export_selected' in context.user_data:
                        del context.user_data['bulk_export_selected']
                    if 'export_format' in context.user_data:
                        del context.user_data['export_format']
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("📤 صادرات جدید", callback_data="bulk_export"),
                            InlineKeyboardButton("📋 لیست توکن‌ها", callback_data="list_all_tokens")
                        ],
                        [
                            InlineKeyboardButton("🔙 منوی اصلی", callback_data="bulk_actions")
                        ]
                    ])
                else:
                    text = f"❌ **خطا در صادرات**\n\nعلت: {export_result.get('error', 'نامشخص')}"
                    keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔄 تلاش مجدد", callback_data="confirm_export"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_export")
                    ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_confirm_export: {e}")
            await self.handle_error(update, context, e)

    # === HELPER METHOD UPDATE ===
    
    async def handle_confirm_new_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأیید نهایی توکن جدید - تکمیل شده"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "✅ **تأیید توکن جدید**\n\n"
            text += "این بخش برای تأیید مراحل نهایی تولید توکن استفاده می‌شود."
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
            ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_confirm_new_token: {e}")
            await self.handle_error(update, context, e)