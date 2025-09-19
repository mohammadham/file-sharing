#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main Bot File - Modular Telegram File Bot
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add bot directory to path
sys.path.append(str(Path(__file__).parent))

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler as TelegramMessageHandler, filters, ContextTypes

# Import configuration
from config.settings import BOT_TOKEN, MESSAGES

# Import database manager
from database.db_manager import DatabaseManager

# Import handlers
from handlers.category_handler import CategoryHandler
from handlers.file_handler import FileHandler
from handlers.message_handler import BotMessageHandler
from handlers.broadcast_handler import BroadcastHandler
from handlers.search_handler import SearchHandler

# Import actions
from actions.stats_action import StatsAction  
from actions.backup_action import BackupAction

# Import utilities
from utils.keyboard_builder import KeyboardBuilder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelegramFileBot:
    """Modular Telegram File Bot"""
    
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.db = DatabaseManager()
        
        # Initialize handlers
        self.category_handler = CategoryHandler(self.db)
        self.file_handler = FileHandler(self.db)
        self.message_handler = BotMessageHandler(self.db)
        self.broadcast_handler = BroadcastHandler(self.db)
        self.search_handler = SearchHandler(self.db)
        
        # Initialize actions
        self.stats_action = StatsAction(self.db)
        self.backup_action = BackupAction(self.db)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            user_id = update.effective_user.id
            session = await self.db.get_user_session(user_id)
            
            # Reset user state
            await self.db.update_user_session(
                user_id,
                current_category=1,
                action_state='browsing',
                temp_data=None
            )
            
            # Get root categories
            categories = await self.db.get_categories(1)  # Get subcategories of root
            root_category = await self.db.get_category_by_id(1)
            
            keyboard = await KeyboardBuilder.build_category_keyboard(
                categories, root_category, True
            )
            
            await update.message.reply_text(
                MESSAGES['welcome'], 
                reply_markup=keyboard, 
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text(MESSAGES['error_occurred'])
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        await self.stats_action.show_detailed_stats(update, context)
    
    async def backup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /backup command"""
        await self.backup_action.create_backup(update, context)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await self.message_handler.show_help(update, context)
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Route callback queries to appropriate handlers"""
        try:
            callback_data = update.callback_query.data
            action = callback_data.split('_')[0]
            
            # Category operations
            if action == 'cat':
                await self.category_handler.show_category(update, context)
            elif callback_data.startswith('add_cat'):
                await self.category_handler.add_category(update, context)
            elif callback_data.startswith('edit_cat'):
                await self.category_handler.edit_category(update, context)
            elif callback_data.startswith('del_cat'):
                await self.category_handler.delete_category(update, context)
            elif callback_data.startswith('confirm_delete_cat'):
                await self.category_handler.confirm_delete_category(update, context)
            
            # File operations
            elif action == 'files':
                await self.file_handler.show_files(update, context)
            elif action == 'file':
                await self.file_handler.show_file_details(update, context)
            elif callback_data.startswith('download'):
                await self.file_handler.download_file(update, context)
            elif callback_data.startswith('edit_file'):
                await self.file_handler.edit_file(update, context)
            elif callback_data.startswith('delete_file'):
                await self.file_handler.delete_file(update, context)
            elif callback_data.startswith('confirm_delete_file'):
                await self.file_handler.confirm_delete_file(update, context)
            elif callback_data.startswith('move_file'):
                await self.file_handler.move_file(update, context)
            elif callback_data.startswith('upload_'):
                await self.file_handler.show_upload_prompt(update, context)
            elif callback_data.startswith('confirm_'):
                await self._handle_confirmations(update, context)
            
            # Broadcast operations
            elif callback_data == 'broadcast_menu':
                await self.broadcast_handler.show_broadcast_menu(update, context)
            elif callback_data == 'broadcast_text':
                await self.broadcast_handler.start_text_broadcast(update, context)
            elif callback_data == 'broadcast_file':
                await self.broadcast_handler.start_file_broadcast(update, context)
            elif callback_data.startswith('confirm_broadcast_text'):
                await self.broadcast_handler.confirm_text_broadcast(update, context)
            elif callback_data.startswith('confirm_broadcast_file'):
                await self.broadcast_handler.confirm_file_broadcast(update, context)
            
            # Search operations
            elif callback_data == 'search':
                await self.search_handler.start_search(update, context)
            elif callback_data == 'advanced_search':
                await self.search_handler.show_advanced_search(update, context)
            
            # Stats
            elif callback_data == 'stats':
                await self.stats_action.show_stats(update, context)
            
            # Cancel operations
            elif action == 'cancel':
                await self._handle_cancel(update, context)
            
            # Page info (just ignore)
            elif callback_data == 'page_info':
                await update.callback_query.answer("ℹ️ اطلاعات صفحه")
            
            else:
                await update.callback_query.answer("❌ عملیات نامشخص!")
                logger.warning(f"Unknown callback data: {callback_data}")
        
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            try:
                await update.callback_query.answer("❌ خطایی رخ داد!")
            except:
                pass
    
    async def _handle_confirmations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle confirmation callbacks"""
        try:
            callback_data = update.callback_query.data
            
            if callback_data.startswith('confirm_delete_cat'):
                await self.category_handler.confirm_delete_category(update, context)
            elif callback_data.startswith('confirm_delete_file'):
                await self.file_handler.confirm_delete_file(update, context)
            elif callback_data.startswith('confirm_broadcast_text'):
                await self.broadcast_handler.confirm_text_broadcast(update, context)
            elif callback_data.startswith('confirm_broadcast_file'):
                await self.broadcast_handler.confirm_file_broadcast(update, context)
            else:
                await update.callback_query.answer("❌ نوع تأیید نامشخص!")
                
        except Exception as e:
            logger.error(f"Error handling confirmation: {e}")
            await update.callback_query.answer("❌ خطا در پردازش تأیید!")
    
    async def _handle_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    def register_handlers(self):
        """Register all handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("backup", self.backup_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))
        
        # Message handlers
        self.application.add_handler(TelegramMessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.message_handler.handle_text_message
        ))
        
        self.application.add_handler(TelegramMessageHandler(
            filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO,
            self.message_handler.handle_file_message
        ))
        
        logger.info("All handlers registered successfully")
    
    async def start_bot(self):
        """Start the Telegram bot"""
        try:
            # Initialize database
            await self.db.init_database()
            logger.info("Database initialized")
            
            # Register handlers
            self.register_handlers()
            
            logger.info("✅ Modular Telegram File Bot started successfully!")
            
            # Start the bot
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            # Keep running
            try:
                await asyncio.Event().wait()
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
            finally:
                await self.application.stop()
                await self.application.shutdown()
                
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise


async def main():
    """Main function"""
    bot = TelegramFileBot()
    await bot.start_bot()


if __name__ == "__main__":
    asyncio.run(main())