"""
🎨 Unified Glass Menu System for Telegram Bot
===============================================
یک سیستم منوی یکپارچه و زیبا برای ربات تلگرام

شامل:
- منوهای کامند (Command Menus) - منوهای inline داخل پیام‌ها
- منوهای شیشه‌ای (Glass Menus) - منوهای overlay برای عملیات  
- منوهای پایین (Bottom Menus) - منوهای context-sensitive

Created by: Advanced Menu System v2.0
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode
import asyncio
import time
import json
import sys
import pathlib

PARENT_PATH = pathlib.Path(__file__).parent.resolve()
sys.path.append(PARENT_PATH)

from bot import Bot
from config import ADMINS, START_MSG, OWNER_ID
from database.database import (
    get_categories, get_category, get_files_by_category, get_file,
    present_user, add_user, full_userbase
)
from helper_func import get_verify_status, update_verify_status

# ========================================================================================
# 🎯 USER STATE MANAGEMENT
# ========================================================================================

user_states = {}
user_contexts = {}  # For storing operation contexts

class MenuState:
    """States for menu system"""
    MAIN = "main"
    CATEGORIES = "categories" 
    CATEGORY_VIEW = "category_view"
    FILES = "files"
    FILE_VIEW = "file_view"
    SEARCH = "search"
    SEARCH_RESULTS = "search_results"
    
    # Operations (where cancel button is needed)
    UPLOADING = "uploading"
    CREATING_CATEGORY = "creating_category"
    EDITING_CATEGORY = "editing_category"
    DELETING_CATEGORY = "deleting_category"
    BROADCASTING = "broadcasting"

def set_user_state(user_id: int, state: str, context: dict = None):
    """Set user state and context"""
    user_states[user_id] = {
        'state': state,
        'timestamp': time.time(),
        'previous_state': user_states.get(user_id, {}).get('state', MenuState.MAIN)
    }
    if context:
        user_contexts[user_id] = context

def get_user_state(user_id: int) -> dict:
    """Get user state"""
    return user_states.get(user_id, {'state': MenuState.MAIN, 'timestamp': time.time()})

def get_user_context(user_id: int) -> dict:
    """Get user context"""
    return user_contexts.get(user_id, {})

def clear_user_data(user_id: int):
    """Clear user data"""
    if user_id in user_states:
        del user_states[user_id]
    if user_id in user_contexts:
        del user_contexts[user_id]

def go_back_to_previous_state(user_id: int):
    """Go back to previous state"""
    current = user_states.get(user_id, {})
    previous = current.get('previous_state', MenuState.MAIN)
    set_user_state(user_id, previous)
    return previous

# ========================================================================================
# 🎨 GLASS MENU CREATORS
# ========================================================================================

def create_glass_style_menu(buttons: list, style: str = "modern") -> InlineKeyboardMarkup:
    """Create beautiful glass-style menu"""
    if style == "modern":
        # Add glass effect with emojis
        styled_buttons = []
        for row in buttons:
            styled_row = []
            for button in row:
                # Add glass effect to button text
                if button.text and not button.text.startswith(('🔥', '✨', '💎', '🚀')):
                    glass_text = f"✨ {button.text}"
                else:
                    glass_text = button.text
                styled_row.append(
                    InlineKeyboardButton(glass_text, callback_data=button.callback_data)
                )
            styled_buttons.append(styled_row)
        return InlineKeyboardMarkup(styled_buttons)
    
    return InlineKeyboardMarkup(buttons)

async def create_command_menu(user_id: int, menu_type: str) -> InlineKeyboardMarkup:
    """Create command-specific inline menus (inside messages)"""
    is_admin = user_id in ADMINS
    
    if menu_type == "start":
        buttons = [
            [
                InlineKeyboardButton("🚀 Mini App", callback_data="cmd_miniapp"),
                InlineKeyboardButton("ℹ️ About Me", callback_data="cmd_about")
            ],
            [
                InlineKeyboardButton("📁 دسته‌بندی‌ها", callback_data="cmd_categories"),
                InlineKeyboardButton("📄 فایل‌ها", callback_data="cmd_files")  
            ],
            [
                InlineKeyboardButton("🔍 جستجو", callback_data="cmd_search")
            ]
        ]
        
        if is_admin:
            buttons.append([
                InlineKeyboardButton("⚙️ پنل ادمین", callback_data="cmd_admin_panel")
            ])
        
        buttons.append([
            InlineKeyboardButton("❌ بستن", callback_data="cmd_close")
        ])
        
        return create_glass_style_menu(buttons)
    
    elif menu_type == "categories":
        # Get categories for display
        categories = await get_categories()
        
        buttons = []
        
        # Show categories (max 8)
        for i, cat in enumerate(categories[:8]):
            files_count = len(await get_files_by_category(cat['id']))
            buttons.append([
                InlineKeyboardButton(
                    f"📁 {cat['name']} ({files_count})", 
                    callback_data=f"cmd_view_category_{cat['id']}"
                )
            ])
        
        if len(categories) > 8:
            buttons.append([
                InlineKeyboardButton(f"... و {len(categories) - 8} دسته دیگر", callback_data="cmd_more_categories")
            ])
        
        # Management buttons for admin
        if is_admin:
            buttons.append([
                InlineKeyboardButton("➕ دسته جدید", callback_data="cmd_create_category"),
                InlineKeyboardButton("📤 آپلود فایل", callback_data="cmd_upload")
            ])
        
        # Navigation buttons
        buttons.extend([
            [
                InlineKeyboardButton("🔍 جستجو", callback_data="cmd_search"),
                InlineKeyboardButton("🏠 خانه", callback_data="cmd_main")
            ],
            [
                InlineKeyboardButton("❌ بستن", callback_data="cmd_close")
            ]
        ])
        
        return create_glass_style_menu(buttons)
    
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ بستن", callback_data="cmd_close")]])

async def create_operation_menu(user_id: int) -> InlineKeyboardMarkup:
    """Create menu for ongoing operations (with cancel button)"""
    state_info = get_user_state(user_id)
    state = state_info['state']
    
    operation_names = {
        MenuState.UPLOADING: "آپلود فایل",
        MenuState.CREATING_CATEGORY: "ایجاد دسته‌بندی",
        MenuState.EDITING_CATEGORY: "ویرایش دسته‌بندی",
        MenuState.DELETING_CATEGORY: "حذف دسته‌بندی",
        MenuState.BROADCASTING: "ارسال پیام همگانی",
        MenuState.SEARCH: "جستجو"
    }
    
    operation_name = operation_names.get(state, "عملیات")
    
    buttons = [[
        InlineKeyboardButton(f"❌ لغو {operation_name}", callback_data="op_cancel")
    ]]
    
    return create_glass_style_menu(buttons, "modern")

async def create_context_menu(user_id: int) -> InlineKeyboardMarkup:
    """Create context-sensitive bottom menu"""
    state_info = get_user_state(user_id)
    state = state_info['state']
    context = get_user_context(user_id)
    is_admin = user_id in ADMINS
    
    buttons = []
    
    if state == MenuState.MAIN:
        # Main context menu
        buttons = [
            [
                InlineKeyboardButton("📁 دسته‌ها", callback_data="ctx_categories"),
                InlineKeyboardButton("📄 فایل‌ها", callback_data="ctx_files")
            ],
            [
                InlineKeyboardButton("🔍 جستجو", callback_data="ctx_search")
            ]
        ]
        
        if is_admin:
            buttons.append([
                InlineKeyboardButton("➕ دسته جدید", callback_data="ctx_create_category"),
                InlineKeyboardButton("📤 آپلود", callback_data="ctx_upload")
            ])
    
    elif state == MenuState.CATEGORIES:
        buttons = [
            [
                InlineKeyboardButton("🏠 خانه", callback_data="ctx_main"),
                InlineKeyboardButton("🔍 جستجو", callback_data="ctx_search")
            ]
        ]
        if is_admin:
            buttons.append([
                InlineKeyboardButton("➕ دسته جدید", callback_data="ctx_create_category")
            ])
    
    elif state == MenuState.CATEGORY_VIEW:
        category_id = context.get('category_id')
        buttons = [
            [
                InlineKeyboardButton("🔙 دسته‌ها", callback_data="ctx_categories"),
                InlineKeyboardButton("📄 فایل‌ها", callback_data=f"ctx_category_files_{category_id}")
            ],
            [
                InlineKeyboardButton("🔍 جستجو در دسته", callback_data=f"ctx_search_category_{category_id}"),
                InlineKeyboardButton("🏠 خانه", callback_data="ctx_main")
            ]
        ]
        
        if is_admin:
            buttons.append([
                InlineKeyboardButton("✏️ ویرایش", callback_data=f"ctx_edit_category_{category_id}"),
                InlineKeyboardButton("🗑️ حذف", callback_data=f"ctx_delete_category_{category_id}")
            ])
    
    # Always add back button if not in main state
    if state != MenuState.MAIN and not any("ctx_main" in str(row) for row in buttons):
        buttons.append([
            InlineKeyboardButton("🏠 منو اصلی", callback_data="ctx_main")
        ])
    
    return create_glass_style_menu(buttons, "modern")

# ========================================================================================
# 🚀 COMMAND HANDLERS
# ========================================================================================

@Bot.on_message(filters.command('start') & filters.private)
async def enhanced_start_command(client: Client, message: Message):
    """Enhanced /start command with proper menu"""
    user_id = message.from_user.id
    
    # Initialize user
    set_user_state(user_id, MenuState.MAIN)
    
    if not await present_user(user_id):
        try:
            await add_user(user_id)
        except:
            pass
    
    # Handle verification and file sharing logic (existing code)
    verify_status = await get_verify_status(user_id)
    
    # Create start menu
    menu = await create_command_menu(user_id, "start")
    
    welcome_text = f"""
