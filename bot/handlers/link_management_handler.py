#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Link Management Handler - File link operations and statistics
"""

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from handlers.base_handler import BaseHandler
from utils.keyboard_builder import KeyboardBuilder
from utils.helpers import format_file_size, escape_filename_for_markdown

logger = logging.getLogger(__name__)


class LinkManagementHandler(BaseHandler):
    """Handle file link operations and statistics"""
    def __init__(self, db):
        super().__init__(db)
    async def link_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    # async def link_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Show link statistics"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         # Extract link code from callback data
    #         parts = query.data.split('_')
    #         if len(parts) < 3:
    #             await query.answer("❌ داده نامعتبر!")
    #             return
            
    #         link_code = parts[2]
            
    #         # Get link from database
    #         link = await self.db.get_link_by_code(link_code)
    #         if not link:
    #             await query.edit_message_text("❌ لینک یافت نشد!")
    #             return
            
    #         # Build statistics text
    #         text = f"📊 **آمار لینک اشتراک‌گذاری**\n\n"
    #         text += f"🔗 **کد لینک:** `{link_code}`\n"
    #         text += f"📈 **تعداد بازدید:** {link.access_count}\n"
    #         text += f"🏷 **نوع لینک:** {link.link_type}\n"
            
    #         if link.title:
    #             text += f"📝 **عنوان:** {link.title}\n"
            
    #         if link.description:
    #             text += f"📄 **توضیحات:** {link.description}\n"
            
    #         if hasattr(link, 'created_at') and link.created_at:
    #             text += f"📅 **تاریخ ایجاد:** {link.created_at}\n"
            
    #         # Additional stats based on link type
    #         if link.link_type == "file":
    #             file = await self.db.get_file_by_id(link.target_id)
    #             if file:
    #                 text += f"\n📄 **جزئیات فایل:**\n"
    #                 text += f"• نام: {escape_filename_for_markdown(file.file_name)}\n"
    #                 text += f"• حجم: {format_file_size(file.file_size)}\n"
    #                 text += f"• نوع: {file.file_type}\n"
            
    #         elif link.link_type == "category":
    #             category = await self.db.get_category_by_id(link.target_id)
    #             if category:
    #                 files = await self.db.get_files(link.target_id, limit=1000)
    #                 total_size = sum(f.file_size for f in files)
                    
    #                 text += f"\n📂 **جزئیات دسته:**\n"
    #                 text += f"• نام: {category.name}\n"
    #                 text += f"• تعداد فایل: {len(files)}\n"
    #                 text += f"• حجم کل: {format_file_size(total_size)}\n"
            
    #         elif link.link_type == "collection":
    #             import json
    #             try:
    #                 file_ids = json.loads(link.target_ids)
    #                 files = []
    #                 total_size = 0
    #                 for file_id in file_ids:
    #                     file = await self.db.get_file_by_id(file_id)
    #                     if file:
    #                         files.append(file)
    #                         total_size += file.file_size
                    
    #                 text += f"\n📦 **جزئیات مجموعه:**\n"
    #                 text += f"• تعداد فایل: {len(files)}\n"
    #                 text += f"• حجم کل: {format_file_size(total_size)}\n"
    #             except:
    #                 text += f"\n📦 **مجموعه فایل‌ها**\n"
            
    #         # Build keyboard
    #         keyboard_buttons = [
    #             [
    #                 InlineKeyboardButton("📋 کپی لینک", callback_data=f"copy_link_{link_code}"),
    #                 InlineKeyboardButton("🔄 بروزرسانی", callback_data=f"link_stats_{link_code}")
    #             ]
    #         ]
            
    #         # Add deactivate button if link is active
    #         if hasattr(link, 'is_active') and link.is_active:
    #             keyboard_buttons.append([
    #                 InlineKeyboardButton("🔒 غیرفعال‌سازی", callback_data=f"deactivate_link_{link_code}")
    #             ])
            
    #         keyboard_buttons.append([
    #             InlineKeyboardButton("🔙 بازگشت", callback_data="my_links")
    #         ])
            
    #         keyboard = InlineKeyboardMarkup(keyboard_buttons)
            
    #         await query.edit_message_text(
    #             text, 
    #             reply_markup=keyboard, 
    #             parse_mode='Markdown'
    #         )
            
    #     except Exception as e:
    #         logger.error(f"Error in link stats: {e}")
    #         await self.handle_error(update, context, e)
    async def deactivate_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    
    # async def deactivate_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Deactivate a link"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         # Extract link code from callback data
    #         parts = query.data.split('_')
    #         if len(parts) < 3:
    #             await query.answer("❌ داده نامعتبر!")
    #             return
            
    #         link_code = parts[2]
            
    #         # Get link from database
    #         link = await self.db.get_link_by_code(link_code)
    #         if not link:
    #             await query.edit_message_text("❌ لینک یافت نشد!")
    #             return
            
    #         # Show confirmation
    #         text = f"🔒 **غیرفعال‌سازی لینک**\n\n"
    #         text += f"🔗 **کد لینک:** `{link_code}`\n"
    #         text += f"🏷 **نوع:** {link.link_type}\n"
            
    #         if link.title:
    #             text += f"📝 **عنوان:** {link.title}\n"
            
    #         text += f"📈 **بازدیدها:** {link.access_count}\n\n"
    #         text += "⚠️ **توجه:** پس از غیرفعال‌سازی، لینک قابل استفاده نخواهد بود.\n\n"
    #         text += "آیا مطمئن هستید؟"
            
    #         keyboard = InlineKeyboardMarkup([
    #             [
    #                 InlineKeyboardButton("✅ بله، غیرفعال کن", callback_data=f"confirm_deactivate_{link_code}"),
    #                 InlineKeyboardButton("❌ لغو", callback_data=f"link_stats_{link_code}")
    #             ]
    #         ])
            
    #         await query.edit_message_text(
    #             text, 
    #             reply_markup=keyboard, 
    #             parse_mode='Markdown'
    #         )
            
    #     except Exception as e:
    #         logger.error(f"Error in deactivate link: {e}")
    #         await self.handle_error(update, context, e)
    async def my_links(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    # async def my_links(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Show user's links"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         user_id = update.effective_user.id
            
    #         # Get user's links from database
    #         user_links = await self.db.get_user_links(user_id, limit=20)
            
    #         text = f"🔗 **لینک‌های من**\n\n"
            
    #         if user_links:
    #             text += f"📊 **تعداد کل:** {len(user_links)} لینک\n\n"
                
    #             for i, link in enumerate(user_links, 1):
    #                 status_icon = "🟢" if getattr(link, 'is_active', True) else "🔴"
    #                 type_icons = {
    #                     'file': '📄',
    #                     'category': '📁',
    #                     'collection': '📦'
    #                 }
    #                 type_icon = type_icons.get(link.link_type, '🔗')
                    
    #                 text += f"{i}. {type_icon} **{link.title or 'بدون عنوان'}** {status_icon}\n"
    #                 text += f"   📈 بازدید: {link.access_count}\n"
    #                 text += f"   🔗 کد: `{link.short_code}`\n"
                    
    #                 if hasattr(link, 'created_at') and link.created_at:
    #                     created_date = str(link.created_at)[:10] if isinstance(link.created_at, str) else link.created_at.strftime("%Y-%m-%d")
    #                     text += f"   📅 ایجاد: {created_date}\n"
                    
    #                 text += "\n"
                
    #             # Build keyboard with quick actions
    #             keyboard_buttons = []
                
    #             # Add buttons for first few links
    #             for link in user_links[:5]:
    #                 keyboard_buttons.append([
    #                     InlineKeyboardButton(
    #                         f"📊 {(link.title or 'بدون عنوان')[:15]}...", 
    #                         callback_data=f"link_stats_{link.short_code}"
    #                     )
    #                 ])
                
    #             if len(user_links) > 5:
    #                 text += f"... و {len(user_links) - 5} لینک دیگر\n"
    #                 text += "برای مشاهده همه لینک‌ها از دکمه‌های زیر استفاده کنید."
                    
    #                 keyboard_buttons.append([
    #                     InlineKeyboardButton("📋 مشاهده همه", callback_data="view_all_my_links")
    #                 ])
                
    #         else:
    #             text += "❌ **هیچ لینکی یافت نشد**\n\n"
    #             text += "شما هنوز هیچ لینک اشتراک‌گذاری ایجاد نکرده‌اید.\n"
    #             text += "برای ایجاد لینک، به دسته یا فایل مورد نظر بروید."
                
    #             keyboard_buttons = []
            
    #         # Add general action buttons
    #         keyboard_buttons.extend([
    #             [
    #                 InlineKeyboardButton("🔄 بروزرسانی", callback_data="my_links"),
    #                 InlineKeyboardButton("📊 آمار کلی", callback_data="my_links_stats")
    #             ],
    #             [
    #                 InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")
    #             ]
    #         ])
            
    #         keyboard = InlineKeyboardMarkup(keyboard_buttons)
            
    #         await query.edit_message_text(
    #             text, 
    #             reply_markup=keyboard, 
    #             parse_mode='Markdown'
    #         )
            
    #     except Exception as e:
    #         logger.error(f"Error in my links: {e}")
    #         await self.handle_error(update, context, e)
    
    async def confirm_deactivate_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm link deactivation"""
        try:
            query = update.callback_query
            await query.answer("در حال غیرفعال‌سازی...")
            
            # Extract link code from callback data
            link_code = query.data.split('_')[-1]
            
            # Deactivate link in database
            success = await self.db.deactivate_link(link_code)
            
            if success:
                text = f"✅ **لینک غیرفعال شد**\n\n"
                text += f"🔗 **کد لینک:** `{link_code}`\n"
                text += f"🔒 **وضعیت:** غیرفعال\n\n"
                text += "لینک با موفقیت غیرفعال شد و دیگر قابل استفاده نیست."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📋 لینک‌های من", callback_data="my_links"),
                        InlineKeyboardButton("🔄 فعال‌سازی مجدد", callback_data=f"reactivate_link_{link_code}")
                    ],
                    [
                        InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")
                    ]
                ])
            else:
                text = f"❌ **خطا در غیرفعال‌سازی**\n\n"
                text += f"🔗 **کد لینک:** `{link_code}`\n"
                text += "متأسفانه امکان غیرفعال‌سازی لینک وجود ندارد.\n"
                text += "لطفاً دوباره تلاش کنید."
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 تلاش مجدد", callback_data=f"deactivate_link_{link_code}"),
                        InlineKeyboardButton("📊 آمار لینک", callback_data=f"link_stats_{link_code}")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="my_links")
                    ]
                ])
            
            await query.edit_message_text(
                text, 
                reply_markup=keyboard, 
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error confirming deactivate link: {e}")
            await self.handle_error(update, context, e)
    
    async def copy_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Copy link to clipboard"""
        try:
            query = update.callback_query
            await query.answer()
            
            # Extract link code from callback data
            parts = query.data.split('_')
            if len(parts) < 3:
                await query.answer("❌ داده نامعتبر!")
                return
            
            link_code = parts[2]
            
            # Get bot username for URL
            bot_info = await context.bot.get_me()
            share_url = f"https://t.me/{bot_info.username}?start=link_{link_code}"
            
            # Send copyable message
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"📋 **لینک کپی شده:**\n`{share_url}`\n\n🔗 **کد کوتاه:**\n`{link_code}`",
                parse_mode='Markdown',
                reply_to_message_id=query.message.message_id
            )
            
            await query.answer("✅ لینک کپی شد!")
            
        except Exception as e:
            logger.error(f"Error copying link: {e}")
            await query.answer("❌ خطا در کپی لینک!")
    
    async def view_all_my_links(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View all user links with pagination"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = update.effective_user.id
            
            # Get all user's links
            user_links = await self.db.get_user_links(user_id, limit=50)
            
            text = f"📋 **تمام لینک‌های من**\n\n"
            text += f"📊 **تعداد کل:** {len(user_links)} لینک\n\n"
            
            if user_links:
                # Group by type
                file_links = [l for l in user_links if l.link_type == 'file']
                category_links = [l for l in user_links if l.link_type == 'category']
                collection_links = [l for l in user_links if l.link_type == 'collection']
                
                if file_links:
                    text += f"📄 **لینک‌های فایل ({len(file_links)}):**\n"
                    for link in file_links[:10]:  # Show first 10
                        status = "🟢" if getattr(link, 'is_active', True) else "🔴"
                        text += f"• {link.title or 'بدون عنوان'} {status} ({link.access_count} بازدید)\n"
                    if len(file_links) > 10:
                        text += f"   ... و {len(file_links) - 10} لینک دیگر\n"
                    text += "\n"
                
                if category_links:
                    text += f"📁 **لینک‌های دسته ({len(category_links)}):**\n"
                    for link in category_links[:10]:
                        status = "🟢" if getattr(link, 'is_active', True) else "🔴"
                        text += f"• {link.title or 'بدون عنوان'} {status} ({link.access_count} بازدید)\n"
                    if len(category_links) > 10:
                        text += f"   ... و {len(category_links) - 10} لینک دیگر\n"
                    text += "\n"
                
                if collection_links:
                    text += f"📦 **لینک‌های مجموعه ({len(collection_links)}):**\n"
                    for link in collection_links[:10]:
                        status = "🟢" if getattr(link, 'is_active', True) else "🔴"
                        text += f"• {link.title or 'بدون عنوان'} {status} ({link.access_count} بازدید)\n"
                    if len(collection_links) > 10:
                        text += f"   ... و {len(collection_links) - 10} لینک دیگر\n"
                    text += "\n"
                
                # Calculate total stats
                total_views = sum(link.access_count for link in user_links)
                active_links = len([l for l in user_links if getattr(l, 'is_active', True)])
                
                text += f"📊 **آمار کلی:**\n"
                text += f"• کل بازدیدها: {total_views:,}\n"
                text += f"• لینک‌های فعال: {active_links}/{len(user_links)}\n"
                text += f"• میانگین بازدید: {total_views/len(user_links):.1f}"
                
            else:
                text += "❌ هیچ لینکی یافت نشد!"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📊 آمار تفصیلی", callback_data="my_links_detailed_stats"),
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data="view_all_my_links")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="my_links")
                ]
            ])
            
            await query.edit_message_text(
                text, 
                reply_markup=keyboard, 
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in view all my links: {e}")
            await self.handle_error(update, context, e)