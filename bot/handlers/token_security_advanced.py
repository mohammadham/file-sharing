#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token Security Advanced Handler - پیاده‌سازی کامل شاخه امنیت از نمودار درختی
"""

import logging
import json
import csv
from io import BytesIO
from io import StringIO



from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta

from handlers.base_handler import BaseHandler

logger = logging.getLogger(__name__)


class TokenSecurityAdvancedHandler(BaseHandler):
    """پیاده‌سازی کامل شاخه امنیت - 🔒 security_menu"""
    
    def __init__(self, db, token_manager):
        """
        Args:
            db: دیتابیس منیجر
            token_manager: TokenManagementHandler اصلی برای API calls
        """
        super().__init__(db)
        self.token_manager = token_manager
    
    # === SECURITY MAIN MENU ===
    
    async def show_security_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """منوی اصلی امنیت - security_menu"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔒 **مدیریت امنیت توکن‌ها**\n\n"
            text += "🛡 **دسته‌بندی‌های امنیتی:**\n"
            text += "• **انقضا:** مدیریت زمان انقضای توکن‌ها\n"
            text += "• **محدودیت استفاده:** تعیین حد مجاز استفاده\n"
            text += "• **IP و جغرافیا:** کنترل دسترسی مکانی\n"
            text += "• **هشدارها:** اطلاع‌رسانی رویدادهای امنیتی\n"
            text += "• **احراز هویت:** تنظیمات ورود امن\n"
            text += "• **غیرفعال‌سازی:** مدیریت توکن‌های مشکوک\n\n"
            
            text += "⚙️ **وضعیت کلی امنیت:** 🟢 مطمئن"
            
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
            logger.error(f"Error in show_security_main_menu: {e}")
            await self.handle_error(update, context, e)
    
    # === SET DEFAULT EXPIRY - Level 2 ===
    
    async def show_set_default_expiry_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیم انقضای پیش‌فرض - set_default_expiry"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "⏰ **تنظیم انقضای پیش‌فرض**\n\n"
            text += "این تنظیم برای همه توکن‌های تولید شده در آینده اعمال خواهد شد.\n\n"
            text += "🔧 **وضعیت فعلی:** بدون محدودیت\n\n"
            text += "لطفاً مدت زمان انقضای پیش‌فرض را انتخاب کنید:"
            
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
                    InlineKeyboardButton("🔙 بازگشت", callback_data="security_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_set_default_expiry_menu: {e}")
            await self.handle_error(update, context, e)
    
    # === SET USAGE LIMIT - Level 2 ===
    
    async def show_set_usage_limit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیم حد استفاده - set_usage_limit"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔢 **تنظیم حد استفاده**\n\n"
            text += "تعیین حداکثر تعداد استفاده روزانه برای توکن‌ها\n\n"
            text += "🔧 **وضعیت فعلی:** نامحدود\n\n"
            text += "لطفاً حد استفاده مورد نظر را انتخاب کنید:"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("100", callback_data="limit_100"),
                    InlineKeyboardButton("500", callback_data="limit_500"),
                    InlineKeyboardButton("1K", callback_data="limit_1k")
                ],
                [
                    InlineKeyboardButton("5K", callback_data="limit_5k"),
                    InlineKeyboardButton("10K", callback_data="limit_10k"),
                    InlineKeyboardButton("♾ نامحدود", callback_data="limit_unlimited")
                ],
                [
                    InlineKeyboardButton("🎯 سفارشی", callback_data="limit_custom"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data="security_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_set_usage_limit_menu: {e}")
            await self.handle_error(update, context, e)
    
    # === IP RESTRICTIONS - Level 2 ===
    
    async def show_ip_restrictions_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """محدودیت‌های IP - ip_restrictions"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🌐 **محدودیت‌های IP**\n\n"
            text += "🔒 **وضعیت فعلی:** غیرفعال\n\n"
            text += "🛡 **انواع محدودیت:**\n"
            text += "• فعال‌سازی کنترل IP\n"
            text += "• مدیریت لیست سفید\n"
            text += "• مدیریت لیست سیاه\n"
            text += "• محدودیت جغرافیایی\n"
            text += "• آمار و گزارش IP ها"
            
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
            ])
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_ip_restrictions_menu: {e}")
            await self.handle_error(update, context, e)

    async def show_ip_statistics_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش آمار IP (top_ips و suspicious_ips)"""
        try:
            query = update.callback_query
            await query.answer()

            if not hasattr(self.db, 'security_manager'):
                await query.edit_message_text("❌ سیستم امنیتی مقداردهی نشده است", parse_mode='Markdown')
                return
            sm = self.db.security_manager
            stats = await sm.get_ip_statistics(limit=10)

            text = "📊 **آمار IP ها (7 روز اخیر)**\n\n"
            top_ips = stats.get('top_ips', [])
            suspicious = stats.get('suspicious_ips', [])

            if top_ips:
                text += "🔥 **IP های پرترافیک:**\n"
                for i, item in enumerate(top_ips, 1):
                    text += f"{i}. `{item['ip_address']}` — {item['count']} دانلود موفق\n"
                text += "\n"
            else:
                text += "هیچ IP پرترافیکی یافت نشد.\n\n"

            if suspicious:
                text += "⚠️ **IP های مشکوک (24 ساعت):**\n"
                for i, item in enumerate(suspicious, 1):
                    text += f"{i}. `{item['ip_address']}` — شکست: {item['failures']}, لینک‌های متمایز: {item['distinct_links']}\n"
                text += "\n"
            else:
                text += "هیچ IP مشکوکی یافت نشد.\n\n"

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data="ip_statistics")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="ip_restrictions")]
            ])
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in show_ip_statistics_menu: {e}")
            await self.handle_error(update, context, e)

    # === MANAGE WHITELIST IP - Level 3 ===
    
    async def show_manage_whitelist_ip_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت لیست سفید IP - manage_whitelist_ip"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "📝 **مدیریت لیست سفید IP**\n\n"
            
            # Get whitelist from security manager
            if hasattr(self.db, 'security_manager'):
                security_manager = self.db.security_manager
                ips = await security_manager.get_whitelist(active_only=True)
                
                text += f"📊 **تعداد IP های مجاز:** {len(ips)}\n\n"
                
                if ips:
                    text += "🟢 **IP های مجاز:**\n"
                    for i, ip_info in enumerate(ips[:5], 1):
                        text += f"{i}. `{ip_info.get('ip_address', 'نامشخص')}`\n"
                        text += f"   📅 اضافه شده: {ip_info.get('created_at', 'نامشخص')[:16]}\n"
                        if ip_info.get('description'):
                            text += f"   📝 توضیح: {ip_info.get('description')}\n"
                        text += "\n"
                    
                    if len(ips) > 5:
                        text += f"... و {len(ips) - 5} IP دیگر\n\n"
                else:
                    text += "❌ هیچ IP مجازی تعریف نشده است!\n\n"
            else:
                text += "❌ خطا: سیستم امنیتی مقداردهی نشده است\n\n"
            
            text += "⚙️ **عملیات مدیریتی:**"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("➕ اضافه کردن IP", callback_data="add_ip_to_whitelist"),
                    InlineKeyboardButton("➖ حذف IP", callback_data="remove_ip_from_whitelist")
                ],
                [
                    InlineKeyboardButton("📥 واردات CSV", callback_data="import_whitelist_csv"),
                    InlineKeyboardButton("📤 صادرات لیست", callback_data="export_whitelist")
                ],
                [
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data="manage_whitelist_ip"),
                    InlineKeyboardButton("🗑 پاک کردن همه", callback_data="clear_whitelist")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="ip_restrictions")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_manage_whitelist_ip_menu: {e}")
            await self.handle_error(update, context, e)
    
    # === ADD IP TO WHITELIST - Level 4 ===
    
    async def show_add_ip_to_whitelist_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """اضافه کردن IP به لیست سفید - add_ip_to_whitelist"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "➕ **اضافه کردن IP به لیست سفید**\n\n"
            text += "🔗 **روش‌های اضافه کردن:**\n"
            text += "• **IP تکی:** اضافه کردن یک IP خاص\n"
            text += "• **محدوده IP:** اضافه کردن یک بازه IP\n"
            text += "• **IP فعلی:** اضافه کردن IP جاری شما\n"
            text += "• **لیست دسته‌ای:** اضافه کردن چندین IP همزمان\n\n"
            
            text += "📝 **راهنما:**\n"
            text += "• فرمت IP: `192.168.1.100`\n"
            text += "• فرمت محدوده: `192.168.1.0/24`\n"
            text += "• توضیح اختیاری برای هر IP"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🎯 IP تکی", callback_data="add_single_ip"),
                    InlineKeyboardButton("📊 محدوده IP", callback_data="add_ip_range")
                ],
                [
                    InlineKeyboardButton("📍 IP فعلی من", callback_data="add_current_ip"),
                    InlineKeyboardButton("📋 لیست دسته‌ای", callback_data="add_bulk_ips")
                ],
                [
                    InlineKeyboardButton("📥 از فایل CSV", callback_data="import_ips_csv"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data="manage_whitelist_ip")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_add_ip_to_whitelist_menu: {e}")
            await self.handle_error(update, context, e)
    
    # === REMOVE IP FROM WHITELIST - Level 4 ===
    
    async def show_remove_ip_from_whitelist_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف IP از لیست سفید - remove_ip_from_whitelist"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت لیست IP های سفید
            result = await self.token_manager.get_whitelist_ips()
            
            text = "➖ **حذف IP از لیست سفید**\n\n"
            
            if result.get('success'):
                ips = result.get('ips', [])
                
                if ips:
                    text += f"📊 **{len(ips)} IP در لیست سفید**\n\n"
                    text += "🎯 **انتخاب IP برای حذف:**\n"
                    
                    # نمایش تا 5 IP اول
                    buttons = []
                    for i, ip_info in enumerate(ips[:5]):
                        ip = ip_info.get('ip', 'نامشخص')
                        desc = ip_info.get('description', '')[:20] + '...' if len(ip_info.get('description', '')) > 20 else ip_info.get('description', 'بدون توضیح')
                        
                        text += f"• `{ip}` - {desc}\n"
                        buttons.append([InlineKeyboardButton(f"🗑 حذف {ip}", callback_data=f"remove_whitelist_ip_{i}")])
                    
                    if len(ips) > 5:
                        text += f"\n... و {len(ips) - 5} IP دیگر\n"
                        buttons.append([InlineKeyboardButton("📄 مشاهده همه", callback_data="view_all_whitelist_ips")])
                    
                    # اضافه کردن دکمه‌های عمومی
                    buttons.extend([
                        [InlineKeyboardButton("🔍 جستجو", callback_data="search_whitelist_ip")],
                        [InlineKeyboardButton("🗑 حذف چندتایی", callback_data="bulk_remove_whitelist")],
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_whitelist_ip")]
                    ])
                    
                    keyboard = InlineKeyboardMarkup(buttons)
                else:
                    text += "❌ هیچ IP در لیست سفید وجود ندارد!\n"
                    text += "ابتدا IP هایی به لیست اضافه کنید."
                    
                    keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton("➕ اضافه کردن IP", callback_data="add_ip_to_whitelist"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data="manage_whitelist_ip")
                    ]])
            else:
                text += "❌ خطا در دریافت لیست IP ها\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}"
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="manage_whitelist_ip")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_remove_ip_from_whitelist_menu: {e}")
            await self.handle_error(update, context, e)
    
    # === IMPORT WHITELIST CSV - Level 4 ===
    
    async def show_import_whitelist_csv_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """واردات لیست سفید از CSV - import_whitelist_csv"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "📥 **واردات لیست سفید از CSV**\n\n"
            text += "📄 **فرمت فایل CSV مورد نیاز:**\n"
            text += "```\n"
            text += "ip,description,active\n"
            text += "192.168.1.100,دفتر مرکزی,true\n"
            text += "10.0.0.0/8,شبکه داخلی,true\n"
            text += "203.0.113.25,سرور بک‌آپ,false\n"
            text += "```\n\n"
            
            text += "📝 **راهنمای ستون‌ها:**\n"
            text += "• `ip`: آدرس IP یا محدوده (الزامی)\n"
            text += "• `description`: توضیحات (اختیاری)\n"
            text += "• `active`: وضعیت فعال/غیرفعال (اختیاری)\n\n"
            
            text += "⚠️ **نکات مهم:**\n"
            text += "• حداکثر 1000 IP در هر فایل\n"
            text += "• فایل باید کمتر از 1MB باشد\n"
            text += "• IP های تکراری نادیده گرفته می‌شوند\n"
            text += "• IP های نامعتبر رد می‌شوند"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📁 انتخاب فایل", callback_data="select_csv_file"),
                    InlineKeyboardButton("📝 نمونه CSV", callback_data="download_csv_template")
                ],
                [
                    InlineKeyboardButton("📊 اعتبارسنجی", callback_data="validate_csv_format"),
                    InlineKeyboardButton("🔄 پیش‌نمایش", callback_data="preview_csv_import")
                ],
                [
                    InlineKeyboardButton("✅ تأیید واردات", callback_data="confirm_csv_import"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data="add_ip_to_whitelist")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_import_whitelist_csv_menu: {e}")
    async def handle_add_ip_range(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ورود محدوده IP برای whitelist"""
        try:
            query = update.callback_query
            await query.answer()
            context.user_data['awaiting_ip_input'] = 'range'
            text = (
                "📊 **افزودن محدوده IP به لیست سفید**\n\n"
                "لطفاً محدوده را با فرمت CIDR ارسال کنید (مثال: 192.168.1.0/24).\n\n"
                "برای انصراف، /cancel را ارسال کنید."
            )
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="add_ip_to_whitelist")]])
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_add_ip_range: {e}")
            await self.handle_error(update, context, e)

    async def process_whitelist_ip_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت متن IP/Range و افزودن به whitelist"""
        try:
            user_text = update.message.text.strip()
            reason = None
            if hasattr(self.db, 'security_manager'):
                sm = self.db.security_manager
                wl_id = await sm.add_to_whitelist(user_text, description=reason, created_by=update.effective_user.id if update.effective_user else None)
                if wl_id:
                    await update.message.reply_text("✅ IP به لیست سفید اضافه شد")
                else:
                    await update.message.reply_text("❌ IP نامعتبر است یا افزودن با خطا مواجه شد")
            else:
                await update.message.reply_text("❌ سیستم امنیتی مقداردهی نشده است")
            # پاک‌کردن حالت انتظار
            if 'awaiting_ip_input' in context.user_data:
                del context.user_data['awaiting_ip_input']
        except Exception as e:
            logger.error(f"Error in process_whitelist_ip_text_input: {e}")
            await update.message.reply_text("❌ خطا در پردازش ورودی")

    async def process_blacklist_ip_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت متن IP/Range و افزودن به blacklist"""
        try:
            user_text = update.message.text.strip()
            reason = context.user_data.get('blacklist_reason')
            if hasattr(self.db, 'security_manager'):
                sm = self.db.security_manager
                bl_id = await sm.add_to_blacklist(user_text, reason=reason, blocked_by=update.effective_user.id if update.effective_user else None)
                if bl_id:
                    await update.message.reply_text("✅ IP به لیست سیاه اضافه شد")
                else:
                    await update.message.reply_text("❌ IP نامعتبر است یا افزودن با خطا مواجه شد")
            else:
                await update.message.reply_text("❌ سیستم امنیتی مقداردهی نشده است")
            if 'awaiting_blacklist_ip_input' in context.user_data:
                del context.user_data['awaiting_blacklist_ip_input']
            if 'blacklist_reason' in context.user_data:
                del context.user_data['blacklist_reason']
        except Exception as e:
            logger.error(f"Error in process_blacklist_ip_text_input: {e}")
            await update.message.reply_text("❌ خطا در پردازش ورودی")

            await self.handle_error(update, context, e)
    
    # === SECURITY ALERTS - Level 2 ===
    
    async def show_security_alerts_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """هشدارهای امنیتی - security_alerts"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔔 **هشدارهای امنیتی**\n\n"
            text += "🟢 **وضعیت:** فعال\n\n"
            text += "🚨 **کانال‌های هشدار:**\n"
            text += "• 📧 ایمیل: فعال\n"
            text += "• 📱 تلگرام: فعال\n"
            text += "• 🔗 Webhook: غیرفعال\n\n"
            
            text += "⚙️ **تنظیمات هشدار:**\n"
            text += "• آستانه تلاش ناموفق: 5 بار\n"
            text += "• آستانه استفاده مشکوک: 1000 درخواست/ساعت\n"
            text += "• هشدار تغییر جغرافیایی: فعال"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📧 تنظیم ایمیل", callback_data="email_alerts_toggle"),
                    InlineKeyboardButton("📱 تنظیم تلگرام", callback_data="telegram_alerts_toggle")
                ],
                [
                    InlineKeyboardButton("🔗 تنظیم Webhook", callback_data="webhook_alerts_toggle"),
                    InlineKeyboardButton("📞 تنظیم SMS", callback_data="sms_alerts_toggle")
                ],
                [
                    InlineKeyboardButton("⚙️ سطح هشدارها", callback_data="alert_settings"),
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
            logger.error(f"Error in show_security_alerts_menu: {e}")
            await self.handle_error(update, context, e)
    
    # === ALERT SETTINGS - Level 3 ===
    
    async def show_alert_settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیمات سطح هشدارها - alert_settings"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "⚙️ **تنظیمات سطح هشدارها**\n\n"
            text += "🎯 **آستانه‌های هشدار:**\n\n"
            
            text += "🔐 **تلاش ورود ناموفق:**\n"
            text += "• آستانه فعلی: 5 تلاش در 10 دقیقه\n"
            text += "• وضعیت: 🟢 فعال\n\n"
            
            text += "📊 **استفاده مشکوک:**\n"
            text += "• آستانه فعلی: 1000 درخواست در ساعت\n"
            text += "• وضعیت: 🟢 فعال\n\n"
            
            text += "🌍 **تغییر جغرافیایی:**\n"
            text += "• آستانه فعلی: تغییر کشور در کمتر از 1 ساعت\n"
            text += "• وضعیت: 🟢 فعال\n\n"
            
            text += "⏰ **فعالیت زمانی:**\n"
            text += "• آستانه فعلی: فعالیت خارج از ساعت 8-20\n"
            text += "• وضعیت: 🟡 محدود"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔐 تلاش ورود", callback_data="threshold_failed_login"),
                    InlineKeyboardButton("📊 حد سهمیه", callback_data="threshold_quota_limit")
                ],
                [
                    InlineKeyboardButton("🌍 تغییر جغرافیا", callback_data="threshold_geo_anomaly"),
                    InlineKeyboardButton("⏰ الگوی زمانی", callback_data="threshold_time_anomaly")
                ],
                [
                    InlineKeyboardButton("🔄 بازنشانی همه", callback_data="reset_all_thresholds"),
                    InlineKeyboardButton("💾 ذخیره تنظیمات", callback_data="save_alert_settings")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="security_alerts")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_alert_settings_menu: {e}")
            await self.handle_error(update, context, e)
    
    # === THRESHOLD SETTINGS - Level 4 ===
    
    async def show_threshold_failed_login_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیم آستانه تلاش ورود ناموفق - threshold_failed_login"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔐 **تنظیم آستانه تلاش ورود ناموفق**\n\n"
            text += "⚙️ **تنظیم فعلی:** 5 تلاش در 10 دقیقه\n\n"
            text += "🎯 **انتخاب آستانه جدید:**\n"
            text += "تعداد تلاش‌های ناموفق مجاز قبل از فعال شدن هشدار"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("3 تلاش/5 دقیقه", callback_data="set_login_threshold_3_5"),
                    InlineKeyboardButton("5 تلاش/10 دقیقه", callback_data="set_login_threshold_5_10")
                ],
                [
                    InlineKeyboardButton("10 تلاش/15 دقیقه", callback_data="set_login_threshold_10_15"),
                    InlineKeyboardButton("20 تلاش/30 دقیقه", callback_data="set_login_threshold_20_30")
                ],
                [
                    InlineKeyboardButton("🎯 تنظیم سفارشی", callback_data="custom_login_threshold"),
                    InlineKeyboardButton("🔴 غیرفعال‌سازی", callback_data="disable_login_threshold")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="alert_settings")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_threshold_failed_login_menu: {e}")
            await self.handle_error(update, context, e)
    
    # === 2FA SETTINGS - Level 2 ===
    
    async def show_2fa_settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیمات احراز هویت دوعاملی - 2fa_settings"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔐 **تنظیمات احراز هویت دوعاملی (2FA)**\n\n"
            text += "🔧 **وضعیت فعلی:**\n"
            text += "• برای توکن‌های مدیر: 🟢 اجباری\n"
            text += "• برای توکن‌های محدود: 🟡 اختیاری\n"
            text += "• برای توکن‌های کاربر: 🔴 غیرفعال\n\n"
            
            text += "📊 **آمار 2FA:**\n"
            text += "• کاربران با 2FA فعال: 45 نفر\n"
            text += "• کاربران بدون 2FA: 123 نفر\n"
            text += "• نرخ پذیرش 2FA: 26.8%\n\n"
            
            text += "⚙️ **روش‌های پشتیبانی شده:**\n"
            text += "• اپلیکیشن احراز هویت (Google Authenticator)\n"
            text += "• SMS (پیامک)\n"
            text += "• ایمیل\n"
            text += "• کدهای بازیابی"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🛡 اجبار برای مدیران", callback_data="force_2fa_for_admin"),
                    InlineKeyboardButton("⚙️ اجبار برای محدودها", callback_data="force_2fa_for_limited")
                ],
                [
                    InlineKeyboardButton("👤 تشویق کاربران", callback_data="encourage_2fa_for_users"),
                    InlineKeyboardButton("📱 تنظیم روش‌ها", callback_data="2fa_methods_config")
                ],
                [
                    InlineKeyboardButton("🔄 بازنشانی 2FA", callback_data="reset_user_2fa_menu"),
                    InlineKeyboardButton("🔑 کدهای بازیابی", callback_data="backup_codes_menu")
                ],
                [
                    InlineKeyboardButton("📊 آمار تفصیلی", callback_data="2fa_detailed_stats"),
                    InlineKeyboardButton("📧 ارسال یادآوری", callback_data="send_2fa_reminders")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="security_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_2fa_settings_menu: {e}")
            await self.handle_error(update, context, e)
    
    # === SESSION SETTINGS - Level 2 ===
    
    async def show_session_settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیمات مدیریت session - session_settings"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🗝 **مدیریت Session ها**\n\n"
            text += "⚙️ **تنظیمات فعلی:**\n"
            text += "• حداکثر session همزمان: 3\n"
            text += "• مدت زمان انقضای session: 24 ساعت\n"
            text += "• انقضای خودکار: فعال\n"
            text += "• Remember Me: 30 روز\n\n"
            
            text += "📊 **آمار session های فعال:**\n"
            text += "• کل session های فعال: 1,234\n"
            text += "• session های منقضی امروز: 156\n"
            text += "• میانگین مدت session: 4.2 ساعت\n"
            text += "• session های مشکوک: 7"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔢 حد همزمان", callback_data="max_concurrent_session"),
                    InlineKeyboardButton("⏰ مدت انقضا", callback_data="session_timeout")
                ],
                [
                    InlineKeyboardButton("🔄 انقضای خودکار", callback_data="auto_session_expiry"),
                    InlineKeyboardButton("💭 Remember Me", callback_data="remember_me_settings")
                ],
                [
                    InlineKeyboardButton("🚫 لغو همه session ها", callback_data="revoke_all_sessions"),
                    InlineKeyboardButton("⚠️ session های مشکوک", callback_data="suspicious_sessions")
                ],
                [
                    InlineKeyboardButton("📊 آمار تفصیلی", callback_data="session_detailed_stats"),
                    InlineKeyboardButton("💾 صادرات لاگ", callback_data="export_session_logs")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="security_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_session_settings_menu: {e}")
            await self.handle_error(update, context, e)
    
    # === DEACTIVATE TOKENS - Level 2 ===
    
    async def show_deactivate_tokens_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """غیرفعال‌سازی توکن‌ها - deactivate_tokens"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔒 **غیرفعال‌سازی توکن‌ها**\n\n"
            text += "⚠️ **هشدار:** غیرفعال‌سازی توکن‌ها آن‌ها را غیرقابل‌استفاده می‌کند!\n\n"
            text += "🎯 **روش‌های غیرفعال‌سازی:**\n"
            text += "• **تک توکن:** انتخاب دقیق یک توکن\n"
            text += "• **دسته‌ای:** انتخاب چندین توکن\n"
            text += "• **بر اساس معیار:** منقضی، مشکوک، کاربر خاص\n"
            text += "• **اضطراری:** غیرفعال‌سازی فوری"
            
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
                    InlineKeyboardButton("🚨 حالت اضطراری", callback_data="emergency_deactivation"),
                    InlineKeyboardButton("📋 لیست غیرفعال", callback_data="list_deactivated_tokens")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="security_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_deactivate_tokens_menu: {e}")
            await self.handle_error(update, context, e)
    
    # === SUSPICIOUS ANALYSIS - Level 2 ===
    
    async def show_suspicious_analysis_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بررسی مشکوک - suspicious_analysis"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت آمار فعالیت‌های مشکوک
            result = await self.token_manager.get_suspicious_activity_summary()
            
            text = "⚠️ **تحلیل فعالیت‌های مشکوک**\n\n"
            
            if result.get('success'):
                data = result.get('data', {})
                
                text += "📊 **خلاصه امروز:**\n"
                text += f"• توکن‌های مشکوک: {data.get('suspicious_tokens', 0)}\n"
                text += f"• IP های مشکوک: {data.get('suspicious_ips', 0)}\n"
                text += f"• تلاش‌های ناموفق: {data.get('failed_attempts', 0)}\n"
                text += f"• فعالیت‌های غیرعادی: {data.get('anomalies', 0)}\n\n"
                
                # سطح خطر کلی
                risk_level = data.get('overall_risk_level', 'low')
                risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(risk_level, "🟢")
                risk_text = {"low": "کم", "medium": "متوسط", "high": "بالا"}.get(risk_level, "کم")
                
                text += f"🛡 **سطح خطر کلی:** {risk_emoji} {risk_text}\n\n"
                
                # اقدامات پیشنهادی
                recommendations = data.get('recommendations', [])
                if recommendations:
                    text += "💡 **اقدامات پیشنهادی:**\n"
                    for rec in recommendations[:3]:
                        text += f"• {rec}\n"
            else:
                text += "❌ خطا در دریافت آمار مشکوک\n\n"
            
            text += "\n🔍 **ابزارهای تحلیل:**"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔍 توکن‌های مشکوک", callback_data="inspect_suspicious_tokens"),
                    InlineKeyboardButton("🌐 IP های مشکوک", callback_data="analyze_suspicious_ips")
                ],
                [
                    InlineKeyboardButton("📊 الگوهای حمله", callback_data="attack_patterns_analysis"),
                    InlineKeyboardButton("⏰ تحلیل زمانی", callback_data="temporal_analysis")
                ],
                [
                    InlineKeyboardButton("🔒 اقدام خودکار", callback_data="auto_security_actions"),
                    InlineKeyboardButton("📧 گزارش امنیتی", callback_data="generate_security_report")
                ],
                [
                    InlineKeyboardButton("⚡ حالت دفاعی", callback_data="defensive_mode"),
                    InlineKeyboardButton("🛡 سفت‌کردن امنیت", callback_data="security_hardening")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="security_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_suspicious_analysis_menu: {e}")
            await self.handle_error(update, context, e)
    
    # === CALLBACK HANDLERS FOR PHASE 1 ===
    
    async def handle_set_default_expiry_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback for setting default expiry (set_def_expiry_1, set_def_expiry_7, etc.)"""
        try:
            query = update.callback_query
            callback_data = query.data
            
            # Extract days from callback data
            if callback_data == "set_def_expiry_custom":
                # TODO: Implement custom expiry input via conversation handler
                await query.answer("🚧 ورود سفارشی - در حال توسعه")
                return
            
            # Parse days from callback: set_def_expiry_1 -> 1, set_def_expiry_0 -> 0 (unlimited)
            try:
                days = int(callback_data.split('_')[-1])
            except (IndexError, ValueError):
                await query.answer("❌ خطا در پردازش درخواست!")
                return
            
            await query.answer("در حال ذخیره تنظیمات...")
            
            # Get security manager from database
            if hasattr(self.db, 'security_manager'):
                security_manager = self.db.security_manager
                success = await security_manager.set_default_expiry(days)
                
                if success:
                    if days == 0:
                        expiry_text = "نامحدود"
                    else:
                        expiry_text = f"{days} روز"
                    
                    text = "✅ **تنظیم انقضای پیش‌فرض**\n\n"
                    text += f"⏰ **مدت زمان انقضا:** {expiry_text}\n"
                    text += f"📅 **زمان اعمال:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    text += "این تنظیم برای همه توکن‌های آینده اعمال خواهد شد."
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("🔄 تغییر مجدد", callback_data="set_default_expiry"),
                            InlineKeyboardButton("✅ تایید", callback_data="security_menu")
                        ]
                    ])
                else:
                    text = "❌ **خطا در ذخیره تنظیمات**\n\nلطفاً دوباره تلاش کنید."
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="set_default_expiry")]
                    ])
            else:
                text = "❌ **خطا:** سیستم امنیتی مقداردهی نشده است."
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="security_menu")]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_set_default_expiry_callback: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_set_usage_limit_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback for setting usage limit (limit_100, limit_1k, etc.)"""
        try:
            query = update.callback_query
            callback_data = query.data
            
            # Handle custom limit
            if callback_data == "limit_custom":
                # TODO: Implement custom limit input via conversation handler
                await query.answer("🚧 ورود سفارشی - در حال توسعه")
                return
            
            # Parse limit from callback
            limit_map = {
                'limit_100': 100,
                'limit_500': 500,
                'limit_1k': 1000,
                'limit_5k': 5000,
                'limit_10k': 10000,
                'limit_unlimited': 0
            }
            
            limit = limit_map.get(callback_data)
            if limit is None:
                await query.answer("❌ خطا در پردازش درخواست!")
                return
            
            await query.answer("در حال ذخیره تنظیمات...")
            
            # Get security manager from database
            if hasattr(self.db, 'security_manager'):
                security_manager = self.db.security_manager
                success = await security_manager.set_usage_limit(limit)
                
                if success:
                    if limit == 0:
                        limit_text = "نامحدود"
                    elif limit >= 1000:
                        limit_text = f"{limit // 1000}K"
                    else:
                        limit_text = str(limit)
                    
                    text = "✅ **تنظیم حد استفاده**\n\n"
                    text += f"🔢 **حد استفاده روزانه:** {limit_text}\n"
                    text += f"📅 **زمان اعمال:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    text += "این محدودیت برای همه توکن‌ها اعمال خواهد شد."
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("🔄 تغییر مجدد", callback_data="set_usage_limit"),
                            InlineKeyboardButton("✅ تایید", callback_data="security_menu")
                        ]
                    ])
                else:
                    text = "❌ **خطا در ذخیره تنظیمات**\n\nلطفاً دوباره تلاش کنید."
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="set_usage_limit")]
                    ])
            else:
                text = "❌ **خطا:** سیستم امنیتی مقداردهی نشده است."
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="security_menu")]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_set_usage_limit_callback: {e}")
            await self.handle_error(update, context, e)
    
    # === IP WHITELIST CRUD HANDLERS ===
    
    async def handle_add_single_ip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add single IP to whitelist - requires text input from user"""
        try:
            query = update.callback_query
            await query.answer()
            
            # Store state for conversation handler
            context.user_data['awaiting_ip_input'] = 'single'
            
            text = "📝 **اضافه کردن IP به لیست سفید**\n\n"
            text += "لطفاً IP address یا IP range (CIDR) را وارد کنید:\n\n"
            text += "**مثال‌ها:**\n"
            text += "• `192.168.1.100` (تک IP)\n"
            text += "• `192.168.1.0/24` (محدوده IP)\n"
            text += "• `10.0.0.0/8` (محدوده بزرگ)\n\n"
            text += "برای انصراف، /cancel را ارسال کنید."
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ انصراف", callback_data="manage_whitelist_ip")]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_add_single_ip: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_remove_whitelist_ip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show list of whitelisted IPs for removal"""
        try:
            query = update.callback_query
            await query.answer()
            
            # Get whitelist
            if hasattr(self.db, 'security_manager'):
                security_manager = self.db.security_manager
                whitelist = await security_manager.get_whitelist(active_only=True)
                
                if not whitelist:
                    text = "📝 **لیست سفید IP خالی است**\n\n"
                    text += "هیچ IP ای در لیست سفید وجود ندارد."
                    
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ اضافه کردن IP", callback_data="add_ip_to_whitelist")],
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_whitelist_ip")]
                    ])
                else:
                    text = f"📝 **لیست سفید IP ({len(whitelist)} مورد)**\n\n"
                    text += "برای حذف، روی IP مورد نظر کلیک کنید:\n\n"
                    
                    keyboard_buttons = []
                    for i, entry in enumerate(whitelist[:20]):  # Limit to 20 entries
                        ip_display = entry['ip_address']
                        if entry['description']:
                            ip_display += f" - {entry['description'][:20]}"
                        keyboard_buttons.append([
                            InlineKeyboardButton(
                                f"❌ {ip_display}", 
                                callback_data=f"remove_wl_{entry['id']}"
                            )
                        ])
                    
                    keyboard_buttons.append([
                        InlineKeyboardButton("🔙 بازگشت", callback_data="manage_whitelist_ip")
                    ])
                    
                    keyboard = InlineKeyboardMarkup(keyboard_buttons)
            else:
                text = "❌ **خطا:** سیستم امنیتی مقداردهی نشده است."
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_whitelist_ip")]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_remove_whitelist_ip: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_confirm_remove_whitelist_ip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm and remove IP from whitelist"""
        try:
            query = update.callback_query
            callback_data = query.data
            
            # Extract IP ID: remove_wl_<id>
            whitelist_id = callback_data.replace('remove_wl_', '')
            
            await query.answer("در حال حذف IP...")
            
            if hasattr(self.db, 'security_manager'):
                security_manager = self.db.security_manager
                success = await security_manager.remove_from_whitelist(whitelist_id)
                
                if success:
                    text = "✅ **IP از لیست سفید حذف شد**\n\n"
                    text += f"📅 **زمان حذف:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("📝 مشاهده لیست", callback_data="remove_ip_from_whitelist"),
                            InlineKeyboardButton("✅ تایید", callback_data="manage_whitelist_ip")
                        ]
                    ])
                else:
                    text = "❌ **خطا در حذف IP**\n\nلطفاً دوباره تلاش کنید."
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="remove_ip_from_whitelist")]
                    ])
            else:
                text = "❌ **خطا:** سیستم امنیتی مقداردهی نشده است."
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_whitelist_ip")]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_confirm_remove_whitelist_ip: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_view_whitelist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View all whitelisted IPs"""
        try:
            query = update.callback_query
            await query.answer()
            
            if hasattr(self.db, 'security_manager'):
                security_manager = self.db.security_manager
                whitelist = await security_manager.get_whitelist(active_only=True)
                
                if not whitelist:
                    text = "📝 **لیست سفید IP خالی است**\n\n"
                    text += "هیچ IP ای در لیست سفید وجود ندارد."
                else:
                    text = f"📝 **لیست سفید IP ({len(whitelist)} مورد)**\n\n"
                    
                    for i, entry in enumerate(whitelist[:15], 1):
                        text += f"{i}. **IP:** `{entry['ip_address']}`\n"
                        if entry['description']:
                            text += f"   📝 {entry['description']}\n"
                        text += f"   📅 {entry['created_at'][:16]}\n\n"
                    
                    if len(whitelist) > 15:
                        text += f"\n... و {len(whitelist) - 15} مورد دیگر"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("➕ افزودن", callback_data="add_ip_to_whitelist"),
                        InlineKeyboardButton("❌ حذف", callback_data="remove_ip_from_whitelist")
                    ],
                    [
                        InlineKeyboardButton("🔄 تازه‌سازی", callback_data="view_whitelist"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data="manage_whitelist_ip")
                    ]
                ])
            else:
                text = "❌ **خطا:** سیستم امنیتی مقداردهی نشده است."
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_whitelist_ip")]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_view_whitelist: {e}")
            await self.handle_error(update, context, e)
    
    # === IP RESTRICTION TOGGLE HANDLERS ===
    
    async def handle_enable_ip_restrictions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enable IP restrictions"""
        try:
            query = update.callback_query
            await query.answer("در حال فعال‌سازی...")
            
            if hasattr(self.db, 'security_manager'):
                security_manager = self.db.security_manager
                success = await security_manager.enable_ip_restrictions()
                
                if success:
                    text = "✅ **محدودیت‌های IP فعال شد**\n\n"
                    text += "🔒 از این پس، تنها IP های موجود در لیست سفید می‌توانند دسترسی داشته باشند.\n\n"
                    text += f"📅 **زمان فعال‌سازی:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("📝 مدیریت لیست سفید", callback_data="manage_whitelist_ip"),
                            InlineKeyboardButton("✅ تایید", callback_data="ip_restrictions")
                        ]
                    ])
                else:
                    text = "❌ **خطا در فعال‌سازی**\n\nلطفاً دوباره تلاش کنید."
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="ip_restrictions")]
                    ])
            else:
                text = "❌ **خطا:** سیستم امنیتی مقداردهی نشده است."
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="ip_restrictions")]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_enable_ip_restrictions: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_disable_ip_restrictions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Disable IP restrictions"""
        try:
            query = update.callback_query
            await query.answer("در حال غیرفعال‌سازی...")
            
            if hasattr(self.db, 'security_manager'):
                security_manager = self.db.security_manager
                success = await security_manager.disable_ip_restrictions()
                
                if success:
                    text = "❌ **محدودیت‌های IP غیرفعال شد**\n\n"
                    text += "🔓 همه IP ها می‌توانند دسترسی داشته باشند (به جز IP های blacklist).\n\n"
                    text += f"📅 **زمان غیرفعال‌سازی:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("🟢 فعال‌سازی مجدد", callback_data="enable_ip_restrictions"),
                            InlineKeyboardButton("✅ تایید", callback_data="ip_restrictions")
                        ]
                    ])
                else:
                    text = "❌ **خطا در غیرفعال‌سازی**\n\nلطفاً دوباره تلاش کنید."
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="ip_restrictions")]
                    ])
            else:
                text = "❌ **خطا:** سیستم امنیتی مقداردهی نشده است."
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="ip_restrictions")]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_disable_ip_restrictions: {e}")

    # === BLACKLIST MANAGEMENT ===
    async def show_manage_blacklist_ip_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت لیست سیاه IP - manage_blacklist_ip"""
        try:
            query = update.callback_query
            await query.answer()

            text = "❌ **مدیریت لیست سیاه IP**\n\n"
            if hasattr(self.db, 'security_manager'):
                sm = self.db.security_manager
                bl = await sm.get_blacklist(active_only=True)
                count = len(bl)
                text += f"📊 **تعداد IP های مسدود:** {count}\n\n"
                if bl:
                    text += "🚫 **IP های مسدود اخیر:**\n"
                    for i, ip in enumerate(bl[:5], 1):
                        ip_disp = ip.get('ip_address', 'نامشخص')
                        reason = ip.get('reason') or 'بدون دلیل'
                        text += f"{i}. `{ip_disp}` - {reason}\n"
                    if count > 5:
                        text += f"... و {count-5} مورد دیگر\n\n"
                else:
                    text += "✅ در حال حاضر هیچ IP ای در لیست سیاه وجود ندارد.\n\n"
            else:
                text += "❌ خطا: سیستم امنیتی مقداردهی نشده است\n\n"

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("➕ افزودن IP تکی", callback_data="add_single_ip_blacklist"),
                    InlineKeyboardButton("📊 افزودن محدوده", callback_data="add_ip_range_blacklist")
                ],
                [
                    InlineKeyboardButton("📋 مشاهده لیست", callback_data="view_blacklist"),
                    InlineKeyboardButton("🗑 حذف IP", callback_data="remove_blacklist_ip")
                ],
                [
                    InlineKeyboardButton("📥 واردات CSV", callback_data="import_blacklist_csv"),
                    InlineKeyboardButton("📤 صادرات لیست", callback_data="export_blacklist")
                ],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="ip_restrictions")]
            ])

            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in show_manage_blacklist_ip_menu: {e}")
            await self.handle_error(update, context, e)

    async def handle_add_single_ip_blacklist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """درخواست ورودی برای اضافه کردن IP تکی به لیست سیاه"""
        try:
            query = update.callback_query
            await query.answer()

            context.user_data['awaiting_blacklist_ip_input'] = 'single'

            text = (
                "➕ **افزودن IP به لیست سیاه**\n\n"
                "لطفاً IP یا محدوده (CIDR) را ارسال کنید.\n\n"
                "مثال‌ها:\n"
                "• 203.0.113.25\n"
                "• 203.0.113.0/24\n\n"
                "برای انصراف، /cancel را ارسال کنید."
            )
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="manage_blacklist_ip")]])
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_add_single_ip_blacklist: {e}")
            await self.handle_error(update, context, e)

    async def handle_add_ip_range_blacklist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """راهنمای افزودن محدوده IP به لیست سیاه"""
        try:
            query = update.callback_query
            await query.answer()

            context.user_data['awaiting_blacklist_ip_input'] = 'range'

            text = (
                "📊 **افزودن محدوده IP به لیست سیاه**\n\n"
                "لطفاً محدوده را با فرمت CIDR ارسال کنید (مانند 203.0.113.0/24).\n\n"
                "برای انصراف، /cancel را ارسال کنید."
            )
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="manage_blacklist_ip")]])
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_add_ip_range_blacklist: {e}")
            await self.handle_error(update, context, e)

    async def handle_view_blacklist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش لیست سیاه"""
        try:
            query = update.callback_query
            await query.answer()
            if hasattr(self.db, 'security_manager'):
                sm = self.db.security_manager
                bl = await sm.get_blacklist(active_only=True)
                if not bl:
                    text = "❌ **لیست سیاه خالی است**\n\nابتدا IP اضافه کنید."
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("➕ افزودن IP", callback_data="add_single_ip_blacklist"), InlineKeyboardButton("🔙 بازگشت", callback_data="manage_blacklist_ip")]])
                else:
                    text = f"❌ **لیست سیاه IP ({len(bl)} مورد)**\n\n"
                    buttons = []
                    for i, entry in enumerate(bl[:15], 1):
                        ip_disp = entry.get('ip_address', 'نامشخص')
                        reason = entry.get('reason') or 'بدون دلیل'
                        text += f"{i}. `{ip_disp}` - {reason}\n"
                        buttons.append([InlineKeyboardButton(f"🗑 حذف {ip_disp}", callback_data=f"remove_bl_{entry['id']}")])
                    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="manage_blacklist_ip")])
                    keyboard = InlineKeyboardMarkup(buttons)
            else:
                text = "❌ **خطا:** سیستم امنیتی مقداردهی نشده است."
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="manage_blacklist_ip")]])
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_view_blacklist: {e}")
            await self.handle_error(update, context, e)

    async def handle_remove_blacklist_ip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش لیست برای حذف از لیست سیاه"""
        try:
            query = update.callback_query
            await query.answer()
            if hasattr(self.db, 'security_manager'):
                sm = self.db.security_manager
                bl = await sm.get_blacklist(active_only=True)
                if not bl:
                    text = "✅ هیچ IP مسدودی وجود ندارد."
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="manage_blacklist_ip")]])
                else:
                    text = "🗑 **حذف از لیست سیاه**\n\nروی مورد دلخواه کلیک کنید:\n"
                    buttons = []
                    for entry in bl[:20]:
                        ip_disp = entry.get('ip_address', 'نامشخص')
                        buttons.append([InlineKeyboardButton(f"🗑 حذف {ip_disp}", callback_data=f"remove_bl_{entry['id']}")])
                    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="manage_blacklist_ip")])
                    keyboard = InlineKeyboardMarkup(buttons)
            else:
                text = "❌ **خطا:** سیستم امنیتی مقداردهی نشده است."
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="manage_blacklist_ip")]])
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_remove_blacklist_ip: {e}")
            await self.handle_error(update, context, e)

    async def handle_confirm_remove_blacklist_ip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف نهایی IP از لیست سیاه"""
        try:
            query = update.callback_query
            await query.answer("در حال حذف IP...")
            blacklist_id = query.data.replace('remove_bl_', '')
            if hasattr(self.db, 'security_manager'):
                sm = self.db.security_manager
                ok = await sm.remove_from_blacklist(blacklist_id)
                if ok:
                    text = "✅ IP از لیست سیاه حذف شد"
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="manage_blacklist_ip")]])
                else:
                    text = "❌ خطا در حذف IP"
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="remove_blacklist_ip")]])
            else:
                text = "❌ **خطا:** سیستم امنیتی مقداردهی نشده است."
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="manage_blacklist_ip")]])
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_confirm_remove_blacklist_ip: {e}")
            await self.handle_error(update, context, e)

    async def show_import_blacklist_csv_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش راهنمای واردات CSV لیست سیاه"""
        try:
            query = update.callback_query
            await query.answer()
            text = (
                "📥 **واردات لیست سیاه از CSV**\n\n"
                "فرمت نمونه:\n"
                "`````\n"
                "ip,reason,active\n"
                "203.0.113.25,اسکن پورت,false\n"
                "203.0.113.0/24,سوءاستفاده از API,true\n"
                "`````\n\n"
                "حداکثر 1000 ردیف، اندازه فایل < 1MB."
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📁 آپلود فایل CSV", callback_data="select_blacklist_csv"), InlineKeyboardButton("📝 نمونه CSV", callback_data="download_blacklist_csv_template")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_blacklist_ip")]
            ])
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in show_import_blacklist_csv_menu: {e}")
            await self.handle_error(update, context, e)

    async def handle_export_blacklist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """صادرات لیست سیاه (نمایش JSON کوتاه)"""
        try:
            query = update.callback_query
            await query.answer()
            if hasattr(self.db, 'security_manager'):
                sm = self.db.security_manager
                bl = await sm.get_blacklist(active_only=True)
                export_data = [{
                    'ip': e.get('ip_address'),
                    'range': e.get('ip_range'),
                    'reason': e.get('reason'),
                    'blocked_at': e.get('blocked_at')
                } for e in bl]
                text = "📤 **صادرات لیست سیاه (JSON پیش‌نمایش)**\n\n"
                preview = json.dumps(export_data[:10], ensure_ascii=False, indent=2)
                if len(export_data) > 10:
                    text += f"نمایش 10 مورد از {len(export_data)} رکورد:\n"
                text += f"````\n{preview}\n````"
            else:
                text = "❌ **خطا:** سیستم امنیتی مقداردهی نشده است."
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="manage_blacklist_ip")]])
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_export_blacklist: {e}")
            await self.handle_error(update, context, e)

    async def handle_import_blacklist_csv_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش فایل CSV ارسالی و درج دسته‌ای در blacklist (مینیمال)"""
        try:
            message = update.message or (update.edited_message if hasattr(update, 'edited_message') else None)
            if not message or not message.document:
                return False
            file = await message.document.get_file()
            content = await file.download_as_bytearray()
            text_data = content.decode('utf-8', errors='ignore')
            f = StringIO(text_data)
            reader = csv.DictReader(f)
            added, failed = 0, 0
            if hasattr(self.db, 'security_manager'):
                sm = self.db.security_manager
                for row in reader:
                    ip = (row.get('ip') or row.get('ip_address') or '').strip()
                    reason = (row.get('reason') or '').strip() or None
                    active_str = (row.get('active') or 'true').strip().lower()
                    is_active = active_str in ['1','true','yes','y']
                    if not ip:
                        failed += 1
                        continue
                    bl_id = await sm.add_to_blacklist(ip, reason=reason, blocked_by=update.effective_user.id if update.effective_user else None)
                    if bl_id:
                        if not is_active:
                            # اگر نیاز به غیرفعال‌سازی داریم، می‌توانیم یک فیلد is_active را با متد جداگانه آپدیت کنیم؛ فعلاً نادیده گرفته می‌شود
                            pass
                        added += 1
                    else:
                        failed += 1
            await message.reply_text(f"📥 واردات CSV پایان یافت. موفق: {added} | ناموفق: {failed}")
            return True
        except Exception as e:
            logger.error(f"Error in handle_import_blacklist_csv_file: {e}")
            if update.message:
                await update.message.reply_text("❌ خطا در پردازش CSV")
            return False

    # === SECURITY ALERT CHANNEL TOGGLES ===
    async def handle_email_alerts_toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._toggle_alert_channel(update, context, key='alert_email_enabled', label='ایمیل')

    async def handle_telegram_alerts_toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._toggle_alert_channel(update, context, key='alert_telegram_enabled', label='تلگرام')

    async def handle_webhook_alerts_toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._toggle_alert_channel(update, context, key='alert_webhook_enabled', label='Webhook')

    async def handle_sms_alerts_toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._toggle_alert_channel(update, context, key='alert_sms_enabled', label='SMS')

    async def _toggle_alert_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE, key: str, label: str):
        try:
            query = update.callback_query
            await query.answer()
            if not hasattr(self.db, 'security_manager'):
                await query.edit_message_text("❌ سیستم امنیتی مقداردهی نشده است", parse_mode='Markdown')
                return
            sm = self.db.security_manager
            cur = await sm.get_setting(key)
            new_val = 'false' if (cur == 'true') else 'true'
            ok = await sm.set_setting(key, new_val, f'{label} alerts toggle')
            # نمایش وضعیت به صورت toast و بازگشت به منو
            try:
                await query.answer("✅ تغییرات اعمال شد" if ok else "❌ خطا در تغییر وضعیت", show_alert=False)
            except Exception:
                pass
            await self.show_security_alerts_menu(update, context)
        except Exception as e:
            logger.error(f"Error toggling alert channel {label}: {e}")
            await self.handle_error(update, context, e)

    # === ALERT HISTORY ===
    async def show_alert_history_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش تاریخچه هشدارها"""
        try:
            query = update.callback_query
            await query.answer()
            page = int(query.data.split('_')[-1]) if query.data.startswith('alert_history_page_') else 1
            per_page = 10
            if not hasattr(self.db, 'security_manager'):
                await query.edit_message_text("❌ سیستم امنیتی مقداردهی نشده است", parse_mode='Markdown')
                return
            sm = self.db.security_manager
            alerts = await sm.get_alerts(unread_only=False, limit=100)
            total = len(alerts)
            start = (page - 1) * per_page
            end = start + per_page
            page_items = alerts[start:end]

            text = "📜 **تاریخچه هشدارها**\n\n"
            if not page_items:
                text += "هیچ هشداری یافت نشد.\n"
            else:
                for a in page_items:
                    status = '🟡 جدید' if a.get('is_read') == 0 else '⚪️ خوانده شده'
                    text += f"• {status} [{a.get('severity','medium')}] {a.get('alert_type','alert')} - {a.get('message','')}\n"
                    text += f"  🕐 {a.get('created_at','')[:16]}  |  ID: `{a.get('id')}`\n"
            # Pagination & actions
            buttons = []
            nav = []
            if page > 1:
                nav.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"alert_history_page_{page-1}"))
            if end < total:
                nav.append(InlineKeyboardButton("بعدی ➡️", callback_data=f"alert_history_page_{page+1}"))
            if nav:
                buttons.append(nav)
            buttons.extend([
                [InlineKeyboardButton("✅ علامت خوانده شد (همه)", callback_data="mark_all_as_read"), InlineKeyboardButton("🗑 پاکسازی قدیمی‌ها", callback_data="clear_history")],
                [InlineKeyboardButton("📄 خروجی JSON", callback_data="export_alerts_json"), InlineKeyboardButton("📊 خروجی CSV", callback_data="export_alerts_csv")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="security_alerts")]
            ])
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in show_alert_history_menu: {e}")
            await self.handle_error(update, context, e)

    async def handle_mark_alert_as_read(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """علامت خوانده شده برای یک هشدار"""
        try:
            query = update.callback_query
            await query.answer("در حال بروز رسانی...")
            alert_id = query.data.replace('mark_as_read_', '')
            if hasattr(self.db, 'security_manager'):
                await self.db.security_manager.mark_alert_as_read(alert_id)
            await self.show_alert_history_menu(update, context)
        except Exception as e:
            logger.error(f"Error in handle_mark_alert_as_read: {e}")
            await self.handle_error(update, context, e)

    async def handle_mark_all_alerts_as_read(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer("علامت‌گذاری همه ...")
            if hasattr(self.db, 'security_manager'):
                alerts = await self.db.security_manager.get_alerts(unread_only=True, limit=200)
                for a in alerts:
                    await self.db.security_manager.mark_alert_as_read(a['id'])
            await self.show_alert_history_menu(update, context)
        except Exception as e:
            logger.error(f"Error in handle_mark_all_alerts_as_read: {e}")
            await self.handle_error(update, context, e)

    async def handle_clear_alert_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer("در حال پاکسازی...")
            if hasattr(self.db, 'security_manager'):
                await self.db.security_manager.clear_old_alerts(days=0)
            await self.show_alert_history_menu(update, context)
        except Exception as e:
            logger.error(f"Error in handle_clear_alert_history: {e}")
            await self.handle_error(update, context, e)

    async def handle_export_alerts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            fmt = 'json' if query.data.endswith('_json') else 'csv'
            await query.answer()
            if not hasattr(self.db, 'security_manager'):
                await query.edit_message_text("❌ سیستم امنیتی مقداردهی نشده است", parse_mode='Markdown')
                return
            alerts = await self.db.security_manager.get_alerts(unread_only=False, limit=200)
            if fmt == 'json':
                payload = json.dumps(alerts, ensure_ascii=False, indent=2)
                text = f"📄 **خروجی JSON هشدارها (پیش‌نمایش)**\n\n````\n{payload[:3500]}\n````"
            else:
                # CSV simple string
                rows = ["id,alert_type,severity,message,created_at,is_read"]
                for a in alerts:
                    line = f"{a.get('id')},{a.get('alert_type')},{a.get('severity')},\"{(a.get('message') or '').replace(',', ' ')}\",{a.get('created_at')},{a.get('is_read')}"
                    rows.append(line)
                csv_text = "\n".join(rows)
                text = f"📊 **خروجی CSV هشدارها (پیش‌نمایش)**\n\n````\n{csv_text[:3500]}\n````"
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="alert_history")]])
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in handle_export_alerts: {e}")
            await self.handle_error(update, context, e)

    # === THRESHOLDS ===
    async def show_threshold_quota_limit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()
            text = (
                "📊 **آستانه هشدار سهمیه (Quota)**\n\n"
                "حد هشدار را انتخاب کنید:"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("80%", callback_data="set_quota_threshold_80"), InlineKeyboardButton("90%", callback_data="set_quota_threshold_90")],
                [InlineKeyboardButton("95%", callback_data="set_quota_threshold_95"), InlineKeyboardButton("🎯 سفارشی", callback_data="set_quota_threshold_custom")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="alert_settings")]
            ])
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in show_threshold_quota_limit_menu: {e}")
            await self.handle_error(update, context, e)

    async def handle_set_login_threshold(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer("در حال ذخیره...")
            mapping = {
                'set_login_threshold_3_5': '3/5',
                'set_login_threshold_5_10': '5/10',
                'set_login_threshold_10_15': '10/15',
                'set_login_threshold_20_30': '20/30',
                'disable_login_threshold': 'disabled'
            }
            val = mapping.get(query.data)
            if not val and query.data == 'custom_login_threshold':
                # Not implemented conversation yet
                await query.answer("🚧 سفارشی - در حال توسعه")
                return
            if not hasattr(self.db, 'security_manager'):
                await query.edit_message_text("❌ سیستم امنیتی مقداردهی نشده است", parse_mode='Markdown')
                return
            await self.db.security_manager.set_setting('threshold_failed_login', val or '5/10', 'Failed login alert threshold')
            await self.show_alert_settings_menu(update, context)
        except Exception as e:
            logger.error(f"Error in handle_set_login_threshold: {e}")
            await self.handle_error(update, context, e)

    async def handle_set_quota_threshold(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer("در حال ذخیره...")
            mapping = {
                'set_quota_threshold_80': '80',
                'set_quota_threshold_90': '90',
                'set_quota_threshold_95': '95'
            }
            if query.data == 'set_quota_threshold_custom':
                await query.answer("🚧 سفارشی - در حال توسعه")
                return
            val = mapping.get(query.data, '90')
            if hasattr(self.db, 'security_manager'):
                await self.db.security_manager.set_setting('threshold_quota_limit', val, 'Quota usage alert threshold')
            await self.show_alert_settings_menu(update, context)
        except Exception as e:
            logger.error(f"Error in handle_set_quota_threshold: {e}")
            await self.handle_error(update, context, e)

    async def handle_disable_all_alerts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()
            if hasattr(self.db, 'security_manager'):
                sm = self.db.security_manager
                for k in ['alert_email_enabled','alert_telegram_enabled','alert_webhook_enabled','alert_sms_enabled']:
                    await sm.set_setting(k, 'false', 'Disable all alerts')
            await self.show_security_alerts_menu(update, context)
        except Exception as e:
            logger.error(f"Error in handle_disable_all_alerts: {e}")
            await self.handle_error(update, context, e)

    async def handle_enable_all_alerts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()
            if hasattr(self.db, 'security_manager'):
                sm = self.db.security_manager
                for k in ['alert_email_enabled','alert_telegram_enabled','alert_webhook_enabled','alert_sms_enabled']:
                    await sm.set_setting(k, 'true', 'Enable all alerts')
            await self.show_security_alerts_menu(update, context)
        except Exception as e:
            logger.error(f"Error in handle_enable_all_alerts: {e}")
            await self.handle_error(update, context, e)

    async def handle_toggle_geo_anomaly(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()
            if hasattr(self.db, 'security_manager'):
                sm = self.db.security_manager
                cur = await sm.get_setting('threshold_geo_anomaly')
                new_val = 'false' if (cur == 'true') else 'true'
                await sm.set_setting('threshold_geo_anomaly', new_val, 'Geo anomaly alerts')
            await self.show_alert_settings_menu(update, context)
        except Exception as e:
            logger.error(f"Error in handle_toggle_geo_anomaly: {e}")
            await self.handle_error(update, context, e)

    async def handle_toggle_time_anomaly(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()
            if hasattr(self.db, 'security_manager'):
                sm = self.db.security_manager
                cur = await sm.get_setting('threshold_time_anomaly')
                new_val = 'false' if (cur == 'true') else 'true'
                await sm.set_setting('threshold_time_anomaly', new_val, 'Time anomaly alerts')
            await self.show_alert_settings_menu(update, context)
        except Exception as e:
            logger.error(f"Error in handle_toggle_time_anomaly: {e}")
            await self.handle_error(update, context, e)

            await self.handle_error(update, context, e)
            await self.handle_error(update, context, e)