"""
Mini App Management Plugin for Telegram Bot
Handles Telegram Mini App integration
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from bot import Bot
from config import ADMINS

@Bot.on_message(filters.private & filters.command('miniapp'))
async def show_miniapp(client: Client, message: Message):
    """Show Mini App to users"""
    try:
        # Create Web App button
        web_app = WebAppInfo(url="http://localhost:8001/miniapp/")
        
        keyboard = [
            [InlineKeyboardButton(
                "🚀 باز کردن اپلیکیشن", 
                web_app=web_app
            )],
            [InlineKeyboardButton(
                "📱 راهنمای استفاده", 
                callback_data="miniapp_help"
            )]
        ]
        
        text = """
🤖 **ربات فایل شیرینگ**

از طریق Mini App می‌توانید:
• 📁 مرور دسته‌بندی‌ها
• 🔍 جستجوی فایل‌ها  
• 💾 دانلود مستقیم فایل‌ها
• 📊 مشاهده آمار

برای استفاده روی دکمه زیر کلیک کنید:
        """
        
        await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
        
    except Exception as e:
        await message.reply_text(
            f"❌ خطا در بارگذاری Mini App: {str(e)}\n\nلطفاً بعداً تلاش کنید."
        )

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('adminapp'))
async def show_admin_app(client: Client, message: Message):
    """Show Admin Panel to admins"""
    try:
        keyboard = [
            [InlineKeyboardButton(
                "⚙️ پنل مدیریت", 
                url="http://localhost:8001/admin/"
            )],
            [InlineKeyboardButton(
                "📱 Mini App کاربران", 
                web_app=WebAppInfo(url="http://localhost:8001/miniapp/")
            )]
        ]
        
        text = """
👨‍💻 **پنل مدیریت ربات**

از طریق پنل ادمین می‌توانید:
• 📊 مشاهده داشبورد و آمار
• 📁 مدیریت فایل‌ها و دسته‌بندی‌ها
• 📤 آپلود فایل (مستقیم یا از URL)
• 👥 مدیریت کاربران
• ⚙️ تنظیمات سیستم
• 📋 مشاهده لاگ‌ها

**نکته:** پنل ادمین در مرورگر باز می‌شود.
        """
        
        await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
        
    except Exception as e:
        await message.reply_text(
            f"❌ خطا در بارگذاری پنل ادمین: {str(e)}\n\nلطفاً بعداً تلاش کنید."
        )

@Bot.on_callback_query(filters.regex("miniapp_help"))
async def miniapp_help(client: Client, callback_query):
    """Show Mini App help"""
    help_text = """
📱 **راهنمای استفاده از Mini App**

**شروع کار:**
1. روی دکمه "باز کردن اپلیکیشن" کلیک کنید
2. Mini App در تلگرام باز می‌شود

**امکانات:**
🔍 **جستجو:** در کادر بالا عبارت مورد نظر را تایپ کنید
📁 **دسته‌بندی‌ها:** روی هر دسته کلیک کنید تا فایل‌هایش را ببینید
💾 **دانلود:** روی دکمه دانلود کنار هر فایل کلیک کنید
🔙 **برگشت:** از دکمه برگشت برای رفتن به صفحه قبل استفاده کنید

**نکات مهم:**
• Mini App به صورت همگام با ربات کار می‌کند
• همه فایل‌ها از همان منبع ربات هستند
• برای دانلود نیاز به عضویت در کانال‌ها دارید

❓ سوال دارید؟ با پشتیبانی در ارتباط باشید.
    """
    
    await callback_query.edit_message_text(
        help_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_miniapp")]
        ])
    )

@Bot.on_callback_query(filters.regex("back_to_miniapp"))
async def back_to_miniapp(client: Client, callback_query):
    """Go back from help to main mini app message"""
    web_app = WebAppInfo(url="http://localhost:8001/miniapp/")
    
    keyboard = [
        [InlineKeyboardButton(
            "🚀 باز کردن اپلیکیشن", 
            web_app=web_app
        )],
        [InlineKeyboardButton(
            "📱 راهنمای استفاده", 
            callback_data="miniapp_help"
        )]
    ]
    
    text = """
🤖 **ربات فایل شیرینگ**

از طریق Mini App می‌توانید:
• 📁 مرور دسته‌بندی‌ها
• 🔍 جستجوی فایل‌ها  
• 💾 دانلود مستقیم فایل‌ها
• 📊 مشاهده آمار

برای استفاده روی دکمه زیر کلیک کنید:
    """
    
    await callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )