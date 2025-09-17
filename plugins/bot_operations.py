"""
Bot Operations Implementation
Complete implementation of search, upload, category management, and broadcast
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
import asyncio
import json
import uuid
import mimetypes
import os
import time
import sys
import pathlib
PARENT_PATH = pathlib.Path(__file__).parent.resolve()
if PARENT_PATH not in ["",None] :
    sys.path.append(PARENT_PATH)
    from config import TEMP_PATH, CHANNEL_ID, ADMINS, APP_PATH, TG_CONFIG_FILE
    from bot import Bot
    from database.database import (
        search_files, create_category, get_category, update_category, delete_category,
        add_file, get_files_by_category, full_userbase, del_user
    )
    from .enhanced_bot_interface import (
        get_state, set_state, BotState, send_menu_message, 
        cleanup_user_messages, add_message_for_cleanup
    )
    from .category_management import get_file_emoji
else:
    from bot import Bot
    from config import ADMINS, CHANNEL_ID
    from database.database import (
        search_files, create_category, get_category, update_category, delete_category,
        add_file, get_files_by_category, full_userbase, del_user
    )
    from plugins.enhanced_bot_interface import (
        get_state, set_state, BotState, send_menu_message, 
        cleanup_user_messages, add_message_for_cleanup
    )
    from plugins.category_management import get_file_emoji
# Search Implementation
async def start_search_process(client: Client, user_id: int, category_id: str = None):
    """Start interactive search process"""
    try:
        # Ask for search query
        search_msg = await client.ask(
            chat_id=user_id,
            text="🔍 عبارت جستجو را وارد کنید (یا /cancel برای لغو):",
            timeout=120
        )
        
        if search_msg.text == "/cancel":
            set_state(user_id, BotState.MAIN)
            text = "❌ جستجو لغو شد.\n\n🏠 **منو اصلی**"
            await send_menu_message(client, user_id, text)
            return
        
        query = search_msg.text.strip()
        
        # Perform search
        results = await search_files(query, category_id)
        
        # Update state to search results
        set_state(user_id, BotState.SEARCH_RESULTS, {
            'query': query,
            'category_id': category_id,
            'results': results
        })
        
        if not results:
            text = f"🔍 **جستجو برای '{query}'**\n\n❌ هیچ نتیجه‌ای یافت نشد."
            await send_menu_message(client, user_id, text)
            return
        
        # Show results
        text = f"🔍 **نتایج جستجو برای '{query}'**\n"
        if category_id:
            category = await get_category(category_id)
            if category:
                text += f"📁 در دسته: {category['name']}\n"
        
        text += f"\n📊 **{len(results)} نتیجه یافت شد:**\n\n"
        
        # Create result buttons
        result_buttons = []
        for i, file in enumerate(results[:15]):  # Show first 15 results
            emoji = get_file_emoji(file.get('mime_type', ''))
            size_mb = (file.get('file_size', 0) / 1024 / 1024)
            size_text = f" ({size_mb:.1f}MB)" if size_mb > 0 else ""
            
            text += f"{i+1}. {emoji} {file['original_name']}{size_text}\n"
            
            result_buttons.append([
                InlineKeyboardButton(
                    f"{emoji} {file['original_name'][:35]}{'...' if len(file['original_name']) > 35 else ''}",
                    callback_data=f"view_file_{file['id']}"
                )
            ])
        
        if len(results) > 15:
            text += f"\n... و {len(results) - 15} نتیجه دیگر"
        
        await send_menu_message(client, user_id, text, custom_buttons=result_buttons)
        
    except asyncio.TimeoutError:
        set_state(user_id, BotState.MAIN)
        text = "⏰ زمان جستجو تمام شد.\n\n🏠 **منو اصلی**"
        await send_menu_message(client, user_id, text)
    except Exception as e:
        set_state(user_id, BotState.MAIN)
        text = f"❌ خطا در جستجو: {str(e)}\n\n🏠 **منو اصلی**"
        await send_menu_message(client, user_id, text)

# Category Creation Implementation
async def start_category_creation(client: Client, user_id: int):
    """Start category creation process"""
    try:
        # Ask for category name
        name_msg = await client.ask(
            chat_id=user_id,
            text="📝 نام دسته‌بندی جدید را وارد کنید (یا /cancel برای لغو):",
            timeout=120
        )
        
        if name_msg.text == "/cancel":
            set_state(user_id, BotState.MAIN)
            text = "❌ ایجاد دسته‌بندی لغو شد.\n\n🏠 **منو اصلی**"
            await send_menu_message(client, user_id, text)
            return
        
        category_name = name_msg.text.strip()
        
        # Ask for description
        desc_msg = await client.ask(
            chat_id=user_id,
            text="📄 توضیحات دسته‌بندی را وارد کنید (یا /skip برای رد کردن):",
            timeout=120
        )
        
        category_description = "" if desc_msg.text == "/skip" else desc_msg.text.strip()
        
        # Create category
        category_id = await create_category(
            name=category_name,
            description=category_description,
            created_by=user_id
        )
        
        # Update state and show success
        set_state(user_id, BotState.CATEGORIES_LIST)
        text = f"✅ دسته‌بندی '{category_name}' با موفقیت ایجاد شد!\n\n📁 **دسته‌بندی‌ها**"
        await send_menu_message(client, user_id, text)
        
        # Show updated categories list
        from enhanced_bot_interface import show_categories_list
        await show_categories_list(client, user_id, None)
        
    except asyncio.TimeoutError:
        set_state(user_id, BotState.MAIN)
        text = "⏰ زمان ایجاد دسته‌بندی تمام شد.\n\n🏠 **منو اصلی**"
        await send_menu_message(client, user_id, text)
    except Exception as e:
        set_state(user_id, BotState.MAIN)
        text = f"❌ خطا در ایجاد دسته‌بندی: {str(e)}\n\n🏠 **منو اصلی**"
        await send_menu_message(client, user_id, text)

# Category Editing Implementation  
async def start_category_editing(client: Client, user_id: int, category_id: str):
    """Start category editing process"""
    try:
        category = await get_category(category_id)
        if not category:
            set_state(user_id, BotState.MAIN)
            text = "❌ دسته‌بندی یافت نشد.\n\n🏠 **منو اصلی**"
            await send_menu_message(client, user_id, text)
            return
        
        # Ask for new name
        name_msg = await client.ask(
            chat_id=user_id,
            text=f"📝 نام جدید برای '{category['name']}' (فعلی: {category['name']}) یا /skip برای رد کردن:",
            timeout=120
        )
        
        if name_msg.text == "/cancel":
            set_state(user_id, BotState.CATEGORY_VIEW, {
                'category_id': category_id,
                'category_name': category['name']
            })
            text = "❌ ویرایش لغو شد."
            await send_menu_message(client, user_id, text)
            return
        
        new_name = None if name_msg.text == "/skip" else name_msg.text.strip()
        
        # Ask for new description
        desc_msg = await client.ask(
            chat_id=user_id,
            text=f"📄 توضیحات جدید (فعلی: {category['description'] or 'ندارد'}) یا /skip برای رد کردن:",
            timeout=120
        )
        
        new_description = None if desc_msg.text == "/skip" else desc_msg.text.strip()
        
        # Update category
        await update_category(
            category_id=category_id,
            name=new_name,
            description=new_description
        )
        
        # Get updated category info
        updated_category = await get_category(category_id)
        
        # Update state and show success
        set_state(user_id, BotState.CATEGORY_VIEW, {
            'category_id': category_id,
            'category_name': updated_category['name']
        })
        
        text = f"✅ دسته‌بندی '{updated_category['name']}' با موفقیت بروزرسانی شد!"
        await send_menu_message(client, user_id, text)
        
    except asyncio.TimeoutError:
        set_state(user_id, BotState.CATEGORY_VIEW, {
            'category_id': category_id,
            'category_name': category['name']
        })
        text = "⏰ زمان ویرایش تمام شد."
        await send_menu_message(client, user_id, text)
    except Exception as e:
        set_state(user_id, BotState.CATEGORY_VIEW, {
            'category_id': category_id,
            'category_name': category['name']
        })
        text = f"❌ خطا در ویرایش: {str(e)}"
        await send_menu_message(client, user_id, text)

# Upload Implementation
async def start_upload_process(client: Client, user_id: int, category_id: str = None):
    """Start file upload process"""
    try:
        # Ask for file
        upload_msg = await client.ask(
            chat_id=user_id,
            text="📤 فایل مورد نظر را ارسال کنید یا لینک دانلود را وارد کنید (یا /cancel برای لغو):",
            timeout=300  # 5 minutes
        )
        
        if upload_msg.text == "/cancel":
            set_state(user_id, BotState.MAIN)
            text = "❌ آپلود لغو شد.\n\n🏠 **منو اصلی**"
            await send_menu_message(client, user_id, text)
            return
        
        # Handle different types of uploads
        if upload_msg.document or upload_msg.photo or upload_msg.video or upload_msg.audio:
            await handle_direct_file_upload(client, upload_msg, category_id, user_id)
        elif upload_msg.text and (upload_msg.text.startswith("http://") or upload_msg.text.startswith("https://")):
            await handle_url_upload(client, upload_msg.text, category_id, user_id)
        else:
            text = "❌ لطفاً یک فایل معتبر یا لینک صحیح ارسال کنید."
            await send_menu_message(client, user_id, text)
            return
            
    except asyncio.TimeoutError:
        set_state(user_id, BotState.MAIN)
        text = "⏰ زمان آپلود تمام شد.\n\n🏠 **منو اصلی**"
        await send_menu_message(client, user_id, text)
    except Exception as e:
        set_state(user_id, BotState.MAIN)
        text = f"❌ خطا در آپلود: {str(e)}\n\n🏠 **منو اصلی**"
        await send_menu_message(client, user_id, text)

async def handle_direct_file_upload(client: Client, message: Message, category_id: str, user_id: int):
    """Handle direct file upload"""
    try:
        # Get file info based on message type
        if message.document:
            file_info = message.document
            file_name = file_info.file_name or f"document_{message.id}"
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
        
        # Forward to database channel
        forwarded = await message.forward(client.db_channel.id)
        
        # Ask for description
        try:
            desc_msg = await client.ask(
                chat_id=user_id,
                text="📝 توضیحات فایل را وارد کنید (یا /skip برای رد کردن):",
                timeout=60
            )
            description = "" if desc_msg.text == "/skip" else desc_msg.text.strip()
        except asyncio.TimeoutError:
            description = ""
        
        # Add to database
        file_id = await add_file(
            original_name=file_name,
            file_name=file_name,
            message_id=forwarded.id,
            chat_id=str(client.db_channel.id),
            file_size=file_size,
            mime_type=mime_type or "",
            category_id=category_id,
            description=description,
            uploaded_by=user_id
        )
        
        # Success message
        set_state(user_id, BotState.MAIN)
        category_text = ""
        if category_id:
            category = await get_category(category_id)
            if category:
                category_text = f" به دسته '{category['name']}'"
        
        text = f"✅ فایل '{file_name}'{category_text} با موفقیت آپلود شد!\n\n🏠 **منو اصلی**"
        await send_menu_message(client, user_id, text)
        
    except Exception as e:
        set_state(user_id, BotState.MAIN)
        text = f"❌ خطا در آپلود فایل: {str(e)}\n\n🏠 **منو اصلی**"
        await send_menu_message(client, user_id, text)

async def handle_url_upload(client: Client, url: str, category_id: str, user_id: int):
    """Handle URL upload - simplified version"""
    try:
        # For now, just save URL info (you can integrate with telegram_uploader later)
        import requests
        
        # Try to get file info from URL
        try:
            response = requests.head(url, timeout=10)
            file_size = int(response.headers.get('content-length', 0))
            content_type = response.headers.get('content-type', 'application/octet-stream')
            file_name = url.split('/')[-1] or f"url_file_{int(time.time())}"
        except:
            file_size = 0
            content_type = 'application/octet-stream'
            file_name = f"url_file_{int(time.time())}"
        
        # Ask for description
        try:
            desc_msg = await client.ask(
                chat_id=user_id,
                text="📝 توضیحات فایل را وارد کنید (یا /skip برای رد کردن):",
                timeout=60
            )
            description = "" if desc_msg.text == "/skip" else desc_msg.text.strip()
        except asyncio.TimeoutError:
            description = ""
        
        # For demo purposes, create a text message with URL info
        url_info_text = f"🔗 **فایل از لینک:**\n\n**URL:** {url}\n**نام:** {file_name}\n"
        if description:
            url_info_text += f"**توضیحات:** {description}"
        
        # Send to database channel
        url_msg = await client.send_message(client.db_channel.id, url_info_text)
        
        # Add to database
        file_id = await add_file(
            original_name=file_name,
            file_name=file_name,
            message_id=url_msg.id,
            chat_id=str(client.db_channel.id),
            file_size=file_size,
            mime_type=content_type,
            category_id=category_id,
            description=f"URL: {url}\n{description}",
            uploaded_by=user_id
        )
        
        set_state(user_id, BotState.MAIN)
        text = f"✅ فایل از لینک با موفقیت آپلود شد!\n\n🏠 **منو اصلی**"
        await send_menu_message(client, user_id, text)
        
    except Exception as e:
        set_state(user_id, BotState.MAIN)
        text = f"❌ خطا در آپلود از لینک: {str(e)}\n\n🏠 **منو اصلی**"
        await send_menu_message(client, user_id, text)

# Broadcast Implementation
async def start_broadcast_process(client: Client, user_id: int):
    """Start broadcast process"""
    try:
        # Ask for broadcast message
        broadcast_msg = await client.ask(
            chat_id=user_id,
            text="📢 پیام مورد نظر برای ارسال همگانی را ارسال کنید (یا /cancel برای لغو):",
            timeout=300
        )
        
        if broadcast_msg.text == "/cancel":
            set_state(user_id, BotState.MAIN)
            text = "❌ ارسال پیام لغو شد.\n\n🏠 **منو اصلی**"
            await send_menu_message(client, user_id, text)
            return
        
        # Get all users
        users = await full_userbase()
        
        if not users:
            set_state(user_id, BotState.MAIN)
            text = "❌ هیچ کاربری برای ارسال پیام وجود ندارد.\n\n🏠 **منو اصلی**"
            await send_menu_message(client, user_id, text)
            return
        
        # Show confirmation
        confirm_buttons = [[
            InlineKeyboardButton("✅ تأیید ارسال", callback_data="confirm_broadcast"),
            InlineKeyboardButton("❌ لغو", callback_data="cancel_operation")
        ]]
        
        text = f"📢 **تأیید ارسال پیام همگانی**\n\n"
        text += f"👥 تعداد کاربران: {len(users)}\n"
        text += f"📝 پیام: {broadcast_msg.text[:100]}{'...' if len(broadcast_msg.text) > 100 else ''}\n\n"
        text += "آیا مطمئن هستید؟"
        
        # Store broadcast message for later use
        set_state(user_id, BotState.BROADCASTING, {
            'message': broadcast_msg,
            'users': users
        })
        
        await send_menu_message(client, user_id, text, custom_buttons=confirm_buttons)
        
    except asyncio.TimeoutError:
        set_state(user_id, BotState.MAIN)
        text = "⏰ زمان ارسال پیام تمام شد.\n\n🏠 **منو اصلی**"
        await send_menu_message(client, user_id, text)
    except Exception as e:
        set_state(user_id, BotState.MAIN)
        text = f"❌ خطا در ارسال پیام: {str(e)}\n\n🏠 **منو اصلی**"
        await send_menu_message(client, user_id, text)

# Broadcast confirmation handler
@Bot.on_callback_query(filters.regex(r"^confirm_broadcast"))
async def handle_confirm_broadcast(client: Client, callback_query: CallbackQuery):
    """Handle broadcast confirmation"""
    user_id = callback_query.from_user.id
    message_id = callback_query.message.id
    
    if user_id not in ADMINS:
        await callback_query.answer("⛔️ شما مجوز دسترسی ندارید.", show_alert=True)
        return
    
    await callback_query.answer()
    
    try:
        state_info = get_state(user_id)
        broadcast_data = state_info['data']
        broadcast_msg = broadcast_data['message']
        users = broadcast_data['users']
        
        # Start broadcasting
        text = f"📢 **شروع ارسال پیام همگانی...**\n\n⏳ در حال ارسال به {len(users)} کاربر..."
        await send_menu_message(client, user_id, text, message_id)
        
        # Send to all users
        successful = 0
        failed = 0
        blocked = 0
        
        for i, target_user_id in enumerate(users):
            try:
                await broadcast_msg.copy(target_user_id)
                successful += 1
            except UserIsBlocked:
                await del_user(target_user_id)
                blocked += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                try:
                    await broadcast_msg.copy(target_user_id)
                    successful += 1
                except:
                    failed += 1
            except:
                failed += 1
            
            # Update progress every 10 users
            if (i + 1) % 10 == 0:
                progress_text = f"📢 **ارسال پیام همگانی...**\n\n"
                progress_text += f"✅ موفق: {successful}\n"
                progress_text += f"❌ ناموفق: {failed}\n"
                progress_text += f"🚫 مسدود شده: {blocked}\n"
                progress_text += f"📊 پیشرفت: {i+1}/{len(users)}"
                
                try:
                    await client.edit_message_text(
                        chat_id=user_id,
                        message_id=message_id,
                        text=progress_text
                    )
                except:
                    pass
        
        # Final results
        set_state(user_id, BotState.MAIN)
        final_text = f"✅ **ارسال پیام همگانی تکمیل شد!**\n\n"
        final_text += f"📊 **نتایج:**\n"
        final_text += f"✅ موفق: {successful}\n"
        final_text += f"❌ ناموفق: {failed}\n"
        final_text += f"🚫 مسدود شده: {blocked}\n"
        final_text += f"📋 کل: {len(users)}\n\n"
        final_text += "🏠 **منو اصلی**"
        
        await send_menu_message(client, user_id, final_text, message_id)
        
    except Exception as e:
        set_state(user_id, BotState.MAIN)
        text = f"❌ خطا در ارسال پیام همگانی: {str(e)}\n\n🏠 **منو اصلی**"
        await send_menu_message(client, user_id, text, message_id)

# Delete confirmation and handling
async def show_delete_confirmation(client: Client, user_id: int, message_id: int, category_id: str):
    """Show category deletion confirmation"""
    try:
        category = await get_category(category_id)
        if not category:
            text = "❌ دسته‌بندی یافت نشد."
            await send_menu_message(client, user_id, text, message_id)
            return
        
        # Get category statistics
        files = await get_files_by_category(category_id)
        from database.database import get_categories
        subcategories = await get_categories(category_id)
        
        set_state(user_id, BotState.DELETING_CATEGORY, {'category_id': category_id})
        
        text = f"⚠️ **تأیید حذف دسته‌بندی**\n\n"
        text += f"📁 **دسته:** {category['name']}\n"
        text += f"📄 **فایل‌ها:** {len(files)}\n"
        text += f"📁 **زیردسته‌ها:** {len(subcategories)}\n\n"
        text += "⚠️ **توجه:** تمام فایل‌ها و زیردسته‌ها به دسته‌بندی والد منتقل خواهند شد.\n\n"
        text += "آیا مطمئن هستید؟"
        
        await send_menu_message(client, user_id, text, message_id)
        
    except Exception as e:
        text = f"❌ خطا: {str(e)}"
        await send_menu_message(client, user_id, text, message_id)

@Bot.on_callback_query(filters.regex(r"^confirm_delete_"))
async def handle_confirm_delete(client: Client, callback_query: CallbackQuery):
    """Handle confirmed category deletion"""
    category_id = callback_query.data.split("_")[-1]
    user_id = callback_query.from_user.id
    message_id = callback_query.message.id
    
    if user_id not in ADMINS:
        await callback_query.answer("⛔️ شما مجوز دسترسی ندارید.", show_alert=True)
        return
    
    await callback_query.answer()
    
    try:
        category = await get_category(category_id)
        if not category:
            text = "❌ دسته‌بندی یافت نشد."
            await send_menu_message(client, user_id, text, message_id)
            return
        
        category_name = category['name']
        
        # Delete category
        await delete_category(category_id)
        
        set_state(user_id, BotState.CATEGORIES_LIST)
        text = f"✅ دسته‌بندی '{category_name}' با موفقیت حذف شد!\n\n📁 **دسته‌بندی‌ها**"
        await send_menu_message(client, user_id, text, message_id)
        
        # Show updated categories list
        from enhanced_bot_interface import show_categories_list
        await show_categories_list(client, user_id, message_id)
        
    except Exception as e:
        text = f"❌ خطا در حذف دسته‌بندی: {str(e)}"
        await send_menu_message(client, user_id, text, message_id)

# Users management placeholder
async def show_users_management(client: Client, user_id: int, message_id: int):
    """Show users management panel"""
    try:
        users = await full_userbase()
        
        text = f"👥 **مدیریت کاربران**\n\n"
        text += f"📊 **آمار:**\n"
        text += f"👤 تعداد کل کاربران: {len(users)}\n"
        text += f"🔧 ادمین‌ها: {len(ADMINS)}\n\n"
        text += "⚠️ **توجه:** امکانات مدیریت کاربران در نسخه‌های بعدی اضافه خواهد شد."
        
        await send_menu_message(client, user_id, text, message_id)
        
    except Exception as e:
        text = f"❌ خطا در نمایش کاربران: {str(e)}"
        await send_menu_message(client, user_id, text, message_id)