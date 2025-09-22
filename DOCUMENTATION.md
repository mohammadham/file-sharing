# 📚 مستندات کامل سیستم

## 🤖 ربات تلگرام

### ویژگی‌های اصلی

#### مدیریت فایل‌ها
- آپلود و ذخیره فایل در کانال تلگرام
- دسته‌بندی هیرارشیک فایل‌ها
- جستجوی پیشرفته در فایل‌ها
- حذف و ویرایش فایل‌ها
- انتقال فایل بین دسته‌ها

#### مدیریت دسته‌ها
- ایجاد دسته‌های چندسطحی
- ویرایش نام و توضیحات دسته‌ها
- حذف دسته (با احتیاط)
- آیکون‌های سفارشی برای دسته‌ها

#### سیستم اشتراک‌گذاری
- ایجاد لینک‌های اشتراک برای فایل‌ها
- لینک‌های دسته‌ای (تمام فایل‌های دسته)
- لینک‌های مجموعه‌ای (فایل‌های انتخابی)
- کنترل دسترسی و آمار

#### برودکست
- ارسال پیام متنی برای همه کاربران
- برودکست فایل
- آمار ارسال

### کامپوننت‌های کلیدی

#### DatabaseManager (`/app/bot/database/db_manager.py`)
```python
class DatabaseManager:
    async def get_categories(self, parent_id=None)
    async def create_category(self, name, parent_id, description)
    async def get_files(self, category_id, limit=20)
    async def create_file_record(self, file_data)
    async def create_link(self, link_data)
```

#### Handlers
- `CategoryHandler`: مدیریت دسته‌ها
- `FileHandler`: مدیریت فایل‌ها
- `MessageHandler`: پردازش پیام‌ها
- `BroadcastHandler`: سیستم برودکست
- `DownloadSystemHandler`: ادغام با سیستم دانلود

### تنظیمات مهم

```python
# /app/bot/config/settings.py
BOT_TOKEN = "YOUR_BOT_TOKEN"
STORAGE_CHANNEL_ID = -1002546879743
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
```

## 🌐 سیستم دانلود

### ویژگی‌های اصلی

#### انواع دانلود
1. **Stream Download**
   - دانلود مستقیم بدون ذخیره
   - مناسب فایل‌های بزرگ
   - کم‌ترین استفاده از منابع

2. **Fast Download**
   - ذخیره در cache برای دانلودهای بعدی
   - سرعت بالا برای فایل‌های تکراری
   - مدیریت خودکار cache

3. **Restricted Download**
   - کنترل تعداد دانلود
   - تنظیم زمان انقضا
   - محدودیت IP
   - رمز عبور اختیاری

#### مدیریت لینک‌ها
- ایجاد لینک‌های موقت
- ردیابی آمار دانلود
- غیرفعال‌سازی لینک‌ها
- وب‌هوک برای اطلاع‌رسانی

### معماری سیستم

#### Core Components

##### DatabaseManager (`/app/download_system/core/database.py`)
```python
class DatabaseManager:
    async def create_download_link(self, link: DownloadLink)
    async def get_download_link(self, link_code: str)
    async def get_download_stats(self, link_code: str)
    async def cleanup_expired_cache(self)
```

##### AuthManager (`/app/download_system/core/auth.py`)
```python
class AuthManager:
    async def create_token(self, name, permissions, ...)
    async def validate_token(self, token_string)
    def check_permission(self, token, permission)
```

##### DownloadManager (`/app/download_system/core/download_manager.py`)
```python
class DownloadManager:
    async def create_download_link(self, file_id, download_type, ...)
    async def stream_download(self, file_id, storage_message_id)
    async def fast_download(self, file_id, file_name, ...)
    async def validate_download_access(self, link_code, ip, password)
```

#### API Routes

##### Authentication (`/api/auth`)
- `POST /api/auth/token` - ایجاد توکن جدید
- `GET /api/auth/validate` - اعتبارسنجی توکن

##### Download (`/api/download`)
- `POST /api/download/links/create` - ایجاد لینک دانلود
- `GET /api/download/stream/{link_code}` - دانلود استریم
- `GET /api/download/fast/{link_code}` - دانلود سریع
- `GET /api/download/info/{link_code}` - اطلاعات لینک
- `GET /api/download/stats/{link_code}` - آمار لینک

##### Files (`/api/files`)
- `GET /api/files/info/{file_id}` - اطلاعات فایل
- `GET /api/files/category/{category_id}` - فایل‌های دسته
- `GET /api/files/search` - جستجو در فایل‌ها

##### System (`/api/system`)
- `GET /api/system/health` - وضعیت سیستم
- `GET /api/system/metrics` - آمار عملکرد
- `POST /api/system/cache/cleanup` - پاکسازی cache

##### Admin (`/api/admin`)
- `GET /api/admin/stats/system` - آمار کامل سیستم
- `GET /api/admin/downloads/active` - دانلودهای فعال
- `POST /api/admin/cache/clear` - پاکسازی کامل cache

