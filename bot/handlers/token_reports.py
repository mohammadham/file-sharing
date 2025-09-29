#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token Reports Handler - مدیریت گزارش‌ها و آمارگیری توکن‌ها
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta

from handlers.base_handler import BaseHandler

logger = logging.getLogger(__name__)


class TokenReportsHandler(BaseHandler):
    """مدیریت گزارش‌ها و آمارگیری توکن‌ها"""
    
    def __init__(self, db, token_manager):
        """
        Args:
            db: دیتابیس منیجر
            token_manager: TokenManagementHandler اصلی برای API calls
        """
        super().__init__(db)
        self.token_manager = token_manager
    
    # === REPORTS MENU ===
    
    async def show_reports_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """منوی اصلی گزارش‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "📈 **مرکز گزارش‌های توکن‌ها**\n\n"
            text += "📊 **انواع گزارش‌ها:**\n"
            text += "• **گزارش استفاده:** آمار استفاده روزانه، هفتگی، ماهانه\n"
            text += "• **گزارش شاذ و ناهنجار:** توکن‌های مشکوک و فعالیت‌های غیرعادی\n"
            text += "• **گزارش کوتا:** وضعیت سهمیه و محدودیت‌ها\n"
            text += "• **گزارش مقایسه‌ای:** مقایسه عملکرد توکن‌ها\n\n"
            
            text += "💾 **صادرات گزارش‌ها:**\n"
            text += "• فرمت‌های مختلف: JSON, CSV, PDF, Excel\n"
            text += "• برنامه‌ریزی گزارش‌های دوره‌ای\n"
            text += "• ارسال خودکار گزارش‌ها"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📊 گزارش استفاده", callback_data="usage_report"),
                    InlineKeyboardButton("📈 نمودارها", callback_data="charts_report")
                ],
                [
                    InlineKeyboardButton("⚠️ گزارش شاذ", callback_data="anomaly_report"),
                    InlineKeyboardButton("📋 گزارش کوتا", callback_data="quota_report")
                ],
                [
                    InlineKeyboardButton("🔄 گزارش مقایسه", callback_data="compare_report"),
                    InlineKeyboardButton("📅 گزارش‌های دوره‌ای", callback_data="periodic_reports")
                ],
                [
                    InlineKeyboardButton("💾 مرکز صادرات", callback_data="export_center"),
                    InlineKeyboardButton("⚙️ تنظیمات گزارش", callback_data="report_settings")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="token_dashboard")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_reports_menu: {e}")
            await self.handle_error(update, context, e)
    
    # === USAGE REPORT ===
    
    async def show_usage_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """گزارش استفاده از توکن‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت آمار استفاده
            stats = await self.token_manager.get_token_statistics()
            
            text = "📊 **گزارش استفاده از توکن‌ها**\n\n"
            
            if stats.get('success'):
                data = stats.get('data', {})
                
                # آمار امروز
                text += f"📈 **آمار امروز** ({datetime.now().strftime('%Y-%m-%d')}):\n"
                text += f"• درخواست‌های کل: {data.get('daily_usage', 0):,}\n"
                text += f"• توکن‌های فعال: {data.get('active_tokens', 0)}\n"
                text += f"• میانگین استفاده هر توکن: {self._calculate_avg_usage(data.get('daily_usage', 0), data.get('active_tokens', 1))}\n\n"
                
                # آمار هفتگی
                text += f"📊 **آمار هفتگی:**\n"
                text += f"• کل استفاده‌ها: {data.get('weekly_usage', 0):,}\n"
                text += f"• رشد نسبت به هفته قبل: {data.get('weekly_growth', 0)}%\n"
                text += f"• پیک استفاده: {data.get('peak_usage_day', 'نامشخص')}\n\n"
                
                # آمار ماهانه
                text += f"📈 **آمار ماهانه:**\n"
                text += f"• کل استفاده‌ها: {data.get('monthly_usage', 0):,}\n"
                text += f"• رشد نسبت به ماه قبل: {data.get('monthly_growth', 0)}%\n"
                text += f"• توکن‌های جدید: {data.get('new_tokens_this_month', 0)}\n\n"
                
                # آمار کلی
                text += f"📊 **آمار کلی:**\n"
                text += f"• کل استفاده‌ها: {data.get('total_usage', 0):,}\n"
                text += f"• کل توکن‌ها: {data.get('total_tokens', 0)}\n"
                text += f"• توکن‌های منقضی: {data.get('expired_tokens', 0)}\n"
                
                # محبوب‌ترین توکن‌ها
                top_tokens = data.get('top_used_tokens', [])
                if top_tokens:
                    text += f"\n🏆 **محبوب‌ترین توکن‌ها:**\n"
                    for i, token in enumerate(top_tokens[:3], 1):
                        text += f"{i}. {token.get('name', 'بدون نام')} - {token.get('usage_count', 0):,} استفاده\n"
                
            else:
                text += "❌ خطا در دریافت آمار استفاده"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📊 نمودار روزانه", callback_data="daily_chart"),
                    InlineKeyboardButton("📈 نمودار هفتگی", callback_data="weekly_chart")
                ],
                [
                    InlineKeyboardButton("📅 نمودار ماهانه", callback_data="monthly_chart"),
                    InlineKeyboardButton("🎯 بازه سفارشی", callback_data="custom_range_chart")
                ],
                [
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data="usage_report"),
                    InlineKeyboardButton("💾 صادرات", callback_data="export_usage_report")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="reports_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_usage_report: {e}")
            await self.handle_error(update, context, e)
    
    # === ANOMALY REPORT ===
    
    async def show_anomaly_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """گزارش فعالیت‌های شاذ و ناهنجار"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت گزارش شذرات
            result = await self.token_manager.get_anomaly_report()
            
            text = "⚠️ **گزارش فعالیت‌های شاذ و ناهنجار**\n\n"
            
            if result.get('success'):
                data = result.get('data', {})
                
                # خلاصه شذرات
                text += f"📊 **خلاصه شذرات ({datetime.now().strftime('%Y-%m-%d')}):**\n"
                text += f"• توکن‌های مشکوک: {data.get('suspicious_tokens', 0)}\n"
                text += f"• IP های مشکوک: {data.get('suspicious_ips', 0)}\n"
                text += f"• تلاش‌های دسترسی ناموفق: {data.get('failed_attempts', 0)}\n"
                text += f"• فعالیت‌های غیرعادی: {data.get('unusual_activities', 0)}\n\n"
                
                # توکن‌های مشکوک
                suspicious_tokens = data.get('suspicious_tokens_list', [])
                if suspicious_tokens:
                    text += f"🔍 **توکن‌های مشکوک:**\n"
                    for token in suspicious_tokens[:3]:
                        text += f"• `{token.get('token_id', 'N/A')}` - {token.get('reason', 'نامشخص')}\n"
                    if len(suspicious_tokens) > 3:
                        text += f"... و {len(suspicious_tokens) - 3} مورد دیگر\n"
                    text += "\n"
                
                # IP های مشکوک
                suspicious_ips = data.get('suspicious_ips_list', [])
                if suspicious_ips:
                    text += f"🌐 **IP های مشکوک:**\n"
                    for ip_info in suspicious_ips[:3]:
                        text += f"• {ip_info.get('ip', 'نامشخص')} - {ip_info.get('reason', 'نامشخص')}\n"
                        text += f"  کشور: {ip_info.get('country', 'نامشخص')} | تعداد: {ip_info.get('count', 0)}\n"
                    if len(suspicious_ips) > 3:
                        text += f"... و {len(suspicious_ips) - 3} IP دیگر\n"
                    text += "\n"
                
                # آمار جغرافیایی
                geo_stats = data.get('geo_anomalies', {})
                if geo_stats:
                    text += f"🌍 **شذرات جغرافیایی:**\n"
                    text += f"• کشورهای جدید: {geo_stats.get('new_countries', 0)}\n"
                    text += f"• تغییر ناگهانی منطقه: {geo_stats.get('region_jumps', 0)}\n"
                    text += f"• فعالیت از VPN/Proxy: {geo_stats.get('vpn_usage', 0)}\n\n"
                
                # الگوهای زمانی مشکوک
                time_patterns = data.get('time_anomalies', {})
                if time_patterns:
                    text += f"🕐 **الگوهای زمانی مشکوک:**\n"
                    text += f"• فعالیت خارج از ساعت کاری: {time_patterns.get('off_hours', 0)}\n"
                    text += f"• فعالیت شبانه غیرعادی: {time_patterns.get('night_activity', 0)}\n"
                    text += f"• افزایش ناگهانی درخواست: {time_patterns.get('sudden_spikes', 0)}\n"
                
            else:
                text += f"❌ خطا در دریافت گزارش شذرات\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔍 بررسی دقیق", callback_data="detailed_anomaly_analysis"),
                    InlineKeyboardButton("📊 آمار IP ها", callback_data="ip_anomaly_stats")
                ],
                [
                    InlineKeyboardButton("⚠️ اقدامات امنیتی", callback_data="security_actions"),
                    InlineKeyboardButton("🔒 لیست سیاه خودکار", callback_data="auto_blacklist")
                ],
                [
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data="anomaly_report"),
                    InlineKeyboardButton("💾 صادرات گزارش", callback_data="export_anomaly_report")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="reports_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_anomaly_report: {e}")
            await self.handle_error(update, context, e)
    
    # === DETAILED STATS ===
    
    async def handle_detailed_token_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """آمار کامل و دقیق توکن‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت آمار دقیق
            stats = await self.token_manager.get_detailed_token_statistics()
            
            text = "📊 **آمار کامل و تفصیلی توکن‌ها**\n\n"
            
            if stats.get('success'):
                data = stats.get('data', {})
                
                # آمار عمومی
                text += f"📈 **آمار عمومی:**\n"
                text += f"• کل توکن‌ها: {data.get('total_tokens', 0):,}\n"
                text += f"• توکن‌های فعال: {data.get('active_tokens', 0):,}\n"
                text += f"• توکن‌های منقضی: {data.get('expired_tokens', 0):,}\n"
                text += f"• توکن‌های غیرفعال: {data.get('inactive_tokens', 0):,}\n\n"
                
                # تفکیک بر اساس نوع
                text += f"🏷 **تفکیک بر اساس نوع:**\n"
                type_stats = data.get('by_type', {})
                for token_type, count in type_stats.items():
                    type_name = self._get_token_type_name(token_type)
                    text += f"• {type_name}: {count:,}\n"
                text += "\n"
                
                # آمار استفاده
                text += f"📊 **آمار استفاده:**\n"
                text += f"• استفاده امروز: {data.get('today_usage', 0):,}\n"
                text += f"• استفاده هفته: {data.get('week_usage', 0):,}\n"
                text += f"• استفاده ماه: {data.get('month_usage', 0):,}\n"
                text += f"• کل استفاده‌ها: {data.get('total_usage', 0):,}\n\n"
                
                # آمار زمانی
                text += f"📅 **آمار زمانی:**\n"
                text += f"• ایجاد شده امروز: {data.get('created_today', 0)}\n"
                text += f"• ایجاد شده این هفته: {data.get('created_week', 0)}\n"
                text += f"• منقضی شده امروز: {data.get('expired_today', 0)}\n"
                text += f"• آخرین فعالیت: {data.get('last_activity', 'نامشخص')}\n\n"
                
                # آمار امنیتی
                security_stats = data.get('security', {})
                if security_stats:
                    text += f"🔒 **آمار امنیتی:**\n"
                    text += f"• توکن‌های مشکوک: {security_stats.get('suspicious', 0)}\n"
                    text += f"• تلاش‌های ناموفق: {security_stats.get('failed_attempts', 0)}\n"
                    text += f"• IP های مسدود: {security_stats.get('blocked_ips', 0)}\n\n"
                
                # آمار عملکرد
                performance_stats = data.get('performance', {})
                if performance_stats:
                    text += f"⚡ **آمار عملکرد:**\n"
                    text += f"• میانگین زمان پاسخ: {performance_stats.get('avg_response_time', 0)}ms\n"
                    text += f"• نرخ موفقیت: {performance_stats.get('success_rate', 0)}%\n"
                    text += f"• خطاهای 5xx: {performance_stats.get('server_errors', 0)}\n"
                
            else:
                text += "❌ خطا در دریافت آمار کامل"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📊 نمودار تفصیلی", callback_data="detailed_charts"),
                    InlineKeyboardButton("📈 تحلیل روند", callback_data="trend_analysis")
                ],
                [
                    InlineKeyboardButton("🔄 بروزرسانی", callback_data="detailed_token_stats"),
                    InlineKeyboardButton("💾 صادرات کامل", callback_data="export_detailed_stats")
                ],
                [
                    InlineKeyboardButton("📧 ارسال ایمیل", callback_data="email_detailed_stats"),
                    InlineKeyboardButton("📅 برنامه‌ریزی گزارش", callback_data="schedule_detailed_report")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="reports_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_detailed_token_stats: {e}")
            await self.handle_error(update, context, e)
    
    # === EXPORT OPERATIONS ===
    
    async def handle_export_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """صادرات گزارش‌های توکن‌ها"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "💾 **مرکز صادرات گزارش‌ها**\n\n"
            text += "لطفاً نوع صادرات و فرمت مورد نظر را انتخاب کنید:\n\n"
            text += "📊 **انواع گزارش:**\n"
            text += "• **لیست توکن‌ها:** اطلاعات کامل همه توکن‌ها\n"
            text += "• **آمار استفاده:** گزارش استفاده و عملکرد\n"
            text += "• **گزارش امنیتی:** فعالیت‌های مشکوک و امنیتی\n"
            text += "• **گزارش تفصیلی:** ترکیبی از همه گزارش‌ها\n\n"
            
            text += "📄 **فرمت‌های پشتیبانی شده:**\n"
            text += "• JSON: مناسب برای پردازش خودکار\n"
            text += "• CSV: مناسب برای Excel و تحلیل\n"
            text += "• PDF: گزارش قابل چاپ و ارائه\n"
            text += "• Excel: جداول تعاملی و نمودارها"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📋 لیست توکن‌ها", callback_data="export_tokens_list"),
                    InlineKeyboardButton("📊 آمار استفاده", callback_data="export_usage_stats")
                ],
                [
                    InlineKeyboardButton("🔒 گزارش امنیتی", callback_data="export_security_report"),
                    InlineKeyboardButton("📈 گزارش کامل", callback_data="export_full_report")
                ],
                [
                    InlineKeyboardButton("⚙️ تنظیمات صادرات", callback_data="export_settings"),
                    InlineKeyboardButton("📅 صادرات برنامه‌ریزی شده", callback_data="scheduled_exports")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="reports_menu")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_export_tokens: {e}")
            await self.handle_error(update, context, e)
    
    async def show_export_format_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """انتخاب فرمت صادرات"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت نوع گزارش از callback_data
            export_type = query.data.replace('export_', '')
            
            text = f"📄 **انتخاب فرمت صادرات**\n\n"
            text += f"نوع گزارش: {self._get_export_type_name(export_type)}\n\n"
            text += "لطفاً فرمت مورد نظر را انتخاب کنید:"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📄 JSON", callback_data=f"export_format_{export_type}_json"),
                    InlineKeyboardButton("📊 CSV", callback_data=f"export_format_{export_type}_csv")
                ],
                [
                    InlineKeyboardButton("📕 PDF", callback_data=f"export_format_{export_type}_pdf"),
                    InlineKeyboardButton("📈 Excel", callback_data=f"export_format_{export_type}_excel")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="export_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_export_format_selection: {e}")
            await self.handle_error(update, context, e)
    
    # === HELPER METHODS ===
    
    def _calculate_avg_usage(self, total_usage: int, active_tokens: int) -> str:
        """محاسبه میانگین استفاده"""
        if active_tokens == 0:
            return "0"
        avg = total_usage / active_tokens
        return f"{avg:.1f}"
    
    def _get_token_type_name(self, token_type: str) -> str:
        """نام فارسی نوع توکن"""
        types = {
            'admin': 'مدیر',
            'limited': 'محدود',
            'user': 'کاربر',
            'api': 'API'
        }
        return types.get(token_type, 'نامشخص')
    
    def _get_export_type_name(self, export_type: str) -> str:
        """نام فارسی نوع صادرات"""
        types = {
            'tokens_list': 'لیست توکن‌ها',
            'usage_stats': 'آمار استفاده',
            'security_report': 'گزارش امنیتی',
            'full_report': 'گزارش کامل'
        }
        return types.get(export_type, 'نامشخص')
    
    # === PLACEHOLDER METHODS ===
    
    async def show_quota_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """گزارش کوتا و سهمیه - placeholder"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "📋 **گزارش کوتا و سهمیه**\n\n"
            text += "این بخش در حال توسعه است...\n\n"
            text += "قابلیت‌های آینده:\n"
            text += "• وضعیت سهمیه هر توکن\n"
            text += "• توکن‌های نزدیک به حد مجاز\n"
            text += "• آمار مصرف سهمیه\n"
            text += "• پیش‌بینی نیاز سهمیه"
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="reports_menu")
            ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_quota_report: {e}")
            await self.handle_error(update, context, e)
    
    async def show_compare_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """گزارش مقایسه‌ای - placeholder"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🔄 **گزارش مقایسه‌ای**\n\n"
            text += "این بخش در حال توسعه است...\n\n"
            text += "قابلیت‌های آینده:\n"
            text += "• مقایسه دو توکن\n"
            text += "• مقایسه دو دوره زمانی\n"
            text += "• مقایسه عملکرد انواع توکن\n"
            text += "• تحلیل روند و پیش‌بینی"
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="reports_menu")
            ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_compare_report: {e}")
            await self.handle_error(update, context, e)