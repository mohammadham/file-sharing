#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telethon Fallback Manager
مدیریت fallback هنگام عدم دسترسی Telethon
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from utils.advanced_logger import advanced_logger, LogLevel, LogCategory
import sys
from pathlib import Path
# Add bot directory to path
sys.path.append(str(Path(__file__).parent))

# Add root app directory to path for download_system imports
sys.path.append(str(Path(__file__).parent.parent))
logger = logging.getLogger(__name__)


class TelethonFallbackManager:
    """مدیریت fallback هنگام عدم دسترسی Telethon"""
    
    def __init__(self):
        self.retry_queue = []
        self.admin_notifications = []
        
    async def check_telethon_availability(self) -> Dict[str, Any]:
        """بررسی وضعیت دسترسی Telethon"""
        try:
            from download_system.core.telethon_manager import TelethonManager
            telethon_manager = TelethonManager()
            
            # تست کانکشن به Telethon clients
            health_status = await telethon_manager.get_health_status()
            
            available_clients = [
                client_name for client_name, status in health_status.get('client_status', {}).items()
                if status.get('connected', False)
            ]
            
            total_clients = len(health_status.get('client_status', {}))
            
            return {
                'available': len(available_clients) > 0,
                'available_clients': available_clients,
                'total_clients': total_clients,
                'availability_percentage': (len(available_clients) / max(total_clients, 1)) * 100,
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking Telethon availability: {e}")
            await advanced_logger.log_telethon_error("system_check", e)
            
            return {
                'available': False,
                'available_clients': [],
                'total_clients': 0,
                'availability_percentage': 0,
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    async def generate_warning_message(self, operation_type: str) -> str:
        """تولید پیام هشدار برای عدم دسترسی Telethon"""
        
        warning_messages = {
            'stream_link': """
⚠️ **هشدار: مشکل در سیستم Telethon**

🔗 لینک استریم شما ایجاد شد اما ممکن است به درستی کار نکند.

**مشکل:** سیستم Telethon در دسترس نیست
**راهکار:** 
• روی 🔧 **تنظیمات** کلیک کنید
• کانفیگ Telethon را بررسی کنید
• اتصال اینترنت را بررسی کنید

💡 **نکته:** لینک بعد از برطرف شدن مشکل، کامل کار خواهد کرد.
            """,
            
            'fast_link': """
⚠️ **هشدار: مشکل در سیستم Telethon**

🚀 لینک دانلود سریع شما ایجاد شد اما ممکن است کُند باشد.

**مشکل:** کلاینت‌های Telethon غیرفعال هستند
**راهکار:**
• روی 🔧 **تنظیمات** کلیک کنید  
• وضعیت کلاینت‌ها را بررسی کنید
• در صورت نیاز مجدد login کنید

💡 **نکته:** سرعت دانلود بعد از اتصال مجدد بهبود می‌یابد.
            """,
            
            'restricted_link': """
⚠️ **هشدار: مشکل در سیستم Telethon**

🔒 لینک محدود شما ایجاد شد اما محدودیت‌ها اعمال نمی‌شوند.

**مشکل:** سیستم کنترل دسترسی غیرفعال است
**راهکار:**
• روی 🔧 **تنظیمات** کلیک کنید
• سیستم Telethon را فعال کنید
• تنظیمات امنیتی را بررسی کنید

💡 **نکته:** محدودیت‌ها بعد از اتصال مجدد اعمال می‌شوند.
            """,
            
            'general': """
⚠️ **هشدار: مشکل در سیستم Telethon**

عملیات شما انجام شد اما سیستم Telethon مشکل دارد.

**راهکار:**
• 🔧 روی **تنظیمات Telethon** کلیک کنید
• وضعیت کانکشن‌ها را بررسی کنید  
• در صورت نیاز مجدد پیکربندی کنید

💡 برای کمک بیشتر از منوی **راهنما** استفاده کنید.
            """
        }
        
        return warning_messages.get(operation_type, warning_messages['general'])
    
    async def create_fallback_download_link(self, file_id: int, link_type: str) -> Dict[str, Any]:
        """ایجاد لینک دانلود با fallback"""
        try:
            # تلاش برای ایجاد لینک معمولی
            availability = await self.check_telethon_availability()
            
            if availability['available']:
                # اگر Telethon در دسترس است، لینک معمولی ایجاد کن
                return {
                    'success': True,
                    'link_url': f"http://localhost:8001/download/{file_id}?type={link_type}",
                    'warning': None,
                    'telethon_status': 'available'
                }
            else:
                # اگر Telethon در دسترس نیست، fallback link ایجاد کن
                fallback_url = f"http://localhost:8001/download/{file_id}?type=fallback&original_type={link_type}"
                warning_message = await self.generate_warning_message(link_type)
                
                # لاگ کردن fallback
                await advanced_logger.log(
                    level=LogLevel.WARNING,
                    category=LogCategory.TELETHON_CLIENT,
                    message=f"Fallback link created for file {file_id} (type: {link_type})",
                    file_id=file_id,
                    context={
                        'link_type': link_type,
                        'telethon_availability': availability['availability_percentage']
                    }
                )
                
                # اضافه کردن به صف retry
                await self.schedule_retry_attempts({
                    'file_id': file_id,
                    'link_type': link_type,
                    'created_at': datetime.now().isoformat(),
                    'retry_count': 0
                })
                
                return {
                    'success': True,
                    'link_url': fallback_url,
                    'warning': warning_message,
                    'telethon_status': 'unavailable',
                    'fallback_mode': True,
                    'retry_scheduled': True
                }
                
        except Exception as e:
            logger.error(f"Error creating fallback download link: {e}")
            await advanced_logger.log_system_error(e, "create_fallback_download_link")
            
            return {
                'success': False,
                'error': str(e),
                'telethon_status': 'error'
            }
    
    async def schedule_retry_attempts(self, operation_data: Dict[str, Any]) -> None:
        """برنامه‌ریزی تلاش‌های مجدد"""
        try:
            # اضافه کردن به صف retry
            retry_item = {
                **operation_data,
                'next_retry': (datetime.now() + timedelta(minutes=5)).isoformat(),
                'max_retries': 10
            }
            
            self.retry_queue.append(retry_item)
            
            await advanced_logger.log(
                level=LogLevel.INFO,
                category=LogCategory.SYSTEM,
                message=f"Retry scheduled for operation: {operation_data}",
                context={'retry_queue_size': len(self.retry_queue)}
            )
            
        except Exception as e:
            logger.error(f"Error scheduling retry: {e}")
    
    async def process_retry_queue(self) -> Dict[str, Any]:
        """پردازش صف تلاش‌های مجدد"""
        try:
            now = datetime.now()
            processed = []
            failed = []
            
            for item in self.retry_queue.copy():
                try:
                    next_retry = datetime.fromisoformat(item['next_retry'])
                    
                    if now >= next_retry:
                        # تلاش مجدد
                        availability = await self.check_telethon_availability()
                        
                        if availability['available']:
                            # موفق - حذف از صف
                            self.retry_queue.remove(item)
                            processed.append(item)
                            
                            await advanced_logger.log(
                                level=LogLevel.INFO,
                                category=LogCategory.TELETHON_CLIENT,
                                message=f"Retry successful for file {item['file_id']}",
                                file_id=item['file_id']
                            )
                        else:
                            # ناموفق - افزایش retry_count
                            item['retry_count'] += 1
                            
                            if item['retry_count'] >= item['max_retries']:
                                # حداکثر تلاش رسیده - حذف از صف
                                self.retry_queue.remove(item)
                                failed.append(item)
                                
                                await advanced_logger.log(
                                    level=LogLevel.ERROR,
                                    category=LogCategory.TELETHON_CLIENT,
                                    message=f"Max retries reached for file {item['file_id']}",
                                    file_id=item['file_id']
                                )
                            else:
                                # برنامه‌ریزی retry بعدی
                                minutes_delay = min(item['retry_count'] * 5, 60)
                                item['next_retry'] = (now + timedelta(minutes=minutes_delay)).isoformat()
                                
                except Exception as e:
                    logger.error(f"Error processing retry item {item}: {e}")
                    
            return {
                'processed_count': len(processed),
                'failed_count': len(failed),
                'remaining_count': len(self.retry_queue),
                'processed_items': processed,
                'failed_items': failed
            }
            
        except Exception as e:
            logger.error(f"Error processing retry queue: {e}")
            return {'error': str(e)}
    
    async def notify_admin_of_issues(self, issue_summary: Dict[str, Any]) -> None:
        """اطلاع‌رسانی مشکلات به ادمین"""
        try:
            notification = {
                'timestamp': datetime.now().isoformat(),
                'issue_summary': issue_summary,
                'severity': self._calculate_severity(issue_summary)
            }
            
            self.admin_notifications.append(notification)
            
            # اگر مشکل جدی است، فوری اطلاع‌رسانی کن
            if notification['severity'] == 'critical':
                await self._send_critical_notification(notification)
                
            await advanced_logger.log(
                level=LogLevel.WARNING,
                category=LogCategory.SYSTEM,
                message="Admin notification created for Telethon issues",
                context=issue_summary
            )
            
        except Exception as e:
            logger.error(f"Error notifying admin: {e}")
    
    def _calculate_severity(self, issue_summary: Dict[str, Any]) -> str:
        """محاسبه شدت مشکل"""
        try:
            availability = issue_summary.get('availability_percentage', 100)
            error_count = issue_summary.get('error_count', 0)
            
            if availability == 0:
                return 'critical'
            elif availability < 50 or error_count > 10:
                return 'high'
            elif availability < 80 or error_count > 5:
                return 'medium'
            else:
                return 'low'
                
        except:
            return 'unknown'
    
    async def _send_critical_notification(self, notification: Dict[str, Any]) -> None:
        """ارسال اطلاع‌رسانی بحرانی"""
        try:
            # در اینجا می‌توان پیام تلگرام، ایمیل یا sms ارسال کرد
            logger.critical(f"Critical Telethon issue detected: {notification}")
            
        except Exception as e:
            logger.error(f"Error sending critical notification: {e}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """دریافت وضعیت کلی سیستم"""
        try:
            availability = await self.check_telethon_availability()
            
            return {
                'telethon_status': availability,
                'retry_queue_size': len(self.retry_queue),
                'pending_notifications': len(self.admin_notifications),
                'system_health': 'healthy' if availability['available'] else 'degraded',
                'last_update': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}


# نمونه سراسری
telethon_fallback_manager = TelethonFallbackManager()