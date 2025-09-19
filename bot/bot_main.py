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

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler as TelegramMessageHandler, filters, ContextTypes

# Import configuration
from config.settings import BOT_TOKEN, MESSAGES

# Import database manager
from database.db_manager import DatabaseManager

# Import models
from models.database_models import Link

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
            
            # Check if it's a share link
            if context.args and len(context.args) > 0:
                arg = context.args[0]
                if arg.startswith('link_'):
                    await self._handle_share_link(update, context, arg[5:])  # Remove 'link_' prefix
                    return
                elif arg.startswith('file_'):
                    # Legacy file link support
                    await self._handle_legacy_file_link(update, context, arg[5:])  # Remove 'file_' prefix
                    return
            
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
            elif callback_data.startswith('move_to_cat_') or callback_data.startswith('move_nav_cat_'):
                await self.file_handler.handle_move_category_selection(update, context)
            elif callback_data.startswith('cancel_move_'):
                await self.file_handler.cancel_file_move(update, context)
            elif callback_data.startswith('upload_'):
                await self.file_handler.show_upload_prompt(update, context)
            elif callback_data.startswith('batch_upload_'):
                await self.file_handler.start_batch_upload(update, context)
            elif callback_data.startswith('finish_batch_'):
                await self.file_handler.finish_batch_upload(update, context)
            elif callback_data.startswith('cancel_batch_'):
                await self.file_handler.cancel_batch_upload(update, context)
            elif callback_data.startswith('copy_link_'):
                await self.file_handler.copy_file_link(update, context)
            elif callback_data.startswith('details_'):
                await self.file_handler.show_file_details(update, context)
            elif callback_data.startswith('download_shared_'):
                await self._handle_shared_file_download(update, context)
            elif callback_data.startswith('details_shared_'):
                await self._handle_shared_file_details(update, context)
            elif callback_data.startswith('copy_shared_'):
                await self._handle_shared_link_copy(update, context)
            elif callback_data.startswith('stats_shared_'):
                await self._handle_shared_link_stats(update, context)
            elif callback_data.startswith('back_shared_'):
                await self._handle_back_shared(update, context)
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
            elif callback_data == 'files_count_info':
                await update.callback_query.answer("📊 تعداد فایل‌های دریافت شده تا کنون")
            
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
            from utils.keyboard_builder import KeyboardBuilder
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
        # Will implement in next step
        await update.message.reply_text("🚧 قابلیت لینک دسته‌ها در حال توسعه است!")
    
    async def _handle_collection_share_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE, link):
        """Handle shared collection link"""
        # Will implement in next step  
        await update.message.reply_text("🚧 قابلیت لینک مجموعه فایل‌ها در حال توسعه است!")
    
    async def _handle_legacy_file_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_id_str: str):
        """Handle legacy file links for backward compatibility"""
        try:
            file_id = int(file_id_str)
            file = await self.db.get_file_by_id(file_id)
            
            if not file:
                await update.message.reply_text("❌ فایل یافت نشد!")
                return
            
            # Forward to storage channel (legacy behavior)
            from config.settings import STORAGE_CHANNEL_ID
            await context.bot.forward_message(
                chat_id=update.effective_chat.id,
                from_chat_id=STORAGE_CHANNEL_ID,
                message_id=file.storage_message_id
            )
            
            await update.message.reply_text(
                f"📄 **{file.file_name}**\n"
                f"💾 حجم: {file.size_mb:.1f} MB\n\n"
                f"💡 برای لینک‌های بهتر از نسخه جدید ربات استفاده کنید!",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in legacy file link: {e}")
            await update.message.reply_text("❌ خطا در دریافت فایل!")
    
    async def _handle_shared_file_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle download from shared file"""
        try:
            query = update.callback_query
            await query.answer("در حال ارسال فایل...")
            
            file_id = int(query.data.split('_')[2])
            file = await self.db.get_file_by_id(file_id)
            
            if not file:
                await query.answer("❌ فایل یافت نشد!")
                return
            
            # Forward file from storage channel
            from config.settings import STORAGE_CHANNEL_ID
            await context.bot.forward_message(
                chat_id=update.effective_chat.id,
                from_chat_id=STORAGE_CHANNEL_ID,
                message_id=file.storage_message_id
            )
            
        except Exception as e:
            logger.error(f"Error in shared file download: {e}")
            await query.answer("❌ خطا در دانلود فایل!")
    
    async def _handle_shared_file_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle details view for shared file"""
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
            
            # Just show info without action buttons
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_shared_{file_id}")
            ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in shared file details: {e}")
            await query.answer("❌ خطا در نمایش جزئیات!")
    
    async def _handle_shared_link_copy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle copy shared link"""  
        try:
            query = update.callback_query
            await query.answer("لینک کپی شد!")
            
            short_code = query.data.split('_')[2]
            bot_info = await context.bot.get_me()
            share_url = f"https://t.me/{bot_info.username}?start=link_{short_code}"
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🔗 **لینک کپی شده:**\n`{share_url}`",
                parse_mode='Markdown',
                reply_to_message_id=query.message.message_id
            )
            
        except Exception as e:
            logger.error(f"Error copying shared link: {e}")
            await query.answer("❌ خطا در کپی لینک!")
    
    async def _handle_shared_link_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle shared link statistics"""
        try:
            query = update.callback_query
            await query.answer()
            
            short_code = query.data.split('_')[2]
            link = await self.db.get_link_by_code(short_code)
            
            if not link:
                await query.answer("❌ لینک یافت نشد!")
                return
            
            text = f"📈 **آمار لینک اشتراک‌گذاری**\n\n"
            text += f"🔗 کد: `{link.short_code}`\n"
            text += f"📊 تعداد بازدید: **{link.access_count}** بار\n"
            text += f"📅 تاریخ ایجاد: {link.created_at[:16] if link.created_at else 'نامشخص'}\n"
            text += f"💡 وضعیت: {'🟢 فعال' if link.is_active else '🔴 غیرفعال'}"
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_shared_stats_{short_code}")
            ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in shared link stats: {e}")
            await query.answer("❌ خطا در نمایش آمار!")
    
    async def _handle_back_shared(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle back button from shared views"""
        try:
            query = update.callback_query
            await query.answer()
            
            callback_data = query.data
            
            if callback_data.startswith('back_shared_stats_'):
                # Back from stats to main shared view
                short_code = callback_data.split('_')[3]
                link = await self.db.get_link_by_code(short_code)
                
                if link and link.link_type == "file":
                    file = await self.db.get_file_by_id(link.target_id)
                    if file:
                        await self._handle_file_share_link(update, context, link)
                        return
                        
            elif callback_data.startswith('back_shared_'):
                # Back from details to main shared view  
                file_id = int(callback_data.split('_')[2])
                file = await self.db.get_file_by_id(file_id)
                
                if file:
                    # Find the link for this file (get the most recent one)
                    # This is a simplification - in production you might want to pass link info
                    from database.db_manager import DatabaseManager
                    import aiosqlite
                    
                    async with aiosqlite.connect(self.db.db_path) as db:
                        db.row_factory = aiosqlite.Row
                        cursor = await db.execute('''
                            SELECT * FROM links 
                            WHERE link_type = 'file' AND target_id = ? AND is_active = 1
                            ORDER BY created_at DESC LIMIT 1
                        ''', (file_id,))
                        row = await cursor.fetchone()
                        
                        if row:
                            link = Link.from_dict(dict(row))
                            await self._handle_file_share_link(update, context, link)
                            return
            
            # Fallback
            await query.edit_message_text("❌ خطا در بازگشت!")
            
        except Exception as e:
            logger.error(f"Error in back shared: {e}")
            await query.answer("❌ خطا در بازگشت!")
    
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