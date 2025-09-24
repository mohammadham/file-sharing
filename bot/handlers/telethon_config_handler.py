#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telethon Configuration Management Handler
هندلر مدیریت کانفیگ‌های Telethon در ربات تلگرام
"""

import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from pathlib import Path

from handlers.base_handler import BaseHandler
from utils.keyboard_builder import KeyboardBuilder

logger = logging.getLogger(__name__)


class TelethonConfigHandler(BaseHandler):
    """مدیریت کانفیگ‌های Telethon از طریق ربات تلگرام"""
    
    def __init__(self, db):
        super().__init__(db)
    
    async def show_telethon_management_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی مدیریت Telethon"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            text = "🔧 **مدیریت سیستم Telethon**\n\n"
            text += "در این بخش می‌توانید کانفیگ‌های Telethon را مدیریت کنید:\n\n"
            text += "📋 **عملیات موجود:**\n"
            text += "• مشاهده کانفیگ‌های موجود\n"
            text += "• افزودن کانفیگ جدید از فایل JSON\n"
            text += "• ورود به اکانت تلگرام\n"
            text += "• تست وضعیت کلاینت‌ها\n"
            text += "• مدیریت session ها\n\n"
            text += "💡 **نکته:** برای استفاده از سیستم دانلود پیشرفته، نیاز به حداقل یک کانفیگ فعال دارید."
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📋 مشاهده کانفیگ‌ها", callback_data="telethon_list_configs"),
                    InlineKeyboardButton("➕ افزودن کانفیگ", callback_data="telethon_add_config")
                ],
                [
                    InlineKeyboardButton("🔐 ورود به اکانت", callback_data="telethon_login_menu"),
                    InlineKeyboardButton("🩺 تست کلاینت‌ها", callback_data="telethon_health_check")
                ],
                [
                    InlineKeyboardButton("⚙️ تنظیمات پیشرفته", callback_data="telethon_advanced_settings"),
                    InlineKeyboardButton("📊 وضعیت سیستم", callback_data="telethon_system_status")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="download_system_control")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def show_config_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش لیست کانفیگ‌های موجود"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            # دریافت لیست کانفیگ‌ها از سیستم دانلود
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            
            telethon_manager = AdvancedTelethonClientManager()
            configs = telethon_manager.config_manager.list_configs()
            
            text = "📋 **کانفیگ‌های Telethon موجود**\n\n"
            
            if configs:
                for i, (config_name, config_info) in enumerate(configs.items(), 1):
                    status_icon = "🟢" if config_info.get('is_active') else "🔴"
                    session_icon = "🔗" if config_info.get('has_session') else "❌"
                    
                    text += f"{i}. **{config_name}** {status_icon}\n"
                    text += f"   📱 شماره: {config_info.get('phone', 'نامشخص')}\n"
                    text += f"   🆔 API ID: {config_info.get('api_id', 'نامشخص')}\n"
                    text += f"   {session_icon} Session: {'دارد' if config_info.get('has_session') else 'ندارد'}\n"
                    text += f"   📅 ایجاد: {config_info.get('created_at', 'نامشخص')[:16]}\n\n"
                
                text += f"📊 **آمار:** {len(configs)} کانفیگ موجود"
            else:
                text += "❌ **هیچ کانفیگی یافت نشد**\n\n"
                text += "💡 **راهنما:**\n"
                text += "• برای شروع، یک کانفیگ JSON اضافه کنید\n"
                text += "• کانفیگ باید شامل api_id و api_hash باشد\n"
                text += "• می‌توانید از منوی 'افزودن کانفیگ' استفاده کنید"
            
            keyboard_rows = []
            
            if configs:
                # دکمه‌های مدیریت برای هر کانفیگ (نمایش 3 کانفیگ اول)
                for config_name in list(configs.keys())[:3]:
                    keyboard_rows.append([
                        InlineKeyboardButton(
                            f"🔧 {config_name[:15]}", 
                            callback_data=f"telethon_manage_config_{config_name}"
                        ),
                        InlineKeyboardButton(
                            f"🗑 حذف {config_name[:10]}", 
                            callback_data=f"telethon_delete_config_{config_name}"
                        )
                    ])
            
            keyboard_rows.extend([
                [
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data="telethon_list_configs"),
                    InlineKeyboardButton("➕ افزودن جدید", callback_data="telethon_add_config")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
                ]
            ])
            
            keyboard = InlineKeyboardMarkup(keyboard_rows)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def show_add_config_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی افزودن کانفیگ"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            user_id = update.effective_user.id
            
            text = "➕ **افزودن کانفیگ Telethon**\n\n"
            text += "🔧 **روش‌های افزودن کانفیگ:**\n\n"
            text += "**۱. فایل JSON:**\n"
            text += "• فایل JSON خود را ارسال کنید\n"
            text += "• فرمت مورد نیاز:\n"
            text += "```json\n"
            text += "{\n"
            text += "  \"api_id\": 123456,\n"
            text += "  \"api_hash\": \"your_api_hash\",\n"
            text += "  \"name\": \"my_config\",\n"
            text += "  \"phone\": \"+1234567890\"\n"
            text += "}\n"
            text += "```\n\n"
            text += "**۲. ایجاد دستی:**\n"
            text += "• وارد کردن اطلاعات به صورت تعاملی\n\n"
            text += "💡 **نکات مهم:**\n"
            text += "• API ID و API Hash را از my.telegram.org دریافت کنید\n"
            text += "• فایل JSON باید معتبر باشد\n"
            text += "• نام کانفیگ باید منحصر به فرد باشد"
            
            # ذخیره وضعیت کاربر
            await self.db.update_user_session(
                user_id,
                action_state='adding_telethon_config',
                temp_data=json.dumps({'step': 'choose_method'})
            )
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📁 آپلود فایل JSON", callback_data="telethon_upload_json"),
                    InlineKeyboardButton("✏️ ایجاد دستی", callback_data="telethon_manual_create")
                ],
                [
                    InlineKeyboardButton("📋 مثال فایل JSON", callback_data="telethon_show_json_example"),
                ],
                [
                    InlineKeyboardButton("❌ لغو", callback_data="telethon_list_configs")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def show_json_example(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش مثال فایل JSON"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            text = "📋 **مثال فایل کانفیگ JSON**\n\n"
            text += "برای ایجاد فایل کانفیگ، از فرمت زیر استفاده کنید:\n\n"
            text += "```json\n"
            text += "{\n"
            text += "  \"api_id\": 123456,\n"
            text += "  \"api_hash\": \"abcdef1234567890abcdef1234567890\",\n"
            text += "  \"name\": \"my_download_client\",\n"
            text += "  \"phone\": \"+1234567890\",\n"
            text += "  \"device_model\": \"Download System\",\n"
            text += "  \"system_version\": \"1.0\",\n"
            text += "  \"app_version\": \"1.0.0\",\n"
            text += "  \"lang_code\": \"fa\",\n"
            text += "  \"is_active\": true\n"
            text += "}\n"
            text += "```\n\n"
            text += "🔑 **فیلدهای ضروری:**\n"
            text += "• `api_id`: شناسه API (عدد)\n"
            text += "• `api_hash`: هش API (رشته)\n\n"
            text += "🔧 **فیلدهای اختیاری:**\n"
            text += "• `name`: نام کانفیگ\n"
            text += "• `phone`: شماره تلفن\n"
            text += "• `device_model`: مدل دستگاه\n"
            text += "• سایر تنظیمات کلاینت\n\n"
            text += "⚠️ **نکات امنیتی:**\n"
            text += "• هرگز کانفیگ خود را با دیگران به اشتراک نگذارید\n"
            text += "• API Hash محرمانه است و باید محافظت شود"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🌐 دریافت API Keys", url="https://my.telegram.org/"),
                ],
                [
                    InlineKeyboardButton("📁 آپلود فایل", callback_data="telethon_upload_json"),
                    InlineKeyboardButton("✏️ ایجاد دستی", callback_data="telethon_manual_create")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_add_config")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def start_json_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع آپلود فایل JSON"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            user_id = update.effective_user.id
            
            # بروزرسانی وضعیت کاربر
            await self.db.update_user_session(
                user_id,
                action_state='uploading_telethon_config',
                temp_data=json.dumps({'step': 'waiting_for_file'})
            )
            
            text = "📁 **آپلود فایل کانفیگ JSON**\n\n"
            text += "لطفاً فایل JSON کانفیگ Telethon خود را ارسال کنید.\n\n"
            text += "🔧 **راهنما:**\n"
            text += "• فایل باید پسوند .json داشته باشد\n"
            text += "• حداکثر اندازه: 1 مگابایت\n"
            text += "• فرمت JSON باید معتبر باشد\n"
            text += "• api_id و api_hash الزامی هستند\n\n"
            text += "⏱ **منتظر دریافت فایل JSON...**"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📋 مشاهده مثال", callback_data="telethon_show_json_example")
                ],
                [
                    InlineKeyboardButton("❌ لغو", callback_data="telethon_add_config")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def handle_config_file_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش فایل کانفیگ آپلود شده"""
        try:
            user_id = update.effective_user.id
            session = await self.db.get_user_session(user_id)
            
            # بررسی وضعیت کاربر
            if session.get('action_state') != 'uploading_telethon_config':
                return
            
            # بررسی فایل
            if not update.message.document:
                await update.message.reply_text(
                    "❌ لطفاً یک فایل ارسال کنید."
                )
                return
            
            file = update.message.document
            
            # بررسی نوع فایل
            if not file.file_name.endswith('.json'):
                await update.message.reply_text(
                    "❌ فایل باید پسوند .json داشته باشد."
                )
                return
            
            # بررسی اندازه فایل
            if file.file_size > 1024 * 1024:  # 1MB
                await update.message.reply_text(
                    "❌ حداکثر اندازه فایل 1 مگابایت است."
                )
                return
            
            # دانلود و پردازش فایل
            file_obj = await context.bot.get_file(file.file_id)
            file_content = await file_obj.download_as_bytearray()
            
            try:
                # تجزیه JSON
                config_data = json.loads(file_content.decode('utf-8'))
                
                # اعتبارسنجی کانفیگ
                if not isinstance(config_data, dict):
                    raise ValueError("Config must be a JSON object")
                
                if 'api_id' not in config_data or 'api_hash' not in config_data:
                    raise ValueError("api_id and api_hash are required")
                
                # تعیین نام کانفیگ
                config_name = config_data.get('name', file.file_name.replace('.json', ''))
                
                # اضافه کردن کانفیگ
                from download_system.core.telethon_manager import AdvancedTelethonClientManager
                
                telethon_manager = AdvancedTelethonClientManager()
                success = telethon_manager.config_manager.save_config(config_name, config_data)
                
                if success:
                    # ریست وضعیت کاربر
                    await self.db.update_user_session(
                        user_id,
                        action_state='browsing',
                        temp_data=None
                    )
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("🔐 ورود به اکانت", callback_data=f"telethon_login_{config_name}"),
                            InlineKeyboardButton("📋 مشاهده کانفیگ‌ها", callback_data="telethon_list_configs")
                        ],
                        [
                            InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")
                        ]
                    ])
                    
                    await update.message.reply_text(
                        f"✅ **کانفیگ '{config_name}' با موفقیت اضافه شد!**\n\n"
                        f"🔧 **مشخصات:**\n"
                        f"• API ID: {config_data.get('api_id')}\n"
                        f"• نام: {config_name}\n"
                        f"• شماره: {config_data.get('phone', 'نامشخص')}\n\n"
                        f"💡 **مرحله بعد:** برای استفاده از این کانفیگ، ابتدا وارد اکانت تلگرام شوید.",
                        reply_markup=keyboard,
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(
                        "❌ خطا در ذخیره کانفیگ. لطفاً دوباره تلاش کنید."
                    )
                
            except json.JSONDecodeError:
                await update.message.reply_text(
                    "❌ فایل JSON نامعتبر است. لطفاً فرمت را بررسی کنید."
                )
            except ValueError as e:
                await update.message.reply_text(
                    f"❌ خطا در اعتبارسنجی: {str(e)}"
                )
            except Exception as e:
                logger.error(f"Error processing config file: {e}")
                await update.message.reply_text(
                    "❌ خطا در پردازش فایل. لطفاً دوباره تلاش کنید."
                )
                
        except Exception as e:
            await self.handle_error(update, context, e)