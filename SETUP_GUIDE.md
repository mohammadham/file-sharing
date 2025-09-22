# 🚀 راهنمای راه‌اندازی گام به گام

## 📋 پیش‌نیازها

### نرم‌افزارهای مورد نیاز

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip supervisor curl jq

# CentOS/RHEL
sudo yum install -y python3.11 python3.11-venv python3-pip supervisor curl jq
```

### ایجاد محیط مجازی Python

```bash
# ایجاد محیط مجازی
python3.11 -m venv /root/.venv

# فعال‌سازی
source /root/.venv/bin/activate

# بروزرسانی pip
pip install --upgrade pip
```

## 🤖 راه‌اندازی ربات تلگرام

### مرحله 1: دریافت Bot Token

1. در تلگرام به `@BotFather` پیام دهید
2. دستور `/newbot` را ارسال کنید
3. نام ربات را انتخاب کنید
4. Bot Token را کپی کنید

### مرحله 2: ایجاد کانال ذخیره‌سازی

1. کانال جدید ایجاد کنید
2. ربات را به کانال اضافه کنید و ادمین کنید
3. ID کانال را دریافت کنید:

```bash
# ارسال پیام به کانال و سپس:
curl "https://api.telegram.org/bot<BOT_TOKEN>/getUpdates"
```

### مرحله 3: تنظیم کانفیگ ربات

```bash
# ویرایش فایل تنظیمات
nano /app/bot/config/settings.py
```

```python
# تغییر این مقادیر
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
STORAGE_CHANNEL_ID = -1001234567890  # Channel ID شما
```

### مرحله 4: نصب وابستگی‌ها

```bash
cd /app/bot
pip install -r requirements.txt
```

### مرحله 5: راه‌اندازی دیتابیس

```bash
cd /app/bot
python -c "
import asyncio
from database.db_manager import DatabaseManager

async def init():
    db = DatabaseManager()
    await db.init_database()
    print('✅ دیتابیس ربات آماده شد')

asyncio.run(init())
"
```

## 🌐 راه‌اندازی سیستم دانلود

### مرحله 1: تنظیم محیط

```bash
cd /app/download_system
cp .env.example .env
nano .env
```

```env
# تنظیمات پایه
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8001

# کلید امنیتی (تولید کلید قوی)
SECRET_KEY=$(openssl rand -base64 32)

# دیتابیس
DATABASE_URL=sqlite+aiosqlite:///./download_system.db

# تنظیمات تلگرام (کپی از ربات)
BOT_TOKEN=YOUR_BOT_TOKEN
STORAGE_CHANNEL_ID=-1001234567890

# Cache
CACHE_DIR=./cache
MAX_CACHE_SIZE=5368709120  # 5GB
```

### مرحله 2: نصب وابستگی‌ها

```bash
cd /app/download_system
pip install -r requirements.txt
```

### مرحله 3: راه‌اندازی دیتابیس

```bash
cd /app/download_system
python -c "
import asyncio
from core.database import DatabaseManager

async def init():
    db = DatabaseManager()
    await db.init_database()
    print('✅ دیتابیس سیستم دانلود آماده شد')

asyncio.run(init())
"
```

### مرحله 4: ایجاد توکن ادمین

```bash
cd /app/download_system
python create_admin_token.py
```

خروجی مشابه زیر خواهید دید:

```
✅ Admin token created successfully!
🔑 Token: xyz123...
📝 Token ID: abc-def-...
⏰ Expires: 2025-01-01T00:00:00

🔗 Use this token in Authorization header as: Bearer xyz123...
```

**مهم**: این توکن را در جای امن ذخیره کنید!

### مرحله 5: بروزرسانی توکن در ربات

```bash
nano /app/bot/bot_main.py
```

خط زیر را پیدا کرده و توکن جدید را جایگزین کنید:

```python
self.download_system_handler = DownloadSystemHandler(
    self.db,
    download_api_url="http://localhost:8001",
    admin_token="YOUR_NEW_ADMIN_TOKEN_HERE"  # ←← اینجا
)
```

## 🔧 تنظیم Supervisor

### مرحله 1: کپی فایل‌های تنظیمات

```bash
# کپی تنظیمات supervisor
cp /app/supervisor_bot.conf /etc/supervisor/conf.d/
cp /app/supervisor_download.conf /etc/supervisor/conf.d/
```

### مرحله 2: بروزرسانی Supervisor

```bash
supervisorctl reread
supervisorctl update
```

### مرحله 3: راه‌اندازی سیستم‌ها

```bash
supervisorctl start telegram_bot
supervisorctl start download_system
```

### مرحله 4: بررسی وضعیت

```bash
supervisorctl status
```

باید خروجی مشابه زیر ببینید:

```
download_system              RUNNING   pid 1234, uptime 0:00:30
telegram_bot                 RUNNING   pid 5678, uptime 0:00:25
```

## 🧪 تست سیستم‌ها

### تست سیستم دانلود

```bash
# تست health endpoint
curl http://localhost:8001/health

