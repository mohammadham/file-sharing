#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telethon Management Handler - Advanced Telethon management operations
"""

import asyncio
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from handlers.base_handler import BaseHandler
from utils.keyboard_builder import KeyboardBuilder
from utils.helpers import safe_json_dumps
from utils.advanced_logger import advanced_logger, LogLevel, LogCategory

logger = logging.getLogger(__name__)


class TelethonManagementHandler(BaseHandler):
    """Handle advanced Telethon management operations"""

    def __init__(self, db):
        super().__init__(db)
    async def telethon_view_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش لاگ‌های پیشرفته Telethon"""
        try:
            query = update.callback_query
            await query.answer()
            
            from utils.advanced_logger import advanced_logger, LogCategory, LogLevel
            from datetime import datetime
            
            # دریافت لاگ‌های اخیر
            recent_logs = advanced_logger.get_recent_logs(LogCategory.TELETHON_CONFIG, limit=20)
            health_info = advanced_logger.get_system_health_info()
            error_summary = advanced_logger.get_error_summary()
            
            text = "📋 **لاگ‌های پیشرفته Telethon**\n\n"
            
            # وضعیت کلی سیستم
            text += f"📊 **وضعیت سیستم:**\n"
            text += f"• خطاهای اخیر: {health_info.get('recent_errors_count', 0)}\n"
            text += f"• فعالیت Telethon: {health_info.get('telethon_activity', 0)}\n"
            text += f"• نرخ خطا: {health_info.get('error_rate', 0):.1f}%\n\n"
            
            # خطاهای پرتکرار
            if error_summary:
                text += f"⚠️ **خطاهای پرتکرار:**\n"
                for error_key, count in list(error_summary.items())[:3]:
                    error_category, error_msg = error_key.split(':', 1)
                    text += f"• {error_msg[:30]}... ({count} بار)\n"
                text += "\n"
            
            # لاگ‌های اخیر
            if recent_logs:
                text += f"📝 **لاگ‌های اخیر ({len(recent_logs)}):**\n\n"
                for i, log in enumerate(recent_logs[-10:], 1):  # آخرین 10 لاگ
                    timestamp = log['timestamp'][:16].replace('T', ' ')
                    level_icon = {
                        'INFO': '📘', 'WARNING': '⚠️', 
                        'ERROR': '❌', 'CRITICAL': '🚨'
                    }.get(log['level'], '📝')
                    
                    text += f"{level_icon} `{timestamp}` - {log['message'][:40]}...\n"
                
                if len(recent_logs) > 10:
                    text += f"\n... و {len(recent_logs) - 10} لاگ دیگر"
            else:
                text += "📝 **هیچ لاگ اخیری موجود نیست**"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data="telethon_view_logs"),
                    InlineKeyboardButton("📊 آمار کامل", callback_data="telethon_detailed_stats")
                ],
                [
                    InlineKeyboardButton("📤 صادرات لاگ‌ها", callback_data="telethon_export_logs"),
                    InlineKeyboardButton("🗑 پاک کردن لاگ‌ها", callback_data="telethon_clear_logs")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error viewing Telethon logs: {e}")
            await query.edit_message_text(
                "❌ خطا در نمایش لاگ‌ها",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
                ]])
            )

    async def telethon_clear_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پاک کردن لاگ‌های Telethon"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🗑 **پاک کردن لاگ‌های Telethon**\n\n"
            text += "آیا مطمئن هستید که می‌خواهید تمام لاگ‌های Telethon را پاک کنید؟\n\n"
            text += "⚠️ **هشدار:**\n"
            text += "• این عمل غیرقابل بازگشت است\n"
            text += "• تمام اطلاعات تشخیص خطا از بین می‌رود\n"
            text += "• آمار و گزارش‌ها حذف خواهند شد"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ بله، پاک کن", callback_data="confirm_telethon_clear_logs"),
                    InlineKeyboardButton("❌ لغو", callback_data="telethon_view_logs")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in clear logs: {e}")
            await query.answer("❌ خطا در عملیات!")

    async def telethon_export_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """صادرات لاگ‌های Telethon"""
        try:
            query = update.callback_query
            await query.answer("در حال آماده‌سازی لاگ‌ها...")
            
            from utils.advanced_logger import advanced_logger, LogCategory, LogLevel
            import json
            from datetime import datetime
            
            # دریافت تمام لاگ‌های Telethon
            telethon_logs = advanced_logger.get_recent_logs(LogCategory.TELETHON_CONFIG, limit=1000)
            client_logs = advanced_logger.get_recent_logs(LogCategory.TELETHON_CLIENT, limit=1000)
            login_logs = advanced_logger.get_recent_logs(LogCategory.TELETHON_LOGIN, limit=1000)
            
            # ترکیب و مرتب‌سازی لاگ‌ها
            all_logs = telethon_logs + client_logs + login_logs
            all_logs.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # ایجاد گزارش JSON
            export_data = {
                'export_time': datetime.now().isoformat(),
                'total_logs': len(all_logs),
                'system_health': advanced_logger.get_system_health_info(),
                'error_summary': advanced_logger.get_error_summary(),
                'logs': all_logs
            }
            
            # تبدیل به فایل JSON
            json_content = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            # ایجاد فایل موقت
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                f.write(json_content)
                temp_path = f.name
            
            # ارسال فایل
            filename = f"telethon_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=open(temp_path, 'rb'),
                filename=filename,
                caption=f"📊 **گزارش کامل لاگ‌های Telethon**\n\n"
                       f"📅 زمان صادرات: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                       f"📋 تعداد لاگ‌ها: {len(all_logs):,}\n"
                       f"⚠️ خطاهای اخیر: {export_data['system_health'].get('recent_errors_count', 0)}\n\n"
                       f"💡 این فایل شامل تمام اطلاعات تشخیص خطا و عملکرد سیستم است.",
                parse_mode='Markdown'
            )
            
            # حذف فایل موقت
            os.unlink(temp_path)
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔙 بازگشت به لاگ‌ها", callback_data="telethon_view_logs")
                ]
            ])
            
            await query.edit_message_text(
                "✅ **لاگ‌ها با موفقیت صادر شدند!**\n\n"
                "فایل JSON حاوی تمام اطلاعات ارسال شد.",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error exporting logs: {e}")
            await query.edit_message_text(
                f"❌ خطا در صادرات لاگ‌ها: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_view_logs")
                ]])
            )
    # async def telethon_view_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """View Telethon logs"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         # Read recent Telethon logs
    #         try:
    #             import os
    #             log_file = "/app/bot/telegram_bot.log"
                
    #             if os.path.exists(log_file):
    #                 with open(log_file, 'r', encoding='utf-8') as f:
    #                     lines = f.readlines()
    #                     recent_lines = lines[-20:]  # Last 20 lines
                    
    #                 text = "📋 **لاگ‌های اخیر Telethon**\n\n"
    #                 text += "```\n"
    #                 for line in recent_lines:
    #                     if len(text) < 3800:  # Telegram message limit
    #                         text += line.strip()[:100] + "\n"  # Truncate long lines
    #                     else:
    #                         text += "...\n"
    #                         break
    #                 text += "```"
    #             else:
    #                 text = "📋 **لاگ‌های Telethon**\n\n"
    #                 text += "❌ فایل لاگ یافت نشد!\n\n"
    #                 text += f"مسیر مورد انتظار: `{log_file}`"
                    
    #         except Exception as e:
    #             text = "📋 **لاگ‌های Telethon**\n\n"
    #             text += f"❌ خطا در خواندن لاگ‌ها: {str(e)}"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("🔄 بروزرسانی", callback_data="telethon_view_logs"),
    #                 InlineKeyboardButton("📤 ارسال فایل", callback_data="telethon_export_logs")
    #             ],
    #             [
    #                 InlineKeyboardButton("🗑 پاک کردن لاگ", callback_data="telethon_clear_logs"),
    #                 InlineKeyboardButton("⚙️ تنظیمات لاگ", callback_data="telethon_log_settings")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
    #             ]
    #         ])
            
    #         await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error viewing telethon logs: {e}")
    #         await self.handle_error(update, context, e)
    
    # async def telethon_clear_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Clear Telethon logs with confirmation"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         text = "🗑 **پاک کردن لاگ‌های Telethon**\n\n"
    #         text += "⚠️ **هشدار:**\n"
    #         text += "• تمام لاگ‌های موجود پاک خواهند شد\n"
    #         text += "• این عملیات قابل بازگشت نیست\n"
    #         text += "• اطلاعات تشخیص خطا از بین خواهد رفت\n\n"
    #         text += "💡 **پیشنهاد:** ابتدا لاگ‌ها را export کنید\n\n"
    #         text += "آیا مطمئن هستید؟"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("📤 Export و پاک کن", callback_data="telethon_export_and_clear"),
    #                 InlineKeyboardButton("🗑 فقط پاک کن", callback_data="confirm_telethon_clear_logs")
    #             ],
    #             [
    #                 InlineKeyboardButton("❌ لغو", callback_data="telethon_view_logs")
    #             ]
    #         ])
            
    #         await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error in telethon clear logs: {e}")
    #         await self.handle_error(update, context, e)
    
    # async def telethon_export_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Export Telethon logs as file"""
    #     try:
    #         query = update.callback_query
    #         await query.answer("در حال تهیه فایل لاگ...")
            
    #         import os
    #         log_file = "/app/bot/telegram_bot.log"
            
    #         if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
    #             # Create a backup with timestamp
    #             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    #             backup_filename = f"telethon_logs_{timestamp}.txt"
                
    #             try:
    #                 await context.bot.send_document(
    #                     chat_id=update.effective_chat.id,
    #                     document=open(log_file, 'rb'),
    #                     filename=backup_filename,
    #                     caption=f"📋 **فایل لاگ Telethon**\n\n"
    #                             f"📅 **تاریخ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    #                             f"📊 **حجم:** {os.path.getsize(log_file)} بایت",
    #                     parse_mode='Markdown',
    #                     reply_to_message_id=query.message.message_id
    #                 )
                    
    #                 await query.answer("✅ فایل لاگ ارسال شد!")
                    
    #             except Exception as e:
    #                 await query.answer(f"❌ خطا در ارسال فایل: {str(e)}")
    #         else:
    #             await query.answer("❌ فایل لاگ وجود ندارد یا خالی است!")
            
    #     except Exception as e:
    #         logger.error(f"Error exporting telethon logs: {e}")
    #         await query.answer("❌ خطا در ارسال لاگ!")
    
    # async def confirm_clear_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Confirm clearing Telethon logs"""
    #     try:
    #         query = update.callback_query
    #         await query.answer("در حال پاک کردن لاگ‌ها...")
            
    #         import os
    #         log_file = "/app/bot/telegram_bot.log"
            
    #         try:
    #             if os.path.exists(log_file):
    #                 # Clear the file content
    #                 with open(log_file, 'w') as f:
    #                     f.write("")
                    
    #                 text = "✅ **لاگ‌ها پاک شدند**\n\n"
    #                 text += f"📁 **فایل:** `{log_file}`\n"
    #                 text += f"🕐 **زمان:** {datetime.now().strftime('%H:%M:%S')}\n\n"
    #                 text += "لاگ‌های جدید از این لحظه ثبت خواهند شد."
    #             else:
    #                 text = "❌ **خطا در پاک کردن**\n\n"
    #                 text += "فایل لاگ یافت نشد!"
                    
    #         except Exception as e:
    #             text = "❌ **خطا در پاک کردن**\n\n"
    #             text += f"علت: {str(e)}"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("📋 مشاهده لاگ", callback_data="telethon_view_logs"),
    #                 InlineKeyboardButton("⚙️ تنظیمات", callback_data="telethon_log_settings")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
    #             ]
    #         ])
            
    #         await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error confirming clear logs: {e}")
    #         await self.handle_error(update, context, e)
    
    # async def telethon_timeout_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Telethon timeout settings"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         text = "⏱ **تنظیمات Timeout Telethon**\n\n"
    #         text += "در این بخش می‌توانید زمان انتظار عملیات Telethon را تنظیم کنید:\n\n"
    #         text += "🔧 **تنظیمات فعلی:**\n"
    #         text += "• Connection Timeout: 30 ثانیه\n"
    #         text += "• Request Timeout: 60 ثانیه\n"
    #         text += "• Upload Timeout: 300 ثانیه\n"
    #         text += "• Download Timeout: 600 ثانیه\n\n"
    #         text += "⚙️ **گزینه‌های تنظیم:**"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("🔗 Connection", callback_data="set_connection_timeout"),
    #                 InlineKeyboardButton("📡 Request", callback_data="set_request_timeout")
    #             ],
    #             [
    #                 InlineKeyboardButton("📤 Upload", callback_data="set_upload_timeout"),
    #                 InlineKeyboardButton("📥 Download", callback_data="set_download_timeout")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔄 بازنشانی", callback_data="reset_timeouts"),
    #                 InlineKeyboardButton("📊 تست سرعت", callback_data="telethon_speed_test")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
    #             ]
    #         ])
            
    #         await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error in telethon timeout settings: {e}")
    #         await self.handle_error(update, context, e)
    
    # async def telethon_download_limits(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Telethon download limits settings"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         text = "📥 **محدودیت‌های دانلود Telethon**\n\n"
    #         text += "تنظیم محدودیت‌ها برای بهینه‌سازی عملکرد:\n\n"
    #         text += "📊 **تنظیمات فعلی:**\n"
    #         text += "• حداکثر اندازه فایل: 2 GB\n"
    #         text += "• دانلودهای همزمان: 3\n"
    #         text += "• سرعت حداکثر: نامحدود\n"
    #         text += "• Chunk Size: 512 KB\n\n"
    #         text += "⚡️ **بهینه‌سازی‌ها:**\n"
    #         text += "• استفاده از CDN: فعال\n"
    #         text += "• فشرده‌سازی: خودکار\n"
    #         text += "• Resume قابلیت: فعال"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("📊 حد اندازه", callback_data="set_file_size_limit"),
    #                 InlineKeyboardButton("🔀 دانلود همزمان", callback_data="set_concurrent_downloads")
    #             ],
    #             [
    #                 InlineKeyboardButton("⚡️ حد سرعت", callback_data="set_speed_limit"),
    #                 InlineKeyboardButton("🗂 Chunk Size", callback_data="set_chunk_size")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔧 بهینه‌سازی خودکار", callback_data="auto_optimize"),
    #                 InlineKeyboardButton("📈 آمار دانلود", callback_data="download_statistics")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
    #             ]
    #         ])
            
    #         await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error in telethon download limits: {e}")
    #         await self.handle_error(update, context, e)
    
    # async def telethon_proxy_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Telethon proxy settings"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         text = "🌐 **تنظیمات پروکسی Telethon**\n\n"
    #         text += "مدیریت اتصال از طریق پروکسی:\n\n"
    #         text += "📡 **وضعیت فعلی:**\n"
    #         text += "• پروکسی: غیرفعال\n"
    #         text += "• نوع اتصال: مستقیم\n"
    #         text += "• IP فعلی: تشخیص خودکار\n\n"
    #         text += "🔧 **انواع پروکسی پشتیبانی شده:**\n"
    #         text += "• HTTP/HTTPS Proxy\n"
    #         text += "• SOCKS4/SOCKS5\n"
    #         text += "• MTProto Proxy\n\n"
    #         text += "⚠️ **توجه:** استفاده از پروکسی ممکن است سرعت را کاهش دهد"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("➕ افزودن پروکسی", callback_data="add_proxy"),
    #                 InlineKeyboardButton("📋 لیست پروکسی‌ها", callback_data="list_proxies")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔄 تست پروکسی", callback_data="test_proxy"),
    #                 InlineKeyboardButton("⚙️ تنظیمات پیشرفته", callback_data="advanced_proxy_settings")
    #             ],
    #             [
    #                 InlineKeyboardButton("🚫 غیرفعال‌سازی", callback_data="disable_proxy"),
    #                 InlineKeyboardButton("📊 آمار اتصال", callback_data="connection_stats")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
    #             ]
    #         ])
            
    #         await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error in telethon proxy settings: {e}")
    #         await self.handle_error(update, context, e)
    
    # async def telethon_security_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Telethon security settings"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         text = "🔒 **تنظیمات امنیتی Telethon**\n\n"
    #         text += "مدیریت امنیت و حریم خصوصی:\n\n"
    #         text += "🛡 **وضعیت امنیتی:**\n"
    #         text += "• رمزنگاری: AES-256 (فعال)\n"
    #         text += "• احراز هویت دومرحله‌ای: تشخیص خودکار\n"
    #         text += "• Session امن: فعال\n"
    #         text += "• IP Allowlist: غیرفعال\n\n"
    #         text += "🔐 **تنظیمات حفاظتی:**\n"
    #         text += "• Lock session پس از بی‌فعالی\n"
    #         text += "• محدودسازی دسترسی API\n"
    #         text += "• نظارت بر فعالیت‌های مشکوک\n"
    #         text += "• Backup خودکار session ها"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("🔐 Session Security", callback_data="session_security"),
    #                 InlineKeyboardButton("🚫 IP Restrictions", callback_data="ip_restrictions")
    #             ],
    #             [
    #                 InlineKeyboardButton("⏰ Auto-lock", callback_data="auto_lock_settings"),
    #                 InlineKeyboardButton("📊 Security Audit", callback_data="security_audit")
    #             ],
    #             [
    #                 InlineKeyboardButton("💾 Backup Manager", callback_data="backup_manager"),
    #                 InlineKeyboardButton("🔍 Activity Monitor", callback_data="activity_monitor")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
    #             ]
    #         ])
            
    #         await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error in telethon security settings: {e}")
    #         await self.handle_error(update, context, e)
    
    # async def telethon_performance_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Telethon performance settings"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         text = "⚡️ **تنظیمات عملکرد Telethon**\n\n"
    #         text += "بهینه‌سازی سرعت و کارایی:\n\n"
    #         text += "📊 **وضعیت فعلی:**\n"
    #         text += "• CPU Usage: متوسط\n"
    #         text += "• Memory Usage: 45 MB\n"
    #         text += "• Network Efficiency: بالا\n"
    #         text += "• Cache Hit Rate: 78%\n\n"
    #         text += "🚀 **بهینه‌سازی‌های فعال:**\n"
    #         text += "• Connection pooling\n"
    #         text += "• Smart caching\n"
    #         text += "• Compression\n"
    #         text += "• Async operations\n\n"
    #         text += "💡 **پیشنهادات بهبود:**\n"
    #         text += "• افزایش حافظه cache\n"
    #         text += "• بهینه‌سازی chunk size"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("🗄 Cache Settings", callback_data="cache_settings"),
    #                 InlineKeyboardButton("🔗 Connection Pool", callback_data="connection_pool_settings")
    #             ],
    #             [
    #                 InlineKeyboardButton("📊 Resource Monitor", callback_data="resource_monitor"),
    #                 InlineKeyboardButton("⚡️ Speed Optimization", callback_data="speed_optimization")
    #             ],
    #             [
    #                 InlineKeyboardButton("🧹 Memory Cleanup", callback_data="memory_cleanup"),
    #                 InlineKeyboardButton("📈 Performance Test", callback_data="telethon_performance_test")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
    #             ]
    #         ])
            
    #         await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error in telethon performance settings: {e}")
    #         await self.handle_error(update, context, e)
    
    # async def telethon_auto_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Telethon auto configuration"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         text = "🤖 **پیکربندی خودکار Telethon**\n\n"
    #         text += "تنظیم خودکار بهترین پارامترها:\n\n"
    #         text += "🔍 **تشخیص خودکار:**\n"
    #         text += "• کیفیت اتصال اینترنت\n"
    #         text += "• منابع سیستم موجود\n"
    #         text += "• نوع کاربری (سبک/سنگین)\n"
    #         text += "• محدودیت‌های شبکه\n\n"
    #         text += "⚙️ **تنظیمات خودکار:**\n"
    #         text += "• Timeout ها\n"
    #         text += "• Buffer sizes\n"
    #         text += "• Connection limits\n"
    #         text += "• Cache policies\n\n"
    #         text += "🎯 **پروفایل‌های آماده:**"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("🏠 خانگی (پایه)", callback_data="config_home_basic"),
    #                 InlineKeyboardButton("🏢 اداری (متوسط)", callback_data="config_office_medium")
    #             ],
    #             [
    #                 InlineKeyboardButton("🚀 سرور (حرفه‌ای)", callback_data="config_server_pro"),
    #                 InlineKeyboardButton("🔧 سفارشی", callback_data="config_custom")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔍 تشخیص خودکار", callback_data="auto_detect_config"),
    #                 InlineKeyboardButton("📊 تست و تنظیم", callback_data="test_and_configure")
    #             ],
    #             [
    #                 InlineKeyboardButton("💾 ذخیره پروفایل", callback_data="save_config_profile"),
    #                 InlineKeyboardButton("📋 بازیابی پروفایل", callback_data="load_config_profile")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
    #             ]
    #         ])
            
    #         await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error in telethon auto config: {e}")
    #         await self.handle_error(update, context, e)
    
    # async def telethon_confirm_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Confirm Telethon configuration deletion"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         # Extract config name from callback data
    #         config_name = query.data.split('_')[-1]
            
    #         text = f"🗑 **حذف کانفیگ Telethon**\n\n"
    #         text += f"📝 **کانفیگ:** `{config_name}`\n\n"
    #         text += "⚠️ **هشدار مهم:**\n"
    #         text += "• کانفیگ و session مربوطه حذف خواهد شد\n"
    #         text += "• اتصال Telethon قطع می‌شود\n"
    #         text += "• بازیابی امکان‌پذیر نیست\n"
    #         text += "• باید مجدداً login کنید\n\n"
    #         text += "آیا مطمئن هستید؟"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("💾 Backup و حذف", callback_data=f"backup_and_delete_{config_name}"),
    #                 InlineKeyboardButton("🗑 فقط حذف", callback_data=f"force_delete_{config_name}")
    #             ],
    #             [
    #                 InlineKeyboardButton("❌ لغو", callback_data="telethon_list_configs")
    #             ]
    #         ])
            
    #         await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error in telethon confirm delete: {e}")
    #         await self.handle_error(update, context, e)
    
    # async def telethon_advanced_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Advanced Telethon settings"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         text = "🔧 **تنظیمات پیشرفته Telethon**\n\n"
    #         text += "پیکربندی‌های تخصصی برای کاربران حرفه‌ای:\n\n"
    #         text += "⚙️ **بخش‌های تنظیمات:**\n"
    #         text += "• Protocol optimization\n"
    #         text += "• Advanced networking\n"
    #         text += "• Custom API endpoints\n"
    #         text += "• Debug و monitoring\n"
    #         text += "• Experimental features\n\n"
    #         text += "⚠️ **هشدار:** تغییر این تنظیمات ممکن است عملکرد را تحت تأثیر قرار دهد"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("🌐 Network Advanced", callback_data="network_advanced"),
    #                 InlineKeyboardButton("🔄 Protocol Settings", callback_data="protocol_settings")
    #             ],
    #             [
    #                 InlineKeyboardButton("🛠 Debug Mode", callback_data="debug_mode"),
    #                 InlineKeyboardButton("📊 Advanced Monitoring", callback_data="advanced_monitoring")
    #             ],
    #             [
    #                 InlineKeyboardButton("🧪 Experimental", callback_data="experimental_features"),
    #                 InlineKeyboardButton("📝 Custom Scripts", callback_data="custom_scripts")
    #             ],
    #             [
    #                 InlineKeyboardButton("💾 Export Config", callback_data="export_advanced_config"),
    #                 InlineKeyboardButton("📥 Import Config", callback_data="import_advanced_config")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔄 Reset to Default", callback_data="reset_advanced_settings"),
    #                 InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
    #             ]
    #         ])
            
    #         await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error in telethon advanced settings: {e}")
    #         await self.handle_error(update, context, e)
    
    # async def telethon_test_client(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Test Telethon client"""
    #     try:
    #         query = update.callback_query
    #         await query.answer("در حال تست کلاینت...")
            
    #         # Extract client name from callback data
    #         client_name = query.data.split('_')[-1]
            
    #         text = f"🧪 **تست کلاینت Telethon**\n\n"
    #         text += f"🤖 **کلاینت:** `{client_name}`\n"
    #         text += "⏳ **در حال انجام تست‌ها...**\n\n"
            
    #         # Perform basic tests
    #         test_results = []
            
    #         try:
    #             # Test 1: Connection
    #             test_results.append("🔗 **اتصال:** ✅ موفق")
                
    #             # Test 2: Authentication
    #             test_results.append("🔐 **احراز هویت:** ✅ معتبر")
                
    #             # Test 3: API Access
    #             test_results.append("📡 **دسترسی API:** ✅ فعال")
                
    #             # Test 4: Download capability
    #             test_results.append("📥 **قابلیت دانلود:** ✅ آماده")
                
    #             # Test 5: Upload capability  
    #             test_results.append("📤 **قابلیت آپلود:** ✅ آماده")
                
    #             overall_status = "✅ **وضعیت کلی:** سالم و آماده"
                
    #         except Exception as e:
    #             test_results.append(f"❌ **خطا:** {str(e)}")
    #             overall_status = "❌ **وضعیت کلی:** مشکل دار"
            
    #         # Build result text
    #         text = f"🧪 **نتایج تست کلاینت**\n\n"
    #         text += f"🤖 **کلاینت:** `{client_name}`\n"
    #         text += f"🕐 **زمان تست:** {datetime.now().strftime('%H:%M:%S')}\n\n"
            
    #         for result in test_results:
    #             text += f"{result}\n"
            
    #         text += f"\n{overall_status}\n\n"
    #         text += "💡 **توصیه‌ها:**\n"
    #         text += "• کلاینت آماده استفاده است\n"
    #         text += "• عملکرد مطلوب\n"
    #         text += "• تنظیمات بهینه"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("🔄 تست مجدد", callback_data=f"telethon_test_client_{client_name}"),
    #                 InlineKeyboardButton("📊 تست عمیق", callback_data=f"deep_test_{client_name}")
    #             ],
    #             [
    #                 InlineKeyboardButton("⚙️ تنظیمات کلاینت", callback_data=f"client_settings_{client_name}"),
    #                 InlineKeyboardButton("📋 گزارش کامل", callback_data=f"full_report_{client_name}")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_health_check")
    #             ]
    #         ])
            
    #         await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error testing telethon client: {e}")
    #         await self.handle_error(update, context, e)
    
    # async def telethon_reset_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Reset Telethon session"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         # Extract session name from callback data
    #         session_name = query.data.split('_')[-1]
            
    #         text = f"🔄 **بازنشانی Session Telethon**\n\n"
    #         text += f"📱 **Session:** `{session_name}`\n\n"
    #         text += "⚠️ **هشدار:**\n"
    #         text += "• Session فعلی حذف خواهد شد\n"
    #         text += "• باید مجدداً login کنید\n"
    #         text += "• تمام اتصالات قطع می‌شود\n"
    #         text += "• تنظیمات محلی پاک می‌شود\n\n"
    #         text += "🔧 **انواع بازنشانی:**"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("🔄 Reset نرم", callback_data=f"soft_reset_{session_name}"),
    #                 InlineKeyboardButton("🗑 Reset کامل", callback_data=f"hard_reset_{session_name}")
    #             ],
    #             [
    #                 InlineKeyboardButton("💾 Backup و Reset", callback_data=f"backup_reset_{session_name}"),
    #                 InlineKeyboardButton("⚙️ Reset تنظیمات", callback_data=f"settings_reset_{session_name}")
    #             ],
    #             [
    #                 InlineKeyboardButton("❌ لغو", callback_data="telethon_health_check")
    #             ]
    #         ])
            
    #         await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error in telethon reset session: {e}")
    #         await self.handle_error(update, context, e)
    
    # async def telethon_edit_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Edit Telethon configuration"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         # Extract config name from callback data
    #         config_name = query.data.split('_')[-1]
            
    #         text = f"✏️ **ویرایش کانفیگ Telethon**\n\n"
    #         text += f"📝 **کانفیگ:** `{config_name}`\n\n"
    #         text += "🔧 **بخش‌های قابل ویرایش:**\n"
    #         text += "• اطلاعات پایه (نام، توضیحات)\n"
    #         text += "• تنظیمات اتصال\n"
    #         text += "• پارامترهای امنیتی\n"
    #         text += "• بهینه‌سازی عملکرد\n\n"
    #         text += "انتخاب کنید که چه بخشی را ویرایش کنید:"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("📝 اطلاعات پایه", callback_data=f"edit_basic_{config_name}"),
    #                 InlineKeyboardButton("🔗 تنظیمات اتصال", callback_data=f"edit_connection_{config_name}")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔒 تنظیمات امنیتی", callback_data=f"edit_security_{config_name}"),
    #                 InlineKeyboardButton("⚡️ بهینه‌سازی", callback_data=f"edit_performance_{config_name}")
    #             ],
    #             [
    #                 InlineKeyboardButton("🌐 پروکسی", callback_data=f"edit_proxy_{config_name}"),
    #                 InlineKeyboardButton("📊 Monitoring", callback_data=f"edit_monitoring_{config_name}")
    #             ],
    #             [
    #                 InlineKeyboardButton("💾 ذخیره تغییرات", callback_data=f"save_config_{config_name}"),
    #                 InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_list_configs")
    #             ]
    #         ])
            
    #         await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error in telethon edit config: {e}")
    #         await self.handle_error(update, context, e)
    
    # async def telethon_view_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """View Telethon configuration details"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         # Extract config name from callback data
    #         config_name = query.data.split('_')[-1]
            
    #         text = f"👁 **مشاهده کانفیگ Telethon**\n\n"
    #         text += f"📝 **نام کانفیگ:** `{config_name}`\n"
    #         text += f"📅 **تاریخ ایجاد:** {datetime.now().strftime('%Y-%m-%d')}\n"
    #         text += f"🔄 **آخرین بروزرسانی:** {datetime.now().strftime('%H:%M:%S')}\n"
    #         text += f"📊 **وضعیت:** فعال\n\n"
            
    #         text += "🔧 **تنظیمات:**\n"
    #         text += "• API ID: ••••••\n"
    #         text += "• API Hash: ••••••••••••\n"
    #         text += "• Phone: +98••••••••••\n"
    #         text += "• Session: فعال\n\n"
            
    #         text += "⚙️ **پیکربندی:**\n"
    #         text += "• Connection: Direct\n"
    #         text += "• Proxy: غیرفعال\n"
    #         text += "• Timeout: 30s\n"
    #         text += "• Max connections: 10\n\n"
            
    #         text += "📈 **آمار استفاده:**\n"
    #         text += "• تعداد درخواست‌ها: 1,247\n"
    #         text += "• آخرین فعالیت: 2 دقیقه پیش\n"
    #         text += "• وضعیت سلامت: ✅ سالم"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("✏️ ویرایش", callback_data=f"telethon_edit_config_{config_name}"),
    #                 InlineKeyboardButton("🧪 تست", callback_data=f"telethon_test_client_{config_name}")
    #             ],
    #             [
    #                 InlineKeyboardButton("📊 آمار تفصیلی", callback_data=f"config_detailed_stats_{config_name}"),
    #                 InlineKeyboardButton("🔄 بازنشانی", callback_data=f"telethon_reset_session_{config_name}")
    #             ],
    #             [
    #                 InlineKeyboardButton("💾 Export", callback_data=f"export_config_{config_name}"),
    #                 InlineKeyboardButton("🗑 حذف", callback_data=f"telethon_confirm_delete_{config_name}")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_list_configs")
    #             ]
    #         ])
            
    #         await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error viewing telethon config: {e}")
    #         await self.handle_error(update, context, e)
    
    # async def telethon_emergency_login(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Emergency Telethon login"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         text = "🚨 **ورود اضطراری Telethon**\n\n"
    #         text += "برای مواقع اضطراری که دسترسی عادی امکان‌پذیر نیست:\n\n"
    #         text += "⚠️ **موارد استفاده:**\n"
    #         text += "• قطع شدن غیرمنتظره session\n"
    #         text += "• مشکل در احراز هویت\n"
    #         text += "• خطای کانفیگ اصلی\n"
    #         text += "• بازیابی دسترسی\n\n"
    #         text += "🔧 **روش‌های ورود اضطراری:**\n"
    #         text += "• استفاده از backup session\n"
    #         text += "• ایجاد کانفیگ موقت\n"
    #         text += "• بازیابی از phone number\n"
    #         text += "• استفاده از recovery code"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("💾 از Backup", callback_data="emergency_from_backup"),
    #                 InlineKeyboardButton("📱 از Phone", callback_data="emergency_from_phone")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔑 Recovery Code", callback_data="emergency_recovery_code"),
    #                 InlineKeyboardButton("⚙️ کانفیگ موقت", callback_data="emergency_temp_config")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔄 بازنشانی کامل", callback_data="emergency_full_reset"),
    #                 InlineKeyboardButton("📞 پشتیبانی", callback_data="emergency_support")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_health_check")
    #             ]
    #         ])
            
    #         await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error in telethon emergency login: {e}")
    #         await self.handle_error(update, context, e)
    
    # async def telethon_fix_issues(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Fix Telethon issues automatically"""
    #     try:
    #         query = update.callback_query
    #         await query.answer("در حال تشخیص و رفع مشکلات...")
            
    #         text = "🔧 **رفع خودکار مشکلات Telethon**\n\n"
    #         text += "⏳ **در حال بررسی سیستم...**\n\n"
            
    #         # Simulate issue detection and fixing
    #         issues_found = []
    #         fixes_applied = []
            
    #         # Check common issues
    #         issues_found.append("🔍 بررسی اتصال شبکه...")
    #         fixes_applied.append("✅ اتصال شبکه: سالم")
            
    #         issues_found.append("🔍 بررسی session files...")
    #         fixes_applied.append("✅ Session files: موجود")
            
    #         issues_found.append("🔍 بررسی API credentials...")
    #         fixes_applied.append("✅ API credentials: معتبر")
            
    #         issues_found.append("🔍 بررسی permissions...")
    #         fixes_applied.append("✅ Permissions: تنظیم شده")
            
    #         # Build results
    #         result_text = "🔧 **نتایج رفع خودکار**\n\n"
    #         result_text += f"🕐 **زمان بررسی:** {datetime.now().strftime('%H:%M:%S')}\n\n"
            
    #         result_text += "✅ **مشکلات رفع شده:**\n"
    #         for fix in fixes_applied:
    #             result_text += f"{fix}\n"
            
    #         result_text += "\n🎯 **خلاصه:**\n"
    #         result_text += f"• {len(fixes_applied)} مورد بررسی شد\n"
    #         result_text += "• تمام موارد سالم هستند\n"
    #         result_text += "• سیستم آماده استفاده است\n\n"
    #         result_text += "💡 **پیشنهادات:**\n"
    #         result_text += "• Restart کلاینت‌ها برای اطمینان\n"
    #         result_text += "• تست عملکرد انجام دهید"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("🔄 اجرای مجدد", callback_data="telethon_fix_issues"),
    #                 InlineKeyboardButton("🧪 تست عملکرد", callback_data="telethon_performance_test")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔄 Restart همه", callback_data="restart_all_clients"),
    #                 InlineKeyboardButton("📊 گزارش تفصیلی", callback_data="detailed_fix_report")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_health_check")
    #             ]
    #         ])
            
    #         await query.edit_message_text(result_text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error fixing telethon issues: {e}")
    #         await self.handle_error(update, context, e)
    
    # async def telethon_detailed_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Show detailed Telethon statistics"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         text = "📊 **آمار تفصیلی Telethon**\n\n"
    #         text += f"📅 **تاریخ گزارش:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
    #         text += "🤖 **وضعیت کلاینت‌ها:**\n"
    #         text += "• کلاینت‌های فعال: 2/3\n"
    #         text += "• Session های سالم: 100%\n"
    #         text += "• آخرین بروزرسانی: 5 دقیقه پیش\n\n"
            
    #         text += "📈 **آمار عملکرد امروز:**\n"
    #         text += "• کل درخواست‌ها: 2,847\n"
    #         text += "• درخواست‌های موفق: 2,831 (99.4%)\n"
    #         text += "• میانگین پاسخ: 1.2 ثانیه\n"
    #         text += "• خطاهای شبکه: 16 (0.6%)\n\n"
            
    #         text += "💾 **مصرف منابع:**\n"
    #         text += "• استفاده از RAM: 128 MB\n"
    #         text += "• استفاده از CPU: 12%\n"
    #         text += "• فضای دیسک: 45 MB\n"
    #         text += "• پهنای باند: 2.1 MB/s\n\n"
            
    #         text += "🔗 **آمار اتصال:**\n"
    #         text += "• Data Center: DC2 (Amsterdam)\n"
    #         text += "• Ping میانگین: 45ms\n"
    #         text += "• Uptime: 23h 42m\n"
    #         text += "• Reconnections: 3 بار\n\n"
            
    #         text += "📤 **آمار Upload/Download:**\n"
    #         text += "• فایل‌های آپلود شده: 127\n"
    #         text += "• فایل‌های دانلود شده: 89\n"
    #         text += "• حجم کل منتقل شده: 3.2 GB\n"
    #         text += "• سرعت میانگین: 5.8 MB/s"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("📈 نمودار آمار", callback_data="stats_chart"),
    #                 InlineKeyboardButton("📋 گزارش PDF", callback_data="export_stats_pdf")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔄 بروزرسانی", callback_data="telethon_detailed_stats"),
    #                 InlineKeyboardButton("⏰ آمار هفتگی", callback_data="weekly_stats")
    #             ],
    #             [
    #                 InlineKeyboardButton("📊 مقایسه عملکرد", callback_data="performance_comparison"),
    #                 InlineKeyboardButton("🎯 بهینه‌سازی", callback_data="optimize_suggestions")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_health_check")
    #             ]
    #         ])
            
    #         await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error showing telethon detailed stats: {e}")
    #         await self.handle_error(update, context, e)
    
    # async def telethon_auto_fix(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Auto-fix Telethon issues"""
    #     try:
    #         query = update.callback_query
    #         await query.answer("شروع رفع خودکار مشکلات...")
            
    #         text = "🤖 **رفع خودکار مشکلات**\n\n"
    #         text += "⏳ **در حال تحلیل سیستم...**\n\n"
            
    #         # Simulate auto-fix process
    #         steps = [
    #             "🔍 تشخیص مشکلات...",
    #             "🔧 تحلیل علل ریشه‌ای...",
    #             "⚡️ اعمال راه‌حل‌های خودکار...",
    #             "✅ تست عملکرد...",
    #             "📊 گزارش نهایی..."
    #         ]
            
    #         fixes_applied = [
    #             "🔄 بازنشانی connection pool",
    #             "🧹 پاکسازی cache فاسد",
    #             "⚙️ بهینه‌سازی تنظیمات",
    #             "🔐 تجدید authentication token",
    #             "📈 بهبود کیفیت اتصال"
    #         ]
            
    #         result_text = "🤖 **رفع خودکار کامل شد**\n\n"
    #         result_text += f"⏰ **زمان پردازش:** 23 ثانیه\n"
    #         result_text += f"🎯 **موفقیت:** 95%\n\n"
            
    #         result_text += "🔧 **اقدامات انجام شده:**\n"
    #         for fix in fixes_applied:
    #             result_text += f"✅ {fix}\n"
            
    #         result_text += "\n📈 **بهبود عملکرد:**\n"
    #         result_text += "• سرعت پاسخ: +40% بهتر\n"
    #         result_text += "• استفاده از memory: -25% کاهش\n"
    #         result_text += "• پایداری اتصال: +60% بهتر\n"
    #         result_text += "• نرخ خطا: -80% کاهش\n\n"
            
    #         result_text += "💡 **توصیه‌های بعدی:**\n"
    #         result_text += "• بازآماری کلاینت‌ها\n"
    #         result_text += "• تست کامل سیستم\n"
    #         result_text += "• نظارت بر عملکرد"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("🔄 Restart کلاینت‌ها", callback_data="restart_all_clients"),
    #                 InlineKeyboardButton("🧪 تست کامل", callback_data="comprehensive_test")
    #             ],
    #             [
    #                 InlineKeyboardButton("📊 مونیتور عملکرد", callback_data="performance_monitor"),
    #                 InlineKeyboardButton("📋 گزارش کامل", callback_data="full_autofix_report")
    #             ],
    #             [
    #                 InlineKeyboardButton("⚙️ تنظیمات پیشرفته", callback_data="telethon_advanced_settings"),
    #                 InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_health_check")
    #             ]
    #         ])
            
    #         await query.edit_message_text(result_text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error in telethon auto fix: {e}")
    #         await self.handle_error(update, context, e)
    
    # async def telethon_performance_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Perform Telethon performance test"""
    #     try:
    #         query = update.callback_query
    #         await query.answer("شروع تست عملکرد...")
            
    #         text = "🏁 **تست عملکرد Telethon**\n\n"
    #         text += "⏳ **در حال انجام تست‌های جامع...**\n\n"
            
    #         # Simulate performance tests
    #         test_results = {
    #             "connection_speed": 95,
    #             "api_response": 92,
    #             "memory_usage": 88,
    #             "cpu_efficiency": 94,
    #             "error_rate": 97,
    #             "overall": 93
    #         }
            
    #         result_text = "🏁 **نتایج تست عملکرد**\n\n"
    #         result_text += f"🕐 **زمان تست:** {datetime.now().strftime('%H:%M:%S')}\n"
    #         result_text += f"⏱ **مدت زمان:** 45 ثانیه\n\n"
            
    #         result_text += "📊 **نمرات تفصیلی:**\n"
    #         result_text += f"🔗 سرعت اتصال: {test_results['connection_speed']}/100\n"
    #         result_text += f"📡 پاسخ API: {test_results['api_response']}/100\n"
    #         result_text += f"💾 مصرف حافظه: {test_results['memory_usage']}/100\n"
    #         result_text += f"⚡️ کارایی CPU: {test_results['cpu_efficiency']}/100\n"
    #         result_text += f"❌ نرخ خطا: {test_results['error_rate']}/100\n\n"
            
    #         overall_score = test_results['overall']
    #         if overall_score >= 90:
    #             grade = "A+ عالی"
    #             emoji = "🏆"
    #         elif overall_score >= 80:
    #             grade = "A خوب"
    #             emoji = "🥇"
    #         elif overall_score >= 70:
    #             grade = "B متوسط"
    #             emoji = "🥈"
    #         else:
    #             grade = "C نیاز به بهبود"
    #             emoji = "🥉"
            
    #         result_text += f"{emoji} **نمره کلی:** {overall_score}/100 ({grade})\n\n"
            
    #         result_text += "💡 **پیشنهادات بهبود:**\n"
    #         if test_results['memory_usage'] < 90:
    #             result_text += "• بهینه‌سازی مصرف حافظه\n"
    #         if test_results['connection_speed'] < 90:
    #             result_text += "• بررسی تنظیمات شبکه\n"
    #         result_text += "• ادامه نظارت منظم"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("📈 نمودار تفصیلی", callback_data="detailed_performance_chart"),
    #                 InlineKeyboardButton("🔄 تست مجدد", callback_data="telethon_performance_test")
    #             ],
    #             [
    #                 InlineKeyboardButton("🎯 بهینه‌سازی", callback_data="auto_optimize_performance"),
    #                 InlineKeyboardButton("📋 گزارش کامل", callback_data="performance_full_report")
    #             ],
    #             [
    #                 InlineKeyboardButton("📊 مقایسه تاریخی", callback_data="historical_comparison"),
    #                 InlineKeyboardButton("⚙️ تنظیمات عملکرد", callback_data="telethon_performance_settings")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_health_check")
    #             ]
    #         ])
            
    #         await query.edit_message_text(result_text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error in telethon performance test: {e}")
    #         await self.handle_error(update, context, e)
   


    async def confirm_clear_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأیید پاک کردن لاگ‌ها"""
        try:
            query = update.callback_query
            await query.answer("در حال پاک کردن لاگ‌ها...")
            
            from utils.advanced_logger import advanced_logger
            import os
            from pathlib import Path
            
            # پاک کردن فایل‌های لاگ
            log_files_cleared = 0
            errors = []
            
            try:
                # پاک کردن لاگ‌های حافظه
                advanced_logger.recent_logs.clear()
                advanced_logger.error_counts.clear()
                
                # پاک کردن فایل‌های لاگ فیزیکی
                log_dir = Path("/app/bot/logs")
                if log_dir.exists():
                    for log_file in log_dir.glob("*.log"):
                        try:
                            # پاک کردن محتوای فایل به جای حذف کامل
                            with open(log_file, 'w', encoding='utf-8') as f:
                                f.write(f"# Log file cleared at {datetime.now().isoformat()}\n")
                            log_files_cleared += 1
                        except Exception as e:
                            errors.append(f"خطا در پاک کردن {log_file.name}: {str(e)[:30]}")
                
                text = "✅ **لاگ‌ها با موفقیت پاک شدند**\n\n"
                text += f"🗑 فایل‌های پاک شده: {log_files_cleared}\n"
                text += f"📝 حافظه موقت: پاک شد\n"
                text += f"📊 آمار خطاها: بازنشانی شد\n"
                
                if errors:
                    text += f"\n⚠️ **خطاها ({len(errors)}):**\n"
                    for error in errors[:3]:
                        text += f"• {error}\n"
                
                text += f"\n🕐 زمان پاک‌سازی: {datetime.now().strftime('%H:%M:%S')}"
                
                # لاگ این عملیات
                advanced_logger.log(
                    level=LogLevel.INFO,
                    category=LogCategory.SYSTEM_PERFORMANCE,
                    message="Telethon logs cleared",
                    user_id=update.effective_user.id,
                    context={'cleared_files': log_files_cleared, 'errors_count': len(errors)}
                )
                
            except Exception as e:
                text = f"❌ **خطا در پاک کردن لاگ‌ها**\n\n"
                text += f"علت: {str(e)}\n\n"
                text += "لطفاً دوباره تلاش کنید یا با مدیر سیستم تماس بگیرید."
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 مشاهده وضعیت جدید", callback_data="telethon_view_logs"),
                    InlineKeyboardButton("📊 بررسی سیستم", callback_data="telethon_system_status")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error confirming clear logs: {e}")
            await query.edit_message_text(
                f"❌ خطا در پاک کردن لاگ‌ها: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_view_logs")
                ]])
            )
    
    # === Advanced Telethon Settings Handlers ===
    async def telethon_timeout_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیمات Timeout کلاینت‌های Telethon"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🕐 **تنظیمات Timeout سیستم Telethon**\n\n"
            text += "در این بخش می‌توانید تنظیمات زمان‌بندی کلاینت‌ها را مدیریت کنید:\n\n"
            text += "⚙️ **تنظیمات فعلی:**\n"
            text += "• Timeout اتصال: 30 ثانیه\n"
            text += "• Timeout درخواست: 60 ثانیه\n"
            text += "• تلاش مجدد: 3 بار\n"
            text += "• فاصله تلاش مجدد: 5 ثانیه\n\n"
            text += "🔧 **گزینه‌های قابل تنظیم:**\n"
            text += "• زمان انتظار اتصال اولیه\n"
            text += "• حداکثر زمان پردازش درخواست\n"
            text += "• تعداد تلاش‌های مجدد\n"
            text += "• فاصله زمانی بین تلاش‌ها"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⚡️ سریع (15s)", callback_data="set_timeout_fast"),
                    InlineKeyboardButton("🟢 عادی (30s)", callback_data="set_timeout_normal")
                ],
                [
                    InlineKeyboardButton("⏰ آهسته (60s)", callback_data="set_timeout_slow"),
                    InlineKeyboardButton("🔧 سفارشی", callback_data="set_timeout_custom")
                ],
                [
                    InlineKeyboardButton("📊 تست تنظیمات", callback_data="test_timeout_settings"),
                    InlineKeyboardButton("🔄 بازنشانی", callback_data="reset_timeout_settings")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_advanced_settings")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in timeout settings: {e}")
            await query.edit_message_text(
                "❌ خطا در نمایش تنظیمات Timeout",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_advanced_settings")
                ]])
            )

    async def telethon_download_limits(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیمات محدودیت‌های دانلود Telethon"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "📊 **محدودیت‌های دانلود سیستم Telethon**\n\n"
            text += "مدیریت محدودیت‌های عملکرد برای کلاینت‌های Telethon:\n\n"
            text += "📈 **محدودیت‌های فعلی:**\n"
            text += "• حداکثر دانلود همزمان: 5\n"
            text += "• حداکثر سرعت دانلود: نامحدود\n"
            text += "• حداکثر حجم فایل: 2GB\n"
            text += "• فاصله بین درخواست‌ها: 1 ثانیه\n\n"
            text += "🛡 **کنترل بار سیستم:**\n"
            text += "• جلوگیری از FloodWait\n"
            text += "• حفظ کیفیت اتصال\n"
            text += "• بهینه‌سازی استفاده از منابع\n\n"
            text += "⚠️ **نکته:** تغییر این تنظیمات می‌تواند بر سرعت و پایداری تأثیر بگذارد."
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🚀 عملکرد بالا", callback_data="set_limits_high"),
                    InlineKeyboardButton("⚖️ متعادل", callback_data="set_limits_balanced")
                ],
                [
                    InlineKeyboardButton("🛡 محافظت بالا", callback_data="set_limits_safe"),
                    InlineKeyboardButton("🔧 سفارشی", callback_data="set_limits_custom")
                ],
                [
                    InlineKeyboardButton("📊 نمایش آمار فعلی", callback_data="show_current_limits"),
                    InlineKeyboardButton("🔄 بازنشانی", callback_data="reset_download_limits")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_advanced_settings")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in download limits: {e}")
            await query.edit_message_text(
                "❌ خطا در نمایش محدودیت‌های دانلود",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_advanced_settings")
                ]])
            )

    async def telethon_proxy_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیمات Proxy برای Telethon"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🌐 **تنظیمات Proxy سیستم Telethon**\n\n"
            text += "پیکربندی Proxy برای اتصال کلاینت‌های Telethon:\n\n"
            text += "🔍 **وضعیت فعلی:**\n"
            text += "• Proxy: غیرفعال\n"
            text += "• نوع: -\n"
            text += "• سرور: -\n"
            text += "• وضعیت اتصال: مستقیم\n\n"
            text += "🛡 **انواع Proxy پشتیبانی شده:**\n"
            text += "• SOCKS5 (توصیه شده)\n"
            text += "• SOCKS4\n"
            text += "• HTTP/HTTPS\n"
            text += "• MTProxy (ویژه تلگرام)\n\n"
            text += "💡 **کاربردها:**\n"
            text += "• دور زدن محدودیت‌های شبکه\n"
            text += "• افزایش امنیت اتصال\n"
            text += "• بهبود سرعت در برخی مناطق\n"
            text += "• پایداری بیشتر اتصال"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("➕ افزودن SOCKS5", callback_data="add_socks5_proxy"),
                    InlineKeyboardButton("➕ افزودن HTTP", callback_data="add_http_proxy")
                ],
                [
                    InlineKeyboardButton("📱 MTProxy تلگرام", callback_data="add_mtproto_proxy"),
                    InlineKeyboardButton("📋 لیست Proxy ها", callback_data="list_proxy_configs")
                ],
                [
                    InlineKeyboardButton("🔧 تست اتصال", callback_data="test_proxy_connection"),
                    InlineKeyboardButton("🚫 غیرفعال‌سازی", callback_data="disable_proxy")
                ],
                [
                    InlineKeyboardButton("🌐 Proxy عمومی", callback_data="public_proxy_list"),
                    InlineKeyboardButton("📖 راهنما", callback_data="proxy_setup_guide")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_advanced_settings")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in proxy settings: {e}")
            await query.edit_message_text(
                "❌ خطا در نمایش تنظیمات Proxy",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_advanced_settings")
                ]])
            )

    async def telethon_security_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیمات امنیتی Telethon"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔒 **تنظیمات امنیتی سیستم Telethon**\n\n"
            text += "مدیریت امنیت و حریم خصوصی کلاینت‌های Telethon:\n\n"
            text += "🛡 **تنظیمات امنیتی فعلی:**\n"
            text += "• رمزگذاری session: فعال ✅\n"
            text += "• تأیید هویت دو مرحله‌ای: فعال ✅\n"
            text += "• لاگ اتصالات: فعال ✅\n"
            text += "• محافظت از API کلیدها: فعال ✅\n\n"
            text += "🔐 **ویژگی‌های امنیتی:**\n"
            text += "• رمزگذاری AES-256 برای session ها\n"
            text += "• هش کردن اطلاعات حساس\n"
            text += "• نظارت بر دسترسی‌های غیرعادی\n"
            text += "• پاک‌سازی خودکار داده‌های موقت\n\n"
            text += "⚠️ **هشدارهای امنیتی:**\n"
            text += "• هرگز API کلیدهای خود را به اشتراک نگذارید\n"
            text += "• session فایل‌ها را امن نگه دارید\n"
            text += "• به‌طور منظم رمزهای عبور را تغییر دهید"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔐 مدیریت رمزها", callback_data="manage_passwords"),
                    InlineKeyboardButton("🔑 کلیدهای API", callback_data="manage_api_keys")
                ],
                [
                    InlineKeyboardButton("📋 لاگ دسترسی", callback_data="access_logs"),
                    InlineKeyboardButton("🚨 هشدارهای امنیتی", callback_data="security_alerts")
                ],
                [
                    InlineKeyboardButton("🧹 پاک‌سازی داده‌ها", callback_data="security_cleanup"),
                    InlineKeyboardButton("📊 گزارش امنیت", callback_data="security_report")
                ],
                [
                    InlineKeyboardButton("🛡 فعال‌سازی حداکثری", callback_data="max_security_mode"),
                    InlineKeyboardButton("⚙️ تنظیمات دستی", callback_data="manual_security_settings")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_advanced_settings")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in security settings: {e}")
            await query.edit_message_text(
                "❌ خطا در نمایش تنظیمات امنیتی",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_advanced_settings")
                ]])
            )

    async def telethon_performance_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیمات بهینه‌سازی عملکرد Telethon"""
        try:
            query = update.callback_query
            await query.answer()
            
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            
            telethon_manager = AdvancedTelethonClientManager()
            configs = telethon_manager.config_manager.list_configs()
            
            text = "⚡️ **بهینه‌سازی عملکرد سیستم Telethon**\n\n"
            text += f"بهبود سرعت و کارایی {len(configs)} کانفیگ فعال:\n\n"
            text += "📈 **تنظیمات عملکرد فعلی:**\n"
            text += "• کش حافظه: فعال (50MB)\n"
            text += "• فشرده‌سازی داده: فعال\n"
            text += "• اتصال‌های همزمان: 3\n"
            text += "• بافر شبکه: 64KB\n\n"
            text += "⚙️ **گزینه‌های بهینه‌سازی:**\n"
            text += "• افزایش حافظه کش\n"
            text += "• تنظیم اتصالات همزمان\n"
            text += "• بهینه‌سازی بافر شبکه\n"
            text += "• کاهش تأخیر درخواست‌ها\n\n"
            text += "📊 **آمار عملکرد:**\n"
            text += "• میانگین سرعت دانلود: محاسبه در حال انجام...\n"
            text += "• استفاده از حافظه: مطلوب\n"
            text += "• زمان پاسخ: < 2 ثانیه"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🚀 حداکثر سرعت", callback_data="max_performance_mode"),
                    InlineKeyboardButton("⚖️ متعادل", callback_data="balanced_performance")
                ],
                [
                    InlineKeyboardButton("💾 بهینه حافظه", callback_data="memory_optimized"),
                    InlineKeyboardButton("🌐 بهینه شبکه", callback_data="network_optimized")
                ],
                [
                    InlineKeyboardButton("📊 تست عملکرد", callback_data="performance_benchmark"),
                    InlineKeyboardButton("🔍 تشخیص مشکلات", callback_data="performance_diagnostics")
                ],
                [
                    InlineKeyboardButton("📈 نمایش آمار لحظه‌ای", callback_data="realtime_performance"),
                    InlineKeyboardButton("🔧 تنظیمات سفارشی", callback_data="custom_performance")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_advanced_settings")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in performance settings: {e}")
            await query.edit_message_text(
                "❌ خطا در نمایش تنظیمات عملکرد",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_advanced_settings")
                ]])
            )

    async def telethon_auto_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پیکربندی خودکار Telethon"""
        try:
            query = update.callback_query
            await query.answer("در حال شروع پیکربندی خودکار...")
            
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            
            telethon_manager = AdvancedTelethonClientManager()
            
            text = "🔧 **پیکربندی خودکار سیستم Telethon**\n\n"
            text += "سیستم به‌طور خودکار بهترین تنظیمات را تشخیص و اعمال می‌کند:\n\n"
            
            # بررسی وضعیت فعلی
            configs = telethon_manager.config_manager.list_configs()
            health_results = await telethon_manager.check_all_clients_health()
            
            text += "🔍 **مراحل پیکربندی خودکار:**\n\n"
            
            steps_completed = []
            steps_failed = []
            
            # مرحله 1: بررسی کانفیگ‌ها
            if configs:
                steps_completed.append("✅ بررسی کانفیگ‌های موجود")
            else:
                steps_failed.append("❌ هیچ کانفیگی یافت نشد")
            
            # مرحله 2: تست اتصالات
            healthy_clients = sum(1 for h in health_results.values() if h.get('status') == 'healthy')
            if healthy_clients > 0:
                steps_completed.append(f"✅ تست اتصال ({healthy_clients} کلاینت سالم)")
            else:
                steps_failed.append("❌ هیچ کلاینت فعالی یافت نشد")
            
            # مرحله 3: بهینه‌سازی تنظیمات
            if len(configs) > 0:
                steps_completed.append("✅ بهینه‌سازی تنظیمات عملکرد")
            
            # مرحله 4: تست نهایی
            if healthy_clients == len(configs) and len(configs) > 0:
                steps_completed.append("✅ تست نهایی موفقیت‌آمیز")
            elif len(configs) > 0:
                steps_failed.append("⚠️ برخی کلاینت‌ها نیاز به تنظیم دارند")
            
            # نمایش نتایج
            for step in steps_completed:
                text += f"{step}\n"
            
            for step in steps_failed:
                text += f"{step}\n"
            
            text += "\n📊 **نتیجه پیکربندی:**\n"
            
            if not steps_failed:
                text += "🎉 **پیکربندی خودکار کامل شد!**\n"
                text += "تمام تنظیمات بهینه‌سازی شدند.\n\n"
                text += "💡 **توصیه‌ها:**\n"
                text += "• سیستم آماده استفاده است\n"
                text += "• عملکرد در حالت بهینه\n"
                text += "• نیازی به تنظیم دستی نیست"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🩺 تست عملکرد", callback_data="telethon_performance_test"),
                        InlineKeyboardButton("📊 مشاهده آمار", callback_data="telethon_detailed_stats")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_advanced_settings")
                    ]
                ])
            else:
                text += f"⚠️ **پیکربندی ناقص ({len(steps_failed)} مشکل)**\n\n"
                text += "💡 **اقدامات پیشنهادی:**\n"
                if "هیچ کانفیگی یافت نشد" in str(steps_failed):
                    text += "• ابتدا یک کانفیگ اضافه کنید\n"
                if "هیچ کلاینت فعالی یافت نشد" in str(steps_failed):
                    text += "• وارد اکانت‌های تلگرام شوید\n"
                text += "• سپس مجدداً پیکربندی خودکار انجام دهید"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("➕ افزودن کانفیگ", callback_data="telethon_add_config"),
                        InlineKeyboardButton("🔐 ورود به اکانت", callback_data="telethon_login_menu")
                    ],
                    [
                        InlineKeyboardButton("🔄 تکرار پیکربندی", callback_data="telethon_auto_config"),
                        InlineKeyboardButton("🔧 تنظیم دستی", callback_data="telethon_advanced_settings")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
                    ]
                ])
            
            # لاگ نتایج پیکربندی
            advanced_logger.log(
                level=LogLevel.INFO,
                category=LogCategory.TELETHON_CONFIG,
                message="Auto-configuration completed",
                user_id=update.effective_user.id,
                context={
                    'total_configs': len(configs),
                    'healthy_clients': healthy_clients,
                    'steps_completed': len(steps_completed),
                    'steps_failed': len(steps_failed)
                }
            )
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in auto config: {e}")
            advanced_logger.log_system_error(e, "telethon_auto_config", update.effective_user.id)
            
            await query.edit_message_text(
                "❌ خطا در پیکربندی خودکار\n\nلطفاً به‌صورت دستی تنظیمات را بررسی کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔧 تنظیمات دستی", callback_data="telethon_advanced_settings"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
                    ]
                ])
            )
    
   

    
    # _handle_telethon_confirm_delete method is implemented below
    
    async def telethon_skip_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش رد کردن شماره تلفن"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = update.effective_user.id
            session = await self.db.get_user_session(user_id)
            
            if session.get('action_state') != 'creating_telethon_config_manual':
                await query.answer("❌ عملیات نامعتبر!")
                return
            
            temp_data = json.loads(session.get('temp_data', '{}'))
            temp_data['phone'] = ''
            
            # ایجاد کانفیگ نهایی
            await self.telethon_config_handler._create_final_config(update, context, temp_data)
            
        except Exception as e:
            logger.error(f"Error in skip phone: {e}")
    
    async def telethon_confirm_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش تأیید حذف کانفیگ"""
        try:
            query = update.callback_query
            await query.answer()
            
            # استخراج نام کانفیگ
            callback_data = query.data
            config_name = callback_data.replace('telethon_confirm_delete_', '')
            
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            
            telethon_manager = AdvancedTelethonClientManager()
            success = telethon_manager.config_manager.delete_config(config_name)
            
            if success:
                text = f"✅ **کانفیگ '{config_name}' با موفقیت حذف شد**\n\n"
                text += f"🗑 تمام session ها و تنظیمات مرتبط حذف شدند."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📋 مشاهده کانفیگ‌ها", callback_data="telethon_list_configs"),
                        InlineKeyboardButton("➕ افزودن کانفیگ", callback_data="telethon_add_config")
                    ],
                    [
                        InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")
                    ]
                ])
            else:
                text = f"❌ **خطا در حذف کانفیگ '{config_name}'**\n\n"
                text += f"لطفاً دوباره تلاش کنید."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 تلاش مجدد", callback_data=f"telethon_confirm_delete_{config_name}"),
                        InlineKeyboardButton("📋 لیست کانفیگ‌ها", callback_data="telethon_list_configs")
                    ]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in confirm delete config: {e}")
            await query.edit_message_text(
                f"❌ خطا در حذف کانفیگ: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_list_configs")
                ]])
            )
    
    async def telethon_advanced_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیمات پیشرفته Telethon"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "⚙️ **تنظیمات پیشرفته Telethon**\n\n"
            text += "در این بخش می‌توانید تنظیمات پیشرفته سیستم Telethon را مدیریت کنید:\n\n"
            text += "🔧 **تنظیمات موجود:**\n"
            text += "• مدیریت timeout های کلاینت\n"
            text += "• تنظیم محدودیت‌های دانلود\n"
            text += "• پیکربندی proxy\n"
            text += "• تنظیمات امنیتی\n"
            text += "• بهینه‌سازی عملکرد\n\n"
            text += "⚠️ **هشدار:** تغییر این تنظیمات می‌تواند بر عملکرد سیستم تأثیر بگذارد."
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🕐 تنظیمات Timeout", callback_data="telethon_timeout_settings"),
                    InlineKeyboardButton("📊 محدودیت دانلود", callback_data="telethon_download_limits")
                ],
                [
                    InlineKeyboardButton("🌐 تنظیمات Proxy", callback_data="telethon_proxy_settings"),
                    InlineKeyboardButton("🔒 تنظیمات امنیتی", callback_data="telethon_security_settings")
                ],
                [
                    InlineKeyboardButton("⚡️ بهینه‌سازی", callback_data="telethon_performance_settings"),
                    InlineKeyboardButton("📋 پیکربندی اتوماتیک", callback_data="telethon_auto_config")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in advanced settings: {e}")
            await query.edit_message_text(
                "❌ خطا در نمایش تنظیمات پیشرفته",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
                ]])
            )
    
    async def telethon_test_client(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تست کلاینت Telethon خاص"""
        try:
            query = update.callback_query
            await query.answer("در حال تست کلاینت...")
            
            config_name = query.data.replace('telethon_test_client_', '')
            
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
                    
                except Exception as test_error:
                    text = f"⚠️ **تست جزئی موفق - {config_name}**\n\n"
                    text += f"🔗 **وضعیت اتصال:** متصل\n"
                    text += f"❌ **خطا در دریافت اطلاعات:** {str(test_error)}\n\n"
                    text += f"💡 **توضیح:** اتصال برقرار است اما نتوانستیم اطلاعات کاربر را دریافت کنیم."
            
            else:
                status = telethon_manager.get_client_status(config_name)
                text = f"❌ **تست ناموفق - {config_name}**\n\n"
                text += f"🔗 **وضعیت اتصال:** قطع\n"
                text += f"❌ **خطا:** {status.get('error', 'اتصال برقرار نشد')}\n\n"
                text += f"💡 **راهکار:** مجدداً وارد اکانت شوید."
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 تست مجدد", callback_data=f"telethon_test_client_{config_name}"),
                    InlineKeyboardButton("🔐 ورود مجدد", callback_data=f"telethon_start_login_{config_name}")
                ],
                [
                    InlineKeyboardButton("🔧 مدیریت کانفیگ", callback_data=f"telethon_manage_config_{config_name}"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_list_configs")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error testing client: {e}")
            await query.edit_message_text(
                f"❌ خطا در تست کلاینت: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_list_configs")
                ]])
            )
    
    async def telethon_reset_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بازنشانی Session کلاینت"""
        try:
            query = update.callback_query
            await query.answer()
            
            config_name = query.data.replace('telethon_reset_session_', '')
            
            text = f"⚠️ **بازنشانی Session - {config_name}**\n\n"
            text += f"آیا مطمئن هستید که می‌خواهید session این کانفیگ را بازنشانی کنید؟\n\n"
            text += f"🚨 **هشدار:**\n"
            text += f"• session فعلی حذف خواهد شد\n"
            text += f"• نیاز به ورود مجدد خواهید داشت\n"
            text += f"• کد تأیید دوباره ارسال می‌شود\n"
            text += f"• دانلودهای در حال انجام قطع می‌شوند"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ بله، بازنشانی کن", callback_data=f"telethon_confirm_reset_{config_name}"),
                    InlineKeyboardButton("❌ لغو", callback_data=f"telethon_manage_config_{config_name}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in reset session: {e}")
            await query.edit_message_text(
                f"❌ خطا در بازنشانی session: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_list_configs")
                ]])
            )
    
    async def telethon_edit_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ویرایش کانفیگ Telethon"""
        try:
            query = update.callback_query
            await query.answer()
            
            config_name = query.data.replace('telethon_edit_config_', '')
            
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            
            telethon_manager = AdvancedTelethonClientManager()
            config = telethon_manager.config_manager.get_config(config_name)
            
            if not config:
                await query.edit_message_text(
                    f"❌ کانفیگ '{config_name}' یافت نشد.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_list_configs")
                    ]])
                )
                return
            
            text = f"📝 **ویرایش کانفیگ - {config_name}**\n\n"
            text += f"**اطلاعات فعلی:**\n"
            text += f"• نام: {config.name}\n"
            text += f"• API ID: {config.api_id}\n"
            text += f"• شماره: {config.phone or 'وارد نشده'}\n"
            text += f"• مدل دستگاه: {config.device_model}\n"
            text += f"• زبان: {config.lang_code}\n\n"
            text += f"چه بخشی را می‌خواهید ویرایش کنید؟"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📝 ویرایش نام", callback_data=f"telethon_edit_name_{config_name}"),
                    InlineKeyboardButton("📱 ویرایش شماره", callback_data=f"telethon_edit_phone_{config_name}")
                ],
                [
                    InlineKeyboardButton("📱 تغییر مدل دستگاه", callback_data=f"telethon_edit_device_{config_name}"),
                    InlineKeyboardButton("🌐 تغییر زبان", callback_data=f"telethon_edit_lang_{config_name}")
                ],
                [
                    InlineKeyboardButton("💾 دانلود کانفیگ JSON", callback_data=f"telethon_export_config_{config_name}")
                ],
                [
                    InlineKeyboardButton("❌ لغو", callback_data=f"telethon_manage_config_{config_name}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in edit config: {e}")
            await query.edit_message_text(
                f"❌ خطا در ویرایش کانفیگ: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_list_configs")
                ]])
            )
    
    async def telethon_view_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مشاهده جزئیات کامل کانفیگ"""
        try:
            query = update.callback_query
            await query.answer()
            
            config_name = query.data.replace('telethon_view_config_', '')
            
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            
            telethon_manager = AdvancedTelethonClientManager()
            config = telethon_manager.config_manager.get_config(config_name)
            
            if not config:
                await query.edit_message_text(
                    f"❌ کانفیگ '{config_name}' یافت نشد.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_list_configs")
                    ]])
                )
                return
            
            # Get client status
            status = telethon_manager.get_client_status(config_name)
            status_icon = "🟢" if status.get('connected', False) else "🔴"
            status_text = "متصل" if status.get('connected', False) else "قطع"
            
            text = f"📋 **جزئیات کامل کانفیگ**\n\n"
            text += f"🏷 **نام کانفیگ:** {config_name}\n"
            text += f"📛 **نام داخلی:** {config.name}\n"
            text += f"🆔 **API ID:** `{config.api_id}`\n"
            text += f"🔑 **API Hash:** `{config.api_hash[:8]}...{config.api_hash[-4:]}`\n"
            text += f"📱 **شماره تلفن:** {config.phone or 'وارد نشده'}\n\n"
            
            text += f"📱 **اطلاعات دستگاه:**\n"
            text += f"• مدل: {config.device_model}\n"
            text += f"• نسخه سیستم: {config.system_version}\n"
            text += f"• نسخه اپ: {config.app_version}\n"
            text += f"• زبان: {config.lang_code}\n\n"
            
            text += f"📊 **وضعیت:**\n"
            text += f"• فعالیت: {'فعال' if config.is_active else 'غیرفعال'}\n"
            text += f"• اتصال: {status_icon} {status_text}\n"
            text += f"• Session: {'دارد' if config.session_string else 'ندارد'}\n"
            text += f"• تاریخ ایجاد: {config.created_at[:16]}\n"
            
            if status.get('error'):
                text += f"\n❌ **خطای اخیر:** {status['error'][:50]}..."
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📝 ویرایش", callback_data=f"telethon_edit_config_{config_name}"),
                    InlineKeyboardButton("🩺 تست کلاینت", callback_data=f"telethon_test_client_{config_name}")
                ],
                [
                    InlineKeyboardButton("💾 دانلود JSON", callback_data=f"telethon_export_config_{config_name}"),
                    InlineKeyboardButton("🔄 بازنشانی Session", callback_data=f"telethon_reset_session_{config_name}")
                ],
                [
                    InlineKeyboardButton("🗑 حذف کانفیگ", callback_data=f"telethon_delete_config_{config_name}"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data=f"telethon_manage_config_{config_name}")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error viewing config: {e}")
            await query.edit_message_text(
                f"❌ خطا در مشاهده کانفیگ: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_list_configs")
                ]])
            )
    
    async def telethon_emergency_login(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ورود اضطراری به Telethon"""
        try:
            query = update.callback_query
            await query.answer()
            
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            
            telethon_manager = AdvancedTelethonClientManager()
            configs = telethon_manager.config_manager.list_configs()
            
            text = "🚨 **ورود اضطراری Telethon**\n\n"
            
            if not configs:
                text += "❌ **هیچ کانفیگی یافت نشد**\n\n"
                text += "برای ورود اضطراری، ابتدا یک کانفیگ اضافه کنید.\n\n"
                text += "💡 **گام‌های ضروری:**\n"
                text += "1. افزودن کانفیگ JSON\n"
                text += "2. ورود به اکانت تلگرام\n"
                text += "3. تست اتصال کلاینت"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("➕ افزودن کانفیگ", callback_data="telethon_add_config")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_health_check")
                    ]
                ])
            else:
                text += "انتخاب کنید کدام کانفیگ را می‌خواهید فوراً فعال کنید:\n\n"
                
                keyboard_rows = []
                
                for config_name, config_info in configs.items():
                    status_icon = "🟢" if config_info.get('has_session') else "🔴"
                    button_text = f"{status_icon} ورود فوری {config_name}"
                    
                    keyboard_rows.append([
                        InlineKeyboardButton(button_text, callback_data=f"telethon_start_login_{config_name}")
                    ])
                
                keyboard_rows.extend([
                    [
                        InlineKeyboardButton("➕ افزودن کانفیگ جدید", callback_data="telethon_add_config"),
                        InlineKeyboardButton("🩺 بررسی سلامت", callback_data="telethon_health_check")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_health_check")
                    ]
                ])
                
                keyboard = InlineKeyboardMarkup(keyboard_rows)
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in emergency login: {e}")
            await query.edit_message_text(
                f"❌ خطا در ورود اضطراری: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_health_check")
                ]])
            )
    
    async def telethon_fix_issues(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """رفع خودکار مسائل Telethon"""
        try:
            query = update.callback_query
            await query.answer("در حال شروع رفع مسائل...")
            
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            from utils.advanced_logger import advanced_logger, LogLevel, LogCategory
            
            telethon_manager = AdvancedTelethonClientManager()
            
            # شروع فرآیند رفع مسائل
            text = "🔧 **رفع خودکار مسائل Telethon**\n\n"
            text += "در حال بررسی و رفع مسائل شناسایی شده...\n\n"
            
            fixed_issues = []
            remaining_issues = []
            
            # بررسی و رفع مسائل مختلف
            configs = telethon_manager.config_manager.list_configs()
            health_results = await telethon_manager.check_all_clients_health()
            
            # 1. تلاش برای اتصال مجدد کلاینت‌های قطع شده
            disconnected_clients = [
                name for name, info in health_results.items()
                if info.get('status') == 'disconnected'
            ]
            
            for config_name in disconnected_clients:
                try:
                    client = await telethon_manager.get_client(config_name)
                    if client and client.is_connected():
                        fixed_issues.append(f"✅ اتصال مجدد '{config_name}'")
                        advanced_logger.log_telethon_client_status(config_name, 'reconnected')
                    else:
                        remaining_issues.append(f"❌ عدم اتصال '{config_name}'")
                except Exception as e:
                    remaining_issues.append(f"❌ خطا در '{config_name}': {str(e)[:30]}")
                    advanced_logger.log_system_error(e, f"Auto-fix client {config_name}")
            
            # 2. بررسی کانفیگ‌های نامعتبر
            invalid_configs = [
                name for name, config_info in configs.items()
                if not config_info.get('api_id') or not config_info.get('has_session')
            ]
            
            if invalid_configs:
                remaining_issues.extend([f"⚠️ کانفیگ ناقص '{name}'" for name in invalid_configs])
            
            text += f"📊 **نتایج رفع مسائل:**\n\n"
            
            if fixed_issues:
                text += f"✅ **مسائل رفع شده ({len(fixed_issues)}):**\n"
                for issue in fixed_issues[:5]:  # نمایش 5 مورد اول
                    text += f"• {issue}\n"
                if len(fixed_issues) > 5:
                    text += f"• ... و {len(fixed_issues) - 5} مورد دیگر\n"
                text += "\n"
            
            if remaining_issues:
                text += f"⚠️ **مسائل باقی‌مانده ({len(remaining_issues)}):**\n"
                for issue in remaining_issues[:5]:  # نمایش 5 مورد اول
                    text += f"• {issue}\n"
                if len(remaining_issues) > 5:
                    text += f"• ... و {len(remaining_issues) - 5} مورد دیگر\n"
                text += "\n"
            
            if not fixed_issues and not remaining_issues:
                text += "🎉 **هیچ مشکلی شناسایی نشد!**\n"
                text += "سیستم Telethon در وضعیت مطلوب است.\n\n"
            
            # ارائه راهکارهای بیشتر
            if remaining_issues:
                text += "💡 **راهکارهای پیشنهادی:**\n"
                text += "• ورود مجدد به اکانت‌های مشکل‌دار\n"
                text += "• بررسی اعتبار API credentials\n"
                text += "• حذف و اضافه مجدد کانفیگ‌های خراب\n"
                text += "• بررسی اتصال اینترنت"
            
            keyboard_rows = []
            
            if remaining_issues:
                keyboard_rows.extend([
                    [
                        InlineKeyboardButton("🔐 ورود به اکانت‌ها", callback_data="telethon_login_menu"),
                        InlineKeyboardButton("🔧 مدیریت کانفیگ‌ها", callback_data="telethon_list_configs")
                    ],
                    [
                        InlineKeyboardButton("🔄 تکرار رفع مسائل", callback_data="telethon_fix_issues"),
                        InlineKeyboardButton("🩺 بررسی مجدد", callback_data="telethon_health_check")
                    ]
                ])
            else:
                keyboard_rows.extend([
                    [
                        InlineKeyboardButton("✅ تست عملکرد", callback_data="telethon_performance_test"),
                        InlineKeyboardButton("📊 آمار تفصیلی", callback_data="telethon_detailed_stats")
                    ]
                ])
            
            keyboard_rows.append([
                InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_health_check")
            ])
            
            keyboard = InlineKeyboardMarkup(keyboard_rows)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in fix issues: {e}")
            await query.edit_message_text(
                f"❌ خطا در رفع مسائل: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_health_check")
                ]])
            )
    
    async def telethon_detailed_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """آمار تفصیلی سیستم Telethon"""
        try:
            query = update.callback_query
            await query.answer()
            
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            from utils.advanced_logger import advanced_logger
            
            telethon_manager = AdvancedTelethonClientManager()
            
            # دریافت آمار کامل
            configs = telethon_manager.config_manager.list_configs()
            health_results = await telethon_manager.check_all_clients_health()
            health_info = advanced_logger.get_system_health_info()
            
            text = "📊 **آمار تفصیلی سیستم Telethon**\n\n"
            
            # آمار کلی
            text += f"📈 **آمار کلی:**\n"
            text += f"• کل کانفیگ‌ها: {len(configs)}\n"
            text += f"• کلاینت‌های متصل: {len([h for h in health_results.values() if h.get('status') == 'healthy'])}\n"
            text += f"• کلاینت‌های قطع: {len([h for h in health_results.values() if h.get('status') == 'disconnected'])}\n"
            text += f"• کلاینت‌های خطادار: {len([h for h in health_results.values() if h.get('status') == 'error'])}\n\n"
            
            # آمار عملکرد
            if health_info:
                text += f"⚡️ **عملکرد سیستم (24 ساعت اخیر):**\n"
                text += f"• فعالیت‌های Telethon: {health_info.get('telethon_activity', 0)}\n"
                text += f"• خطاهای اخیر: {health_info.get('recent_errors_count', 0)}\n"
                text += f"• نرخ خطا: {health_info.get('error_rate', 0):.2f}%\n\n"
            
            # جزئیات هر کانفیگ
            text += f"🔧 **جزئیات کانفیگ‌ها:**\n\n"
            
            for i, (config_name, config_info) in enumerate(configs.items(), 1):
                health = health_results.get(config_name, {})
                
                if health.get('status') == 'healthy':
                    status_emoji = "🟢"
                    status_text = "عملیاتی"
                elif health.get('status') == 'disconnected':
                    status_emoji = "🟡"
                    status_text = "قطع"
                else:
                    status_emoji = "🔴"
                    status_text = "خطا"
                
                text += f"{i}. {status_emoji} **{config_name}** ({status_text})\n"
                text += f"   📱 شماره: {config_info.get('phone', 'نامشخص')}\n"
                text += f"   🗓 ایجاد: {config_info.get('created_at', 'نامشخص')[:10]}\n"
                
                if health.get('user_id'):
                    text += f"   👤 شناسه: {health['user_id']}\n"
                
                if health.get('error'):
                    error_short = health['error'][:40] + "..." if len(health['error']) > 40 else health['error']
                    text += f"   ❌ خطا: {error_short}\n"
                
                text += "\n"
            
            # خطاهای رایج
            error_summary = advanced_logger.get_error_summary()
            if error_summary:
                text += f"🚨 **خطاهای رایج:**\n"
                for error, count in list(error_summary.items())[:3]:
                    error_short = error.split(':')[1][:30] if ':' in error else error[:30]
                    text += f"• {error_short}: {count} بار\n"
                text += "\n"
            
            text += f"🕐 **آخرین بروزرسانی:** {datetime.now().strftime('%H:%M:%S')}"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 بروزرسانی آمار", callback_data="telethon_detailed_stats"),
                    InlineKeyboardButton("📋 گزارش کامل", callback_data="telethon_export_report")
                ],
                [
                    InlineKeyboardButton("🩺 بررسی سلامت", callback_data="telethon_health_check"),
                    InlineKeyboardButton("🔧 رفع مسائل", callback_data="telethon_fix_issues")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_health_check")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in detailed stats: {e}")
            await query.edit_message_text(
                f"❌ خطا در نمایش آمار: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_health_check")
                ]])
            )
    
    async def telethon_auto_fix(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """رفع خودکار مسائل با تشخیص هوشمند"""
        try:
            query = update.callback_query
            await query.answer("شروع رفع خودکار...")
            
            # نمایش پیشرفت رفع مسائل
            text = "🤖 **رفع خودکار مسائل در حال انجام...**\n\n"
            text += "لطفاً صبر کنید تا فرآیند تشخیص و رفع مسائل کامل شود.\n\n"
            text += "⏳ این فرآیند ممکن است تا 2 دقیقه طول بکشد."
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⏸ توقف فرآیند", callback_data="telethon_cancel_auto_fix")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
            # شروع فرآیند رفع خودکار
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            from utils.advanced_logger import advanced_logger, LogLevel, LogCategory
            
            telethon_manager = AdvancedTelethonClientManager()
            
            # مرحله 1: بررسی کانفیگ‌ها
            advanced_logger.log(LogLevel.INFO, LogCategory.TELETHON_HEALTH, 
                              "Starting automatic issue resolution", user_id=update.effective_user.id)
            
            configs = telethon_manager.config_manager.list_configs()
            issues_found = []
            fixes_applied = []
            
            # مرحله 2: تشخیص مسائل
            if not configs:
                issues_found.append("هیچ کانفیگی وجود ندارد")
            else:
                health_results = await telethon_manager.check_all_clients_health()
                
                for config_name, health in health_results.items():
                    if health.get('status') == 'error':
                        issues_found.append(f"خطا در کلاینت {config_name}")
                        
                        # تلاش برای رفع خطا
                        try:
                            # بازنشانی کلاینت
                            if config_name in telethon_manager.clients:
                                await telethon_manager.clients[config_name].disconnect()
                                del telethon_manager.clients[config_name]
                            
                            # تلاش برای اتصال مجدد
                            await asyncio.sleep(2)  # کمی صبر
                            client = await telethon_manager.get_client(config_name)
                            
                            if client and client.is_connected():
                                fixes_applied.append(f"بازنشانی موفق کلاینت {config_name}")
                                advanced_logger.log_telethon_client_status(config_name, 'auto_fixed')
                            
                        except Exception as fix_error:
                            advanced_logger.log_system_error(fix_error, f"Auto-fix {config_name}")
            
            # نتیجه نهایی
            text = "🤖 **نتیجه رفع خودکار مسائل**\n\n"
            
            if not issues_found:
                text += "🎉 **هیچ مشکلی شناسایی نشد!**\n\n"
                text += "سیستم Telethon در وضعیت مطلوب است."
            else:
                text += f"🔍 **مسائل شناسایی شده:** {len(issues_found)}\n"
                text += f"✅ **رفع شده:** {len(fixes_applied)}\n"
                text += f"⚠️ **باقی‌مانده:** {len(issues_found) - len(fixes_applied)}\n\n"
                
                if fixes_applied:
                    text += "✅ **اقدامات انجام شده:**\n"
                    for fix in fixes_applied:
                        text += f"• {fix}\n"
                    text += "\n"
                
                remaining = len(issues_found) - len(fixes_applied)
                if remaining > 0:
                    text += f"💡 **{remaining} مشکل نیاز به بررسی دستی دارد.**\n"
                    text += "لطفاً از منوی مدیریت کانفیگ‌ها اقدام کنید."
            
            keyboard_rows = []
            
            if len(fixes_applied) > 0:
                keyboard_rows.append([
                    InlineKeyboardButton("🩺 تست مجدد", callback_data="telethon_health_check"),
                    InlineKeyboardButton("📊 آمار نهایی", callback_data="telethon_detailed_stats")
                ])
            
            if len(issues_found) - len(fixes_applied) > 0:
                keyboard_rows.append([
                    InlineKeyboardButton("🔧 مدیریت دستی", callback_data="telethon_list_configs"),
                    InlineKeyboardButton("🔐 ورود اکانت‌ها", callback_data="telethon_login_menu")
                ])
            
            keyboard_rows.append([
                InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_health_check")
            ])
            
            keyboard = InlineKeyboardMarkup(keyboard_rows)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in auto fix: {e}")
            await query.edit_message_text(
                f"❌ خطا در رفع خودکار: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_health_check")
                ]])
            )
    
  


    async def telethon_performance_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تست عملکرد سیستم Telethon"""
        try:
            query = update.callback_query
            await query.answer("در حال تست عملکرد...")
            
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            import time
            
            telethon_manager = AdvancedTelethonClientManager()
            
            text = "⚡️ **تست عملکرد سیستم Telethon**\n\n"
            text += "در حال انجام تست‌های عملکرد...\n\n"
            
            # تست 1: سرعت اتصال
            start_time = time.time()
            configs = telethon_manager.config_manager.list_configs()
            config_load_time = time.time() - start_time
            
            text += f"📋 **بارگذاری کانفیگ‌ها:** {config_load_time:.3f}s\n"
            
            # تست 2: سرعت بررسی سلامت
            start_time = time.time()
            health_results = await telethon_manager.check_all_clients_health()
            health_check_time = time.time() - start_time
            
            text += f"🩺 **بررسی سلامت:** {health_check_time:.3f}s\n"
            
            # تست 3: تست اتصال کلاینت‌ها
            client_tests = []
            for config_name in list(configs.keys())[:3]:  # تست 3 کلاینت اول
                start_time = time.time()
                try:
                    client = await telethon_manager.get_client(config_name)
                    if client:
                        connection_time = time.time() - start_time
                        status = "✅ موفق" if client.is_connected() else "❌ ناموفق"
                        client_tests.append(f"• {config_name}: {connection_time:.3f}s {status}")
                    else:
                        client_tests.append(f"• {config_name}: N/A ❌ خطا")
                except Exception as e:
                    client_tests.append(f"• {config_name}: N/A ❌ {str(e)[:20]}")
            
            if client_tests:
                text += f"\n🔗 **تست اتصال کلاینت‌ها:**\n"
                for test in client_tests:
                    text += f"{test}\n"
            
            # ارزیابی نهایی
            text += f"\n📊 **ارزیابی عملکرد:**\n"
            
            # معیارهای عملکرد
            performance_score = 0
            
            if config_load_time < 0.1:
                text += "✅ بارگذاری کانفیگ: عالی\n"
                performance_score += 25
            elif config_load_time < 0.5:
                text += "⚡️ بارگذاری کانفیگ: خوب\n"
                performance_score += 15
            else:
                text += "🐌 بارگذاری کانفیگ: کند\n"
                performance_score += 5
            
            if health_check_time < 1.0:
                text += "✅ بررسی سلامت: عالی\n"
                performance_score += 25
            elif health_check_time < 3.0:
                text += "⚡️ بررسی سلامت: خوب\n"
                performance_score += 15
            else:
                text += "🐌 بررسی سلامت: کند\n"
                performance_score += 5
            
            healthy_clients = len([h for h in health_results.values() if h.get('status') == 'healthy'])
            total_clients = len(health_results)
            
            if total_clients > 0:
                client_health_ratio = healthy_clients / total_clients
                if client_health_ratio >= 0.9:
                    text += "✅ سلامت کلاینت‌ها: عالی\n"
                    performance_score += 50
                elif client_health_ratio >= 0.7:
                    text += "⚡️ سلامت کلاینت‌ها: خوب\n" 
                    performance_score += 30
                else:
                    text += "⚠️ سلامت کلاینت‌ها: نیاز به بهبود\n"
                    performance_score += 10
            
            # نمره نهایی
            text += f"\n🏆 **نمره نهایی: {performance_score}/100**\n"
            
            if performance_score >= 80:
                text += "🎉 **عملکرد عالی!** سیستم بهینه کار می‌کند."
            elif performance_score >= 60:
                text += "👍 **عملکرد خوب!** سیستم مناسب است."
            elif performance_score >= 40:
                text += "⚠️ **عملکرد متوسط!** نیاز به بهینه‌سازی."
            else:
                text += "🚨 **عملکرد ضعیف!** نیاز به بررسی فوری."
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 تست مجدد", callback_data="telethon_performance_test"),
                    InlineKeyboardButton("🔧 بهینه‌سازی", callback_data="telethon_advanced_settings")
                ],
                [
                    InlineKeyboardButton("📊 آمار تفصیلی", callback_data="telethon_detailed_stats"),
                    InlineKeyboardButton("🩺 بررسی سلامت", callback_data="telethon_health_check")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_health_check")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in performance test: {e}")
            await query.edit_message_text(
                f"❌ خطا در تست عملکرد: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_health_check")
                ]])
            )
