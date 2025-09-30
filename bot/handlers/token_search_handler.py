#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token Search Handler - مدیریت کامل سیستم جستجوی توکن‌ها
"""

import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from handlers.base_handler import BaseHandler

logger = logging.getLogger(__name__)


class TokenSearchHandler(BaseHandler):
    """مدیریت کامل سیستم جستجوی توکن‌ها"""
    
    def __init__(self, db, token_manager):
        """
        Args:
            db: دیتابیس منیجر
            token_manager: TokenManagementHandler اصلی برای API calls
        """
        super().__init__(db)
        self.token_manager = token_manager
    
    # === MAIN SEARCH MENU ===
    
    async def show_advanced_search_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """منوی جستجوی پیشرفته"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت آمار جستجوهای اخیر کاربر
            user_id = update.effective_user.id
            recent_searches = context.user_data.get('recent_searches', [])
            
            text = "🔍 **جستجوی پیشرفته توکن‌ها**\n\n"
            text += "🎯 **معیارهای جستجو:**\n"
            text += "• **نام توکن:** جستجو در نام‌ها\n"
            text += "• **نوع توکن:** فیلتر بر اساس نوع\n"
            text += "• **وضعیت:** فعال، غیرفعال، منقضی\n"
            text += "• **تاریخ ایجاد:** بازه زمانی خاص\n"
            text += "• **آخرین استفاده:** بازه زمانی استفاده\n"
            text += "• **IP دسترسی:** بر اساس آخرین IP\n\n"
            
            if recent_searches:
                text += f"🕐 **آخرین جستجوها:** {len(recent_searches)} مورد\n\n"
            
            text += "⚙️ **فیلترهای ترکیبی:**\n"
            text += "امکان ترکیب چندین معیار برای جستجوی دقیق‌تر"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📝 جستجوی نام", callback_data="search_by_name"),
                    InlineKeyboardButton("🏷 جستجوی نوع", callback_data="search_by_type")
                ],
                [
                    InlineKeyboardButton("📊 جستجوی وضعیت", callback_data="search_by_status"),
                    InlineKeyboardButton("📅 جستجوی تاریخ", callback_data="search_by_date_range")
                ],
                [
                    InlineKeyboardButton("🌐 جستجوی IP", callback_data="search_by_ip"),
                    InlineKeyboardButton("📈 میزان استفاده", callback_data="search_by_usage")
                ],
                [
                    InlineKeyboardButton("🔄 فیلتر ترکیبی", callback_data="combined_search"),
                    InlineKeyboardButton("💾 ذخیره جستجو", callback_data="save_search")
                ],
                [
                    InlineKeyboardButton("🕐 جستجوهای اخیر", callback_data="recent_searches") if recent_searches else None,
                    InlineKeyboardButton("🗑 پاک کردن تاریخچه", callback_data="clear_search_history") if recent_searches else None
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="list_all_tokens")
                ]
            ])
            
            # حذف دکمه‌های None
            keyboard.inline_keyboard = [[btn for btn in row if btn] for row in keyboard.inline_keyboard]
            keyboard.inline_keyboard = [row for row in keyboard.inline_keyboard if row]
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_advanced_search_menu: {e}")
            await self.handle_error(update, context, e)
    
    # === SEARCH BY NAME ===
    
    async def search_by_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """جستجو بر اساس نام توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "📝 **جستجو بر اساس نام توکن**\n\n"
            text += "لطفاً نام یا بخشی از نام توکن را وارد کنید:\n\n"
            text += "📝 **راهنما:**\n"
            text += "• حداقل 2 کاراکتر لازم است\n"
            text += "• جستجو حساس به حروف کوچک و بزرگ نیست\n"
            text += "• می‌توانید بخشی از نام را وارد کنید\n"
            text += "• از * برای جایگزین استفاده کنید\n\n"
            text += "💡 **مثال:** `admin*` برای یافتن تمام نام‌های شروع شده با admin"
            
            # ذخیره نوع جستجوی فعلی
            context.user_data['current_search_type'] = 'name'
            context.user_data['awaiting_search_input'] = True
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("❌ انصراف", callback_data="search_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in search_by_name: {e}")
            await self.handle_error(update, context, e)
    
    # === SEARCH BY TYPE ===
    
    async def search_by_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """جستجو بر اساس نوع توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🏷 **جستجو بر اساس نوع توکن**\n\n"
            text += "نوع توکن مورد نظر را انتخاب کنید:\n\n"
            text += "🔧 **انواع توکن:**\n"
            text += "• **مدیر:** دسترسی کامل به سیستم\n"
            text += "• **محدود:** دسترسی محدود\n"
            text += "• **کاربر:** دسترسی عادی\n"
            text += "• **API:** توکن‌های API"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🛡 مدیر", callback_data="filter_type_admin"),
                    InlineKeyboardButton("⚙️ محدود", callback_data="filter_type_limited")
                ],
                [
                    InlineKeyboardButton("👤 کاربر", callback_data="filter_type_user"),
                    InlineKeyboardButton("🔧 API", callback_data="filter_type_api")
                ],
                [
                    InlineKeyboardButton("🎯 همه انواع", callback_data="filter_type_all"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in search_by_type: {e}")
            await self.handle_error(update, context, e)
    
    # === SEARCH BY STATUS ===
    
    async def search_by_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """جستجو بر اساس وضعیت توکن"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "📊 **جستجو بر اساس وضعیت توکن**\n\n"
            text += "وضعیت مورد نظر را انتخاب کنید:\n\n"
            text += "🔍 **انواع وضعیت:**\n"
            text += "• **فعال:** توکن‌های در حال استفاده\n"
            text += "• **غیرفعال:** توکن‌های غیرفعال شده\n"
            text += "• **منقضی:** توکن‌های گذشته از تاریخ انقضا\n"
            text += "• **نزدیک انقضا:** کمتر از 7 روز باقی‌مانده"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🟢 فعال", callback_data="filter_status_active"),
                    InlineKeyboardButton("🔴 غیرفعال", callback_data="filter_status_inactive")
                ],
                [
                    InlineKeyboardButton("⏰ منقضی", callback_data="filter_status_expired"),
                    InlineKeyboardButton("⚠️ نزدیک انقضا", callback_data="filter_status_expiring")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in search_by_status: {e}")
            await self.handle_error(update, context, e)
    
    # === SEARCH BY DATE RANGE ===
    
    async def search_by_date_range(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """جستجو بر اساس بازه زمانی"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "📅 **جستجو بر اساس تاریخ ایجاد**\n\n"
            text += "بازه زمانی مورد نظر را انتخاب کنید:\n\n"
            text += "🗓 **بازه‌های زمانی:**\n"
            text += "• **امروز:** توکن‌های ایجاد شده امروز\n"
            text += "• **هفته اخیر:** 7 روز گذشته\n"
            text += "• **ماه اخیر:** 30 روز گذشته\n"
            text += "• **سفارشی:** انتخاب تاریخ دلخواه"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📅 امروز", callback_data="filter_date_today"),
                    InlineKeyboardButton("📊 این هفته", callback_data="filter_date_week")
                ],
                [
                    InlineKeyboardButton("📆 این ماه", callback_data="filter_date_month"),
                    InlineKeyboardButton("📈 3 ماه اخیر", callback_data="filter_date_3months")
                ],
                [
                    InlineKeyboardButton("🎯 بازه سفارشی", callback_data="filter_date_custom"),
                    InlineKeyboardButton("📋 همه تاریخ‌ها", callback_data="filter_date_all")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in search_by_date_range: {e}")
            await self.handle_error(update, context, e)
    
    # === SEARCH BY IP ===
    
    async def search_by_ip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """جستجو بر اساس IP"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🌐 **جستجو بر اساس IP دسترسی**\n\n"
            text += "لطفاً IP مورد نظر یا روش جستجو را انتخاب کنید:\n\n"
            text += "🔍 **روش‌های جستجو:**\n"
            text += "• **IP مشخص:** جستجوی IP کامل\n"
            text += "• **محدوده IP:** جستجو در یک بازه\n"
            text += "• **کشور خاص:** بر اساس موقعیت جغرافیایی\n"
            text += "• **IP های مشکوک:** فعالیت‌های غیرعادی\n\n"
            text += "📝 **مثال:** `192.168.1.*` یا `192.168.1.100`"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🎯 IP مشخص", callback_data="search_specific_ip"),
                    InlineKeyboardButton("📊 محدوده IP", callback_data="search_ip_range")
                ],
                [
                    InlineKeyboardButton("🌍 بر اساس کشور", callback_data="search_by_country"),
                    InlineKeyboardButton("⚠️ IP های مشکوک", callback_data="search_suspicious_ips")
                ],
                [
                    InlineKeyboardButton("📋 پربازدیدترین IP ها", callback_data="search_top_ips"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in search_by_ip: {e}")
            await self.handle_error(update, context, e)
    
    # === FILTER HANDLERS ===
    
    async def handle_filter_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش فیلتر نوع توکن"""
        try:
            query = update.callback_query
            await query.answer("در حال جستجو...")
            
            # استخراج نوع از callback_data
            token_type = query.data.split('_')[-1]
            
            # جستجو در توکن‌ها
            result = await self.token_manager.search_tokens_by_type(token_type)
            
            await self._display_search_results(
                update, context, result, 
                title=f"🏷 توکن‌های نوع {self._get_token_type_name(token_type)}",
                search_type="type",
                search_value=token_type
            )
            
        except Exception as e:
            logger.error(f"Error in handle_filter_type: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_filter_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش فیلتر وضعیت توکن"""
        try:
            query = update.callback_query
            await query.answer("در حال جستجو...")
            
            # استخراج وضعیت از callback_data
            status = query.data.split('_')[-1]
            
            # جستجو در توکن‌ها
            result = await self.token_manager.search_tokens_by_status(status)
            
            status_names = {
                'active': 'فعال',
                'inactive': 'غیرفعال', 
                'expired': 'منقضی',
                'expiring': 'نزدیک انقضا'
            }
            
            await self._display_search_results(
                update, context, result,
                title=f"📊 توکن‌های {status_names.get(status, status)}",
                search_type="status", 
                search_value=status
            )
            
        except Exception as e:
            logger.error(f"Error in handle_filter_status: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_filter_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش فیلتر تاریخ"""
        try:
            query = update.callback_query
            await query.answer("در حال جستجو...")
            
            # استخراج بازه تاریخ از callback_data
            date_range = query.data.split('_')[-1]
            
            # محاسبه تاریخ شروع و پایان
            end_date = datetime.now()
            
            if date_range == 'today':
                start_date = end_date.replace(hour=0, minute=0, second=0)
                title = "📅 توکن‌های ایجاد شده امروز"
            elif date_range == 'week':
                start_date = end_date - timedelta(days=7)
                title = "📊 توکن‌های هفته اخیر"
            elif date_range == 'month':
                start_date = end_date - timedelta(days=30)
                title = "📆 توکن‌های ماه اخیر"
            elif date_range == '3months':
                start_date = end_date - timedelta(days=90)
                title = "📈 توکن‌های 3 ماه اخیر"
            elif date_range == 'all':
                start_date = datetime(2020, 1, 1)
                title = "📋 تمام توکن‌ها"
            else:
                await query.edit_message_text(
                    "❌ بازه زمانی نامعتبر!",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="search_by_date_range")
                    ]])
                )
                return
            
            # جستجو در توکن‌ها
            result = await self.token_manager.search_tokens_by_date_range(start_date, end_date)
            
            await self._display_search_results(
                update, context, result,
                title=title,
                search_type="date",
                search_value=date_range
            )
            
        except Exception as e:
            logger.error(f"Error in handle_filter_date: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_search_specific_ip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """جستجوی IP مشخص"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🎯 **جستجوی IP مشخص**\n\n"
            text += "لطفاً IP مورد نظر را وارد کنید:\n\n"
            text += "📝 **فرمت‌های مجاز:**\n"
            text += "• IP کامل: `192.168.1.100`\n"
            text += "• با ماسک: `192.168.1.*`\n"
            text += "• محدوده: `192.168.1.1-100`\n\n"
            text += "⚠️ **نکته:** جستجو دقیق انجام می‌شود"
            
            # ذخیره نوع جستجوی فعلی
            context.user_data['current_search_type'] = 'specific_ip'
            context.user_data['awaiting_search_input'] = True
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("❌ انصراف", callback_data="search_by_ip")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_search_specific_ip: {e}")
            await self.handle_error(update, context, e)
    
    # === PAGINATION HANDLER ===
    
    async def handle_paginated_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش صفحه‌بندی نتایج جستجو"""
        try:
            query = update.callback_query
            await query.answer()
            
            # Parse callback data: search_results_{type}_{value}_{page}
            callback_data = query.data
            parts = callback_data.replace('search_results_', '').rsplit('_', 1)
            
            if len(parts) != 2:
                await query.answer("❌ خطا در پردازش صفحه‌بندی")
                return
            
            type_value = parts[0]
            page = int(parts[1])
            
            # Extract search_type and search_value
            type_value_parts = type_value.split('_', 1)
            if len(type_value_parts) != 2:
                await query.answer("❌ خطا در پردازش")
                return
            
            search_type = type_value_parts[0]
            search_value = type_value_parts[1]
            
            # Re-execute search based on type
            result = None
            title = ""
            
            if search_type == 'type':
                result = await self.token_manager.search_tokens_by_type(search_value)
                title = f"🏷 توکن‌های نوع {self._get_token_type_name(search_value)}"
            elif search_type == 'status':
                result = await self.token_manager.search_tokens_by_status(search_value)
                status_names = {'active': 'فعال', 'inactive': 'غیرفعال', 'expired': 'منقضی', 'expiring': 'نزدیک انقضا'}
                title = f"📊 توکن‌های {status_names.get(search_value, search_value)}"
            elif search_type == 'date':
                # Parse date range from value
                end_date = datetime.now()
                if search_value == 'today':
                    start_date = end_date.replace(hour=0, minute=0, second=0)
                    title = "📅 توکن‌های امروز"
                elif search_value == 'week':
                    start_date = end_date - timedelta(days=7)
                    title = "📊 توکن‌های هفته اخیر"
                elif search_value == 'month':
                    start_date = end_date - timedelta(days=30)
                    title = "📆 توکن‌های ماه اخیر"
                elif search_value == '3months':
                    start_date = end_date - timedelta(days=90)
                    title = "📈 توکن‌های 3 ماه اخیر"
                else:
                    start_date = datetime(2020, 1, 1)
                    title = "📋 تمام توکن‌ها"
                result = await self.token_manager.search_tokens_by_date_range(start_date, end_date)
            elif search_type == 'name':
                result = await self.token_manager.search_tokens_by_name(search_value)
                title = f"📝 جستجوی نام: {search_value}"
            elif search_type in ['ip', 'specific_ip']:
                result = await self.token_manager.search_tokens_by_ip(search_value)
                title = f"🌐 جستجوی IP: {search_value}"
            elif search_type == 'usage':
                # Parse usage range from value
                usage_parts = search_value.split('_')
                min_usage = int(usage_parts[0]) if len(usage_parts) > 0 else 0
                max_usage = int(usage_parts[1]) if len(usage_parts) > 1 and usage_parts[1] != 'unlimited' else None
                result = await self.token_manager.search_tokens_by_usage(min_usage, max_usage)
                title = f"📊 توکن‌ها با استفاده {min_usage}+"
            elif search_type == 'country':
                result = await self.token_manager.search_tokens_by_country(search_value)
                title = f"🌍 توکن‌های کشور {search_value}"
            elif search_type == 'combined':
                # For combined search, re-execute with stored filters
                filters = context.user_data.get('combined_filters', {})
                result = await self.token_manager.get_all_tokens()  # Simplified - can be enhanced
                title = "🔍 نتایج جستجوی ترکیبی"
            else:
                result = {'success': True, 'tokens': []}
                title = "🔍 نتایج جستجو"
            
            # Display results with pagination
            await self._display_search_results(
                update, context, result, title, search_type, search_value, page
            )
            
        except Exception as e:
            logger.error(f"Error in handle_paginated_results: {e}")
            await self.handle_error(update, context, e)
    
    # === SEARCH RESULTS DISPLAY ===
    
    async def _display_search_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                     result: Dict[str, Any], title: str, search_type: str, 
                                     search_value: str, page: int = 1):
        """نمایش نتایج جستجو"""
        try:
            query = update.callback_query
            
            if not result.get('success'):
                text = "❌ **خطا در جستجو**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}"
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                ]])
                
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
                return
            
            tokens = result.get('tokens', [])
            total_count = result.get('total_count', len(tokens))
            
            # ذخیره جستجو در تاریخچه
            await self._save_search_to_history(context, search_type, search_value, total_count)
            
            if not tokens:
                text = f"🔍 **{title}**\n\n"
                text += "❌ هیچ توکنی با این معیار یافت نشد!\n\n"
                text += "💡 **پیشنهادها:**\n"
                text += "• معیار جستجو را تغییر دهید\n"
                text += "• از فیلتر ترکیبی استفاده کنید\n"
                text += "• جستجوی کلی انجام دهید"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 جستجوی مجدد", callback_data="search_tokens"),
                        InlineKeyboardButton("📋 همه توکن‌ها", callback_data="list_all_tokens")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                    ]
                ])
                
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
                return
            
            # صفحه‌بندی
            items_per_page = 8
            total_pages = (total_count + items_per_page - 1) // items_per_page
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            page_tokens = tokens[start_idx:end_idx]
            
            text = f"🔍 **{title}**\n\n"
            text += f"📊 **یافت شده:** {total_count} توکن"
            if total_pages > 1:
                text += f" | صفحه {page} از {total_pages}"
            text += "\n\n"
            
            for i, token in enumerate(page_tokens, start_idx + 1):
                status_icon = "🟢" if token.get('is_active', True) else "🔴"
                type_icon = self._get_token_type_icon(token.get('type', 'user'))
                
                text += f"{i}. {type_icon} **{token.get('name', f'توکن {i}')}** {status_icon}\n"
                text += f"   🆔 `{token.get('token_id', 'N/A')}`\n"
                text += f"   🏷 {self._get_token_type_name(token.get('type', 'user'))}\n"
                text += f"   📅 {token.get('created_at', 'نامشخص')[:16]}\n"
                
                # اطلاعات اضافی بر اساس نوع جستجو
                if search_type == 'ip' and token.get('last_ip'):
                    text += f"   🌐 IP: `{token.get('last_ip')}`\n"
                elif search_type == 'status' and token.get('expires_at'):
                    text += f"   ⏰ انقضا: {token.get('expires_at')[:16]}\n"
                
                text += "\n"
            
            # ساخت کیبورد
            buttons = []
            
            # دکمه‌های صفحه‌بندی
            if total_pages > 1:
                nav_buttons = []
                if page > 1:
                    nav_buttons.append(InlineKeyboardButton(
                        "⬅️ قبلی", 
                        callback_data=f"search_results_{search_type}_{search_value}_{page-1}"
                    ))
                if page < total_pages:
                    nav_buttons.append(InlineKeyboardButton(
                        "➡️ بعدی", 
                        callback_data=f"search_results_{search_type}_{search_value}_{page+1}"
                    ))
                if nav_buttons:
                    buttons.append(nav_buttons)
            
            # دکمه‌های عملیاتی
            buttons.extend([
                [
                    InlineKeyboardButton("💾 صادرات نتایج", callback_data=f"export_search_results_{search_type}_{search_value}"),
                    InlineKeyboardButton("📊 آمار نتایج", callback_data=f"search_results_stats_{search_type}_{search_value}")
                ],
                [
                    InlineKeyboardButton("🔄 جستجوی جدید", callback_data="search_tokens"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                ]
            ])
            
            keyboard = InlineKeyboardMarkup(buttons)
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in _display_search_results: {e}")
            await self.handle_error(update, context, e)
    
    # === SEARCH HISTORY MANAGEMENT ===
    
    async def _save_search_to_history(self, context: ContextTypes.DEFAULT_TYPE, search_type: str, search_value: str, result_count: int):
        """ذخیره جستجو در تاریخچه"""
        try:
            if 'recent_searches' not in context.user_data:
                context.user_data['recent_searches'] = []
            
            search_entry = {
                'type': search_type,
                'value': search_value,
                'result_count': result_count,
                'timestamp': datetime.now().isoformat(),
                'display_name': self._get_search_display_name(search_type, search_value)
            }
            
            # اضافه کردن به ابتدای لیست
            context.user_data['recent_searches'].insert(0, search_entry)
            
            # حداکثر 20 جستجوی اخیر نگه داری
            if len(context.user_data['recent_searches']) > 20:
                context.user_data['recent_searches'] = context.user_data['recent_searches'][:20]
            
        except Exception as e:
            logger.error(f"Error saving search to history: {e}")
    
    def _get_search_display_name(self, search_type: str, search_value: str) -> str:
        """نام نمایشی جستجو"""
        display_names = {
            'type': {
                'admin': '🛡 توکن‌های مدیر',
                'limited': '⚙️ توکن‌های محدود', 
                'user': '👤 توکن‌های کاربر',
                'api': '🔧 توکن‌های API'
            },
            'status': {
                'active': '🟢 توکن‌های فعال',
                'inactive': '🔴 توکن‌های غیرفعال',
                'expired': '⏰ توکن‌های منقضی',
                'expiring': '⚠️ نزدیک انقضا'
            },
            'date': {
                'today': '📅 امروز',
                'week': '📊 این هفته',
                'month': '📆 این ماه',
                '3months': '📈 3 ماه اخیر',
                'all': '📋 همه'
            }
        }
        
        if search_type in display_names and search_value in display_names[search_type]:
            return display_names[search_type][search_value]
        elif search_type == 'name':
            return f"📝 نام: {search_value}"
        elif search_type == 'specific_ip':
            return f"🌐 IP: {search_value}"
        else:
            return f"🔍 {search_type}: {search_value}"
    
    async def show_recent_searches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش جستجوهای اخیر"""
        try:
            query = update.callback_query
            await query.answer()
            
            recent_searches = context.user_data.get('recent_searches', [])
            
            if not recent_searches:
                text = "🕐 **جستجوهای اخیر**\n\n"
                text += "❌ هنوز هیچ جستجویی انجام نداده‌اید!\n\n"
                text += "💡 با استفاده از گزینه‌های جستجو، تاریخچه شما ایجاد خواهد شد."
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔍 شروع جستجو", callback_data="search_tokens")
                ]])
            else:
                text = "🕐 **جستجوهای اخیر**\n\n"
                text += f"📊 **تعداد:** {len(recent_searches)} جستجو\n\n"
                
                buttons = []
                for i, search in enumerate(recent_searches[:10], 1):
                    display_name = search['display_name']
                    result_count = search['result_count']
                    timestamp = search['timestamp'][:16].replace('T', ' ')
                    
                    text += f"{i}. {display_name}\n"
                    text += f"   📊 {result_count} نتیجه | 🕐 {timestamp}\n\n"
                    
                    buttons.append([InlineKeyboardButton(
                        f"🔄 اجرای مجدد #{i}", 
                        callback_data=f"repeat_search_{i-1}"
                    )])
                
                if len(recent_searches) > 10:
                    text += f"... و {len(recent_searches) - 10} جستجوی دیگر\n\n"
                
                buttons.extend([
                    [
                        InlineKeyboardButton("🗑 پاک کردن تاریخچه", callback_data="clear_search_history"),
                        InlineKeyboardButton("💾 صادرات تاریخچه", callback_data="export_search_history")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                    ]
                ])
                
                keyboard = InlineKeyboardMarkup(buttons)
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_recent_searches: {e}")
            await self.handle_error(update, context, e)
    
    async def clear_search_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پاک کردن تاریخچه جستجو"""
        try:
            query = update.callback_query
            await query.answer("✅ تاریخچه پاک شد")
            
            context.user_data['recent_searches'] = []
            
            text = "🗑 **پاک کردن تاریخچه**\n\n"
            text += "✅ تاریخچه جستجوهای شما با موفقیت پاک شد.\n\n"
            text += "💡 جستجوهای جدید شما دوباره ذخیره خواهند شد."
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔍 شروع جستجوی جدید", callback_data="search_tokens")
            ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in clear_search_history: {e}")
            await self.handle_error(update, context, e)
    
    # === HELPER METHODS ===
    
    def _get_token_type_name(self, token_type: str) -> str:
        """نام فارسی نوع توکن"""
        types = {
            'admin': 'مدیر',
            'limited': 'محدود',
            'user': 'کاربر',
            'api': 'API'
        }
        return types.get(token_type, 'نامشخص')
    
    def _get_token_type_icon(self, token_type: str) -> str:
        """آیکون نوع توکن"""
        icons = {
            'admin': '🛡',
            'limited': '⚙️',
            'user': '👤',
            'api': '🔧'
        }
        return icons.get(token_type, '❓')
    
    # === MESSAGE HANDLING ===
    
    async def handle_search_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش ورودی جستجو از کاربر"""
        try:
            # بررسی ورودی برای ذخیره نام جستجو
            if context.user_data.get('awaiting_search_name'):
                await self.handle_confirm_save_search(update, context)
                return True
            
            if not context.user_data.get('awaiting_search_input'):
                return False
            
            search_type = context.user_data.get('current_search_type')
            search_term = update.message.text.strip()
            
            if not search_term or len(search_term) < 2:
                await update.message.reply_text(
                    "❌ لطفاً حداقل 2 کاراکتر وارد کنید!",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                    ]])
                )
                return True
            
            # پاک کردن وضعیت انتظار
            context.user_data['awaiting_search_input'] = False
            context.user_data['current_search_type'] = None
            
            # انجام جستجو بر اساس نوع
            if search_type == 'name':
                result = await self.token_manager.search_tokens_by_name(search_term)
                title = f"📝 جستجوی نام: {search_term}"
            elif search_type == 'specific_ip':
                result = await self.token_manager.search_tokens_by_ip(search_term)
                title = f"🌐 جستجوی IP: {search_term}"
            elif search_type == 'ip_range':
                result = await self.token_manager.search_tokens_by_ip_range(search_term)
                title = f"📊 جستجوی محدوده IP: {search_term}"
            else:
                await update.message.reply_text("❌ نوع جستجوی نامعتبر!")
                return True
            
            # نمایش نتایج
            await self._display_search_results_message(
                update, context, result, title, search_type, search_term
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error in handle_search_input: {e}")
            await update.message.reply_text("❌ خطا در پردازش جستجو!")
            return True
    
    async def _display_search_results_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                            result: Dict[str, Any], title: str, search_type: str, search_value: str):
        """نمایش نتایج جستجو از پیام"""
        try:
            if not result.get('success'):
                text = "❌ **خطا در جستجو**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}"
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                ]])
                
                await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')
                return
            
            tokens = result.get('tokens', [])
            total_count = result.get('total_count', len(tokens))
            
            # ذخیره جستجو در تاریخچه
            await self._save_search_to_history(context, search_type, search_value, total_count)
            
            if not tokens:
                text = f"🔍 **{title}**\n\n"
                text += "❌ هیچ توکنی یافت نشد!\n\n"
                text += "💡 **پیشنهادها:**\n"
                text += "• کلمه جستجو را تغییر دهید\n"
                text += "• از * برای جستجوی گسترده استفاده کنید"
            else:
                text = f"🔍 **{title}**\n\n"
                text += f"📊 **یافت شده:** {total_count} توکن\n\n"
                
                for i, token in enumerate(tokens[:5], 1):
                    status_icon = "🟢" if token.get('is_active', True) else "🔴"
                    type_icon = self._get_token_type_icon(token.get('type', 'user'))
                    
                    text += f"{i}. {type_icon} **{token.get('name', f'توکن {i}')}** {status_icon}\n"
                    text += f"   🆔 `{token.get('token_id', 'N/A')}`\n"
                    text += f"   🏷 {self._get_token_type_name(token.get('type', 'user'))}\n\n"
                
                if total_count > 5:
                    text += f"... و {total_count - 5} توکن دیگر"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📋 مشاهده همه", callback_data=f"search_results_{search_type}_{search_value}_1") if total_count > 5 else None,
                    InlineKeyboardButton("🔄 جستجوی جدید", callback_data="search_tokens")
                ],
                [
                    InlineKeyboardButton("🔙 منوی جستجو", callback_data="search_tokens")
                ]
            ])
            
            # حذف دکمه‌های None
            keyboard.inline_keyboard[0] = [btn for btn in keyboard.inline_keyboard[0] if btn]
            
            await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in _display_search_results_message: {e}")
            await update.message.reply_text("❌ خطا در نمایش نتایج!")
    
    # === SEARCH BY USAGE ===
    
    async def search_by_usage(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """جستجو بر اساس میزان استفاده"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "📈 **جستجو بر اساس میزان استفاده**\n\n"
            text += "لطفاً محدوده استفاده مورد نظر را انتخاب کنید:\n\n"
            text += "📊 **محدوده‌های آماده:**\n"
            text += "• **بدون استفاده:** توکن‌های استفاده نشده\n"
            text += "• **کم استفاده:** کمتر از 100 بار\n"
            text += "• **متوسط:** 100 تا 1000 بار\n"
            text += "• **پراستفاده:** بیش از 1000 بار\n"
            text += "• **محدوده سفارشی:** تعیین دقیق بازه"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⭕ بدون استفاده", callback_data="filter_usage_0_0"),
                    InlineKeyboardButton("📉 کم (< 100)", callback_data="filter_usage_0_100")
                ],
                [
                    InlineKeyboardButton("📊 متوسط (100-1K)", callback_data="filter_usage_100_1000"),
                    InlineKeyboardButton("📈 زیاد (> 1K)", callback_data="filter_usage_1000_999999")
                ],
                [
                    InlineKeyboardButton("🔥 خیلی زیاد (> 10K)", callback_data="filter_usage_10000_999999"),
                    InlineKeyboardButton("🎯 محدوده سفارشی", callback_data="filter_usage_custom")
                ],
                [
                    InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in search_by_usage: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_filter_usage(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش فیلتر میزان استفاده"""
        try:
            query = update.callback_query
            await query.answer("در حال جستجو...")
            
            # استخراج محدوده از callback_data
            parts = query.data.split('_')
            if len(parts) >= 4:
                min_usage = int(parts[2])
                max_usage = int(parts[3]) if parts[3] != '999999' else None
            else:
                min_usage = 0
                max_usage = None
            
            # جستجو در توکن‌ها
            result = await self.token_manager.search_tokens_by_usage(min_usage, max_usage)
            
            # تعیین عنوان بر اساس محدوده
            if min_usage == 0 and (max_usage is None or max_usage == 0):
                title = "📊 توکن‌های بدون استفاده"
            elif min_usage == 0 and max_usage == 100:
                title = "📉 توکن‌های کم استفاده (< 100)"
            elif min_usage == 100 and max_usage == 1000:
                title = "📊 توکن‌های با استفاده متوسط (100-1K)"
            elif min_usage >= 1000:
                title = f"📈 توکن‌های پراستفاده (> {min_usage:,})"
            else:
                title = f"📊 توکن‌ها با استفاده {min_usage:,} تا {max_usage:,}" if max_usage else f"📈 توکن‌ها با بیش از {min_usage:,} استفاده"
            
            await self._display_search_results(
                update, context, result,
                title=title,
                search_type="usage",
                search_value=f"{min_usage}_{max_usage or 'unlimited'}"
            )
            
        except Exception as e:
            logger.error(f"Error in handle_filter_usage: {e}")
            await self.handle_error(update, context, e)
    
    # === ADVANCED IP SEARCH ===
    
    async def handle_search_ip_range(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """جستجوی محدوده IP"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "📊 **جستجوی محدوده IP**\n\n"
            text += "لطفاً محدوده IP مورد نظر را وارد کنید:\n\n"
            text += "📝 **فرمت‌های پشتیبانی شده:**\n"
            text += "• CIDR: `192.168.1.0/24`\n"
            text += "• Range: `192.168.1.1-192.168.1.100`\n"
            text += "• Wildcard: `192.168.1.*`\n\n"
            text += "💡 **مثال‌ها:**\n"
            text += "• `10.0.0.0/8` - کل شبکه کلاس A\n"
            text += "• `192.168.1.0/24` - شبکه محلی\n"
            text += "• `192.168.1.100-200` - محدوده مشخص"
            
            # ذخیره نوع جستجوی فعلی
            context.user_data['current_search_type'] = 'ip_range'
            context.user_data['awaiting_search_input'] = True
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📋 محدوده‌های رایج", callback_data="common_ip_ranges"),
                    InlineKeyboardButton("❌ انصراف", callback_data="search_by_ip")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_search_ip_range: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_search_by_country(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """جستجو بر اساس کشور"""
        try:
            query = update.callback_query
            await query.answer()
            
            text = "🌍 **جستجو بر اساس کشور**\n\n"
            text += "لطفاً کشور مورد نظر را انتخاب کنید:\n\n"
            text += "🗺 **کشورهای پراستفاده:**"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🇮🇷 ایران", callback_data="filter_country_IR"),
                    InlineKeyboardButton("🇺🇸 آمریکا", callback_data="filter_country_US")
                ],
                [
                    InlineKeyboardButton("🇩🇪 آلمان", callback_data="filter_country_DE"),
                    InlineKeyboardButton("🇬🇧 انگلستان", callback_data="filter_country_GB")
                ],
                [
                    InlineKeyboardButton("🇫🇷 فرانسه", callback_data="filter_country_FR"),
                    InlineKeyboardButton("🇳🇱 هلند", callback_data="filter_country_NL")
                ],
                [
                    InlineKeyboardButton("🇹🇷 ترکیه", callback_data="filter_country_TR"),
                    InlineKeyboardButton("🇦🇪 امارات", callback_data="filter_country_AE")
                ],
                [
                    InlineKeyboardButton("🌍 لیست کامل کشورها", callback_data="all_countries_list"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data="search_by_ip")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_search_by_country: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_filter_country(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش فیلتر کشور"""
        try:
            query = update.callback_query
            await query.answer("در حال جستجو...")
            
            # استخراج کد کشور از callback_data
            country_code = query.data.split('_')[-1]
            
            # جستجو در توکن‌ها
            result = await self.token_manager.search_tokens_by_country(country_code)
            
            # نام کشورها
            country_names = {
                'IR': '🇮🇷 ایران',
                'US': '🇺🇸 آمریکا',
                'DE': '🇩🇪 آلمان',
                'GB': '🇬🇧 انگلستان',
                'FR': '🇫🇷 فرانسه',
                'NL': '🇳🇱 هلند',
                'TR': '🇹🇷 ترکیه',
                'AE': '🇦🇪 امارات'
            }
            
            country_name = country_names.get(country_code, country_code)
            
            await self._display_search_results(
                update, context, result,
                title=f"🌍 توکن‌های کشور {country_name}",
                search_type="country",
                search_value=country_code
            )
            
        except Exception as e:
            logger.error(f"Error in handle_filter_country: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_search_suspicious_ips(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش IP های مشکوک"""
        try:
            query = update.callback_query
            await query.answer("در حال تحلیل...")
            
            # دریافت IP های مشکوک
            result = await self.token_manager.get_suspicious_ips()
            
            text = "⚠️ **IP های مشکوک**\n\n"
            
            if result.get('success'):
                ips = result.get('ips', [])
                
                if ips:
                    text += f"📊 **تعداد:** {len(ips)} IP مشکوک شناسایی شد\n\n"
                    
                    for i, ip_info in enumerate(ips[:10], 1):
                        text += f"{i}. 🔴 `{ip_info.get('ip', 'N/A')}`\n"
                        text += f"   ⚠️ دلیل: {ip_info.get('reason', 'نامشخص')}\n"
                        text += f"   📊 تعداد توکن: {ip_info.get('token_count', 0)}\n"
                        text += f"   🔥 تلاش ناموفق: {ip_info.get('failed_attempts', 0)}\n"
                        text += f"   🕐 آخرین فعالیت: {ip_info.get('last_seen', 'نامشخص')[:16]}\n\n"
                    
                    if len(ips) > 10:
                        text += f"... و {len(ips) - 10} IP مشکوک دیگر"
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("🔒 مسدود کردن همه", callback_data="block_all_suspicious_ips"),
                            InlineKeyboardButton("📋 گزارش کامل", callback_data="detailed_suspicious_report")
                        ],
                        [
                            InlineKeyboardButton("🔍 تحلیل عمیق", callback_data="deep_analysis_suspicious"),
                            InlineKeyboardButton("💾 صادرات لیست", callback_data="export_suspicious_ips")
                        ],
                        [
                            InlineKeyboardButton("🔙 بازگشت", callback_data="search_by_ip")
                        ]
                    ])
                else:
                    text += "✅ **هیچ IP مشکوکی یافت نشد!**\n\n"
                    text += "تمام IP ها در محدوده امن هستند."
                    
                    keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="search_by_ip")
                    ]])
            else:
                text += "❌ خطا در دریافت IP های مشکوک\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}"
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="search_by_ip")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_search_suspicious_ips: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_search_top_ips(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش پربازدیدترین IP ها"""
        try:
            query = update.callback_query
            await query.answer("در حال تحلیل...")
            
            # دریافت پربازدیدترین IP ها
            result = await self.token_manager.get_top_ips(limit=15)
            
            text = "📋 **پربازدیدترین IP ها**\n\n"
            
            if result.get('success'):
                ips = result.get('ips', [])
                
                if ips:
                    text += "📊 **15 IP برتر:**\n\n"
                    
                    for i, ip_info in enumerate(ips, 1):
                        # ایموجی بر اساس رتبه
                        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                        
                        text += f"{medal} `{ip_info.get('ip', 'N/A')}`\n"
                        text += f"   📊 درخواست‌ها: {ip_info.get('request_count', 0):,}\n"
                        text += f"   🔑 توکن‌ها: {ip_info.get('token_count', 0)}\n"
                        text += f"   🌍 کشور: {ip_info.get('country', 'نامشخص')}\n"
                        text += f"   🕐 آخرین فعالیت: {ip_info.get('last_seen', 'نامشخص')[:16]}\n\n"
                    
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("📊 نمودار آماری", callback_data="ip_stats_chart"),
                            InlineKeyboardButton("🔍 جزئیات IP اول", callback_data=f"ip_details_{ips[0].get('ip', '')}")
                        ],
                        [
                            InlineKeyboardButton("📈 آمار کامل", callback_data="full_ip_statistics"),
                            InlineKeyboardButton("💾 صادرات", callback_data="export_top_ips")
                        ],
                        [
                            InlineKeyboardButton("🔙 بازگشت", callback_data="search_by_ip")
                        ]
                    ])
                else:
                    text += "❌ هیچ داده‌ای یافت نشد!"
                    
                    keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت", callback_data="search_by_ip")
                    ]])
            else:
                text += "❌ خطا در دریافت آمار IP ها\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}"
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="search_by_ip")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_search_top_ips: {e}")
            await self.handle_error(update, context, e)
    
    # === COMBINED SEARCH ===
    
    async def show_combined_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """جستجوی ترکیبی با مدیریت state"""
        try:
            query = update.callback_query
            await query.answer()
            
            # دریافت فیلترهای فعلی از context
            user_id = update.effective_user.id
            filters = context.user_data.get('combined_filters', {})
            
            text = "🔄 **فیلتر ترکیبی**\n\n"
            text += "امکان ترکیب چندین معیار برای جستجوی دقیق‌تر:\n\n"
            text += "🔧 **معیارهای فعلی:**\n"
            
            # نمایش فیلترهای انتخاب شده
            if filters.get('type'):
                text += f"• نوع: {self._get_token_type_name(filters['type'])}\n"
            else:
                text += "• نوع: همه\n"
            
            if filters.get('status'):
                status_names = {'active': 'فعال', 'inactive': 'غیرفعال', 'expired': 'منقضی', 'expiring': 'نزدیک انقضا'}
                text += f"• وضعیت: {status_names.get(filters['status'], filters['status'])}\n"
            else:
                text += "• وضعیت: همه\n"
            
            if filters.get('date_from') or filters.get('date_to'):
                text += f"• تاریخ: {filters.get('date_from', 'ابتدا')} تا {filters.get('date_to', 'اکنون')}\n"
            else:
                text += "• تاریخ: همه\n"
            
            if filters.get('min_usage') is not None:
                text += f"• استفاده: {filters.get('min_usage', 0)} تا {filters.get('max_usage', 'نامحدود')}\n"
            else:
                text += "• استفاده: همه\n"
            
            text += "\n💡 فیلترها را یکی یکی اضافه کنید:"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🏷 افزودن نوع", callback_data="add_type_filter"),
                    InlineKeyboardButton("📊 افزودن وضعیت", callback_data="add_status_filter")
                ],
                [
                    InlineKeyboardButton("📅 افزودن تاریخ", callback_data="add_date_filter"),
                    InlineKeyboardButton("📈 افزودن استفاده", callback_data="add_usage_filter")
                ],
                [
                    InlineKeyboardButton("🔍 اجرای جستجو", callback_data="execute_combined_search"),
                    InlineKeyboardButton("🗑 پاک کردن فیلترها", callback_data="clear_combined_filters")
                ],
                [
                    InlineKeyboardButton("💾 ذخیره جستجو", callback_data="save_combined_search"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_combined_search: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_add_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """اضافه کردن فیلتر به جستجوی ترکیبی"""
        try:
            query = update.callback_query
            callback_data = query.data
            
            if callback_data == "add_type_filter":
                await self.search_by_type(update, context)
            elif callback_data == "add_status_filter":
                await self.search_by_status(update, context)
            elif callback_data == "add_date_filter":
                await self.search_by_date_range(update, context)
            elif callback_data == "add_usage_filter":
                await self.search_by_usage(update, context)
            
        except Exception as e:
            logger.error(f"Error in handle_add_filter: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_execute_combined_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """اجرای جستجوی ترکیبی"""
        try:
            query = update.callback_query
            await query.answer("در حال اجرای جستجوی ترکیبی...")
            
            filters = context.user_data.get('combined_filters', {})
            
            if not filters:
                await query.answer("❌ هیچ فیلتری انتخاب نشده است!", show_alert=True)
                return
            
            # اجرای جستجو بر اساس فیلترهای ترکیبی
            # این بخش نیاز به API endpoint خاص دارد که همه فیلترها را پشتیبانی کند
            # فعلاً از یک فیلتر اصلی استفاده می‌کنیم
            
            result = None
            title = "🔍 نتایج جستجوی ترکیبی"
            
            if filters.get('type'):
                result = await self.token_manager.search_tokens_by_type(filters['type'])
            elif filters.get('status'):
                result = await self.token_manager.search_tokens_by_status(filters['status'])
            else:
                result = await self.token_manager.get_all_tokens()
            
            # فیلتر کردن نتایج بر اساس سایر معیارها
            if result and result.get('success'):
                tokens = result.get('tokens', [])
                
                # فیلتر استفاده
                if filters.get('min_usage') is not None:
                    min_usage = filters['min_usage']
                    max_usage = filters.get('max_usage')
                    tokens = [t for t in tokens if t.get('usage_count', 0) >= min_usage and (max_usage is None or t.get('usage_count', 0) <= max_usage)]
                
                result['tokens'] = tokens
                result['total_count'] = len(tokens)
            
            await self._display_search_results(
                update, context, result,
                title=title,
                search_type="combined",
                search_value="multi_filter"
            )
            
        except Exception as e:
            logger.error(f"Error in handle_execute_combined_search: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_clear_combined_filters(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پاک کردن فیلترهای ترکیبی"""
        try:
            query = update.callback_query
            await query.answer("✅ فیلترها پاک شدند")
            
            context.user_data['combined_filters'] = {}
            
            await self.show_combined_search(update, context)
            
        except Exception as e:
            logger.error(f"Error in handle_clear_combined_filters: {e}")
            await self.handle_error(update, context, e)
    
    # === SAVE SEARCH ===
    
    async def handle_save_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ذخیره جستجوی فعلی"""
        try:
            query = update.callback_query
            await query.answer()
            
            # بررسی وجود فیلترها یا جستجوی اخیر
            filters = context.user_data.get('combined_filters', {})
            recent_searches = context.user_data.get('recent_searches', [])
            
            if not filters and not recent_searches:
                await query.answer("❌ هیچ جستجویی برای ذخیره وجود ندارد!", show_alert=True)
                return
            
            text = "💾 **ذخیره جستجو**\n\n"
            text += "لطفاً نامی برای این جستجو انتخاب کنید:\n\n"
            text += "📝 **نام باید:**\n"
            text += "• بین 3 تا 30 کاراکتر باشد\n"
            text += "• منحصر به فرد باشد\n"
            text += "• توصیفی و قابل فهم باشد\n\n"
            
            if filters:
                text += "🔧 **جستجوی فعلی شامل:**\n"
                for key, value in filters.items():
                    text += f"• {key}: {value}\n"
            
            # ذخیره حالت برای دریافت نام
            context.user_data['awaiting_search_name'] = True
            context.user_data['search_to_save'] = filters or recent_searches[0] if recent_searches else {}
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📝 نام پیشنهادی 1", callback_data=f"save_search_name_جستجوی_{datetime.now().strftime('%Y%m%d')}"),
                    InlineKeyboardButton("📝 نام پیشنهادی 2", callback_data="save_search_name_جستجوی_سفارشی")
                ],
                [
                    InlineKeyboardButton("❌ انصراف", callback_data="search_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_save_search: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_confirm_save_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأیید و ذخیره جستجو در دیتابیس"""
        try:
            query = update.callback_query
            
            # دریافت نام از callback یا از پیام
            if query:
                await query.answer("در حال ذخیره...")
                search_name = query.data.split('save_search_name_')[1] if 'save_search_name_' in query.data else None
            else:
                # نام از پیام متنی کاربر
                search_name = update.message.text.strip()
            
            if not search_name or len(search_name) < 3:
                await query.answer("❌ نام باید حداقل 3 کاراکتر باشد!", show_alert=True)
                return
            
            user_id = update.effective_user.id
            search_params = context.user_data.get('search_to_save', {})
            
            # ذخیره در دیتابیس
            result = await self.token_manager.save_search_to_db(user_id, search_name, search_params)
            
            if result.get('success'):
                text = "✅ **جستجو ذخیره شد**\n\n"
                text += f"📝 **نام:** {search_name}\n"
                text += f"🆔 **شناسه:** {result.get('search_id')}\n"
                text += f"📅 **تاریخ:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                text += "می‌توانید از منوی \"جستجوهای ذخیره شده\" به آن دسترسی داشته باشید."
                
                # پاک کردن وضعیت موقت
                context.user_data['awaiting_search_name'] = False
                context.user_data['search_to_save'] = None
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📋 جستجوهای ذخیره شده", callback_data="show_saved_searches"),
                        InlineKeyboardButton("🔍 جستجوی جدید", callback_data="search_tokens")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                    ]
                ])
            else:
                text = "❌ **خطا در ذخیره جستجو**\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}\n\n"
                text += "لطفاً دوباره تلاش کنید."
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 تلاش مجدد", callback_data="save_search"),
                    InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                ]])
            
            if query:
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_confirm_save_search: {e}")
            await self.handle_error(update, context, e)
    
    async def show_saved_searches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش جستجوهای ذخیره شده"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = update.effective_user.id
            result = await self.token_manager.get_saved_searches(user_id)
            
            text = "💾 **جستجوهای ذخیره شده**\n\n"
            
            if result.get('success'):
                searches = result.get('searches', [])
                
                if searches:
                    text += f"📊 **تعداد:** {len(searches)} جستجو\n\n"
                    
                    buttons = []
                    for i, search in enumerate(searches[:10], 1):
                        text += f"{i}. 📝 **{search.get('name')}**\n"
                        text += f"   🆔 شناسه: {search.get('id')}\n"
                        text += f"   📅 ایجاد: {search.get('created_at', '')[:16]}\n"
                        text += f"   📊 استفاده: {search.get('usage_count', 0)} بار\n"
                        if search.get('last_used'):
                            text += f"   🕐 آخرین استفاده: {search.get('last_used')[:16]}\n"
                        text += "\n"
                        
                        buttons.append([
                            InlineKeyboardButton(f"🔄 اجرا #{i}", callback_data=f"load_saved_search_{search.get('id')}"),
                            InlineKeyboardButton(f"🗑 حذف #{i}", callback_data=f"delete_saved_search_{search.get('id')}")
                        ])
                    
                    if len(searches) > 10:
                        text += f"... و {len(searches) - 10} جستجوی دیگر\n\n"
                    
                    buttons.append([
                        InlineKeyboardButton("🔄 بروزرسانی", callback_data="show_saved_searches"),
                        InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                    ])
                    
                    keyboard = InlineKeyboardMarkup(buttons)
                else:
                    text += "❌ هیچ جستجوی ذخیره شده‌ای وجود ندارد!\n\n"
                    text += "از منوی جستجو می‌توانید جستجوهای خود را ذخیره کنید."
                    
                    keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔍 شروع جستجو", callback_data="search_tokens")
                    ]])
            else:
                text += "❌ خطا در دریافت جستجوهای ذخیره شده\n\n"
                text += f"علت: {result.get('error', 'نامشخص')}"
                
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                ]])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in show_saved_searches: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_load_saved_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بارگذاری و اجرای جستجوی ذخیره شده"""
        try:
            query = update.callback_query
            await query.answer("در حال اجرای جستجو...")
            
            # استخراج search_id
            search_id = int(query.data.split('_')[-1])
            
            user_id = update.effective_user.id
            result = await self.token_manager.get_saved_searches(user_id)
            
            if result.get('success'):
                searches = result.get('searches', [])
                search = next((s for s in searches if s.get('id') == search_id), None)
                
                if search:
                    # افزایش شمارنده استفاده
                    await self.token_manager.increment_saved_search_usage(user_id, search_id)
                    
                    # اجرای جستجو بر اساس پارامترهای ذخیره شده
                    params = search.get('params', {})
                    
                    # اجرای جستجو بر اساس نوع
                    if params.get('type'):
                        search_result = await self.token_manager.search_tokens_by_type(params['type'])
                        title = f"💾 {search.get('name')}"
                        search_type = "type"
                        search_value = params['type']
                    elif params.get('status'):
                        search_result = await self.token_manager.search_tokens_by_status(params['status'])
                        title = f"💾 {search.get('name')}"
                        search_type = "status"
                        search_value = params['status']
                    else:
                        search_result = await self.token_manager.get_all_tokens()
                        title = f"💾 {search.get('name')}"
                        search_type = "saved"
                        search_value = str(search_id)
                    
                    await self._display_search_results(
                        update, context, search_result,
                        title=title,
                        search_type=search_type,
                        search_value=search_value
                    )
                else:
                    await query.answer("❌ جستجو یافت نشد!", show_alert=True)
            else:
                await query.answer("❌ خطا در بارگذاری جستجو!", show_alert=True)
            
        except Exception as e:
            logger.error(f"Error in handle_load_saved_search: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_delete_saved_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حذف جستجوی ذخیره شده"""
        try:
            query = update.callback_query
            await query.answer()
            
            # استخراج search_id
            search_id = int(query.data.split('_')[-1])
            
            user_id = update.effective_user.id
            result = await self.token_manager.delete_saved_search(user_id, search_id)
            
            if result.get('success'):
                await query.answer("✅ جستجو حذف شد", show_alert=True)
                await self.show_saved_searches(update, context)
            else:
                await query.answer(f"❌ خطا: {result.get('error', 'نامشخص')}", show_alert=True)
            
        except Exception as e:
            logger.error(f"Error in handle_delete_saved_search: {e}")
            await self.handle_error(update, context, e)
    
    # === EXPORT SEARCH RESULTS ===
    
    async def handle_export_search_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """صادرات نتایج جستجو"""
        try:
            query = update.callback_query
            await query.answer()
            
            # استخراج اطلاعات جستجو از callback_data
            parts = query.data.split('_')
            if len(parts) >= 4:
                search_type = parts[3]
                search_value = parts[4] if len(parts) > 4 else ""
            else:
                await query.answer("❌ خطا در شناسایی جستجو!", show_alert=True)
                return
            
            text = "💾 **صادرات نتایج جستجو**\n\n"
            text += "لطفاً فرمت صادرات را انتخاب کنید:\n\n"
            text += "📄 **فرمت‌های پشتیبانی شده:**\n"
            text += "• **JSON:** مناسب برای پردازش خودکار\n"
            text += "• **CSV:** مناسب برای Excel و تحلیل\n"
            text += "• **TXT:** فرمت متنی ساده و خوانا\n"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📄 JSON", callback_data=f"export_format_json_{search_type}_{search_value}"),
                    InlineKeyboardButton("📊 CSV", callback_data=f"export_format_csv_{search_type}_{search_value}")
                ],
                [
                    InlineKeyboardButton("📝 TXT", callback_data=f"export_format_text_{search_type}_{search_value}"),
                    InlineKeyboardButton("❌ انصراف", callback_data="search_tokens")
                ]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_export_search_results: {e}")
            await self.handle_error(update, context, e)
    
    async def handle_export_format(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش صادرات با فرمت انتخاب شده"""
        try:
            query = update.callback_query
            await query.answer("در حال آماده‌سازی فایل...")
            
            # استخراج اطلاعات از callback_data
            parts = query.data.split('_')
            if len(parts) >= 4:
                format_type = parts[2]
                search_type = parts[3]
                search_value = parts[4] if len(parts) > 4 else ""
            else:
                await query.answer("❌ خطا در پردازش!", show_alert=True)
                return
            
            # دریافت نتایج جستجو دوباره
            if search_type == 'type':
                result = await self.token_manager.search_tokens_by_type(search_value)
            elif search_type == 'status':
                result = await self.token_manager.search_tokens_by_status(search_value)
            elif search_type == 'usage':
                parts_usage = search_value.split('_')
                min_usage = int(parts_usage[0]) if parts_usage else 0
                max_usage = int(parts_usage[1]) if len(parts_usage) > 1 and parts_usage[1] != 'unlimited' else None
                result = await self.token_manager.search_tokens_by_usage(min_usage, max_usage)
            else:
                result = await self.token_manager.get_all_tokens()
            
            if result.get('success'):
                tokens = result.get('tokens', [])
                
                # صادرات داده‌ها
                export_result = await self.token_manager.export_search_results_data(tokens, format_type)
                
                if export_result.get('success'):
                    data = export_result.get('data')
                    filename = export_result.get('filename')
                    
                    # ارسال فایل به کاربر
                    from io import BytesIO
                    file_bytes = BytesIO(data.encode('utf-8'))
                    file_bytes.name = filename
                    
                    await query.message.reply_document(
                        document=file_bytes,
                        filename=filename,
                        caption=f"✅ **صادرات با موفقیت انجام شد**\n\n📊 تعداد: {len(tokens)} توکن\n📄 فرمت: {format_type.upper()}\n📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    )
                    
                    await query.edit_message_text(
                        f"✅ فایل آماده شد و ارسال گردید!\n\n📄 {filename}",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 بازگشت", callback_data="search_tokens")
                        ]])
                    )
                else:
                    await query.answer(f"❌ خطا: {export_result.get('error')}", show_alert=True)
            else:
                await query.answer("❌ خطا در دریافت نتایج!", show_alert=True)
            
        except Exception as e:
            logger.error(f"Error in handle_export_format: {e}")
            await query.answer("❌ خطا در صادرات!", show_alert=True)
    
    # === SEARCH RESULTS STATS ===
    
    async def handle_search_results_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش آمار تفصیلی نتایج جستجو"""
        try:
            query = update.callback_query
            await query.answer()
            
            # استخراج اطلاعات جستجو
            parts = query.data.split('_')
            if len(parts) >= 4:
                search_type = parts[3]
                search_value = parts[4] if len(parts) > 4 else ""
            else:
                await query.answer("❌ خطا در شناسایی جستجو!", show_alert=True)
                return
            
            # دریافت نتایج جستجو
            if search_type == 'type':
                result = await self.token_manager.search_tokens_by_type(search_value)
            elif search_type == 'status':
                result = await self.token_manager.search_tokens_by_status(search_value)
            else:
                result = await self.token_manager.get_all_tokens()
            
            if result.get('success'):
                tokens = result.get('tokens', [])
                total = len(tokens)
                
                text = "📊 **آمار تفصیلی نتایج جستجو**\n\n"
                text += f"🔍 **کل نتایج:** {total} توکن\n\n"
                
                if total > 0:
                    # آمار بر اساس نوع
                    type_counts = {}
                    for token in tokens:
                        t = token.get('type', 'unknown')
                        type_counts[t] = type_counts.get(t, 0) + 1
                    
                    text += "🏷 **توزیع بر اساس نوع:**\n"
                    for t, count in type_counts.items():
                        percentage = (count / total) * 100
                        text += f"• {self._get_token_type_name(t)}: {count} ({percentage:.1f}%)\n"
                    text += "\n"
                    
                    # آمار بر اساس وضعیت
                    active_count = sum(1 for t in tokens if t.get('is_active', True))
                    inactive_count = total - active_count
                    
                    text += "📊 **توزیع بر اساس وضعیت:**\n"
                    text += f"• فعال: {active_count} ({(active_count/total)*100:.1f}%)\n"
                    text += f"• غیرفعال: {inactive_count} ({(inactive_count/total)*100:.1f}%)\n\n"
                    
                    # آمار استفاده
                    total_usage = sum(t.get('usage_count', 0) for t in tokens)
                    avg_usage = total_usage / total if total > 0 else 0
                    max_usage = max((t.get('usage_count', 0) for t in tokens), default=0)
                    min_usage = min((t.get('usage_count', 0) for t in tokens), default=0)
                    
                    text += "📈 **آمار استفاده:**\n"
                    text += f"• کل استفاده‌ها: {total_usage:,}\n"
                    text += f"• میانگین: {avg_usage:.1f}\n"
                    text += f"• حداکثر: {max_usage:,}\n"
                    text += f"• حداقل: {min_usage:,}\n\n"
                    
                    # آمار تاریخی
                    today = datetime.now().date()
                    created_today = sum(1 for t in tokens if t.get('created_at', '')[:10] == str(today))
                    
                    text += "📅 **آمار تاریخی:**\n"
                    text += f"• ایجاد شده امروز: {created_today}\n"
                    
                    # پربازدیدترین
                    top_token = max(tokens, key=lambda t: t.get('usage_count', 0), default=None)
                    if top_token:
                        text += "\n🔥 **پربازدیدترین:**\n"
                        text += f"• نام: {top_token.get('name', 'N/A')}\n"
                        text += f"• استفاده: {top_token.get('usage_count', 0):,} بار\n"
                else:
                    text += "❌ نتیجه‌ای یافت نشد!"
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📊 نمودار", callback_data=f"stats_chart_{search_type}_{search_value}"),
                        InlineKeyboardButton("💾 صادرات آمار", callback_data=f"export_stats_{search_type}_{search_value}")
                    ],
                    [
                        InlineKeyboardButton("🔙 بازگشت به نتایج", callback_data=f"search_results_{search_type}_{search_value}_1")
                    ]
                ])
                
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                await query.answer("❌ خطا در دریافت نتایج!", show_alert=True)
            
        except Exception as e:
            logger.error(f"Error in handle_search_results_stats: {e}")
            await self.handle_error(update, context, e)
