#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Category Handler - Handles category-related operations
"""

import json
import logging
from telegram import Update
from telegram.ext import ContextTypes

from handlers.base_handler import BaseHandler
from utils.keyboard_builder import KeyboardBuilder
from utils.helpers import safe_json_loads, safe_json_dumps

logger = logging.getLogger(__name__)


class CategoryHandler(BaseHandler):
    """Handle category operations"""
    
    async def show_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show category and its subcategories"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            category_id = int(query.data.split('_')[1])
            user_id = update.effective_user.id
            
            # Reset user state to browsing when navigating categories
            await self.update_user_session(
                user_id, 
                current_category=category_id,
                action_state='browsing'
            )
            
            category = await self.db.get_category_by_id(category_id)
            if not category:
                await query.edit_message_text("دسته‌بندی یافت نشد!")
                return
            
            subcategories = await self.db.get_categories(category_id)
            
            text = f"📁 **{category.name}**\n\n"
            if category.description:
                text += f"📝 {category.description}\n\n"
            
            if subcategories:
                text += f"📂 تعداد زیردسته‌ها: {len(subcategories)}"
            else:
                text += "📄 هیچ زیردسته‌ای وجود ندارد"
            
            keyboard = await KeyboardBuilder.build_category_keyboard(
                subcategories, category, True
            )
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def add_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding new category"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            parent_id = int(query.data.split('_')[2])
            user_id = update.effective_user.id
            
            await self.update_user_session(
                user_id,
                action_state='adding_category',
                temp_data=safe_json_dumps({'parent_id': parent_id})
            )
            
            keyboard = KeyboardBuilder.build_cancel_keyboard(f"cat_{parent_id}")
            
            await query.edit_message_text(
                "✏️ **افزودن دسته جدید**\n\nنام دسته جدید را وارد کنید:",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def edit_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start editing category"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            category_id = int(query.data.split('_')[2])
            user_id = update.effective_user.id
            
            category = await self.db.get_category_by_id(category_id)
            if not category:
                await query.edit_message_text("دسته‌بندی یافت نشد!")
                return
            
            await self.update_user_session(
                user_id,
                action_state='editing_category',
                temp_data=safe_json_dumps({'category_id': category_id})
            )
            
            keyboard = KeyboardBuilder.build_cancel_keyboard(f"cat_{category_id}")
            
            text = f"✏️ **ویرایش دسته '{category.name}'**\n\n"
            text += "نام جدید دسته را وارد کنید:"
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def delete_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show delete confirmation"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            category_id = int(query.data.split('_')[2])
            
            category = await self.db.get_category_by_id(category_id)
            if not category:
                await query.edit_message_text("دسته‌بندی یافت نشد!")
                return
            
            # Check if category has subcategories or files
            subcategories = await self.db.get_categories(category_id)
            files = await self.db.get_files(category_id, limit=1)
            
            warning_text = ""
            if subcategories:
                warning_text += f"⚠️ این دسته دارای {len(subcategories)} زیردسته است.\n"
            if files:
                file_count = len(await self.db.get_files(category_id, limit=1000))
                warning_text += f"⚠️ این دسته دارای {file_count} فایل است.\n"
            
            if warning_text:
                warning_text += "\nدر صورت حذف، زیردسته‌ها و فایل‌ها به دسته والد منتقل می‌شوند.\n\n"
            
            text = f"🗑 **حذف دسته '{category.name}'**\n\n"
            text += warning_text
            text += "آیا مطمئن هستید؟"
            
            keyboard = KeyboardBuilder.build_confirmation_keyboard("delete_cat", category_id)
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def confirm_delete_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm category deletion"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            category_id = int(query.data.split('_')[3])
            
            category = await self.db.get_category_by_id(category_id)
            if not category:
                await query.edit_message_text("دسته‌بندی یافت نشد!")
                return
            
            parent_id = category.parent_id or 1
            success = await self.db.delete_category(category_id)
            
            if success:
                # Show parent category
                parent_category = await self.db.get_category_by_id(parent_id)
                subcategories = await self.db.get_categories(parent_id)
                
                keyboard = await KeyboardBuilder.build_category_keyboard(
                    subcategories, parent_category, True
                )
                
                await query.edit_message_text(
                    f"✅ دسته '{category.name}' با موفقیت حذف شد!",
                    reply_markup=keyboard
                )
            else:
                await query.edit_message_text("❌ خطا در حذف دسته!")
                
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def process_category_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process category name input"""
        try:
            user_id = update.effective_user.id
            session = await self.get_user_session(user_id)
            temp_data = safe_json_loads(session.temp_data)
            
            category_name = update.message.text.strip()
            
            if not category_name or len(category_name) < 1:
                await update.message.reply_text(self.messages['invalid_input'])
                return
            
            if session.action_state == 'adding_category':
                parent_id = temp_data.get('parent_id', 1)
                
                new_cat_id = await self.db.create_category(category_name, parent_id)
                
                await self.reset_user_state(user_id)
                await self.update_user_session(user_id, current_category=parent_id)
                
                # Show updated parent category
                parent_category = await self.db.get_category_by_id(parent_id)
                subcategories = await self.db.get_categories(parent_id)
                
                keyboard = await KeyboardBuilder.build_category_keyboard(
                    subcategories, parent_category, True
                )
                
                await update.message.reply_text(
                    f"✅ دسته '{category_name}' با موفقیت اضافه شد!",
                    reply_markup=keyboard
                )
                
            elif session.action_state == 'editing_category':
                category_id = temp_data.get('category_id')
                
                success = await self.db.update_category(category_id, name=category_name)
                
                await self.reset_user_state(user_id)
                
                if success:
                    # Show updated category
                    category = await self.db.get_category_by_id(category_id)
                    subcategories = await self.db.get_categories(category_id)
                    
                    keyboard = await KeyboardBuilder.build_category_keyboard(
                        subcategories, category, True
                    )
                    
                    await update.message.reply_text(
                        f"✅ نام دسته به '{category_name}' تغییر یافت!",
                        reply_markup=keyboard
                    )
                else:
                    await update.message.reply_text("❌ خطا در ویرایش دسته!")
                    
        except Exception as e:
            logger.error(f"Error processing category name: {e}")
            await update.message.reply_text(self.messages['error_occurred'])