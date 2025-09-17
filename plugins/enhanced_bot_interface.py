"""
Enhanced Bot Interface with Glass Menu System
Complete implementation of user-friendly bot interface with context-sensitive menus
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from pyrogram.enums import ParseMode
import asyncio
import json
import uuid
import time
import sys
import pathlib

import random
import string

PARENT_PATH = pathlib.Path(__file__).parent.resolve()
if PARENT_PATH not in ["",None] :
    sys.path.append(PARENT_PATH)
    from bot import Bot
    from config import (ADMINS, FORCE_MSG,
        START_MSG,
        CUSTOM_CAPTION,
        IS_VERIFY,
        VERIFY_EXPIRE,
        SHORTLINK_API,
        SHORTLINK_URL,
        DISABLE_CHANNEL_BUTTON,
        PROTECT_CONTENT,
        TUT_VID,
        OWNER_ID,
    )
    from database.database import (
        get_categories, get_category, create_category, update_category, delete_category,
        get_files_by_category, get_file, search_files, add_file, create_file_link,
        full_userbase, present_user, add_user
    )
    from helper_func import subscribed, encode, decode, get_messages, get_shortlink, get_verify_status, update_verify_status, get_exp_time, get_readable_time
    from .category_management import get_file_emoji
else:
    from bot import Bot
    from config import (ADMINS, FORCE_MSG,
        START_MSG,
        CUSTOM_CAPTION,
        IS_VERIFY,
        VERIFY_EXPIRE,
        SHORTLINK_API,
        SHORTLINK_URL,
        DISABLE_CHANNEL_BUTTON,
        PROTECT_CONTENT,
        TUT_VID,
        OWNER_ID,
    )
    from database.database import (
        get_categories, get_category, create_category, update_category, delete_category,
        get_files_by_category, get_file, search_files, add_file, create_file_link,
        full_userbase, present_user, add_user
    )
    from helper_func import subscribed, encode, decode, get_messages, get_shortlink, get_verify_status, update_verify_status, get_exp_time, get_readable_time
    from plugins.category_management import get_file_emoji
# Enhanced user state management
user_states = {}
user_messages = {}  # Store message IDs for cleanup

class BotState:
    """Enhanced bot states"""
    MAIN = "main"
    CATEGORIES_LIST = "categories_list"
    CATEGORY_VIEW = "category_view"
    FILES_LIST = "files_list"
    FILE_VIEW = "file_view"
    SEARCH = "search"
    SEARCH_RESULTS = "search_results"
    
    # Operations
    UPLOADING = "uploading"
    CREATING_CATEGORY = "creating_category"
    EDITING_CATEGORY = "editing_category"
    DELETING_CATEGORY = "deleting_category"
    BROADCASTING = "broadcasting"
    
    # Admin states
    ADMIN_PANEL = "admin_panel"
    USER_MANAGEMENT = "user_management"

def set_state(user_id: int, state: str, data: dict = None, save_previous: bool = True):
    """Set user state with data"""
    previous = user_states.get(user_id, {}) if save_previous else {}
    user_states[user_id] = {
        'state': state,
        'data': data or {},
        'previous': previous.get('state'),
        'previous_data': previous.get('data', {}),
        'timestamp': time.time()
    }

def get_state(user_id: int):
    """Get user state"""
    return user_states.get(user_id, {'state': BotState.MAIN, 'data': {}, 'previous': None})

def clear_state(user_id: int):
    """Clear user state"""
    if user_id in user_states:
        del user_states[user_id]

def add_message_for_cleanup(user_id: int, message_id: int):
    """Add message ID for later cleanup"""
    if user_id not in user_messages:
        user_messages[user_id] = []
    user_messages[user_id].append(message_id)

async def cleanup_user_messages(client: Client, user_id: int):
    """Clean up user messages"""
    if user_id in user_messages:
        for msg_id in user_messages[user_id]:
            try:
                await client.delete_messages(user_id, msg_id)
            except:
                pass
        user_messages[user_id] = []

async def create_glass_menu(user_id: int, show_back: bool = False, 
                           custom_buttons: list = None) -> InlineKeyboardMarkup:
    """Create glass-style dynamic menu"""
    state_info = get_state(user_id)
    state = state_info['state']
    data = state_info['data']
    is_admin = user_id in ADMINS
    
    keyboard = []
    
    # Custom buttons for specific operations
    if custom_buttons:
        for button_row in custom_buttons:
            keyboard.append(button_row)
    
    # State-specific menus
    elif state == BotState.MAIN:
        # Main menu
        row1 = [
            InlineKeyboardButton("📁 دسته‌بندی‌ها", callback_data="nav_categories"),
            InlineKeyboardButton("📄 فایل‌ها", callback_data="nav_files")
        ]
        row2 = [
            InlineKeyboardButton("🔍 جستجو", callback_data="nav_search"),
            InlineKeyboardButton("ℹ️ درباره", callback_data="nav_about")
        ]
        keyboard.extend([row1, row2])
        
        if is_admin:
            admin_row1 = [
                InlineKeyboardButton("➕ دسته جدید", callback_data="admin_create_category"),
                InlineKeyboardButton("📤 آپلود", callback_data="admin_upload")
            ]
            admin_row2 = [
                InlineKeyboardButton("📢 پیام همگانی", callback_data="admin_broadcast"),
                InlineKeyboardButton("👥 کاربران", callback_data="admin_users")
            ]
            keyboard.extend([admin_row1, admin_row2])
    
    elif state == BotState.CATEGORIES_LIST:
        row1 = [
            InlineKeyboardButton("🏠 خانه", callback_data="nav_main"),
            InlineKeyboardButton("🔍 جستجو", callback_data="nav_search")
        ]
        keyboard.append(row1)
        if is_admin:
            keyboard.append([
                InlineKeyboardButton("➕ دسته جدید", callback_data="admin_create_category")
            ])
    
    elif state == BotState.CATEGORY_VIEW:
        category_id = data.get('category_id')
        category_name = data.get('category_name', 'دسته‌بندی')
        
        # Show category name as inactive button
        keyboard.append([
            InlineKeyboardButton(f"📁 {category_name}", callback_data="noop")
        ])
        
        row1 = [
            InlineKeyboardButton("🔙 دسته‌بندی‌ها", callback_data="nav_categories"),
            InlineKeyboardButton("📄 فایل‌ها", callback_data=f"nav_category_files_{category_id}")
        ]
        row2 = [
            InlineKeyboardButton("🔍 جستجو", callback_data=f"nav_search_in_{category_id}"),
            InlineKeyboardButton("🏠 خانه", callback_data="nav_main")
        ]
        keyboard.extend([row1, row2])
        
        if is_admin:
            admin_row = [
                InlineKeyboardButton("✏️ ویرایش", callback_data=f"admin_edit_category_{category_id}"),
                InlineKeyboardButton("🗑️ حذف", callback_data=f"admin_delete_category_{category_id}")
            ]
            keyboard.append(admin_row)
            keyboard.append([
                InlineKeyboardButton("📤 آپلود به دسته", callback_data=f"admin_upload_to_{category_id}")
            ])
    
    elif state == BotState.FILES_LIST:
        row1 = [
            InlineKeyboardButton("🔙 برگشت", callback_data="nav_back"),
            InlineKeyboardButton("🔍 جستجو", callback_data="nav_search")
        ]
        row2 = [
            InlineKeyboardButton("📁 دسته‌بندی‌ها", callback_data="nav_categories"),
            InlineKeyboardButton("🏠 خانه", callback_data="nav_main")
        ]
        keyboard.extend([row1, row2])
    
    elif state in [BotState.UPLOADING, BotState.CREATING_CATEGORY, 
                   BotState.EDITING_CATEGORY, BotState.BROADCASTING]:
        # During operations - only cancel
        operation_names = {
            BotState.UPLOADING: "آپلود",
            BotState.CREATING_CATEGORY: "ایجاد دسته‌بندی",
            BotState.EDITING_CATEGORY: "ویرایش دسته‌بندی", 
            BotState.BROADCASTING: "ارسال پیام"
        }
        keyboard.append([
            InlineKeyboardButton(f"❌ لغو {operation_names[state]}", callback_data="cancel_operation")
        ])
    
    elif state == BotState.SEARCH:
        keyboard.append([
            InlineKeyboardButton("❌ لغو جستجو", callback_data="cancel_operation")
        ])
    
    elif state == BotState.SEARCH_RESULTS:
        row1 = [
            InlineKeyboardButton("🔙 برگشت", callback_data="nav_back"),
            InlineKeyboardButton("🔍 جستجو جدید", callback_data="nav_search")
        ]
        keyboard.append(row1)
    
    elif state == BotState.DELETING_CATEGORY:
        category_id = data.get('category_id')
        keyboard.append([
            InlineKeyboardButton("✅ تأیید حذف", callback_data=f"confirm_delete_{category_id}"),
            InlineKeyboardButton("❌ انصراف", callback_data="cancel_operation")
        ])
    
    # Default back to main if nothing else
    if not keyboard:
        keyboard.append([
            InlineKeyboardButton("🏠 منو اصلی", callback_data="nav_main")
        ])
    
    return InlineKeyboardMarkup(keyboard)

async def send_menu_message(client: Client, user_id: int, text: str, 
                           edit_message_id: int = None, show_back: bool = False,
                           custom_buttons: list = None):
    """Send message with dynamic menu"""
    menu = await create_glass_menu(user_id, show_back, custom_buttons)
    
    try:
        if edit_message_id:
            await client.edit_message_text(
                chat_id=user_id,
                message_id=edit_message_id,
                text=text,
                reply_markup=menu
            )
        else:
            msg = await client.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=menu
            )
            add_message_for_cleanup(user_id, msg.id)
    except Exception:
        # If edit fails, send new message
        if edit_message_id:
            msg = await client.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=menu
            )
            add_message_for_cleanup(user_id, msg.id)

# Enhanced start command (with subscribed filter) - avoid duplicate handlers
@Bot.on_message(filters.command('start') & filters.private & subscribed)
async def enhanced_start(client: Client, message: Message):
    """Enhanced start command with menu"""
    user_id = message.from_user.id
    
    # Clean up any previous messages
    await cleanup_user_messages(client, user_id)
    
    # Initialize user state
    set_state(user_id, BotState.MAIN)
    
    # Check if user exists
    if not await present_user(user_id):
        try:
            await add_user(user_id)
        except:
            pass
    id = user_id
    verify_status = await get_verify_status(id)
    if verify_status['is_verified'] and VERIFY_EXPIRE < (time.time() - verify_status['verified_time']):
        await update_verify_status(id, is_verified=False)
    if "verify_" in message.text:
        _, token = message.text.split("_", 1)
        if verify_status['verify_token'] != token:
            return await message.reply("Your token is invalid or Expired. Try again by clicking /start")
        await update_verify_status(id, is_verified=True, verified_time=time.time())
        if verify_status["link"] == "":
            reply_markup = None
        await message.reply(f"Your token successfully verified and valid for: 24 Hour", reply_markup=reply_markup, protect_content=False, quote=True)
    elif len(message.text) > 7 and verify_status['is_verified']:
        try:
            base64_string = message.text.split(" ", 1)[1]
        except:
            return
        _string = await decode(base64_string)
        argument = _string.split("-")
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
            except:
                return
            if start <= end:
                ids = range(start, end+1)
            else:
                ids = []
                i = start
                while True:
                    ids.append(i)
                    i -= 1
                    if i < end:
                        break
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except:
                return
        temp_msg = await message.reply("Please wait...")
        try:
            messages = await get_messages(client, ids)
        except:
            await message.reply_text("Something went wrong..!")
            return
        await temp_msg.delete()
        
        snt_msgs = []
        
        for msg in messages:
            if bool(CUSTOM_CAPTION) & bool(msg.document):
                caption = CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html, filename=msg.document.file_name)
            else:
                caption = "" if not msg.caption else msg.caption.html
            if DISABLE_CHANNEL_BUTTON:
                reply_markup = msg.reply_markup
            else:
                reply_markup = None
            try:
                snt_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                await asyncio.sleep(0.5)
                snt_msgs.append(snt_msg)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                snt_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                snt_msgs.append(snt_msg)
            except:
                pass
        SD = await message.reply_text("Baka! Files will be deleted After 600 seconds. Save them to the Saved Message now!")
        await asyncio.sleep(600)
        for snt_msg in snt_msgs:
            try:
                await snt_msg.delete()
                await SD.delete()
            except:
                pass
    elif verify_status['is_verified']:
        reply_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🚀 Mini App", callback_data="open_miniapp")],
                [InlineKeyboardButton("About Me", callback_data="about"),
                 InlineKeyboardButton("Close", callback_data="close")]
            ]
        )
        await message.reply_text(
            text=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            quote=True
        )
    else:
        verify_status = await get_verify_status(id)
        if IS_VERIFY and not verify_status['is_verified']:
            short_url = f"api.shareus.io"
            TUT_VID = f"https://t.me/ultroid_official/18"
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            await update_verify_status(id, verify_token=token, link="")
            link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API,f'https://telegram.dog/{client.username}?start=verify_{token}')
            btn = [
                [InlineKeyboardButton("Click here", url=link)],
                [InlineKeyboardButton('How to use the bot', url=TUT_VID)]
            ]
            await message.reply(f"Your Ads token is expired, refresh your token and try again.\n\nToken Timeout: {get_exp_time(VERIFY_EXPIRE)}\n\nWhat is the token?\n\nThis is an ads token. If you pass 1 ad, you can use the bot for 24 Hour after passing the ad.", reply_markup=InlineKeyboardMarkup(btn), protect_content=False, quote=True)
    
    
    welcome_text = f"""
