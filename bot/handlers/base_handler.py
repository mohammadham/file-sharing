#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base Handler - Common functionality for all handlers
"""

import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

from database.db_manager import DatabaseManager
from models.database_models import UserSession
from config.settings import MESSAGES

logger = logging.getLogger(__name__)


class BaseHandler:
    """Base class for all bot handlers"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.messages = MESSAGES
    
    def get_user_id(self, update: Update) -> Optional[int]:
        """Safely get user ID from update"""
        if update and update.effective_user:
            return update.effective_user.id
        return None
    
    async def get_user_session(self, user_id: int) -> UserSession:
        """Get current user session"""
        return await self.db.get_user_session(user_id)
    
    async def update_user_session(self, user_id: int, **kwargs):
        """Update user session"""
        await self.db.update_user_session(user_id, **kwargs)
    
    async def handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception):
        """Handle errors gracefully"""
        logger.error(f"Error in handler: {error}")
        
        try:
            if update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.edit_message_text(
                    self.messages['error_occurred']
                )
            elif update.message:
                await update.message.reply_text(self.messages['error_occurred'])
        except Exception as e:
            logger.error(f"Error sending error message: {e}")
    
    async def answer_callback_query(self, update: Update, text: str = None):
        """Answer callback query safely"""
        try:
            if update.callback_query:
                await update.callback_query.answer(text)
        except Exception as e:
            logger.warning(f"Failed to answer callback query: {e}")
    
    def extract_user_info(self, update: Update) -> tuple:
        """Extract user information from update"""
        user = update.effective_user
        chat = update.effective_chat
        return user.id, user.first_name, chat.id
    
    async def reset_user_state(self, user_id: int):
        """Reset user to browsing state"""
        await self.update_user_session(
            user_id,
            action_state='browsing',
            temp_data=None
        )