# باید پاسخ مشابه زیر دریافت کنید:
# {"status":"healthy","ready":true,"version":"1.0.0",...}
```

### تست ربات تلگرام

1. در تلگرام به ربات خود پیام `/start` ارسال کنید
2. باید منوی اصلی نمایش داده شود
3. یک فایل کوچک آپلود کنید و بررسی کنید که ذخیره می‌شود

### تست ادغام

1. در ربات یک فایل آپلود کنید
2. روی فایل کلیک کنید
3. گزینه "🔗 مدیریت لینک‌های دانلود پیشرفته" را انتخاب کنید
4. یکی از انواع لینک را ایجاد کنید

## 🚀 استفاده از Launcher

### نصب Launcher

```bash
chmod +x /app/launcher.py

# اضافه کردن به PATH (اختیاری)
ln -s /app/launcher.py /usr/local/bin/bot-launcher
```

### دستورات Launcher

```bash
# راه‌اندازی
python /app/launcher.py start

# توقف
python /app/launcher.py stop

# ری‌استارت
python /app/launcher.py restart

# وضعیت
python /app/launcher.py status

# لاگ‌ها
python /app/launcher.py logs bot
python /app/launcher.py logs download

# تست
python /app/launcher.py test

# اطلاعات سیستم
python /app/launcher.py info

# ایجاد توکن جدید
python /app/launcher.py token
```

## 🔄 راه‌اندازی خودکار در بوت

### SystemD Service (پیشنهادی)

```bash
# ایجاد سرویس
sudo nano /etc/systemd/system/telegram-bot-system.service
```

```ini
[Unit]
Description=Telegram Bot and Download System
After=network.target

[Service]
Type=forking
User=root
ExecStart=/usr/bin/supervisord -c /etc/supervisor/supervisord.conf
ExecReload=/usr/bin/supervisorctl reload
ExecStop=/usr/bin/supervisorctl shutdown
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# فعال‌سازی
sudo systemctl enable telegram-bot-system
sudo systemctl start telegram-bot-system
```

### Auto-start script (جایگزین)

```bash
# اضافه کردن به crontab
crontab -e

# اضافه کردن خط زیر:
@reboot /app/launcher.py start
```

## 🔍 عیب‌یابی

### مشکلات رایج

#### 1. ربات شروع نمی‌شود

```bash
# بررسی لاگ
tail -n 50 /var/log/supervisor/bot.out.log

# مشکلات رایج:
# - Bot Token اشتباه
# - مشکل در import ماژول‌ها
# - خطای دیتابیس
```

#### 2. سیستم دانلود کار نمی‌کند

```bash
# بررسی لاگ
tail -n 50 /var/log/supervisor/download_system.out.log

# تست پورت
netstat -tlnp | grep 8001

# مشکلات رایج:
# - پورت در حال استفاده
# - مشکل در دیتابیس
# - کم بودن حافظه
```

#### 3. خطای دسترسی فایل

```bash
# بررسی مجوزها
ls -la /app/bot/bot_database.db
ls -la /app/download_system/download_system.db

# تصحیح مجوزها
chown -R root:root /app/
chmod 644 /app/bot/bot_database.db
chmod 644 /app/download_system/download_system.db
```

#### 4. پر شدن فضای Cache

```bash
# بررسی فضا
du -sh /app/download_system/cache/

# پاکسازی
python /app/launcher.py cleanup
# یا
rm -rf /app/download_system/cache/*
```

## 📊 نظارت و نگهداری

### نظارت روزانه

```bash
# چک لیست روزانه
echo "# گزارش روزانه - $(date)" > daily_report.txt
echo "## وضعیت سیستم‌ها" >> daily_report.txt
python /app/launcher.py status >> daily_report.txt
echo "## آمار" >> daily_report.txt
python /app/launcher.py info >> daily_report.txt
```

### بک‌آپ خودکار

```bash
# اسکریپت بک‌آپ
cat > /app/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# بک‌آپ دیتابیس‌ها
cp /app/bot/bot_database.db $BACKUP_DIR/
cp /app/download_system/download_system.db $BACKUP_DIR/

# بک‌آپ تنظیمات
cp /app/bot/config/settings.py $BACKUP_DIR/
cp /app/download_system/.env $BACKUP_DIR/

# فشرده‌سازی
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR/
rm -rf $BACKUP_DIR/

echo "✅ Backup completed: $BACKUP_DIR.tar.gz"
EOF

chmod +x /app/backup.sh

# اضافه کردن به crontab برای بک‌آپ روزانه
echo "0 2 * * * /app/backup.sh" | crontab -
```

### بروزرسانی سیستم

```bash
# بروزرسانی کتابخانه‌ها
cd /app/bot && pip install --upgrade -r requirements.txt
cd /app/download_system && pip install --upgrade -r requirements.txt

# ری‌استارت
python /app/launcher.py restart
```

## ✅ چک لیست نهایی

- [ ] Bot Token تنظیم شده
- [ ] Storage Channel ID تنظیم شده
- [ ] دیتابیس‌ها ایجاد شده
- [ ] Admin Token ایجاد شده
- [ ] Supervisor تنظیم شده
- [ ] سیستم‌ها running هستند
- [ ] تست‌های اولیه انجام شده
- [ ] بک‌آپ خودکار تنظیم شده
- [ ] نظارت روزانه تنظیم شده

🎉 **تبریک! سیستم شما آماده استفاده است.**

برای هر گونه مشکل، لطفاً مستندات کامل را مطالعه کنید یا لاگ‌ها را بررسی کنید.