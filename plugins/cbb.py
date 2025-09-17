"""
🎛️ Legacy Callback Handler for Backward Compatibility
====================================================
Handles old callback queries that are not covered by the new unified system
"""

from pyrogram import __version__
from bot import Bot
from config import OWNER_ID
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, WebAppInfo

@Bot.on_callback_query()
async def legacy_callback_handler(client: Bot, query: CallbackQuery):
    """Handle legacy callbacks for backward compatibility"""
    data = query.data
    
    # Skip if already handled by unified system
    if data.startswith(('cmd_', 'ctx_', 'op_')):
        return
    
    if data == "about":
        await query.message.edit_text(
            text = f"""
ℹ️ **درباره ربات**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 **ربات مدیریت فایل پیشرفته**
👨‍💻 **مالک:** <a href='tg://user?id={OWNER_ID}'>Mikey</a>

🔗 **لینک‌های مفید:**
• 📢 کانال اصلی: <a href='https://t.me/ultroid_official'>Ultroid Official</a>
• 🎬 کانال فیلم: <a href='https://t.me/MovizTube'>MovizTube</a>
• 💬 چت گروه: <a href='https://t.me/ultroidofficial_chat'>Community Chat</a>
• 🍁 یوتیوب: <a href='https://www.youtube.com/@ultroidofficial'>YouTube Channel</a>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💎 **نسخه 2.0 - Glass Edition**
""",
            disable_web_page_preview = True,
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔙 برگشت", callback_data="back_to_start"),
                    InlineKeyboardButton("❌ بستن", callback_data="close")
                ]
            ])
        )
        
    elif data == "open_miniapp":
        web_app = WebAppInfo(url="http://localhost:8001/miniapp/")
        keyboard = [
            [InlineKeyboardButton("🚀 باز کردن Mini App", web_app=web_app)],
            [InlineKeyboardButton("📱 راهنما", callback_data="miniapp_help")],
            [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_start")]
        ]
        
        await query.message.edit_text(
            text="""
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
""",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    elif data == "miniapp_help":
        await query.message.edit_text(
            text="""
📱 **راهنمای Mini App**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 **شروع کار:**
1️⃣ روی "باز کردن Mini App" کلیک کنید
2️⃣ اپلیکیشن در تلگرام باز می‌شود

✨ **امکانات:**
• 🔍 جستجوی فوری در فایل‌ها
• 📁 مرور دسته‌بندی‌ها
• 💾 دانلود مستقیم فایل‌ها
• 📊 مشاهده آمار کامل
• 🎨 رابط کاربری شیشه‌ای

💡 **نکته:** Mini App تمام امکانات ربات را در یک رابط زیبا ارائه می‌دهد.
""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 برگشت", callback_data="open_miniapp")]
            ])
        )
        
    elif data == "back_to_start":
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Mini App", callback_data="open_miniapp")],
            [
                InlineKeyboardButton("ℹ️ About Me", callback_data="about"),
                InlineKeyboardButton("❌ Close", callback_data="close")
            ]
        ])
        await query.message.edit_text(
            text="""
🔥 **خوش آمدید!**

🤖 **ربات مدیریت فایل پیشرفته**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

من یک ربات پیشرفته برای ذخیره و مدیریت فایل‌ها هستم. 
می‌توانم فایل‌های خصوصی را در کانال مخصوص ذخیره کنم 
و از طریق لینک‌های ویژه به کاربران ارائه دهم.

💎 **نسخه 2.0 - Glass Edition**
✨ **با رابط کاربری شیشه‌ای**
""",
            reply_markup=reply_markup
        )
        
    elif data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except:
            pass
