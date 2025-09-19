#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for Telegram Bot functionality
"""

import asyncio
import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).parent / "bot_database.db"

async def test_database():
    """Test database connectivity and data"""
    print("🔍 Testing database connectivity...")
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Test categories
        cursor = await db.execute('SELECT COUNT(*) FROM categories')
        categories_count = (await cursor.fetchone())[0]
        print(f"📁 Categories: {categories_count}")
        
        # Test files
        cursor = await db.execute('SELECT COUNT(*) FROM files')
        files_count = (await cursor.fetchone())[0]
        print(f"📄 Files: {files_count}")
        
        # Test users
        cursor = await db.execute('SELECT COUNT(*) FROM user_sessions')
        users_count = (await cursor.fetchone())[0]
        print(f"👥 Users: {users_count}")
        
        # Show sample categories
        print("\n📂 Sample categories:")
        cursor = await db.execute('SELECT id, name, parent_id FROM categories LIMIT 5')
        categories = await cursor.fetchall()
        for cat in categories:
            print(f"  ID: {cat[0]}, Name: {cat[1]}, Parent: {cat[2]}")

async def test_bot_token():
    """Test bot token validity"""
    print("\n🤖 Testing bot token...")
    
    import httpx
    BOT_TOKEN = "8428725185:AAELFU6lUasbSDUvRuhTLNDBT3uEmvNruN0"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe")
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    print(f"✅ Bot is valid: @{bot_info['result']['username']}")
                else:
                    print("❌ Bot token is invalid")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Connection error: {e}")

async def main():
    """Run all tests"""
    print("🧪 Starting Telegram Bot Tests\n")
    
    await test_database()
    await test_bot_token()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())