#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Keyboard Builder - Creates inline keyboards for the bot
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional
from models.database_models import Category, File, Link


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
                        f"{cat.display_name}", 
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
                    InlineKeyboardButton("✏️ ویرایش دسته", callback_data=f"edit_category_menu_{current_category.id}"),
                    InlineKeyboardButton("🗑 حذف دسته", callback_data=f"del_cat_{current_category.id}")
                ]
                keyboard.append(category_mgmt_row)
            
            # Files and actions row
            files_row = [
                InlineKeyboardButton("📁 مشاهده فایل‌ها", callback_data=f"files_{category_id}"),
                InlineKeyboardButton("📤 آپلود فایل", callback_data=f"upload_{category_id}")
            ]
            keyboard.append(files_row)
            
            # Category link and batch upload row
            category_actions_row = [
                InlineKeyboardButton("🔗 لینک دسته", callback_data=f"category_link_{category_id}"),
                InlineKeyboardButton("📤🗂 آپلود چند فایل", callback_data=f"batch_upload_{category_id}")
            ]
            keyboard.append(category_actions_row)
            
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
                InlineKeyboardButton("🔄 انتقال", callback_data=f"move_file_{file.id}")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"files_{file.category_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_enhanced_file_link_keyboard(file: File, short_code: str) -> InlineKeyboardMarkup:
        """Build enhanced keyboard for file link with advanced options"""
        keyboard = [
            [
                InlineKeyboardButton("📥 دانلود", callback_data=f"download_{file.id}"),
                InlineKeyboardButton("📊 آمار لینک", callback_data=f"link_stats_{short_code}")
            ],
            [
                InlineKeyboardButton("🔗 کپی دوباره", callback_data=f"copy_link_{file.id}"),
                InlineKeyboardButton("✏️ ویرایش فایل", callback_data=f"edit_file_{file.id}")
            ],
            [
                InlineKeyboardButton("🔒 غیرفعال‌سازی لینک", callback_data=f"deactivate_link_{short_code}"),
                InlineKeyboardButton("📋 لینک‌های من", callback_data="my_links")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"files_{file.category_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_shared_file_keyboard(file: File, link: Link) -> InlineKeyboardMarkup:
        """Build keyboard for shared file view"""
        keyboard = [
            [
                InlineKeyboardButton("📥 دانلود فایل", callback_data=f"download_shared_{file.id}"),
                InlineKeyboardButton("📊 جزئیات", callback_data=f"details_shared_{file.id}")
            ],
            [
                InlineKeyboardButton("🔗 کپی لینک", callback_data=f"copy_shared_{link.short_code}"),
                InlineKeyboardButton("📈 آمار لینک", callback_data=f"stats_shared_{link.short_code}")
            ]
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
    
    @staticmethod
    def build_category_link_options_keyboard(category_id: int) -> InlineKeyboardMarkup:
        """Build keyboard for category link options"""
        keyboard = [
            [InlineKeyboardButton("📂 لینک تمام فایل‌های دسته", callback_data=f"create_category_link_{category_id}")],
            [InlineKeyboardButton("📋 انتخاب فایل‌های خاص", callback_data=f"select_files_{category_id}")],
            [InlineKeyboardButton("📊 آمار دسته", callback_data=f"category_stats_{category_id}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"cat_{category_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_files_selection_keyboard(files: List[File], category_id: int, selected_ids: List[int] = None) -> InlineKeyboardMarkup:
        """Build keyboard for selecting multiple files"""
        if selected_ids is None:
            selected_ids = []
            
        keyboard = []
        
        # File selection buttons
        for file in files:
            from utils.helpers import format_file_size, escape_filename_for_markdown
            file_size_formatted = format_file_size(file.file_size)
            # Truncate and escape filename for safe display
            display_name = file.file_name[:25] + "..." if len(file.file_name) > 25 else file.file_name
            safe_display_name = escape_filename_for_markdown(display_name)
            
            # Check if selected
            selected_mark = "✅" if file.id in selected_ids else "⬜"
            
            keyboard.append([InlineKeyboardButton(
                f"{selected_mark} {display_name} ({file_size_formatted})",  # Use original name for button text (no escaping needed here)
                callback_data=f"toggle_file_{file.id}_{category_id}"
            )])
        
        # Action buttons
        if selected_ids:
            action_row = [
                InlineKeyboardButton(f"🔗 ایجاد لینک ({len(selected_ids)} فایل)", callback_data=f"create_collection_link_{category_id}"),
                InlineKeyboardButton("🗑 پاک کردن انتخاب", callback_data=f"clear_selection_{category_id}")
            ]
            keyboard.append(action_row)
        
        # Navigation
        nav_row = [
            InlineKeyboardButton("✅ انتخاب همه", callback_data=f"select_all_{category_id}"),
            InlineKeyboardButton("🔙 بازگشت", callback_data=f"category_link_{category_id}")
        ]
        keyboard.append(nav_row)
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_shared_category_keyboard(category: Category, link: Link) -> InlineKeyboardMarkup:
        """Build keyboard for shared category view"""
        keyboard = [
            [
                InlineKeyboardButton("📁 مشاهده فایل‌ها", callback_data=f"browse_shared_category_{link.short_code}"),
                InlineKeyboardButton("📥 دانلود همه", callback_data=f"download_all_category_{link.short_code}")
            ],
            [
                InlineKeyboardButton("🔗 کپی لینک", callback_data=f"copy_shared_{link.short_code}"),
                InlineKeyboardButton("📈 آمار لینک", callback_data=f"stats_shared_{link.short_code}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_shared_collection_keyboard(link: Link) -> InlineKeyboardMarkup:
        """Build keyboard for shared collection view"""
        keyboard = [
            [
                InlineKeyboardButton("📂 مشاهده فایل‌ها", callback_data=f"browse_shared_collection_{link.short_code}"),
                InlineKeyboardButton("📥 دانلود همه", callback_data=f"download_all_collection_{link.short_code}")
            ],
            [
                InlineKeyboardButton("🔗 کپی لینک", callback_data=f"copy_shared_{link.short_code}"),
                InlineKeyboardButton("📈 آمار لینک", callback_data=f"stats_shared_{link.short_code}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_category_edit_menu_keyboard(category_id: int) -> InlineKeyboardMarkup:
        """Build advanced category edit menu keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("📝 ویرایش نام", callback_data=f"edit_cat_name_{category_id}"),
                InlineKeyboardButton("📄 ویرایش توضیحات", callback_data=f"edit_cat_desc_{category_id}")
            ],
            [
                InlineKeyboardButton("🖼 تنظیم تامپنیل", callback_data=f"set_cat_thumbnail_{category_id}"),
                InlineKeyboardButton("🎨 انتخاب آیکون", callback_data=f"set_cat_icon_{category_id}")
            ],
            [
                InlineKeyboardButton("🏷 تنظیم برچسب‌ها", callback_data=f"set_cat_tags_{category_id}"),
                InlineKeyboardButton("📊 مشاهده آمار", callback_data=f"category_stats_{category_id}")
            ],
            [
                InlineKeyboardButton("🔗 ایجاد لینک", callback_data=f"category_link_{category_id}"),
                InlineKeyboardButton("📤 انتقال دسته", callback_data=f"move_category_{category_id}")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"cat_{category_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_icon_selection_keyboard(category_id: int, current_page: int = 0) -> InlineKeyboardMarkup:
        """Build keyboard for selecting category icon"""
        icons = [
            ("📁", "folder"), ("🗂", "folder2"), ("📂", "folder3"), ("🗃", "folder4"),
            ("📊", "chart"), ("📈", "graph"), ("📉", "graph2"), ("💼", "briefcase"),
            ("🎵", "music"), ("🎶", "music2"), ("🎤", "mic"), ("🎧", "headphone"),
            ("🎬", "movie"), ("🎥", "camera"), ("📹", "video"), ("🖼", "image"),
            ("📄", "document"), ("📝", "note"), ("📋", "clipboard"), ("📓", "book"),
            ("💻", "computer"), ("⚙️", "settings"), ("🔧", "tools"), ("🛠", "tools2"),
            ("📱", "mobile"), ("📞", "phone"), ("💾", "disk"), ("🖥", "desktop"),
            ("🎮", "game"), ("🎯", "target"), ("🎨", "art"), ("✨", "sparkle")
        ]
        
        keyboard = []
        start_idx = current_page * 16
        page_icons = icons[start_idx:start_idx + 16]
        
        # Icon buttons (4 per row)
        for i in range(0, len(page_icons), 4):
            row = []
            for j in range(4):
                if i + j < len(page_icons):
                    icon, code = page_icons[i + j]
                    row.append(InlineKeyboardButton(
                        icon, 
                        callback_data=f"select_icon_{category_id}_{code}"
                    ))
            keyboard.append(row)
        
        # Pagination
        nav_row = []
        if current_page > 0:
            nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"icon_page_{category_id}_{current_page-1}"))
        
        if start_idx + 16 < len(icons):
            nav_row.append(InlineKeyboardButton("➡️", callback_data=f"icon_page_{category_id}_{current_page+1}"))
        
        if nav_row:
            keyboard.append(nav_row)
        
        # Back button
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"edit_category_menu_{category_id}")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_thumbnail_options_keyboard(category_id: int) -> InlineKeyboardMarkup:
        """Build keyboard for thumbnail options"""
        keyboard = [
            [InlineKeyboardButton("📸 ارسال تصویر جدید", callback_data=f"upload_thumbnail_{category_id}")],
            [InlineKeyboardButton("🗑 حذف تامپنیل", callback_data=f"remove_thumbnail_{category_id}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"edit_category_menu_{category_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)