🔥 **خوش آمدید {message.from_user.first_name}!**

🤖 **ربات مدیریت فایل پیشرفته**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ **امکانات:**
📁 مدیریت دسته‌بندی‌ها
📄 آپلود و دانلود فایل‌ها
🔍 جستجوی پیشرفته
🌐 Mini App تحت وب
💎 رابط کاربری شیشه‌ای

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💫 **برای شروع، یکی از گزینه‌های زیر را انتخاب کنید:**
"""
    
    await message.reply_text(
        text=welcome_text,
        reply_markup=menu,
        quote=True
    )

@Bot.on_message(filters.command('categories') & filters.private)
async def categories_command(client: Client, message: Message):
    """Enhanced /categories command"""
    user_id = message.from_user.id
    set_user_state(user_id, MenuState.CATEGORIES)
    
    categories = await get_categories()
    menu = await create_command_menu(user_id, "categories")
    
    if not categories:
        text = """
📁 **دسته‌بندی‌ها**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ **هیچ دسته‌بندی موجود نیست**

💡 ادمین‌ها می‌توانند دسته‌بندی جدید ایجاد کنند.
"""
    else:
        text = f"""
📁 **دسته‌بندی‌ها**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **آمار:** {len(categories)} دسته‌بندی موجود

💎 **برای مشاهده هر دسته، روی آن کلیک کنید:**
"""
    
    await message.reply_text(
        text=text,
        reply_markup=menu,
        quote=True
    )

@Bot.on_message(filters.command('menu') & filters.private)
async def menu_command(client: Client, message: Message):
    """Show context menu"""
    user_id = message.from_user.id
    menu = await create_context_menu(user_id)
    
    text = """
