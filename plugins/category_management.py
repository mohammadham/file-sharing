"""
Category Management Plugin for File-Sharing Bot
Handles category creation, editing, deletion and navigation
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot import Bot
from config import ADMINS
from database.database import (
    create_category, get_category, get_categories, update_category, delete_category,
    get_files_by_category, search_files, add_file, create_file_link, get_file
)
import os
import uuid
import asyncio

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('categories'))
async def show_categories_command(client: Client, message: Message):
    """Show main categories menu"""
    await show_categories_menu(client, message.from_user.id, None, message.id)

async def show_categories_menu(client: Client, user_id: int, parent_id: str = None, 
                              message_id: int = None, edit_message: bool = False):
    """Show categories menu with navigation"""
    categories = await get_categories(parent_id)
    files = await get_files_by_category(parent_id)
    
    # Build category name path
    path_text = "📁 دسته‌بندی‌ها"
    if parent_id:
        current_category = await get_category(parent_id)
        if current_category:
            path_text = f"📁 {current_category['name']}"
    
    # Build keyboard
    keyboard = []
    
    # Add subcategories
    for category in categories:
        sub_files = await get_files_by_category(category['id'])
        keyboard.append([
            InlineKeyboardButton(
                f"📁 {category['name']} ({len(sub_files)} فایل)",
                callback_data=f"cat_view_{category['id']}"
            )
        ])
    
    # Add files in current category
    for file in files[:10]:  # Show max 10 files
        file_emoji = get_file_emoji(file['mime_type'])
        keyboard.append([
            InlineKeyboardButton(
                f"{file_emoji} {file['original_name'][:30]}{'...' if len(file['original_name']) > 30 else ''}",
                callback_data=f"file_info_{file['id']}"
            )
        ])
    
    if len(files) > 10:
        keyboard.append([
            InlineKeyboardButton(f"... و {len(files) - 10} فایل دیگر", callback_data=f"cat_files_{parent_id or 'root'}")
        ])
    
    # Management buttons for admins
    management_row = []
    if parent_id:
        management_row.append(
            InlineKeyboardButton("➕ دسته جدید", callback_data=f"cat_create_{parent_id}")
        )
        management_row.append(
            InlineKeyboardButton("✏️ ویرایش", callback_data=f"cat_edit_{parent_id}")
        )
        management_row.append(
            InlineKeyboardButton("🗑️ حذف", callback_data=f"cat_delete_{parent_id}")
        )
    else:
        management_row.append(
            InlineKeyboardButton("➕ دسته جدید", callback_data="cat_create_root")
        )
    
    if management_row:
        keyboard.append(management_row)
    
    # Navigation buttons
    nav_row = []
    if parent_id:
        # Get parent category to show back button
        current_cat = await get_category(parent_id)
        back_parent = current_cat['parent_id'] if current_cat else None
        nav_row.append(
            InlineKeyboardButton("🔙 برگشت", callback_data=f"cat_back_{back_parent or 'root'}")
        )
    
    nav_row.append(
        InlineKeyboardButton("🔍 جستجو", callback_data=f"cat_search_{parent_id or 'root'}")
    )
    nav_row.append(
        InlineKeyboardButton("📤 آپلود فایل", callback_data=f"cat_upload_{parent_id or 'root'}")
    )
    
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([
        InlineKeyboardButton("❌ بستن", callback_data="close_menu")
    ])
    
    text = f"{path_text}\n\n"
    if categories:
        text += f"📂 زیردسته‌ها: {len(categories)}\n"
    if files:
        text += f"📄 فایل‌ها: {len(files)}\n"
    
    if not categories and not files:
        text += "این دسته خالی است."
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if edit_message and message_id:
        try:
            await client.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup
            )
        except:
            await client.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=reply_markup
            )
    else:
        await client.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=reply_markup
        )

def get_file_emoji(mime_type: str) -> str:
    """Get emoji based on file type"""
    if not mime_type:
        return "📄"
    
    if mime_type.startswith("image/"):
        return "🖼️"
    elif mime_type.startswith("video/"):
        return "🎬"
    elif mime_type.startswith("audio/"):
        return "🎵"
    elif mime_type in ["application/pdf"]:
        return "📕"
    elif mime_type in ["application/zip", "application/x-rar-compressed"]:
        return "📦"
    elif mime_type.startswith("text/"):
        return "📝"
    else:
        return "📄"

@Bot.on_callback_query()
async def handle_category_callbacks(client: Client, callback_query: CallbackQuery):
    """Handle category management callbacks"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    message_id = callback_query.message.id
    
    # Check if user is admin
    if user_id not in ADMINS:
        await callback_query.answer("شما مجوز دسترسی به این بخش را ندارید.", show_alert=True)
        return
    
    try:
        if data.startswith("cat_view_"):
            category_id = data.split("_", 2)[2]
            await show_categories_menu(client, user_id, category_id, message_id, True)
            await callback_query.answer()
            
        elif data.startswith("cat_back_"):
            parent_id = data.split("_", 2)[2]
            if parent_id == "root":
                parent_id = None
            await show_categories_menu(client, user_id, parent_id, message_id, True)
            await callback_query.answer()
            
        elif data.startswith("cat_create_"):
            parent_id = data.split("_", 2)[2]
            if parent_id == "root":
                parent_id = None
            await start_category_creation(client, callback_query, parent_id)
            
        elif data == "close_menu":
            await client.delete_messages(user_id, message_id)
            await callback_query.answer()
            
        elif data.startswith("file_info_"):
            file_id = data.split("_", 2)[2]
            await show_file_info(client, callback_query, file_id)
            
    except Exception as e:
        await callback_query.answer(f"خطا: {str(e)}", show_alert=True)

