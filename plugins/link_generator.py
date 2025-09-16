#(©)Codeflix_Bots

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from config import ADMINS
from helper_func import encode, get_message_id
from database.database import add_file, create_file_link, get_files_by_category
import uuid

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('batch'))
async def batch(client: Client, message: Message):
    while True:
        try:
            first_message = await client.ask(text = "𝐅𝐨𝐫𝐰𝐚𝐫𝐝 𝐭𝐡𝐞 𝐅𝐢𝐫𝐬𝐭 𝐌𝐞𝐬𝐬𝐚𝐠𝐞 𝐟𝐫𝐨𝐦 𝐃𝐚𝐭𝐚𝐛𝐚𝐬𝐞 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 (with Quotes)..\n\n𝐨𝐫 𝐒𝐞𝐧𝐝 𝐭𝐡𝐞 𝐃𝐚𝐭𝐚𝐛𝐚𝐬𝐞 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 𝐏𝐨𝐬𝐭 𝐥𝐢𝐧𝐤", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except:
            return
        f_msg_id = await get_message_id(client, first_message)
        if f_msg_id:
            break
        else:
            await first_message.reply("❌ Error\n\n𝐈𝐭𝐬 𝐧𝐨𝐭 𝐅𝐫𝐨𝐦 𝐃𝐚𝐭𝐚𝐛𝐚𝐬𝐞 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 𝐃𝐮𝐝𝐞 𝐂𝐡𝐞𝐜𝐤 𝐀𝐠𝐚𝐢𝐧..!", quote = True)
            continue

    while True:
        try:
            second_message = await client.ask(text = "𝐅𝐨𝐫𝐰𝐚𝐫𝐝 𝐭𝐡𝐞 𝐋𝐚𝐬𝐭 𝐌𝐞𝐬𝐬𝐚𝐠𝐞 𝐟𝐫𝐨𝐦 𝐃𝐚𝐭𝐚𝐛𝐚𝐬𝐞 𝐂𝐡𝐚𝐧𝐧𝐞𝐥..! (with Quotes)..\n𝐨𝐫 𝐒𝐞𝐧𝐝 𝐭𝐡𝐞 𝐃𝐚𝐭𝐚𝐛𝐚𝐬𝐞 𝐂𝐡𝐚𝐧𝐧𝐞𝐝 𝐏𝐨𝐬𝐭 𝐥𝐢𝐧𝐤", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except:
            return
        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        else:
            await second_message.reply("❌ Error\n\n𝐈𝐭𝐬 𝐧𝐨𝐭 𝐅𝐫𝐨𝐦 𝐃𝐚𝐭𝐚𝐛𝐚𝐬𝐞 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 𝐃𝐮𝐝𝐞 𝐂𝐡𝐞𝐜𝐤 𝐀𝐠𝐚𝐢𝐧..!", quote = True)
            continue


    string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
    base64_string = await encode(string)
    link = f"https://telegram.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await second_message.reply_text(f"<b>Here is your link</b>\n\n{link}", quote=True, reply_markup=reply_markup)


@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    while True:
        try:
            channel_message = await client.ask(text = "𝐅𝐨𝐫𝐰𝐚𝐫𝐝 𝐌𝐞𝐬𝐬𝐚𝐠𝐞 𝐟𝐫𝐨𝐦 𝐃𝐚𝐭𝐚𝐛𝐚𝐬𝐞 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 (with Quotes)..\n𝐨𝐫 𝐒𝐞𝐧𝐝 𝐭𝐡𝐞 𝐃𝐚𝐭𝐚𝐛𝐚𝐬𝐞 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 𝐏𝐨𝐬𝐭 𝐥𝐢𝐧𝐤", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except:
            return
        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        else:
            await channel_message.reply("❌ Error\n\n𝐈𝐭𝐬 𝐧𝐨𝐭 𝐅𝐫𝐨𝐦 𝐃𝐚𝐭𝐚𝐛𝐚𝐬𝐞 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 𝐃𝐮𝐝𝐞 𝐂𝐡𝐞𝐜𝐤 𝐀𝐠𝐚𝐢𝐧..!", quote = True)
            continue

    base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
    link = f"https://telegram.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await channel_message.reply_text(f"<b>Here is your link</b>\n\n{link}", quote=True, reply_markup=reply_markup)

# New streaming link generator
@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('streamlink'))
async def generate_stream_link(client: Client, message: Message):
    """Generate streaming download links for files"""
    try:
        channel_message = await client.ask(
            text="📤 Forward a message from Database Channel to generate streaming links\n\nیا پیام را از کانال دیتابیس forward کنید",
            chat_id=message.from_user.id,
            filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
            timeout=60
        )
        
        msg_id = await get_message_id(client, channel_message)
        if not msg_id:
            await channel_message.reply("❌ Error\n\nپیام از کانال دیتابیس نیست!")
            return
        
        # Get file info from the message
        if channel_message.document:
            file_info = channel_message.document
            file_name = file_info.file_name or f"file_{msg_id}"
            file_size = file_info.file_size
            mime_type = file_info.mime_type
        elif channel_message.photo:
            file_info = channel_message.photo
            file_name = f"photo_{msg_id}.jpg"
            file_size = file_info.file_size
            mime_type = "image/jpeg"
        elif channel_message.video:
            file_info = channel_message.video
            file_name = file_info.file_name or f"video_{msg_id}.mp4"
            file_size = file_info.file_size
            mime_type = file_info.mime_type
        elif channel_message.audio:
            file_info = channel_message.audio
            file_name = file_info.file_name or f"audio_{msg_id}.mp3"
            file_size = file_info.file_size
            mime_type = file_info.mime_type
        else:
            await channel_message.reply("❌ This message doesn't contain a downloadable file!")
            return
        
        # Add file to database if not exists
        try:
            file_id = await add_file(
                original_name=file_name,
                file_name=file_name,
                message_id=msg_id,
                chat_id=str(client.db_channel.id),
                file_size=file_size,
                mime_type=mime_type or "",
                uploaded_by=message.from_user.id
            )
        except Exception as e:
            # File might already exist, that's okay
            file_id = str(uuid.uuid4())
        
        # Generate streaming links
        stream_code = str(uuid.uuid4())
        download_code = str(uuid.uuid4())
        
        await create_file_link(file_id, "stream", stream_code)
        await create_file_link(file_id, "download", download_code)
        
        # Create response with both traditional and streaming links
        traditional_link = f"https://telegram.me/{client.username}?start={await encode(f'get-{msg_id * abs(client.db_channel.id)}')}"
        stream_link = f"https://your-domain.com/stream/{stream_code}"
        download_link = f"https://your-domain.com/download/{download_code}"
        
        text = f"🔗 **Download Links Generated**\n\n"
        text += f"📄 **File:** `{file_name}`\n"
        text += f"📏 **Size:** {file_size / (1024*1024):.2f} MB\n\n"
        text += f"**Traditional Link (Telegram Bot):**\n{traditional_link}\n\n"
        text += f"**🎬 Direct Stream Link:**\n`{stream_link}`\n\n"
        text += f"**💾 Download Link:**\n`{download_link}`"
        
        keyboard = [
            [
                InlineKeyboardButton("📥 Stream Direct", url=stream_link),
                InlineKeyboardButton("💾 Download", url=download_link)
            ],
            [
                InlineKeyboardButton("🔗 Traditional Link", url=traditional_link)
            ],
            [
                InlineKeyboardButton("🔁 Share Stream", url=f'https://telegram.me/share/url?url={stream_link}'),
                InlineKeyboardButton("🔁 Share Download", url=f'https://telegram.me/share/url?url={download_link}')
            ]
        ]
        
        await channel_message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            quote=True
        )
        
    except Exception as e:
        await message.reply(f"❌ Error generating links: {str(e)}")

# Generate category-based links
@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('category_links'))
async def generate_category_links(client: Client, message: Message):
    """Generate download links for all files in a category"""
    try:
        from database.database import get_categories
        
        categories = await get_categories()
        if not categories:
            await message.reply("❌ No categories found. Create categories first using /categories")
            return
        
        keyboard = []
        for category in categories[:10]:  # Show max 10 categories
            keyboard.append([
                InlineKeyboardButton(
                    f"📁 {category['name']}",
                    callback_data=f"gen_cat_links_{category['id']}"
                )
            ])
        
        await message.reply(
            "📁 **Select Category to Generate Links**\n\nChoose a category to generate download links for all files:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@Bot.on_callback_query(filters.regex(r"^gen_cat_links_"))
async def handle_category_link_generation(client: Client, callback_query):
    """Handle category link generation"""
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("Access denied!", show_alert=True)
        return
    
    category_id = callback_query.data.split("_", 3)[3]
    
    try:
        files = await get_files_by_category(category_id)
        
        if not files:
            await callback_query.answer("No files in this category!", show_alert=True)
            return
        
        await callback_query.answer()
        
        status_msg = await client.send_message(
            callback_query.from_user.id,
            f"⏳ Generating links for {len(files)} files..."
        )
        
        links_text = "🔗 **Category Download Links**\n\n"
        
        for i, file in enumerate(files[:50]):  # Max 50 files
            # Generate new links for each file
            stream_code = str(uuid.uuid4())
            download_code = str(uuid.uuid4())
            
            await create_file_link(file['id'], "stream", stream_code)
            await create_file_link(file['id'], "download", download_code)
            
            stream_link = f"https://your-domain.com/stream/{stream_code}"
            download_link = f"https://your-domain.com/download/{download_code}"
            
            links_text += f"**{i+1}. {file['original_name']}**\n"
            links_text += f"Stream: `{stream_link}`\n"
            links_text += f"Download: `{download_link}`\n\n"
            
            if len(links_text) > 3500:  # Telegram message limit
                await client.send_message(callback_query.from_user.id, links_text)
                links_text = ""
        
        if links_text:
            await client.send_message(callback_query.from_user.id, links_text)
        
        await status_msg.delete()
        
    except Exception as e:
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)