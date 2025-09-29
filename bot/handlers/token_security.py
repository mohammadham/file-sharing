#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token Security Handler - مدیریت امنیت و تنظیمات امنیتی توکن‌ها
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

from handlers.base_handler import BaseHandler

logger = logging.getLogger(__name__)


class TokenSecurityHandler(BaseHandler):
    """مدیریت امنیت و تنظیمات امنیتی توکن‌ها"""
    
    def __init__(self, db, token_manager):
        """
        Args:
            db: دیتابیس منیجر
            token_manager: TokenManagementHandler اصلی برای API calls
        """
        super().__init__(db)
        self.token_manager = token_manager
    
    # === SECURITY SETTINGS MENU ===
    
    async def show_security_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """منوی اصلی امنیت"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔒 **مدیریت امنیت توکن‌ها**\n\n"
            text += "🛡 **تنظیمات امنیتی:**\n"
            text += "• **انقضا:** مدیریت زمان انقضای توکن‌ها\n"
            text += "• **محدودیت استفاده:** تعیین حد مجاز استفاده\n"
            text += "• **IP و جغرافیا:** کنترل دسترسی مکانی\n"
            text += "• **هشدارها:** اطلاع‌رسانی رویدادهای امنیتی\n"
            text += "• **احراز هویت:** تنظیمات ورود امن\n\n"
            
            text += "🔒 **عملیات غیرفعال‌سازی:**\n"
            text += "• غیرفعال‌سازی توکن‌های مختلف\n"
            text += "• شناسایی و مدیریت توکن‌های مشکوک"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⏰ انقضا", callback_data="expiry_settings"),
                    InlineKeyboardButton("🔢 حد استفاده", callback_data="usage_limit_settings")
                ],
                [
                    InlineKeyboardButton("🌐 محدودیت IP", callback_data="ip_restrictions"),
                    InlineKeyboardButton("🔔 هشدارها", callback_data="security_alerts")
                ],
                [
                    InlineKeyboardButton("🔐 احراز هویت 2FA", callback_data="2fa_settings"),
                    InlineKeyboardButton("🗝 مدیریت session", callback_data="session_settings")
                ],
                [
                    InlineKeyboardButton("🔒 غیرفعال‌سازی", callback_data="deactivate_tokens"),
                    InlineKeyboardButton("⚠️ بررسی مشکوک", callback_data="suspicious_analysis")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_security_menu: {e}")
            await self.handle_error(update, context, e)
    
    # === EXPIRY SETTINGS ===
    
    async def show_expiry_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیمات انقضا"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "⏰ **تنظیمات انقضای توکن‌ها**\n\n"
            text += "🔧 **انواع تنظیمات:**\n"
            text += "• **انقضای پیش‌فرض:** برای توکن‌های جدید\n"
            text += "• **انقضای دسته‌ای:** تغییر انقضای چندین توکن\n"
            text += "• **انقضای سفارشی:** تنظیم انقضای یک توکن خاص\n"
            text += "• **تمدید خودکار:** تنظیم تمدید اتوماتیک\n\n"
            
            text += "⚙️ **وضعیت فعلی:**\n"
            text += "• انقضای پیش‌فرض: بدون محدودیت\n"
            text += "• تمدید خودکار: غیرفعال\n"
            text += "• یادآوری انقضا: فعال"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⏰ انقضای پیش‌فرض", callback_data="set_default_expiry"),
                    InlineKeyboardButton("📦 انقضای دسته‌ای", callback_data="set_bulk_expiry")
                ],
                [
                    InlineKeyboardButton("🎯 انقضای سفارشی", callback_data="set_custom_expiry"),
                    InlineKeyboardButton("🔄 تمدید خودکار", callback_data="auto_renewal_settings")
                ],
                [
                    InlineKeyboardButton("⏰ توکن‌های منقضی", callback_data="expired_tokens_list"),
                    InlineKeyboardButton("📅 برنامه‌ریزی انقضا", callback_data="expiry_schedule")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="security_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_expiry_settings: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_set_default_expiry(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیم انقضای پیش‌فرض"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "⏰ **تنظیم انقضای پیش‌فرض**\n\n"
            text += "لطفاً مدت زمان انقضای پیش‌فرض را برای توکن‌های جدید انتخاب کنید:\n\n"
            text += "این تنظیم برای همه توکن‌های تولید شده در آینده اعمال خواهد شد."
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("1 روز", callback_data="set_def_expiry_1"),
                    InlineKeyboardButton("7 روز", callback_data="set_def_expiry_7"),
                    InlineKeyboardButton("30 روز", callback_data="set_def_expiry_30")
                ],
                [
                    InlineKeyboardButton("90 روز", callback_data="set_def_expiry_90"),
                    InlineKeyboardButton("365 روز", callback_data="set_def_expiry_365"),
                    InlineKeyboardButton("♾ نامحدود", callback_data="set_def_expiry_0")
                ],
                [
                    InlineKeyboardButton("🎯 سفارشی", callback_data="set_def_expiry_custom"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data="expiry_settings")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_set_default_expiry: {e}")
            await self.handle_error(update, context, e)
    
    # === USAGE LIMITS ===
    
    async def show_usage_limit_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیمات محدودیت استفاده"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔢 **تنظیمات محدودیت استفاده**\n\n"
            text += "⚙️ **انواع محدودیت:**\n"
            text += "• **حد روزانه:** تعداد درخواست در روز\n"
            text += "• **حد ماهانه:** تعداد درخواست در ماه\n"
            text += "• **حد همزمان:** تعداد درخواست همزمان\n"
            text += "• **محدودیت نرخ:** تعداد درخواست در ثانیه\n\n"
            
            text += "📊 **وضعیت فعلی:**\n"
            text += "• حد روزانه: نامحدود\n"
            text += "• حد ماهانه: نامحدود\n"
            text += "• حد همزمان: 10 درخواست\n"
            text += "• Rate Limit: 5 درخواست/ثانیه"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📅 حد روزانه", callback_data="set_daily_limit"),
                    InlineKeyboardButton("📆 حد ماهانه", callback_data="set_monthly_limit")
                ],
                [
                    InlineKeyboardButton("⚡ حد همزمان", callback_data="set_concurrent_limit"),
                    InlineKeyboardButton("🏃 Rate Limiting", callback_data="set_rate_limit")
                ],
                [
                    InlineKeyboardButton("📊 کوتا به اشتراک‌گذاری", callback_data="quota_sharing"),
                    InlineKeyboardButton("⚠️ هشدار سهمیه", callback_data="quota_alerts")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="security_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_usage_limit_settings: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_set_usage_limit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیم حد استفاده"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔢 **تنظیم حد استفاده روزانه**\n\n"
            text += "لطفاً حداکثر تعداد استفاده روزانه را برای توکن‌ها تعیین کنید:\n\n"
            text += "این محدودیت برای تمام توکن‌ها اعمال خواهد شد."
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("100", callback_data="set_usage_100"),
                    InlineKeyboardButton("500", callback_data="set_usage_500"),
                    InlineKeyboardButton("1K", callback_data="set_usage_1000")
                ],
                [
                    InlineKeyboardButton("5K", callback_data="set_usage_5000"),
                    InlineKeyboardButton("10K", callback_data="set_usage_10000"),
                    InlineKeyboardButton("50K", callback_data="set_usage_50000")
                ],
                [
                    InlineKeyboardButton("♾ نامحدود", callback_data="set_usage_0"),
                    InlineKeyboardButton("🎯 سفارشی", callback_data="set_usage_custom")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="usage_limit_settings")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_set_usage_limit: {e}")
            await self.handle_error(update, context, e)
    
    # === IP RESTRICTIONS ===
    
    async def handle_ip_restrictions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """محدودیت‌های IP"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🌐 **محدودیت‌های IP**\n\n"
            text += "🔒 **وضعیت فعلی:** غیرفعال\n\n"
            text += "🛡 **انواع محدودیت:**\n"
            text += "• **لیست سفید:** فقط IP های مجاز دسترسی داشته باشند\n"
            text += "• **لیست سیاه:** IP های خاص مسدود شوند\n"
            text += "• **محدودیت جغرافیایی:** بر اساس کشور\n"
            text += "• **تشخیص VPN/Proxy:** شناسایی و مسدودسازی\n\n"
            
            text += "📊 **آمار IP:**\n"
            text += "• IP های فعال: 25\n"
            text += "• IP های مشکوک: 3\n"
            text += "• کشورهای دسترسی: 12"
            
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
                    InlineKeyboardButton("🔍 تشخیص VPN", callback_data="vpn_detection")
                ],
                [
                    InlineKeyboardButton("📊 آمار IP", callback_data="ip_statistics"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data="security_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_ip_restrictions: {e}")
            await self.handle_error(update, context, e)
    
    # === SECURITY ALERTS ===
    
    async def handle_security_alerts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """هشدارهای امنیتی"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔔 **هشدارهای امنیتی**\n\n"
            text += "🟢 **وضعیت:** فعال\n\n"
            text += "🚨 **انواع هشدارها:**\n"
            text += "• **توکن جدید:** اطلاع از ایجاد توکن جدید\n"
            text += "• **دسترسی مشکوک:** فعالیت غیرعادی\n"
            text += "• **تلاش ورود ناموفق:** دسترسی غیرمجاز\n"
            text += "• **انقضای توکن:** یادآوری انقضا\n"
            text += "• **حد استفاده:** رسیدن به سهمیه\n\n"
            
            text += "📨 **کانال‌های هشدار:**\n"
            text += "• 📧 ایمیل: فعال\n"
            text += "• 📱 تلگرام: فعال\n"
            text += "• 🔗 Webhook: غیرفعال"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📧 تنظیم ایمیل", callback_data="email_alerts_settings"),
                    InlineKeyboardButton("📱 تنظیم تلگرام", callback_data="telegram_alerts_settings")
                ],
                [
                    InlineKeyboardButton("🔗 تنظیم Webhook", callback_data="webhook_alerts_settings"),
                    InlineKeyboardButton("📞 تنظیم SMS", callback_data="sms_alerts_settings")
                ],
                [
                    InlineKeyboardButton("⚙️ سطح هشدارها", callback_data="alert_thresholds"),
                    InlineKeyboardButton("📊 تاریخچه هشدارها", callback_data="alert_history")
                ],
                [
                    InlineKeyboardButton("🔕 غیرفعال کردن همه", callback_data="disable_all_alerts"),
                    InlineKeyboardButton("🔔 فعال کردن همه", callback_data="enable_all_alerts")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="security_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_security_alerts: {e}")
            await self.handle_error(update, context, e)
    
    # === DEACTIVATION OPERATIONS ===
    
    async def handle_deactivate_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """منوی غیرفعال‌سازی توکن‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔒 **غیرفعال‌سازی توکن‌ها**\n\n"
            text += "⚠️ **هشدار:** غیرفعال‌سازی توکن‌ها آن‌ها را غیرقابل‌استفاده می‌کند!\n\n"
            text += "🎯 **انواع غیرفعال‌سازی:**\n"
            text += "• **تک توکن:** غیرفعال کردن یک توکن خاص\n"
            text += "• **دسته‌ای:** غیرفعال کردن چندین توکن همزمان\n"
            text += "• **منقضی‌ها:** غیرفعال کردن توکن‌های منقضی شده\n"
            text += "• **مشکوک:** غیرفعال کردن توکن‌های با فعالیت مشکوک\n"
            text += "• **کاربر خاص:** غیرفعال کردن همه توکن‌های یک کاربر"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔒 تک توکن", callback_data="deactivate_single_token"),
                    InlineKeyboardButton("📦 دسته‌ای", callback_data="deactivate_bulk_tokens")
                ],
                [
                    InlineKeyboardButton("⏰ منقضی‌ها", callback_data="deactivate_expired_tokens"),
                    InlineKeyboardButton("⚠️ مشکوک", callback_data="deactivate_suspicious_tokens")
                ],
                [
                    InlineKeyboardButton("👤 کاربر خاص", callback_data="deactivate_user_tokens"),
                    InlineKeyboardButton("🔄 توکن فعلی", callback_data="deactivate_current_token")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="security_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_deactivate_tokens: {e}")
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
                        InlineKeyboardButton("🔙 بازگشت", callback_data="deactivate_tokens")
                    ]])
                )
                return
            
            token_id = session.get('current_token_id')
            
            # غیرفعال‌سازی توکن از طریق API
            result = await self.token_manager.deactivate_token(token_id)
            
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
                        InlineKeyboardButton("🔙 بازگشت", callback_data="deactivate_tokens")
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
            result = await self.token_manager.deactivate_expired_tokens()
            
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
                        InlineKeyboardButton("🔙 بازگشت", callback_data="deactivate_tokens")
                    ]
                ])
            else:
                text = f"❌ **خطا در غیرفعال‌سازی توکن‌های منقضی**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}\n\n"
                text += "لطفاً دوباره تلاش کنید."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 تلاش مجدد", callback_data="deactivate_expired_tokens"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data="deactivate_tokens")
                    ]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_deactivate_expired_tokens: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_deactivate_suspicious_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """غیرفعال‌سازی توکن‌های مشکوک"""
        try:
            query = update.callback_query
            await query.answer("در حال بررسی توکن‌های مشکوک...")
            
            # دریافت توکن‌های مشکوک از طریق API
            result = await self.token_manager.get_suspicious_tokens()
            
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
                        InlineKeyboardButton("❌ انصراف", callback_data="deactivate_tokens")
                    ]
                ])
            else:
                text = "✅ **هیچ توکن مشکوکی یافت نشد**\n\n"
                text += "تمام توکن‌ها در حالت عادی هستند."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 بررسی مجدد", callback_data="deactivate_suspicious_tokens"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data="deactivate_tokens")
                    ]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_deactivate_suspicious_tokens: {e}")
            await self.handle_error(update, context, e)
    
    # === TOKEN EXPIRY ===
    
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
                    InlineKeyboardButton("🔙 بازگشت", callback_data="security_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_set_token_expiry: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_set_expiry_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """اجرای تنظیم انقضا"""
        try:
            query = update.callback_query
            await query.answer()
            
            # Extract expiry period from callback_data
            expiry_data = query.data.split('_')
            if len(expiry_data) >= 3:
                days = expiry_data[2]
                
                if days == '0':
                    period_text = "نامحدود"
                else:
                    period_text = f"{days} روز"
                
                # Call API to set expiry
                result = await self.token_manager.set_token_expiry(days)
                
                if result.get('success'):
                    text = f"✅ **انقضای پیش‌فرض تنظیم شد**\n\n"
                    text += f"⏰ **مدت زمان جدید:** {period_text}\n"
                    text += f"📅 **زمان تنظیم:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    text += "این تنظیم برای همه توکن‌های آینده اعمال خواهد شد."
                else:
                    text = f"❌ **خطا در تنظیم انقضا**\n\n"
                    text += f"علت: {result.get('error', 'نامشخص')}"
            else:
                text = "❌ **خطا در پردازش درخواست**"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 تنظیم مجدد", callback_data="set_default_expiry"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data="expiry_settings")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_set_expiry_action: {e}")
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