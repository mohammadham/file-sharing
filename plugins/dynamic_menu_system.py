"""
Dynamic Glass Menu System for File Sharing Bot
Creates context-sensitive bottom menus for different user states
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import asyncio
import json
import sys
import pathlib
PARENT_PATH = pathlib.Path(__file__).parent.resolve()
if PARENT_PATH not in ["",None] :
    sys.path.append(PARENT_PATH)
    from config import TEMP_PATH, CHANNEL_ID, ADMINS, APP_PATH, TG_CONFIG_FILE
    from bot import Bot
    from database.database import get_categories, get_files_by_category
else:
    from config import ADMINS

    from bot import Bot
    from database.database import get_categories, get_files_by_category

# User state storage (in production, use Redis or database)
user_states = {}

class UserState:
    """Class to manage user states"""
    MAIN_MENU = "main_menu"
    CATEGORIES = "categories" 
    CATEGORY_VIEW = "category_view"
    FILES_LIST = "files_list"
    SEARCH = "search"
    SEARCH_RESULTS = "search_results"
    UPLOADING = "uploading"
    CREATING_CATEGORY = "creating_category"
    EDITING_CATEGORY = "editing_category"
    DELETING_CATEGORY = "deleting_category"
    BROADCASTING = "broadcasting"
    FILE_MANAGEMENT = "file_management"

def set_user_state(user_id: int, state: str, data: dict = None):
    """Set user state with optional data"""
    user_states[user_id] = {
        'state': state,
        'data': data or {},
        'previous_state': user_states.get(user_id, {}).get('state'),
        'previous_data': user_states.get(user_id, {}).get('data', {})
    }

def get_user_state(user_id: int):
    """Get current user state"""
    return user_states.get(user_id, {'state': UserState.MAIN_MENU, 'data': {}})

def clear_user_state(user_id: int):
    """Clear user state"""
    if user_id in user_states:
        del user_states[user_id]

def go_back_state(user_id: int):
    """Go back to previous state"""
    current = user_states.get(user_id, {})
    if current.get('previous_state'):
        user_states[user_id] = {
            'state': current['previous_state'],
            'data': current.get('previous_data', {}),
            'previous_state': None,
            'previous_data': {}
        }
        return True
    return False

async def get_dynamic_menu(user_id: int) -> InlineKeyboardMarkup:
    """Generate dynamic menu based on user state"""
    state_info = get_user_state(user_id)
    state = state_info['state']
    data = state_info['data']
    is_admin = user_id in ADMINS
    
    keyboard = []
    
    if state == UserState.MAIN_MENU:
        # Main menu buttons
        row1 = [
            InlineKeyboardButton("📁 دسته‌بندی‌ها", callback_data="menu_categories"),
            InlineKeyboardButton("📄 فایل‌ها", callback_data="menu_files")
        ]
        row2 = [
            InlineKeyboardButton("🔍 جستجو", callback_data="menu_search")
        ]
        
        keyboard.extend([row1, row2])
        
        # Admin-only buttons
        if is_admin:
            admin_row1 = [
                InlineKeyboardButton("➕ دسته جدید", callback_data="menu_create_category"),
                InlineKeyboardButton("📤 آپلود فایل", callback_data="menu_upload")
            ]
            admin_row2 = [
                InlineKeyboardButton("📢 ارسال پیام", callback_data="menu_broadcast"),
                InlineKeyboardButton("⚙️ تنظیمات", callback_data="menu_settings")
            ]
            keyboard.extend([admin_row1, admin_row2])
    
    elif state == UserState.CATEGORIES:
        # In categories view
        keyboard.append([
            InlineKeyboardButton("🔙 منو اصلی", callback_data="menu_main"),
            InlineKeyboardButton("🔍 جستجو", callback_data="menu_search")
        ])
        if is_admin:
            keyboard.append([
                InlineKeyboardButton("➕ دسته جدید", callback_data="menu_create_category")
            ])
    
    elif state == UserState.CATEGORY_VIEW:
        # In specific category
        category_id = data.get('category_id')
        keyboard.append([
            InlineKeyboardButton("🔙 دسته‌بندی‌ها", callback_data="menu_categories"),
            InlineKeyboardButton("📄 فایل‌ها", callback_data=f"menu_category_files_{category_id}")
        ])
        keyboard.append([
            InlineKeyboardButton("🔍 جستجو در دسته", callback_data=f"menu_search_category_{category_id}")
        ])
        
        if is_admin:
            keyboard.append([
                InlineKeyboardButton("✏️ ویرایش", callback_data=f"menu_edit_category_{category_id}"),
                InlineKeyboardButton("🗑️ حذف", callback_data=f"menu_delete_category_{category_id}")
            ])
            keyboard.append([
                InlineKeyboardButton("📤 آپلود فایل", callback_data=f"menu_upload_to_{category_id}")
            ])
    
    elif state == UserState.FILES_LIST:
        # In files list
        keyboard.append([
            InlineKeyboardButton("🔙 برگشت", callback_data="menu_back"),
            InlineKeyboardButton("🔍 جستجو", callback_data="menu_search")
        ])
    
    elif state == UserState.SEARCH:
        # During search
        keyboard.append([
            InlineKeyboardButton("❌ لغو جستجو", callback_data="menu_cancel_search")
        ])
    
    elif state == UserState.SEARCH_RESULTS:
        # Search results view
        keyboard.append([
            InlineKeyboardButton("🔙 برگشت", callback_data="menu_back"),
            InlineKeyboardButton("🔍 جستجو جدید", callback_data="menu_search")
        ])
    
    elif state in [UserState.UPLOADING, UserState.CREATING_CATEGORY, 
                   UserState.EDITING_CATEGORY, UserState.BROADCASTING]:
        # During operations - only cancel button
        operation_names = {
            UserState.UPLOADING: "آپلود",
            UserState.CREATING_CATEGORY: "ایجاد دسته‌بندی", 
            UserState.EDITING_CATEGORY: "ویرایش دسته‌بندی",
            UserState.BROADCASTING: "ارسال پیام"
        }
        keyboard.append([
            InlineKeyboardButton(f"❌ لغو {operation_names.get(state, 'عملیات')}", 
                               callback_data="menu_cancel_operation")
        ])
    
    elif state == UserState.DELETING_CATEGORY:
        # During category deletion confirmation
        category_id = data.get('category_id')
        keyboard.append([
            InlineKeyboardButton("✅ تأیید حذف", callback_data=f"menu_confirm_delete_{category_id}"),
            InlineKeyboardButton("❌ انصراف", callback_data="menu_cancel_operation")
        ])
    
    else:
        # Default fallback
        keyboard.append([
            InlineKeyboardButton("🏠 منو اصلی", callback_data="menu_main")
        ])
    
    return InlineKeyboardMarkup(keyboard)

async def send_menu_message(client: Client, user_id: int, text: str, 
                           edit_message_id: int = None):
    """Send or edit menu message"""
    menu = await get_dynamic_menu(user_id)
    
    if edit_message_id:
        try:
            await client.edit_message_text(
                chat_id=user_id,
                message_id=edit_message_id,
                text=text,
                reply_markup=menu
            )
        except:
            # If edit fails, send new message
            await client.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=menu
            )
    else:
        await client.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=menu
        )

# Main menu command
@Bot.on_message(filters.private & filters.command('menu'))
async def show_main_menu(client: Client, message: Message):
    """Show main menu"""
    user_id = message.from_user.id
    set_user_state(user_id, UserState.MAIN_MENU)
    
    text = "🏠 **منو اصلی**\n\nیکی از گزینه‌های زیر را انتخاب کنید:"
    await send_menu_message(client, user_id, text)

# Menu callback handlers
@Bot.on_callback_query(filters.regex(r"^menu_"))
async def handle_menu_callbacks(client: Client, callback_query: CallbackQuery):
    """Handle all menu-related callbacks"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    message_id = callback_query.message.id
    is_admin = user_id in ADMINS
    
    try:
        await callback_query.answer()
        
        if data == "menu_main":
            set_user_state(user_id, UserState.MAIN_MENU)
            text = "🏠 **منو اصلی**\n\nیکی از گزینه‌های زیر را انتخاب کنید:"
            await send_menu_message(client, user_id, text, message_id)
            
        elif data == "menu_categories":
            set_user_state(user_id, UserState.CATEGORIES)
            await show_categories_list(client, user_id, message_id)
            
        elif data == "menu_files":
            set_user_state(user_id, UserState.FILES_LIST)
            await show_all_files(client, user_id, message_id)
            
        elif data == "menu_search":
            set_user_state(user_id, UserState.SEARCH)
            text = "🔍 **جستجو**\n\nعبارت مورد نظر خود را وارد کنید:"
            await send_menu_message(client, user_id, text, message_id)
            await start_search_process(client, user_id)
            
        elif data.startswith("menu_search_category_"):
            category_id = data.split("_")[-1]
            set_user_state(user_id, UserState.SEARCH, {'category_id': category_id})
            text = "🔍 **جستجو در دسته‌بندی**\n\nعبارت مورد نظر خود را وارد کنید:"
            await send_menu_message(client, user_id, text, message_id)
            await start_search_process(client, user_id, category_id)
            
        elif data == "menu_create_category" and is_admin:
            set_user_state(user_id, UserState.CREATING_CATEGORY)
            text = "➕ **ایجاد دسته‌بندی جدید**\n\nنام دسته‌بندی را وارد کنید:"
            await send_menu_message(client, user_id, text, message_id)
            await start_category_creation(client, user_id)
            
        elif data == "menu_upload" and is_admin:
            set_user_state(user_id, UserState.UPLOADING)
            text = "📤 **آپلود فایل**\n\nفایل مورد نظر یا لینک دانلود را ارسال کنید:"
            await send_menu_message(client, user_id, text, message_id)
            await start_upload_process(client, user_id)
            
        elif data.startswith("menu_upload_to_") and is_admin:
            category_id = data.split("_")[-1]
            set_user_state(user_id, UserState.UPLOADING, {'category_id': category_id})
            text = "📤 **آپلود به دسته‌بندی**\n\nفایل مورد نظر یا لینک دانلود را ارسال کنید:"
            await send_menu_message(client, user_id, text, message_id)
            await start_upload_process(client, user_id, category_id)
            
        elif data == "menu_broadcast" and is_admin:
            set_user_state(user_id, UserState.BROADCASTING)
            text = "📢 **ارسال پیام همگانی**\n\nپیام مورد نظر را ارسال کنید یا روی پیامی که می‌خواهید ارسال کنید Reply کنید:"
            await send_menu_message(client, user_id, text, message_id)
            await start_broadcast_process(client, user_id)
            
        elif data == "menu_cancel_operation":
            # Cancel current operation and go back
            if go_back_state(user_id):
                text = "✅ عملیات لغو شد."
            else:
                set_user_state(user_id, UserState.MAIN_MENU)
                text = "✅ عملیات لغو شد.\n\n🏠 **منو اصلی**"
            await send_menu_message(client, user_id, text, message_id)
            
        elif data == "menu_cancel_search":
            # Cancel search and go back
            if go_back_state(user_id):
                text = "❌ جستجو لغو شد."
            else:
                set_user_state(user_id, UserState.MAIN_MENU)
                text = "❌ جستجو لغو شد.\n\n🏠 **منو اصلی**"
            await send_menu_message(client, user_id, text, message_id)
            
        elif data == "menu_back":
            # Go back to previous state
            if go_back_state(user_id):
                current_state = get_user_state(user_id)
                if current_state['state'] == UserState.MAIN_MENU:
                    text = "🏠 **منو اصلی**"
                elif current_state['state'] == UserState.CATEGORIES:
                    await show_categories_list(client, user_id, message_id)
                    return
                else:
                    text = "🔙 برگشت"
            else:
                set_user_state(user_id, UserState.MAIN_MENU)
                text = "🏠 **منو اصلی**"
            await send_menu_message(client, user_id, text, message_id)
        
        # Add more handlers as needed...
        
    except Exception as e:
        await callback_query.answer(f"خطا: {str(e)}", show_alert=True)