🤖 **خوش آمدید {message.from_user.first_name}!**

من ربات مدیریت و اشتراک فایل هستم. با استفاده از منوی زیر می‌توانید:

📁 **دسته‌بندی‌ها:** مرور فایل‌ها بر اساس دسته‌بندی
📄 **فایل‌ها:** مشاهده تمام فایل‌های موجود  
🔍 **جستجو:** جستجو در فایل‌ها
ℹ️ **درباره:** اطلاعات بیشتر درباره ربات
"""
    
    if user_id in ADMINS:
        welcome_text += "\n🔧 **امکانات ادمین:** مدیریت فایل‌ها و دسته‌بندی‌ها"
    
    await send_menu_message(client, user_id, welcome_text)

# Menu command for quick access
@Bot.on_message(filters.command('menu') & filters.private)
async def show_menu_command(client: Client, message: Message):
    """Show menu command"""
    await enhanced_start(client, message)

# Navigation callback handlers  
@Bot.on_callback_query(filters.regex(r"^nav_"))
async def handle_navigation(client: Client, callback_query: CallbackQuery):
    """Handle navigation callbacks"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    message_id = callback_query.message.id
    
    await callback_query.answer()
    
    try:
        if data == "nav_main":
            set_state(user_id, BotState.MAIN)
            text = "🏠 **منو اصلی**\n\nیکی از گزینه‌های زیر را انتخاب کنید:"
            await send_menu_message(client, user_id, text, message_id)
            
        elif data == "nav_categories":
            set_state(user_id, BotState.CATEGORIES_LIST)
            await show_categories_list(client, user_id, message_id)
            
        elif data == "nav_files":
            set_state(user_id, BotState.FILES_LIST)
            await show_files_list(client, user_id, message_id)
            
        elif data == "nav_search":
            set_state(user_id, BotState.SEARCH)
            text = "🔍 **جستجو**\n\nلطفاً عبارت مورد نظر خود را وارد کنید:"
            await send_menu_message(client, user_id, text, message_id)
            await start_search_process(client, user_id)
            
        elif data.startswith("nav_search_in_"):
            category_id = data.split("_")[-1]
            set_state(user_id, BotState.SEARCH, {'category_id': category_id})
            category = await get_category(category_id)
            cat_name = category['name'] if category else "این دسته"
            text = f"🔍 **جستجو در {cat_name}**\n\nعبارت مورد نظر خود را وارد کنید:"
            await send_menu_message(client, user_id, text, message_id)
            await start_search_process(client, user_id, category_id)
            
        elif data.startswith("nav_category_files_"):
            category_id = data.split("_")[-1]
            set_state(user_id, BotState.FILES_LIST, {'category_id': category_id})
            await show_files_list(client, user_id, message_id, category_id)
            
        elif data == "nav_back":
            # Go back to previous state
            state_info = get_state(user_id)
            previous = state_info.get('previous')
            if previous:
                set_state(user_id, previous, state_info.get('previous_data', {}), False)
                if previous == BotState.MAIN:
                    text = "🏠 **منو اصلی**"
                    await send_menu_message(client, user_id, text, message_id)
                elif previous == BotState.CATEGORIES_LIST:
                    await show_categories_list(client, user_id, message_id)
                # Add more back navigation as needed
            else:
                set_state(user_id, BotState.MAIN)
                text = "🏠 **منو اصلی**"
                await send_menu_message(client, user_id, text, message_id)
                
        elif data == "nav_about":
            text = """
ℹ️ **درباره ربات**

🤖 **ربات مدیریت فایل** 
📌 **نسخه:** 2.0
👨‍💻 **توسعه‌دهنده:** UltroidX Team

**امکانات:**
📁 سازماندهی فایل‌ها در دسته‌بندی‌ها
🔍 جستجوی پیشرفته
📤 آپلود فایل از لینک
💾 دانلود مستقیم و استریمینگ
🌐 پنل مدیریت وب

**پشتیبانی:** @ultroid_official
            """
            await send_menu_message(client, user_id, text, message_id)
            
        elif data == "noop":
            # No operation - for display-only buttons
            pass
            
    except Exception as e:
        await callback_query.answer(f"خطا: {str(e)}", show_alert=True)

