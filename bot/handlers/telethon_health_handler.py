#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telethon Health Check Handler
هندلر بررسی سلامت و دیباگینگ پیشرفته Telethon
"""

import asyncio
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.base_handler import BaseHandler
import sys
from pathlib import Path
# Add bot directory to path
sys.path.append(str(Path(__file__).parent))

# Add root app directory to path for download_system imports
sys.path.append(str(Path(__file__).parent.parent))
logger = logging.getLogger(__name__)


class TelethonHealthHandler(BaseHandler):
    """مدیریت سیستم دیباگینگ و بررسی سلامت Telethon"""
    
    def __init__(self, db):
        super().__init__(db)
    
    async def show_health_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش بررسی کامل سلامت سیستم"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update, "در حال بررسی سیستم...")
            
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            
            # بررسی سلامت تمام کلاینت‌ها
            telethon_manager = AdvancedTelethonClientManager()
            health_results = await telethon_manager.check_all_clients_health()
            configs = telethon_manager.config_manager.list_configs()
            
            text = "🩺 **گزارش کامل سلامت سیستم Telethon**\n\n"
            text += f"📊 **آمار کلی:**\n"
            text += f"• کل کانفیگ‌ها: {len(configs)}\n"
            
            healthy_count = sum(1 for r in health_results.values() if r.get('status') == 'healthy')
            text += f"• کلاینت‌های سالم: {healthy_count}\n"
            text += f"• کلاینت‌های مشکل‌دار: {len(health_results) - healthy_count}\n\n"
            
            if not configs:
                text += "❌ **هیچ کانفیگی یافت نشد**\n\n"
                text += "💡 **راهکار:**\n"
                text += "• ابتدا یک کانفیگ JSON اضافه کنید\n"
                text += "• سپس وارد اکانت تلگرام شوید"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("➕ افزودن کانفیگ", callback_data="telethon_add_config")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
                    ]
                ])
            
            elif not health_results:
                text += "⚠️ **هیچ کلاینت فعالی یافت نشد**\n\n"
                text += "💡 **مشکلات احتمالی:**\n"
                text += "• کانفیگ‌ها نامعتبر هستند\n"
                text += "• نیاز به ورود مجدد به اکانت‌ها\n"
                text += "• مشکل در اتصال به اینترنت\n\n"
                text += "🔧 **راهکارها:**\n"
                text += "• بررسی کانفیگ‌ها\n"
                text += "• ورود مجدد به اکانت‌ها\n"
                text += "• بررسی اتصال اینترنت"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔐 ورود به اکانت‌ها", callback_data="telethon_login_menu"),
                        InlineKeyboardButton("📋 مشاهده کانفیگ‌ها", callback_data="telethon_list_configs")
                    ],
                    [
                        InlineKeyboardButton("🔄 بررسی مجدد", callback_data="telethon_health_check"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
                    ]
                ])
            
            else:
                text += "📋 **جزئیات هر کلاینت:**\n\n"
                
                for config_name, health_info in health_results.items():
                    if health_info.get('status') == 'healthy':
                        icon = "🟢"
                        status_text = "سالم"
                        details = f"شناسه: {health_info.get('user_id', 'نامشخص')}"
                        if health_info.get('phone'):
                            details += f" | {health_info['phone']}"
                    elif health_info.get('status') == 'disconnected':
                        icon = "🟡"
                        status_text = "قطع"
                        details = "اتصال برقرار نشده"
                    else:
                        icon = "🔴"
                        status_text = "خطا"
                        error = health_info.get('error', 'نامشخص')[:50]
                        details = f"خطا: {error}"
                    
                    text += f"{icon} **{config_name}** - {status_text}\n"
                    text += f"   {details}\n\n"
                
                # ارزیابی کلی سیستم
                if healthy_count == 0:
                    text += "🚨 **وضعیت کلی: بحرانی**\n"
                    text += "هیچ کلاینت فعالی در دسترس نیست!"
                elif healthy_count < len(configs) // 2:
                    text += "⚠️ **وضعیت کلی: نیازمند توجه**\n"
                    text += "اکثر کلاینت‌ها مشکل دارند."
                else:
                    text += "✅ **وضعیت کلی: خوب**\n"
                    text += "سیستم عملکرد مناسبی دارد."
                
                keyboard_rows = []
                
                # دکمه‌های اقدام سریع
                if healthy_count == 0:
                    keyboard_rows.extend([
                        [
                            InlineKeyboardButton("🔐 ورود اضطراری", callback_data="telethon_emergency_login"),
                            InlineKeyboardButton("🔧 تشخیص مشکل", callback_data="telethon_diagnose_issues")
                        ]
                    ])
                else:
                    keyboard_rows.extend([
                        [
                            InlineKeyboardButton("🔧 رفع مشکلات", callback_data="telethon_fix_issues"),
                            InlineKeyboardButton("📊 آمار تفصیلی", callback_data="telethon_detailed_stats")
                        ]
                    ])
                
                keyboard_rows.extend([
                    [
                        InlineKeyboardButton("🔄 بررسی مجدد", callback_data="telethon_health_check"),
                        InlineKeyboardButton("⚙️ تنظیمات", callback_data="telethon_advanced_settings")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
                    ]
                ])
                
                keyboard = InlineKeyboardMarkup(keyboard_rows)
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def show_detailed_diagnostics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش تشخیص مفصل مشکلات"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update, "در حال تشخیص مشکلات...")
            
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            
            telethon_manager = AdvancedTelethonClientManager()
            configs = telethon_manager.config_manager.list_configs()
            health_results = await telethon_manager.check_all_clients_health()
            
            text = "🔧 **تشخیص پیشرفته مشکلات**\n\n"
            
            # تجزیه تحلیل مشکلات
            issues_found = []
            solutions = []
            
            # بررسی عدم وجود کانفیگ
            if not configs:
                issues_found.append("❌ **هیچ کانفیگی تعریف نشده**")
                solutions.append("• افزودن کانفیگ JSON جدید")
            
            # بررسی کانفیگ‌های بدون session
            configs_without_session = [
                name for name, info in configs.items() 
                if not info.get('has_session')
            ]
            if configs_without_session:
                issues_found.append(f"🔴 **{len(configs_without_session)} کانفیگ بدون session**")
                solutions.append("• ورود به اکانت‌های مربوطه")
            
            # بررسی خطاهای اتصال
            connection_errors = [
                (name, info.get('error', '')) for name, info in health_results.items()
                if info.get('status') == 'error'
            ]
            if connection_errors:
                issues_found.append(f"🔴 **{len(connection_errors)} کلاینت با خطای اتصال**")
                solutions.append("• بررسی اعتبار API credentials")
                solutions.append("• بررسی اتصال اینترنت")
            
            # بررسی کلاینت‌های قطع
            disconnected_clients = [
                name for name, info in health_results.items()
                if info.get('status') == 'disconnected'
            ]
            if disconnected_clients:
                issues_found.append(f"🟡 **{len(disconnected_clients)} کلاینت قطع شده**")
                solutions.append("• اتصال مجدد کلاینت‌ها")
            
            # نمایش نتایج
            if issues_found:
                text += "🔍 **مشکلات شناسایی شده:**\n\n"
                for issue in issues_found:
                    text += f"{issue}\n"
                
                text += "\n💡 **راهکارهای پیشنهادی:**\n\n"
                for solution in solutions:
                    text += f"{solution}\n"
                
                # جزئیات خطاها
                if connection_errors:
                    text += "\n📋 **جزئیات خطاها:**\n\n"
                    for config_name, error in connection_errors[:3]:  # نمایش 3 خطا اول
                        short_error = error[:50] + "..." if len(error) > 50 else error
                        text += f"• **{config_name}:** {short_error}\n"
                
                keyboard_rows = [
                    [
                        InlineKeyboardButton("🔧 شروع رفع خودکار", callback_data="telethon_auto_fix"),
                        InlineKeyboardButton("🔐 ورود دستی", callback_data="telethon_login_menu")
                    ],
                    [
                        InlineKeyboardButton("📋 مشاهده کانفیگ‌ها", callback_data="telethon_list_configs"),
                        InlineKeyboardButton("➕ افزودن کانفیگ", callback_data="telethon_add_config")
                    ]
                ]
            else:
                text += "✅ **هیچ مشکلی شناسایی نشد**\n\n"
                text += "🎉 **تمام سیستم‌ها عادی کار می‌کنند:**\n"
                text += "• تمام کانفیگ‌ها معتبر هستند\n"
                text += "• کلاینت‌ها متصل و سالم هستند\n"
                text += "• سیستم دانلود آماده استفاده است\n\n"
                text += f"📊 **آمار:** {len(configs)} کانفیگ، {len(health_results)} کلاینت فعال"
                
                keyboard_rows = [
                    [
                        InlineKeyboardButton("🩺 تست عملکرد", callback_data="telethon_performance_test"),
                        InlineKeyboardButton("📊 آمار تفصیلی", callback_data="telethon_detailed_stats")
                    ]
                ]
            
            keyboard_rows.append([
                InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_health_check")
            ])
            
            keyboard = InlineKeyboardMarkup(keyboard_rows)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def show_system_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش وضعیت کامل سیستم"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            
            telethon_manager = AdvancedTelethonClientManager()
            configs = telethon_manager.config_manager.list_configs()
            health_results = await telethon_manager.check_all_clients_health()
            
            # محاسبه آمار
            total_configs = len(configs)
            healthy_clients = sum(1 for r in health_results.values() if r.get('status') == 'healthy')
            has_active_clients = telethon_manager.has_active_clients()
            
            text = "📊 **وضعیت کامل سیستم Telethon**\n\n"
            
            # وضعیت کلی
            if has_active_clients:
                system_status = "🟢 **آنلاین و عملیاتی**"
                availability = "✅ سیستم دانلود در دسترس"
            else:
                system_status = "🔴 **آفلاین**"
                availability = "❌ سیستم دانلود در دسترس نیست"
            
            text += f"🌐 **وضعیت سیستم:** {system_status}\n"
            text += f"📡 **دسترسی:** {availability}\n\n"
            
            # آمار تفصیلی
            text += f"📈 **آمار عملکرد:**\n"
            text += f"• کل کانفیگ‌ها: {total_configs}\n"
            text += f"• کلاینت‌های فعال: {healthy_clients}\n"
            
            if total_configs > 0:
                health_percentage = (healthy_clients / total_configs) * 100
                text += f"• درصد سلامت: {health_percentage:.1f}%\n"
            
            text += f"• آخرین بررسی: {datetime.now().strftime('%H:%M:%S')}\n\n"
            
            # وضعیت هر کانفیگ
            if configs:
                text += f"🔧 **وضعیت کانفیگ‌ها:**\n\n"
                
                for config_name, config_info in configs.items():
                    health_info = health_results.get(config_name, {})
                    
                    if health_info.get('status') == 'healthy':
                        status_icon = "🟢"
                        status_text = "فعال"
                    elif health_info.get('status') == 'disconnected':
                        status_icon = "🟡"
                        status_text = "قطع"
                    else:
                        status_icon = "🔴"
                        status_text = "خطا"
                    
                    text += f"{status_icon} **{config_name}** - {status_text}\n"
                    
                    if config_info.get('phone'):
                        text += f"   📱 {config_info['phone']}\n"
                    
                    if health_info.get('error'):
                        error_short = health_info['error'][:30] + "..."
                        text += f"   ❌ {error_short}\n"
                    
                    text += "\n"
            else:
                text += "❌ **هیچ کانفیگی تعریف نشده است**\n\n"
            
            # هشدارها و توصیه‌ها
            text += "💡 **توصیه‌ها:**\n"
            
            if not has_active_clients:
                text += "• برای استفاده از سیستم دانلود، حداقل یک کلاینت فعال نیاز است\n"
                text += "• ابتدا کانفیگ اضافه کرده و سپس وارد اکانت شوید\n"
            elif healthy_clients < total_configs:
                text += "• برخی کلاینت‌ها مشکل دارند، آنها را بررسی کنید\n"
                text += "• برای بهترین عملکرد، تمام کلاینت‌ها باید فعال باشند\n"
            else:
                text += "• سیستم در وضعیت بهینه است\n"
                text += "• می‌توانید از تمام قابلیت‌های دانلود استفاده کنید\n"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data="telethon_system_status"),
                    InlineKeyboardButton("🩺 بررسی سلامت", callback_data="telethon_health_check")
                ],
                [
                    InlineKeyboardButton("🔧 رفع مشکلات", callback_data="telethon_diagnose_issues"),
                    InlineKeyboardButton("⚙️ تنظیمات", callback_data="telethon_advanced_settings")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="telethon_management_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def emergency_status_check(self) -> dict:
        """بررسی اضطراری وضعیت سیستم - برای استفاده در سایر بخش‌ها"""
        try:
            from download_system.core.telethon_manager import AdvancedTelethonClientManager
            
            telethon_manager = AdvancedTelethonClientManager()
            
            # بررسی سریع
            has_active = telethon_manager.has_active_clients()
            client_status = telethon_manager.get_client_status()
            
            return {
                'has_active_clients': has_active,
                'total_clients': len(client_status),
                'healthy_clients': sum(
                    1 for status in client_status.values() 
                    if status.get('connected', False)
                ),
                'system_ready': has_active,
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Emergency status check failed: {e}")
            return {
                'has_active_clients': False,
                'total_clients': 0,
                'healthy_clients': 0,
                'system_ready': False,
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }