#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database Migration Script - Add new category fields
"""

import asyncio
import aiosqlite
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

async def migrate_database():
    """Migrate database to add new category fields"""
    db_path = Path(__file__).parent / "bot_database.db"
    
    async with aiosqlite.connect(db_path) as db:
        try:
            # Check if new columns exist
            cursor = await db.execute("PRAGMA table_info(categories)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Add missing columns
            if 'icon' not in column_names:
                await db.execute("ALTER TABLE categories ADD COLUMN icon TEXT DEFAULT '📁'")
                print("✅ Added 'icon' column to categories table")
            
            if 'thumbnail_file_id' not in column_names:
                await db.execute("ALTER TABLE categories ADD COLUMN thumbnail_file_id TEXT DEFAULT ''")
                print("✅ Added 'thumbnail_file_id' column to categories table")
            
            if 'tags' not in column_names:
                await db.execute("ALTER TABLE categories ADD COLUMN tags TEXT DEFAULT ''")
                print("✅ Added 'tags' column to categories table")
            
            await db.commit()
            print("🎉 Database migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration error: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(migrate_database())