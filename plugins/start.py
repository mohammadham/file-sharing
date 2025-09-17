#(©)Codeflix_Bots

import logging
import base64
import random
import re
import string
import time
import asyncio

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from shortzy import Shortzy
import sys
import pathlib
PARENT_PATH = pathlib.Path(__file__).parent.resolve()
if PARENT_PATH not in ["",None] :
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

        # Import enhanced interface 
    from .enhanced_bot_interface import enhanced_start
else:
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

        # Import enhanced interface 
    from .enhanced_bot_interface import enhanced_start


# NOTE: start command for subscribed users is handled in enhanced_bot_interface to avoid duplication.
# This handler only responds to non-subscribed users to show force-join menu.
@Bot.on_message(filters.command('start') & filters.private & ~filters.user(ADMINS) & ~subscribed)
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

WAIT_MSG = "<b>ᴡᴏʀᴋɪɴɢ....</b>"

REPLY_ERROR = "<code>Use this command as a reply to any telegram message without any spaces.</code>"


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