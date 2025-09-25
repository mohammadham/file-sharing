#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
General Utils Handler - Handle general utility operations
"""

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from handlers.base_handler import BaseHandler
from utils.keyboard_builder import KeyboardBuilder

logger = logging.getLogger(__name__)


class GeneralUtilsHandler(BaseHandler):
    """Handle general utility operations like confirmations and cancellations"""
    
    def __init__(self, db):
        super().__init__(db)
    # async def _handle_confirmations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Handle confirmation callbacks"""
    #     try:
    #         callback_data = update.callback_query.data
            
    #         if callback_data.startswith('confirm_delete_cat'):
    #             await self.category_handler.confirm_delete_category(update, context)
    #         elif callback_data.startswith('confirm_delete_file'):
    #             await self.file_handler.confirm_delete_file(update, context)
    #         elif callback_data.startswith('confirm_broadcast_text'):
    #             await self.broadcast_handler.confirm_text_broadcast(update, context)
    #         elif callback_data.startswith('confirm_broadcast_file'):
    #             await self.broadcast_handler.confirm_file_broadcast(update, context)
    #         else:
    #             await update.callback_query.answer("❌ نوع تأیید نامشخص!")
                
    #     except Exception as e:
    #         logger.error(f"Error handling confirmation: {e}")
    #         await update.callback_query.answer("❌ خطا در پردازش تأیید!")
    
    async def handle_confirmations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle confirmation callbacks"""
        try:
            callback_data = update.callback_query.data
            
            if callback_data.startswith('confirm_delete_cat'):
                from handlers.category_handler import CategoryHandler
                category_handler = CategoryHandler(self.db)
                await category_handler.confirm_delete_category(update, context)
            elif callback_data.startswith('confirm_delete_file'):
                from handlers.file_handler import FileHandler
                file_handler = FileHandler(self.db)
                await file_handler.confirm_delete_file(update, context)
            elif callback_data.startswith('confirm_broadcast_text'):
                from handlers.broadcast_handler import BroadcastHandler
                broadcast_handler = BroadcastHandler(self.db)
                await broadcast_handler.confirm_text_broadcast(update, context)
            elif callback_data.startswith('confirm_broadcast_file'):
                from handlers.broadcast_handler import BroadcastHandler
                broadcast_handler = BroadcastHandler(self.db)
                await broadcast_handler.confirm_file_broadcast(update, context)
            elif callback_data.startswith('confirm_deactivate_'):
                from handlers.link_management_handler import LinkManagementHandler
                link_handler = LinkManagementHandler(self.db)
                await link_handler.confirm_deactivate_link(update, context)
            else:
                await update.callback_query.answer("❌ نوع تأیید نامشخص!")
                
        except Exception as e:
            logger.error(f"Error handling confirmation: {e}")
            await update.callback_query.answer("❌ خطا در پردازش تأیید!")
    # async def _handle_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Handle cancel operations"""
    #     try:
    #         user_id = update.effective_user.id
            
    #         # Reset user state
    #         await self.db.update_user_session(
    #             user_id,
    #             action_state='browsing',
    #             temp_data=None
    #         )
            
    #         # Return to main menu
    #         categories = await self.db.get_categories(1)
    #         root_category = await self.db.get_category_by_id(1)
            
    #         keyboard = await KeyboardBuilder.build_category_keyboard(
    #             categories, root_category, True
    #         )
            
    #         await update.callback_query.edit_message_text(
    #             "✅ عملیات لغو شد. به منوی اصلی بازگشتید.",
    #             reply_markup=keyboard
    #         )
            
    #     except Exception as e:
    #         logger.error(f"Error handling cancel: {e}")
    async def handle_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle cancel operations"""
        try:
            user_id = update.effective_user.id
            
            # Reset user state
            await self.db.update_user_session(
                user_id,
                action_state='browsing',
                temp_data=None
            )
            
            # Return to main menu
            categories = await self.db.get_categories(1)
            root_category = await self.db.get_category_by_id(1)
            
            keyboard = await KeyboardBuilder.build_category_keyboard(
                categories, root_category, True
            )
            
            await update.callback_query.edit_message_text(
                "✅ عملیات لغو شد. به منوی اصلی بازگشتید.",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error handling cancel: {e}")
    
    async def handle_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle main menu navigation"""
        try:
            query = update.callback_query
            await query.answer()
            
            # Reset user state
            user_id = update.effective_user.id
            await self.db.update_user_session(
                user_id,
                current_category=1,
                action_state='browsing',
                temp_data=None
            )
            
            # Return to main menu
            categories = await self.db.get_categories(1)
            root_category = await self.db.get_category_by_id(1)
            keyboard = await KeyboardBuilder.build_category_keyboard(categories, root_category, True)
            
            await query.edit_message_text(
                "🏠 **منوی اصلی**\n\nلطفاً یکی از گزینه‌ها را انتخاب کنید:",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error handling main menu: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_page_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle page info callbacks"""
        try:
            query = update.callback_query
            
            callback_data = query.data
            
            if callback_data == 'page_info':
                await query.answer("ℹ️ اطلاعات صفحه")
            elif callback_data == 'files_count_info':
                await query.answer("📊 تعداد فایل‌های دریافت شده تا کنون")
            else:
                await query.answer("ℹ️ اطلاعات")
                
        except Exception as e:
            logger.error(f"Error handling page info: {e}")
            await query.answer("❌ خطا!")
    
    async def handle_unknown_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown callback queries"""
        try:
            callback_data = update.callback_query.data
            await update.callback_query.answer("❌ عملیات نامشخص!")
            logger.warning(f"Unknown callback data: {callback_data}")
            
            # Optionally, provide fallback to main menu
            text = "❌ **عملیات نامشخص**\n\n"
            text += "عملیات درخواستی شناخته نشده است.\n"
            text += "لطفاً از منوی اصلی استفاده کنید."
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
            ])
            
            await update.callback_query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error handling unknown callback: {e}")
    
    async def handle_error_safe(self, update, context):
        """Safe error handling for callback queries"""
        try:
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.answer("❌ خطایی رخ داد!")
            elif hasattr(update, 'message') and update.message:
                await update.message.reply_text("❌ خطایی رخ داد!")
        except Exception as e:
            logger.error(f"Error in safe error handling: {e}")