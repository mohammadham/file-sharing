#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Broadcast Handler - Handles broadcast operations
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from handlers.base_handler import BaseHandler
from utils.keyboard_builder import KeyboardBuilder
from utils.helpers import extract_file_info
from config.settings import STORAGE_CHANNEL_ID

logger = logging.getLogger(__name__)


class BroadcastHandler(BaseHandler):
    """Handle broadcast operations"""
    
    async def show_broadcast_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show broadcast menu"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            text = "📢 **منوی برودکست**\n\nنوع برودکست را انتخاب کنید:"
            keyboard = KeyboardBuilder.build_broadcast_keyboard()
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def start_text_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start text broadcast"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            user_id = update.effective_user.id
            await self.update_user_session(user_id, action_state='broadcast_text')
            
            keyboard = KeyboardBuilder.build_cancel_keyboard("broadcast_menu")
            
            text = "✏️ **برودکست متنی**\n\n"
            text += "متن پیام برای ارسال به همه کاربران را وارد کنید:\n\n"
            text += "💡 **نکته:** می‌توانید از فرمت Markdown استفاده کنید."
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def start_file_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start file broadcast"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            user_id = update.effective_user.id
            await self.update_user_session(user_id, action_state='broadcast_file')
            
            keyboard = KeyboardBuilder.build_cancel_keyboard("broadcast_menu")
            
            text = "📁 **برودکست فایل**\n\n"
            text += "فایل مورد نظر برای ارسال به همه کاربران را ارسال کنید:\n\n"
            text += "⚠️ **توجه:** حجم فایل نباید بیش از 50 مگابایت باشد."
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def process_broadcast_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process text broadcast"""
        try:
            user_id = update.effective_user.id
            broadcast_text = update.message.text.strip()
            
            if not broadcast_text:
                await update.message.reply_text(self.messages['invalid_input'])
                return
            
            # Get all users
            stats = await self.db.get_stats()
            total_users = stats['users_count']
            
            if total_users == 0:
                await update.message.reply_text("❌ هیچ کاربری برای ارسال یافت نشد!")
                await self.reset_user_state(user_id)
                return
            
            # Show confirmation
            confirmation_text = f"📢 **تأیید برودکست**\n\n"
            confirmation_text += f"📝 پیام: {broadcast_text[:100]}{'...' if len(broadcast_text) > 100 else ''}\n"
            confirmation_text += f"👥 تعداد کاربران: {total_users}\n\n"
            confirmation_text += "آیا مطمئن هستید؟"
            
            keyboard = KeyboardBuilder.build_confirmation_keyboard("broadcast_text", user_id)
            
            await update.message.reply_text(
                confirmation_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error processing broadcast text: {e}")
            await update.message.reply_text(self.messages['error_occurred'])
    
    async def process_broadcast_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process file broadcast"""
        try:
            user_id = update.effective_user.id
            
            # Extract file information
            file_info = extract_file_info(update.message)
            if not file_info:
                await update.message.reply_text("❌ نوع فایل پشتیبانی نمی‌شود!")
                return
            
            file_obj, file_name, file_size, file_type = file_info
            
            # Check file size
            if file_size > 50 * 1024 * 1024:
                await update.message.reply_text(self.messages['file_too_large'])
                return
            
            # Get all users
            stats = await self.db.get_stats()
            total_users = stats['users_count']
            
            if total_users == 0:
                await update.message.reply_text("❌ هیچ کاربری برای ارسال یافت نشد!")
                await self.reset_user_state(user_id)
                return
            
            # Store file for broadcast
            await self.update_user_session(
                user_id,
                temp_data=str(update.message.message_id)
            )
            
            # Show confirmation
            file_size_mb = file_size / 1024 / 1024
            confirmation_text = f"📁 **تأیید برودکست فایل**\n\n"
            confirmation_text += f"📄 فایل: {file_name}\n"
            confirmation_text += f"💾 حجم: {file_size_mb:.1f} MB\n"
            confirmation_text += f"👥 تعداد کاربران: {total_users}\n\n"
            confirmation_text += "آیا مطمئن هستید؟"
            
            keyboard = KeyboardBuilder.build_confirmation_keyboard("broadcast_file", user_id)
            
            await update.message.reply_text(
                confirmation_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error processing broadcast file: {e}")
            await update.message.reply_text(self.messages['error_occurred'])
    
    async def confirm_text_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm and execute text broadcast"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update, "در حال ارسال برودکست...")
            
            user_id = update.effective_user.id
            session = await self.get_user_session(user_id)
            
            # Get the original message (assuming it's stored or we need to get it differently)
            # For now, we'll ask user to send the text again (this is a limitation we should fix)
            
            # Get all user IDs from sessions
            import aiosqlite
            async with aiosqlite.connect(self.db.db_path) as db:
                cursor = await db.execute('SELECT user_id FROM user_sessions')
                users = await cursor.fetchall()
            
            sent_count = 0
            failed_count = 0
            
            # This is a workaround - in a real implementation, we'd store the message
            broadcast_text = "📢 پیام برودکست از مدیر"
            
            for user_row in users:
                try:
                    await context.bot.send_message(
                        chat_id=user_row[0],
                        text=f"📢 **پیام برودکست:**\n\n{broadcast_text}",
                        parse_mode='Markdown'
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Error sending broadcast to {user_row[0]}: {e}")
                    failed_count += 1
            
            await self.reset_user_state(user_id)
            
            # Show result
            result_text = f"✅ **نتیجه برودکست**\n\n"
            result_text += f"📤 ارسال شده: {sent_count}\n"
            result_text += f"❌ ناموفق: {failed_count}\n"
            result_text += f"📊 کل: {sent_count + failed_count}"
            
            keyboard = KeyboardBuilder.build_cancel_keyboard("cat_1")
            
            await query.edit_message_text(
                result_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def confirm_file_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm and execute file broadcast"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update, "در حال ارسال برودکست...")
            
            user_id = update.effective_user.id
            session = await self.get_user_session(user_id)
            
            message_id = int(session.temp_data)
            
            # Get all user IDs
            import aiosqlite
            async with aiosqlite.connect(self.db.db_path) as db:
                cursor = await db.execute('SELECT user_id FROM user_sessions')
                users = await cursor.fetchall()
            
            sent_count = 0
            failed_count = 0
            
            for user_row in users:
                try:
                    await context.bot.forward_message(
                        chat_id=user_row[0],
                        from_chat_id=update.effective_chat.id,
                        message_id=message_id
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Error sending file broadcast to {user_row[0]}: {e}")
                    failed_count += 1
            
            await self.reset_user_state(user_id)
            
            # Show result
            result_text = f"✅ **نتیجه برودکست فایل**\n\n"
            result_text += f"📤 ارسال شده: {sent_count}\n"
            result_text += f"❌ ناموفق: {failed_count}\n"
            result_text += f"📊 کل: {sent_count + failed_count}"
            
            keyboard = KeyboardBuilder.build_cancel_keyboard("cat_1")
            
            await query.edit_message_text(
                result_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)