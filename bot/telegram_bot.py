#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import os
from pathlib import Path
import aiosqlite
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime

# Bot configuration
BOT_TOKEN = "8428725185:AAELFU6lUasbSDUvRuhTLNDBT3uEmvNruN0"
STORAGE_CHANNEL_ID = -1002546879743

# Database path
DB_PATH = Path(__file__).parent / "bot_database.db"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelegramFileBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.db_path = DB_PATH
        
    async def init_database(self):
        """Initialize SQLite database with necessary tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Categories table - hierarchical structure
            await db.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    parent_id INTEGER,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES categories (id)
                )
            ''')
            
            # Files table - file metadata
            await db.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT NOT NULL,
                    file_type TEXT,
                    file_size INTEGER,
                    category_id INTEGER,
                    telegram_file_id TEXT,
                    storage_message_id INTEGER,
                    uploaded_by INTEGER,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                )
            ''')
            
            # User sessions table - track user states
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    user_id INTEGER PRIMARY KEY,
                    current_category INTEGER,
                    action_state TEXT,
                    temp_data TEXT,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create default root categories if not exists
            categories_count = await db.execute('SELECT COUNT(*) FROM categories')
            count = await categories_count.fetchone()
            
            if count[0] == 0:
                await db.execute('''
                    INSERT INTO categories (name, parent_id, description) 
                    VALUES ('📁 فایل‌ها', NULL, 'دسته بندی اصلی فایل‌ها')
                ''')
                
                await db.execute('''
                    INSERT INTO categories (name, parent_id, description) 
                    VALUES ('🎵 موزیک', 1, 'فایل‌های صوتی و موزیک')
                ''')
                
                await db.execute('''
                    INSERT INTO categories (name, parent_id, description) 
                    VALUES ('🎬 ویدیو', 1, 'فایل‌های ویدیویی')
                ''')
                
                await db.execute('''
                    INSERT INTO categories (name, parent_id, description) 
                    VALUES ('📄 اسناد', 1, 'فایل‌های متنی و اسناد')
                ''')
            
            await db.commit()
            logger.info("Database initialized successfully")

    async def get_categories(self, parent_id: Optional[int] = None) -> List[Dict]:
        """Get categories by parent_id"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if parent_id is None:
                cursor = await db.execute('''
                    SELECT * FROM categories WHERE parent_id IS NULL ORDER BY name
                ''')
            else:
                cursor = await db.execute('''
                    SELECT * FROM categories WHERE parent_id = ? ORDER BY name
                ''', (parent_id,))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_category_by_id(self, category_id: int) -> Optional[Dict]:
        """Get category by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM categories WHERE id = ?
            ''', (category_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def create_category(self, name: str, parent_id: Optional[int] = None, description: str = "") -> int:
        """Create new category"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO categories (name, parent_id, description)
                VALUES (?, ?, ?)
            ''', (name, parent_id, description))
            await db.commit()
            return cursor.lastrowid

    async def get_user_session(self, user_id: int) -> Dict:
        """Get user session data"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM user_sessions WHERE user_id = ?
            ''', (user_id,))
            row = await cursor.fetchone()
            if row:
                return dict(row)
            else:
                # Create new session
                await db.execute('''
                    INSERT INTO user_sessions (user_id, current_category, action_state)
                    VALUES (?, ?, ?)
                ''', (user_id, 1, 'browsing'))
                await db.commit()
                return {
                    'user_id': user_id,
                    'current_category': 1, 
                    'action_state': 'browsing',
                    'temp_data': None
                }

    async def update_user_session(self, user_id: int, **kwargs):
        """Update user session"""
        async with aiosqlite.connect(self.db_path) as db:
            fields = []
            values = []
            for key, value in kwargs.items():
                if key in ['current_category', 'action_state', 'temp_data']:
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            if fields:
                values.append(user_id)
                await db.execute(f'''
                    UPDATE user_sessions 
                    SET {', '.join(fields)}, last_activity = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', values)
                await db.commit()

    async def build_category_keyboard(self, parent_id: Optional[int] = None, user_id: int = None) -> InlineKeyboardMarkup:
        """Build inline keyboard for categories"""
        categories = await self.get_categories(parent_id)
        keyboard = []
        
        # Categories buttons (2 per row)
        for i in range(0, len(categories), 2):
            row = []
            for j in range(2):
                if i + j < len(categories):
                    cat = categories[i + j]
                    row.append(InlineKeyboardButton(
                        f"{cat['name']}", 
                        callback_data=f"cat_{cat['id']}"
                    ))
            keyboard.append(row)
        
        # Add management buttons
        management_row = []
        if parent_id is not None and parent_id != 1:
            # Back button
            parent_cat = await self.get_category_by_id(parent_id)
            if parent_cat and parent_cat['parent_id']:
                management_row.append(InlineKeyboardButton("🔙 بازگشت", callback_data=f"cat_{parent_cat['parent_id']}"))
            else:
                management_row.append(InlineKeyboardButton("🔙 منوی اصلی", callback_data="cat_1"))
        
        # Add category button
        management_row.append(InlineKeyboardButton("➕ افزودن دسته", callback_data=f"add_cat_{parent_id or 1}"))
        
        if management_row:
            keyboard.append(management_row)
        
        # Files in this category
        files_row = [InlineKeyboardButton("📁 مشاهده فایل‌ها", callback_data=f"files_{parent_id or 1}")]
        keyboard.append(files_row)
        
        # Broadcast button
        broadcast_row = [
            InlineKeyboardButton("📢 برودکست", callback_data="broadcast_menu"),
            InlineKeyboardButton("🔍 جستجو", callback_data="search")
        ]
        keyboard.append(broadcast_row)
        
        # Stats button  
        stats_row = [InlineKeyboardButton("📊 آمار", callback_data="stats")]
        keyboard.append(stats_row)
        
        return InlineKeyboardMarkup(keyboard)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        session = await self.get_user_session(user_id)
        
        welcome_text = """
🤖 **سلام! به ربات مدیریت فایل خوش آمدید**

این ربات امکانات زیر را ارائه می‌دهد:
• 📁 **دسته‌بندی فایل‌ها** با ساختار درختی
• 📤 **آپلود و ذخیره فایل** در کانال
• 📢 **برودکست پیام** به کاربران
• 🔍 **جستجو در فایل‌ها**

برای شروع از منوی زیر استفاده کنید:
        """
        
        keyboard = await self.build_category_keyboard(1, user_id)
        await update.message.reply_text(welcome_text, reply_markup=keyboard, parse_mode='Markdown')

    async def category_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle category selection"""
        query = update.callback_query
        await query.answer()
        
        category_id = int(query.data.split('_')[1])
        user_id = update.effective_user.id
        
        await self.update_user_session(user_id, current_category=category_id)
        
        category = await self.get_category_by_id(category_id)
        if not category:
            await query.edit_message_text("دسته‌بندی یافت نشد!")
            return
            
        subcategories = await self.get_categories(category_id)
        
        text = f"📁 **{category['name']}**\n\n"
        if category['description']:
            text += f"📝 {category['description']}\n\n"
        
        if subcategories:
            text += f"📂 تعداد زیردسته‌ها: {len(subcategories)}"
        else:
            text += "📄 هیچ زیردسته‌ای وجود ندارد"
        
        keyboard = await self.build_category_keyboard(category_id, user_id)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def add_category_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle add category"""
        query = update.callback_query
        await query.answer()
        
        parent_id = int(query.data.split('_')[2])
        user_id = update.effective_user.id
        
        await self.update_user_session(
            user_id, 
            action_state='adding_category',
            temp_data=json.dumps({'parent_id': parent_id})
        )
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ لغو", callback_data=f"cat_{parent_id}")
        ]])
        
        await query.edit_message_text(
            "✏️ **افزودن دسته جدید**\n\nنام دسته جدید را وارد کنید:",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

    async def files_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle files view"""
        query = update.callback_query
        await query.answer()
        
        category_id = int(query.data.split('_')[1])
        
        # Get files in this category
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM files WHERE category_id = ? 
                ORDER BY uploaded_at DESC LIMIT 20
            ''', (category_id,))
            files = await cursor.fetchall()
        
        category = await self.get_category_by_id(category_id)
        
        text = f"📁 **فایل‌های {category['name']}**\n\n"
        
        if files:
            for file in files:
                size_mb = file['file_size'] / 1024 / 1024 if file['file_size'] else 0
                text += f"📄 **{file['file_name']}**\n"
                text += f"   💾 {size_mb:.1f} MB | {file['file_type']}\n"
                text += f"   📅 {file['uploaded_at'][:16]}\n\n"
        else:
            text += "هیچ فایلی در این دسته موجود نیست."
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 بازگشت", callback_data=f"cat_{category_id}")
        ]])
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def broadcast_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle broadcast menu"""
        query = update.callback_query
        await query.answer()
        
        text = "📢 **منوی برودکست**\n\nنوع برودکست را انتخاب کنید:"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 برودکست متنی", callback_data="broadcast_text")],
            [InlineKeyboardButton("📁 برودکست فایل", callback_data="broadcast_file")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="cat_1")]
        ])
        
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def broadcast_text_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text broadcast"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        await self.update_user_session(user_id, action_state='broadcast_text')
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ لغو", callback_data="broadcast_menu")
        ]])
        
        await query.edit_message_text(
            "✏️ **برودکست متنی**\n\nمتن پیام برای ارسال به همه کاربران را وارد کنید:",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

    async def stats_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot statistics"""
        query = update.callback_query
        await query.answer()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Get stats
            cursor = await db.execute('SELECT COUNT(*) FROM files')
            files_count = (await cursor.fetchone())[0]
            
            cursor = await db.execute('SELECT COUNT(*) FROM categories')
            categories_count = (await cursor.fetchone())[0]
            
            cursor = await db.execute('SELECT COUNT(*) FROM user_sessions')
            users_count = (await cursor.fetchone())[0]
            
            cursor = await db.execute('SELECT SUM(file_size) FROM files')
            total_size = (await cursor.fetchone())[0] or 0
            total_size_mb = total_size / 1024 / 1024
        
        text = f"""
📊 **آمار ربات**

👥 تعداد کاربران: {users_count}
📁 تعداد فایل‌ها: {files_count}
🗂 تعداد دسته‌ها: {categories_count}
💾 حجم کل فایل‌ها: {total_size_mb:.1f} MB

📈 ربات در حال کار عادی است!
        """
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 بازگشت", callback_data="cat_1")
        ]])
        
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def search_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle search"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        await self.update_user_session(user_id, action_state='searching')
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ لغو", callback_data="cat_1")
        ]])
        
        await query.edit_message_text(
            "🔍 **جستجو در فایل‌ها**\n\nنام فایل یا کلمه کلیدی را وارد کنید:",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages and files"""
        user_id = update.effective_user.id
        session = await self.get_user_session(user_id)
        
        # Handle adding category name
        if session['action_state'] == 'adding_category':
            temp_data = json.loads(session['temp_data'] or '{}')
            parent_id = temp_data.get('parent_id', 1)
            
            category_name = update.message.text
            if category_name and len(category_name.strip()) > 0:
                try:
                    new_cat_id = await self.create_category(
                        category_name.strip(), 
                        parent_id
                    )
                    
                    await self.update_user_session(
                        user_id,
                        action_state='browsing',
                        current_category=parent_id,
                        temp_data=None
                    )
                    
                    keyboard = await self.build_category_keyboard(parent_id, user_id)
                    await update.message.reply_text(
                        f"✅ دسته '{category_name}' با موفقیت اضافه شد!",
                        reply_markup=keyboard
                    )
                except Exception as e:
                    logger.error(f"Error creating category: {e}")
                    await update.message.reply_text("❌ خطا در ایجاد دسته! دوباره تلاش کنید.")
            else:
                await update.message.reply_text("❌ نام دسته نامعتبر است! دوباره تلاش کنید.")
            return
        
        # Handle broadcast text
        elif session['action_state'] == 'broadcast_text':
            broadcast_text = update.message.text
            if broadcast_text and len(broadcast_text.strip()) > 0:
                # Get all users
                async with aiosqlite.connect(self.db_path) as db:
                    cursor = await db.execute('SELECT user_id FROM user_sessions')
                    users = await cursor.fetchall()
                
                sent_count = 0
                for user in users:
                    try:
                        await context.bot.send_message(
                            chat_id=user[0],
                            text=f"📢 **پیام برودکست:**\n\n{broadcast_text}",
                            parse_mode='Markdown'
                        )
                        sent_count += 1
                    except Exception as e:
                        logger.error(f"Error sending broadcast to {user[0]}: {e}")
                
                await self.update_user_session(user_id, action_state='browsing')
                keyboard = await self.build_category_keyboard(1, user_id)
                await update.message.reply_text(
                    f"✅ پیام برودکست به {sent_count} کاربر ارسال شد!",
                    reply_markup=keyboard
                )
            else:
                await update.message.reply_text("❌ متن پیام نامعتبر است!")
            return
        
        # Handle search
        elif session['action_state'] == 'searching':
            search_query = update.message.text
            if search_query and len(search_query.strip()) > 0:
                # Search in files
                async with aiosqlite.connect(self.db_path) as db:
                    db.row_factory = aiosqlite.Row
                    cursor = await db.execute('''
                        SELECT f.*, c.name as category_name 
                        FROM files f 
                        JOIN categories c ON f.category_id = c.id
                        WHERE f.file_name LIKE ? OR f.description LIKE ?
                        ORDER BY f.uploaded_at DESC LIMIT 10
                    ''', (f'%{search_query}%', f'%{search_query}%'))
                    files = await cursor.fetchall()
                
                if files:
                    text = f"🔍 **نتایج جستجو برای '{search_query}':**\n\n"
                    for file in files:
                        size_mb = file['file_size'] / 1024 / 1024 if file['file_size'] else 0
                        text += f"📄 **{file['file_name']}**\n"
                        text += f"   📁 {file['category_name']}\n"
                        text += f"   💾 {size_mb:.1f} MB\n"
                        text += f"   📅 {file['uploaded_at'][:16]}\n\n"
                else:
                    text = f"❌ هیچ فایلی با کلمه '{search_query}' یافت نشد."
                
                await self.update_user_session(user_id, action_state='browsing')
                keyboard = await self.build_category_keyboard(1, user_id)
                await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ کلمه جستجو نامعتبر است!")
            return
        
        # Handle file uploads
        if update.message.document or update.message.photo or update.message.video or update.message.audio:
            await self.handle_file_upload(update, context, session)

    async def handle_file_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session):
        """Handle file upload"""
        try:
            file = None
            file_name = "Unknown"
            file_size = 0
            
            if update.message.document:
                file = update.message.document
                file_name = file.file_name or "Document"
                file_size = file.file_size
            elif update.message.photo:
                file = update.message.photo[-1]  # Get largest photo
                file_name = f"Photo_{file.file_id[:8]}.jpg"
                file_size = file.file_size
            elif update.message.video:
                file = update.message.video
                file_name = file.file_name or f"Video_{file.file_id[:8]}.mp4"
                file_size = file.file_size
            elif update.message.audio:
                file = update.message.audio
                file_name = file.file_name or f"Audio_{file.file_id[:8]}.mp3"
                file_size = file.file_size
            
            # Check file size (50MB limit)
            if file_size > 50 * 1024 * 1024:
                await update.message.reply_text("❌ حجم فایل بیش از 50 مگابایت است!")
                return
            
            # Forward to storage channel
            forwarded = await context.bot.forward_message(
                chat_id=STORAGE_CHANNEL_ID,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            
            # Save file metadata
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO files (
                        file_name, file_type, file_size, category_id,
                        telegram_file_id, storage_message_id, uploaded_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    file_name,
                    file.mime_type if hasattr(file, 'mime_type') else "Unknown",
                    file_size,
                    session['current_category'],
                    file.file_id,
                    forwarded.message_id,
                    update.effective_user.id
                ))
                await db.commit()
            
            category = await self.get_category_by_id(session['current_category'])
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("📁 مشاهده دسته", callback_data=f"cat_{session['current_category']}")
            ]])
            
            await update.message.reply_text(
                f"✅ فایل با موفقیت در دسته '{category['name']}' ذخیره شد!",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error handling file upload: {e}")
            await update.message.reply_text("❌ خطا در ذخیره فایل!")

    async def start_bot(self):
        """Start the Telegram bot"""
        await self.init_database()
        
        # Register handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CallbackQueryHandler(self.category_callback, pattern=r'^cat_\d+$'))
        self.application.add_handler(CallbackQueryHandler(self.add_category_callback, pattern=r'^add_cat_\d+$'))
        self.application.add_handler(CallbackQueryHandler(self.files_callback, pattern=r'^files_\d+$'))
        self.application.add_handler(CallbackQueryHandler(self.broadcast_callback, pattern=r'^broadcast_menu$'))
        self.application.add_handler(CallbackQueryHandler(self.broadcast_text_callback, pattern=r'^broadcast_text$'))
        self.application.add_handler(CallbackQueryHandler(self.search_callback, pattern=r'^search$'))
        self.application.add_handler(CallbackQueryHandler(self.stats_callback, pattern=r'^stats$'))
        self.application.add_handler(MessageHandler(filters.TEXT | filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO, self.handle_message))
        
        logger.info("✅ Telegram File Bot started successfully!")
        
        # Start the bot
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        # Keep running
        try:
            # Keep the application running
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        finally:
            await self.application.stop()
            await self.application.shutdown()


async def main():
    bot = TelegramFileBot()
    await bot.start_bot()


if __name__ == "__main__":
    asyncio.run(main())