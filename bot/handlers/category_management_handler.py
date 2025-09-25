#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Category Management Handler - Advanced category operations
"""

import json
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from handlers.base_handler import BaseHandler
from utils.keyboard_builder import KeyboardBuilder
from utils.helpers import safe_json_loads, safe_json_dumps

logger = logging.getLogger(__name__)


class CategoryManagementHandler(BaseHandler):
    """Handle advanced category management operations"""
    
    def __init__(self, db):
        super().__init__(db)
    async def move_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle category move operation"""
        try:
            query = update.callback_query
            await query.answer()
            
            category_id = int(query.data.split('_')[2])
            user_id = update.effective_user.id
            
            category = await self.db.get_category_by_id(category_id)
            if not category:
                await query.edit_message_text("دسته‌بندی یافت نشد!")
                return
            
            # Root category cannot be moved
            if category_id == 1:
                text = "❌ **خطا در انتقال دسته**\n\n"
                text += "دسته اصلی قابل انتقال نیست."
                
                keyboard = KeyboardBuilder.build_cancel_keyboard(f"edit_category_menu_{category_id}")
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
                return
            
            # Set user state for moving category
            await self.update_user_session(
                user_id,
                action_state='moving_category',
                temp_data=safe_json_dumps({'category_id': category_id, 'current_move_category': 1})
            )
            
            # Show category selection starting from root
            await self._show_move_category_destinations(update, context, category_id, 1)
            
        except Exception as e:
            logger.error(f"Error in move category: {e}")
            await query.answer("❌ خطا در انتقال دسته!")
    
    async def _show_move_category_destinations(self, update: Update, context: ContextTypes.DEFAULT_TYPE, category_id: int, current_parent_id: int):
        """Show available destination categories for moving"""
        try:
            category = await self.db.get_category_by_id(category_id)
            current_parent = await self.db.get_category_by_id(current_parent_id)
            
            # Get available categories (excluding self and its children)
            all_categories = await self.db.get_categories(current_parent_id)
            available_categories = []
            
            for cat in all_categories:
                # Exclude the category being moved and its children
                if cat.id != category_id and not await self._is_child_category(cat.id, category_id):
                    available_categories.append(cat)
            
            text = f"📁 **انتقال دسته '{category.name}'**\n\n"
            text += f"📂 دسته فعلی: {current_parent.name if current_parent else 'منوی اصلی'}\n\n"
            
            if available_categories:
                text += "📋 دسته‌های موجود برای انتقال:"
            else:
                text += "📄 هیچ دسته مقصدی در این بخش موجود نیست.\n"
                text += "برای انتقال به این دسته، 'انتخاب این دسته' را بزنید."
            
            keyboard = await self._build_move_category_keyboard(available_categories, category_id, current_parent_id, current_parent)
            
            await update.callback_query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error showing move category destinations: {e}")
    # async def move_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Handle category move operation"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         category_id = int(query.data.split('_')[2])
    #         user_id = update.effective_user.id
            
    #         category = await self.db.get_category_by_id(category_id)
    #         if not category:
    #             await query.edit_message_text("دسته‌بندی یافت نشد!")
    #             return
            
    #         # Root category cannot be moved
    #         if category_id == 1:
    #             text = "❌ **خطا در انتقال دسته**\n\n"
    #             text += "دسته اصلی قابل انتقال نیست."
                
    #             keyboard = KeyboardBuilder.build_cancel_keyboard(f"edit_category_menu_{category_id}")
    #             await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
    #             return
            
    #         # Set user state for moving category
    #         await self.update_user_session(
    #             user_id,
    #             action_state='moving_category',
    #             temp_data=safe_json_dumps({'category_id': category_id, 'current_move_category': 1})
    #         )
            
    #         # Show category selection starting from root
    #         await self._show_move_category_destinations(update, context, category_id, 1)
            
    #     except Exception as e:
    #         logger.error(f"Error in move category: {e}")
    #         await query.answer("❌ خطا در انتقال دسته!")
    
    # async def _show_move_category_destinations(self, update: Update, context: ContextTypes.DEFAULT_TYPE, category_id: int, current_parent_id: int):
    #     """Show available destination categories for moving"""
    #     try:
    #         category = await self.db.get_category_by_id(category_id)
    #         current_parent = await self.db.get_category_by_id(current_parent_id)
            
    #         # Get available categories (excluding self and its children)
    #         all_categories = await self.db.get_categories(current_parent_id)
    #         available_categories = []
            
    #         for cat in all_categories:
    #             # Exclude the category being moved and its children
    #             if cat.id != category_id and not await self._is_child_category(cat.id, category_id):
    #                 available_categories.append(cat)
            
    #         text = f"📁 **انتقال دسته '{category.name}'**\n\n"
    #         text += f"📂 دسته فعلی: {current_parent.name if current_parent else 'منوی اصلی'}\n\n"
            
    #         if available_categories:
    #             text += "📋 دسته‌های موجود برای انتقال:"
    #         else:
    #             text += "📄 هیچ دسته مقصدی در این بخش موجود نیست.\n"
    #             text += "برای انتقال به این دسته، 'انتخاب این دسته' را بزنید."
            
    #         keyboard = await self._build_move_category_keyboard(available_categories, category_id, current_parent_id, current_parent)
            
    #         await update.callback_query.edit_message_text(
    #             text,
    #             reply_markup=keyboard,
    #             parse_mode='Markdown'
    #         )
            
    #     except Exception as e:
    #         logger.error(f"Error showing move category destinations: {e}")
    async def _is_child_category(self, potential_child_id: int, parent_id: int) -> bool:
        """Check if a category is a child of another category"""
        try:
            current_category = await self.db.get_category_by_id(potential_child_id)
            
            while current_category and current_category.parent_id:
                if current_category.parent_id == parent_id:
                    return True
                current_category = await self.db.get_category_by_id(current_category.parent_id)
            
            return False
        except:
            return False
    async def _build_move_category_keyboard(self, categories, category_id: int, current_parent_id: int, current_parent):
        """Build keyboard for category move operation"""
        keyboard = []
        
        # Show categories (navigate into them)
        for i in range(0, len(categories), 2):
            row = []
            for j in range(2):
                if i + j < len(categories):
                    cat = categories[i + j]
                    row.append(InlineKeyboardButton(
                        f"📁 {cat.name}", 
                        callback_data=f"move_cat_nav_{category_id}_{cat.id}"
                    ))
            keyboard.append(row)
        
        # Option to select current category (if not root)
        if current_parent and current_parent.id != 1:
            keyboard.append([
                InlineKeyboardButton(
                    f"✅ انتخاب '{current_parent.name}'", 
                    callback_data=f"move_cat_to_{category_id}_{current_parent.id}"
                )
            ])
        elif current_parent_id == 1:
            keyboard.append([
                InlineKeyboardButton(
                    "✅ انتقال به منوی اصلی", 
                    callback_data=f"move_cat_to_{category_id}_1"
                )
            ])
        
        # Navigation buttons
        nav_row = []
        
        # Back button (if not at root)
        if current_parent and current_parent.parent_id:
            nav_row.append(InlineKeyboardButton(
                "🔙 بازگشت", 
                callback_data=f"move_cat_nav_{category_id}_{current_parent.parent_id}"
            ))
        elif current_parent and current_parent.id != 1:
            nav_row.append(InlineKeyboardButton(
                "🔙 منوی اصلی", 
                callback_data=f"move_cat_nav_{category_id}_1"
            ))
        
        # Cancel button
        nav_row.append(InlineKeyboardButton(
            "❌ لغو انتقال", 
            callback_data=f"cancel_move_cat_{category_id}"
        ))
        
        if nav_row:
            keyboard.append(nav_row)
        
        return InlineKeyboardMarkup(keyboard)
    
    # async def _build_move_category_keyboard(self, categories, category_id: int, current_parent_id: int, current_parent):
    #     """Build keyboard for category move operation"""
    #     keyboard = []
        
    #     # Show categories (navigate into them)
    #     for i in range(0, len(categories), 2):
    #         row = []
    #         for j in range(2):
    #             if i + j < len(categories):
    #                 cat = categories[i + j]
    #                 row.append(InlineKeyboardButton(
    #                     f"📁 {cat.name}", 
    #                     callback_data=f"move_cat_nav_{category_id}_{cat.id}"
    #                 ))
    #         keyboard.append(row)
        
    #     # Option to select current category (if not root)
    #     if current_parent and current_parent.id != 1:
    #         keyboard.append([
    #             InlineKeyboardButton(
    #                 f"✅ انتخاب '{current_parent.name}'", 
    #                 callback_data=f"move_cat_to_{category_id}_{current_parent.id}"
    #             )
    #         ])
    #     elif current_parent_id == 1:
    #         keyboard.append([
    #             InlineKeyboardButton(
    #                 "✅ انتقال به منوی اصلی", 
    #                 callback_data=f"move_cat_to_{category_id}_1"
    #             )
    #         ])
        
    #     # Navigation buttons
    #     nav_row = []
        
    #     # Back button (if not at root)
    #     if current_parent and current_parent.parent_id:
    #         nav_row.append(InlineKeyboardButton(
    #             "🔙 بازگشت", 
    #             callback_data=f"move_cat_nav_{category_id}_{current_parent.parent_id}"
    #         ))
    #     elif current_parent and current_parent.id != 1:
    #         nav_row.append(InlineKeyboardButton(
    #             "🔙 منوی اصلی", 
    #             callback_data=f"move_cat_nav_{category_id}_1"
    #         ))
        
    #     # Cancel button
    #     nav_row.append(InlineKeyboardButton(
    #         "❌ لغو انتقال", 
    #         callback_data=f"cancel_move_cat_{category_id}"
    #     ))
        
    #     if nav_row:
    #         keyboard.append(nav_row)
        
    #     return InlineKeyboardMarkup(keyboard)
    async def move_category_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle navigation during category move"""
        try:
            query = update.callback_query
            await query.answer()
            
            parts = query.data.split('_')
            category_id = int(parts[3])
            new_parent_id = int(parts[4])
            
            # Update user session with new current category
            user_id = update.effective_user.id
            await self.update_user_session(
                user_id,
                temp_data=safe_json_dumps({'category_id': category_id, 'current_move_category': new_parent_id})
            )
            
            # Show new destinations
            await self._show_move_category_destinations(update, context, category_id, new_parent_id)
            
        except Exception as e:
            logger.error(f"Error in move category navigation: {e}")
            await query.answer("❌ خطا در ناوبری!")
    
    async def move_category_to(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Execute the category move operation"""
        try:
            query = update.callback_query
            await query.answer("در حال انتقال دسته...")
            
            parts = query.data.split('_')
            category_id = int(parts[3])
            new_parent_id = int(parts[4])
            user_id = update.effective_user.id
            
            # Get category info
            category = await self.db.get_category_by_id(category_id)
            new_parent = await self.db.get_category_by_id(new_parent_id) if new_parent_id != 1 else None
            
            # Perform the move
            success = await self.db.update_category(category_id, parent_id=new_parent_id)
            
            # Reset user state
            await self.update_user_session(user_id, action_state='browsing', temp_data=None)
            
            if success:
                text = f"✅ **انتقال موفقیت‌آمیز**\n\n"
                text += f"📁 دسته: {category.name}\n"
                text += f"📂 مقصد جدید: {new_parent.name if new_parent else 'منوی اصلی'}\n\n"
                text += "دسته با موفقیت منتقل شد!"
                
                keyboard = KeyboardBuilder.build_category_edit_menu_keyboard(category_id)
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                await query.edit_message_text("❌ خطا در انتقال دسته!")
                
        except Exception as e:
            logger.error(f"Error moving category: {e}")
            await query.answer("❌ خطا در انتقال دسته!")
    # async def move_category_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Handle navigation during category move"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         parts = query.data.split('_')
    #         category_id = int(parts[3])
    #         new_parent_id = int(parts[4])
            
    #         # Update user session with new current category
    #         user_id = update.effective_user.id
    #         await self.update_user_session(
    #             user_id,
    #             temp_data=safe_json_dumps({'category_id': category_id, 'current_move_category': new_parent_id})
    #         )
            
    #         # Show new destinations
    #         await self._show_move_category_destinations(update, context, category_id, new_parent_id)
            
    #     except Exception as e:
    #         logger.error(f"Error in move category navigation: {e}")
    #         await query.answer("❌ خطا در ناوبری!")
    
    # async def move_category_to(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Execute the category move operation"""
    #     try:
    #         query = update.callback_query
    #         await query.answer("در حال انتقال دسته...")
            
    #         parts = query.data.split('_')
    #         category_id = int(parts[3])
    #         new_parent_id = int(parts[4])
    #         user_id = update.effective_user.id
            
    #         # Get category info
    #         category = await self.db.get_category_by_id(category_id)
    #         new_parent = await self.db.get_category_by_id(new_parent_id) if new_parent_id != 1 else None
            
    #         # Perform the move
    #         success = await self.db.update_category(category_id, parent_id=new_parent_id)
            
    #         # Reset user state
    #         await self.update_user_session(user_id, action_state='browsing', temp_data=None)
            
    #         if success:
    #             text = f"✅ **انتقال موفقیت‌آمیز**\n\n"
    #             text += f"📁 دسته: {category.name}\n"
    #             text += f"📂 مقصد جدید: {new_parent.name if new_parent else 'منوی اصلی'}\n\n"
    #             text += "دسته با موفقیت منتقل شد!"
                
    #             keyboard = KeyboardBuilder.build_category_edit_menu_keyboard(category_id)
    #             await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
    #         else:
    #             text = f"❌ **خطا در انتقال دسته**\n\n"
    #             text += "متأسفانه امکان انتقال دسته وجود ندارد.\n"
    #             text += "لطفاً دوباره تلاش کنید."
                
    #             keyboard = KeyboardBuilder.build_category_edit_menu_keyboard(category_id)
    #             await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
                
    #     except Exception as e:
    #         logger.error(f"Error in move category to: {e}")
    #         await query.answer("❌ خطا در انتقال دسته!")
    # async def cancel_move_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Cancel category move operation"""
    #     try:
    #         query = update.callback_query
    #         await query.answer()
            
    #         category_id = int(query.data.split('_')[3])
    #         user_id = update.effective_user.id
            
    #         # Reset user state
    #         await self.update_user_session(user_id, action_state='browsing', temp_data=None)
            
    #         text = "❌ انتقال دسته لغو شد."
    #         keyboard = KeyboardBuilder.build_category_edit_menu_keyboard(category_id)
            
    #         await query.edit_message_text(text, reply_markup=keyboard)
            
    #     except Exception as e:
    #         logger.error(f"Error canceling move category: {e}")
    async def cancel_move_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel category move operation"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = update.effective_user.id
            category_id = int(query.data.split('_')[3])
            
            # Reset user state
            await self.update_user_session(user_id, action_state='browsing', temp_data=None)
            
            # Return to category edit menu
            text = "❌ **انتقال دسته لغو شد**\n\n"
            text += "به منوی ویرایش دسته بازگشتید."
            
            keyboard = KeyboardBuilder.build_category_edit_menu_keyboard(category_id)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in cancel move category: {e}")
            await query.answer("❌ خطا در لغو انتقال!")
    
    async def icon_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle icon page navigation"""
        try:
            query = update.callback_query
            await query.answer()
            
            # Extract page number and category_id from callback data
            parts = query.data.split('_')
            if len(parts) < 3:
                await query.answer("❌ داده نامعتبر!")
                return
            
            page = int(parts[2])
            
            # Get category_id from user session
            user_id = update.effective_user.id
            session = await self.get_user_session(user_id)
            temp_data = safe_json_loads(session.temp_data)
            category_id = temp_data.get('category_id')
            
            if not category_id:
                await query.edit_message_text("❌ خطا در دریافت اطلاعات دسته!")
                return
            
            # Show icon selection for the requested page
            from handlers.category_edit_handler import CategoryEditHandler
            category_edit_handler = CategoryEditHandler(self.db)
            await category_edit_handler.show_icon_selection_page(update, context, category_id, page)
            
        except Exception as e:
            logger.error(f"Error in icon page: {e}")
            await self.handle_error(update, context, e)