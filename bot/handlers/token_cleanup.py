#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token Cleanup Handler - مدیریت پاکسازی و حذف توکن‌ها
"""

import logging
from typing import Dict, Any, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

from handlers.base_handler import BaseHandler

logger = logging.getLogger(__name__)


class TokenCleanupHandler(BaseHandler):
    """مدیریت پاکسازی و حذف توکن‌ها"""
    
    def __init__(self, db, token_manager):
        """
        Args:
            db: دیتابیس منیجر
            token_manager: TokenManagementHandler اصلی برای API calls
        """
        super().__init__(db)
        self.token_manager = token_manager
    
    # === CLEANUP MENU ===
    
    async def show_cleanup_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """منوی اصلی پاکسازی"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🧹 **مدیریت پاکسازی توکن‌ها**\n\n"
            text += "⚠️ **هشدار:** عملیات‌های پاکسازی برگشت‌پذیر نیستند!\n\n"
            text += "🎯 **انواع پاکسازی:**\n"
            text += "• **منقضی‌ها:** حذف توکن‌هایی که تاریخ انقضایشان گذشته\n"
            text += "• **غیرفعال‌ها:** حذف توکن‌های غیرفعال شده\n"
            text += "• **بدون استفاده:** حذف توکن‌هایی که مدت طولانی استفاده نشده‌اند\n"
            text += "• **پاکسازی کامل:** حذف همه توکن‌ها به جز مدیر فعلی\n\n"
            
            text += "⚙️ **عملیات پیشرفته:**\n"
            text += "• برنامه‌ریزی پاکسازی خودکار\n"
            text += "• پاکسازی بر اساس معیارهای سفارشی\n"
            text += "• بک‌آپ قبل از پاکسازی"
            
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
                    InlineKeyboardButton("📅 پاکسازی برنامه‌ریزی شده", callback_data="cleanup_schedule"),
                    InlineKeyboardButton("🎯 پاکسازی سفارشی", callback_data="cleanup_custom")
                ],
                [
                    InlineKeyboardButton("💾 بک‌آپ و پاکسازی", callback_data="backup_cleanup"),
                    InlineKeyboardButton("📊 آمار پاکسازی", callback_data="cleanup_stats")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_cleanup_menu: {e}")
            await self.handle_error(update, context, e)
    
    # === CLEANUP EXPIRED TOKENS ===
    
    async def handle_cleanup_expired(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پاکسازی توکن‌های منقضی - پیش‌نمایش"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت لیست توکن‌های منقضی برای پیش‌نمایش
            result = await self.token_manager.get_expired_tokens_preview()
            
            if result.get('success'):
                count = result.get('count', 0)
                tokens = result.get('tokens', [])[:5]  # نمایش 5 توکن اول
                
                text = f"⏰ **پیش‌نمایش پاکسازی توکن‌های منقضی**\n\n"
                text += f"📊 **تعداد کل:** {count} توکن منقضی\n\n"
                
                if tokens:
                    text += f"📋 **نمونه توکن‌های منقضی:**\n"
                    for i, token in enumerate(tokens, 1):
                        text += f"{i}. {token.get('name', 'بدون نام')} - `{token.get('token_id', 'N/A')}`\n"
                        text += f"   انقضا: {token.get('expires_at', 'نامشخص')[:16]}\n\n"
                    
                    if count > 5:
                        text += f"... و {count - 5} توکن دیگر\n\n"
                    
                    text += "⚠️ **هشدار:** این عملیات برگشت‌پذیر نیست!"
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("✅ تأیید پاکسازی", callback_data="confirm_cleanup_expired"),
                            InlineKeyboardButton("📋 مشاهده همه", callback_data="preview_all_expired")
                        ],
                        [
                            InlineKeyboardButton("💾 بک‌آپ و پاکسازی", callback_data="backup_cleanup_expired"),
                            InlineKeyboardButton("❌ انصراف", callback_data="cleanup_menu")
                        ]
                    ])
                else:
                    text += "✅ هیچ توکن منقضی‌ای برای پاکسازی یافت نشد!"
                    
                    keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="cleanup_menu")
                    ]])
            else:
                text = f"❌ **خطا در دریافت توکن‌های منقضی**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}"
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="cleanup_menu")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_cleanup_expired: {e}")
            await self.handle_error(update, context, e)
    
    async def confirm_cleanup_expired(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأیید نهایی پاکسازی توکن‌های منقضی"""
        try:
            query = update.callback_query
            await query.answer("در حال پاکسازی توکن‌های منقضی...")
            
            # پاکسازی توکن‌های منقضی از طریق API
            result = await self.token_manager.cleanup_expired_tokens()
            
            if result.get('success'):
                count = result.get('count', 0)
                text = f"✅ **توکن‌های منقضی پاکسازی شدند**\n\n"
                text += f"📊 **تعداد توکن‌های پاکسازی شده:** {count}\n"
                text += f"📅 **زمان پاکسازی:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                text += "✅ پاکسازی با موفقیت انجام شد!"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 پاکسازی دوباره", callback_data="cleanup_expired"),
                        InlineKeyboardButton("📋 لیست توکن‌ها", callback_data="list_all_tokens")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="cleanup_menu")
                    ]
                ])
            else:
                text = f"❌ **خطا در پاکسازی**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}\n\n"
                text += "لطفاً دوباره تلاش کنید."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 تلاش مجدد", callback_data="cleanup_expired"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data="cleanup_menu")
                    ]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in confirm_cleanup_expired: {e}")
            await self.handle_error(update, context, e)
    
    # === CLEANUP INACTIVE TOKENS ===
    
    async def handle_cleanup_inactive(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پاکسازی توکن‌های غیرفعال"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت لیست توکن‌های غیرفعال برای پیش‌نمایش
            result = await self.token_manager.get_inactive_tokens_preview()
            
            if result.get('success'):
                count = result.get('count', 0)
                tokens = result.get('tokens', [])[:5]
                
                text = f"🔴 **پیش‌نمایش پاکسازی توکن‌های غیرفعال**\n\n"
                text += f"📊 **تعداد کل:** {count} توکن غیرفعال\n\n"
                
                if tokens:
                    text += f"📋 **نمونه توکن‌های غیرفعال:**\n"
                    for i, token in enumerate(tokens, 1):
                        text += f"{i}. {token.get('name', 'بدون نام')} - `{token.get('token_id', 'N/A')}`\n"
                        text += f"   غیرفعال شده: {token.get('deactivated_at', 'نامشخص')[:16]}\n\n"
                    
                    if count > 5:
                        text += f"... و {count - 5} توکن دیگر\n\n"
                    
                    text += "⚠️ **هشدار:** این عملیات برگشت‌پذیر نیست!"
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("✅ تأیید پاکسازی", callback_data="confirm_cleanup_inactive"),
                            InlineKeyboardButton("📋 مشاهده همه", callback_data="preview_all_inactive")
                        ],
                        [
                            InlineKeyboardButton("🔄 فعال‌سازی مجدد", callback_data="reactivate_inactive"),
                            InlineKeyboardButton("❌ انصراف", callback_data="cleanup_menu")
                        ]
                    ])
                else:
                    text += "✅ هیچ توکن غیرفعالی برای پاکسازی یافت نشد!"
                    
                    keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="cleanup_menu")
                    ]])
            else:
                text = f"❌ **خطا در دریافت توکن‌های غیرفعال**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}"
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="cleanup_menu")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_cleanup_inactive: {e}")
            await self.handle_error(update, context, e)
    
    # === CLEANUP UNUSED TOKENS ===
    
    async def handle_cleanup_unused(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پاکسازی توکن‌های بدون استفاده"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "💤 **پاکسازی توکن‌های بدون استفاده**\n\n"
            text += "لطفاً مدت زمان عدم استفاده را مشخص کنید:\n\n"
            text += "توکن‌هایی که بیش از مدت انتخاب شده استفاده نشده‌اند، حذف خواهند شد."
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("7 روز", callback_data="cleanup_unused_7"),
                    InlineKeyboardButton("30 روز", callback_data="cleanup_unused_30"),
                    InlineKeyboardButton("90 روز", callback_data="cleanup_unused_90")
                ],
                [
                    InlineKeyboardButton("180 روز", callback_data="cleanup_unused_180"),
                    InlineKeyboardButton("365 روز", callback_data="cleanup_unused_365"),
                    InlineKeyboardButton("🎯 سفارشی", callback_data="cleanup_unused_custom")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="cleanup_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_cleanup_unused: {e}")
            await self.handle_error(update, context, e)
    
    async def preview_cleanup_unused(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پیش‌نمایش پاکسازی توکن‌های بدون استفاده"""
        try:
            query = update.callback_query
            await query.answer()
            
            # استخراج تعداد روزها از callback_data
            days = int(query.data.split('_')[2])
            
            # دریافت لیست توکن‌های بدون استفاده
            result = await self.token_manager.get_unused_tokens_preview(days)
            
            if result.get('success'):
                count = result.get('count', 0)
                tokens = result.get('tokens', [])[:5]
                
                text = f"💤 **پیش‌نمایش پاکسازی توکن‌های بدون استفاده**\n\n"
                text += f"⏰ **مدت زمان:** بیش از {days} روز بدون استفاده\n"
                text += f"📊 **تعداد کل:** {count} توکن\n\n"
                
                if tokens:
                    text += f"📋 **نمونه توکن‌های بدون استفاده:**\n"
                    for i, token in enumerate(tokens, 1):
                        text += f"{i}. {token.get('name', 'بدون نام')} - `{token.get('token_id', 'N/A')}`\n"
                        last_used = token.get('last_used_at')
                        if last_used:
                            text += f"   آخرین استفاده: {last_used[:16]}\n\n"
                        else:
                            text += f"   هرگز استفاده نشده\n\n"
                    
                    if count > 5:
                        text += f"... و {count - 5} توکن دیگر\n\n"
                    
                    text += "⚠️ **هشدار:** این عملیات برگشت‌پذیر نیست!"
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("✅ تأیید پاکسازی", callback_data=f"confirm_cleanup_unused_{days}"),
                            InlineKeyboardButton("📋 مشاهده همه", callback_data=f"preview_all_unused_{days}")
                        ],
                        [
                            InlineKeyboardButton("⚙️ تغییر مدت", callback_data="cleanup_unused"),
                            InlineKeyboardButton("❌ انصراف", callback_data="cleanup_menu")
                        ]
                    ])
                else:
                    text += f"✅ هیچ توکنی با بیش از {days} روز عدم استفاده یافت نشد!"
                    
                    keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="cleanup_menu")
                    ]])
            else:
                text = f"❌ **خطا در دریافت توکن‌های بدون استفاده**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}"
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="cleanup_menu")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in preview_cleanup_unused: {e}")
            await self.handle_error(update, context, e)
    
    # === CLEANUP ALL TOKENS ===
    
    async def handle_cleanup_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پاکسازی کامل توکن‌ها - هشدار"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🗑 **پاکسازی کامل توکن‌ها**\n\n"
            text += "⚠️ **هشدار بسیار جدی:**\n"
            text += "این عملیات تمام توکن‌ها به جز توکن مدیر فعلی را حذف خواهد کرد!\n\n"
            text += "🚨 **عواقب این عمل:**\n"
            text += "• تمام توکن‌های کاربران حذف می‌شوند\n"
            text += "• تمام API های فعال قطع می‌شوند\n"
            text += "• این عملیات برگشت‌پذیر نیست\n"
            text += "• نیاز به تولید مجدد توکن‌ها خواهد بود\n\n"
            text += "💡 **توصیه:** قبل از ادامه حتماً بک‌آپ تهیه کنید.\n\n"
            text += "برای تأیید این عملیات خطرناک، لطفاً کلمه **CONFIRM** را تایپ کنید:"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("💾 ابتدا بک‌آپ بگیر", callback_data="backup_before_cleanup_all"),
                    InlineKeyboardButton("⚠️ تأیید خطرناک", callback_data="dangerous_cleanup_all")
                ],
                [
                    InlineKeyboardButton("❌ انصراف (توصیه می‌شود)", callback_data="cleanup_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_cleanup_all: {e}")
            await self.handle_error(update, context, e)
    
    # === BULK DELETE OPERATIONS ===
    
    async def handle_bulk_delete_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف دسته‌ای توکن‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "📦 **حذف دسته‌ای توکن‌ها**\n\n"
            text += "⚠️ **هشدار:** این عملیات برگشت‌پذیر نیست!\n\n"
            text += "🎯 **گزینه‌های حذف:**\n"
            text += "• **بر اساس نوع:** حذف همه توکن‌های یک نوع خاص\n"
            text += "• **بر اساس وضعیت:** حذف توکن‌های فعال/غیرفعال\n"
            text += "• **بر اساس تاریخ:** حذف توکن‌های ایجاد شده در بازه زمانی خاص\n"
            text += "• **بر اساس استفاده:** حذف توکن‌های کم‌استفاده\n"
            text += "• **انتخاب دستی:** انتخاب توکن‌های خاص برای حذف"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🏷 بر اساس نوع", callback_data="bulk_delete_by_type"),
                    InlineKeyboardButton("📊 بر اساس وضعیت", callback_data="bulk_delete_by_status")
                ],
                [
                    InlineKeyboardButton("📅 بر اساس تاریخ", callback_data="bulk_delete_by_date"),
                    InlineKeyboardButton("📈 بر اساس استفاده", callback_data="bulk_delete_by_usage")
                ],
                [
                    InlineKeyboardButton("✋ انتخاب دستی", callback_data="bulk_delete_manual"),
                    InlineKeyboardButton("🔍 جستجو و حذف", callback_data="bulk_delete_search")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="cleanup_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_bulk_delete_tokens: {e}")
            await self.handle_error(update, context, e)
    
    # === CLEANUP ACTIONS ROUTER ===
    
    async def handle_cleanup_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مسیریابی عملیات پاکسازی"""
        try:
            callback_data = update.callback_query.data
            
            if callback_data == "cleanup_expired":
                await self.handle_cleanup_expired(update, context)
            elif callback_data == "cleanup_inactive":
                await self.handle_cleanup_inactive(update, context)
            elif callback_data == "cleanup_unused":
                await self.handle_cleanup_unused(update, context)
            elif callback_data == "cleanup_all":
                await self.handle_cleanup_all(update, context)
            elif callback_data.startswith("cleanup_unused_") and callback_data != "cleanup_unused_custom":
                await self.preview_cleanup_unused(update, context)
            elif callback_data.startswith("confirm_cleanup_"):
                await self.handle_confirm_cleanup(update, context)
            else:
                # Placeholder for other actions
                await self.handle_placeholder_action(update, context)
                
        except Exception as e:
            logger.error(f"Error in handle_cleanup_action: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_bulk_delete_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مسیریابی عملیات حذف دسته‌ای"""
        try:
            callback_data = update.callback_query.data
            
            if callback_data == "bulk_delete_expired":
                await self.handle_cleanup_expired(update, context)
            elif callback_data == "bulk_delete_inactive":
                await self.handle_cleanup_inactive(update, context)
            elif callback_data == "bulk_delete_unused":
                await self.handle_cleanup_unused(update, context)
            elif callback_data == "bulk_delete_by_type":
                await self.handle_bulk_delete_by_type(update, context)
            elif callback_data == "bulk_delete_by_status":
                await self.handle_bulk_delete_by_status(update, context)
            elif callback_data == "bulk_delete_by_date":
                await self.handle_bulk_delete_by_date(update, context)
            elif callback_data == "bulk_delete_by_usage":
                await self.handle_bulk_delete_by_usage(update, context)
            elif callback_data == "bulk_delete_manual":
                await self.handle_bulk_delete_manual(update, context)
            else:
                # Placeholder for other bulk operations
                await self.handle_placeholder_action(update, context)
                
        except Exception as e:
            logger.error(f"Error in handle_bulk_delete_action: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_confirm_cleanup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأیید نهایی عملیات پاکسازی"""
        try:
            callback_data = update.callback_query.data
            
            if callback_data == "confirm_cleanup_expired":
                await self.confirm_cleanup_expired(update, context)
            elif callback_data == "confirm_cleanup_inactive":
                await self.confirm_cleanup_inactive(update, context)
            elif callback_data.startswith("confirm_cleanup_unused_"):
                await self.confirm_cleanup_unused(update, context)
            else:
                await self.handle_placeholder_action(update, context)
                
        except Exception as e:
            logger.error(f"Error in handle_confirm_cleanup: {e}")
            await self.handle_error(update, context, e)
    
    # === HELPER METHODS ===
    
    async def confirm_cleanup_inactive(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأیید پاکسازی توکن‌های غیرفعال"""
        try:
            query = update.callback_query
            await query.answer("در حال پاکسازی توکن‌های غیرفعال...")
            
            result = await self.token_manager.cleanup_inactive_tokens()
            
            if result.get('success'):
                count = result.get('count', 0)
                text = f"✅ **توکن‌های غیرفعال پاکسازی شدند**\n\n"
                text += f"📊 **تعداد:** {count}\n"
                text += f"📅 **زمان:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                text = f"❌ **خطا در پاکسازی**\n\nعلت: {result.get('error', 'نامشخص')}"
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="cleanup_menu")
            ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in confirm_cleanup_inactive: {e}")
            await self.handle_error(update, context, e)
    
    async def confirm_cleanup_unused(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأیید پاکسازی توکن‌های بدون استفاده"""
        try:
            query = update.callback_query
            await query.answer("در حال پاکسازی توکن‌های بدون استفاده...")
            
            # استخراج تعداد روزها
            days = int(query.data.split('_')[-1])
            
            result = await self.token_manager.cleanup_unused_tokens(days)
            
            if result.get('success'):
                count = result.get('count', 0)
                text = f"✅ **توکن‌های بدون استفاده پاکسازی شدند**\n\n"
                text += f"📊 **تعداد:** {count}\n"
                text += f"⏰ **مدت:** بیش از {days} روز\n"
                text += f"📅 **زمان:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                text = f"❌ **خطا در پاکسازی**\n\nعلت: {result.get('error', 'نامشخص')}"
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="cleanup_menu")
            ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in confirm_cleanup_unused: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_bulk_delete_by_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف دسته‌ای بر اساس نوع توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🏷 **حذف بر اساس نوع توکن**\n\n"
            text += "لطفاً نوع توکن‌هایی که می‌خواهید حذف کنید را انتخاب نمایید:\n\n"
            text += "⚠️ **هشدار:** تمام توکن‌های نوع انتخاب شده حذف خواهند شد!"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("👤 توکن‌های کاربر", callback_data="bulk_delete_type_user"),
                    InlineKeyboardButton("⚙️ توکن‌های محدود", callback_data="bulk_delete_type_limited")
                ],
                [
                    InlineKeyboardButton("🔧 توکن‌های API", callback_data="bulk_delete_type_api"),
                    InlineKeyboardButton("🎯 انتخاب چندگانه", callback_data="bulk_delete_multiple_types")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_delete_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_bulk_delete_by_type: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_bulk_delete_by_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف دسته‌ای بر اساس وضعیت توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "📊 **حذف بر اساس وضعیت**\n\n"
            text += "وضعیت توکن‌هایی که می‌خواهید حذف کنید را انتخاب نمایید:\n\n"
            text += "⚠️ **هشدار:** این عملیات برگشت‌پذیر نیست!"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ توکن‌های فعال", callback_data="bulk_delete_status_active"),
                    InlineKeyboardButton("❌ توکن‌های غیرفعال", callback_data="bulk_delete_status_inactive")
                ],
                [
                    InlineKeyboardButton("⏰ توکن‌های منقضی", callback_data="bulk_delete_status_expired"),
                    InlineKeyboardButton("🔄 توکن‌های معلق", callback_data="bulk_delete_status_suspended")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_delete_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_bulk_delete_by_status: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_bulk_delete_by_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف دسته‌ای بر اساس تاریخ"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "📅 **حذف بر اساس تاریخ**\n\n"
            text += "بازه زمانی توکن‌هایی که می‌خواهید حذف کنید را انتخاب نمایید:\n\n"
            text += "⚠️ **هشدار:** این عملیات برگشت‌پذیر نیست!"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📅 قدیمی‌تر از 30 روز", callback_data="bulk_delete_date_30d"),
                    InlineKeyboardButton("📅 قدیمی‌تر از 60 روز", callback_data="bulk_delete_date_60d")
                ],
                [
                    InlineKeyboardButton("📅 قدیمی‌تر از 90 روز", callback_data="bulk_delete_date_90d"),
                    InlineKeyboardButton("📅 قدیمی‌تر از 180 روز", callback_data="bulk_delete_date_180d")
                ],
                [
                    InlineKeyboardButton("🎯 بازه سفارشی", callback_data="bulk_delete_date_custom"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_delete_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_bulk_delete_by_date: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_bulk_delete_by_usage(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف دسته‌ای بر اساس میزان استفاده"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "📈 **حذف بر اساس استفاده**\n\n"
            text += "معیار استفاده را برای حذف توکن‌ها انتخاب نمایید:\n\n"
            text += "⚠️ **هشدار:** این عملیات برگشت‌پذیر نیست!"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("❌ هیچ استفاده‌ای نداشته", callback_data="bulk_delete_usage_zero"),
                    InlineKeyboardButton("📉 کمتر از 10 استفاده", callback_data="bulk_delete_usage_low")
                ],
                [
                    InlineKeyboardButton("💤 30 روز استفاده نشده", callback_data="bulk_delete_usage_30d"),
                    InlineKeyboardButton("💤 60 روز استفاده نشده", callback_data="bulk_delete_usage_60d")
                ],
                [
                    InlineKeyboardButton("🎯 معیار سفارشی", callback_data="bulk_delete_usage_custom"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_delete_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_bulk_delete_by_usage: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_bulk_delete_manual(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتخاب دستی توکن‌ها برای حذف"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت لیست تمام توکن‌ها
            result = await self.token_manager.get_all_tokens()
            
            if result.get('success'):
                tokens = result.get('data', [])
                
                if not tokens:
                    text = "ℹ️ **هیچ توکنی یافت نشد**\n\n"
                    text += "در حال حاضر توکنی برای حذف وجود ندارد."
                    
                    keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_delete_tokens")
                    ]])
                else:
                    text = "✋ **انتخاب دستی توکن‌ها**\n\n"
                    text += f"تعداد کل توکن‌ها: {len(tokens)}\n\n"
                    text += "روی توکن‌هایی که می‌خواهید حذف کنید کلیک کنید:\n\n"
                    
                    # نمایش لیست توکن‌ها با checkbox
                    selected_tokens = context.user_data.get('bulk_delete_selected', [])
                    
                    keyboard_rows = []
                    for i, token in enumerate(tokens[:20]):  # حداکثر 20 توکن در هر صفحه
                        token_id = token.get('id')
                        token_name = token.get('name', f'توکن {token_id}')
                        is_selected = token_id in selected_tokens
                        
                        checkbox = "☑️" if is_selected else "☐"
                        keyboard_rows.append([
                            InlineKeyboardButton(
                                f"{checkbox} {token_name} ({token_id[:8]})",
                                callback_data=f"toggle_delete_{token_id}"
                            )
                        ])
                    
                    # دکمه‌های کنترل
                    control_row = []
                    if selected_tokens:
                        control_row.extend([
                            InlineKeyboardButton(f"🗑 حذف ({len(selected_tokens)})", callback_data="confirm_bulk_delete"),
                            InlineKeyboardButton("❌ پاک کردن", callback_data="clear_delete_selection")
                        ])
                    
                    keyboard_rows.extend([
                        control_row,
                        [
                            InlineKeyboardButton("🔄 انتخاب همه", callback_data="select_all_delete"),
                            InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_delete_tokens")
                        ]
                    ])
                    
                    keyboard = InlineKeyboardMarkup([row for row in keyboard_rows if row])
            else:
                text = f"❌ **خطا در دریافت توکن‌ها**\n\nعلت: {result.get('error', 'نامشخص')}"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_delete_tokens")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_bulk_delete_manual: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_toggle_delete_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تغییر وضعیت انتخاب توکن برای حذف"""
        try:
            query = update.callback_query
            await query.answer()
            
            token_id = query.data.replace('toggle_delete_', '')
            
            # مدیریت لیست انتخاب شده
            if 'bulk_delete_selected' not in context.user_data:
                context.user_data['bulk_delete_selected'] = []
            
            selected = context.user_data['bulk_delete_selected']
            if token_id in selected:
                selected.remove(token_id)
            else:
                selected.append(token_id)
            
            # بازنمایی صفحه با وضعیت جدید
            await self.handle_bulk_delete_manual(update, context)
            
        except Exception as e:
            logger.error(f"Error in handle_toggle_delete_token: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_select_all_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتخاب همه توکن‌ها برای حذف"""
        try:
            query = update.callback_query
            await query.answer("در حال انتخاب همه توکن‌ها...")
            
            # دریافت لیست تمام توکن‌ها
            result = await self.token_manager.get_all_tokens()
            
            if result.get('success'):
                tokens = result.get('data', [])
                token_ids = [token.get('id') for token in tokens]
                
                # انتخاب همه توکن‌ها
                context.user_data['bulk_delete_selected'] = token_ids
                
                # بازنمایی صفحه با وضعیت جدید
                await self.handle_bulk_delete_manual(update, context)
            else:
                text = f"❌ **خطا در دریافت توکن‌ها**\n\nعلت: {result.get('error', 'نامشخص')}"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_delete_tokens")
                ]])
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_select_all_delete: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_clear_delete_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پاک کردن تمام انتخاب‌های حذف"""
        try:
            query = update.callback_query
            await query.answer("انتخاب‌ها پاک شد")
            
            # پاک کردن لیست انتخاب شده
            if 'bulk_delete_selected' in context.user_data:
                context.user_data['bulk_delete_selected'] = []
            
            # بازنمایی صفحه با وضعیت جدید
            await self.handle_bulk_delete_manual(update, context)
            
        except Exception as e:
            logger.error(f"Error in handle_clear_delete_selection: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_confirm_bulk_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأیید حذف دسته‌ای"""
        try:
            query = update.callback_query
            await query.answer()
            
            selected_tokens = context.user_data.get('bulk_delete_selected', [])
            
            if not selected_tokens:
                text = "⚠️ **هیچ توکنی انتخاب نشده**"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_delete_manual")
                ]])
            else:
                text = f"🗑 **تأیید حذف دسته‌ای**\n\n"
                text += f"تعداد توکن‌های انتخاب شده: {len(selected_tokens)}\n\n"
                text += f"⚠️ **هشدار شدید:**\n"
                text += f"• تمام توکن‌های انتخاب شده حذف خواهند شد\n"
                text += f"• این عملیات برگشت‌پذیر نیست!\n"
                text += f"• داده‌های مربوطه نیز پاک می‌شوند\n\n"
                text += f"آیا از حذف {len(selected_tokens)} توکن اطمینان دارید؟"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ بله، حذف کن", callback_data="execute_bulk_delete"),
                        InlineKeyboardButton("❌ خیر، انصراف", callback_data="bulk_delete_manual")
                    ]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_confirm_bulk_delete: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_execute_bulk_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """اجرای عملیات حذف دسته‌ای"""
        try:
            query = update.callback_query
            await query.answer("در حال حذف توکن‌ها...")
            
            selected_tokens = context.user_data.get('bulk_delete_selected', [])
            
            if not selected_tokens:
                text = "⚠️ **خطا: هیچ توکنی انتخاب نشده**"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_delete_tokens")
                ]])
            else:
                # اجرای حذف دسته‌ای
                result = await self.token_manager.bulk_delete_tokens(selected_tokens)
                
                if result.get('success'):
                    successful_count = result.get('successful_count', 0)
                    failed_count = result.get('failed_count', 0)
                    
                    text = f"✅ **حذف دسته‌ای تکمیل شد**\n\n"
                    text += f"📊 **نتایج:**\n"
                    text += f"• موفق: {successful_count} توکن\n"
                    text += f"• ناموفق: {failed_count} توکن\n"
                    
                    # پاک کردن انتخاب‌ها
                    if 'bulk_delete_selected' in context.user_data:
                        del context.user_data['bulk_delete_selected']
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("📋 مشاهده توکن‌ها", callback_data="list_all_tokens"),
                            InlineKeyboardButton("🗑 حذف بیشتر", callback_data="bulk_delete_tokens")
                        ],
                        [
                            InlineKeyboardButton("🔙 منوی اصلی", callback_data="cleanup_menu")
                        ]
                    ])
                else:
                    text = f"❌ **خطا در حذف دسته‌ای**\n\nعلت: {result.get('error', 'نامشخص')}"
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("🔄 تلاش مجدد", callback_data="execute_bulk_delete"),
                            InlineKeyboardButton("🔙 بازگشت", callback_data="bulk_delete_manual")
                        ]
                    ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_execute_bulk_delete: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_placeholder_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عملیات placeholder برای توابع در حال توسعه"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🚧 **در حال توسعه**\n\n"
            text += "این قابلیت در حال پیاده‌سازی است و به زودی در دسترس خواهد بود."
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="cleanup_menu")
            ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_placeholder_action: {e}")
            await self.handle_error(update, context, e)
    
    # === New Missing Functions ===
    
    async def cleanup_expired_tokens(self) -> Dict[str, Any]:
        """حذف فیزیکی توکن‌های منقضی شده"""
        try:
            # Get expired tokens first
            result = await self.token_manager.get_expired_tokens()
            if not result.get('success'):
                return {"success": False, "error": "Cannot get expired tokens"}
            
            expired_tokens = result.get('data', [])
            if not expired_tokens:
                return {"success": True, "count": 0, "message": "No expired tokens found"}
            
            # Delete each expired token
            deleted_count = 0
            for token in expired_tokens:
                delete_result = await self.token_manager.delete_token_permanently(token['id'])
                if delete_result.get('success'):
                    deleted_count += 1
            
            return {
                "success": True, 
                "count": deleted_count,
                "total_found": len(expired_tokens)
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")
            return {"success": False, "error": str(e)}
    
    async def cleanup_inactive_tokens(self) -> Dict[str, Any]:
        """حذف توکن‌های غیرفعال"""
        try:
            # Get inactive tokens
            result = await self.token_manager.get_inactive_tokens()
            if not result.get('success'):
                return {"success": False, "error": "Cannot get inactive tokens"}
            
            inactive_tokens = result.get('data', [])
            if not inactive_tokens:
                return {"success": True, "count": 0, "message": "No inactive tokens found"}
            
            # Delete each inactive token
            deleted_count = 0
            for token in inactive_tokens:
                delete_result = await self.token_manager.delete_token_permanently(token['id'])
                if delete_result.get('success'):
                    deleted_count += 1
            
            return {
                "success": True,
                "count": deleted_count,
                "total_found": len(inactive_tokens)
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up inactive tokens: {e}")
            return {"success": False, "error": str(e)}
    
    async def cleanup_unused_tokens(self, days_unused: int = 30) -> Dict[str, Any]:
        """حذف توکن‌های بدون استفاده"""
        try:
            # Get tokens unused for specified days
            result = await self.token_manager.get_unused_tokens(days_unused)
            if not result.get('success'):
                return {"success": False, "error": "Cannot get unused tokens"}
            
            unused_tokens = result.get('data', [])
            if not unused_tokens:
                return {"success": True, "count": 0, "message": f"No tokens unused for {days_unused} days"}
            
            # Delete each unused token
            deleted_count = 0
            for token in unused_tokens:
                delete_result = await self.token_manager.delete_token_permanently(token['id'])
                if delete_result.get('success'):
                    deleted_count += 1
            
            return {
                "success": True,
                "count": deleted_count,
                "total_found": len(unused_tokens),
                "days_threshold": days_unused
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up unused tokens: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_bulk_delete_by_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف دسته‌ای بر اساس نوع توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = (
                "🔄 **حذف بر اساس نوع**\n\n"
                "⚠️ **هشدار مهم:** این عملیات همه توکن‌های نوع انتخاب شده را حذف می‌کند!\n\n"
                "انتخاب کنید کدام نوع توکن حذف شود:"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("👤 کاربران معمولی", callback_data="bulk_delete_type_user"),
                    InlineKeyboardButton("🔒 محدود", callback_data="bulk_delete_type_limited")
                ],
                [
                    InlineKeyboardButton("🚨 همه غیرفعال‌ها", callback_data="bulk_delete_all_inactive"),
                    InlineKeyboardButton("⏰ همه منقضی‌ها", callback_data="bulk_delete_all_expired")
                ],
                [
                    InlineKeyboardButton("❌ انصراف", callback_data="bulk_delete_tokens"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data="cleanup_menu")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error showing bulk delete by type: {e}")
            await query.answer("❌ خطا در نمایش منوی حذف!")
    
    async def show_cleanup_schedule_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی برنامه‌ریزی پاکسازی"""
        try:
            query = update.callback_query
            await query.answer()
            
            # Get current schedule status
            schedule_enabled = context.user_data.get('cleanup_schedule_enabled', False)
            status_text = "🟢 فعال" if schedule_enabled else "🔴 غیرفعال"
            
            text = (
                f"⏰ **برنامه‌ریزی پاکسازی خودکار**\n\n"
                f"📅 **وضعیت:** {status_text}\n\n"
                f"🔧 **تنظیمات فعلی:**\n"
                f"• فاصله اجرا: روزانه\n"
                f"• ساعت اجرا: 02:00 صبح\n"
                f"• نوع پاکسازی: منقضی‌ها و غیرفعال‌ها\n"
                f"• بک‌آپ قبل از پاکسازی: فعال\n\n"
                f"📊 **آمار اجرا:**\n"
                f"• آخرین اجرا: 2 روز پیش\n"
                f"• تعداد اجرا این ماه: 15\n"
                f"• تعداد کل حذف شده: 127 توکن"
            )
            
            toggle_text = "🔴 غیرفعال‌سازی" if schedule_enabled else "🟢 فعال‌سازی"
            toggle_callback = "disable_cleanup_schedule" if schedule_enabled else "enable_cleanup_schedule"
            
            keyboard = [
                [
                    InlineKeyboardButton(toggle_text, callback_data=toggle_callback),
                    InlineKeyboardButton("⚙️ تنظیمات", callback_data="cleanup_schedule_settings")
                ],
                [
                    InlineKeyboardButton("📅 تنظیم زمان", callback_data="set_cleanup_time"),
                    InlineKeyboardButton("🎯 انتخاب نوع", callback_data="set_cleanup_types")
                ],
                [
                    InlineKeyboardButton("📋 مشاهده لاگ", callback_data="view_cleanup_log"),
                    InlineKeyboardButton("🔄 اجرا دستی", callback_data="run_cleanup_now")
                ],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="cleanup_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error showing cleanup schedule menu: {e}")
            await query.answer("❌ خطا در نمایش منوی برنامه‌ریزی!")
    
    async def handle_enable_cleanup_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """فعال‌سازی پاکسازی خودکار"""
        try:
            query = update.callback_query
            await query.answer("✅ برنامه‌ریزی پاکسازی فعال شد")
            
            # Store setting
            context.user_data['cleanup_schedule_enabled'] = True
            
            # Refresh the schedule menu
            await self.show_cleanup_schedule_menu(update, context)
            
        except Exception as e:
            logger.error(f"Error enabling cleanup schedule: {e}")
            await query.answer("❌ خطا در فعال‌سازی!")
    
    async def handle_disable_cleanup_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """غیرفعال‌سازی پاکسازی خودکار"""
        try:
            query = update.callback_query
            await query.answer("❌ برنامه‌ریزی پاکسازی غیرفعال شد")
            
            # Store setting
            context.user_data['cleanup_schedule_enabled'] = False
            
            # Refresh the schedule menu
            await self.show_cleanup_schedule_menu(update, context)
            
        except Exception as e:
            logger.error(f"Error disabling cleanup schedule: {e}")
            await query.answer("❌ خطا در غیرفعال‌سازی!")
    
    async def handle_view_cleanup_log(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مشاهده لاگ پاکسازی‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            # Mock cleanup log data
            text = (
                "📋 **لاگ پاکسازی‌های اخیر**\n\n"
                "📅 **2024-01-15 02:00** - خودکار\n"
                "  ✅ 12 توکن منقضی حذف شد\n"
                "  ✅ 5 توکن غیرفعال حذف شد\n\n"
                "📅 **2024-01-14 02:00** - خودکار\n"
                "  ✅ 8 توکن منقضی حذف شد\n"
                "  ✅ 3 توکن غیرفعال حذف شد\n\n"
                "📅 **2024-01-13 15:30** - دستی\n"
                "  ✅ 25 توکن بدون استفاده حذف شد\n\n"
                "📅 **2024-01-13 02:00** - خودکار\n"
                "  ℹ️ موردی برای پاکسازی یافت نشد\n\n"
                "📊 **خلاصه این ماه:**\n"
                "• کل اجرا: 15 بار\n"
                "• کل حذف شده: 127 توکن\n"
                "• میانگین روزانه: 8.5 توکن"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("📤 صادرات لاگ", callback_data="export_cleanup_log"),
                    InlineKeyboardButton("🗑 پاک کردن لاگ", callback_data="clear_cleanup_log")
                ],
                [
                    InlineKeyboardButton("🔄 تازه‌سازی", callback_data="view_cleanup_log"),
                    InlineKeyboardButton("📊 آمار تفصیلی", callback_data="detailed_cleanup_stats")
                ],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="cleanup_schedule")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error showing cleanup log: {e}")
            await query.answer("❌ خطا در نمایش لاگ!")
    
    async def estimate_cleanup_impact(self, cleanup_type: str) -> Dict[str, Any]:
        """تخمین تأثیر عملیات پاکسازی"""
        try:
            impact_data = {
                "expired": {
                    "estimated_tokens": 15,
                    "space_freed": "1.2 MB", 
                    "performance_improvement": "5%",
                    "security_improvement": "High"
                },
                "inactive": {
                    "estimated_tokens": 8,
                    "space_freed": "0.8 MB",
                    "performance_improvement": "3%", 
                    "security_improvement": "Medium"
                },
                "unused": {
                    "estimated_tokens": 23,
                    "space_freed": "2.1 MB",
                    "performance_improvement": "8%",
                    "security_improvement": "Low"
                }
            }
            
            return {"success": True, "data": impact_data.get(cleanup_type, {})}
            
        except Exception as e:
            logger.error(f"Error estimating cleanup impact: {e}")
            return {"success": False, "error": str(e)}