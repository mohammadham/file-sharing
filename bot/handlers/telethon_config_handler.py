#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telethon Configuration Management Handler
هندلر مدیریت کانفیگ‌های Telethon در ربات تلگرام
"""

import json
import logging
import re
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
            try:
                import sys
                sys.path.append('/app')
                from download_system.core.telethon_manager import AdvancedTelethonClientManager
                
                telethon_manager = AdvancedTelethonClientManager()
                configs = telethon_manager.config_manager.list_configs()
            except Exception as e:
                logger.error(f"Error accessing telethon manager: {e}")
                configs = {}
            
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
    
    async def manage_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت کانفیگ خاص"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            # استخراج نام کانفیگ از callback_data
            callback_data = query.data
            config_name = callback_data.replace('telethon_manage_config_', '')
            
            # دریافت اطلاعات کانفیگ
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            
            telethon_manager = AdvancedTelethonClientManager()
            configs = telethon_manager.config_manager.list_configs()
            
            if config_name not in configs:
                await query.edit_message_text(
                    f"❌ کانفیگ '{config_name}' یافت نشد.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_list_configs")
                    ]])
                )
                return
            
            config_info = configs[config_name]
            status_icon = "🟢" if config_info.get('is_active') else "🔴"
            session_icon = "🔗" if config_info.get('has_session') else "❌"
            
            text = f"🔧 **مدیریت کانفیگ: {config_name}**\n\n"
            text += f"📊 **وضعیت:** {status_icon} {'فعال' if config_info.get('is_active') else 'غیرفعال'}\n"
            text += f"📱 **شماره:** {config_info.get('phone', 'نامشخص')}\n"
            text += f"🆔 **API ID:** {config_info.get('api_id', 'نامشخص')}\n"
            text += f"{session_icon} **Session:** {'دارد' if config_info.get('has_session') else 'ندارد'}\n"
            text += f"📅 **ایجاد:** {config_info.get('created_at', 'نامشخص')[:16]}\n\n"
            text += "⚙️ **عملیات موجود:**"
            
            keyboard_rows = []
            
            # دکمه‌های مدیریت
            if config_info.get('has_session'):
                keyboard_rows.append([
                    InlineKeyboardButton("🩺 تست کلاینت", callback_data=f"telethon_test_client_{config_name}"),
                    InlineKeyboardButton("🔄 بازنشانی Session", callback_data=f"telethon_reset_session_{config_name}")
                ])
            else:
                keyboard_rows.append([
                    InlineKeyboardButton("🔐 ورود به اکانت", callback_data=f"telethon_login_{config_name}")
                ])
            
            keyboard_rows.extend([
                [
                    InlineKeyboardButton("📝 ویرایش کانفیگ", callback_data=f"telethon_edit_config_{config_name}"),
                    InlineKeyboardButton("📋 مشاهده جزئیات", callback_data=f"telethon_view_config_{config_name}")
                ],
                [
                    InlineKeyboardButton("🗑 حذف کانفیگ", callback_data=f"telethon_confirm_delete_{config_name}")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_list_configs")
                ]
            ])
            
            keyboard = InlineKeyboardMarkup(keyboard_rows)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def delete_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف کانفیگ"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            # استخراج نام کانفیگ از callback_data
            callback_data = query.data
            config_name = callback_data.replace('telethon_delete_config_', '')
            
            # نمایش تأیید حذف
            text = f"⚠️ **تأیید حذف کانفیگ**\n\n"
            text += f"آیا مطمئن هستید که می‌خواهید کانفیگ **{config_name}** را حذف کنید؟\n\n"
            text += "🚨 **هشدار:**\n"
            text += "• این عمل غیرقابل بازگشت است\n"
            text += "• تمام session های مرتبط حذف خواهند شد\n"
            text += "• دانلودهای در حال انجام متوقف می‌شوند"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ بله، حذف کن", callback_data=f"telethon_confirm_delete_{config_name}"),
                    InlineKeyboardButton("❌ لغو", callback_data=f"telethon_manage_config_{config_name}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def start_manual_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع ایجاد دستی کانفیگ"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            user_id = update.effective_user.id
            
            # بروزرسانی وضعیت کاربر
            await self.db.update_user_session(
                user_id,
                action_state='creating_telethon_config_manual',
                temp_data=json.dumps({'step': 'enter_name'})
            )
            
            text = "✏️ **ایجاد دستی کانفیگ Telethon**\n\n"
            text += "برای ایجاد کانفیگ جدید، لطفاً مراحل زیر را طی کنید:\n\n"
            text += "**مرحله ۱: نام کانفیگ**\n"
            text += "یک نام منحصر به فرد برای کانفیگ خود انتخاب کنید.\n\n"
            text += "💡 **نکات:**\n"
            text += "• نام باید فقط شامل حروف انگلیسی و اعداد باشد\n"
            text += "• نام نمی‌تواند تکراری باشد\n"
            text += "• حداقل ۳ کاراکتر باشد\n\n"
            text += "لطفاً نام کانفیگ خود را وارد کنید:"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("❌ لغو", callback_data="telethon_add_config")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def handle_manual_config_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش ورودی ایجاد دستی کانفیگ"""
        try:
            user_id = update.effective_user.id
            session = await self.db.get_user_session(user_id)
            
            if session.get('action_state') != 'creating_telethon_config_manual':
                return
            
            temp_data = json.loads(session.get('temp_data', '{}'))
            step = temp_data.get('step')
            user_input = update.message.text.strip()
            
            if step == 'enter_name':
                await self._handle_config_name_input(update, context, user_input, temp_data)
            elif step == 'enter_api_id':
                await self._handle_api_id_input(update, context, user_input, temp_data)
            elif step == 'enter_api_hash':
                await self._handle_api_hash_input(update, context, user_input, temp_data)
            elif step == 'enter_phone':
                await self._handle_config_phone_input(update, context, user_input, temp_data)
                
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def _handle_config_name_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, name: str, temp_data: dict):
        """پردازش نام کانفیگ"""
        # اعتبارسنجی نام
        if len(name) < 3:
            await update.message.reply_text("❌ نام کانفیگ باید حداقل ۳ کاراکتر باشد.")
            return
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            await update.message.reply_text("❌ نام فقط می‌تواند شامل حروف انگلیسی، اعداد و _ و - باشد.")
            return
        
        # بررسی عدم تکرار
        try:
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            telethon_manager = AdvancedTelethonClientManager()
            configs = telethon_manager.config_manager.list_configs()
        except Exception as e:
            logger.error(f"Error accessing telethon manager: {e}")
            configs = {}
        
        if name in configs:
            await update.message.reply_text("❌ نام انتخابی تکراری است. لطفاً نام دیگری انتخاب کنید.")
            return
        
        # ذخیره و مرحله بعد
        temp_data['name'] = name
        temp_data['step'] = 'enter_api_id'
        
        await self.db.update_user_session(
            update.effective_user.id,
            temp_data=json.dumps(temp_data)
        )
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("❌ لغو", callback_data="telethon_add_config")
            ]
        ])
        
        await update.message.reply_text(
            f"✅ **نام کانفیگ:** {name}\n\n"
            f"**مرحله ۲: API ID**\n"
            f"لطفاً API ID خود را از my.telegram.org وارد کنید:\n\n"
            f"💡 **نکته:** API ID یک عدد است (مثلاً: 123456)",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def _handle_api_id_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, api_id: str, temp_data: dict):
        """پردازش API ID"""
        try:
            api_id_int = int(api_id)
            if api_id_int <= 0:
                raise ValueError()
        except ValueError:
            await update.message.reply_text("❌ API ID باید یک عدد مثبت باشد.")
            return
        
        temp_data['api_id'] = api_id_int
        temp_data['step'] = 'enter_api_hash'
        
        await self.db.update_user_session(
            update.effective_user.id,
            temp_data=json.dumps(temp_data)
        )
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("❌ لغو", callback_data="telethon_add_config")
            ]
        ])
        
        await update.message.reply_text(
            f"✅ **API ID:** {api_id_int}\n\n"
            f"**مرحله ۳: API Hash**\n"
            f"لطفاً API Hash خود را وارد کنید:\n\n"
            f"💡 **نکته:** API Hash یک رشته 32 کاراکتری است",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def _handle_api_hash_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, api_hash: str, temp_data: dict):
        """پردازش API Hash"""
        if len(api_hash) != 32:
            await update.message.reply_text("❌ API Hash باید دقیقاً 32 کاراکتر باشد.")
            return
        
        if not re.match(r'^[a-f0-9]+$', api_hash.lower()):
            await update.message.reply_text("❌ API Hash فقط می‌تواند شامل اعداد و حروف a-f باشد.")
            return
        
        temp_data['api_hash'] = api_hash
        temp_data['step'] = 'enter_phone'
        
        await self.db.update_user_session(
            update.effective_user.id,
            temp_data=json.dumps(temp_data)
        )
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⏭ رد کردن", callback_data="telethon_skip_phone"),
                InlineKeyboardButton("❌ لغو", callback_data="telethon_add_config")
            ]
        ])
        
        await update.message.reply_text(
            f"✅ **API Hash:** {api_hash[:8]}...{api_hash[-4:]}\n\n"
            f"**مرحله ۴: شماره تلفن (اختیاری)**\n"
            f"می‌توانید شماره تلفن خود را وارد کنید یا رد کنید:\n\n"
            f"💡 **فرمت:** +989123456789",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def _handle_config_phone_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, phone: str, temp_data: dict):
        """پردازش شماره تلفن کانفیگ"""
        # اعتبارسنجی شماره (اگر وارد شده باشد)
        if phone and not re.match(r'^\+\d{10,15}$', phone):
            await update.message.reply_text(
                "❌ فرمت شماره تلفن نامعتبر است.\n"
                "لطفاً شماره را با کد کشور وارد کنید (مثل: +989123456789)"
            )
            return
        
        temp_data['phone'] = phone
        
        # ایجاد کانفیگ نهایی
        await self._create_final_config(update, context, temp_data)
    
    async def _create_final_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE, config_data: dict):
        """ایجاد کانفیگ نهایی"""
        try:
            user_id = update.effective_user.id
            
            # آماده‌سازی داده‌های کانفیگ
            final_config = {
                'api_id': config_data['api_id'],
                'api_hash': config_data['api_hash'],
                'name': config_data['name'],
                'phone': config_data.get('phone', ''),
                'device_model': 'Download System',
                'system_version': '1.0',
                'app_version': '1.0.0',
                'lang_code': 'fa',
                'is_active': True
            }
            
            # ذخیره کانفیگ
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            
            telethon_manager = AdvancedTelethonClientManager()
            success = telethon_manager.config_manager.save_config(config_data['name'], final_config)
            
            if success:
                # ریست وضعیت کاربر
                await self.db.update_user_session(
                    user_id,
                    action_state='browsing',
                    temp_data=None
                )
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔐 ورود به اکانت", callback_data=f"telethon_login_{config_data['name']}"),
                        InlineKeyboardButton("📋 مشاهده کانفیگ‌ها", callback_data="telethon_list_configs")
                    ],
                    [
                        InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")
                    ]
                ])
                
                await update.message.reply_text(
                    f"✅ **کانفیگ '{config_data['name']}' با موفقیت ایجاد شد!**\n\n"
                    f"🔧 **مشخصات:**\n"
                    f"• نام: {config_data['name']}\n"
                    f"• API ID: {config_data['api_id']}\n"
                    f"• شماره: {config_data.get('phone', 'وارد نشده')}\n\n"
                    f"💡 **مرحله بعد:** برای استفاده از این کانفیگ، ابتدا وارد اکانت تلگرام شوید.",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ خطا در ذخیره کانفیگ. لطفاً دوباره تلاش کنید."
                )
                
        except Exception as e:
            logger.error(f"Error creating final config: {e}")
            await update.message.reply_text(
                "❌ خطا در ایجاد کانفیگ. لطفاً دوباره تلاش کنید."
            )