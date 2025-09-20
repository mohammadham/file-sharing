#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Category Link Handler - Handles category link operations
"""

import json
import logging
from telegram import Update
from telegram.ext import ContextTypes

from handlers.base_handler import BaseHandler
from utils.keyboard_builder import KeyboardBuilder
from utils.helpers import safe_json_loads, safe_json_dumps, format_file_size
from utils.link_manager import LinkManager

logger = logging.getLogger(__name__)


class CategoryLinkHandler(BaseHandler):
    """Handle category link operations"""
    
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.link_manager = LinkManager(db_manager)
    
    async def show_category_link_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show category link options menu"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            parts = query.data.split('_')
            logger.info(f"Category link options callback: {query.data}, parts: {parts}")
            
            # Validate callback data format
            if len(parts) < 3:
                await query.answer("❌ داده callback نامعتبر!")
                return
                
            try:
                category_id = int(parts[2])
            except ValueError:
                logger.error(f"Invalid category_id in callback: {query.data}")
                await query.answer("❌ خطا در پردازش داده!")
                return
            
            category = await self.db.get_category_by_id(category_id)
            if not category:
                await query.edit_message_text("دسته‌بندی یافت نشد!")
                return
            
            # Count files in category
            files = await self.db.get_files(category_id, limit=1000)
            files_count = len(files)
            
            if files_count == 0:
                text = f"📂 **دسته '{category.name}'**\n\n"
                text += "❌ این دسته هیچ فایلی ندارد.\n"
                text += "ابتدا فایل‌هایی را در این دسته قرار دهید."
                
                keyboard = KeyboardBuilder.build_cancel_keyboard(f"cat_{category_id}")
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
                return
            
            # Calculate total size
            total_size = sum(f.file_size for f in files)
            total_size_formatted = format_file_size(total_size)
            
            text = f"🔗 **ایجاد لینک برای دسته '{category.name}'**\n\n"
            text += f"📊 **آمار دسته:**\n"
            text += f"• تعداد فایل: {files_count}\n"
            text += f"• حجم کل: {total_size_formatted}\n\n"
            text += f"💡 **گزینه‌های اشتراک‌گذاری:**"
            
            keyboard = KeyboardBuilder.build_category_link_options_keyboard(category_id)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def create_category_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create link for entire category"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update, "در حال ایجاد لینک دسته...")
            
            parts = query.data.split('_')
            logger.info(f"Create category link callback: {query.data}, parts: {parts}")
            
            if len(parts) < 4:
                await query.answer("❌ داده callback نامعتبر!")
                return
                
            try:
                category_id = int(parts[3])
            except ValueError:
                logger.error(f"Invalid category_id in callback: {query.data}")
                await query.answer("❌ خطا در پردازش داده!")
                return
                
            user_id = update.effective_user.id
            
            # Create category link
            short_code, share_url = await self.link_manager.create_category_link(
                category_id=category_id,
                user_id=user_id
            )
            
            # Get bot username for proper URL
            bot_info = await context.bot.get_me()
            share_url = f"https://t.me/{bot_info.username}?start=link_{short_code}"
            
            category = await self.db.get_category_by_id(category_id)
            files = await self.db.get_files(category_id, limit=1000)
            
            text = f"✅ **لینک دسته ایجاد شد**\n\n"
            text += f"📂 **دسته:** {category.name}\n"
            text += f"📊 **فایل‌ها:** {len(files)} فایل\n"
            text += f"🔗 **کد کوتاه:** `{short_code}`\n\n"
            text += f"🌐 **لینک کامل:**\n`{share_url}`\n\n"
            text += f"💡 کاربران با استفاده از این لینک می‌توانند:\n"
            text += f"• تمام فایل‌های دسته را مشاهده کنند\n"
            text += f"• فایل‌ها را دانلود کنند\n"
            text += f"• فایل‌های مورد نظر را انتخاب کنند"
            
            keyboard = KeyboardBuilder.build_cancel_keyboard(f"category_link_{category_id}")
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
            # Send copyable link
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"📋 **کپی لینک دسته:**\n`{share_url}`",
                parse_mode='Markdown',
                reply_to_message_id=query.message.message_id
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def show_files_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show files for selection - FIXED"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            parts = query.data.split('_')
            logger.info(f"Show files selection callback: {query.data}, parts: {parts}")
            
            if len(parts) < 3:
                await query.answer("❌ داده callback نامعتبر!")
                return
                
            try:
                category_id = int(parts[2])
            except ValueError:
                logger.error(f"Invalid category_id in callback: {query.data}")
                await query.answer("❌ خطا در پردازش داده!")
                return
                
            user_id = update.effective_user.id
            
            # Get or initialize selection with proper session management
            session = await self.get_user_session(user_id)
            temp_data = safe_json_loads(session.temp_data)
            
            # Initialize selection data if not exists or reset if category changed
            if 'selected_files' not in temp_data or temp_data.get('current_selection_category') != category_id:
                temp_data['selected_files'] = []
                temp_data['current_selection_category'] = category_id
                # Save updated session immediately
                await self.update_user_session(user_id, temp_data=safe_json_dumps(temp_data))
            
            selected_ids = temp_data.get('selected_files', [])
            
            category = await self.db.get_category_by_id(category_id)
            files = await self.db.get_files(category_id, limit=50)  # Limit for performance
            
            if not files:
                text = f"📂 **دسته '{category.name}'**\n\n"
                text += "❌ این دسته هیچ فایلی ندارد."
                
                keyboard = KeyboardBuilder.build_cancel_keyboard(f"category_link_{category_id}")
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
                return
            
            text = f"📋 **انتخاب فایل‌ها از دسته '{category.name}'**\n\n"
            text += f"📊 کل فایل‌ها: {len(files)}\n"
            text += f"✅ انتخاب شده: {len(selected_ids)}\n\n"
            text += f"💡 روی فایل‌های مورد نظر کلیک کنید:"
            
            keyboard = KeyboardBuilder.build_files_selection_keyboard(files, category_id, selected_ids)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def toggle_file_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle file selection - FIXED"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            parts = query.data.split('_')
            logger.info(f"Toggle file selection callback: {query.data}, parts: {parts}")
            
            if len(parts) < 4:
                await query.answer("❌ داده callback نامعتبر!")
                return
                
            try:
                file_id = int(parts[2])
                category_id = int(parts[3])
            except ValueError:
                logger.error(f"Invalid ids in callback: {query.data}")
                await query.answer("❌ خطا در پردازش داده!")
                return
                
            user_id = update.effective_user.id
            
            # Get current selection with proper validation
            session = await self.get_user_session(user_id)
            temp_data = safe_json_loads(session.temp_data)
            
            # Ensure we have proper selection data for this category
            if 'selected_files' not in temp_data or temp_data.get('current_selection_category') != category_id:
                temp_data['selected_files'] = []
                temp_data['current_selection_category'] = category_id
            
            selected_ids = temp_data.get('selected_files', [])
            
            # Toggle selection
            if file_id in selected_ids:
                selected_ids.remove(file_id)
                action_text = "حذف شد"
            else:
                selected_ids.append(file_id)
                action_text = "اضافه شد"
            
            # Update session with new selection
            temp_data['selected_files'] = selected_ids
            temp_data['current_selection_category'] = category_id
            await self.update_user_session(user_id, temp_data=safe_json_dumps(temp_data))
            
            # Get file name for feedback
            file = await self.db.get_file_by_id(file_id)
            file_name = file.file_name[:30] + "..." if file and len(file.file_name) > 30 else (file.file_name if file else "فایل نامشخص")
            
            # Show brief feedback
            await query.answer(f"✅ {file_name} {action_text}")
            
            # Refresh the keyboard immediately to show updated state
            await self._refresh_file_selection_display(update, context, category_id, user_id)
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def _refresh_file_selection_display(self, update: Update, context: ContextTypes.DEFAULT_TYPE, category_id: int, user_id: int):
        """Refresh file selection display - NEW HELPER METHOD"""
        try:
            # Get updated session data
            session = await self.get_user_session(user_id)
            temp_data = safe_json_loads(session.temp_data)
            selected_ids = temp_data.get('selected_files', [])
            
            category = await self.db.get_category_by_id(category_id)
            files = await self.db.get_files(category_id, limit=50)
            
            text = f"📋 **انتخاب فایل‌ها از دسته '{category.name}'**\n\n"
            text += f"📊 کل فایل‌ها: {len(files)}\n"
            text += f"✅ انتخاب شده: {len(selected_ids)}\n\n"
            text += f"💡 روی فایل‌های مورد نظر کلیک کنید:"
            
            keyboard = KeyboardBuilder.build_files_selection_keyboard(files, category_id, selected_ids)
            
            await update.callback_query.edit_message_text(
                text, 
                reply_markup=keyboard, 
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error refreshing file selection display: {e}")
    
    async def select_all_files(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Select all files in category - FIXED"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update, "در حال انتخاب همه فایل‌ها...")
            
            parts = query.data.split('_')
            logger.info(f"Select all files callback: {query.data}, parts: {parts}")
            
            if len(parts) < 3:
                await query.answer("❌ داده callback نامعتبر!")
                return
                
            try:
                category_id = int(parts[2])
            except ValueError:
                logger.error(f"Invalid category_id in callback: {query.data}")
                await query.answer("❌ خطا در پردازش داده!")
                return
                
            user_id = update.effective_user.id
            
            # Get all files
            files = await self.db.get_files(category_id, limit=50)
            all_file_ids = [f.id for f in files]
            
            # Update session with proper category tracking
            temp_data = {
                'selected_files': all_file_ids,
                'current_selection_category': category_id
            }
            await self.update_user_session(user_id, temp_data=safe_json_dumps(temp_data))
            
            # Refresh the display
            await self._refresh_file_selection_display(update, context, category_id, user_id)
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def clear_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clear file selection - FIXED"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update, "انتخاب پاک شد")
            
            parts = query.data.split('_')
            logger.info(f"Clear selection callback: {query.data}, parts: {parts}")
            
            if len(parts) < 3:
                await query.answer("❌ داده callback نامعتبر!")
                return
                
            try:
                category_id = int(parts[2])
            except ValueError:
                logger.error(f"Invalid category_id in callback: {query.data}")
                await query.answer("❌ خطا در پردازش داده!")
                return
                
            user_id = update.effective_user.id
            
            # Clear selection while maintaining category context
            temp_data = {
                'selected_files': [],
                'current_selection_category': category_id
            }
            await self.update_user_session(user_id, temp_data=safe_json_dumps(temp_data))
            
            # Refresh the display
            await self._refresh_file_selection_display(update, context, category_id, user_id)
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def create_collection_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create link for selected files"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update, "در حال ایجاد لینک مجموعه...")
            
            parts = query.data.split('_')
            logger.info(f"Create collection link callback: {query.data}, parts: {parts}")
            
            if len(parts) < 4:
                await query.answer("❌ داده callback نامعتبر!")
                return
                
            try:
                category_id = int(parts[3])
            except ValueError:
                logger.error(f"Invalid category_id in callback: {query.data}")
                await query.answer("❌ خطا در پردازش داده!")
                return
                
            user_id = update.effective_user.id
            
            # Get selected files
            session = await self.get_user_session(user_id)
            temp_data = safe_json_loads(session.temp_data)
            selected_ids = temp_data.get('selected_files', [])
            
            if not selected_ids:
                await query.answer("❌ هیچ فایلی انتخاب نشده!")
                return
            
            # Create collection link
            short_code, share_url = await self.link_manager.create_collection_link(
                file_ids=selected_ids,
                user_id=user_id
            )
            
            # Get bot username for proper URL
            bot_info = await context.bot.get_me()
            share_url = f"https://t.me/{bot_info.username}?start=link_{short_code}"
            
            # Get files info for display
            files_info = []
            total_size = 0
            for file_id in selected_ids:
                file = await self.db.get_file_by_id(file_id)
                if file:
                    files_info.append((file.file_name, file.file_size))
                    total_size += file.file_size
            
            text = f"✅ **لینک مجموعه ایجاد شد**\n\n"
            text += f"📦 **فایل‌های انتخاب شده:** {len(files_info)}\n"
            text += f"💾 **حجم کل:** {format_file_size(total_size)}\n"
            text += f"🔗 **کد کوتاه:** `{short_code}`\n\n"
            text += f"🌐 **لینک کامل:**\n`{share_url}`\n\n"
            text += f"📋 **فایل‌های شامل:**\n"
            
            for i, (name, size) in enumerate(files_info[:5], 1):
                text += f"{i}. {name} ({format_file_size(size)})\n"
            
            if len(files_info) > 5:
                text += f"... و {len(files_info) - 5} فایل دیگر"
            
            # Clear selection after successful link creation
            await self.update_user_session(user_id, temp_data=safe_json_dumps({}))
            
            keyboard = KeyboardBuilder.build_cancel_keyboard(f"category_link_{category_id}")
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
            # Send copyable link
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"📋 **کپی لینک مجموعه:**\n`{share_url}`",
                parse_mode='Markdown',
                reply_to_message_id=query.message.message_id
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def show_category_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show category statistics - FIXED"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            parts = query.data.split('_')
            logger.info(f"Show category stats callback: {query.data}, parts: {parts}")
            
            # Handle both normal category stats and shared link stats
            if len(parts) >= 3:
                try:
                    category_id = int(parts[2])
                except ValueError:
                    # This might be a shared link callback - skip it
                    logger.info(f"Non-numeric category_id in stats callback, might be shared link: {query.data}")
                    await query.answer("❌ خطا در پردازش داده!")
                    return
            else:
                await query.answer("❌ داده callback نامعتبر!")
                return
            
            category = await self.db.get_category_by_id(category_id)
            if not category:
                await query.edit_message_text("دسته‌بندی یافت نشد!")
                return
            
            files = await self.db.get_files(category_id, limit=1000)
            
            # Calculate stats
            total_files = len(files)
            total_size = sum(f.file_size for f in files)
            
            file_types = {}
            for file in files:
                file_type = file.file_type.split('/')[0] if '/' in file.file_type else file.file_type
                file_types[file_type] = file_types.get(file_type, 0) + 1
            
            text = f"📊 **آمار دسته '{category.name}'**\n\n"
            text += f"📁 **تعداد فایل:** {total_files}\n"
            text += f"💾 **حجم کل:** {format_file_size(total_size)}\n"
            text += f"📅 **تاریخ ایجاد:** {category.created_at[:16] if category.created_at else 'نامشخص'}\n\n"
            
            if category.description:
                text += f"📝 **توضیحات:** {category.description}\n\n"
            
            if file_types:
                text += f"🏷 **انواع فایل:**\n"
                for file_type, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
                    text += f"• {file_type}: {count} فایل\n"
            
            keyboard = KeyboardBuilder.build_cancel_keyboard(f"category_link_{category_id}")
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)