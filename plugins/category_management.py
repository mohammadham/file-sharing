"""
Category Management Plugin for File-Sharing Bot
Handles category creation, editing, deletion and navigation
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import os
import uuid
import asyncio
import sys
import time

import pathlib
PARENT_PATH = pathlib.Path(__file__).parent.resolve()
sys.path.append(PARENT_PATH)
from config import TEMP_PATH, CHANNEL_ID, ADMINS, APP_PATH, DATABASE_PATH
from bot import Bot

from database.database import (
    create_category, get_category, get_categories, update_category, delete_category,
    get_files_by_category, search_files, add_file, create_file_link, get_file
)

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

@Bot.on_callback_query(filters.regex(r"^cat_"))
async def handle_category_callbacks(client: Client, callback_query: CallbackQuery):
    """Handle category management callbacks"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    message_id = callback_query.message.id
    
    # Check if user is admin for admin-only operations
    admin_operations = ['cat_create_', 'cat_edit_', 'cat_delete_', 'cat_upload_']
    if any(data.startswith(op) for op in admin_operations) and user_id not in ADMINS:
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
        
        elif data.startswith("cat_edit_"):
            category_id = data.split("_", 2)[2]
            if category_id == "root":
                await callback_query.answer("ریشه قابل ویرایش نیست.", show_alert=True)
            else:
                await start_category_editing(client, callback_query, category_id)
        
        elif data.startswith("cat_delete_"):
            category_id = data.split("_", 2)[2]
            if category_id == "root":
                await callback_query.answer("ریشه قابل حذف نیست.", show_alert=True)
            else:
                await show_delete_confirmation(client, callback_query, category_id)
        
        elif data.startswith("cat_search_"):
            target_id = data.split("_", 2)[2]
            category_id = None if target_id == "root" else target_id
            await start_category_search(client, callback_query, category_id)
        
        elif data.startswith("cat_upload_"):
            target_id = data.split("_", 2)[2]
            category_id = None if target_id == "root" else target_id
            await start_category_upload(client, callback_query, category_id)
        
        elif data.startswith("cat_confirm_delete_"):
            category_id = data.split("_", 3)[3]
            await confirm_delete_category(client, callback_query, category_id)
        
        elif data == "cat_cancel":
            await callback_query.answer("لغو شد.")
            await show_categories_menu(client, user_id, None, message_id, True)
        
        elif data.startswith("cat_files_"):
            # Show full files list for category
            target_id = data.split("_", 2)[2]
            category_id = None if target_id == "root" else target_id
            await show_more_files(client, user_id, message_id, category_id)
            await callback_query.answer()
        
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

async def start_category_editing(client: Client, callback_query: CallbackQuery, category_id: str):
    """Edit category name/description"""
    user_id = callback_query.from_user.id
    msg_id = callback_query.message.id
    try:
        category = await get_category(category_id)
        if not category:
            await callback_query.answer("دسته‌بندی یافت نشد.", show_alert=True)
            return
        name_msg = await client.ask(user_id, f"📝 نام جدید برای '{category['name']}' (یا /skip):", timeout=120)
        new_name = None if name_msg.text == "/skip" else name_msg.text.strip()
        desc_msg = await client.ask(user_id, f"📄 توضیحات جدید (یا /skip):", timeout=120)
        new_desc = None if desc_msg.text == "/skip" else desc_msg.text.strip()
        await update_category(category_id, name=new_name, description=new_desc)
        await client.send_message(user_id, "✅ دسته‌بندی بروزرسانی شد.")
        await show_categories_menu(client, user_id, category_id, msg_id, True)
    except asyncio.TimeoutError:
        await client.send_message(user_id, "⏰ زمان ویرایش تمام شد.")
    except Exception as e:
        await client.send_message(user_id, f"❌ خطا در ویرایش: {str(e)}")

async def show_delete_confirmation(client: Client, callback_query: CallbackQuery, category_id: str):
    """Show delete confirmation UI"""
    user_id = callback_query.from_user.id
    msg_id = callback_query.message.id
    try:
        category = await get_category(category_id)
        if not category:
            await callback_query.answer("دسته‌بندی یافت نشد.", show_alert=True)
            return
        files = await get_files_by_category(category_id)
        subcats = await get_categories(category_id)
        text = (
            f"⚠️ **حذف دسته‌بندی**\n\n"
            f"📁 {category['name']}\n"
            f"📄 فایل‌ها: {len(files)}\n"
            f"📁 زیردسته‌ها: {len(subcats)}\n\n"
            f"آیا مطمئن هستید؟"
        )
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ تأیید", callback_data=f"cat_confirm_delete_{category_id}"),
                InlineKeyboardButton("❌ انصراف", callback_data="cat_cancel")
            ]
        ])
        await client.edit_message_text(user_id, msg_id, text, reply_markup=kb)
    except Exception as e:
        await client.send_message(user_id, f"❌ خطا: {str(e)}")

async def confirm_delete_category(client: Client, callback_query: CallbackQuery, category_id: str):
    user_id = callback_query.from_user.id
    msg_id = callback_query.message.id
    try:
        category = await get_category(category_id)
        if not category:
            await callback_query.answer("یافت نشد.", show_alert=True)
            return
        name = category['name']
        await delete_category(category_id)
        await client.send_message(user_id, f"✅ دسته‌بندی '{name}' حذف شد.")
        # refresh to parent
        parent_id = category.get('parent_id')
        await show_categories_menu(client, user_id, parent_id, msg_id, True)
        await callback_query.answer()
    except Exception as e:
        await client.send_message(user_id, f"❌ خطا در حذف: {str(e)}")