🏠 **منو اصلی**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💎 **منوی زیبای شیشه‌ای**
✨ انتخاب کنید:
"""
    
    await message.reply_text(
        text=text,
        reply_markup=menu,
        quote=True
    )

# ========================================================================================
# 🎛️ CALLBACK HANDLERS
# ========================================================================================

@Bot.on_callback_query(filters.regex(r"^cmd_"))
async def handle_command_callbacks(client: Client, callback_query: CallbackQuery):
    """Handle command menu callbacks"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    message_id = callback_query.message.id
    
    try:
        await callback_query.answer()
        
        if data == "cmd_close":
            # Close the menu message
            await client.delete_messages(user_id, message_id)
            return
        
        elif data == "cmd_main":
            set_user_state(user_id, MenuState.MAIN)
            menu = await create_command_menu(user_id, "start")
            text = "🏠 **منو اصلی**\n\n💎 یکی از گزینه‌های زیر را انتخاب کنید:"
            
        elif data == "cmd_categories":
            set_user_state(user_id, MenuState.CATEGORIES)
            menu = await create_command_menu(user_id, "categories")
            categories = await get_categories()
            text = f"📁 **دسته‌بندی‌ها**\n\n📊 {len(categories)} دسته‌بندی موجود"
            
        elif data == "cmd_about":
            text = f"""
ℹ️ **درباره ربات**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 **ربات مدیریت فایل پیشرفته**
📌 **نسخه:** 2.0 Glass Edition
👨‍💻 **توسعه‌دهنده:** <a href='tg://user?id={OWNER_ID}'>UltroidX Team</a>

✨ **امکانات:**
• 📁 سازماندهی فایل‌ها در دسته‌بندی‌ها
• 🔍 جستجوی پیشرفته و هوشمند
• 📤 آپلود فایل از لینک و مستقیم
• 💾 دانلود مستقیم و استریمینگ
• 🌐 پنل مدیریت وب (Mini App)
• 💎 رابط کاربری شیشه‌ای

🔗 **لینک‌ها:**
• 📢 کانال ما: @ultroid_official
• 💬 چت گروه: @ultroidofficial_chat
• 🎬 کانال فیلم: @MovizTube

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💫 **ساخته شده با ❤️ توسط تیم UltroidX**
"""
            menu = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 برگشت", callback_data="cmd_main")],
                [InlineKeyboardButton("❌ بستن", callback_data="cmd_close")]
            ])
        
        elif data == "cmd_miniapp":
            text = """
🚀 **Mini App ربات فایل شیرینگ**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌐 **وب اپلیکیشن پیشرفته**

💎 **امکانات Mini App:**
• 📁 مرور تمام دسته‌بندی‌ها
• 🔍 جستجوی فوری فایل‌ها  
• 💾 دانلود مستقیم فایل‌ها
• 📊 مشاهده آمار کامل
• 🎨 رابط کاربری زیبا

🚀 **برای شروع روی دکمه زیر کلیک کنید:**
"""
            menu = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 باز کردن Mini App", web_app={'url': 'http://localhost:8001/miniapp/'})],
                [InlineKeyboardButton("📱 راهنما", callback_data="cmd_miniapp_help")],
                [InlineKeyboardButton("🔙 برگشت", callback_data="cmd_main")]
            ])
        
        else:
            # Default fallback
            menu = await create_command_menu(user_id, "start")
            text = "🏠 **منو اصلی**"
        
        # Edit the message
        await client.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=text,
            reply_markup=menu,
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        await callback_query.answer(f"خطا: {str(e)}", show_alert=True)

