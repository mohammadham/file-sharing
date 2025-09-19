#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bot Configuration Settings
"""

import os
from pathlib import Path

# Bot Token and Channel ID
BOT_TOKEN = "8428725185:AAELFU6lUasbSDUvRuhTLNDBT3uEmvNruN0"
STORAGE_CHANNEL_ID = -1002546879743

# Database configuration
ROOT_DIR = Path(__file__).parent.parent
DB_PATH = ROOT_DIR / "bot_database.db"
BACKUP_PATH = ROOT_DIR / "backups"

# File settings
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
SUPPORTED_FILE_TYPES = ['document', 'photo', 'video', 'audio']

# Bot limits
MAX_SEARCH_RESULTS = 10
MAX_FILES_PER_PAGE = 20
MAX_CATEGORIES_PER_PAGE = 10

# Messages
MESSAGES = {
    'welcome': """
🤖 **سلام! به ربات مدیریت فایل خوش آمدید**

این ربات امکانات زیر را ارائه می‌دهد:
• 📁 **مدیریت کامل فایل‌ها** با قابلیت حذف و ویرایش
• 📤 **آپلود و ذخیره فایل** در کانال
• 📢 **برودکست پیام** به کاربران
• 🔍 **جستجو پیشرفته** در فایل‌ها
• 🗂 **مدیریت دسته‌بندی‌ها**

برای شروع از منوی زیر استفاده کنید:
    """,
    'file_too_large': "❌ حجم فایل بیش از 50 مگابایت است!",
    'file_saved': "✅ فایل با موفقیت ذخیره شد!",
    'file_deleted': "✅ فایل با موفقیت حذف شد!",
    'category_created': "✅ دسته با موفقیت اضافه شد!",
    'category_deleted': "✅ دسته با موفقیت حذف شد!",
    'error_occurred': "❌ خطایی رخ داد! لطفا دوباره تلاش کنید.",
    'invalid_input': "❌ ورودی نامعتبر است!",
    'no_files_found': "هیچ فایلی در این دسته موجود نیست.",
    'no_results_found': "❌ هیچ نتیجه‌ای یافت نشد.",
}