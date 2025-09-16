# btn : about and close change here

from pyrogram import __version__
from bot import Bot
from config import OWNER_ID
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, WebAppInfo

@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data
    if data == "about":
        await query.message.edit_text(
            text = f"<b>○ ᴏᴡɴᴇʀ : <a href='tg://user?id={OWNER_ID}'>ᴍɪᴋᴇʏ</a>\n○ ᴍʏ ᴜᴘᴅᴀᴛᴇs : <a href='https://t.me/ultroid_official'>Channel</a>\n○ ᴍᴏᴠɪᴇs ᴜᴘᴅᴀᴛᴇs : <a href='https://t.me/MovizTube'>MovizTube</a>\n○ ᴏᴜʀ ᴄᴏᴍᴍᴜɴɪᴛʏ : <a href='https://t.me/ultroidofficial_chat'>Chat</a></b>",
            disable_web_page_preview = True,
            reply_markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⚡️ ᴄʟᴏsᴇ", callback_data = "close"),
                        InlineKeyboardButton('🍁 Youtube', url='https://www.youtube.com/@ultroidofficial')
                    ]
                ]
            )
        )
    elif data == "open_miniapp":
        web_app = WebAppInfo(url="http://localhost:8001/miniapp/")
        keyboard = [
            [InlineKeyboardButton("🚀 باز کردن Mini App", web_app=web_app)],
            [InlineKeyboardButton("📱 راهنما", callback_data="miniapp_help")],
            [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_start")]
        ]
        
        await query.message.edit_text(
            text="🤖 **Mini App ربات فایل شیرینگ**\n\n"
                 "از طریق Mini App می‌توانید:\n"
                 "• 📁 مرور دسته‌بندی‌ها\n"
                 "• 🔍 جستجوی فایل‌ها\n"
                 "• 💾 دانلود مستقیم فایل‌ها\n\n"
                 "برای شروع روی دکمه زیر کلیک کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif data == "miniapp_help":
        await query.message.edit_text(
            text="📱 **راهنمای Mini App**\n\n"
                 "**شروع کار:**\n"
                 "1. روی \"باز کردن Mini App\" کلیک کنید\n"
                 "2. اپلیکیشن در تلگرام باز می‌شود\n\n"
                 "**امکانات:**\n"
                 "🔍 جستجو در فایل‌ها\n"
                 "📁 مرور دسته‌بندی‌ها\n"
                 "💾 دانلود مستقیم\n"
                 "📊 مشاهده آمار",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 برگشت", callback_data="open_miniapp")]
            ])
        )
    elif data == "back_to_start":
        reply_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🚀 Mini App", callback_data="open_miniapp")],
                [InlineKeyboardButton("About Me", callback_data="about"),
                 InlineKeyboardButton("Close", callback_data="close")]
            ]
        )
        await query.message.edit_text(
            text="ʜᴇʟʟᴏ!\n\nɪ ᴀᴍ ᴍᴜʟᴛɪ ғɪʟᴇ sᴛᴏʀᴇ ʙᴏᴛ , ɪ ᴄᴀɴ sᴛᴏʀᴇ ᴘʀɪᴠᴀᴛᴇ ғɪʟᴇs ɪɴ sᴘᴇᴄɪғɪᴇᴅ ᴄʜᴀɴɴᴇʟ ᴀɴᴅ ᴏᴛʜᴇʀ ᴜsᴇʀs ᴄᴀɴ ᴀᴄᴄᴇss ɪᴛ ғʀᴏᴍ sᴘᴇᴄɪᴀʟ ʟɪɴᴋ",
            reply_markup=reply_markup
        )
    elif data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except:
            pass