# Admin callback handlers
@Bot.on_callback_query(filters.regex(r"^admin_"))
async def handle_admin_callbacks(client: Client, callback_query: CallbackQuery):
    """Handle admin callbacks"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    message_id = callback_query.message.id
    
    if user_id not in ADMINS:
        await callback_query.answer("⛔️ شما مجوز دسترسی ندارید.", show_alert=True)
        return
    
    await callback_query.answer()
    
    try:
        if data == "admin_create_category":
            set_state(user_id, BotState.CREATING_CATEGORY)
            text = "➕ **ایجاد دسته‌بندی جدید**\n\nنام دسته‌بندی را وارد کنید:"
            await send_menu_message(client, user_id, text, message_id)
            await start_category_creation(client, user_id)
            
        elif data == "admin_upload":
            set_state(user_id, BotState.UPLOADING)
            text = "📤 **آپلود فایل**\n\nفایل یا لینک دانلود را ارسال کنید:"
            await send_menu_message(client, user_id, text, message_id)
            await start_upload_process(client, user_id)
            
        elif data.startswith("admin_upload_to_"):
            category_id = data.split("_")[-1]
            set_state(user_id, BotState.UPLOADING, {'category_id': category_id})
            category = await get_category(category_id)
            cat_name = category['name'] if category else "این دسته"
            text = f"📤 **آپلود به {cat_name}**\n\nفایل یا لینک دانلود را ارسال کنید:"
            await send_menu_message(client, user_id, text, message_id)
            await start_upload_process(client, user_id, category_id)
            
        elif data == "admin_broadcast":
            set_state(user_id, BotState.BROADCASTING)
            text = "📢 **ارسال پیام همگانی**\n\nپیام مورد نظر را ارسال کنید یا روی پیام مورد نظر Reply کنید:"
            await send_menu_message(client, user_id, text, message_id)
            await start_broadcast_process(client, user_id)
            
        elif data == "admin_users":
            await show_users_management(client, user_id, message_id)
            
        elif data.startswith("admin_edit_category_"):
            category_id = data.split("_")[-1]
            set_state(user_id, BotState.EDITING_CATEGORY, {'category_id': category_id})
            category = await get_category(category_id)
            text = f"✏️ **ویرایش دسته‌بندی '{category['name']}'**\n\nنام جدید را وارد کنید (یا /skip برای رد کردن):"
            await send_menu_message(client, user_id, text, message_id)
            await start_category_editing(client, user_id, category_id)
            
        elif data.startswith("admin_delete_category_"):
            category_id = data.split("_")[-1]
            await show_delete_confirmation(client, user_id, message_id, category_id)
            
    except Exception as e:
        await callback_query.answer(f"خطا: {str(e)}", show_alert=True)

# Cancel operation handler
@Bot.on_callback_query(filters.regex(r"^cancel_operation"))
async def handle_cancel_operation(client: Client, callback_query: CallbackQuery):
    """Handle operation cancellation"""
    user_id = callback_query.from_user.id
    message_id = callback_query.message.id
    
    await callback_query.answer("✅ عملیات لغو شد.")
    
    # Go back to previous state or main menu
    state_info = get_state(user_id)
    previous = state_info.get('previous')
    
    if previous:
        set_state(user_id, previous, state_info.get('previous_data', {}), False)
    else:
        set_state(user_id, BotState.MAIN)
    
    text = "✅ عملیات لغو شد.\n\n🏠 **منو اصلی**"
    await send_menu_message(client, user_id, text, message_id)

# Show functions
async def show_categories_list(client: Client, user_id: int, message_id: int):
    """Show categories with inline buttons"""
    try:
        categories = await get_categories()
        
        if not categories:
            text = "📁 **دسته‌بندی‌ها**\n\n❌ هیچ دسته‌بندی وجود ندارد."
            await send_menu_message(client, user_id, text, message_id)
            return
        
        text = f"📁 **دسته‌بندی‌ها** ({len(categories)} دسته)\n\n"
        
        # Create buttons for categories
        category_buttons = []
        for i, cat in enumerate(categories):
            files_count = len(await get_files_by_category(cat['id']))
            text += f"{i+1}. 📁 {cat['name']} ({files_count} فایل)\n"
            
            category_buttons.append([
                InlineKeyboardButton(
                    f"📁 {cat['name']} ({files_count})",
                    callback_data=f"view_category_{cat['id']}"
                )
            ])
        
        await send_menu_message(client, user_id, text, message_id, custom_buttons=category_buttons)
        
    except Exception as e:
        text = f"❌ خطا در نمایش دسته‌بندی‌ها: {str(e)}"
        await send_menu_message(client, user_id, text, message_id)

async def show_files_list(client: Client, user_id: int, message_id: int, category_id: str = None):
    """Show files list"""
    try:
        files = await get_files_by_category(category_id)
        
        if not files:
            text = "📄 **فایل‌ها**\n\n❌ هیچ فایلی وجود ندارد."
            await send_menu_message(client, user_id, text, message_id)
            return
        
        text = f"📄 **فایل‌ها** ({len(files)} فایل)\n\n"
        
        # Create buttons for files
        file_buttons = []
        for i, file in enumerate(files[:20]):  # Show first 20
            emoji = get_file_emoji(file.get('mime_type', ''))
            size_mb = (file.get('file_size', 0) / 1024 / 1024)
            size_text = f" ({size_mb:.1f}MB)" if size_mb > 0 else ""
            
            text += f"{i+1}. {emoji} {file['original_name']}{size_text}\n"
            
            file_buttons.append([
                InlineKeyboardButton(
                    f"{emoji} {file['original_name'][:40]}{'...' if len(file['original_name']) > 40 else ''}",
                    callback_data=f"view_file_{file['id']}"
                )
            ])
        
        if len(files) > 20:
            text += f"\n... و {len(files) - 20} فایل دیگر"
        
        await send_menu_message(client, user_id, text, message_id, custom_buttons=file_buttons)
        
    except Exception as e:
        text = f"❌ خطا در نمایش فایل‌ها: {str(e)}"
        await send_menu_message(client, user_id, text, message_id)

# Category view handler
@Bot.on_callback_query(filters.regex(r"^view_category_"))
async def handle_view_category(client: Client, callback_query: CallbackQuery):
    """Handle category view"""
    category_id = callback_query.data.split("_")[-1]
    user_id = callback_query.from_user.id
    message_id = callback_query.message.id
    
    await callback_query.answer()
    
    try:
        category = await get_category(category_id)
        if not category:
            await callback_query.answer("دسته‌بندی یافت نشد!", show_alert=True)
            return
        
        # Set state
        set_state(user_id, BotState.CATEGORY_VIEW, {
            'category_id': category_id,
            'category_name': category['name']
        })
        
        # Get category info
        files = await get_files_by_category(category_id)
        subcategories = await get_categories(category_id)
        
        text = f"📁 **{category['name']}**\n\n"
        if category['description']:
            text += f"📝 {category['description']}\n\n"
        
        text += f"📊 **آمار:**\n"
        text += f"📄 فایل‌ها: {len(files)}\n"
        text += f"📁 زیردسته‌ها: {len(subcategories)}\n"
        
        if files:
            text += f"\n📄 **فایل‌های اخیر:**\n"
            for i, file in enumerate(files[:5]):
                emoji = get_file_emoji(file.get('mime_type', ''))
                text += f"{i+1}. {emoji} {file['original_name']}\n"
            
            if len(files) > 5:
                text += f"... و {len(files) - 5} فایل دیگر"
        
        await send_menu_message(client, user_id, text, message_id)
        
    except Exception as e:
        await callback_query.answer(f"خطا: {str(e)}", show_alert=True)

# File view handler
@Bot.on_callback_query(filters.regex(r"^view_file_"))
async def handle_view_file(client: Client, callback_query: CallbackQuery):
    """Handle file view and download"""
    file_id = callback_query.data.split("_")[-1]
    user_id = callback_query.from_user.id
    
    await callback_query.answer()
    
    try:
        file_info = await get_file(file_id)
        if not file_info:
            await callback_query.answer("فایل یافت نشد!", show_alert=True)
            return
        
        # Generate download links
        stream_code = str(uuid.uuid4())
        download_code = str(uuid.uuid4())
        
        await create_file_link(file_id, "stream", stream_code)
        await create_file_link(file_id, "download", download_code)
        
        emoji = get_file_emoji(file_info.get('mime_type', ''))
        size_mb = (file_info.get('file_size', 0) / 1024 / 1024)
        
        text = f"{emoji} **{file_info['original_name']}**\n\n"
        text += f"📏 **حجم:** {size_mb:.2f} MB\n"
        text += f"📅 **تاریخ:** {file_info['created_at'][:10]}\n"
        
        if file_info.get('description'):
            text += f"📝 **توضیحات:** {file_info['description']}\n"
        
        text += f"\n🔗 **لینک‌های دانلود:**\n"
        text += f"• استریم: `/stream_{stream_code}`\n"
        text += f"• دانلود: `/download_{download_code}`"
        
        # Create download buttons
        download_buttons = [[
            InlineKeyboardButton("📥 دانلود مستقیم", callback_data=f"download_{download_code}"),
            InlineKeyboardButton("🎬 پخش آنلاین", callback_data=f"stream_{stream_code}")
        ]]
        
        await send_menu_message(client, user_id, text, callback_query.message.id, 
                               custom_buttons=download_buttons)
        
    except Exception as e:
        await callback_query.answer(f"خطا: {str(e)}", show_alert=True)

# ===== Bridge to real implementations to avoid circular imports =====
async def start_search_process(client: Client, user_id: int, category_id: str = None):
    from .bot_operations import start_search_process as impl
    return await impl(client, user_id, category_id)

async def start_category_creation(client: Client, user_id: int):
    from .bot_operations import start_category_creation as impl
    return await impl(client, user_id)

async def start_upload_process(client: Client, user_id: int, category_id: str = None):
    from .bot_operations import start_upload_process as impl
    return await impl(client, user_id, category_id)

async def start_broadcast_process(client: Client, user_id: int):
    from .bot_operations import start_broadcast_process as impl
    return await impl(client, user_id)

async def start_category_editing(client: Client, user_id: int, category_id: str):
    from .bot_operations import start_category_editing as impl
    return await impl(client, user_id, category_id)

async def show_delete_confirmation(client: Client, user_id: int, message_id: int, category_id: str):
    from .bot_operations import show_delete_confirmation as impl
    return await impl(client, user_id, message_id, category_id)

async def show_users_management(client: Client, user_id: int, message_id: int):
    from .bot_operations import show_users_management as impl
    return await impl(client, user_id, message_id)

# Message handler for cleanup and state management
@Bot.on_message(filters.private & ~filters.command(['start', 'menu']) & ~filters.media)
async def handle_user_messages(client: Client, message: Message):
    """Handle user messages and manage state"""
    user_id = message.from_user.id
    state_info = get_state(user_id)
    state = state_info['state']
    
    # Only process messages if user is in an interactive state
    if state in [BotState.SEARCH, BotState.CREATING_CATEGORY, 
                 BotState.EDITING_CATEGORY, BotState.UPLOADING, BotState.BROADCASTING]:
        # Let the operation handlers deal with these messages
        return
    
    # For other states, show menu after a short delay
    if state == BotState.MAIN:
        await asyncio.sleep(1)
        await send_menu_message(client, user_id, "🏠 **منو اصلی**\n\nیکی از گزینه‌های زیر را انتخاب کنید:")

# Clean up messages periodically (runs every hour)
async def periodic_cleanup():
    """Periodic cleanup of old messages"""
    while True:
        try:
            current_time = time.time()
            cleanup_users = []
            
            for user_id, state_info in user_states.items():
                # Clean up states older than 1 hour
                if current_time - state_info.get('timestamp', 0) > 3600:
                    cleanup_users.append(user_id)
            
            for user_id in cleanup_users:
                clear_state(user_id)
                if user_id in user_messages:
                    del user_messages[user_id]
            
            await asyncio.sleep(3600)  # Wait 1 hour
        except Exception as e:
            print(f"Cleanup error: {e}")
            await asyncio.sleep(3600)