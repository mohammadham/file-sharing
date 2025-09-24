#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telethon Login Handler
هندلر ورود و مدیریت session های Telethon
"""

import json
import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.base_handler import BaseHandler

logger = logging.getLogger(__name__)


class TelethonLoginHandler(BaseHandler):
    """مدیریت فرآیند ورود و احراز هویت Telethon"""
    
    def __init__(self, db):
        super().__init__(db)
    
    async def show_login_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی ورود Telethon"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            # دریافت لیست کانفیگ‌ها
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            
            telethon_manager = AdvancedTelethonClientManager()
            configs = telethon_manager.config_manager.list_configs()
            
            text = "🔐 **ورود به اکانت Telethon**\n\n"
            
            if configs:
                text += "انتخاب کنید که کدام کانفیگ را می‌خواهید فعال کنید:\n\n"
                
                for config_name, config_info in configs.items():
                    status_icon = "🟢" if config_info.get('has_session') else "🔴"
                    text += f"{status_icon} **{config_name}**\n"
                    text += f"   📱 {config_info.get('phone', 'شماره نامشخص')}\n"
                    text += f"   🔗 Session: {'دارد' if config_info.get('has_session') else 'ندارد'}\n\n"
                
                text += "💡 **راهنما:**\n"
                text += "• کانفیگ‌های با نشان 🟢 آماده استفاده هستند\n"
                text += "• کانفیگ‌های با نشان 🔴 نیاز به ورود دارند"
            else:
                text += "❌ **هیچ کانفیگی یافت نشد**\n\n"
                text += "ابتدا باید یک کانفیگ اضافه کنید."
            
            keyboard_rows = []
            
            if configs:
                for config_name, config_info in configs.items():
                    if config_info.get('has_session'):
                        button_text = f"✅ {config_name} (فعال)"
                        callback_data = f"telethon_test_session_{config_name}"
                    else:
                        button_text = f"🔐 ورود {config_name}"
                        callback_data = f"telethon_start_login_{config_name}"
                    
                    keyboard_rows.append([
                        InlineKeyboardButton(button_text, callback_data=callback_data)
                    ])
            
            keyboard_rows.extend([
                [
                    InlineKeyboardButton("➕ افزودن کانفیگ", callback_data="telethon_add_config"),
                    InlineKeyboardButton("🩺 تست همه", callback_data="telethon_health_check")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
                ]
            ])
            
            keyboard = InlineKeyboardMarkup(keyboard_rows)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def start_login_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع فرآیند ورود"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            config_name = query.data.split('_')[-1]
            user_id = update.effective_user.id
            
            # دریافت اطلاعات کانفیگ
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            
            telethon_manager = AdvancedTelethonClientManager()
            config = telethon_manager.config_manager.get_config(config_name)
            
            if not config:
                await query.edit_message_text(
                    "❌ کانفیگ مورد نظر یافت نشد.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_login_menu")
                    ]])
                )
                return
            
            text = f"🔐 **ورود به {config_name}**\n\n"
            text += f"🔧 **مشخصات کانفیگ:**\n"
            text += f"• API ID: {config.api_id}\n"
            text += f"• نام: {config.name}\n"
            
            if config.phone:
                text += f"• شماره: {config.phone}\n\n"
                text += "آیا می‌خواهید با همین شماره ورود کنید؟"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(f"✅ ورود با {config.phone}", callback_data=f"telethon_login_phone_{config_name}_{config.phone}"),
                    ],
                    [
                        InlineKeyboardButton("📝 شماره دیگری", callback_data=f"telethon_enter_phone_{config_name}"),
                    ],
                    [
                        InlineKeyboardButton("❌ لغو", callback_data="telethon_login_menu")
                    ]
                ])
            else:
                text += "\n\nلطفاً شماره تلفن خود را وارد کنید:"
                
                # ذخیره وضعیت
                await self.db.update_user_session(
                    user_id,
                    action_state='telethon_entering_phone',
                    temp_data=json.dumps({'config_name': config_name})
                )
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("❌ لغو", callback_data="telethon_login_menu")
                    ]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def handle_phone_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش ورودی شماره تلفن"""
        try:
            user_id = update.effective_user.id
            session = await self.db.get_user_session(user_id)
            
            if session.get('action_state') != 'telethon_entering_phone':
                return
            
            phone = update.message.text.strip()
            
            # اعتبارسنجی شماره تلفن
            if not re.match(r'^\+\d{10,15}$', phone):
                await update.message.reply_text(
                    "❌ فرمت شماره تلفن نامعتبر است.\n"
                    "لطفاً شماره را با کد کشور وارد کنید (مثل: +989123456789)"
                )
                return
            
            temp_data = json.loads(session.get('temp_data', '{}'))
            config_name = temp_data.get('config_name')
            
            if not config_name:
                await update.message.reply_text("❌ خطا در داده‌های session.")
                return
            
            # ارسال کد تأیید
            await self.send_verification_code(update, context, config_name, phone)
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def send_verification_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE, config_name: str, phone: str):
        """ارسال کد تأیید"""
        try:
            user_id = update.effective_user.id
            
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            
            telethon_manager = AdvancedTelethonClientManager()
            result = await telethon_manager.login_with_phone(config_name, phone)
            
            if result.get('success'):
                # ذخیره اطلاعات برای مرحله بعد
                await self.db.update_user_session(
                    user_id,
                    action_state='telethon_entering_code',
                    temp_data=json.dumps({
                        'config_name': config_name,
                        'phone': phone,
                        'phone_code_hash': result['phone_code_hash']
                    })
                )
                
                text = f"📱 **کد تأیید ارسال شد**\n\n"
                text += f"کد تأیید به شماره {phone} ارسال شد.\n"
                text += f"لطفاً کد ۵ رقمی را وارد کنید:\n\n"
                text += f"💡 **نکته:** کد معمولاً تا ۲ دقیقه طول می‌کشد."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 ارسال مجدد", callback_data=f"telethon_resend_code_{config_name}_{phone}"),
                    ],
                    [
                        InlineKeyboardButton("❌ لغو", callback_data="telethon_login_menu")
                    ]
                ])
                
                if hasattr(update, 'callback_query') and update.callback_query:
                    await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
                else:
                    await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
            else:
                error_msg = result.get('error', 'خطای نامشخص')
                await update.message.reply_text(
                    f"❌ خطا در ارسال کد: {error_msg}\n"
                    f"لطفاً دوباره تلاش کنید.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_login_menu")
                    ]])
                )
                
        except Exception as e:
            logger.error(f"Error sending verification code: {e}")
            await update.message.reply_text(
                "❌ خطا در ارسال کد تأیید. لطفاً دوباره تلاش کنید."
            )
    
    async def handle_verification_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش کد تأیید"""
        try:
            user_id = update.effective_user.id
            session = await self.db.get_user_session(user_id)
            
            if session.get('action_state') != 'telethon_entering_code':
                return
            
            code = update.message.text.strip()
            
            # اعتبارسنجی کد
            if not re.match(r'^\d{5}$', code):
                await update.message.reply_text(
                    "❌ کد تأیید باید ۵ رقم باشد."
                )
                return
            
            temp_data = json.loads(session.get('temp_data', '{}'))
            config_name = temp_data.get('config_name')
            phone = temp_data.get('phone')
            phone_code_hash = temp_data.get('phone_code_hash')
            
            # تأیید کد
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            
            telethon_manager = AdvancedTelethonClientManager()
            result = await telethon_manager.verify_code(config_name, phone, code, phone_code_hash)
            
            if result.get('success'):
                # ورود موفق
                await self.db.update_user_session(
                    user_id,
                    action_state='browsing',
                    temp_data=None
                )
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🩺 تست کلاینت", callback_data=f"telethon_test_session_{config_name}"),
                        InlineKeyboardButton("📋 مشاهده کانفیگ‌ها", callback_data="telethon_list_configs")
                    ],
                    [
                        InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")
                    ]
                ])
                
                await update.message.reply_text(
                    f"✅ **ورود موفق!**\n\n"
                    f"🎉 کانفیگ '{config_name}' با موفقیت فعال شد.\n"
                    f"👤 شناسه کاربری: {result.get('user_id')}\n\n"
                    f"💡 اکنون می‌توانید از سیستم دانلود پیشرفته استفاده کنید.",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            
            elif result.get('needs_password'):
                # نیاز به رمز دو مرحله‌ای
                await self.db.update_user_session(
                    user_id,
                    action_state='telethon_entering_password',
                    temp_data=json.dumps({
                        'config_name': config_name,
                        'phone': phone,
                        'phone_code_hash': phone_code_hash
                    })
                )
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("❌ لغو", callback_data="telethon_login_menu")
                    ]
                ])
                
                await update.message.reply_text(
                    "🔐 **تأیید هویت دو مرحله‌ای**\n\n"
                    "اکانت شما دارای تأیید هویت دو مرحله‌ای است.\n"
                    "لطفاً رمز عبور خود را وارد کنید:",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            
            else:
                error_msg = result.get('error', 'کد نامعتبر')
                await update.message.reply_text(
                    f"❌ {error_msg}\n"
                    f"لطفاً کد صحیح را وارد کنید."
                )
                
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def handle_password_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش رمز دو مرحله‌ای"""
        try:
            user_id = update.effective_user.id
            session = await self.db.get_user_session(user_id)
            
            if session.get('action_state') != 'telethon_entering_password':
                return
            
            password = update.message.text.strip()
            temp_data = json.loads(session.get('temp_data', '{}'))
            
            config_name = temp_data.get('config_name')
            phone = temp_data.get('phone')
            phone_code_hash = temp_data.get('phone_code_hash')
            
            # تأیید رمز
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            
            telethon_manager = AdvancedTelethonClientManager()
            result = await telethon_manager.verify_password(config_name, password, phone, phone_code_hash)
            
            if result.get('success'):
                # ورود موفق
                await self.db.update_user_session(
                    user_id,
                    action_state='browsing',
                    temp_data=None
                )
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🩺 تست کلاینت", callback_data=f"telethon_test_session_{config_name}"),
                        InlineKeyboardButton("📋 مشاهده کانفیگ‌ها", callback_data="telethon_list_configs")
                    ],
                    [
                        InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")
                    ]
                ])
                
                await update.message.reply_text(
                    f"✅ **ورود موفق با تأیید دو مرحله‌ای!**\n\n"
                    f"🎉 کانفیگ '{config_name}' فعال شد.\n"
                    f"👤 شناسه: {result.get('user_id')}\n\n"
                    f"🔐 امنیت اکانت شما تأیید شد.",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            
            else:
                error_msg = result.get('error', 'رمز نامعتبر')
                await update.message.reply_text(
                    f"❌ {error_msg}\n"
                    f"لطفاً رمز صحیح را وارد کنید."
                )
                
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def test_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تست session فعال"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update, "در حال تست...")
            
            config_name = query.data.split('_')[-1]
            
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            
            telethon_manager = AdvancedTelethonClientManager()
            client = await telethon_manager.get_client(config_name)
            
            if client and client.is_connected():
                try:
                    me = await client.get_me()
                    
                    text = f"✅ **تست موفق - {config_name}**\n\n"
                    text += f"🔗 **وضعیت اتصال:** متصل\n"
                    text += f"👤 **نام:** {me.first_name} {me.last_name or ''}\n"
                    text += f"📱 **شماره:** {me.phone}\n"
                    text += f"🆔 **شناسه:** `{me.id}`\n"
                    text += f"👤 **نام کاربری:** @{me.username or 'ندارد'}\n\n"
                    text += f"🎉 **کلاینت آماده استفاده است!**"
                    
                except Exception as e:
                    text = f"⚠️ **تست جزئی موفق - {config_name}**\n\n"
                    text += f"🔗 **وضعیت اتصال:** متصل\n"
                    text += f"❌ **خطا در دریافت اطلاعات:** {str(e)}\n\n"
                    text += f"💡 **توضیح:** اتصال برقرار است اما نتوانستیم اطلاعات کاربر را دریافت کنیم."
            
            else:
                status = telethon_manager.get_client_status(config_name)
                text = f"❌ **تست ناموفق - {config_name}**\n\n"
                text += f"🔗 **وضعیت اتصال:** قطع\n"
                text += f"❌ **خطا:** {status.get('error', 'اتصال برقرار نشد')}\n\n"
                text += f"💡 **راهکار:** مجدداً وارد اکانت شوید."
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 تست مجدد", callback_data=f"telethon_test_session_{config_name}"),
                    InlineKeyboardButton("🔐 ورود مجدد", callback_data=f"telethon_start_login_{config_name}")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_login_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)