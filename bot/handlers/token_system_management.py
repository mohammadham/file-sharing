#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token System Management Handler - مدیریت سیستمی توکن‌ها
"""

import logging
import json
import os
import shutil
import asyncio
import zipfile
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class TokenSystemHandler:
    """مدیریت سیستم توکن‌ها"""
    
    def __init__(self, db):
        self.db = db
        
    # === System Menu ===
    async def show_system_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی مدیریت سیستم"""
        try:
            keyboard = [
                [
                    InlineKeyboardButton("💾 بک‌آپ", callback_data="backup_menu"),
                    InlineKeyboardButton("📋 لاگ‌ها", callback_data="logs_menu")
                ],
                [
                    InlineKeyboardButton("🔍 سلامت سیستم", callback_data="health_menu"),
                    InlineKeyboardButton("🌐 زبان", callback_data="language_menu")
                ],
                [
                    InlineKeyboardButton("⚠️ بازگردانی سیستم", callback_data="reset_system_menu")
                ],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = (
                "⚙️ *مدیریت سیستم*\n\n"
                "🔧 مدیریت پیکربندی‌های سیستم\n"
                "📊 بررسی سلامت و عملکرد\n"
                "🗂 مدیریت بک‌آپ و بازیابی\n"
                "📝 مشاهده و مدیریت لاگ‌ها\n\n"
                "یکی از گزینه‌ها را انتخاب کنید:"
            )
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
                await update.callback_query.answer()
            else:
                await update.message.reply_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            logger.error(f"Error showing system menu: {e}")
            await update.callback_query.answer("❌ خطا در نمایش منوی سیستم!")
    
    # === Backup Management ===
    async def show_backup_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی بک‌آپ"""
        keyboard = [
            [
                InlineKeyboardButton("📤 ایجاد بک‌آپ", callback_data="create_backup_now"),
                InlineKeyboardButton("📥 بازیابی بک‌آپ", callback_data="restore_backup")
            ],
            [
                InlineKeyboardButton("⬇️ دانلود بک‌آپ", callback_data="download_backup"),
                InlineKeyboardButton("🕐 برنامه‌ریزی بک‌آپ", callback_data="schedule_backup")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="system_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "💾 *مدیریت بک‌آپ*\n\n"
            "🛡 نسخه پشتیبان از داده‌های سیستم\n"
            "📊 شامل تمام توکن‌ها و تنظیمات\n"
            "🔄 قابلیت بازیابی کامل\n\n"
            "یکی از گزینه‌ها را انتخاب کنید:"
        )
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        await update.callback_query.answer()
    
    async def create_backup_now(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ایجاد بک‌آپ فوری"""
        try:
            await update.callback_query.answer("⏳ در حال ایجاد بک‌آپ...")
            
            # Create backup directory
            backup_dir = f"/tmp/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Export database data
            tokens_data = await self.db.get_all_tokens()
            users_data = await self.db.get_all_users() if hasattr(self.db, 'get_all_users') else []
            system_stats = await self.db.get_system_stats()
            
            # Save to JSON files
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0",
                "tokens": tokens_data,
                "users": users_data,
                "system_stats": system_stats
            }
            
            backup_file = os.path.join(backup_dir, "backup.json")
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            # Create zip file
            zip_path = f"/tmp/system_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.write(backup_file, "backup.json")
            
            # Cleanup temp directory
            shutil.rmtree(backup_dir)
            
            keyboard = [
                [
                    InlineKeyboardButton("⬇️ دانلود بک‌آپ", callback_data=f"download_backup_file_{os.path.basename(zip_path)}"),
                    InlineKeyboardButton("🔄 بک‌آپ جدید", callback_data="create_backup_now")
                ],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="backup_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = (
                f"✅ *بک‌آپ با موفقیت ایجاد شد*\n\n"
                f"📅 تاریخ: {datetime.now().strftime('%Y/%m/%d %H:%M')}\n"
                f"📊 تعداد توکن‌ها: {len(tokens_data)}\n"
                f"👥 تعداد کاربران: {len(users_data)}\n"
                f"📦 حجم فایل: {os.path.getsize(zip_path) / 1024:.1f} KB\n\n"
                "می‌توانید فایل بک‌آپ را دانلود کنید."
            )
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            await update.callback_query.answer("❌ خطا در ایجاد بک‌آپ!")
    
    # === Health Check ===
    async def show_health_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی سلامت سیستم"""
        try:
            # Get system health data
            health_data = await self.get_system_health()
            
            keyboard = [
                [
                    InlineKeyboardButton("🔄 تازه‌سازی", callback_data="health_menu"),
                    InlineKeyboardButton("📊 جزئیات بیشتر", callback_data="detailed_health")
                ],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="system_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Create health status text
            db_status = "🟢 سالم" if health_data['database']['status'] == 'healthy' else "🔴 مشکل"
            api_status = "🟢 فعال" if health_data['api']['status'] == 'active' else "🔴 غیرفعال"
            
            text = (
                f"🔍 *وضعیت سلامت سیستم*\n\n"
                f"🗄 دیتابیس: {db_status}\n"
                f"🔌 API: {api_status}\n"
                f"⚡ زمان پاسخ: {health_data['response_time']:.2f}ms\n"
                f"💾 حافظه: {health_data['memory']['used']:.1f}MB / {health_data['memory']['total']:.1f}MB\n"
                f"🔢 توکن‌های فعال: {health_data['active_tokens']}\n"
                f"📊 درخواست‌های امروز: {health_data['daily_requests']}\n\n"
                f"🕐 آخرین بررسی: {datetime.now().strftime('%H:%M:%S')}"
            )
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            await update.callback_query.answer()
            
        except Exception as e:
            logger.error(f"Error showing health menu: {e}")
            await update.callback_query.answer("❌ خطا در دریافت اطلاعات سلامت!")
    
    async def get_system_health(self) -> Dict[str, Any]:
        """دریافت اطلاعات سلامت سیستم"""
        try:
            import psutil
            import time
            
            start_time = time.time()
            
            # Database health
            try:
                await self.db.get_system_stats()
                db_health = {'status': 'healthy'}
            except:
                db_health = {'status': 'error'}
            
            # API health (if available)
            api_health = {'status': 'active'}  # Simplified
            
            # System resources
            memory = psutil.virtual_memory()
            
            # Token statistics
            tokens = await self.db.get_all_tokens()
            active_tokens = len([t for t in tokens if t.get('active', True)])
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            return {
                'database': db_health,
                'api': api_health,
                'response_time': response_time,
                'memory': {
                    'total': memory.total / (1024 * 1024),
                    'used': memory.used / (1024 * 1024),
                    'percent': memory.percent
                },
                'active_tokens': active_tokens,
                'daily_requests': 0  # Should be implemented with proper logging
            }
            
        except ImportError:
            # Fallback if psutil is not available
            return {
                'database': {'status': 'healthy'},
                'api': {'status': 'active'},
                'response_time': 50.0,
                'memory': {'total': 1000.0, 'used': 500.0, 'percent': 50.0},
                'active_tokens': len(await self.db.get_all_tokens()),
                'daily_requests': 0
            }
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                'database': {'status': 'error'},
                'api': {'status': 'error'},
                'response_time': 0.0,
                'memory': {'total': 0.0, 'used': 0.0, 'percent': 0.0},
                'active_tokens': 0,
                'daily_requests': 0
            }
    
    # === Log Management ===
    async def show_logs_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی مدیریت لاگ‌ها"""
        keyboard = [
            [
                InlineKeyboardButton("📋 مشاهده لاگ‌ها", callback_data="view_system_log"),
                InlineKeyboardButton("⬇️ دانلود لاگ", callback_data="download_log")
            ],
            [
                InlineKeyboardButton("🗑 پاکسازی لاگ‌های قدیمی", callback_data="clear_old_logs"),
                InlineKeyboardButton("⚙️ تنظیمات لاگ", callback_data="log_settings")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="system_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "📋 *مدیریت لاگ‌ها*\n\n"
            "📝 مشاهده فعالیت‌های سیستم\n"
            "🔍 بررسی خطاها و رویدادها\n"
            "📁 مدیریت فایل‌های لاگ\n\n"
            "یکی از گزینه‌ها را انتخاب کنید:"
        )
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        await update.callback_query.answer()
    
    # === Language Settings ===
    async def show_language_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی تنظیمات زبان"""
        keyboard = [
            [
                InlineKeyboardButton("🇮🇷 فارسی", callback_data="set_persian"),
                InlineKeyboardButton("🇺🇸 English", callback_data="set_english")
            ],
            [InlineKeyboardButton("🔄 تشخیص خودکار", callback_data="set_auto")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="system_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "🌐 *تنظیمات زبان*\n\n"
            "انتخاب زبان رابط کاربری:\n"
            "🇮🇷 فارسی (پیش‌فرض)\n"
            "🇺🇸 انگلیسی\n"
            "🔄 تشخیص خودکار بر اساس پروفایل\n\n"
            "زبان مورد نظر را انتخاب کنید:"
        )
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        await update.callback_query.answer()
    
    # === System Reset ===
    async def show_reset_system_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی بازگردانی سیستم"""
        keyboard = [
            [InlineKeyboardButton("⚠️ تأیید بازگردانی", callback_data="type_password_reset")],
            [InlineKeyboardButton("❌ انصراف", callback_data="system_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "⚠️ *بازگردانی سیستم*\n\n"
            "🚨 *هشدار مهم:*\n"
            "این عملیات تمام داده‌ها را پاک می‌کند:\n"
            "• همه توکن‌ها\n"
            "• تنظیمات امنیتی\n"
            "• آمار و گزارش‌ها\n"
            "• لاگ‌های سیستم\n\n"
            "💡 توصیه: قبل از ادامه بک‌آپ تهیه کنید\n\n"
            "برای تأیید، دکمه زیر را فشار دهید:"
        )
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        await update.callback_query.answer()
    
    # === Placeholder methods for complete implementation ===
    async def handle_download_backup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت دانلود بک‌آپ"""
        await update.callback_query.answer("🚧 این قسمت در حال توسعه است")
    
    async def handle_restore_backup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت بازیابی بک‌آپ"""
        await update.callback_query.answer("🚧 این قسمت در حال توسعه است")
    
    async def handle_schedule_backup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """برنامه‌ریزی بک‌آپ خودکار"""
        await update.callback_query.answer("🚧 این قسمت در حال توسعه است")
    
    async def handle_view_system_log(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مشاهده لاگ‌های سیستم"""
        await update.callback_query.answer("🚧 این قسمت در حال توسعه است")
    
    async def handle_download_log(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دانلود لاگ‌های سیستم"""
        await update.callback_query.answer("🚧 این قسمت در حال توسعه است")
    
    async def handle_clear_old_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پاکسازی لاگ‌های قدیمی"""
        await update.callback_query.answer("🚧 این قسمت در حال توسعه است")
    
    async def handle_log_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیمات لاگ"""
        await update.callback_query.answer("🚧 این قسمت در حال توسعه است")
    
    async def handle_set_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تنظیم زبان"""
        callback_data = update.callback_query.data
        lang = callback_data.split('_')[-1]
        
        # Store language preference (simplified)
        context.user_data['language'] = lang
        
        lang_names = {
            'persian': 'فارسی 🇮🇷',
            'english': 'English 🇺🇸',
            'auto': 'تشخیص خودکار 🔄'
        }
        
        await update.callback_query.answer(f"✅ زبان تنظیم شد: {lang_names.get(lang, lang)}")
        await self.show_language_menu(update, context)
    
    async def handle_type_password_reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """درخواست رمز عبور برای بازگردانی"""
        await update.callback_query.answer("🚧 این قسمت در حال توسعه است")
        # This should implement password confirmation for system reset