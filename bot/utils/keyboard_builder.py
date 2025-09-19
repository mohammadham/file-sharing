#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Keyboard Builder - Creates inline keyboards for the bot
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional
from models.database_models import Category, File


class KeyboardBuilder:
    """Build inline keyboards for various bot functions"""
    
    @staticmethod
    async def build_category_keyboard(
        categories: List[Category],
        current_category: Optional[Category] = None,
        show_management: bool = True
    ) -> InlineKeyboardMarkup:
        """Build keyboard for category navigation"""
        keyboard = []
        
        # Categories buttons (2 per row)
        for i in range(0, len(categories), 2):
            row = []
            for j in range(2):
                if i + j < len(categories):
                    cat = categories[i + j]
                    row.append(InlineKeyboardButton(
                        f"{cat.name}", 
                        callback_data=f"cat_{cat.id}"
                    ))
            keyboard.append(row)
        
        if show_management:
            # Management buttons
            management_row = []
            
            # Back button
            if current_category and current_category.parent_id:
                management_row.append(InlineKeyboardButton(
                    "🔙 بازگشت", 
                    callback_data=f"cat_{current_category.parent_id}"
                ))
            elif current_category and current_category.id != 1:
                management_row.append(InlineKeyboardButton(
                    "🔙 منوی اصلی", 
                    callback_data="cat_1"
                ))
            
            # Add category button
            category_id = current_category.id if current_category else 1
            management_row.append(InlineKeyboardButton(
                "➕ افزودن دسته", 
                callback_data=f"add_cat_{category_id}"
            ))
            
            if management_row:
                keyboard.append(management_row)
            
            # Category management buttons
            if current_category and current_category.id != 1:
                category_mgmt_row = [
                    InlineKeyboardButton("✏️ ویرایش دسته", callback_data=f"edit_cat_{current_category.id}"),
                    InlineKeyboardButton("🗑 حذف دسته", callback_data=f"del_cat_{current_category.id}")
                ]
                keyboard.append(category_mgmt_row)
            
            # Files and actions row
            files_row = [
                InlineKeyboardButton("📁 مشاهده فایل‌ها", callback_data=f"files_{category_id}"),
                InlineKeyboardButton("📤 آپلود فایل", callback_data=f"upload_{category_id}")
            ]
            keyboard.append(files_row)
            
            # Batch upload row
            batch_row = [
                InlineKeyboardButton("📤🗂 آپلود چند فایل", callback_data=f"batch_upload_{category_id}")
            ]
            keyboard.append(batch_row)
            
            # Main actions
            actions_row = [
                InlineKeyboardButton("📢 برودکست", callback_data="broadcast_menu"),
                InlineKeyboardButton("🔍 جستجو", callback_data="search")
            ]
            keyboard.append(actions_row)
            
            # Stats button
            stats_row = [InlineKeyboardButton("📊 آمار", callback_data="stats")]
            keyboard.append(stats_row)
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_files_keyboard(
        files: List[File],
        category_id: int,
        page: int = 0,
        total_pages: int = 1
    ) -> InlineKeyboardMarkup:
        """Build keyboard for file management"""
        keyboard = []
        
        # File buttons (1 per row)  
        for file in files:
            from utils.helpers import format_file_size
            file_size_formatted = format_file_size(file.file_size)
            # Truncate long file names for button display
            display_name = file.file_name[:30] + "..." if len(file.file_name) > 30 else file.file_name
            file_row = [InlineKeyboardButton(
                f"📄 {display_name} ({file_size_formatted})",
                callback_data=f"file_{file.id}"
            )]
            keyboard.append(file_row)
        
        # Pagination
        if total_pages > 1:
            pagination_row = []
            if page > 0:
                pagination_row.append(InlineKeyboardButton(
                    "⬅️ قبلی", 
                    callback_data=f"files_{category_id}_{page-1}"
                ))
            
            pagination_row.append(InlineKeyboardButton(
                f"{page + 1}/{total_pages}", 
                callback_data="page_info"
            ))
            
            if page < total_pages - 1:
                pagination_row.append(InlineKeyboardButton(
                    "➡️ بعدی", 
                    callback_data=f"files_{category_id}_{page+1}"
                ))
            
            keyboard.append(pagination_row)
        
        # Back button
        keyboard.append([InlineKeyboardButton(
            "🔙 بازگشت", 
            callback_data=f"cat_{category_id}"
        )])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_file_actions_keyboard(file: File) -> InlineKeyboardMarkup:
        """Build keyboard for individual file actions"""
        keyboard = [
            [
                InlineKeyboardButton("📥 دانلود", callback_data=f"download_{file.id}"),
                InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_file_{file.id}")
            ],
            [
                InlineKeyboardButton("🗑 حذف", callback_data=f"delete_file_{file.id}"),
                InlineKeyboardButton("📋 کپی لینک", callback_data=f"copy_link_{file.id}")
            ],
            [
                InlineKeyboardButton("🔄 انتقال", callback_data=f"move_file_{file.id}"),
                InlineKeyboardButton("📊 جزئیات", callback_data=f"details_{file.id}")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"files_{file.category_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_broadcast_keyboard() -> InlineKeyboardMarkup:
        """Build keyboard for broadcast menu"""
        keyboard = [
            [InlineKeyboardButton("📝 برودکست متنی", callback_data="broadcast_text")],
            [InlineKeyboardButton("📁 برودکست فایل", callback_data="broadcast_file")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="cat_1")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_confirmation_keyboard(action: str, item_id: int) -> InlineKeyboardMarkup:
        """Build confirmation keyboard for dangerous actions"""
        keyboard = [
            [
                InlineKeyboardButton("✅ تأیید", callback_data=f"confirm_{action}_{item_id}"),
                InlineKeyboardButton("❌ لغو", callback_data=f"cancel_{action}_{item_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_cancel_keyboard(return_to: str = "cat_1") -> InlineKeyboardMarkup:
        """Build simple cancel keyboard"""
        keyboard = [[InlineKeyboardButton("❌ لغو", callback_data=return_to)]]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_batch_upload_keyboard(category_id: int, files_count: int = 0) -> InlineKeyboardMarkup:
        """Build keyboard for batch upload process"""
        keyboard = [
            [InlineKeyboardButton(f"📊 فایل‌های دریافت شده: {files_count}", callback_data="files_count_info")],
            [
                InlineKeyboardButton("✅ اتمام ارسال", callback_data=f"finish_batch_{category_id}"),
                InlineKeyboardButton("❌ لغو", callback_data=f"cancel_batch_{category_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_move_file_keyboard(
        categories: List[Category], 
        file_id: int, 
        current_category_id: int,
        current_category: Optional[Category] = None
    ) -> InlineKeyboardMarkup:
        """Build keyboard for file move operation"""
        keyboard = []
        
        # Show categories (navigate into them)
        for i in range(0, len(categories), 2):
            row = []
            for j in range(2):
                if i + j < len(categories):
                    cat = categories[i + j]
                    row.append(InlineKeyboardButton(
                        f"📁 {cat.name}", 
                        callback_data=f"move_nav_cat_{file_id}_{cat.id}"
                    ))
            keyboard.append(row)
        
        # Option to select current category (if not root)
        if current_category and current_category.id != 1:
            keyboard.append([
                InlineKeyboardButton(
                    f"✅ انتخاب '{current_category.name}'", 
                    callback_data=f"move_to_cat_{file_id}_{current_category.id}"
                )
            ])
        
        # Navigation buttons
        nav_row = []
        
        # Back button (if not at root)
        if current_category and current_category.parent_id:
            nav_row.append(InlineKeyboardButton(
                "🔙 بازگشت", 
                callback_data=f"move_nav_cat_{file_id}_{current_category.parent_id}"
            ))
        elif current_category and current_category.id != 1:
            nav_row.append(InlineKeyboardButton(
                "🔙 منوی اصلی", 
                callback_data=f"move_nav_cat_{file_id}_1"
            ))
        
        # Cancel button
        nav_row.append(InlineKeyboardButton(
            "❌ لغو انتقال", 
            callback_data=f"cancel_move_{file_id}"
        ))
        
        if nav_row:
            keyboard.append(nav_row)
        
        return InlineKeyboardMarkup(keyboard)