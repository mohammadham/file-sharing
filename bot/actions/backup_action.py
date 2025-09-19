#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Backup Action - Handle database backup operations
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from pathlib import Path

from handlers.base_handler import BaseHandler
from utils.keyboard_builder import KeyboardBuilder

logger = logging.getLogger(__name__)


class BackupAction(BaseHandler):
    """Handle backup operations"""
    
    async def create_backup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create database backup"""
        try:
            # Check if this is a command or callback
            if update.callback_query:
                query = update.callback_query
                await self.answer_callback_query(update, "در حال تهیه نسخه پشتیبان...")
                chat_id = query.message.chat_id
                message_method = query.edit_message_text
            else:
                chat_id = update.message.chat_id
                message_method = update.message.reply_text
            
            # Create backup
            backup_file = await self.db.create_backup()
            
            # Get backup info
            backup_path = Path(backup_file)
            backup_size = backup_path.stat().st_size
            backup_size_mb = backup_size / 1024 / 1024
            
            text = f"✅ **نسخه پشتیبان ایجاد شد**\n\n"
            text += f"📁 فایل: {backup_path.name}\n"
            text += f"💾 حجم: {backup_size_mb:.2f} MB\n"
            text += f"📅 تاریخ: {backup_path.stat().st_mtime}\n\n"
            text += "نسخه پشتیبان در سرور ذخیره شد."
            
            keyboard = KeyboardBuilder.build_cancel_keyboard("cat_1")
            
            # Send backup file to admin (if needed)
            try:
                with open(backup_file, 'rb') as f:
                    await context.bot.send_document(
                        chat_id=chat_id,
                        document=f,
                        filename=backup_path.name,
                        caption="🗄 نسخه پشتیبان دیتابیس"
                    )
            except Exception as e:
                logger.warning(f"Could not send backup file: {e}")
            
            await message_method(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            error_text = "❌ خطا در ایجاد نسخه پشتیبان!"
            
            if update.callback_query:
                await update.callback_query.edit_message_text(error_text)
            else:
                await update.message.reply_text(error_text)
    
    async def list_backups(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List available backups"""
        try:
            from config.settings import BACKUP_PATH
            
            if not BACKUP_PATH.exists():
                await update.message.reply_text("❌ هیچ نسخه پشتیبانی موجود نیست!")
                return
            
            backup_files = list(BACKUP_PATH.glob("backup_*.db"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            if not backup_files:
                await update.message.reply_text("❌ هیچ نسخه پشتیبانی موجود نیست!")
                return
            
            text = "🗄 **فهرست نسخه‌های پشتیبان**\n\n"
            
            for i, backup_file in enumerate(backup_files[:10], 1):
                size_mb = backup_file.stat().st_size / 1024 / 1024
                mtime = backup_file.stat().st_mtime
                from datetime import datetime
                date_str = datetime.fromtimestamp(mtime).strftime("%Y/%m/%d %H:%M")
                
                text += f"**{i}.** {backup_file.name}\n"
                text += f"   💾 {size_mb:.2f} MB | 📅 {date_str}\n\n"
            
            if len(backup_files) > 10:
                text += f"... و {len(backup_files) - 10} فایل دیگر"
            
            keyboard = KeyboardBuilder.build_cancel_keyboard("cat_1")
            await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            await update.message.reply_text("❌ خطا در نمایش فهرست نسخه‌های پشتیبان!")
    
    async def schedule_auto_backup(self):
        """Schedule automatic backup (to be called periodically)"""
        try:
            # This would be called by the scheduler
            backup_file = await self.db.create_backup()
            logger.info(f"Automatic backup created: {backup_file}")
            
            # Clean up old backups (keep last 10)
            from config.settings import BACKUP_PATH
            if BACKUP_PATH.exists():
                backup_files = list(BACKUP_PATH.glob("backup_*.db"))
                backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                # Remove old backups
                for old_backup in backup_files[10:]:
                    try:
                        old_backup.unlink()
                        logger.info(f"Removed old backup: {old_backup}")
                    except Exception as e:
                        logger.warning(f"Could not remove old backup {old_backup}: {e}")
            
        except Exception as e:
            logger.error(f"Error in automatic backup: {e}")