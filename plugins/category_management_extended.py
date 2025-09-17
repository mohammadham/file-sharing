"""
Extended Category Management Functions
Additional functions for editing, deleting, searching and uploading
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import os
import uuid
import asyncio
import json
import sys
import pathlib
PARENT_PATH = pathlib.Path(__file__).parent.resolve()
if PARENT_PATH not in ["",None] :
    sys.path.append(PARENT_PATH)
    from config import TEMP_PATH, CHANNEL_ID, ADMINS, APP_PATH, TG_CONFIG_FILE
    from telegram_uploader_integration import TelegramUploader
else:
    from ..telegram_uploader_integration import TelegramUploader
    #DATABASE_PATH = os.getenv("DATABASE_PATH", "/app/data/file_sharing_bot.db")
    TG_CONFIG_FILE = os.getenv("TG_CONFIG_FILE", None)
    TEMP_PATH = os.getenv("TEMP_PATH", "/app/temp")
    CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1002075726565"))
    ADMINS = [6695586027]  # Default admin
    APP_PATH = os.getenv("APP_PATH", "/app")
from bot import Bot
from database.database import (
    create_category, get_category, get_categories, update_category, delete_category,
    get_files_by_category, search_files, add_file, create_file_link, get_file
)
# Initialize uploader
uploader = TelegramUploader() if TG_CONFIG_FILE else None

@Bot.on_callback_query(filters.regex(r"^cat_edit_"))
async def handle_category_edit(client: Client, callback_query: CallbackQuery):
    """Handle category editing"""
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("شما مجوز دسترسی ندارید.", show_alert=True)
        return
    
    category_id = callback_query.data.split("_", 2)[2]
    await start_category_editing(client, callback_query, category_id)

@Bot.on_callback_query(filters.regex(r"^cat_delete_"))
async def handle_category_delete(client: Client, callback_query: CallbackQuery):
    """Handle category deletion"""
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("شما مجوز دسترسی ندارید.", show_alert=True)
        return
    
    category_id = callback_query.data.split("_", 2)[2]
    await confirm_category_deletion(client, callback_query, category_id)

@Bot.on_callback_query(filters.regex(r"^cat_search_"))
async def handle_category_search(client: Client, callback_query: CallbackQuery):
    """Handle category search"""
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("شما مجوز دسترسی ندارید.", show_alert=True)
        return
    
    category_id = callback_query.data.split("_", 2)[2]
    if category_id == "root":
        category_id = None
    await start_category_search(client, callback_query, category_id)

@Bot.on_callback_query(filters.regex(r"^cat_upload_"))
async def handle_category_upload(client: Client, callback_query: CallbackQuery):
    """Handle file upload to category"""
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("شما مجوز دسترسی ندارید.", show_alert=True)
        return
    
    category_id = callback_query.data.split("_", 2)[2]
    if category_id == "root":
        category_id = None
    await start_file_upload(client, callback_query, category_id)

@Bot.on_callback_query(filters.regex(r"^confirm_delete_"))
async def handle_confirmed_deletion(client: Client, callback_query: CallbackQuery):
    """Handle confirmed category deletion"""
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("شما مجوز دسترسی ندارید.", show_alert=True)
        return
    
    category_id = callback_query.data.split("_", 2)[2]
    user_id = callback_query.from_user.id
    
    try:
        category = await get_category(category_id)
        parent_id = category['parent_id'] if category else None
        
        await delete_category(category_id)
        
        await callback_query.answer("✅ دسته‌بندی حذف شد.", show_alert=True)
        
        # Import the function from the main plugin
        from .category_management import show_categories_menu
        await show_categories_menu(client, user_id, parent_id, callback_query.message.id, True)
        
    except Exception as e:
        await callback_query.answer(f"خطا: {str(e)}", show_alert=True)

async def start_category_editing(client: Client, callback_query: CallbackQuery, category_id: str):
    """Start category editing process"""
    await callback_query.answer()
    user_id = callback_query.from_user.id
    
    category = await get_category(category_id)
    if not category:
        await callback_query.answer("دسته‌بندی یافت نشد!", show_alert=True)
        return
    
    try:
        # Ask for new name
        name_msg = await client.ask(
            chat_id=user_id,
            text=f"📝 نام جدید برای دسته‌بندی '{category['name']}' (یا /skip برای عدم تغییر):",
            timeout=60
        )
        
        new_name = None if name_msg.text == "/skip" else name_msg.text.strip()
        
        # Ask for new description
        desc_msg = await client.ask(
            chat_id=user_id,
            text=f"📄 توضیحات جدید (فعلی: {category['description']}) (یا /skip برای عدم تغییر):",
            timeout=60
        )
        
        new_description = None if desc_msg.text == "/skip" else desc_msg.text.strip()
        
        # Update category
        await update_category(
            category_id=category_id,
            name=new_name,
            description=new_description
        )
        
        await client.send_message(
            chat_id=user_id,
            text="✅ دسته‌بندی با موفقیت بروزرسانی شد!"
        )
        
        # Show updated categories
        from .category_management import show_categories_menu
        await show_categories_menu(client, user_id, category['parent_id'], callback_query.message.id, True)
        
    except asyncio.TimeoutError:
        await client.send_message(user_id, "⏰ زمان شما تمام شد.")
    except Exception as e:
        await client.send_message(user_id, f"❌ خطا در بروزرسانی دسته‌بندی: {str(e)}")

async def confirm_category_deletion(client: Client, callback_query: CallbackQuery, category_id: str):
    """Confirm category deletion"""
    category = await get_category(category_id)
    if not category:
        await callback_query.answer("دسته‌بندی یافت نشد!", show_alert=True)
        return
    
    # Count files and subcategories
    files = await get_files_by_category(category_id)
    subcategories = await get_categories(category_id)
    
    text = f"⚠️ آیا مطمئن هستید که می‌خواهید دسته‌بندی '{category['name']}' را حذف کنید؟\n\n"
    text += f"📁 زیردسته‌ها: {len(subcategories)}\n"
    text += f"📄 فایل‌ها: {len(files)}\n\n"
    text += "⚠️ تمام زیردسته‌ها و فایل‌ها به دسته‌بندی والد منتقل می‌شوند."
    
    keyboard = [
        [
            InlineKeyboardButton("✅ بله، حذف کن", callback_data=f"confirm_delete_{category_id}"),
            InlineKeyboardButton("❌ انصراف", callback_data=f"cat_view_{category_id}")
        ]
    ]
    
    await client.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    await callback_query.answer()

async def start_category_search(client: Client, callback_query: CallbackQuery, category_id: str = None):
    """Start search in category"""
    await callback_query.answer()
    user_id = callback_query.from_user.id
    
    try:
        search_msg = await client.ask(
            chat_id=user_id,
            text="🔍 عبارت جستجو را وارد کنید:",
            timeout=60
        )
        
        query = search_msg.text.strip()
        results = await search_files(query, category_id)
        
        if not results:
            await client.send_message(user_id, "❌ هیچ فایلی یافت نشد.")
            return
        
        # Import function from main plugin
        from .category_management import get_file_emoji
        
        text = f"🔍 نتایج جستجو برای '{query}':\n\n"
        keyboard = []
        
        for i, file in enumerate(results[:20]):  # Show max 20 results
            file_emoji = get_file_emoji(file['mime_type'])
            text += f"{i+1}. {file_emoji} {file['original_name']}\n"
            keyboard.append([
                InlineKeyboardButton(
                    f"{file_emoji} {file['original_name'][:30]}{'...' if len(file['original_name']) > 30 else ''}",
                    callback_data=f"file_info_{file['id']}"
                )
            ])
        
        if len(results) > 20:
            text += f"\n... و {len(results) - 20} نتیجه دیگر"
        
        keyboard.append([
            InlineKeyboardButton("🔙 برگشت", callback_data=f"cat_view_{category_id}" if category_id else "cat_back_root")
        ])
        
        await client.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except asyncio.TimeoutError:
        await client.send_message(user_id, "⏰ زمان شما تمام شد.")
    except Exception as e:
        await client.send_message(user_id, f"❌ خطا در جستجو: {str(e)}")

async def start_file_upload(client: Client, callback_query: CallbackQuery, category_id: str = None):
    """Start file upload process"""
    await callback_query.answer()
    user_id = callback_query.from_user.id
    
    try:
        upload_msg = await client.ask(
            chat_id=user_id,
            text="📤 فایل مورد نظر را ارسال کنید یا لینک دانلود را وارد کنید:",
            timeout=300  # 5 minutes for file upload
        )
        
        if upload_msg.document or upload_msg.photo or upload_msg.video or upload_msg.audio:
            # Handle direct file upload
            await handle_direct_file_upload(client, upload_msg, category_id, user_id)
        elif upload_msg.text and (upload_msg.text.startswith("http://") or upload_msg.text.startswith("https://")):
            # Handle URL upload
            await handle_url_upload(client, upload_msg.text, category_id, user_id)
        else:
            await client.send_message(user_id, "❌ لطفاً یک فایل معتبر یا لینک صحیح ارسال کنید.")
            
    except asyncio.TimeoutError:
        await client.send_message(user_id, "⏰ زمان شما تمام شد.")
    except Exception as e:
        await client.send_message(user_id, f"❌ خطا در آپلود: {str(e)}")

async def handle_direct_file_upload(client: Client, message: Message, category_id: str, user_id: int):
    """Handle direct file upload to category"""
    try:
        # Get file info
        if message.document:
            file_info = message.document
            file_name = file_info.file_name or f"file_{message.id}"
            mime_type = file_info.mime_type
            file_size = file_info.file_size
        elif message.photo:
            file_info = message.photo
            file_name = f"photo_{message.id}.jpg"
            mime_type = "image/jpeg"
            file_size = file_info.file_size
        elif message.video:
            file_info = message.video
            file_name = file_info.file_name or f"video_{message.id}.mp4"
            mime_type = file_info.mime_type
            file_size = file_info.file_size
        elif message.audio:
            file_info = message.audio
            file_name = file_info.file_name or f"audio_{message.id}.mp3"
            mime_type = file_info.mime_type
            file_size = file_info.file_size
        
        # Forward message to database channel
        forwarded = await message.forward(client.db_channel.id)
        
        # Add file to database
        file_id = await add_file(
            original_name=file_name,
            file_name=file_name,
            message_id=forwarded.id,
            chat_id=str(client.db_channel.id),
            file_size=file_size,
            mime_type=mime_type or "",
            category_id=category_id,
            uploaded_by=user_id
        )
        
        await client.send_message(
            chat_id=user_id,
            text=f"✅ فایل '{file_name}' با موفقیت آپلود شد!"
        )
        
    except Exception as e:
        await client.send_message(user_id, f"❌ خطا در آپلود فایل: {str(e)}")

async def handle_url_upload(client: Client, url: str, category_id: str, user_id: int):
    """Handle URL upload using TelegramUploader"""
    if not uploader:
        await client.send_message(user_id, "❌ سیستم آپلود از لینک در دسترس نیست.")
        return
    
    try:
        status_msg = await client.send_message(user_id, "⏳ در حال دانلود و آپلود فایل...")
        
        # Upload URL to Telegram
        result = uploader.upload_url_to_telegram(
            url=url,
            to=str(client.db_channel.id),
            caption=f"Uploaded from URL by user {user_id}"
        )
        
        result_data = json.loads(result)
        
        if result_data['success']:
            # Add file to database
            file_id = await add_file(
                original_name=result_data['file_name'],
                file_name=result_data['file_name'],
                message_id=result_data['telegram_message_id'],
                chat_id=result_data['telegram_chat'],
                file_size=result_data['size_bytes'],
                mime_type="",
                category_id=category_id,
                uploaded_by=user_id
            )
            
            await status_msg.edit_text(f"✅ فایل '{result_data['file_name']}' با موفقیت از لینک آپلود شد!")
        else:
            await status_msg.edit_text(f"❌ خطا در آپلود: {result_data.get('error', 'نامشخص')}")
            
    except Exception as e:
        await client.send_message(user_id, f"❌ خطا در آپلود از لینک: {str(e)}")

# Command for bulk URL upload
@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('bulk_upload'))
async def bulk_url_upload(client: Client, message: Message):
    """Handle bulk URL upload"""
    try:
        # Show categories for selection
        categories = await get_categories()
        
        if not categories:
            await message.reply("❌ هیچ دسته‌بندی وجود ندارد. ابتدا دسته‌بندی ایجاد کنید.")
            return
        
        keyboard = []
        for category in categories:
            keyboard.append([
                InlineKeyboardButton(
                    f"📁 {category['name']}",
                    callback_data=f"bulk_cat_{category['id']}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("📁 بدون دسته‌بندی", callback_data="bulk_cat_none")
        ])
        
        await message.reply(
            "📤 **آپلود گروهی از لینک‌ها**\n\nدسته‌بندی مورد نظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        await message.reply(f"❌ خطا: {str(e)}")

@Bot.on_callback_query(filters.regex(r"^bulk_cat_"))
async def handle_bulk_category_selection(client: Client, callback_query: CallbackQuery):
    """Handle bulk upload category selection"""
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("شما مجوز دسترسی ندارید.", show_alert=True)
        return
    
    category_id = callback_query.data.split("_", 2)[2]
    if category_id == "none":
        category_id = None
    
    await callback_query.answer()
    user_id = callback_query.from_user.id
    
    try:
        urls_msg = await client.ask(
            chat_id=user_id,
            text="📋 لینک‌های دانلود را هر کدام در یک خط وارد کنید:",
            timeout=300
        )
        
        urls = [url.strip() for url in urls_msg.text.split('\n') if url.strip().startswith(('http://', 'https://'))]
        
        if not urls:
            await client.send_message(user_id, "❌ هیچ لینک معتبری یافت نشد.")
            return
        
        status_msg = await client.send_message(
            user_id, 
            f"⏳ شروع آپلود {len(urls)} فایل..."
        )
        
        success_count = 0
        failed_count = 0
        
        for i, url in enumerate(urls):
            try:
                await status_msg.edit_text(
                    f"⏳ آپلود فایل {i+1} از {len(urls)}...\n"
                    f"✅ موفق: {success_count}\n"
                    f"❌ ناموفق: {failed_count}"
                )
                
                result = uploader.upload_url_to_telegram(
                    url=url,
                    to=str(client.db_channel.id),
                    caption=f"Bulk uploaded by user {user_id}"
                )
                
                result_data = json.loads(result)
                
                if result_data['success']:
                    await add_file(
                        original_name=result_data['file_name'],
                        file_name=result_data['file_name'],
                        message_id=result_data['telegram_message_id'],
                        chat_id=result_data['telegram_chat'],
                        file_size=result_data['size_bytes'],
                        mime_type="",
                        category_id=category_id,
                        uploaded_by=user_id
                    )
                    success_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                failed_count += 1
                print(f"Error uploading {url}: {e}")
        
        await status_msg.edit_text(
            f"✅ **آپلود گروهی تکمیل شد**\n\n"
            f"📊 نتایج:\n"
            f"✅ موفق: {success_count}\n"
            f"❌ ناموفق: {failed_count}\n"
            f"📋 کل: {len(urls)}"
        )
        
    except asyncio.TimeoutError:
        await client.send_message(user_id, "⏰ زمان شما تمام شد.")
    except Exception as e:
        await client.send_message(user_id, f"❌ خطا در آپلود گروهی: {str(e)}")