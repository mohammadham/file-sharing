#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Stats Action - Handle statistics display
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from handlers.base_handler import BaseHandler
from utils.keyboard_builder import KeyboardBuilder
from utils.helpers import build_stats_text

logger = logging.getLogger(__name__)


class StatsAction(BaseHandler):
    """Handle statistics display"""
    
    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot statistics"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            # Get statistics
            stats = await self.db.get_stats()
            
            text = build_stats_text(stats)
            
            keyboard = KeyboardBuilder.build_cancel_keyboard("cat_1")
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def show_detailed_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show detailed statistics"""
        try:
            stats = await self.db.get_stats()
            
            # Get additional detailed stats
            import aiosqlite
            async with aiosqlite.connect(self.db.db_path) as db:
                # Files by category
                cursor = await db.execute('''
                    SELECT c.name, COUNT(f.id) as file_count, SUM(f.file_size) as total_size
                    FROM categories c
                    LEFT JOIN files f ON c.id = f.category_id
                    GROUP BY c.id, c.name
                    ORDER BY file_count DESC
                    LIMIT 10
                ''')
                category_stats = await cursor.fetchall()
                
                # Recent uploads
                cursor = await db.execute('''
                    SELECT COUNT(*) FROM files 
                    WHERE uploaded_at > datetime('now', '-7 days')
                ''')
                recent_uploads = (await cursor.fetchone())[0]
                
                # File types
                cursor = await db.execute('''
                    SELECT file_type, COUNT(*) as count
                    FROM files
                    GROUP BY file_type
                    ORDER BY count DESC
                    LIMIT 5
                ''')
                file_types = await cursor.fetchall()
            
            text = f"""
📊 **آمار تفصیلی ربات**
════════════════════════

📈 **آمار کلی**
👥 کاربران: {stats['users_count']}
📁 فایل‌ها: {stats['files_count']}
🗂 دسته‌ها: {stats['categories_count']}
💾 حجم کل: {stats['total_size_mb']:.1f} MB

📂 **فایل‌ها بر اساس دسته**
"""
            
            for cat_name, file_count, total_size in category_stats[:5]:
                size_mb = (total_size or 0) / 1024 / 1024
                text += f"• {cat_name}: {file_count} فایل ({size_mb:.1f} MB)\n"
            
            text += f"\n📅 **فعالیت اخیر**\n"
            text += f"• آپلود هفته گذشته: {recent_uploads} فایل\n"
            
            text += f"\n🏷 **انواع فایل محبوب**\n"
            for file_type, count in file_types:
                text += f"• {file_type}: {count} فایل\n"
            
            keyboard = KeyboardBuilder.build_cancel_keyboard("cat_1")
            
            await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error showing detailed stats: {e}")
            await update.message.reply_text("❌ خطا در نمایش آمار تفصیلی!")