#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File Handler - Handles file-related operations
"""

import logging
import math
from telegram import Update
from telegram.ext import ContextTypes

from handlers.base_handler import BaseHandler
from utils.keyboard_builder import KeyboardBuilder
from utils.helpers import (
    extract_file_info, validate_file_size, safe_json_loads, 
    safe_json_dumps, build_file_info_text, format_file_size
)
from models.database_models import File
from config.settings import MAX_FILE_SIZE, MAX_FILES_PER_PAGE, STORAGE_CHANNEL_ID

logger = logging.getLogger(__name__)


class FileHandler(BaseHandler):
    """Handle file operations"""
    
    async def show_files(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show files in category with pagination"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            # Parse callback data
            parts = query.data.split('_')
            category_id = int(parts[1])
            page = int(parts[2]) if len(parts) > 2 else 0
            
            category = await self.db.get_category_by_id(category_id)
            if not category:
                await query.edit_message_text("دسته‌بندی یافت نشد!")
                return
            
            # Get files with pagination
            offset = page * MAX_FILES_PER_PAGE
            files = await self.db.get_files(category_id, MAX_FILES_PER_PAGE, offset)
            
            # Calculate total pages
            all_files = await self.db.get_files(category_id, limit=1000)
            total_files = len(all_files)
            total_pages = math.ceil(total_files / MAX_FILES_PER_PAGE) if total_files > 0 else 1
            
            text = f"📁 **فایل‌های {category.name}**\n\n"
            
            if files:
                for file in files:
                    text += f"📄 **{file.file_name}**\n"
                    text += f"   💾 {file.size_mb:.1f} MB | {file.file_type}\n"
                    text += f"   📅 {file.uploaded_at[:16] if file.uploaded_at else 'نامشخص'}\n\n"
                
                text += f"📊 صفحه {page + 1} از {total_pages} (کل {total_files} فایل)"
            else:
                text += self.messages['no_files_found']
            
            keyboard = KeyboardBuilder.build_files_keyboard(files, category_id, page, total_pages)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def show_file_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show individual file details and actions"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            file_id = int(query.data.split('_')[1])
            
            file = await self.db.get_file_by_id(file_id)
            if not file:
                await query.edit_message_text("فایل یافت نشد!")
                return
            
            category = await self.db.get_category_by_id(file.category_id)
            category_name = category.name if category else "نامشخص"
            
            text = "📄 **جزئیات فایل**\n\n"
            text += build_file_info_text(file.to_dict(), category_name)
            
            keyboard = KeyboardBuilder.build_file_actions_keyboard(file)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def download_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send file to user for download"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update, "در حال ارسال فایل...")
            
            file_id = int(query.data.split('_')[1])
            
            file = await self.db.get_file_by_id(file_id)
            if not file:
                await query.edit_message_text("فایل یافت نشد!")
                return
            
            # Forward file from storage channel
            try:
                await context.bot.forward_message(
                    chat_id=update.effective_chat.id,
                    from_chat_id=STORAGE_CHANNEL_ID,
                    message_id=file.storage_message_id
                )
                
                await query.answer("✅ فایل ارسال شد!")
                
            except Exception as e:
                logger.error(f"Error forwarding file: {e}")
                await query.answer("❌ خطا در ارسال فایل!")
                
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def edit_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start editing file information"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            file_id = int(query.data.split('_')[2])
            user_id = update.effective_user.id
            
            file = await self.db.get_file_by_id(file_id)
            if not file:
                await query.edit_message_text("فایل یافت نشد!")
                return
            
            await self.update_user_session(
                user_id,
                action_state='editing_file',
                temp_data=safe_json_dumps({'file_id': file_id, 'step': 'name'})
            )
            
            keyboard = KeyboardBuilder.build_cancel_keyboard(f"file_{file_id}")
            
            text = f"✏️ **ویرایش فایل '{file.file_name}'**\n\n"
            text += "نام جدید فایل را وارد کنید:"
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def delete_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show delete confirmation"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            file_id = int(query.data.split('_')[2])
            
            file = await self.db.get_file_by_id(file_id)
            if not file:
                await query.edit_message_text("فایل یافت نشد!")
                return
            
            text = f"🗑 **حذف فایل '{file.file_name}'**\n\n"
            text += f"💾 حجم: {file.size_mb:.1f} MB\n"
            text += f"📁 دسته: فایل از دسته فعلی حذف می‌شود\n\n"
            text += "⚠️ **توجه:** فایل از کانال ذخیره‌سازی حذف نمی‌شود.\n\n"
            text += "آیا مطمئن هستید؟"
            
            keyboard = KeyboardBuilder.build_confirmation_keyboard("delete_file", file_id)
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def confirm_delete_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm file deletion"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            file_id = int(query.data.split('_')[3])
            
            file = await self.db.get_file_by_id(file_id)
            if not file:
                await query.edit_message_text("فایل یافت نشد!")
                return
            
            category_id = file.category_id
            success = await self.db.delete_file(file_id)
            
            if success:
                # Show updated files list
                files = await self.db.get_files(category_id, MAX_FILES_PER_PAGE)
                keyboard = KeyboardBuilder.build_files_keyboard(files, category_id)
                
                await query.edit_message_text(
                    f"✅ فایل '{file.file_name}' با موفقیت حذف شد!",
                    reply_markup=keyboard
                )
            else:
                await query.edit_message_text("❌ خطا در حذف فایل!")
                
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def show_upload_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show upload file prompt"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            category_id = int(query.data.split('_')[1])
            user_id = update.effective_user.id
            
            category = await self.db.get_category_by_id(category_id)
            if not category:
                await query.edit_message_text("دسته‌بندی یافت نشد!")
                return
            
            # Set user state to current category and upload mode for file upload
            await self.update_user_session(
                user_id, 
                current_category=category_id,
                action_state='uploading_file'
            )
            
            # Escape special characters for Markdown
            from utils.helpers import escape_markdown
            safe_category_name = escape_markdown(category.name)
            
            text = f"📤 **آپلود فایل در دسته '{safe_category_name}'**\n\n"
            text += "فایل مورد نظر را ارسال کنید:\n\n"
            text += "💡 **راهنما:**\n"
            text += "• انواع پشتیبانی شده: سند، عکس، ویدیو، صوت\n"
            text += "• حداکثر حجم: 50 مگابایت\n"
            text += "• فایل به کانال ذخیره‌سازی فرستاده می‌شود\n\n"
            text += "🔙 برای بازگشت از دکمه زیر استفاده کنید:"
            
            keyboard = KeyboardBuilder.build_cancel_keyboard(f"cat_{category_id}")
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def move_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start moving file to another category"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            file_id = int(query.data.split('_')[2])
            user_id = update.effective_user.id
            
            file = await self.db.get_file_by_id(file_id)
            if not file:
                await query.edit_message_text("فایل یافت نشد!")
                return
            
            await self.update_user_session(
                user_id,
                action_state='moving_file',
                temp_data=safe_json_dumps({'file_id': file_id})
            )
            
            # Show root categories for selection
            categories = await self.db.get_categories(None)
            keyboard = await KeyboardBuilder.build_category_keyboard(categories, None, False)
            
            text = f"📁 **انتقال فایل '{file.file_name}'**\n\n"
            text += "دسته مقصد را انتخاب کنید:"
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def start_batch_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start batch upload process"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            category_id = int(query.data.split('_')[2])
            user_id = update.effective_user.id
            
            category = await self.db.get_category_by_id(category_id)
            if not category:
                await query.edit_message_text("دسته‌بندی یافت نشد!")
                return
            
            # Set user state to batch uploading
            await self.update_user_session(
                user_id,
                current_category=category_id,
                action_state='batch_uploading',
                temp_data=safe_json_dumps({'files': [], 'category_id': category_id})
            )
            
            # Escape special characters for Markdown
            from utils.helpers import escape_markdown
            safe_category_name = escape_markdown(category.name)
            
            text = f"📤🗂 **آپلود چندگانه فایل در دسته '{safe_category_name}'**\n\n"
            text += "🔄 **نحوه کار:**\n"
            text += "• فایل‌هایتان را یکی پس از دیگری ارسال کنید\n"
            text += "• هر فایل ارسالی ثبت خواهد شد\n"
            text += "• پس از ارسال همه فایل‌ها، \\'اتمام ارسال\\' را بزنید\n\n"
            text += "💡 **راهنما:**\n"
            text += "• انواع پشتیبانی شده: سند، عکس، ویدیو، صوت\n"
            text += "• حداکثر حجم هر فایل: 50 مگابایت\n"
            text += "• حداکثر 20 فایل در هر دسته\n\n"
            text += "🎯 **آماده دریافت فایل‌ها\\.\\.\\.**"
            
            keyboard = KeyboardBuilder.build_batch_upload_keyboard(category_id, 0)
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def handle_batch_file_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle individual file in batch upload"""
        try:
            user_id = update.effective_user.id
            session = await self.get_user_session(user_id)
            temp_data = safe_json_loads(session.temp_data)
            
            files_list = temp_data.get('files', [])
            category_id = temp_data.get('category_id', session.current_category)
            
            # Check file limit
            if len(files_list) >= 20:
                await update.message.reply_text(
                    "❌ حداکثر 20 فایل در هر دسته مجاز است!\n"
                    "لطفا 'اتمام ارسال' را بزنید تا فایل‌های موجود پردازش شوند."
                )
                return
            
            # Extract file information
            file_info = extract_file_info(update.message)
            if not file_info:
                await update.message.reply_text("❌ نوع فایل پشتیبانی نمی‌شود!")
                return
            
            file_obj, file_name, file_size, file_type = file_info
            
            # Validate file size
            if not validate_file_size(file_size, MAX_FILE_SIZE):
                await update.message.reply_text(self.messages['file_too_large'])
                return
            
            # Forward to storage channel
            forwarded = await context.bot.forward_message(
                chat_id=STORAGE_CHANNEL_ID,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            
            # Add to files list
            file_data = {
                'file_name': file_name,
                'file_type': file_type,
                'file_size': file_size,
                'telegram_file_id': file_obj.file_id,
                'storage_message_id': forwarded.message_id,
                'uploaded_by': user_id
            }
            
            files_list.append(file_data)
            
            # Update temp data
            temp_data['files'] = files_list
            await self.update_user_session(user_id, temp_data=safe_json_dumps(temp_data))
            
            # Send confirmation with updated keyboard
            keyboard = KeyboardBuilder.build_batch_upload_keyboard(category_id, len(files_list))
            size_mb = file_size / 1024 / 1024 if file_size else 0
            
            await update.message.reply_text(
                f"✅ فایل {len(files_list)} دریافت شد!\n"
                f"📄 <b>{file_name}</b>\n"
                f"💾 حجم: {size_mb:.1f} MB\n\n"
                f"📊 مجموع فایل‌های دریافت شده: {len(files_list)}\n"
                f"🔄 در انتظار فایل بعدی یا اتمام ارسال...",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error in batch file upload: {e}")
            await update.message.reply_text(self.messages['error_occurred'])
    
    async def finish_batch_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Finish batch upload and save all files"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update, "در حال پردازش فایل‌ها...")
            
            user_id = update.effective_user.id
            session = await self.get_user_session(user_id)
            temp_data = safe_json_loads(session.temp_data)
            
            files_list = temp_data.get('files', [])
            category_id = temp_data.get('category_id', session.current_category)
            
            if not files_list:
                await query.edit_message_text("❌ هیچ فایلی برای ذخیره یافت نشد!")
                return
            
            # Save all files to database
            saved_count = 0
            total_size = 0
            
            for file_data in files_list:
                try:
                    file_obj = File(
                        file_name=file_data['file_name'],
                        file_type=file_data['file_type'],
                        file_size=file_data['file_size'],
                        category_id=category_id,
                        telegram_file_id=file_data['telegram_file_id'],
                        storage_message_id=file_data['storage_message_id'],
                        uploaded_by=file_data['uploaded_by']
                    )
                    
                    await self.db.save_file(file_obj)
                    saved_count += 1
                    total_size += file_data['file_size']
                    
                except Exception as e:
                    logger.error(f"Error saving file {file_data['file_name']}: {e}")
            
            # Reset user state
            await self.update_user_session(user_id, action_state='browsing', temp_data=None)
            
            # Get category info
            category = await self.db.get_category_by_id(category_id)
            total_size_mb = total_size / 1024 / 1024
            
            # Success message
            text = f"🎉 <b>آپلود چندگانه تکمیل شد!</b>\n\n"
            text += f"📁 دسته: {category.name}\n"
            text += f"📊 تعداد فایل‌های ذخیره شده: {saved_count}\n"
            text += f"💾 حجم کل: {total_size_mb:.1f} MB\n\n"
            text += f"<b>فایل‌های ذخیره شده:</b>\n"
            
            for i, file_data in enumerate(files_list[:5], 1):  # Show first 5 files
                size_mb = file_data['file_size'] / 1024 / 1024
                text += f"{i}. {file_data['file_name']} ({size_mb:.1f}MB)\n"
            
            if len(files_list) > 5:
                text += f"... و {len(files_list) - 5} فایل دیگر"
            
            keyboard = await KeyboardBuilder.build_category_keyboard(
                await self.db.get_categories(category_id),
                category,
                True
            )
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def cancel_batch_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel batch upload process"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            user_id = update.effective_user.id
            session = await self.get_user_session(user_id)
            temp_data = safe_json_loads(session.temp_data)
            
            files_count = len(temp_data.get('files', []))
            category_id = temp_data.get('category_id', session.current_category)
            
            # Reset user state
            await self.update_user_session(user_id, action_state='browsing', temp_data=None)
            
            # Return to category
            category = await self.db.get_category_by_id(category_id)
            categories = await self.db.get_categories(category_id)
            keyboard = await KeyboardBuilder.build_category_keyboard(categories, category, True)
            
            # Escape special characters for Markdown
            from utils.helpers import escape_markdown
            safe_category_name = escape_markdown(category.name)
            
            text = f"❌ **آپلود چندگانه لغو شد**\n\n"
            if files_count > 0:
                text += f"⚠️ {files_count} فایل دریافت شده بود اما ذخیره نشد\\.\n"
                text += f"فایل‌ها همچنان در کانال ذخیره‌سازی موجود هستند\\.\n\n"
            text += f"📁 بازگشت به دسته '{safe_category_name}'"
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def handle_file_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle file upload"""
        try:
            user_id = update.effective_user.id
            session = await self.get_user_session(user_id)
            
            # Extract file information
            file_info = extract_file_info(update.message)
            if not file_info:
                await update.message.reply_text("❌ نوع فایل پشتیبانی نمی‌شود!")
                return
            
            file_obj, file_name, file_size, file_type = file_info
            
            # Validate file size
            if not validate_file_size(file_size, MAX_FILE_SIZE):
                await update.message.reply_text(self.messages['file_too_large'])
                return
            
            # Forward to storage channel
            forwarded = await context.bot.forward_message(
                chat_id=STORAGE_CHANNEL_ID,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            
            # Create file object
            file_data = File(
                file_name=file_name,
                file_type=file_type,
                file_size=file_size,
                category_id=session.current_category,
                telegram_file_id=file_obj.file_id,
                storage_message_id=forwarded.message_id,
                uploaded_by=user_id
            )
            
            # Save to database
            new_file_id = await self.db.save_file(file_data)
            
            # Reset user state to browsing after successful upload
            await self.update_user_session(user_id, action_state='browsing')
            
            category = await self.db.get_category_by_id(session.current_category)
            
            keyboard = KeyboardBuilder.build_file_actions_keyboard(file_data)
            
            text = f"✅ فایل با موفقیت در دسته '{category.name}' ذخیره شد!\n\n"
            text += f"📄 <b>{file_name}</b>\n"
            text += f"💾 حجم: {format_file_size(file_size)}\n"
            text += f"🏷 نوع: {file_type}"
            
            await update.message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error handling file upload: {e}")
            await update.message.reply_text(self.messages['error_occurred'])
    
    async def process_file_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process file edit input"""
        try:
            user_id = update.effective_user.id
            session = await self.get_user_session(user_id)
            temp_data = safe_json_loads(session.temp_data)
            
            file_id = temp_data.get('file_id')
            step = temp_data.get('step', 'name')
            
            new_value = update.message.text.strip()
            
            if not new_value:
                await update.message.reply_text(self.messages['invalid_input'])
                return
            
            success = False
            if step == 'name':
                success = await self.db.update_file(file_id, file_name=new_value)
            elif step == 'description':
                success = await self.db.update_file(file_id, description=new_value)
            
            await self.reset_user_state(user_id)
            
            if success:
                file = await self.db.get_file_by_id(file_id)
                keyboard = KeyboardBuilder.build_file_actions_keyboard(file)
                
                await update.message.reply_text(
                    f"✅ اطلاعات فایل با موفقیت به‌روزرسانی شد!",
                    reply_markup=keyboard
                )
            else:
                await update.message.reply_text("❌ خطا در به‌روزرسانی فایل!")
                
        except Exception as e:
            logger.error(f"Error processing file edit: {e}")
            await update.message.reply_text(self.messages['error_occurred'])