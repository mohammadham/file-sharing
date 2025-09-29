#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main Bot File - Modular Telegram File Bot
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
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
from handlers.share_link_handler import ShareLinkHandler
from handlers.category_management_handler import CategoryManagementHandler
from handlers.link_management_handler import LinkManagementHandler
from handlers.general_utils_handler import GeneralUtilsHandler
from handlers.telethon_management_handler import TelethonManagementHandler

# Import actions
from actions.stats_action import StatsAction  
from actions.backup_action import BackupAction

# Import utilities
from utils.keyboard_builder import KeyboardBuilder
from utils.helpers import safe_json_dumps
from utils.advanced_logger import advanced_logger, LogLevel, LogCategory

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
        
        # Initialize new handlers
        self.share_link_handler = ShareLinkHandler(self.db)
        self.category_management_handler = CategoryManagementHandler(self.db)
        self.link_management_handler = LinkManagementHandler(self.db)
        self.general_utils_handler = GeneralUtilsHandler(self.db)
        self.telethon_management_handler = TelethonManagementHandler(self.db)
        
        # Initialize download system handler
        from handlers.download_system_handler import DownloadSystemHandler
        self.download_system_handler = DownloadSystemHandler(
            self.db,
            download_api_url="http://localhost:8001",
            admin_token="uVsXgmICyxa0mhPshBJZ1XtYpFFt-p5rLrdMvZnhv4c"
        )
        
        # Initialize token management handler
        from handlers.token_management_handler import TokenManagementHandler
        self.token_management_handler = TokenManagementHandler(
            self.db,
            download_api_url="http://localhost:8001",
            admin_token="uVsXgmICyxa0mhPshBJZ1XtYpFFt-p5rLrdMvZnhv4c"
        )
        
        # Initialize token management modules
        from handlers.token_dashboard import TokenDashboardHandler
        from handlers.token_security import TokenSecurityHandler
        from handlers.token_security_advanced import TokenSecurityAdvancedHandler
        from handlers.token_cleanup import TokenCleanupHandler
        from handlers.token_reports import TokenReportsHandler
        from handlers.token_users import TokenUsersHandler
        from handlers.token_callbacks import TokenCallbacks
        
        # Initialize new token handlers
        self.token_dashboard = TokenDashboardHandler(self.db, self.token_management_handler)
        self.token_security = TokenSecurityHandler(self.db, self.token_management_handler)
        self.token_security_advanced = TokenSecurityAdvancedHandler(self.db, self.token_management_handler)
        self.token_cleanup = TokenCleanupHandler(self.db, self.token_management_handler)
        self.token_reports = TokenReportsHandler(self.db, self.token_management_handler)
        self.token_users = TokenUsersHandler(self.db, self.token_management_handler)
        
        # Initialize token callbacks router
        token_handlers_dict = {
            'dashboard': self.token_dashboard,
            'security': self.token_security,
            'security_advanced': self.token_security_advanced,
            'cleanup': self.token_cleanup,
            'reports': self.token_reports,
            'users': self.token_users
        }
        self.token_callbacks = TokenCallbacks(self.db, token_handlers_dict)
        
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
            # Safely get user ID
            if not update.effective_user:
                logger.warning("Received start command without effective_user")
                return
            
            user_id = update.effective_user.id
            
            # Check if it's a share link
            if context.args and len(context.args) > 0:
                arg = context.args[0]
                if arg.startswith('link_'):
                    await self.share_link_handler.handle_share_link(update, context, arg[5:])  # Remove 'link_' prefix
                    return
                elif arg.startswith('file_'):
                    # Legacy file link support
                    await self.share_link_handler.legacy_file_link(update, context, arg[5:])  # Remove 'file_' prefix
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
            
            # Safely get user ID
            if not update.effective_user:
                logger.warning("Received callback query without effective_user")
                if update.callback_query:
                    await update.callback_query.answer("❌ خطای احراز هویت!")
                return
            
            user_id = update.effective_user.id
            
            # Advanced logging of user interactions
            advanced_logger.log_user_interaction(
                user_id=user_id,
                action=f"callback_query: {action}",
                details={'callback_data': callback_data}
            )
            
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
                await self.link_management_handler.link_stats(update, context)
            elif callback_data.startswith('deactivate_link_'):
                await self.link_management_handler.deactivate_link(update, context)
            elif callback_data == 'my_links':
                await self.link_management_handler.my_links(update, context)
            
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
                await self.share_link_handler.browse_shared_category(update, context)
            elif callback_data.startswith('browse_shared_collection_'):
                await self.share_link_handler.browse_shared_collection(update, context)
            elif callback_data.startswith('back_to_shared_'):
                await self.share_link_handler.back_to_shared(update, context)
            
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
            elif callback_data == 'speed_settings':
                await self.download_system_handler.handle_speed_settings(update, context)
            elif callback_data.startswith('set_speed_'):
                await self.download_system_handler.handle_set_speed(update, context)
            # Token Management - Use new callback router
            elif await self.token_callbacks.route_token_callback(update, context, callback_data):
                pass  # Token callback was handled by router
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
                await self.download_system_handler.handle_test_api_connection(update, context)
            elif callback_data == 'api_statistics':
                await self.download_system_handler.handle_api_statistics(update, context)
            elif callback_data == 'view_all_download_links' or callback_data.startswith('view_all_download_links_'):
                await self.download_system_handler.view_all_download_links(update, context)
            
            # API Settings Callbacks
            elif callback_data == 'advanced_api_settings':
                await self.download_system_handler.handle_advanced_api_settings(update, context)
            elif callback_data == 'api_logs':
                await self.download_system_handler.handle_api_logs(update, context)
            elif callback_data == 'diagnose_api_issue':
                await self.download_system_handler.handle_diagnose_api_issue(update, context)
            
            # Token Management Callbacks moved to router - legacy callbacks removed
            
            # Download Stats Callbacks
            elif callback_data == 'detailed_download_stats':
                await self.download_system_handler.handle_detailed_download_stats(update, context)
            elif callback_data == 'stats_chart':
                await self.download_system_handler.handle_stats_chart(update, context)
            elif callback_data == 'export_stats_pdf':
                await self.download_system_handler.handle_export_stats_pdf(update, context)
            
            # Additional API Settings Callbacks
            elif callback_data == 'set_api_timeout':
                await self.download_system_handler.handle_set_api_timeout(update, context)
            elif callback_data == 'set_api_retry':
                await self.download_system_handler.handle_set_api_retry(update, context)
            elif callback_data == 'set_buffer_size':
                await self.download_system_handler.handle_set_buffer_size(update, context)
            elif callback_data == 'set_log_level':
                await self.download_system_handler.handle_set_log_level(update, context)
            elif callback_data == 'download_api_logs':
                await self.download_system_handler.handle_download_api_logs(update, context)
            elif callback_data == 'clear_api_logs':
                await self.download_system_handler.handle_clear_api_logs(update, context)
            elif callback_data == 'search_api_logs':
                await self.download_system_handler.handle_search_api_logs(update, context)
            elif callback_data == 'auto_fix_api':
                await self.download_system_handler.handle_auto_fix_api(update, context)
            elif callback_data == 'contact_support':
                await self.download_system_handler.handle_contact_support(update, context)
            
            # Additional Token Management Callbacks moved to router - legacy callbacks removed
            
            # Additional Stats Callbacks
            elif callback_data == 'daily_chart':
                await self.download_system_handler.handle_daily_chart(update, context)
            elif callback_data == 'monthly_chart':
                await self.download_system_handler.handle_monthly_chart(update, context)
            elif callback_data == 'download_chart':
                await self.download_system_handler.handle_download_chart(update, context)
            elif callback_data == 'download_pdf_report':
                await self.download_system_handler.handle_download_pdf_report(update, context)
            elif callback_data == 'email_pdf_report':
                await self.download_system_handler.handle_email_pdf_report(update, context)
            elif callback_data == 'report_settings':
                await self.download_system_handler.handle_report_settings(update, context)
            
            # Telethon Management Operations
            elif callback_data == 'telethon_management_menu':
                await self.telethon_config_handler.show_telethon_management_menu(update, context)
            elif callback_data == 'telethon_view_logs':
                await self.telethon_management_handler.telethon_view_logs(update, context)
            elif callback_data == 'telethon_clear_logs':
                await self.telethon_management_handler.telethon_clear_logs(update, context)
            elif callback_data == 'telethon_export_logs':
                await self.telethon_management_handler.telethon_export_logs(update, context)
            elif callback_data == 'confirm_telethon_clear_logs':
                await self.telethon_management_handler.confirm_clear_logs(update, context)
            elif callback_data == 'telethon_timeout_settings':
                await self.telethon_management_handler.telethon_timeout_settings(update, context)
            elif callback_data == 'telethon_download_limits':
                await self.telethon_management_handler.telethon_download_limits(update, context)
            elif callback_data == 'telethon_proxy_settings':
                await self.telethon_management_handler.telethon_proxy_settings(update, context)
            elif callback_data == 'telethon_security_settings':
                await self.telethon_management_handler.telethon_security_settings(update, context)
            elif callback_data == 'telethon_performance_settings':
                await self.telethon_management_handler.telethon_performance_settings(update, context)
            elif callback_data == 'telethon_auto_config':
                await self.telethon_management_handler.telethon_auto_config(update, context)
            elif callback_data == 'telethon_list_configs':
                await self.telethon_config_handler.show_config_list(update, context)
            elif callback_data == 'telethon_add_config':
                await self.telethon_config_handler.show_add_config_menu(update, context)
            elif callback_data == 'telethon_show_json_example':
                await self.telethon_config_handler.show_json_example(update, context)
            elif callback_data == 'telethon_upload_json':
                await self.telethon_config_handler.start_json_upload(update, context)
            elif callback_data == 'telethon_manual_create':
                await self.telethon_config_handler.start_manual_creation(update, context)
            elif callback_data == 'telethon_skip_phone':
                await self.telethon_config_handler.handle_skip_phone(update, context)
            elif callback_data.startswith('telethon_confirm_delete_'):
                await self.telethon_management_handler.telethon_confirm_delete(update, context)
            elif callback_data.startswith('telethon_manage_config_'):
                await self.telethon_config_handler.manage_config(update, context)
            elif callback_data.startswith('telethon_delete_config_'):
                await self.telethon_config_handler.delete_config(update, context)
            
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
            elif callback_data == 'telethon_emergency_login':
                await self.telethon_management_handler.telethon_emergency_login(update, context)
            elif callback_data == 'telethon_fix_issues':
                await self.telethon_management_handler.telethon_fix_issues(update, context)
            elif callback_data == 'telethon_detailed_stats':
                await self.telethon_management_handler.telethon_detailed_stats(update, context)
            elif callback_data == 'telethon_auto_fix':
                await self.telethon_management_handler.telethon_auto_fix(update, context)
            elif callback_data == 'telethon_performance_test':
                await self.telethon_management_handler.telethon_performance_test(update, context)
            elif callback_data == 'telethon_advanced_settings':
                await self.telethon_management_handler.telethon_advanced_settings(update, context)
            elif callback_data.startswith('telethon_test_client_'):
                await self.telethon_management_handler.telethon_test_client(update, context)
            elif callback_data.startswith('telethon_reset_session_'):
                await self.telethon_management_handler.telethon_reset_session(update, context)
            elif callback_data.startswith('telethon_edit_config_'):
                await self.telethon_management_handler.telethon_edit_config(update, context)
            elif callback_data.startswith('telethon_view_config_'):
                await self.telethon_management_handler.telethon_view_config(update, context)
            
            # Handle download all operations
            elif callback_data.startswith('download_all_category_'):
                await self.share_link_handler.download_all_category(update, context)
            elif callback_data.startswith('download_all_collection_'):
                await self.share_link_handler.download_all_collection(update, context)
            elif callback_data.startswith('download_shared_file_'):
                await self.share_link_handler.download_shared_file(update, context)
            elif callback_data.startswith('download_shared_'):
                await self.share_link_handler.shared_file_download(update, context)
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
                await self.category_management_handler.icon_page(update, context)
            elif callback_data.startswith('set_cat_thumbnail_'):
                await self.category_edit_handler.show_thumbnail_options(update, context)
            elif callback_data.startswith('upload_thumbnail_'):
                await self.category_edit_handler.start_thumbnail_upload(update, context)
            elif callback_data.startswith('remove_thumbnail_'):
                await self.category_edit_handler.remove_thumbnail(update, context)
            elif callback_data.startswith('set_cat_tags_'):
                await self.category_edit_handler.set_category_tags(update, context)
            elif callback_data.startswith('move_category_'):
                await self.category_management_handler.move_category(update, context)
            elif callback_data.startswith('move_cat_nav_'):
                await self.category_management_handler.move_category_navigation(update, context)
            elif callback_data.startswith('move_cat_to_'):
                await self.category_management_handler.move_category_to(update, context)
            elif callback_data.startswith('cancel_move_cat_'):
                await self.category_management_handler.cancel_move_category(update, context)
            elif callback_data.startswith('details_shared_'):
                await self.share_link_handler.shared_file_details(update, context)
            elif callback_data.startswith('details_'):
                await self.file_handler.show_file_details(update, context)
            elif callback_data.startswith('copy_shared_'):
                await self.share_link_handler.shared_link_copy(update, context)
            elif callback_data.startswith('stats_shared_'):
                await self.share_link_handler.shared_link_stats(update, context)
            elif callback_data.startswith('back_shared_'):
                await self.share_link_handler.back_shared(update, context)
            elif callback_data.startswith('confirm_'):
                await self.general_utils_handler.handle_confirmations(update, context)
            
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
                await self.general_utils_handler.handle_cancel(update, context)
            
            # Page info callbacks
            elif callback_data in ['page_info', 'files_count_info']:
                await self.general_utils_handler.handle_page_info(update, context)
            elif callback_data == 'main_menu':
                await self.general_utils_handler.handle_main_menu(update, context)
            
            else:
                await self.general_utils_handler.handle_unknown_callback(update, context)
        
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            
            # Advanced error logging
            advanced_logger.log_system_error(
                error=e,
                context="callback_query_handler",
                user_id=update.effective_user.id if update.effective_user else None,
                additional_info={
                    'callback_data': getattr(update.callback_query, 'data', 'unknown'),
                    'action': action if 'action' in locals() else 'unknown'
                }
            )
            
            try:
                await update.callback_query.answer("❌ خطایی رخ داد!")
            except:
                pass
    
    
    
    
    
    
    
    async def _handle_back_shared(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle back from shared link"""
        try:
            await self.share_link_handler.back_to_shared(update, context)
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

    # === Telethon Advanced Logging Handlers ===
    
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