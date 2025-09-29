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
    
    # === SEARCH RESULTS DISPLAY ===
    
    async def _display_search_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                     result: Dict[str, Any], title: str, search_type: str, 
                                     search_value: str, page: int = 1):
        """نمایش نتایج جستجو"""
        try:
            query = update.callback_query
            
            if not result.get('success'):
                text = f"❌ **خطا در جستجو**\n\n"
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
                text = f"❌ **خطا در جستجو**\n\n"
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