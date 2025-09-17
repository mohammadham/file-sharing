"""
🚀 Start Command Handler - Integrated with Unified Menu System
=============================================================
Enhanced start command with proper file sharing and verification logic
"""

import logging
import base64
import random
import re
import string
import time
import asyncio

from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from shortzy import Shortzy
import sys
import pathlib

PARENT_PATH = pathlib.Path(__file__).parent.resolve()
sys.path.append(PARENT_PATH)

from bot import Bot
from config import (
    ADMINS,
    FORCE_MSG,
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
from helper_func import subscribed, encode, decode, get_messages, get_shortlink, get_verify_status, update_verify_status, get_exp_time
from database.database import add_user, del_user, full_userbase, present_user

# Import our unified menu system
from .unified_menu_system import create_command_menu, set_user_state, MenuState

@Bot.on_message(filters.command('start') & filters.private & subscribed)
async def start_command_subscribed(client: Client, message: Message):
    """Enhanced start command for subscribed users with file sharing logic"""
    user_id = message.from_user.id
    
    # Initialize user state
    set_user_state(user_id, MenuState.MAIN)
    
    # Check if user exists in database
    if not await present_user(user_id):
        try:
            await add_user(user_id)
        except:
            pass
    
    # Handle verification and file sharing logic
    verify_status = await get_verify_status(user_id)
    
    # Check if verification is expired
    if verify_status['is_verified'] and VERIFY_EXPIRE < (time.time() - verify_status['verified_time']):
        await update_verify_status(user_id, is_verified=False)
    
    # Handle verification token
    if "verify_" in message.text:
        _, token = message.text.split("_", 1)
        if verify_status['verify_token'] != token:
            return await message.reply("Your token is invalid or Expired. Try again by clicking /start")
        await update_verify_status(user_id, is_verified=True, verified_time=time.time())
        await message.reply(f"✅ Your token successfully verified and valid for: 24 Hour", protect_content=False, quote=True)
        return
    
    # Handle file sharing (existing logic)
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
        
        temp_msg = await message.reply("🔄 Please wait...")
        try:
            messages = await get_messages(client, ids)
        except:
            await message.reply_text("❌ Something went wrong..!")
            return
        await temp_msg.delete()
        
        snt_msgs = []
        
        for msg in messages:
            if bool(CUSTOM_CAPTION) & bool(msg.document):
                caption = CUSTOM_CAPTION.format(
                    previouscaption="" if not msg.caption else msg.caption.html, 
                    filename=msg.document.file_name
                )
            else:
                caption = "" if not msg.caption else msg.caption.html
            
            if DISABLE_CHANNEL_BUTTON:
                reply_markup = msg.reply_markup
            else:
                reply_markup = None
            
            try:
                snt_msg = await msg.copy(
                    chat_id=message.from_user.id, 
                    caption=caption, 
                    parse_mode=ParseMode.HTML, 
                    reply_markup=reply_markup, 
                    protect_content=PROTECT_CONTENT
                )
                await asyncio.sleep(0.5)
                snt_msgs.append(snt_msg)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                snt_msg = await msg.copy(
                    chat_id=message.from_user.id, 
                    caption=caption, 
                    parse_mode=ParseMode.HTML, 
                    reply_markup=reply_markup, 
                    protect_content=PROTECT_CONTENT
                )
                snt_msgs.append(snt_msg)
            except:
                pass
        
        # Auto-delete files after 10 minutes
        SD = await message.reply_text("⚠️ Files will be deleted after 600 seconds. Save them to Saved Messages now!")
        await asyncio.sleep(600)
        for snt_msg in snt_msgs:
            try:
                await snt_msg.delete()
                await SD.delete()
            except:
                pass
        return
    
    # Handle verified users - show enhanced menu
    elif verify_status['is_verified']:
        menu = await create_command_menu(user_id, "start")
        
        welcome_text = f"""
🔥 **خوش آمدید {message.from_user.first_name}!**

🤖 **ربات مدیریت فایل پیشرفته**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ **امکانات کامل:**
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
        return
    
    # Handle unverified users - show verification
    else:
        if IS_VERIFY and not verify_status['is_verified']:
            TUT_VID = f"https://t.me/ultroid_official/18"
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            await update_verify_status(user_id, verify_token=token, link="")
            link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, f'https://telegram.dog/{client.username}?start=verify_{token}')
            
            btn = [
                [InlineKeyboardButton("✅ Click here to verify", url=link)],
                [InlineKeyboardButton('❓ How to use the bot', url=TUT_VID)]
            ]
            
            await message.reply(
                f"""
🔐 **Verification Required**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your ads token is expired, refresh your token and try again.

⏰ **Token Timeout:** {get_exp_time(VERIFY_EXPIRE)}

❓ **What is the token?**
This is an ads token. If you pass 1 ad, you can use the bot for 24 hours after passing the ad.

💡 After verification, you'll get access to all premium features!
""", 
                reply_markup=InlineKeyboardMarkup(btn), 
                protect_content=False, 
                quote=True
            )
            return

@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    """Handle users who haven't joined required channels"""
    buttons = []
    
    # Add channel join buttons
    if hasattr(client, 'invitelink') and client.invitelink:
        buttons.append([InlineKeyboardButton("• ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ •", url=client.invitelink)])
    
    if hasattr(client, 'invitelink2') and client.invitelink2:
        buttons.append([InlineKeyboardButton("• ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=client.invitelink2)])
    
    if hasattr(client, 'invitelink3') and client.invitelink3:
        buttons.append([InlineKeyboardButton("ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ •", url=client.invitelink3)])
    
    # Add try again button
    try:
        buttons.append([
            InlineKeyboardButton(
                '• ɴᴏᴡ ᴄʟɪᴄᴋ ʜᴇʀᴇ •',
                url = f"https://t.me/{client.username}?start={message.command[1] if len(message.command) > 1 else ''}"
            )
        ])
    except IndexError:
        buttons.append([
            InlineKeyboardButton(
                '• ɴᴏᴡ ᴄʟɪᴄᴋ ʜᴇʀᴇ •',
                url = f"https://t.me/{client.username}?start="
            )
        ])

    await message.reply(
        text = FORCE_MSG.format(
                first = message.from_user.first_name,
                last = message.from_user.last_name,
                username = None if not message.from_user.username else '@' + message.from_user.username,
                mention = message.from_user.mention,
                id = message.from_user.id
            ),
        reply_markup = InlineKeyboardMarkup(buttons),
        quote = True,
        disable_web_page_preview = True
    )

# Admin commands
WAIT_MSG = "<b>ᴡᴏʀᴋɪɴɢ....</b>"
REPLY_ERROR = "<code>Use this command as a reply to any telegram message without any spaces.</code>"

@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await full_userbase()
    await msg.edit(f"📊 **آمار کاربران**\n\n👥 {len(users)} کاربر از ربات استفاده می‌کنند")

@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        
        pls_wait = await message.reply("📢 **شروع ارسال پیام همگانی...**\n\n⏳ لطفاً صبر کنید...")
        
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except Exception as e:
                unsuccessful += 1
                logging.error(f"Broadcast Error: {e}")
            total += 1
        
        status = f"""
✅ **ارسال پیام همگانی تکمیل شد!**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **نتایج:**
👥 کل کاربران: <code>{total}</code>
✅ موفق: <code>{successful}</code>
🚫 مسدود شده: <code>{blocked}</code>
🗑️ حذف شده: <code>{deleted}</code>
❌ ناموفق: <code>{unsuccessful}</code>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💫 **پیام به همه کاربران ارسال شد!**
"""
        
        return await pls_wait.edit(status)

    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()


WAIT_MSG = "<b>ᴡᴏʀᴋɪɴɢ....</b>"

REPLY_ERROR = "<code>Use this command as a reply to any telegram message without any spaces.</code>"


@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    buttons = [
        [
            InlineKeyboardButton(text="• ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=client.invitelink2),
            InlineKeyboardButton(text="ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ •", url=client.invitelink3),
        ],
        [
            InlineKeyboardButton(text="• ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ •", url=client.invitelink),
        ]
    ]
    try:
        buttons.append(
            [
                InlineKeyboardButton(
                    text = '• ɴᴏᴡ ᴄʟɪᴄᴋ ʜᴇʀᴇ •',
                    url = f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ]
        )
    except IndexError:
        pass

    await message.reply(
        text = FORCE_MSG.format(
                first = message.from_user.first_name,
                last = message.from_user.last_name,
                username = None if not message.from_user.username else '@' + message.from_user.username,
                mention = message.from_user.mention,
                id = message.from_user.id
            ),
        reply_markup = InlineKeyboardMarkup(buttons),
        quote = True,
        disable_web_page_preview = True
    )

@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await full_userbase()
    await msg.edit(f"{len(users)} ᴜꜱᴇʀꜱ ᴀʀᴇ ᴜꜱɪɴɢ ᴛʜɪꜱ ʙᴏᴛ")

@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        
        pls_wait = await message.reply("<i>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴘʀᴏᴄᴇꜱꜱɪɴɢ ᴛɪʟʟ ᴡᴀɪᴛ ʙʀᴏᴏ... </i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except Exception as e:
                unsuccessful += 1
                logging.error(f"Broadcast Error: {e}")
            total += 1
        
        status = f"""<b><u>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ᴍʏ sᴇɴᴘᴀɪ!!</u>

ᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ: <code>{total}</code>
ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ: <code>{successful}</code>
ʙʟᴏᴄᴋᴇᴅ ᴜꜱᴇʀꜱ: <code>{blocked}</code>
ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛꜱ: <code>{deleted}</code>
ᴜɴꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ: <code>{unsuccessful}</code></b></b>"""
        
        return await pls_wait.edit(status)

    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()
