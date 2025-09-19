# 🤖 ربات مدیریت فایل تلگرام - نسخه مدولار

## 📋 معرفی

این نسخه بهبود یافته و مدولار شده ربات مدیریت فایل تلگرام است که با ساختار منظم و قابلیت‌های پیشرفته ارائه می‌شود.

## 🏗 ساختار پروژه

```
/app/bot/
├── 📁 config/                  # تنظیمات و پیکربندی
│   ├── settings.py            # تنظیمات اصلی ربات
│   └── __init__.py
├── 📁 database/               # عملیات دیتابیس
│   ├── db_manager.py          # مدیر کل دیتابیس
│   └── __init__.py
├── 📁 models/                 # مدل‌های داده
│   ├── database_models.py     # مدل‌های Category, File, UserSession
│   └── __init__.py
├── 📁 handlers/              # هندلرهای مختلف
│   ├── base_handler.py       # کلاس پایه همه هندلرها
│   ├── category_handler.py   # مدیریت دسته‌ها
│   ├── file_handler.py       # مدیریت فایل‌ها
│   ├── message_handler.py    # مدیریت پیام‌ها
│   ├── broadcast_handler.py  # برودکست
│   ├── search_handler.py     # جستجو
│   └── __init__.py
├── 📁 actions/               # اکشن‌های خاص
│   ├── stats_action.py       # نمایش آمار
│   ├── backup_action.py      # پشتیبان‌گیری
│   └── __init__.py
├── 📁 utils/                 # ابزارهای کمکی
│   ├── keyboard_builder.py   # ساخت کیبورد
│   ├── helpers.py            # توابع کمکی
│   └── __init__.py
├── 📁 backups/               # پشتیبان‌های دیتابیس
├── bot_main.py               # فایل اصلی ربات
├── telegram_bot_runner_new.py # راه‌انداز جدید
├── bot_database.db           # دیتابیس SQLite
└── README_MODULAR.md         # این فایل
```

## ✨ امکانات جدید

### 🆕 امکانات اضافه شده:
- **حذف فایل‌ها**: امکان حذف فایل‌ها از دیتابیس
- **ویرایش فایل‌ها**: تغییر نام و توضیحات فایل‌ها
- **ویرایش دسته‌ها**: تغییر نام و توضیحات دسته‌ها
- **حذف دسته‌ها**: حذف دسته‌ها با انتقال محتوا به دسته والد
- **دانلود مستقیم**: دانلود فایل‌ها مستقیماً از ربات
- **پشتیبان‌گیری خودکار**: تهیه نسخه پشتیبان از دیتابیس
- **آمار تفصیلی**: نمایش آمار کامل و تفصیلی
- **بهبود UI/UX**: رابط کاربری بهتر و پیام‌های راهنما

### 🔄 بهبودهای ساختاری:
- **مدولار**: کد تقسیم شده به ماژول‌های منطقی
- **قابلیت توسعه**: امکان اضافه کردن قابلیت‌های جدید
- **مدیریت خطا**: سیستم بهتر مدیریت خطاها
- **لاگ‌گیری**: سیستم لاگ پیشرفته
- **کیش**: بهینه‌سازی عملکرد

## 🚀 راه‌اندازی

### روش 1: استفاده از ربات جدید
```bash
cd /app/bot
python telegram_bot_runner_new.py
```

### روش 2: استفاده از supervisor
```bash
# اضافه کردن تنظیمات جدید به supervisor
sudo nano /etc/supervisor/conf.d/telegram_bot_modular.conf

# محتوا:
[program:telegram_bot_modular]
command=python3 /app/bot/telegram_bot_runner_new.py
directory=/app/bot
autostart=true
autorestart=true
user=root
stdout_logfile=/var/log/supervisor/telegram_bot_modular.out.log
stderr_logfile=/var/log/supervisor/telegram_bot_modular.err.log

# راه‌اندازی
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start telegram_bot_modular
```

## 📱 دستورات جدید

### دستورات ربات:
- `/start` - شروع مجدد و نمایش منوی اصلی
- `/help` - نمایش راهنمای کامل
- `/stats` - نمایش آمار تفصیلی
- `/backup` - تهیه نسخه پشتیبان

### امکانات رابط کاربری:
- **✏️ ویرایش دسته** - تغییر نام دسته‌ها
- **🗑 حذف دسته** - حذف دسته با تأیید
- **📄 جزئیات فایل** - نمایش اطلاعات کامل فایل
- **📥 دانلود** - دانلود مستقیم فایل
- **✏️ ویرایش فایل** - تغییر نام و توضیحات
- **🗑 حذف فایل** - حذف فایل با تأیید
- **🔄 انتقال فایل** - انتقال به دسته دیگر

## 🔧 تنظیمات

### فایل `config/settings.py`:
```python
# تنظیمات اصلی
BOT_TOKEN = "YOUR_BOT_TOKEN"
STORAGE_CHANNEL_ID = -1002546879743
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
```

### مسیرهای مهم:
- **دیتابیس**: `/app/bot/bot_database.db`
- **پشتیبان‌ها**: `/app/bot/backups/`
- **لاگ‌ها**: `/var/log/telegram_bot_modular.log`

## 🛠 توسعه و سفارشی‌سازی

### افزودن قابلیت جدید:
1. ایجاد handler جدید در پوشه `handlers/`
2. اضافه کردن به `bot_main.py`
3. تعریف callback در `handle_callback_query`

### مثال اضافه کردن handler:
```python
# handlers/new_handler.py
from handlers.base_handler import BaseHandler

class NewHandler(BaseHandler):
    async def new_function(self, update, context):
        # پیاده‌سازی قابلیت جدید
        pass
```

## 📊 مانیتورینگ

### بررسی وضعیت:
```bash
# وضعیت supervisor
sudo supervisorctl status telegram_bot_modular

# لاگ‌های ربات
tail -f /var/log/telegram_bot_modular.log

# آمار دیتابیس
sqlite3 /app/bot/bot_database.db "SELECT COUNT(*) FROM files;"
```

### پشتیبان‌گیری:
```bash
# پشتیبان‌گیری دستی
python3 -c "
import asyncio
from database.db_manager import DatabaseManager
asyncio.run(DatabaseManager().create_backup())
"
```

## 🔒 امنیت

- تمام ورودی‌های کاربر اعتبارسنجی می‌شوند
- فایل‌های بزرگ‌تر از حد مجاز رد می‌شوند  
- سیستم مدیریت خطای قوی
- لاگ‌گیری کامل عملیات

## 🆘 عیب‌یابی

### مشکلات رایج:

1. **ربات شروع نمی‌شود**:
   ```bash
   # بررسی لاگ‌ها
   tail -f /var/log/supervisor/telegram_bot_modular.err.log
   ```

2. **خطای import**:
   ```bash
   # بررسی مسیر Python
   cd /app/bot && python3 -c "import bot_main"
   ```

3. **مشکل دیتابیس**:
   ```bash
   # بررسی دیتابیس
   sqlite3 /app/bot/bot_database.db ".tables"
   ```

## 📞 پشتیبانی

برای مشکلات فنی:
1. بررسی لاگ‌ها در `/var/log/`
2. اجرای تست‌ها با `python test_bot.py`
3. بررسی وضعیت دیتابیس
4. راه‌اندازی مجدد سرویس

---

**نسخه**: 2.0.0 (مدولار)  
**تاریخ**: دسامبر 2024  
**سازنده**: تیم توسعه ربات فایل