async def start_category_search(client: Client, callback_query: CallbackQuery, category_id: str = None):
    user_id = callback_query.from_user.id
    msg_id = callback_query.message.id
    try:
        ask = await client.ask(user_id, "🔍 عبارت جستجو را وارد کنید (یا /cancel):", timeout=120)
        if ask.text == "/cancel":
            await show_categories_menu(client, user_id, category_id, msg_id, True)
            return
        query = ask.text.strip()
        results = await search_files(query, category_id)
        if not results:
            await client.send_message(user_id, "❌ نتیجه‌ای یافت نشد.")
            return
        text = f"🔍 نتایج جستجو ({len(results)}):\n\n"
        buttons = []
        for i, f in enumerate(results[:20]):
            emoji = get_file_emoji(f.get('mime_type',''))
            text += f"{i+1}. {emoji} {f['original_name']}\n"
            buttons.append([InlineKeyboardButton(f"{emoji} {f['original_name'][:40]}", callback_data=f"file_info_{f['id']}")])
        await client.edit_message_text(user_id, msg_id, text, reply_markup=InlineKeyboardMarkup(buttons))
    except asyncio.TimeoutError:
        await client.send_message(user_id, "⏰ زمان جستجو تمام شد.")
    except Exception as e:
        await client.send_message(user_id, f"❌ خطا در جستجو: {str(e)}")

async def start_category_upload(client: Client, callback_query: CallbackQuery, category_id: str = None):
    user_id = callback_query.from_user.id
    msg_id = callback_query.message.id
    try:
        ask = await client.ask(user_id, "📤 فایل را ارسال کنید یا لینک بدهید (یا /cancel):", timeout=300)
        if ask.text == "/cancel":
            await show_categories_menu(client, user_id, category_id, msg_id, True)
            return
        if ask.document or ask.photo or ask.video or ask.audio:
            # Forward to DB channel
            forwarded = await ask.forward(callback_query.message.chat.id if False else client.db_channel.id)
            # Determine file meta
            if ask.document:
                file_name = ask.document.file_name or f"document_{ask.id}"
                mime = ask.document.mime_type
                size = ask.document.file_size
            elif ask.photo:
                file_name = f"photo_{ask.id}.jpg"
                mime = "image/jpeg"
                size = ask.photo.file_size
            elif ask.video:
                file_name = ask.video.file_name or f"video_{ask.id}.mp4"
                mime = ask.video.mime_type
                size = ask.video.file_size
            else:
                file_name = ask.audio.file_name or f"audio_{ask.id}.mp3"
                mime = ask.audio.mime_type
                size = ask.audio.file_size
            # Optional description
            try:
                desc_msg = await client.ask(user_id, "📝 توضیح فایل (یا /skip):", timeout=60)
                description = "" if desc_msg.text == "/skip" else desc_msg.text.strip()
            except asyncio.TimeoutError:
                description = ""
            await add_file(
                original_name=file_name,
                file_name=file_name,
                message_id=forwarded.id,
                chat_id=str(client.db_channel.id),
                file_size=size or 0,
                mime_type=mime or "",
                category_id=category_id,
                description=description,
                uploaded_by=user_id
            )
            await client.send_message(user_id, "✅ فایل ثبت شد.")
            await show_categories_menu(client, user_id, category_id, msg_id, True)
        elif ask.text and (ask.text.startswith("http://") or ask.text.startswith("https://")):
            # Simple URL save as placeholder entry
            import requests
            try:
                r = requests.head(ask.text, timeout=10)
                size = int(r.headers.get('content-length', 0))
                mime = r.headers.get('content-type', 'application/octet-stream')
                fname = ask.text.split('/')[-1] or f"url_{int(time.time())}"
            except:
                size = 0
                mime = 'application/octet-stream'
                fname = f"url_{int(time.time())}"
            url_text = f"🔗 URL: {ask.text}\nنام: {fname}"
            url_msg = await client.send_message(client.db_channel.id, url_text)
            await add_file(
                original_name=fname,
                file_name=fname,
                message_id=url_msg.id,
                chat_id=str(client.db_channel.id),
                file_size=size,
                mime_type=mime,
                category_id=category_id,
                description=f"URL: {ask.text}",
                uploaded_by=user_id
            )
            await client.send_message(user_id, "✅ فایل از لینک ثبت شد.")
            await show_categories_menu(client, user_id, category_id, msg_id, True)
        else:
            await client.send_message(user_id, "❌ ورودی معتبر نیست.")
    except asyncio.TimeoutError:
        await client.send_message(user_id, "⏰ زمان آپلود تمام شد.")
    except Exception as e:
        await client.send_message(user_id, f"❌ خطا در آپلود: {str(e)}")

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

async def show_more_files(client: Client, user_id: int, message_id: int, category_id: str = None):
    try:
        files = await get_files_by_category(category_id)
        if not files:
            await client.edit_message_text(user_id, message_id, "هیچ فایلی وجود ندارد.")
            return
        text = f"📄 لیست کامل فایل‌ها ({len(files)}):\n\n"
        buttons = []
        for i, f in enumerate(files):
            emoji = get_file_emoji(f.get('mime_type',''))
            text += f"{i+1}. {emoji} {f['original_name']}\n"
            buttons.append([InlineKeyboardButton(f"{emoji} {f['original_name'][:40]}", callback_data=f"file_info_{f['id']}")])
        await client.edit_message_text(user_id, message_id, text, reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        await client.send_message(user_id, f"❌ خطا در نمایش فایل‌ها: {str(e)}")