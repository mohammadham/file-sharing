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
from handlers.category_link_handler import CategoryLinkHandler
from handlers.category_edit_handler import CategoryEditHandler

# Import actions
from actions.stats_action import StatsAction  
from actions.backup_action import BackupAction

# Import utilities
from utils.keyboard_builder import KeyboardBuilder
from utils.helpers import safe_json_dumps

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
        self.category_link_handler = CategoryLinkHandler(self.db)
        self.category_edit_handler = CategoryEditHandler(self.db)
        
        # Initialize download system handler
        from handlers.download_system_handler import DownloadSystemHandler
        self.download_system_handler = DownloadSystemHandler(
            self.db,
            download_api_url="http://localhost:8001",
            admin_token="uVsXgmICyxa0mhPshBJZ1XtYpFFt-p5rLrdMvZnhv4c"
        )
        
        # Initialize Telethon management handlers
        from handlers.telethon_config_handler import TelethonConfigHandler
        from handlers.telethon_login_handler import TelethonLoginHandler
        from handlers.telethon_health_handler import TelethonHealthHandler
        
        self.telethon_config_handler = TelethonConfigHandler(self.db)
        self.telethon_login_handler = TelethonLoginHandler(self.db)
        self.telethon_health_handler = TelethonHealthHandler(self.db)
        
        # Initialize actions
        self.stats_action = StatsAction(self.db)
        self.backup_action = BackupAction(self.db)
    
    async def update_user_session(self, user_id: int, **kwargs):
        """Update user session"""
        await self.db.update_user_session(user_id, **kwargs)
    
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
            
            # DEBUG: Log all callback data for troubleshooting
            logger.info(f"Received callback_data: '{callback_data}', action: '{action}'")
            
            # Category operations
            if action == 'cat':
                await self.category_handler.show_category(update, context)
            elif callback_data.startswith('add_cat'):
                await self.category_handler.add_category(update, context)
            elif callback_data.startswith('edit_category_menu_'):
                await self.category_edit_handler.show_edit_menu(update, context)
            elif callback_data.startswith('edit_cat_name_'):
                await self.category_edit_handler.edit_category_name(update, context)
            elif callback_data.startswith('edit_cat_desc_'):
                await self.category_edit_handler.edit_category_description(update, context)
            elif callback_data.startswith('edit_cat') and not callback_data.startswith('edit_cat_'):
                await self.category_handler.edit_category(update, context)
            elif callback_data.startswith('del_cat'):
                await self.category_handler.delete_category(update, context)
            elif callback_data.startswith('confirm_delete_cat'):
                await self.category_handler.confirm_delete_category(update, context)
            
            # File operations - IMPORTANT: Check specific patterns before general ones
            elif callback_data.startswith('file_download_links_'):
                await self.download_system_handler.show_file_download_options(update, context)
            elif action == 'files':
                await self.file_handler.show_files(update, context)
            elif action == 'file':
                await self.file_handler.show_file_details(update, context)
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
            elif callback_data.startswith('link_stats_'):
                await self._handle_link_stats(update, context)
            elif callback_data.startswith('deactivate_link_'):
                await self._handle_deactivate_link(update, context)
            elif callback_data == 'my_links':
                await self._handle_my_links(update, context)
            
            # Category link operations
            elif callback_data.startswith('category_link_'):
                await self.category_link_handler.show_category_link_options(update, context)
            elif callback_data.startswith('create_category_link_'):
                await self.category_link_handler.create_category_link(update, context)
            elif callback_data.startswith('select_files_'):
                await self.category_link_handler.show_files_selection(update, context)
            elif callback_data.startswith('toggle_file_'):
                await self.category_link_handler.toggle_file_selection(update, context)
            elif callback_data.startswith('select_all_'):
                await self.category_link_handler.select_all_files(update, context)
            elif callback_data.startswith('clear_selection_'):
                await self.category_link_handler.clear_selection(update, context)
            elif callback_data.startswith('create_collection_link_'):
                await self.category_link_handler.create_collection_link(update, context)
            elif callback_data.startswith('category_stats_'):
                await self.category_link_handler.show_category_stats(update, context)
            elif callback_data.startswith('browse_shared_category_'):
                await self._handle_browse_shared_category(update, context)
            elif callback_data.startswith('browse_shared_collection_'):
                await self._handle_browse_shared_collection(update, context)
            elif callback_data.startswith('back_to_shared_'):
                await self._handle_back_to_shared(update, context)
            
            # Download System Control - MUST BE BEFORE other download checks
            elif callback_data == 'download_system_control':
                await self.download_system_handler.show_system_control(update, context)
            elif callback_data.startswith('create_stream_link_'):
                await self.download_system_handler.create_stream_link(update, context)
            elif callback_data.startswith('create_fast_link_'):
                await self.download_system_handler.create_fast_link(update, context)
            elif callback_data.startswith('create_restricted_link_'):
                await self.download_system_handler.create_restricted_link(update, context)
            elif callback_data.startswith('view_file_links_'):
                await self.download_system_handler.view_file_links(update, context)
            elif callback_data.startswith('set_max_downloads_'):
                await self.download_system_handler.handle_set_max_downloads(update, context)
            elif callback_data.startswith('set_expires_'):
                await self.download_system_handler.handle_set_expires(update, context)
            elif callback_data.startswith('confirm_create_restricted_'):
                await self.download_system_handler.create_final_restricted_link(update, context)
            elif callback_data.startswith('copy_restricted_link_'):
                await self.download_system_handler.copy_link_handler(update, context)
            elif callback_data.startswith('copy_stream_link_'):
                await self.download_system_handler.copy_link_handler(update, context)
            elif callback_data.startswith('copy_fast_link_'):
                await self.download_system_handler.copy_link_handler(update, context)
            elif callback_data.startswith('download_link_stats_'):
                await self.download_system_handler.show_download_link_stats(update, context)
            elif callback_data.startswith('download_link_info_'):
                await self.download_system_handler.show_download_link_info(update, context)
            elif callback_data.startswith('delete_download_link_'):
                await self.download_system_handler.delete_download_link(update, context)
            elif callback_data == 'system_monitoring':
                await self.download_system_handler.system_monitoring(update, context)
            elif callback_data == 'system_cleanup':
                await self.download_system_handler.system_cleanup(update, context)
            elif callback_data == 'system_settings':
                await self.download_system_handler.handle_system_settings(update, context)
            elif callback_data == 'token_management':
                await self.download_system_handler.handle_token_management(update, context)
            elif callback_data == 'api_settings':
                await self.download_system_handler.handle_api_settings(update, context)
            elif callback_data == 'download_stats':
                await self.download_system_handler.handle_download_stats(update, context)
            elif callback_data == 'retry_api_connection':
                await self.download_system_handler.handle_api_settings(update, context)
            elif callback_data == 'telethon_management':
                # Navigate to Telethon management
                from handlers.telethon_config_handler import TelethonConfigHandler
                telethon_handler = TelethonConfigHandler(self.db)
                await telethon_handler.show_telethon_management_menu(update, context)
            elif callback_data == 'test_api_connection':
                await self._handle_test_api_connection(update, context)
            
            # Telethon Management Operations
            elif callback_data == 'telethon_management_menu':
                await self.telethon_config_handler.show_telethon_management_menu(update, context)
            elif callback_data == 'telethon_list_configs':
                await self.telethon_config_handler.show_config_list(update, context)
            elif callback_data == 'telethon_add_config':
                await self.telethon_config_handler.show_add_config_menu(update, context)
            elif callback_data == 'telethon_show_json_example':
                await self.telethon_config_handler.show_json_example(update, context)
            elif callback_data == 'telethon_upload_json':
                await self.telethon_config_handler.start_json_upload(update, context)
            elif callback_data.startswith('telethon_manage_config_'):
                # TODO: Implement config management
                await update.callback_query.answer("در حال توسعه...")
            elif callback_data.startswith('telethon_delete_config_'):
                # TODO: Implement config deletion
                await update.callback_query.answer("در حال توسعه...")
            
            # Telethon Login Operations
            elif callback_data == 'telethon_login_menu':
                await self.telethon_login_handler.show_login_menu(update, context)
            elif callback_data.startswith('telethon_start_login_'):
                await self.telethon_login_handler.start_login_process(update, context)
            elif callback_data.startswith('telethon_login_phone_'):
                # Extract config_name and phone from callback data
                parts = callback_data.split('_')[3:]
                config_name = parts[0]
                phone = '_'.join(parts[1:])
                await self.telethon_login_handler.send_verification_code(update, context, config_name, phone)
            elif callback_data.startswith('telethon_test_session_'):
                await self.telethon_login_handler.test_session(update, context)
            
            # Telethon Health Check Operations
            elif callback_data == 'telethon_health_check':
                await self.telethon_health_handler.show_health_check(update, context)
            elif callback_data == 'telethon_diagnose_issues':
                await self.telethon_health_handler.show_detailed_diagnostics(update, context)
            elif callback_data == 'telethon_system_status':
                await self.telethon_health_handler.show_system_status(update, context)
            
            # NEW: Handle download all operations
            elif callback_data.startswith('download_all_category_'):
                await self._handle_download_all_category(update, context)
            elif callback_data.startswith('download_all_collection_'):
                await self._handle_download_all_collection(update, context)
            elif callback_data.startswith('download_shared_file_'):
                await self._handle_download_shared_file(update, context)
            elif callback_data.startswith('download_shared_'):
                await self._handle_shared_file_download(update, context)
            elif callback_data.startswith('download'):
                await self.file_handler.download_file(update, context)
            
            # Advanced category edit operations
            elif callback_data.startswith('edit_cat_name_'):
                await self.category_edit_handler.edit_category_name(update, context)
            elif callback_data.startswith('edit_cat_desc_'):
                await self.category_edit_handler.edit_category_description(update, context)
            elif callback_data.startswith('set_cat_icon_'):
                await self.category_edit_handler.show_icon_selection(update, context)
            elif callback_data.startswith('select_icon_'):
                await self.category_edit_handler.select_icon(update, context)
            elif callback_data.startswith('icon_page_'):
                await self._handle_icon_page(update, context)
            elif callback_data.startswith('set_cat_thumbnail_'):
                await self.category_edit_handler.show_thumbnail_options(update, context)
            elif callback_data.startswith('upload_thumbnail_'):
                await self.category_edit_handler.start_thumbnail_upload(update, context)
            elif callback_data.startswith('remove_thumbnail_'):
                await self.category_edit_handler.remove_thumbnail(update, context)
            elif callback_data.startswith('set_cat_tags_'):
                await self.category_edit_handler.set_category_tags(update, context)
            elif callback_data.startswith('move_category_'):
                await self._handle_move_category(update, context)
            elif callback_data.startswith('move_cat_nav_'):
                await self._handle_move_category_navigation(update, context)
            elif callback_data.startswith('move_cat_to_'):
                await self._handle_move_category_to(update, context)
            elif callback_data.startswith('cancel_move_cat_'):
                await self._handle_cancel_move_category(update, context)
            elif callback_data.startswith('details_shared_'):
                await self._handle_shared_file_details(update, context)
            elif callback_data.startswith('details_'):
                await self.file_handler.show_file_details(update, context)
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
            elif callback_data == 'main_menu':
                # Return to main menu
                categories = await self.db.get_categories(1)
                root_category = await self.db.get_category_by_id(1)
                keyboard = await KeyboardBuilder.build_category_keyboard(categories, root_category, True)
                await update.callback_query.edit_message_text(
                    "🏠 **منوی اصلی**\n\nلطفاً یکی از گزینه‌ها را انتخاب کنید:",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            
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
            
    async def _handle_browse_shared_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            
    async def _handle_browse_shared_collection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    async def _handle_download_shared_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    async def _handle_download_all_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    async def _handle_download_all_collection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    async def _handle_back_to_shared(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    async def _handle_move_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle category move operation"""
        try:
            query = update.callback_query
            await query.answer()
            
            category_id = int(query.data.split('_')[2])
            user_id = update.effective_user.id
            
            category = await self.db.get_category_by_id(category_id)
            if not category:
                await query.edit_message_text("دسته‌بندی یافت نشد!")
                return
            
            # Root category cannot be moved
            if category_id == 1:
                text = "❌ **خطا در انتقال دسته**\n\n"
                text += "دسته اصلی قابل انتقال نیست."
                
                keyboard = KeyboardBuilder.build_cancel_keyboard(f"edit_category_menu_{category_id}")
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
                return
            
            # Set user state for moving category
            await self.update_user_session(
                user_id,
                action_state='moving_category',
                temp_data=safe_json_dumps({'category_id': category_id, 'current_move_category': 1})
            )
            
            # Show category selection starting from root
            await self._show_move_category_destinations(update, context, category_id, 1)
            
        except Exception as e:
            logger.error(f"Error in move category: {e}")
            await query.answer("❌ خطا در انتقال دسته!")
    
    async def _show_move_category_destinations(self, update: Update, context: ContextTypes.DEFAULT_TYPE, category_id: int, current_parent_id: int):
        """Show available destination categories for moving"""
        try:
            category = await self.db.get_category_by_id(category_id)
            current_parent = await self.db.get_category_by_id(current_parent_id)
            
            # Get available categories (excluding self and its children)
            all_categories = await self.db.get_categories(current_parent_id)
            available_categories = []
            
            for cat in all_categories:
                # Exclude the category being moved and its children
                if cat.id != category_id and not await self._is_child_category(cat.id, category_id):
                    available_categories.append(cat)
            
            text = f"📁 **انتقال دسته '{category.name}'**\n\n"
            text += f"📂 دسته فعلی: {current_parent.name if current_parent else 'منوی اصلی'}\n\n"
            
            if available_categories:
                text += "📋 دسته‌های موجود برای انتقال:"
            else:
                text += "📄 هیچ دسته مقصدی در این بخش موجود نیست.\n"
                text += "برای انتقال به این دسته، 'انتخاب این دسته' را بزنید."
            
            keyboard = await self._build_move_category_keyboard(available_categories, category_id, current_parent_id, current_parent)
            
            await update.callback_query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error showing move category destinations: {e}")
    
    async def _is_child_category(self, potential_child_id: int, parent_id: int) -> bool:
        """Check if a category is a child of another category"""
        try:
            current_category = await self.db.get_category_by_id(potential_child_id)
            
            while current_category and current_category.parent_id:
                if current_category.parent_id == parent_id:
                    return True
                current_category = await self.db.get_category_by_id(current_category.parent_id)
            
            return False
        except:
            return False
    
    async def _build_move_category_keyboard(self, categories, category_id: int, current_parent_id: int, current_parent):
        """Build keyboard for category move operation"""
        keyboard = []
        
        # Show categories (navigate into them)
        for i in range(0, len(categories), 2):
            row = []
            for j in range(2):
                if i + j < len(categories):
                    cat = categories[i + j]
                    row.append(InlineKeyboardButton(
                        f"📁 {cat.name}", 
                        callback_data=f"move_cat_nav_{category_id}_{cat.id}"
                    ))
            keyboard.append(row)
        
        # Option to select current category (if not root)
        if current_parent and current_parent.id != 1:
            keyboard.append([
                InlineKeyboardButton(
                    f"✅ انتخاب '{current_parent.name}'", 
                    callback_data=f"move_cat_to_{category_id}_{current_parent.id}"
                )
            ])
        elif current_parent_id == 1:
            keyboard.append([
                InlineKeyboardButton(
                    "✅ انتقال به منوی اصلی", 
                    callback_data=f"move_cat_to_{category_id}_1"
                )
            ])
        
        # Navigation buttons
        nav_row = []
        
        # Back button (if not at root)
        if current_parent and current_parent.parent_id:
            nav_row.append(InlineKeyboardButton(
                "🔙 بازگشت", 
                callback_data=f"move_cat_nav_{category_id}_{current_parent.parent_id}"
            ))
        elif current_parent and current_parent.id != 1:
            nav_row.append(InlineKeyboardButton(
                "🔙 منوی اصلی", 
                callback_data=f"move_cat_nav_{category_id}_1"
            ))
        
        # Cancel button
        nav_row.append(InlineKeyboardButton(
            "❌ لغو انتقال", 
            callback_data=f"cancel_move_cat_{category_id}"
        ))
        
        if nav_row:
            keyboard.append(nav_row)
        
        return InlineKeyboardMarkup(keyboard)
    
    async def _handle_move_category_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle navigation during category move"""
        try:
            query = update.callback_query
            await query.answer()
            
            parts = query.data.split('_')
            category_id = int(parts[3])
            new_parent_id = int(parts[4])
            
            # Update user session with new current category
            user_id = update.effective_user.id
            await self.update_user_session(
                user_id,
                temp_data=safe_json_dumps({'category_id': category_id, 'current_move_category': new_parent_id})
            )
            
            # Show new destinations
            await self._show_move_category_destinations(update, context, category_id, new_parent_id)
            
        except Exception as e:
            logger.error(f"Error in move category navigation: {e}")
            await query.answer("❌ خطا در ناوبری!")
    
    async def _handle_move_category_to(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Execute the category move operation"""
        try:
            query = update.callback_query
            await query.answer("در حال انتقال دسته...")
            
            parts = query.data.split('_')
            category_id = int(parts[3])
            new_parent_id = int(parts[4])
            user_id = update.effective_user.id
            
            # Get category info
            category = await self.db.get_category_by_id(category_id)
            new_parent = await self.db.get_category_by_id(new_parent_id) if new_parent_id != 1 else None
            
            # Perform the move
            success = await self.db.update_category(category_id, parent_id=new_parent_id)
            
            # Reset user state
            await self.update_user_session(user_id, action_state='browsing', temp_data=None)
            
            if success:
                text = f"✅ **انتقال موفقیت‌آمیز**\n\n"
                text += f"📁 دسته: {category.name}\n"
                text += f"📂 مقصد جدید: {new_parent.name if new_parent else 'منوی اصلی'}\n\n"
                text += "دسته با موفقیت منتقل شد!"
                
                keyboard = KeyboardBuilder.build_category_edit_menu_keyboard(category_id)
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                await query.edit_message_text("❌ خطا در انتقال دسته!")
                
        except Exception as e:
            logger.error(f"Error moving category: {e}")
            await query.answer("❌ خطا در انتقال دسته!")
    
    async def _handle_cancel_move_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel category move operation"""
        try:
            query = update.callback_query
            await query.answer()
            
            category_id = int(query.data.split('_')[3])
            user_id = update.effective_user.id
            
            # Reset user state
            await self.update_user_session(user_id, action_state='browsing', temp_data=None)
            
            text = "❌ انتقال دسته لغو شد."
            keyboard = KeyboardBuilder.build_category_edit_menu_keyboard(category_id)
            
            await query.edit_message_text(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error canceling move category: {e}")
    
    async def _handle_legacy_file_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_id: str):
        """Handle legacy file links"""
        try:
            file = await self.db.get_file_by_id(int(file_id))
            if not file:
                await update.message.reply_text("❌ فایل یافت نشد!")
                return
                
            category = await self.db.get_category_by_id(file.category_id)
            category_name = category.name if category else "نامشخص"
            
            from utils.helpers import build_file_info_text
            
            text = f"📄 **فایل**\n\n"
            text += f"📁 دسته: {category_name}\n\n"
            text += build_file_info_text(file.to_dict(), category_name)
            
            keyboard = KeyboardBuilder.build_file_actions_keyboard(file)
            
            await update.message.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error handling legacy file link: {e}")
            await update.message.reply_text("❌ خطا در پردازش لینک!")
    
    async def _handle_shared_file_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle shared file download"""
        try:
            await self._handle_download_shared_file(update, context)
        except Exception as e:
            logger.error(f"Error in shared file download: {e}")
            await update.callback_query.answer("❌ خطا در دانلود فایل!")
    
    async def _handle_shared_file_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    async def _handle_shared_link_copy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle copying shared link"""
        try:
            query = update.callback_query
            await query.answer()
            
            short_code = query.data.split('_')[2]
            
            # Get bot username for proper URL
            bot_info = await context.bot.get_me()
            share_url = f"https://t.me/{bot_info.username}?start=link_{short_code}"
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🔗 **کپی لینک:**\n`{share_url}`",
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
            
            from utils.link_manager import LinkManager
            link_manager = LinkManager(self.db)
            
            stats = await link_manager.get_link_stats(short_code)
            if not stats:
                await query.answer("❌ آمار لینک یافت نشد!")
                return
            
            text = f"📈 **آمار لینک اشتراک‌گذاری**\n\n"
            text += f"🔗 **کد:** `{stats['short_code']}`\n"
            text += f"📊 **بازدید:** {stats['access_count']} بار\n"
            text += f"📅 **تاریخ ایجاد:** {stats['created_at'][:16] if stats['created_at'] else 'نامشخص'}\n"
            text += f"🏷 **عنوان:** {stats['title']}\n"
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")
            ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in shared link stats: {e}")
            await query.answer("❌ خطا در نمایش آمار!")
    
    async def _handle_back_shared(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle back from shared link"""
        try:
            await self._handle_back_to_shared(update, context)
        except Exception as e:
            logger.error(f"Error in back shared: {e}")
            await update.callback_query.answer("❌ خطا در بازگشت!")
    
    async def _handle_icon_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle icon page navigation"""
        try:
            query = update.callback_query
            await query.answer()
            
            parts = query.data.split('_')
            category_id = int(parts[2])
            page = int(parts[3])
            
            keyboard = KeyboardBuilder.build_icon_selection_keyboard(category_id, page)
            
            await query.edit_message_reply_markup(reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in icon page: {e}")
            await query.answer("❌ خطا در تغییر صفحه!")
    
    async def _handle_link_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle link statistics"""
        try:
            query = update.callback_query
            await query.answer()
            
            short_code = query.data.split('_')[2]
            
            from utils.link_manager import LinkManager
            link_manager = LinkManager(self.db)
            
            stats = await link_manager.get_link_stats(short_code)
            if not stats:
                await query.answer("❌ لینک یافت نشد!")
                return
            
            text = f"📈 **آمار تفصیلی لینک**\n\n"
            text += f"🔗 **کد:** `{stats['short_code']}`\n"
            text += f"📊 **بازدید:** {stats['access_count']} بار\n"
            text += f"📅 **تاریخ ایجاد:** {stats['created_at'][:16] if stats['created_at'] else 'نامشخص'}\n"
            
            if stats['expires_at']:
                expiry_status = "🔴 منقضی شده" if stats['is_expired'] else "🟢 فعال"
                text += f"⏰ **انقضا:** {stats['expires_at'][:16]} ({expiry_status})\n"
            else:
                text += f"♾️ **انقضا:** بدون محدودیت\n"
            
            text += f"🏷 **عنوان:** {stats['title']}\n"
            
            if stats.get('target_info'):
                target = stats['target_info']
                if stats['link_type'] == 'file':
                    from utils.helpers import format_file_size
                    text += f"\n📄 **فایل مقصد:**\n"
                    text += f"   • نام: {target['name']}\n"
                    text += f"   • حجم: {format_file_size(target['size'])}\n"
                    text += f"   • نوع: {target['type']}\n"
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data=f"file_{stats.get('target_id', 1)}")
            ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in link stats: {e}")
            await query.answer("❌ خطا در نمایش آمار!")
    
    async def _handle_deactivate_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle link deactivation"""
        try:
            query = update.callback_query
            await query.answer()
            
            short_code = query.data.split('_')[2]
            user_id = update.effective_user.id
            
            from utils.link_manager import LinkManager
            link_manager = LinkManager(self.db)
            
            success = await link_manager.deactivate_link(short_code, user_id)
            
            if success:
                text = f"🔒 **لینک غیرفعال شد**\n\n"
                text += f"کد `{short_code}` با موفقیت غیرفعال شد.\n"
                text += f"دیگر قابل استفاده نخواهد بود."
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("📋 لینک‌های من", callback_data="my_links"),
                    InlineKeyboardButton("🏠 منوی اصلی", callback_data="cat_1")
                ]])
                
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                await query.answer("❌ خطا در غیرفعال‌سازی لینک!")
                
        except Exception as e:
            logger.error(f"Error deactivating link: {e}")
            await query.answer("❌ خطا در غیرفعال‌سازی!")
    
    async def _handle_my_links(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's created links"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = update.effective_user.id
            
            from utils.link_manager import LinkManager
            link_manager = LinkManager(self.db)
            
            links = await link_manager.get_user_links(user_id, limit=10)
            
            if not links:
                text = "📋 **لینک‌های شما**\n\n"
                text += "شما هنوز هیچ لینکی ایجاد نکرده‌اید.\n"
                text += "از منوی فایل‌ها برای ایجاد لینک استفاده کنید."
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 منوی اصلی", callback_data="cat_1")
                ]])
            else:
                text = f"📋 **لینک‌های شما** ({len(links)} لینک)\n\n"
                
                for i, link in enumerate(links[:5], 1):
                    status = "🔴" if link['is_expired'] else "🟢"
                    text += f"{i}. {status} **{link['title'][:25]}...**\n"
                    text += f"   🔗 `{link['short_code']}` | 📊 {link['access_count']} بازدید\n"
                    text += f"   📅 {link['created_at'][:16] if link['created_at'] else 'نامشخص'}\n\n"
                
                if len(links) > 5:
                    text += f"... و {len(links) - 5} لینک دیگر"
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 منوی اصلی", callback_data="cat_1")]
                ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error showing user links: {e}")
            await query.answer("❌ خطا در نمایش لینک‌ها!")
    
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
    
    async def handle_error_safe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors safely without causing additional exceptions"""
        try:
            if update.callback_query:
                await update.callback_query.answer("❌ خطایی رخ داد! لطفا دوباره تلاش کنید.")
            elif update.message:
                await update.message.reply_text("❌ خطایی رخ داد! لطفا دوباره تلاش کنید.")
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
    
    
    async def _handle_test_api_connection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تست اتصال API"""
        try:
            query = update.callback_query
            await query.answer("در حال تست اتصال...")
            
            # تست اتصال به API
            start_time = asyncio.get_event_loop().time()
            system_status = await self.download_system_handler.get_system_status()
            end_time = asyncio.get_event_loop().time()
            
            ping_time = int((end_time - start_time) * 1000)  # تبدیل به میلی‌ثانیه
            
            if system_status.get('ready', False):
                text = "✅ **تست اتصال موفقیت‌آمیز**\n\n"
                text += f"🌐 **سرور:** `{self.download_system_handler.api_url}`\n"
                text += f"⏱ **زمان پاسخ:** {ping_time} ms\n"
                text += f"📡 **وضعیت API:** آنلاین\n"
                text += f"📊 **نسخه سرور:** {system_status.get('version', 'نامشخص')}\n"
                text += f"💾 **حافظه آزاد:** {system_status.get('free_memory', 'نامشخص')}\n"
                text += f"🔄 **دانلودهای فعال:** {system_status.get('active_downloads', 0)}\n\n"
                
                if ping_time < 100:
                    text += "🚀 **سرعت اتصال:** عالی"
                elif ping_time < 300:
                    text += "⚡️ **سرعت اتصال:** خوب"
                elif ping_time < 500:
                    text += "🐌 **سرعت اتصال:** متوسط"
                else:
                    text += "🔴 **سرعت اتصال:** کند"
            else:
                text = "❌ **تست اتصال ناموفق**\n\n"
                text += f"🌐 **سرور:** `{self.download_system_handler.api_url}`\n"
                text += f"⏱ **زمان پاسخ:** {ping_time} ms (Timeout)\n"
                text += f"📡 **وضعیت API:** آفلاین\n"
                text += f"🔍 **خطا:** {system_status.get('error', 'نامشخص')}\n\n"
                text += "💡 **راهکارهای احتمالی:**\n"
                text += "• بررسی اتصال اینترنت\n"
                text += "• بررسی تنظیمات فایروال\n"
                text += "• بررسی وضعیت سرور دانلود\n"
                text += "• تماس با مدیر سیستم"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 تست مجدد", callback_data="test_api_connection"),
                    InlineKeyboardButton("📊 جزئیات بیشتر", callback_data="api_detailed_info")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="api_settings")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in test API connection: {e}")
            await self.download_system_handler._show_api_error_with_retry(
                query,
                "❌ خطا در تست اتصال", 
                str(e),
                "test_api_connection",
                "api_settings"
            )
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