async def start_category_creation(client: Client, callback_query: CallbackQuery, parent_id: str = None):
    """Start category creation process"""
    await callback_query.answer()
    user_id = callback_query.from_user.id
    
    try:
        name_msg = await client.ask(
            chat_id=user_id,
            text="📝 نام دسته‌بندی جدید را وارد کنید:",
            timeout=60
        )
        category_name = name_msg.text.strip()
        
        desc_msg = await client.ask(
            chat_id=user_id,
            text="📄 توضیحات دسته‌بندی را وارد کنید (یا /skip برای رد کردن):",
            timeout=60
        )
        
        category_description = "" if desc_msg.text == "/skip" else desc_msg.text.strip()
        
        category_id = await create_category(
            name=category_name,
            description=category_description,
            parent_id=parent_id,
            created_by=user_id
        )
        
        await client.send_message(
            chat_id=user_id,
            text=f"✅ دسته‌بندی '{category_name}' با موفقیت ایجاد شد!"
        )
        
        await show_categories_menu(client, user_id, parent_id, callback_query.message.id, True)
        
    except asyncio.TimeoutError:
        await client.send_message(user_id, "⏰ زمان شما تمام شد. لطفاً دوباره تلاش کنید.")
    except Exception as e:
        await client.send_message(user_id, f"❌ خطا در ایجاد دسته‌بندی: {str(e)}")

async def show_file_info(client: Client, callback_query: CallbackQuery, file_id: str):
    """Show file information and download links"""
    file_info = await get_file(file_id)
    if not file_info:
        await callback_query.answer("فایل یافت نشد!", show_alert=True)
        return
    
    # Create download links
    stream_link_code = str(uuid.uuid4())
    download_link_code = str(uuid.uuid4())
    
    await create_file_link(file_id, "stream", stream_link_code)
    await create_file_link(file_id, "download", download_link_code)
    
    file_emoji = get_file_emoji(file_info['mime_type'])
    size_mb = file_info['file_size'] / (1024 * 1024) if file_info['file_size'] > 0 else 0
    
    text = f"{file_emoji} **اطلاعات فایل**\n\n"
    text += f"📛 نام: `{file_info['original_name']}`\n"
    text += f"📏 حجم: {size_mb:.2f} MB\n"
    text += f"📅 تاریخ آپلود: {file_info['created_at'][:10]}\n"
    
    if file_info['description']:
        text += f"📝 توضیحات: {file_info['description']}\n"
    
    text += f"\n🔗 **لینک‌های دانلود:**\n"
    text += f"• دانلود مستقیم (استریم): `/stream_{stream_link_code}`\n"
    text += f"• دانلود معمولی: `/download_{download_link_code}`"
    
    keyboard = [
        [
            InlineKeyboardButton("🔙 برگشت", callback_data=f"cat_view_{file_info['category_id'] or 'root'}")
        ]
    ]
    
    await client.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    await callback_query.answer()