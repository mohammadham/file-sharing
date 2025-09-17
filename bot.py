#(©)MohammadHam Bots

from aiohttp import web
from plugins import web_server

import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
from datetime import datetime
import os

from config import API_HASH, APP_ID, LOGGER, TG_BOT_TOKEN, TG_BOT_WORKERS, FORCESUB_CHANNEL, FORCESUB_CHANNEL2, FORCESUB_CHANNEL3, CHANNEL_ID, PORT, USE_SQLITE, APP_PATH
import pyrogram.utils

# APP_PATH = os.getenv("APP_PATH", "/app")
pyrogram.utils.MIN_CHAT_ID = -999999999999
pyrogram.utils.MIN_CHANNEL_ID = -100999999999999

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={
                "root": "plugins"
            },
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()

        # Initialize database
        if USE_SQLITE:
            try:
                from database.sqlite_database import db
                self.LOGGER(__name__).info("✅ SQLite database initialized successfully")
            except Exception as e:
                self.LOGGER(__name__).error(f"❌ SQLite database initialization failed: {e}")
        else:
            self.LOGGER(__name__).info("📊 Using MongoDB database")

        if FORCESUB_CHANNEL and FORCESUB_CHANNEL != 0:
            try:
                link = (await self.get_chat(FORCESUB_CHANNEL)).invite_link
                if not link:
                    await self.export_chat_invite_link(FORCESUB_CHANNEL)
                    link = (await self.get_chat(FORCESUB_CHANNEL)).invite_link
                self.invitelink = link
            except Exception as a:
                self.LOGGER(__name__).warning(f"Force Sub Channel 1 not accessible: {a}")
                self.invitelink = ""
                
        if FORCESUB_CHANNEL2 and FORCESUB_CHANNEL2 != 0:
            try:
                link = (await self.get_chat(FORCESUB_CHANNEL2)).invite_link
                if not link:
                    await self.export_chat_invite_link(FORCESUB_CHANNEL2)
                    link = (await self.get_chat(FORCESUB_CHANNEL2)).invite_link
                self.invitelink2 = link
            except Exception as a:
                self.LOGGER(__name__).warning(f"Force Sub Channel 2 not accessible: {a}")
                self.invitelink2 = ""
                
        if FORCESUB_CHANNEL3 and FORCESUB_CHANNEL3 != 0:
            try:
                link = (await self.get_chat(FORCESUB_CHANNEL3)).invite_link
                if not link:
                    await self.export_chat_invite_link(FORCESUB_CHANNEL3)
                    link = (await self.get_chat(FORCESUB_CHANNEL3)).invite_link
                self.invitelink3 = link
            except Exception as a:
                self.LOGGER(__name__).warning(f"Force Sub Channel 3 not accessible: {a}")
                self.invitelink3 = ""
        try:
            db_channel = await self.get_chat(CHANNEL_ID)
            self.db_channel = db_channel
            test = await self.send_message(chat_id = db_channel.id, text = "Test Message")
            await test.delete()
        except Exception as e:
            self.LOGGER(__name__).warning(e)
            self.LOGGER(__name__).warning(f"Make Sure bot is Admin in DB Channel, and Double check the CHANNEL_ID Value, Current Value {CHANNEL_ID}")
            self.LOGGER(__name__).info("\nBot Stopped. Join https://t.me/ultroid_official for support")
            sys.exit()

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info(f"Bot Running..!\n\nCreated by \nhttps://t.me/ultroid_official")
        self.LOGGER(__name__).info(f""" \n\n       
🚀 File-Sharing Bot v2.0 🚀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Bot Status: Running
📊 Database: {"SQLite" if USE_SQLITE else "MongoDB"}
📁 Categories: Enabled
🎬 Streaming: Enabled
🔗 Link Generation: Enhanced
🌐 Web Server: Integrated
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                          """)
        self.username = usr_bot_me.username

        # Create necessary directories
        os.makedirs(APP_PATH + "/data", exist_ok=True)
        os.makedirs(APP_PATH + "/temp", exist_ok=True)
        
        #web-response
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()
        
        self.LOGGER(__name__).info(f"🌐 Web server started on http://{bind_address}:{PORT}")
        self.LOGGER(__name__).info(f"📡 API server starting on http://localhost:8000")

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")
