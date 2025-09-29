#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token Advanced Analytics Handler - تحلیل‌های پیشرفته توکن‌ها
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class TokenAdvancedAnalytics:
    """تحلیل‌های پیشرفته و آمار توکن‌ها"""
    
    def __init__(self, db):
        self.db = db
    
    # === Advanced Analytics Menu ===
    async def show_advanced_analytics_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی تحلیل‌های پیشرفته"""
        keyboard = [
            [
                InlineKeyboardButton("📊 نمودارهای استفاده", callback_data="usage_charts"),
                InlineKeyboardButton("🔍 تحلیل رفتار", callback_data="behavior_analysis")
            ],
            [
                InlineKeyboardButton("📈 پیش‌بینی ترند", callback_data="trend_prediction"),
                InlineKeyboardButton("⚡ آمار عملکرد", callback_data="performance_stats")
            ],
            [
                InlineKeyboardButton("🌍 تحلیل جغرافیایی", callback_data="geo_analysis"),
                InlineKeyboardButton("⏰ تحلیل زمانی", callback_data="time_analysis")
            ],
            [
                InlineKeyboardButton("🎯 توصیه‌های بهینه‌سازی", callback_data="optimization_recommendations")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="reports_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get quick stats
        try:
            stats = await self.get_quick_analytics_stats()
            trend = "📈" if stats['growth_rate'] > 0 else "📉" if stats['growth_rate'] < 0 else "➡️"
            
            text = (
                "🧠 *تحلیل‌های پیشرفته توکن‌ها*\n\n"
                f"📊 آمار سریع:\n"
                f"• توکن‌های فعال: {stats['active_tokens']}\n"
                f"• درخواست‌های امروز: {stats['today_requests']}\n"
                f"• نرخ رشد: {trend} {abs(stats['growth_rate']):.1f}%\n"
                f"• میانگین استفاده: {stats['avg_usage']:.1f} درخواست/توکن\n\n"
                "برای تحلیل‌های عمیق‌تر گزینه مورد نظر را انتخاب کنید:"
            )
        except Exception as e:
            logger.error(f"Error getting analytics stats: {e}")
            text = (
                "🧠 *تحلیل‌های پیشرفته توکن‌ها*\n\n"
                "🔍 ابزارهای تحلیل قدرتمند\n"
                "📊 نمودارها و آمار دقیق\n"
                "🎯 بینش‌های عملی برای بهینه‌سازی\n\n"
                "گزینه مورد نظر را انتخاب کنید:"
            )
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        await update.callback_query.answer()
    
    # === Usage Charts ===
    async def show_usage_charts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش نمودارهای استفاده"""
        keyboard = [
            [
                InlineKeyboardButton("📅 نمودار روزانه", callback_data="daily_usage_chart"),
                InlineKeyboardButton("📆 نمودار هفتگی", callback_data="weekly_usage_chart")
            ],
            [
                InlineKeyboardButton("📊 نمودار ماهانه", callback_data="monthly_usage_chart"),
                InlineKeyboardButton("🔄 مقایسه دوره‌ای", callback_data="period_comparison_chart")
            ],
            [
                InlineKeyboardButton("🎯 نمودار بر اساس نوع", callback_data="token_type_chart"),
                InlineKeyboardButton("👥 نمودار کاربران", callback_data="users_chart")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="advanced_analytics")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "📊 *نمودارهای استفاده*\n\n"
            "📈 تصویرسازی داده‌های استفاده\n"
            "🔍 تحلیل روند استفاده در بازه‌های مختلف\n"
            "📊 مقایسه عملکرد انواع توکن‌ها\n\n"
            "نوع نمودار مورد نظر را انتخاب کنید:"
        )
        
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        await update.callback_query.answer()
    
    # === Behavior Analysis ===
    async def show_behavior_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش تحلیل رفتار کاربران"""
        try:
            behavior_data = await self.analyze_user_behavior()
            
            keyboard = [
                [
                    InlineKeyboardButton("📋 جزئیات کامل", callback_data="detailed_behavior"),
                    InlineKeyboardButton("📊 نمودار رفتار", callback_data="behavior_chart")
                ],
                [
                    InlineKeyboardButton("🔍 کاربران فعال", callback_data="most_active_users"),
                    InlineKeyboardButton("😴 کاربران غیرفعال", callback_data="inactive_users")
                ],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="advanced_analytics")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = (
                f"🔍 *تحلیل رفتار کاربران*\n\n"
                f"📈 *الگوهای استفاده:*\n"
                f"• فعال‌ترین ساعت: {behavior_data['peak_hour']}:00\n"
                f"• فعال‌ترین روز: {behavior_data['peak_day']}\n"
                f"• میانگین جلسات: {behavior_data['avg_sessions']:.1f} / روز\n"
                f"• طول متوسط جلسه: {behavior_data['avg_session_duration']:.1f} دقیقه\n\n"
                f"🎯 *دسته‌بندی کاربران:*\n"
                f"• فعال روزانه: {behavior_data['daily_active']} نفر\n"
                f"• فعال هفتگی: {behavior_data['weekly_active']} نفر\n"
                f"• غیرفعال: {behavior_data['inactive']} نفر\n\n"
                f"برای جزئیات بیشتر گزینه مورد نظر را انتخاب کنید:"
            )
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            await update.callback_query.answer()
            
        except Exception as e:
            logger.error(f"Error showing behavior analysis: {e}")
            await update.callback_query.answer("❌ خطا در تحلیل رفتار!")
    
    # === Trend Prediction ===
    async def show_trend_prediction(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش پیش‌بینی ترند"""
        try:
            prediction_data = await self.predict_usage_trends()
            
            keyboard = [
                [
                    InlineKeyboardButton("📅 پیش‌بینی هفته آینده", callback_data="next_week_prediction"),
                    InlineKeyboardButton("📆 پیش‌بینی ماه آینده", callback_data="next_month_prediction")
                ],
                [
                    InlineKeyboardButton("📊 تحلیل فصلی", callback_data="seasonal_analysis"),
                    InlineKeyboardButton("⚡ نقاط اوج پیش‌بینی", callback_data="peak_predictions")
                ],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="advanced_analytics")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            trend_icon = "📈" if prediction_data['trend'] == 'increasing' else "📉" if prediction_data['trend'] == 'decreasing' else "➡️"
            
            text = (
                f"📈 *پیش‌بینی ترندهای استفاده*\n\n"
                f"🎯 *وضعیت فعلی:*\n"
                f"• روند کلی: {trend_icon} {prediction_data['trend_persian']}\n"
                f"• اعتماد پیش‌بینی: {prediction_data['confidence']:.0f}%\n"
                f"• نرخ رشد پیش‌بینی: {prediction_data['growth_rate']:+.1f}%\n\n"
                f"📊 *پیش‌بینی‌های کلیدی:*\n"
                f"• استفاده هفته آینده: {prediction_data['next_week_usage']} درخواست\n"
                f"• بیشینه بار پیش‌بینی: {prediction_data['predicted_peak']} درخواست\n"
                f"• احتمال اوج بار: {prediction_data['peak_probability']:.0f}%\n\n"
                f"برای جزئیات بیشتر گزینه مورد نظر را انتخاب کنید:"
            )
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            await update.callback_query.answer()
            
        except Exception as e:
            logger.error(f"Error showing trend prediction: {e}")
            await update.callback_query.answer("❌ خطا در پیش‌بینی ترند!")
    
    # === Performance Statistics ===
    async def show_performance_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش آمار عملکرد"""
        try:
            perf_data = await self.get_performance_statistics()
            
            keyboard = [
                [
                    InlineKeyboardButton("⚡ جزئیات سرعت", callback_data="speed_details"),
                    InlineKeyboardButton("📊 آمار خطاها", callback_data="error_statistics")
                ],
                [
                    InlineKeyboardButton("🔄 بهینه‌سازی خودکار", callback_data="auto_optimization"),
                    InlineKeyboardButton("📈 مقایسه عملکرد", callback_data="performance_comparison")
                ],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="advanced_analytics")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Status indicators
            response_status = "🟢" if perf_data['avg_response_time'] < 100 else "🟡" if perf_data['avg_response_time'] < 500 else "🔴"
            error_status = "🟢" if perf_data['error_rate'] < 1 else "🟡" if perf_data['error_rate'] < 5 else "🔴"
            uptime_status = "🟢" if perf_data['uptime'] > 99 else "🟡" if perf_data['uptime'] > 95 else "🔴"
            
            text = (
                f"⚡ *آمار عملکرد سیستم*\n\n"
                f"🎯 *شاخص‌های کلیدی:*\n"
                f"• زمان پاسخ: {response_status} {perf_data['avg_response_time']:.1f}ms\n"
                f"• نرخ خطا: {error_status} {perf_data['error_rate']:.2f}%\n"
                f"• زمان فعالیت: {uptime_status} {perf_data['uptime']:.1f}%\n"
                f"• تعداد درخواست‌ها: {perf_data['total_requests']:,}\n\n"
                f"📊 *تفصیلات عملکرد:*\n"
                f"• سریع‌ترین پاسخ: {perf_data['fastest_response']:.1f}ms\n"
                f"• کندترین پاسخ: {perf_data['slowest_response']:.1f}ms\n"
                f"• میانه زمان پاسخ: {perf_data['median_response']:.1f}ms\n"
                f"• درصد موفقیت: {perf_data['success_rate']:.1f}%\n\n"
                f"برای تحلیل عمیق‌تر گزینه مورد نظر را انتخاب کنید:"
            )
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            await update.callback_query.answer()
            
        except Exception as e:
            logger.error(f"Error showing performance stats: {e}")
            await update.callback_query.answer("❌ خطا در آمار عملکرد!")
    
    # === Geographic Analysis ===
    async def show_geo_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش تحلیل جغرافیایی"""
        try:
            geo_data = await self.get_geographic_analysis()
            
            keyboard = [
                [
                    InlineKeyboardButton("🗺 نقشه استفاده", callback_data="usage_map"),
                    InlineKeyboardButton("🌍 آمار کشورها", callback_data="countries_stats")
                ],
                [
                    InlineKeyboardButton("🏙 آمار شهرها", callback_data="cities_stats"),
                    InlineKeyboardButton("🌐 تحلیل IP", callback_data="ip_analysis")
                ],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="advanced_analytics")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = (
                f"🌍 *تحلیل جغرافیایی استفاده*\n\n"
                f"📊 *توزیع جغرافیایی:*\n"
                f"• تعداد کشورها: {geo_data['total_countries']}\n"
                f"• تعداد شهرها: {geo_data['total_cities']}\n"
                f"• پربازدیدترین کشور: {geo_data['top_country']}\n"
                f"• پربازدیدترین شهر: {geo_data['top_city']}\n\n"
                f"🎯 *5 کشور برتر:*\n"
            )
            
            for i, country_data in enumerate(geo_data['top_countries'][:5], 1):
                text += f"• {i}. {country_data['name']}: {country_data['usage']} درخواست\n"
            
            text += "\nبرای تحلیل عمیق‌تر گزینه مورد نظر را انتخاب کنید:"
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            await update.callback_query.answer()
            
        except Exception as e:
            logger.error(f"Error showing geo analysis: {e}")
            await update.callback_query.answer("❌ خطا در تحلیل جغرافیایی!")
    
    # === Optimization Recommendations ===
    async def show_optimization_recommendations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش توصیه‌های بهینه‌سازی"""
        try:
            recommendations = await self.generate_optimization_recommendations()
            
            keyboard = [
                [
                    InlineKeyboardButton("🚀 اعمال توصیه‌ها", callback_data="apply_recommendations"),
                    InlineKeyboardButton("📊 شبیه‌سازی تأثیر", callback_data="simulate_impact")
                ],
                [
                    InlineKeyboardButton("📋 گزارش کامل", callback_data="full_recommendations_report"),
                    InlineKeyboardButton("⚙️ تنظیمات سفارشی", callback_data="custom_optimization")
                ],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="advanced_analytics")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = (
                f"🎯 *توصیه‌های بهینه‌سازی*\n\n"
                f"📈 *امتیاز عملکرد فعلی: {recommendations['current_score']}/100*\n\n"
                f"🚀 *توصیه‌های اولویت بالا:*\n"
            )
            
            for i, rec in enumerate(recommendations['high_priority'][:3], 1):
                impact = "🔥" if rec['impact'] == 'high' else "🔸" if rec['impact'] == 'medium' else "🔹"
                text += f"• {impact} {rec['title']}\n  💡 {rec['description']}\n  📊 بهبود پیش‌بینی: +{rec['expected_improvement']}%\n\n"
            
            if recommendations['medium_priority']:
                text += f"⚠️ *توصیه‌های اولویت متوسط:* {len(recommendations['medium_priority'])} مورد\n"
            
            if recommendations['low_priority']:
                text += f"📝 *توصیه‌های اولویت پایین:* {len(recommendations['low_priority'])} مورد\n"
            
            text += f"\n🎯 *امتیاز پیش‌بینی بعد از بهینه‌سازی: {recommendations['predicted_score']}/100*"
            
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            await update.callback_query.answer()
            
        except Exception as e:
            logger.error(f"Error showing optimization recommendations: {e}")
            await update.callback_query.answer("❌ خطا در تولید توصیه‌ها!")
    
    # === Helper Methods ===
    async def get_quick_analytics_stats(self) -> Dict[str, Any]:
        """دریافت آمار سریع برای analytics"""
        try:
            tokens = await self.db.get_all_tokens()
            active_tokens = len([t for t in tokens if t.get('active', True)])
            
            # Simulate some analytics (in real implementation, this would come from logs/database)
            return {
                'active_tokens': active_tokens,
                'today_requests': 1245,  # This should come from actual logs
                'growth_rate': 12.5,     # This should be calculated from historical data
                'avg_usage': 45.2        # This should be calculated from usage data
            }
        except Exception as e:
            logger.error(f"Error getting quick analytics stats: {e}")
            return {
                'active_tokens': 0,
                'today_requests': 0,
                'growth_rate': 0,
                'avg_usage': 0
            }
    
    async def analyze_user_behavior(self) -> Dict[str, Any]:
        """تحلیل رفتار کاربران - simplified mock"""
        # In real implementation, this would analyze actual usage logs
        return {
            'peak_hour': 14,
            'peak_day': 'یکشنبه',
            'avg_sessions': 3.2,
            'avg_session_duration': 15.5,
            'daily_active': 45,
            'weekly_active': 120,
            'inactive': 15
        }
    
    async def predict_usage_trends(self) -> Dict[str, Any]:
        """پیش‌بینی ترند استفاده - simplified mock"""
        return {
            'trend': 'increasing',
            'trend_persian': 'صعودی',
            'confidence': 85.2,
            'growth_rate': 12.5,
            'next_week_usage': 8500,
            'predicted_peak': 1200,
            'peak_probability': 78
        }
    
    async def get_performance_statistics(self) -> Dict[str, Any]:
        """آمار عملکرد - simplified mock"""
        return {
            'avg_response_time': 125.5,
            'error_rate': 0.8,
            'uptime': 99.7,
            'total_requests': 125486,
            'fastest_response': 23.1,
            'slowest_response': 2340.5,
            'median_response': 98.2,
            'success_rate': 99.2
        }
    
    async def get_geographic_analysis(self) -> Dict[str, Any]:
        """تحلیل جغرافیایی - simplified mock"""
        return {
            'total_countries': 15,
            'total_cities': 45,
            'top_country': 'ایران',
            'top_city': 'تهران',
            'top_countries': [
                {'name': 'ایران', 'usage': 8500},
                {'name': 'آلمان', 'usage': 1200},
                {'name': 'کانادا', 'usage': 890},
                {'name': 'انگلیس', 'usage': 650},
                {'name': 'فرانسه', 'usage': 420}
            ]
        }
    
    async def generate_optimization_recommendations(self) -> Dict[str, Any]:
        """تولید توصیه‌های بهینه‌سازی - simplified mock"""
        return {
            'current_score': 78,
            'predicted_score': 89,
            'high_priority': [
                {
                    'title': 'بهینه‌سازی کش API',
                    'description': 'پیاده‌سازی caching هوشمند برای درخواست‌های تکراری',
                    'impact': 'high',
                    'expected_improvement': 15
                },
                {
                    'title': 'حذف توکن‌های غیرفعال',
                    'description': 'پاکسازی توکن‌های بدون استفاده برای بهبود عملکرد',
                    'impact': 'medium',
                    'expected_improvement': 8
                }
            ],
            'medium_priority': [
                {
                    'title': 'تنظیم محدودیت‌های IP',
                    'description': 'محدودیت درخواست بر اساس IP',
                    'impact': 'medium',
                    'expected_improvement': 5
                }
            ],
            'low_priority': [
                {
                    'title': 'بهبود لاگ‌گذاری',
                    'description': 'ساختار بهتر برای لاگ‌ها',
                    'impact': 'low',
                    'expected_improvement': 2
                }
            ]
        }