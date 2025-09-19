# 🤖 راهنمای ربات مدیریت فایل تلگرام

## 📋 معرفی

این ربات یک سیستم کامل مدیریت فایل برای تلگرام است که امکانات زیر را ارائه می‌دهد:

- 📁 **دسته‌بندی فایل‌ها** با ساختار درختی
- 📤 **آپلود و ذخیره فایل** در کانال
- 📢 **برودکست پیام** به کاربران  
- 🔍 **جستجو در فایل‌ها**
- 📊 **آمار و گزارش**

## 🔧 مشخصات فنی

- **Bot Token**: `8428725185:AAELFU6lUasbSDUvRuhTLNDBT3uEmvNruN0`
- **Storage Channel ID**: `-1002546879743`
- **Database**: SQLite (bot_database.db)
- **Max File Size**: 50 MB
- **Framework**: python-telegram-bot 21.10

## 📚 ساختار دیتابیس

### جدول Categories
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES categories (id)
);
```

### جدول Files
```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_type TEXT,
    file_size INTEGER,
    category_id INTEGER,
    telegram_file_id TEXT,
    storage_message_id INTEGER,
    uploaded_by INTEGER,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    FOREIGN KEY (category_id) REFERENCES categories (id)
);
```

### جدول User Sessions
```sql
CREATE TABLE user_sessions (
    user_id INTEGER PRIMARY KEY,
    current_category INTEGER,
    action_state TEXT,
    temp_data TEXT,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🎛 امکانات ربات

### 1. مدیریت دسته‌ها
- **ایجاد دسته جدید**: کلیک روی "➕ افزودن دسته"
- **مرور دسته‌ها**: ناوبری در ساختار درختی
- **بازگشت**: دکمه "🔙 بازگشت" برای بازگشت به دسته والد

### 2. مدیریت فایل‌ها
- **آپلود فایل**: ارسال فایل در هر دسته
- **انواع فایل پشتیبانی شده**: سند، عکس، ویدیو، صوت
- **محدودیت حجم**: 50 مگابایت
- **ذخیره خودکار**: فایل‌ها به کانال storage forward می‌شوند

### 3. برودکست
- **برودکست متنی**: ارسال پیام به همه کاربران
- **گزارش ارسال**: نمایش تعداد کاربران دریافت کننده

### 4. جستجو
- **جستجو در نام فایل**: جستجو بر اساس نام فایل
- **جستجو در توضیحات**: جستجو در فیلد description
- **نمایش نتایج**: حداکثر 10 نتیجه با جزئیات کامل

### 5. آمار
- **تعداد کاربران**: تعداد کل کاربران ثبت شده
- **تعداد فایل‌ها**: تعداد کل فایل‌های ذخیره شده
- **تعداد دسته‌ها**: تعداد کل دسته‌بندی‌ها
- **حجم کل**: مجموع حجم تمام فایل‌ها

## 🚀 نحوه استفاده

### شروع کار
1. ربات را استارت کنید: `/start`
2. منوی اصلی نمایش داده می‌شود
3. دسته مورد نظر را انتخاب کنید

### آپلود فایل
1. وارد دسته مورد نظر شوید
2. فایل را ارسال کنید
3. فایل به کانال storage forward می‌شود
4. metadata در دیتابیس ذخیره می‌شود

### ایجاد دسته جدید
1. روی "➕ افزودن دسته" کلیک کنید
2. نام دسته را وارد کنید
3. دسته جدید ایجاد می‌شود

### جستجو
1. روی "🔍 جستجو" کلیک کنید
2. کلمه کلیدی را وارد کنید
3. نتایج نmایش داده می‌شود

### برودکست
1. روی "📢 برودکست" کلیک کنید
2. "📝 برودکست متنی" را انتخاب کنید
3. متن پیام را وارد کنید
4. پیام به همه کاربران ارسال می‌شود

## 🔨 مدیریت سرور

### وضعیت سرویس‌ها
```bash
sudo supervisorctl status
```

### راه‌اندازی مجدد ربات
```bash
sudo supervisorctl restart telegram_bot
```

### مشاهده لاگ‌ها
```bash
# لاگ خروجی
tail -f /var/log/supervisor/telegram_bot.out.log

# لاگ خطا
tail -f /var/log/supervisor/telegram_bot.err.log
```

### بک‌آپ دیتابیس
```bash
cp /app/backend/bot_database.db /path/to/backup/
```

## 🎨 رابط کاربری

### دکمه‌های اصلی
- 📁 **نام دسته**: ورود به دسته
- ➕ **افزودن دسته**: ایجاد دسته جدید
- 📁 **مشاهده فایل‌ها**: نمایش فایل‌های دسته
- 📢 **برودکست**: منوی برودکست
- 🔍 **جستجو**: جستجو در فایل‌ها
- 📊 **آمار**: نمایش آمار ربات
- 🔙 **بازگشت**: بازگشت به دسته والد

### وضعیت‌های کاربر
- `browsing`: حالت عادی مرور
- `adding_category`: در حال اضافه کردن دسته
- `broadcast_text`: در حال ارسال برودکست
- `searching`: در حال جستجو

## 🐛 عیب‌یابی

### مشکلات رایج

1. **ربات پاسخ نمی‌دهد**
   - وضعیت سرویس را چک کنید
   - لاگ‌ها را بررسی کنید
   - ربات را restart کنید

2. **فایل آپلود نمی‌شود**
   - حجم فایل را چک کنید (حداکثر 50MB)
   - دسترسی کانال storage را بررسی کنید

3. **برودکست کار نمی‌کند**
   - لاگ‌های خطا را چک کنید
   - وضعیت دیتابیس را بررسی کنید

## 📞 پشتیبانی

برای مشکلات فنی و پشتیبانی:
- بررسی لاگ‌های supervisor
- بررسی وضعیت دیتابیس SQLite
- بررسی اتصال به API تلگرام

---

**تاریخ آخرین بروزرسانی**: مهر 1403  
**نسخه**: 1.0.0