### مدل‌های داده

#### Token
```python
class Token(BaseModel):
    id: str
    token_hash: str
    name: str
    token_type: TokenType
    permissions: str  # JSON
    expires_at: Optional[datetime]
    is_active: bool
```

#### DownloadLink
```python
class DownloadLink(BaseModel):
    link_code: str
    file_id: int
    download_type: DownloadType
    max_downloads: Optional[int]
    expires_at: Optional[datetime]
    password_hash: Optional[str]
    download_count: int
```

#### DownloadSession
```python
class DownloadSession(BaseModel):
    link_code: str
    file_id: int
    ip_address: str
    file_size: int
    downloaded_bytes: int
    status: DownloadStatus
```

### تنظیمات سیستم

```python
# /app/download_system/config/settings.py
class Settings(BaseSettings):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    SECRET_KEY: str
    DATABASE_URL: str
    MAX_CACHE_SIZE: int = 5 * 1024 * 1024 * 1024  # 5GB
    RATE_LIMIT_PER_MINUTE: int = 60
```

## 🔗 ادغام سیستم‌ها

### DownloadSystemHandler در ربات

```python
class DownloadSystemHandler(BaseHandler):
    def __init__(self, db, download_api_url, admin_token):
        self.api_url = download_api_url  # http://localhost:8001
        self.admin_token = admin_token
        self.headers = {"Authorization": f"Bearer {admin_token}"}
    
    async def show_file_download_options(self, update, context):
        # نمایش گزینه‌های دانلود برای فایل
    
    async def create_stream_link(self, update, context):
        # ایجاد لینک دانلود استریم
    
    async def create_fast_link(self, update, context):
        # ایجاد لینک دانلود سریع
    
    async def create_restricted_link(self, update, context):
        # ایجاد لینک دانلود محدود
```

### فراخوانی API

```python
async def create_download_link_via_api(self, link_data: dict):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{self.api_url}/api/download/links/create",
            headers=self.headers,
            json=link_data
        ) as response:
            return await response.json()
```

## 🛠 توسعه و سفارشی‌سازی

### اضافه کردن Handler جدید

1. ایجاد کلاس جدید در `/app/bot/handlers/`
2. ارث‌بری از `BaseHandler`
3. تعریف متدهای async
4. ثبت در `bot_main.py`

```python
class CustomHandler(BaseHandler):
    async def handle_custom_action(self, update, context):
        # پیاده‌سازی عملکرد
        pass
```

### اضافه کردن API Route جدید

1. ایجاد فایل در `/app/download_system/api/routes/`
2. تعریف router
3. ثبت در `main.py`

```python
# custom_route.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/custom")
async def custom_endpoint():
    return {"message": "Custom endpoint"}

# main.py
from api.routes import custom_route
app.include_router(custom_route.router, prefix="/api/custom")
```

### اضافه کردن مدل داده جدید

```python
# در core/models.py
class CustomModel(BaseModel):
    id: str
    name: str
    created_at: datetime

# در core/database.py
async def create_custom_record(self, data: CustomModel):
    # پیاده‌سازی ذخیره در دیتابیس
    pass
```

## 📊 نظارت و عملکرد

### متریک‌های مهم

1. **سیستم عمومی**
   - تعداد کاربران فعال
   - تعداد فایل‌های ذخیره شده
   - حجم کل داده‌ها

2. **دانلودها**
   - تعداد دانلودهای روزانه
   - میانگین سرعت دانلود
   - نرخ موفقیت

3. **Cache**
   - درصد استفاده از cache
   - Hit rate
   - فضای مصرفی

### لاگ‌ها

```bash
# لاگ‌های ربات
tail -f /var/log/supervisor/bot.out.log

# لاگ‌های سیستم دانلود
tail -f /var/log/supervisor/download_system.out.log

# لاگ‌های supervisor
tail -f /var/log/supervisor/supervisord.log
```

### بک‌آپ و بازیابی

```bash
# بک‌آپ دیتابیس‌ها
cp /app/bot/bot_database.db /backup/
cp /app/download_system/download_system.db /backup/

# بک‌آپ تنظیمات
cp /app/bot/config/settings.py /backup/
cp /app/download_system/.env /backup/
```

## 🔒 امنیت و بهترین شیوه‌ها

### مدیریت توکن‌ها
- استفاده از توکن‌های قوی
- تنظیم زمان انقضا مناسب
- محدودیت permissions
- نظارت بر استفاده

### محافظت از API
- Rate limiting
- Input validation
- SQL injection prevention
- XSS protection

### محافظت از دیتابیس
- Backup منظم
- رمزگذاری داده‌های حساس
- کنترل دسترسی فایل‌ها
- Audit trail

این مستندات شامل تمام جنبه‌های سیستم برای توسعه‌دهندگان و مدیران سیستم است.