# Helper functions for specific operations
async def show_categories_list(client: Client, user_id: int, message_id: int):
    """Show categories list"""
    try:
        categories = await get_categories()
        
        if not categories:
            text = "📁 **دسته‌بندی‌ها**\n\nهیچ دسته‌بندی وجود ندارد."
        else:
            text = f"📁 **دسته‌بندی‌ها** ({len(categories)} دسته)\n\n"
            for i, cat in enumerate(categories[:10]):  # Show first 10
                text += f"{i+1}. 📁 {cat['name']}\n"
            
            if len(categories) > 10:
                text += f"\n... و {len(categories) - 10} دسته دیگر"
        
        await send_menu_message(client, user_id, text, message_id)
        
    except Exception as e:
        text = f"❌ خطا در نمایش دسته‌بندی‌ها: {str(e)}"
        await send_menu_message(client, user_id, text, message_id)

async def show_all_files(client: Client, user_id: int, message_id: int):
    """Show all files"""
    try:
        files = await get_files_by_category(None)
        
        if not files:
            text = "📄 **فایل‌ها**\n\nهیچ فایلی وجود ندارد."
        else:
            text = f"📄 **همه فایل‌ها** ({len(files)} فایل)\n\n"
            for i, file in enumerate(files[:10]):  # Show first 10
                text += f"{i+1}. 📄 {file['original_name']}\n"
            
            if len(files) > 10:
                text += f"\n... و {len(files) - 10} فایل دیگر"
        
        await send_menu_message(client, user_id, text, message_id)
        
    except Exception as e:
        text = f"❌ خطا در نمایش فایل‌ها: {str(e)}"
        await send_menu_message(client, user_id, text, message_id)

# Placeholder functions for operations (to be implemented)
async def start_search_process(client: Client, user_id: int, category_id: str = None):
    """Start search process"""
    pass

async def start_category_creation(client: Client, user_id: int):
    """Start category creation process"""
    pass

async def start_upload_process(client: Client, user_id: int, category_id: str = None):
    """Start upload process"""
    pass

async def start_broadcast_process(client: Client, user_id: int):
    """Start broadcast process"""
    pass

# Auto-show menu for new messages (optional)
@Bot.on_message(filters.private & ~filters.command(['start', 'menu']))
async def auto_show_menu(client: Client, message: Message):
    """Auto-show menu for regular messages"""
    user_id = message.from_user.id
    current_state = get_user_state(user_id)
    
    # Only show menu if user is not in a specific operation
    if current_state['state'] == UserState.MAIN_MENU:
        await asyncio.sleep(2)  # Wait a bit
        await show_main_menu(client, message)