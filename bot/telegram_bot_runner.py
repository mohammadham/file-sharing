#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram Bot Runner - Runs the telegram bot as a background service
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent))

from telegram_bot import TelegramFileBot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/telegram_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def run_bot():
    """Run the telegram bot"""
    try:
        logger.info("Starting Telegram File Bot...")
        bot = TelegramFileBot()
        await bot.start_bot()
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_bot())