# 🤖 سیستم ربات تلگرام و دانلود پیشرفته

## 📋 توضیحات

این پروژه شامل دو سیستم اصلی است:

1. **ربات تلگرام پیشرفته** - مدیریت فایل‌ها با قابلیت‌های کامل
2. **سیستم دانلود پیشرفته** - API قدرتمند برای مدیریت دانلود فایل‌ها

## 🚀 نصب و راه‌اندازی

### پیش‌نیازها

```bash
# نصب Python 3.11+
# نصب supervisor
sudo apt-get install supervisor

# نصب وابستگی‌ها
cd /app/bot && pip install -r requirements.txt
cd /app/download_system && pip install -r requirements.txt
```

### راه‌اندازی سریع

```bash
# استفاده از launcher
python /app/launcher.py start

# یا به صورت دستی
supervisorctl start telegram_bot download_system
```

## 🔧 تنظیمات

### ربات تلگرام

فایل تنظیمات: `/app/bot/config/settings.py`

```python
BOT_TOKEN = "YOUR_BOT_TOKEN"
STORAGE_CHANNEL_ID = YOUR_CHANNEL_ID
```

### سیستم دانلود

فایل تنظیمات: `/app/download_system/.env`

```env
API_HOST=0.0.0.0
API_PORT=8001
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite+aiosqlite:///./download_system.db
```

## 📊 وضعیت سیستم

```bash
# بررسی وضعیت
python /app/launcher.py status

# مشاهده لاگ‌ها
python /app/launcher.py logs bot
python /app/launcher.py logs download

# تست سیستم‌ها
python /app/launcher.py test
```

## 🔑 مدیریت توکن‌ها

```bash
# ایجاد توکن ادمین جدید
python /app/launcher.py token

# یا به صورت دستی
cd /app/download_system
python create_admin_token.py
```

## 📁 ساختار پروژه

```
/app/
├── bot/                    # ربات تلگرام
│   ├── bot_main.py        # فایل اصلی ربات
│   ├── handlers/          # هندلرها
│   ├── config/           # تنظیمات
│   └── requirements.txt  # وابستگی‌ها
├── download_system/       # سیستم دانلود
│   ├── main.py           # فایل اصلی API
│   ├── api/              # API routes
│   ├── core/             # کامپوننت‌های اصلی
│   └── requirements.txt  # وابستگی‌ها
├── launcher.py           # اسکریپت راه‌اندازی
└── README.md            # این فایل
```

## 🔄 دستورات مفید

```bash
# راه‌اندازی
python launcher.py start

# توقف
python launcher.py stop

# ری‌استارت
python launcher.py restart

# وضعیت سیستم
python launcher.py info

# مشاهده لاگ‌ها
tail -f /var/log/supervisor/bot.out.log
tail -f /var/log/supervisor/download_system.out.log
```

## 🌐 API Endpoints

### سیستم دانلود API

- **Health Check**: `GET /health`
- **Create Link**: `POST /api/download/links/create`
- **Stream Download**: `GET /api/download/stream/{link_code}`
- **Fast Download**: `GET /api/download/fast/{link_code}`
- **Admin Stats**: `GET /api/admin/stats/system`

### نمونه استفاده API

```bash
# تست سلامتی سیستم
curl http://localhost:8001/health

# ایجاد لینک دانلود (نیاز به توکن)
curl -X POST "http://localhost:8001/api/download/links/create" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"file_id": 1, "download_type": "stream"}'
```

## 🐛 عیب‌یابی

### مشکلات رایج

1. **ربات شروع نمی‌شود**
   ```bash
   # بررسی لاگ
   tail -n 50 /var/log/supervisor/bot.out.log
   ```

2. **سیستم دانلود در دسترس نیست**
   ```bash
   # بررسی پورت
   netstat -tlnp | grep 8001
   # بررسی لاگ
   tail -n 50 /var/log/supervisor/download_system.out.log
   ```

3. **خطای دیتابیس**
   ```bash
   # بررسی مجوزهای فایل
   ls -la /app/bot/bot_database.db
   ls -la /app/download_system/download_system.db
   ```

## 📈 نظارت و عملکرد

### مشاهده آمار

```bash
# آمار سیستم
python launcher.py info

# آمار تفصیلی از API
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8001/api/admin/stats/system
```

### بک‌آپ دیتابیس

```bash
# بک‌آپ دیتابیس ربات
cp /app/bot/bot_database.db /backup/bot_db_$(date +%Y%m%d_%H%M%S).db

# بک‌آپ دیتابیس دانلود
cp /app/download_system/download_system.db /backup/download_db_$(date +%Y%m%d_%H%M%S).db
```

## 🔒 امنیت

- تمام API endpoints با توکن محافظت می‌شوند
- رمزهای عبور با bcrypt هش می‌شوند
- لینک‌های دانلود قابل تنظیم برای IP و زمان هستند
- لاگ‌های کامل برای audit trail

## 📞 پشتیبانی

برای گزارش مشکل یا درخواست ویژگی جدید، لطفاً issue ایجاد کنید.

## 📄 لایسنس

این پروژه تحت لایسنس MIT منتشر شده است.