#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Message Handler - Handles text messages and user inputs
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from handlers.base_handler import BaseHandler
from handlers.category_handler import CategoryHandler
from handlers.file_handler import FileHandler
from handlers.broadcast_handler import BroadcastHandler
from handlers.search_handler import SearchHandler

logger = logging.getLogger(__name__)


class BotMessageHandler(BaseHandler):
    """Handle text messages based on user state"""
    
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.category_handler = CategoryHandler(db_manager)
        self.file_handler = FileHandler(db_manager)
        self.broadcast_handler = BroadcastHandler(db_manager)
        self.search_handler = SearchHandler(db_manager)
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Route text messages based on user state"""
        try:
            user_id = update.effective_user.id
            session = await self.get_user_session(user_id)
            
            # Route based on current action state
            if session.action_state == 'adding_category':
                await self.category_handler.process_category_name(update, context)
            
            elif session.action_state == 'editing_category':
                await self.category_handler.process_category_name(update, context)
            
            elif session.action_state == 'editing_file':
                await self.file_handler.process_file_edit(update, context)
            
            elif session.action_state == 'broadcast_text':
                await self.broadcast_handler.process_broadcast_text(update, context)
            
            elif session.action_state == 'searching':
                await self.search_handler.process_search_query(update, context)
            
            else:
                # Default state - show help or main menu
                await self.show_help(update, context)
        
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def handle_file_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle file uploads"""
        try:
            user_id = update.effective_user.id
            session = await self.get_user_session(user_id)
            
            logger.info(f"File upload attempt - User: {user_id}, State: {session.action_state}, Category: {session.current_category}")
            
            # Check if user is in a file-accepting state
            if session.action_state == 'browsing' or session.action_state == 'uploading_file':
                await self.file_handler.handle_file_upload(update, context)
            elif session.action_state == 'batch_uploading':
                await self.file_handler.handle_batch_file_upload(update, context)
            elif session.action_state == 'broadcast_file':
                await self.broadcast_handler.process_broadcast_file(update, context)
            elif session.current_category and session.current_category > 0:
                # If user has a valid current category, allow upload even in other states
                logger.info(f"Allowing file upload in category {session.current_category} for state {session.action_state}")
                # Temporarily set state to uploading_file to allow upload
                await self.update_user_session(user_id, action_state='uploading_file')
                await self.file_handler.handle_file_upload(update, context)
            else:
                await update.message.reply_text(
                    "لطفا ابتدا به دسته مورد نظر بروید و سپس فایل را ارسال کنید.\n"
                    "برای بازگشت به منوی اصلی /start را بزنید."
                )
        
        except Exception as e:
            logger.error(f"Error in handle_file_message: {e}")
            await self.handle_error(update, context, e)
    
    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help message"""
        help_text = """
🆘 **راهنمای استفاده از ربات**

**دستورات کلیدی:**
• `/start` - شروع مجدد ربات
• `/stats` - مشاهده آمار
• `/backup` - تهیه نسخه پشتیبان

**نحوه استفاده:**
1️⃣ از منوی اصلی دسته مورد نظر را انتخاب کنید
2️⃣ برای آپلود فایل، آن را در همان دسته ارسال کنید
3️⃣ برای مدیریت فایل‌ها از دکمه "مشاهده فایل‌ها" استفاده کنید

**امکانات:**
• 📁 مدیریت دسته‌بندی‌ها
• 📤 آپلود و ذخیره فایل
• 🔍 جستجو در فایل‌ها
• 📢 برودکست پیام
• 📊 مشاهده آمار

برای بازگشت به منوی اصلی از دستور /start استفاده کنید.
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')