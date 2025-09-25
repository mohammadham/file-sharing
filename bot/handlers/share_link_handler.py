#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Share Link Handler - Handles share link operations
"""

import json
import logging
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from handlers.base_handler import BaseHandler
from utils.keyboard_builder import KeyboardBuilder
from utils.helpers import format_file_size, escape_filename_for_markdown
from models.database_models import Link
from config.settings import STORAGE_CHANNEL_ID

logger = logging.getLogger(__name__)


class ShareLinkHandler(BaseHandler):
    """Handle share link operations"""

    def __init__(self, db):
        super().__init__(db)
        
    async def _handle_share_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE, short_code: str):
        """Handle share link access"""
        try:
            # Get link from database
            link = await self.db.get_link_by_code(short_code)
            
            if not link:
                await update.message.reply_text(
                    "❌ لینک یافت نشد یا منقضی شده است!",
                    parse_mode='Markdown'
                )
                return
            
            # Increment access count
            await self.db.increment_link_access(short_code)
            
            if link.link_type == "file":
                await self._handle_file_share_link(update, context, link)
            elif link.link_type == "category":
                await self._handle_category_share_link(update, context, link)
            elif link.link_type == "collection":
                await self._handle_collection_share_link(update, context, link)
            else:
                await update.message.reply_text("❌ نوع لینک پشتیبانی نمی‌شود!")
                
        except Exception as e:
            logger.error(f"Error handling share link: {e}")
            await update.message.reply_text("❌ خطا در پردازش لینک!")
    
    async def _handle_file_share_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE, link):
        """Handle shared file link"""
        try:
            file = await self.db.get_file_by_id(link.target_id)
            if not file:
                await update.message.reply_text("❌ فایل یافت نشد!")
                return
            
            category = await self.db.get_category_by_id(file.category_id)
            category_name = category.name if category else "نامشخص"
            
            from utils.helpers import build_file_info_text, format_file_size
            
            text = f"📄 **فایل اشتراک‌گذاری شده**\n\n"
            text += f"📁 دسته: {category_name}\n"
            text += f"📊 بازدید: {link.access_count} بار\n\n"
            text += build_file_info_text(file.to_dict(), category_name)
            
            # Create download keyboard
            keyboard = KeyboardBuilder.build_shared_file_keyboard(file, link)
            
            await update.message.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in file share link: {e}")
            await update.message.reply_text("❌ خطا در نمایش فایل!")
    
    async def _handle_category_share_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE, link):
        """Handle shared category link"""
        try:
            category = await self.db.get_category_by_id(link.target_id)
            if not category:
                await update.message.reply_text("❌ دسته یافت نشد!")
                return
            
            files = await self.db.get_files(link.target_id, limit=1000)
            from utils.helpers import format_file_size
            
            total_size = sum(f.file_size for f in files)
            
            text = f"📂 **دسته اشتراک‌گذاری شده**\n\n"
            text += f"📁 **نام دسته:** {category.name}\n"
            text += f"📊 **تعداد فایل:** {len(files)}\n"
            text += f"💾 **حجم کل:** {format_file_size(total_size)}\n"
            text += f"📈 **بازدید:** {link.access_count} بار\n\n"
            
            if category.description:
                text += f"📝 **توضیحات:** {category.description}\n\n"
            
            text += f"💡 می‌توانید فایل‌ها را مشاهده و دانلود کنید."
            
            keyboard = KeyboardBuilder.build_shared_category_keyboard(category, link)
            
            await update.message.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in category share link: {e}")
            await update.message.reply_text("❌ خطا در نمایش دسته!")
    
    async def _handle_collection_share_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE, link):
        """Handle shared collection link"""
        try:
            import json
            file_ids = json.loads(link.target_ids)
            
            files = []
            total_size = 0
            for file_id in file_ids:
                file = await self.db.get_file_by_id(file_id)
                if file:
                    files.append(file)
                    total_size += file.file_size
            
            if not files:
                await update.message.reply_text("❌ فایل‌های مجموعه یافت نشد!")
                return
            
            from utils.helpers import format_file_size
            
            text = f"📦 **مجموعه فایل‌های اشتراک‌گذاری شده**\n\n"
            text += f"📊 **تعداد فایل:** {len(files)}\n"
            text += f"💾 **حجم کل:** {format_file_size(total_size)}\n"
            text += f"📈 **بازدید:** {link.access_count} بار\n\n"
            text += f"📋 **فایل‌ها:**\n"
            
            for i, file in enumerate(files[:5], 1):
                # Escape filename for Markdown
                from utils.helpers import escape_filename_for_markdown
                safe_filename = escape_filename_for_markdown(file.file_name)
                text += f"{i}. {safe_filename} ({format_file_size(file.file_size)})\n"
            
            if len(files) > 5:
                text += f"... و {len(files) - 5} فایل دیگر"
            
            keyboard = KeyboardBuilder.build_shared_collection_keyboard(link)
            
            await update.message.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in collection share link: {e}")
            await update.message.reply_text("❌ خطا در نمایش مجموعه!")

    async def _handle_category_share_link_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, link):
        """Handle shared category link for edit message"""
        try:
            category = await self.db.get_category_by_id(link.target_id)
            if not category:
                await update.callback_query.edit_message_text("❌ دسته یافت نشد!")
                return
            
            files = await self.db.get_files(link.target_id, limit=1000)
            from utils.helpers import format_file_size
            
            total_size = sum(f.file_size for f in files)
            
            text = f"📂 **دسته اشتراک‌گذاری شده**\n\n"
            text += f"📁 **نام دسته:** {category.name}\n"
            text += f"📊 **تعداد فایل:** {len(files)}\n"
            text += f"💾 **حجم کل:** {format_file_size(total_size)}\n"
            text += f"📈 **بازدید:** {link.access_count} بار\n\n"
            
            if category.description:
                text += f"📝 **توضیحات:** {category.description}\n\n"
            
            text += f"💡 می‌توانید فایل‌ها را مشاهده و دانلود کنید."
            
            keyboard = KeyboardBuilder.build_shared_category_keyboard(category, link)
            
            await update.callback_query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in category share link edit: {e}")
            await update.callback_query.edit_message_text("❌ خطا در نمایش دسته!")
    
    async def _handle_collection_share_link_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, link):
        """Handle shared collection link for edit message"""
        try:
            import json
            file_ids = json.loads(link.target_ids)
            
            files = []
            total_size = 0
            for file_id in file_ids:
                file = await self.db.get_file_by_id(file_id)
                if file:
                    files.append(file)
                    total_size += file.file_size
            
            if not files:
                await update.callback_query.edit_message_text("❌ فایل‌های مجموعه یافت نشد!")
                return
            
            from utils.helpers import format_file_size
            
            text = f"📦 **مجموعه فایل‌های اشتراک‌گذاری شده**\n\n"
            text += f"📊 **تعداد فایل:** {len(files)}\n"
            text += f"💾 **حجم کل:** {format_file_size(total_size)}\n"
            text += f"📈 **بازدید:** {link.access_count} بار\n\n"
            text += f"📋 **فایل‌ها:**\n"
            
            for i, file in enumerate(files[:5], 1):
                # Escape filename for Markdown
                from utils.helpers import escape_filename_for_markdown
                safe_filename = escape_filename_for_markdown(file.file_name)
                text += f"{i}. {safe_filename} ({format_file_size(file.file_size)})\n"
            
            if len(files) > 5:
                text += f"... و {len(files) - 5} فایل دیگر"
            
            keyboard = KeyboardBuilder.build_shared_collection_keyboard(link)
            
            await update.callback_query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in collection share link edit: {e}")
            await update.callback_query.edit_message_text("❌ خطا در نمایش مجموعه!")

    
    async def handle_share_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE, short_code: str):
        """Handle share link access"""
        try:
            # Get link from database
            link = await self.db.get_link_by_code(short_code)
            
            if not link:
                await update.message.reply_text(
                    "❌ لینک یافت نشد یا منقضی شده است!",
                    parse_mode='Markdown'
                )
                return
            
            # Increment access count
            await self.db.increment_link_access(short_code)
            
            if link.link_type == "file":
                await self.handle_file_share_link(update, context, link)
            elif link.link_type == "category":
                await self.handle_category_share_link(update, context, link)
            elif link.link_type == "collection":
                await self.handle_collection_share_link(update, context, link)
            else:
                await update.message.reply_text("❌ نوع لینک پشتیبانی نمی‌شود!")
                
        except Exception as e:
            logger.error(f"Error handling share link: {e}")
            await update.message.reply_text("❌ خطا در پردازش لینک!")
    
    async def handle_file_share_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE, link):
        """Handle shared file link"""
        try:
            file = await self.db.get_file_by_id(link.target_id)
            if not file:
                await update.message.reply_text("❌ فایل یافت نشد!")
                return
            
            category = await self.db.get_category_by_id(file.category_id)
            category_name = category.name if category else "نامشخص"
            
            from utils.helpers import build_file_info_text
            
            text = f"📄 **فایل اشتراک‌گذاری شده**\n\n"
            text += f"📁 دسته: {category_name}\n"
            text += f"📊 بازدید: {link.access_count} بار\n\n"
            text += build_file_info_text(file.to_dict(), category_name)
            
            # Create download keyboard
            keyboard = KeyboardBuilder.build_shared_file_keyboard(file, link)
            
            await update.message.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in file share link: {e}")
            await update.message.reply_text("❌ خطا در نمایش فایل!")
    
    async def handle_category_share_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE, link):
        """Handle shared category link"""
        try:
            category = await self.db.get_category_by_id(link.target_id)
            if not category:
                await update.message.reply_text("❌ دسته یافت نشد!")
                return
            
            files = await self.db.get_files(link.target_id, limit=1000)
            
            total_size = sum(f.file_size for f in files)
            
            text = f"📂 **دسته اشتراک‌گذاری شده**\n\n"
            text += f"📁 **نام دسته:** {category.name}\n"
            text += f"📊 **تعداد فایل:** {len(files)}\n"
            text += f"💾 **حجم کل:** {format_file_size(total_size)}\n"
            text += f"📈 **بازدید:** {link.access_count} بار\n\n"
            
            if category.description:
                text += f"📝 **توضیحات:** {category.description}\n\n"
            
            text += f"💡 می‌توانید فایل‌ها را مشاهده و دانلود کنید."
            
            keyboard = KeyboardBuilder.build_shared_category_keyboard(category, link)
            
            await update.message.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in category share link: {e}")
            await update.message.reply_text("❌ خطا در نمایش دسته!")
    
    async def handle_collection_share_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE, link):
        """Handle shared collection link"""
        try:
            file_ids = json.loads(link.target_ids)
            
            files = []
            total_size = 0
            for file_id in file_ids:
                file = await self.db.get_file_by_id(file_id)
                if file:
                    files.append(file)
                    total_size += file.file_size
            
            if not files:
                await update.message.reply_text("❌ فایل‌های مجموعه یافت نشد!")
                return
            
            text = f"📦 **مجموعه فایل‌های اشتراک‌گذاری شده**\n\n"
            text += f"📊 **تعداد فایل:** {len(files)}\n"
            text += f"💾 **حجم کل:** {format_file_size(total_size)}\n"
            text += f"📈 **بازدید:** {link.access_count} بار\n\n"
            text += f"📋 **فایل‌ها:**\n"
            
            for i, file in enumerate(files[:5], 1):
                # Escape filename for Markdown
                safe_filename = escape_filename_for_markdown(file.file_name)
                text += f"{i}. {safe_filename} ({format_file_size(file.file_size)})\n"
            
            if len(files) > 5:
                text += f"... و {len(files) - 5} فایل دیگر"
            
            keyboard = KeyboardBuilder.build_shared_collection_keyboard(link)
            
            await update.message.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in collection share link: {e}")
            await update.message.reply_text("❌ خطا در نمایش مجموعه!")
    async def browse_shared_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle browsing shared category files - FIXED"""
        try:
            query = update.callback_query
            await query.answer()
            
            short_code = query.data.split('_')[3]
            link = await self.db.get_link_by_code(short_code)
            
            if not link or link.link_type != "category":
                await query.answer("❌ لینک نامعتبر!")
                return
            
            category = await self.db.get_category_by_id(link.target_id)
            files = await self.db.get_files(link.target_id, limit=50)
            
            if not files:
                await query.edit_message_text("❌ هیچ فایلی در این دسته موجود نیست!")
                return
            
            text = f"📂 **فایل‌های دسته '{category.name}'**\n\n"
            
            # Build file list with download buttons
            from utils.helpers import format_file_size
            keyboard = []
            
            for i, file in enumerate(files, 1):
                # Escape filename for Markdown
                from utils.helpers import escape_filename_for_markdown
                safe_filename = escape_filename_for_markdown(file.file_name)
                text += f"{i}. **{safe_filename}**\n"
                text += f"   💾 {format_file_size(file.file_size)} | {file.file_type}\n\n"
                
                # Add individual file download button
                keyboard.append([
                    InlineKeyboardButton(
                        f"📥 دانلود {file.file_name[:20]}...", 
                        callback_data=f"download_shared_file_{file.id}_{short_code}"
                    )
                ])
            
            # Add back button
            keyboard.append([
                InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_to_shared_{short_code}")
            ])
            
            await query.edit_message_text(
                text, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error browsing shared category: {e}")
            await query.answer("❌ خطا در مشاهده فایل‌ها!")
            
    # async def browse_shared_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Handle browsing shared category files"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         short_code = query.data.split('_')[3]
    #         link = await self.db.get_link_by_code(short_code)
            
    #         if not link or link.link_type != "category":
    #             await query.answer("❌ لینک نامعتبر!")
    #             return
            
    #         category = await self.db.get_category_by_id(link.target_id)
    #         files = await self.db.get_files(link.target_id, limit=50)
            
    #         if not files:
    #             await query.edit_message_text("❌ هیچ فایلی در این دسته موجود نیست!")
    #             return
            
    #         text = f"📂 **فایل‌های دسته '{category.name}'**\n\n"
            
    #         # Build file list with download buttons
    #         keyboard = []
            
    #         for i, file in enumerate(files, 1):
    #             # Escape filename for Markdown
    #             safe_filename = escape_filename_for_markdown(file.file_name)
    #             text += f"{i}. **{safe_filename}**\n"
    #             text += f"   💾 {format_file_size(file.file_size)} | {file.file_type}\n\n"
                
    #             # Add individual file download button
    #             keyboard.append([
    #                 InlineKeyboardButton(
    #                     f"📥 دانلود {file.file_name[:20]}...", 
    #                     callback_data=f"download_shared_file_{file.id}_{short_code}"
    #                 )
    #             ])
            
    #         # Add back button
    #         keyboard.append([
    #             InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_to_shared_{short_code}")
    #         ])
            
    #         await query.edit_message_text(
    #             text, 
    #             reply_markup=InlineKeyboardMarkup(keyboard), 
    #             parse_mode='Markdown'
    #         )
            
    #     except Exception as e:
    #         logger.error(f"Error browsing shared category: {e}")
    #         await query.answer("❌ خطا در مشاهده فایل‌ها!")
    async def browse_shared_collection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle browsing shared collection files - FIXED"""
        try:
            query = update.callback_query
            await query.answer()
            
            short_code = query.data.split('_')[3]
            link = await self.db.get_link_by_code(short_code)
            
            if not link or link.link_type != "collection":
                await query.answer("❌ لینک نامعتبر!")
                return
            
            import json
            file_ids = json.loads(link.target_ids)
            
            files = []
            for file_id in file_ids:
                file = await self.db.get_file_by_id(file_id)
                if file:
                    files.append(file)
            
            if not files:
                await query.edit_message_text("❌ فایل‌های مجموعه یافت نشد!")
                return
            
            text = f"📦 **فایل‌های مجموعه**\n\n"
            
            # Build file list with download buttons
            from utils.helpers import format_file_size
            keyboard = []
            
            for i, file in enumerate(files, 1):
                # Escape filename for Markdown
                from utils.helpers import escape_filename_for_markdown
                safe_filename = escape_filename_for_markdown(file.file_name)
                text += f"{i}. **{safe_filename}**\n"
                text += f"   💾 {format_file_size(file.file_size)} | {file.file_type}\n\n"
                
                # Add individual file download button
                keyboard.append([
                    InlineKeyboardButton(
                        f"📥 دانلود {file.file_name[:20]}...", 
                        callback_data=f"download_shared_file_{file.id}_{short_code}"
                    )
                ])
            
            # Add back button
            keyboard.append([
                InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_to_shared_{short_code}")
            ])
            
            await query.edit_message_text(
                text, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error browsing shared collection: {e}")
            await query.answer("❌ خطا در مشاهده فایل‌ها!")
    
    # async def browse_shared_collection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Handle browsing shared collection files"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         short_code = query.data.split('_')[3]
    #         link = await self.db.get_link_by_code(short_code)
            
    #         if not link or link.link_type != "collection":
    #             await query.answer("❌ لینک نامعتبر!")
    #             return
            
    #         file_ids = json.loads(link.target_ids)
            
    #         files = []
    #         for file_id in file_ids:
    #             file = await self.db.get_file_by_id(file_id)
    #             if file:
    #                 files.append(file)
            
    #         if not files:
    #             await query.edit_message_text("❌ فایل‌های مجموعه یافت نشد!")
    #             return
            
    #         text = f"📦 **فایل‌های مجموعه**\n\n"
            
    #         # Build file list with download buttons
    #         keyboard = []
            
    #         for i, file in enumerate(files, 1):
    #             # Escape filename for Markdown
    #             safe_filename = escape_filename_for_markdown(file.file_name)
    #             text += f"{i}. **{safe_filename}**\n"
    #             text += f"   💾 {format_file_size(file.file_size)} | {file.file_type}\n\n"
                
    #             # Add individual file download button
    #             keyboard.append([
    #                 InlineKeyboardButton(
    #                     f"📥 دانلود {file.file_name[:20]}...", 
    #                     callback_data=f"download_shared_file_{file.id}_{short_code}"
    #                 )
    #             ])
            
    #         # Add back button
    #         keyboard.append([
    #             InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_to_shared_{short_code}")
    #         ])
            
    #         await query.edit_message_text(
    #             text, 
    #             reply_markup=InlineKeyboardMarkup(keyboard), 
    #             parse_mode='Markdown'
    #         )
            
    #     except Exception as e:
    #         logger.error(f"Error browsing shared collection: {e}")
    #         await query.answer("❌ خطا در مشاهده فایل‌ها!")
    async def download_shared_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle downloading shared file - FIXED"""
        try:
            query = update.callback_query
            await query.answer("در حال ارسال فایل...")
            
            parts = query.data.split('_')
            logger.info(f"Download shared file callback data: {query.data}, parts: {parts}")
            
            # Validate parts array
            if len(parts) < 5:
                await query.answer("❌ داده callback نامعتبر!")
                logger.error(f"Invalid callback data format: {query.data}")
                return
            
            try:
                file_id = int(parts[3])
                short_code = parts[4]
                logger.info(f"Parsed file_id: {file_id}, short_code: {short_code}")
            except ValueError as ve:
                logger.error(f"Error parsing callback data {query.data}: {ve}")
                await query.answer("❌ خطا در پردازش داده!")
                return
            
            logger.info(f"Getting file by id: {file_id}")
            file = await self.db.get_file_by_id(file_id)
            if not file:
                await query.answer("❌ فایل یافت نشد!")
                return
            
            logger.info(f"File found: {file.file_name}, storage_message_id: {file.storage_message_id}")
            
            # Forward file from storage channel
            from config.settings import STORAGE_CHANNEL_ID
            try:
                logger.info(f"Forwarding message from channel {STORAGE_CHANNEL_ID}, message_id: {file.storage_message_id}")
                await context.bot.forward_message(
                    chat_id=update.effective_chat.id,
                    from_chat_id=STORAGE_CHANNEL_ID,
                    message_id=file.storage_message_id
                )
                
                await query.answer("✅ فایل ارسال شد!")
                logger.info(f"File successfully forwarded: {file.file_name}")
                
            except Exception as e:
                logger.error(f"Error forwarding shared file: {e}")
                await query.answer("❌ خطا در ارسال فایل!")
                
        except Exception as e:
            logger.error(f"Error in download shared file: {e}")
            await self.handle_error_safe(update, context)
    # async def download_shared_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Handle downloading shared file"""
    #     try:
    #         query = update.callback_query
    #         await query.answer("در حال ارسال فایل...")
            
    #         parts = query.data.split('_')
    #         logger.info(f"Download shared file callback data: {query.data}, parts: {parts}")
            
    #         # Validate parts array
    #         if len(parts) < 5:
    #             await query.answer("❌ داده callback نامعتبر!")
    #             logger.error(f"Invalid callback data format: {query.data}")
    #             return
            
    #         try:
    #             file_id = int(parts[3])
    #             short_code = parts[4]
    #             logger.info(f"Parsed file_id: {file_id}, short_code: {short_code}")
    #         except ValueError as ve:
    #             logger.error(f"Error parsing callback data {query.data}: {ve}")
    #             await query.answer("❌ خطا در پردازش داده!")
    #             return
            
    #         logger.info(f"Getting file by id: {file_id}")
    #         file = await self.db.get_file_by_id(file_id)
    #         if not file:
    #             await query.answer("❌ فایل یافت نشد!")
    #             return
            
    #         logger.info(f"File found: {file.file_name}, storage_message_id: {file.storage_message_id}")
            
    #         # Forward file from storage channel
    #         try:
    #             logger.info(f"Forwarding message from channel {STORAGE_CHANNEL_ID}, message_id: {file.storage_message_id}")
    #             await context.bot.forward_message(
    #                 chat_id=update.effective_chat.id,
    #                 from_chat_id=STORAGE_CHANNEL_ID,
    #                 message_id=file.storage_message_id
    #             )
                
    #             await query.answer("✅ فایل ارسال شد!")
    #             logger.info(f"File successfully forwarded: {file.file_name}")
                
    #         except Exception as e:
    #             logger.error(f"Error forwarding shared file: {e}")
    #             await query.answer("❌ خطا در ارسال فایل!")
                
    #     except Exception as e:
    #         logger.error(f"Error in download shared file: {e}")
    #         await self.handle_error(update, context, e)
    async def download_all_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle downloading all files from shared category - FIXED"""
        try:
            query = update.callback_query
            await query.answer("در حال ارسال تمام فایل‌های دسته...")
            
            parts = query.data.split('_')
            logger.info(f"Download all category callback data: {query.data}, parts: {parts}")
            
            # Expected format: download_all_category_{short_code}
            # Parts: ['download', 'all', 'category', short_code]
            if len(parts) < 4:
                await query.answer("❌ داده callback نامعتبر!")
                logger.error(f"Invalid callback data format: {query.data}")
                return
                
            short_code = parts[3]
            link = await self.db.get_link_by_code(short_code)
            
            if not link or link.link_type != "category":
                await query.answer("❌ لینک نامعتبر!")
                return
            
            # Ensure target_id is integer for database query
            try:
                category_id = int(link.target_id) if isinstance(link.target_id, str) else link.target_id
            except (ValueError, TypeError):
                logger.error(f"Invalid target_id in link: {link.target_id}")
                await query.answer("❌ داده لینک نامعتبر!")
                return
            
            files = await self.db.get_files(category_id, limit=50)
            
            if not files:
                await query.answer("❌ هیچ فایلی برای دانلود وجود ندارد!")
                return
            
            # Send a message about starting download
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"📥 **شروع ارسال {len(files)} فایل...**\n\nلطفاً منتظر بمانید تا تمام فایل‌ها ارسال شوند.",
                parse_mode='Markdown'
            )
            
            from config.settings import STORAGE_CHANNEL_ID
            sent_count = 0
            failed_count = 0
            
            for file in files:
                try:
                    await context.bot.forward_message(
                        chat_id=update.effective_chat.id,
                        from_chat_id=STORAGE_CHANNEL_ID,
                        message_id=file.storage_message_id
                    )
                    sent_count += 1
                    # Small delay to avoid hitting rate limits
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error forwarding file {file.file_name}: {e}")
                    failed_count += 1
            
            # Send completion message
            completion_text = f"✅ **ارسال کامل شد!**\n\n"
            completion_text += f"📤 ارسال شده: {sent_count} فایل\n"
            if failed_count > 0:
                completion_text += f"❌ خطا در ارسال: {failed_count} فایل\n"
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=completion_text,
                parse_mode='Markdown'
            )
                
        except Exception as e:
            logger.error(f"Error in download all category: {e}")
            await self.handle_error_safe(query, context)
    # async def download_all_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Handle downloading all files from shared category"""
    #     try:
    #         query = update.callback_query
    #         await query.answer("در حال ارسال تمام فایل‌های دسته...")
            
    #         parts = query.data.split('_')
    #         logger.info(f"Download all category callback data: {query.data}, parts: {parts}")
            
    #         # Expected format: download_all_category_{short_code}
    #         # Parts: ['download', 'all', 'category', short_code]
    #         if len(parts) < 4:
    #             await query.answer("❌ داده callback نامعتبر!")
    #             logger.error(f"Invalid callback data format: {query.data}")
    #             return
                
    #         short_code = parts[3]
    #         link = await self.db.get_link_by_code(short_code)
            
    #         if not link or link.link_type != "category":
    #             await query.answer("❌ لینک نامعتبر!")
    #             return
            
    #         # Ensure target_id is integer for database query
    #         try:
    #             category_id = int(link.target_id) if isinstance(link.target_id, str) else link.target_id
    #         except (ValueError, TypeError):
    #             logger.error(f"Invalid target_id in link: {link.target_id}")
    #             await query.answer("❌ داده لینک نامعتبر!")
    #             return
            
    #         files = await self.db.get_files(category_id, limit=50)
            
    #         if not files:
    #             await query.answer("❌ هیچ فایلی برای دانلود وجود ندارد!")
    #             return
            
    #         # Send a message about starting download
    #         await context.bot.send_message(
    #             chat_id=update.effective_chat.id,
    #             text=f"📥 **شروع ارسال {len(files)} فایل...**\n\nلطفاً منتظر بمانید تا تمام فایل‌ها ارسال شوند.",
    #             parse_mode='Markdown'
    #         )
            
    #         sent_count = 0
    #         failed_count = 0
            
    #         for file in files:
    #             try:
    #                 await context.bot.forward_message(
    #                     chat_id=update.effective_chat.id,
    #                     from_chat_id=STORAGE_CHANNEL_ID,
    #                     message_id=file.storage_message_id
    #                 )
    #                 sent_count += 1
    #                 # Small delay to avoid hitting rate limits
    #                 await asyncio.sleep(0.5)
                    
    #             except Exception as e:
    #                 logger.error(f"Error forwarding file {file.file_name}: {e}")
    #                 failed_count += 1
            
    #         # Send completion message
    #         completion_text = f"✅ **ارسال کامل شد!**\n\n"
    #         completion_text += f"📤 ارسال شده: {sent_count} فایل\n"
    #         if failed_count > 0:
    #             completion_text += f"❌ خطا در ارسال: {failed_count} فایل\n"
            
    #         await context.bot.send_message(
    #             chat_id=update.effective_chat.id,
    #             text=completion_text,
    #             parse_mode='Markdown'
    #         )
                
    #     except Exception as e:
    #         logger.error(f"Error in download all category: {e}")
    #         await self.handle_error(update, context, e)
    async def download_all_collection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle downloading all files from shared collection - FIXED"""
        try:
            query = update.callback_query
            await query.answer("در حال ارسال تمام فایل‌های مجموعه...")
            
            parts = query.data.split('_')
            logger.info(f"Download all collection callback data: {query.data}, parts: {parts}")
            
            # Expected format: download_all_collection_{short_code}
            # Parts: ['download', 'all', 'collection', short_code]
            if len(parts) < 4:
                await query.answer("❌ داده callback نامعتبر!")
                logger.error(f"Invalid callback data format: {query.data}")
                return
                
            short_code = parts[3]
            link = await self.db.get_link_by_code(short_code)
            
            if not link or link.link_type != "collection":
                await query.answer("❌ لینک نامعتبر!")
                return
            
            import json
            file_ids = json.loads(link.target_ids)
            
            files = []
            for file_id in file_ids:
                file = await self.db.get_file_by_id(file_id)
                if file:
                    files.append(file)
            
            if not files:
                await query.answer("❌ هیچ فایلی برای دانلود وجود ندارد!")
                return
            
            # Send a message about starting download
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"📥 **شروع ارسال {len(files)} فایل...**\n\nلطفاً منتظر بمانید تا تمام فایل‌ها ارسال شوند.",
                parse_mode='Markdown'
            )
            
            from config.settings import STORAGE_CHANNEL_ID
            sent_count = 0
            failed_count = 0
            
            for file in files:
                try:
                    await context.bot.forward_message(
                        chat_id=update.effective_chat.id,
                        from_chat_id=STORAGE_CHANNEL_ID,
                        message_id=file.storage_message_id
                    )
                    sent_count += 1
                    # Small delay to avoid hitting rate limits
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error forwarding file {file.file_name}: {e}")
                    failed_count += 1
            
            # Send completion message
            completion_text = f"✅ **ارسال کامل شد!**\n\n"
            completion_text += f"📤 ارسال شده: {sent_count} فایل\n"
            if failed_count > 0:
                completion_text += f"❌ خطا در ارسال: {failed_count} فایل\n"
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=completion_text,
                parse_mode='Markdown'
            )
                
        except Exception as e:
            logger.error(f"Error in download all collection: {e}")
            # await query.answer("❌ خطا در دانلود گروهی!")
            await self.handle_error_safe(query, context)
    # async def download_all_collection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Handle downloading all files from shared collection"""
    #     try:
    #         query = update.callback_query
    #         await query.answer("در حال ارسال تمام فایل‌های مجموعه...")
            
    #         parts = query.data.split('_')
    #         logger.info(f"Download all collection callback data: {query.data}, parts: {parts}")
            
    #         # Expected format: download_all_collection_{short_code}
    #         # Parts: ['download', 'all', 'collection', short_code]
    #         if len(parts) < 4:
    #             await query.answer("❌ داده callback نامعتبر!")
    #             logger.error(f"Invalid callback data format: {query.data}")
    #             return
                
    #         short_code = parts[3]
    #         link = await self.db.get_link_by_code(short_code)
            
    #         if not link or link.link_type != "collection":
    #             await query.answer("❌ لینک نامعتبر!")
    #             return
            
    #         file_ids = json.loads(link.target_ids)
            
    #         files = []
    #         for file_id in file_ids:
    #             file = await self.db.get_file_by_id(file_id)
    #             if file:
    #                 files.append(file)
            
    #         if not files:
    #             await query.answer("❌ هیچ فایلی برای دانلود وجود ندارد!")
    #             return
            
    #         # Send a message about starting download
    #         await context.bot.send_message(
    #             chat_id=update.effective_chat.id,
    #             text=f"📥 **شروع ارسال {len(files)} فایل...**\n\nلطفاً منتظر بمانید تا تمام فایل‌ها ارسال شوند.",
    #             parse_mode='Markdown'
    #         )
            
    #         sent_count = 0
    #         failed_count = 0
            
    #         for file in files:
    #             try:
    #                 await context.bot.forward_message(
    #                     chat_id=update.effective_chat.id,
    #                     from_chat_id=STORAGE_CHANNEL_ID,
    #                     message_id=file.storage_message_id
    #                 )
    #                 sent_count += 1
    #                 # Small delay to avoid hitting rate limits
    #                 await asyncio.sleep(0.5)
                    
    #             except Exception as e:
    #                 logger.error(f"Error forwarding file {file.file_name}: {e}")
    #                 failed_count += 1
            
    #         # Send completion message
    #         completion_text = f"✅ **ارسال کامل شد!**\n\n"
    #         completion_text += f"📤 ارسال شده: {sent_count} فایل\n"
    #         if failed_count > 0:
    #             completion_text += f"❌ خطا در ارسال: {failed_count} فایل\n"
            
    #         await context.bot.send_message(
    #             chat_id=update.effective_chat.id,
    #             text=completion_text,
    #             parse_mode='Markdown'
    #         )
                
    #     except Exception as e:
    #         logger.error(f"Error in download all collection: {e}")
    #         await self.handle_error(update, context, e)
    async def back_to_shared(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle back to shared link main view - FIXED"""
        try:
            query = update.callback_query
            await query.answer()
            
            parts = query.data.split('_')
            logger.info(f"Back to shared callback data: {query.data}, parts: {parts}")
            
            if len(parts) < 4:
                await query.answer("❌ داده callback نامعتبر!")
                logger.error(f"Invalid callback data format: {query.data}")
                return
                
            short_code = parts[3]
            
            # Re-handle the original share link by recreating the display
            link = await self.db.get_link_by_code(short_code)
            if not link:
                await query.edit_message_text("❌ لینک یافت نشد!")
                return
                
            # Recreate the share link display based on type
            if link.link_type == "category":
                await self._handle_category_share_link_edit(update, context, link)
            elif link.link_type == "collection":
                await self._handle_collection_share_link_edit(update, context, link)
            else:
                await query.edit_message_text("❌ نوع لینک پشتیبانی نمی‌شود!")
            
        except Exception as e:
            logger.error(f"Error in back to shared: {e}")
            await query.answer("❌ خطا در بازگشت!")
    # async def back_to_shared(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Handle back to shared link main view"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         parts = query.data.split('_')
    #         logger.info(f"Back to shared callback data: {query.data}, parts: {parts}")
            
    #         if len(parts) < 4:
    #             await query.answer("❌ داده callback نامعتبر!")
    #             logger.error(f"Invalid callback data format: {query.data}")
    #             return
                
    #         short_code = parts[3]
            
    #         # Re-handle the original share link by recreating the display
    #         link = await self.db.get_link_by_code(short_code)
    #         if not link:
    #             await query.edit_message_text("❌ لینک یافت نشد!")
    #             return
                
    #         # Recreate the share link display based on type
    #         if link.link_type == "category":
    #             await self.category_share_link_edit(update, context, link)
    #         elif link.link_type == "collection":
    #             await self.collection_share_link_edit(update, context, link)
    #         else:
    #             await query.edit_message_text("❌ نوع لینک پشتیبانی نمی‌شود!")
            
    #     except Exception as e:
    #         logger.error(f"Error in back to shared: {e}")
    #         await query.answer("❌ خطا در بازگشت!")
    
    async def category_share_link_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, link):
        """Handle shared category link for edit message"""
        try:
            category = await self.db.get_category_by_id(link.target_id)
            if not category:
                await update.callback_query.edit_message_text("❌ دسته یافت نشد!")
                return
            
            files = await self.db.get_files(link.target_id, limit=1000)
            
            total_size = sum(f.file_size for f in files)
            
            text = f"📂 **دسته اشتراک‌گذاری شده**\n\n"
            text += f"📁 **نام دسته:** {category.name}\n"
            text += f"📊 **تعداد فایل:** {len(files)}\n"
            text += f"💾 **حجم کل:** {format_file_size(total_size)}\n"
            text += f"📈 **بازدید:** {link.access_count} بار\n\n"
            
            if category.description:
                text += f"📝 **توضیحات:** {category.description}\n\n"
            
            text += f"💡 می‌توانید فایل‌ها را مشاهده و دانلود کنید."
            
            keyboard = KeyboardBuilder.build_shared_category_keyboard(category, link)
            
            await update.callback_query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in category share link edit: {e}")
            await update.callback_query.edit_message_text("❌ خطا در نمایش دسته!")
    
    async def collection_share_link_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, link):
        """Handle shared collection link for edit message"""
        try:
            file_ids = json.loads(link.target_ids)
            
            files = []
            total_size = 0
            for file_id in file_ids:
                file = await self.db.get_file_by_id(file_id)
                if file:
                    files.append(file)
                    total_size += file.file_size
            
            if not files:
                await update.callback_query.edit_message_text("❌ فایل‌های مجموعه یافت نشد!")
                return
            
            text = f"📦 **مجموعه فایل‌های اشتراک‌گذاری شده**\n\n"
            text += f"📊 **تعداد فایل:** {len(files)}\n"
            text += f"💾 **حجم کل:** {format_file_size(total_size)}\n"
            text += f"📈 **بازدید:** {link.access_count} بار\n\n"
            text += f"📋 **فایل‌ها:**\n"
            
            for i, file in enumerate(files[:5], 1):
                # Escape filename for Markdown
                safe_filename = escape_filename_for_markdown(file.file_name)
                text += f"{i}. {safe_filename} ({format_file_size(file.file_size)})\n"
            
            if len(files) > 5:
                text += f"... و {len(files) - 5} فایل دیگر"
            
            keyboard = KeyboardBuilder.build_shared_collection_keyboard(link)
            
            await update.callback_query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in collection share link edit: {e}")
            await update.callback_query.edit_message_text("❌ خطا در نمایش مجموعه!")
    # async def _handle_legacy_file_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_id: str):
    #     """Handle legacy file links"""
    #     try:
    #         file = await self.db.get_file_by_id(int(file_id))
    #         if not file:
    #             await update.message.reply_text("❌ فایل یافت نشد!")
    #             return
                
    #         category = await self.db.get_category_by_id(file.category_id)
    #         category_name = category.name if category else "نامشخص"
            
    #         from utils.helpers import build_file_info_text
            
    #         text = f"📄 **فایل**\n\n"
    #         text += f"📁 دسته: {category_name}\n\n"
    #         text += build_file_info_text(file.to_dict(), category_name)
            
    #         keyboard = KeyboardBuilder.build_file_actions_keyboard(file)
            
    #         await update.message.reply_text(
    #             text,
    #             reply_markup=keyboard,
    #             parse_mode='Markdown'
    #         )
            
    #     except Exception as e:
    #         logger.error(f"Error handling legacy file link: {e}")
    #         await update.message.reply_text("❌ خطا در پردازش لینک!")
    
    async def legacy_file_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_id: str):
        """Handle legacy file link support"""
        try:
            # Convert to int and get file
            try:
                file_id_int = int(file_id)
                file = await self.db.get_file_by_id(file_id_int)
                
                if not file:
                    await update.message.reply_text("❌ فایل یافت نشد!")
                    return
                
                # Get category info
                category = await self.db.get_category_by_id(file.category_id)
                category_name = category.name if category else "نامشخص"
                
                from utils.helpers import build_file_info_text
                
                text = f"📄 **فایل (لینک قدیمی)**\n\n"
                text += f"📁 دسته: {category_name}\n\n"
                text += build_file_info_text(file.to_dict(), category_name)
                
                # Create simple download keyboard
                keyboard = KeyboardBuilder.build_file_actions_keyboard(file)
                
                await update.message.reply_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                
            except ValueError:
                await update.message.reply_text("❌ لینک فایل نامعتبر!")
                
        except Exception as e:
            logger.error(f"Error in legacy file link: {e}")
            await update.message.reply_text("❌ خطا در پردازش لینک فایل!")
    
    # async def shared_file_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Handle shared file download"""
    #     # This is the same as download_shared_file - keeping for compatibility
    #     await self.download_shared_file(update, context)
    
    # async def shared_file_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Handle shared file details view"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         parts = query.data.split('_')
    #         if len(parts) < 3:
    #             await query.answer("❌ داده callback نامعتبر!")
    #             return
            
    #         file_id = int(parts[2])
    #         file = await self.db.get_file_by_id(file_id)
            
    #         if not file:
    #             await query.edit_message_text("❌ فایل یافت نشد!")
    #             return
            
    #         category = await self.db.get_category_by_id(file.category_id)
    #         category_name = category.name if category else "نامشخص"
            
    #         from utils.helpers import build_file_info_text
            
    #         text = f"📄 **جزئیات فایل اشتراک‌گذاری شده**\n\n"
    #         text += build_file_info_text(file.to_dict(), category_name)
            
    #         keyboard = KeyboardBuilder.build_shared_file_keyboard(file, None)
            
    #         await query.edit_message_text(
    #             text,
    #             reply_markup=keyboard,
    #             parse_mode='Markdown'
    #         )
            
    #     except Exception as e:
    #         logger.error(f"Error in shared file details: {e}")
    #         await self.handle_error(update, context, e)
    
    async def shared_link_copy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle copying shared link"""
        try:
            query = update.callback_query
            await query.answer("در حال کپی لینک...")
            
            parts = query.data.split('_')
            if len(parts) < 3:
                await query.answer("❌ داده callback نامعتبر!")
                return
            
            short_code = parts[2]
            
            # Get bot username for proper URL
            bot_info = await context.bot.get_me()
            share_url = f"https://t.me/{bot_info.username}?start=link_{short_code}"
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"📋 **لینک کپی شده:**\n`{share_url}`\n\n🔗 **کد کوتاه:**\n`{short_code}`",
                parse_mode='Markdown',
                reply_to_message_id=query.message.message_id
            )
            
            await query.answer("✅ لینک کپی شد!")
            
        except Exception as e:
            logger.error(f"Error copying shared link: {e}")
            await query.answer("❌ خطا در کپی لینک!")
    
    async def shared_link_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle shared link statistics"""
        try:
            query = update.callback_query
            await query.answer()
            
            parts = query.data.split('_')
            if len(parts) < 3:
                await query.answer("❌ داده callback نامعتبر!")
                return
            
            short_code = parts[2]
            link = await self.db.get_link_by_code(short_code)
            
            if not link:
                await query.edit_message_text("❌ لینک یافت نشد!")
                return
            
            text = f"📊 **آمار لینک اشتراک‌گذاری**\n\n"
            text += f"🔗 **کد کوتاه:** `{short_code}`\n"
            text += f"📈 **تعداد بازدید:** {link.access_count}\n"
            text += f"🏷 **نوع:** {link.link_type}\n"
            
            if link.title:
                text += f"📝 **عنوان:** {link.title}\n"
            
            if link.created_at:
                text += f"📅 **ایجاد شده:** {link.created_at}\n"
            
            keyboard = KeyboardBuilder.build_shared_link_stats_keyboard(short_code)
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in shared link stats: {e}")
            await self.handle_error(update, context, e)
    
    async def back_shared(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle back from shared content"""
        # This is the same as back_to_shared - keeping for compatibility
        await self.back_to_shared(update, context)
    async def shared_file_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle shared file download"""
        try:
            await self.download_shared_file(update, context)
        except Exception as e:
            logger.error(f"Error in shared file download: {e}")
            await update.callback_query.answer("❌ خطا در دانلود فایل!")
    
    async def shared_file_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle shared file details"""
        try:
            query = update.callback_query
            await query.answer()
            
            file_id = int(query.data.split('_')[2])
            
            file = await self.db.get_file_by_id(file_id)
            if not file:
                await query.edit_message_text("❌ فایل یافت نشد!")
                return
            
            category = await self.db.get_category_by_id(file.category_id)
            category_name = category.name if category else "نامشخص"
            
            from utils.helpers import build_file_info_text
            text = "📄 **جزئیات فایل اشتراک‌گذاری شده**\n\n"
            text += build_file_info_text(file.to_dict(), category_name)
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("📥 دانلود", callback_data=f"download_shared_{file_id}"),
                InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")
            ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in shared file details: {e}")
            await query.answer("❌ خطا در نمایش جزئیات!")
    
    # async def shared_link_copy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Handle copying shared link"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         short_code = query.data.split('_')[2]
            
    #         # Get bot username for proper URL
    #         bot_info = await context.bot.get_me()
    #         share_url = f"https://t.me/{bot_info.username}?start=link_{short_code}"
            
    #         await context.bot.send_message(
    #             chat_id=update.effective_chat.id,
    #             text=f"🔗 **کپی لینک:**\n`{share_url}`",
    #             parse_mode='Markdown',
    #             reply_to_message_id=query.message.message_id
    #         )
            
    #     except Exception as e:
    #         logger.error(f"Error copying shared link: {e}")
    #         await query.answer("❌ خطا در کپی لینک!")
    
    # async def shared_link_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Handle shared link statistics"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         short_code = query.data.split('_')[2]
            
    #         from utils.link_manager import LinkManager
    #         link_manager = LinkManager(self.db)
            
    #         stats = await link_manager.get_link_stats(short_code)
    #         if not stats:
    #             await query.answer("❌ آمار لینک یافت نشد!")
    #             return
            
    #         text = f"📈 **آمار لینک اشتراک‌گذاری**\n\n"
    #         text += f"🔗 **کد:** `{stats['short_code']}`\n"
    #         text += f"📊 **بازدید:** {stats['access_count']} بار\n"
    #         text += f"📅 **تاریخ ایجاد:** {stats['created_at'][:16] if stats['created_at'] else 'نامشخص'}\n"
    #         text += f"🏷 **عنوان:** {stats['title']}\n"
            
    #         keyboard = InlineKeyboardMarkup([[
    #             InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")
    #         ]])
            
    #         await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
    #     except Exception as e:
    #         logger.error(f"Error in shared link stats: {e}")
    #         await query.answer("❌ خطا در نمایش آمار!")
    