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
            elif callback_data.startswith('edit_category_menu_'):
                await self.category_edit_handler.show_edit_menu(update, context)
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
            
            from utils.keyboard_builder import KeyboardBuilder
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
                text += f"{i}. {file.file_name} ({format_file_size(file.file_size)})\n"
            
            if len(files) > 5:
                text += f"... و {len(files) - 5} فایل دیگر"
            
            from utils.keyboard_builder import KeyboardBuilder
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
        """Handle browsing shared category files"""
        try:
            query = update.callback_query
            await query.answer()
            
            short_code = query.data.split('_')[3]
            link = await self.db.get_link_by_code(short_code)
            
            if not link or link.link_type != "category":
                await query.answer("❌ لینک نامعتبر!")
                return
            
            category = await self.db.get_category_by_id(link.target_id)
            files = await self.db.get_files(link.target_id, limit=20)
            
            if not files:
                await query.edit_message_text("❌ هیچ فایلی در این دسته موجود نیست!")
                return
            
            text = f"📂 **فایل‌های دسته '{category.name}'**\n\n"
            
            for i, file in enumerate(files, 1):
                from utils.helpers import format_file_size
                text += f"{i}. **{file.file_name}**\n"
                text += f"   💾 {format_file_size(file.file_size)} | {file.file_type}\n\n"
            
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_to_shared_{short_code}")]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error browsing shared category: {e}")
            await query.answer("❌ خطا در مشاهده فایل‌ها!")
            
    async def _handle_browse_shared_collection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle browsing shared collection files"""
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
            
            for i, file in enumerate(files, 1):
                from utils.helpers import format_file_size
                text += f"{i}. **{file.file_name}**\n"
                text += f"   💾 {format_file_size(file.file_size)} | {file.file_type}\n\n"
            
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_to_shared_{short_code}")]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error browsing shared collection: {e}")
            await query.answer("❌ خطا در مشاهده فایل‌ها!")
    
    async def _handle_back_to_shared(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle back to shared link main view"""
        try:
            query = update.callback_query
            await query.answer()
            
            short_code = query.data.split('_')[3]
            
            # Re-handle the original share link
            await self._handle_share_link(update, context, short_code)
            
        except Exception as e:
            logger.error(f"Error in back to shared: {e}")
            await query.answer("❌ خطا در بازگشت!")
    
    async def _handle_icon_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle icon page navigation"""
        try:
            query = update.callback_query
            await query.answer()
            
            parts = query.data.split('_')
            category_id = int(parts[2])
            page = int(parts[3])
            
            category = await self.db.get_category_by_id(category_id)
            if not category:
                await query.edit_message_text("دسته‌بندی یافت نشد!")
                return
            
            text = f"🎨 **انتخاب آیکون برای '{category.name}'**\n\n"
            text += f"🔄 آیکون فعلی: {category.icon}\n\n"
            text += f"💡 آیکون مورد نظر را انتخاب کنید:"
            
            from utils.keyboard_builder import KeyboardBuilder
            keyboard = KeyboardBuilder.build_icon_selection_keyboard(category_id, page)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in icon page navigation: {e}")
            await query.answer("❌ خطا در تغییر صفحه!")
    
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
    
    async def _handle_link_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle link statistics view"""
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
            text += f"📊 **بازدیدها:** {stats['access_count']} بار\n"
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