@Bot.on_callback_query(filters.regex(r"^ctx_"))
async def handle_context_callbacks(client: Client, callback_query: CallbackQuery):
    """Handle context menu callbacks"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    try:
        await callback_query.answer("🔄 در حال پردازش...")
        
        if data == "ctx_main":
            set_user_state(user_id, MenuState.MAIN)
            text = "🏠 **منو اصلی**\n\n✨ به منو اصلی برگشتید."
            
        elif data == "ctx_categories":
            set_user_state(user_id, MenuState.CATEGORIES)
            text = "📁 **دسته‌بندی‌ها**\n\n💎 مشاهده دسته‌بندی‌ها"
            
        else:
            text = "🔧 **در حال توسعه**\n\nاین قابلیت به زودی اضافه خواهد شد."
        
        # Send new message with context menu
        menu = await create_context_menu(user_id)
        await client.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=menu
        )
        
    except Exception as e:
        await callback_query.answer(f"خطا: {str(e)}", show_alert=True)

@Bot.on_callback_query(filters.regex(r"^op_"))
async def handle_operation_callbacks(client: Client, callback_query: CallbackQuery):
    """Handle operation callbacks (cancel operations)"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if data == "op_cancel":
        # Cancel current operation
        previous_state = go_back_to_previous_state(user_id)
        clear_user_data(user_id)
        
        await callback_query.answer("✅ عملیات لغو شد.")
        
        # Send main menu
        menu = await create_context_menu(user_id)
        text = "❌ **عملیات لغو شد**\n\n🏠 به منو اصلی برگشتید."
        
        await client.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=menu
        )

# ========================================================================================
# 🧹 CLEANUP AND UTILITIES
# ========================================================================================

async def periodic_cleanup():
    """Clean up old states periodically"""
    while True:
        try:
            current_time = time.time()
            expired_users = [
                user_id for user_id, state_info in user_states.items()
                if current_time - state_info.get('timestamp', 0) > 3600  # 1 hour
            ]
            
            for user_id in expired_users:
                clear_user_data(user_id)
            
            await asyncio.sleep(1800)  # Clean every 30 minutes
        except Exception as e:
            print(f"Cleanup error: {e}")
            await asyncio.sleep(1800)

# Start cleanup task
asyncio.create_task(periodic_cleanup())

print("🎨 Unified Glass Menu System loaded successfully!")