#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Search Handler - Handles search operations
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.base_handler import BaseHandler
from utils.keyboard_builder import KeyboardBuilder
from utils.helpers import build_file_info_text
from config.settings import MAX_SEARCH_RESULTS

logger = logging.getLogger(__name__)


class SearchHandler(BaseHandler):
    """Handle search operations"""
    
    async def start_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start search process"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            user_id = update.effective_user.id
            await self.update_user_session(user_id, action_state='searching')
            
            keyboard = KeyboardBuilder.build_cancel_keyboard("cat_1")
            
            text = "🔍 **جستجو در فایل‌ها**\n\n"
            text += "نام فایل یا کلمه کلیدی را وارد کنید:\n\n"
            text += "💡 **نکات:**\n"
            text += "• می‌توانید بخشی از نام فایل را وارد کنید\n"
            text += "• جستجو در نام فایل و توضیحات انجام می‌شود\n"
            text += f"• حداکثر {MAX_SEARCH_RESULTS} نتیجه نمایش داده می‌شود"
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def process_search_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process search query"""
        try:
            user_id = update.effective_user.id
            search_query = update.message.text.strip()
            
            if not search_query or len(search_query) < 2:
                await update.message.reply_text(
                    "❌ کلمه جستجو باید حداقل 2 کاراکتر باشد!"
                )
                return
            
            # Perform search
            results = await self.db.search_files(search_query, MAX_SEARCH_RESULTS)
            
            await self.reset_user_state(user_id)
            
            if results:
                text = f"🔍 **نتایج جستجو برای '{search_query}':**\n\n"
                text += f"📊 تعداد نتایج: {len(results)}\n\n"
                
                keyboard_buttons = []
                
                for i, file_dict in enumerate(results, 1):
                    # Add file info to text
                    size_mb = file_dict.get('file_size', 0) / 1024 / 1024
                    text += f"**{i}.** 📄 **{file_dict.get('file_name', 'نامشخص')}**\n"
                    text += f"   📁 {file_dict.get('category_name', 'نامشخص')}\n"
                    text += f"   💾 {size_mb:.1f} MB\n"
                    
                    upload_date = file_dict.get('uploaded_at', '')
                    if upload_date:
                        text += f"   📅 {upload_date[:16]}\n"
                    
                    if file_dict.get('description'):
                        desc = file_dict['description'][:50]
                        text += f"   📝 {desc}{'...' if len(file_dict['description']) > 50 else ''}\n"
                    
                    text += "\n"
                    
                    # Add button for file
                    keyboard_buttons.append([{
                        'text': f"📄 {file_dict.get('file_name', 'نامشخص')[:20]}...",
                        'callback_data': f"file_{file_dict.get('id')}"
                    }])
                
                # Build keyboard with file buttons
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = []
                
                for button_info in keyboard_buttons[:5]:  # Show max 5 buttons
                    button = button_info[0]
                    keyboard.append([InlineKeyboardButton(
                        button['text'], 
                        callback_data=button['callback_data']
                    )])
                
                # Add back button
                keyboard.append([InlineKeyboardButton("🔙 منوی اصلی", callback_data="cat_1")])
                keyboard_markup = InlineKeyboardMarkup(keyboard)
                
            else:
                text = f"❌ هیچ فایلی با کلمه '{search_query}' یافت نشد.\n\n"
                text += "💡 **پیشنهادات:**\n"
                text += "• از کلمات کوتاه‌تر استفاده کنید\n"
                text += "• املای کلمات را بررسی کنید\n"
                text += "• از بخشی از نام فایل استفاده کنید"
                
                keyboard_markup = KeyboardBuilder.build_cancel_keyboard("cat_1")
            
            await update.message.reply_text(
                text,
                reply_markup=keyboard_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error processing search: {e}")
            await update.message.reply_text(self.messages['error_occurred'])
    
    async def show_advanced_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show advanced search options"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            text = "🔍 **جستجوی پیشرفته**\n\n"
            text += "انواع جستجو:\n"
            text += "• 📄 **بر اساس نام فایل**\n"
            text += "• 🏷 **بر اساس نوع فایل**\n"
            text += "• 📁 **در دسته خاص**\n"
            text += "• 📅 **بر اساس تاریخ**\n"
            text += "• 💾 **بر اساس اندازه**"
            
            keyboard = [
                [
                    InlineKeyboardButton("📄 نام فایل", callback_data="search_name"),
                    InlineKeyboardButton("🏷 نوع فایل", callback_data="search_type")
                ],
                [
                    InlineKeyboardButton("📁 در دسته", callback_data="search_category"),
                    InlineKeyboardButton("📅 تاریخ", callback_data="search_date")
                ],
                [
                    InlineKeyboardButton("💾 اندازه", callback_data="search_size"),
                    InlineKeyboardButton("🔍 جستجوی عادی", callback_data="search")
                ],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="cat_1")]
            ]
            
            from telegram import InlineKeyboardMarkup
            keyboard_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)