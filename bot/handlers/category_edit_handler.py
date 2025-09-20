#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Advanced Category Edit Handler - Handles advanced category editing features
"""

import json
import logging
from telegram import Update
from telegram.ext import ContextTypes

from handlers.base_handler import BaseHandler
from utils.keyboard_builder import KeyboardBuilder
from utils.helpers import safe_json_loads, safe_json_dumps

logger = logging.getLogger(__name__)


class CategoryEditHandler(BaseHandler):
    """Handle advanced category edit operations"""
    
    async def show_edit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show advanced category edit menu"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            category_id = int(query.data.split('_')[3])
            
            category = await self.db.get_category_by_id(category_id)
            if not category:
                await query.edit_message_text("دسته‌بندی یافت نشد!")
                return
            
            # Build information text
            text = f"⚙️ **ویرایش دسته '{category.display_name}'**\n\n"
            text += f"📊 **اطلاعات فعلی:**\n"
            text += f"• 📝 نام: {category.name}\n"
            text += f"• 🎨 آیکون: {category.icon}\n"
            
            if category.description:
                desc_preview = category.description[:50] + "..." if len(category.description) > 50 else category.description
                text += f"• 📄 توضیحات: {desc_preview}\n"
            else:
                text += f"• 📄 توضیحات: تنظیم نشده\n"
            
            if category.thumbnail_file_id:
                text += f"• 🖼 تامپنیل: ✅ تنظیم شده\n"
            else:
                text += f"• 🖼 تامپنیل: ❌ تنظیم نشده\n"
            
            tags = category.tags_list
            if tags:
                text += f"• 🏷 برچسب‌ها: {', '.join(tags[:3])}"
                if len(tags) > 3:
                    text += f" و {len(tags) - 3} مورد دیگر"
                text += "\n"
            else:
                text += f"• 🏷 برچسب‌ها: تنظیم نشده\n"
            
            text += f"\n💡 گزینه مورد نظر را انتخاب کنید:"
            
            keyboard = KeyboardBuilder.build_category_edit_menu_keyboard(category_id)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def edit_category_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start editing category name"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            category_id = int(query.data.split('_')[3])
            user_id = update.effective_user.id
            
            category = await self.db.get_category_by_id(category_id)
            if not category:
                await query.edit_message_text("دسته‌بندی یافت نشد!")
                return
            
            await self.update_user_session(
                user_id,
                action_state='editing_category_name',
                temp_data=safe_json_dumps({'category_id': category_id})
            )
            
            text = f"✏️ **ویرایش نام دسته**\n\n"
            text += f"📁 **دسته فعلی:** {category.display_name}\n\n"
            text += f"💡 نام جدید دسته را وارد کنید:"
            
            keyboard = KeyboardBuilder.build_cancel_keyboard(f"edit_category_menu_{category_id}")
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def edit_category_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start editing category description"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            category_id = int(query.data.split('_')[3])
            user_id = update.effective_user.id
            
            category = await self.db.get_category_by_id(category_id)
            if not category:
                await query.edit_message_text("دسته‌بندی یافت نشد!")
                return
            
            await self.update_user_session(
                user_id,
                action_state='editing_category_description',
                temp_data=safe_json_dumps({'category_id': category_id})
            )
            
            text = f"📄 **ویرایش توضیحات دسته**\n\n"
            text += f"📁 **دسته:** {category.display_name}\n\n"
            
            if category.description:
                text += f"📝 **توضیحات فعلی:**\n{category.description}\n\n"
            
            text += f"💡 توضیحات جدید را وارد کنید (یا 'حذف' برای پاک کردن):"
            
            keyboard = KeyboardBuilder.build_cancel_keyboard(f"edit_category_menu_{category_id}")
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def show_icon_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show icon selection menu"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            category_id = int(query.data.split('_')[3])
            
            category = await self.db.get_category_by_id(category_id)
            if not category:
                await query.edit_message_text("دسته‌بندی یافت نشد!")
                return
            
            text = f"🎨 **انتخاب آیکون برای '{category.name}'**\n\n"
            text += f"🔄 آیکون فعلی: {category.icon}\n\n"
            text += f"💡 آیکون مورد نظر را انتخاب کنید:"
            
            keyboard = KeyboardBuilder.build_icon_selection_keyboard(category_id)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def select_icon(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle icon selection"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update, "در حال تنظیم آیکون...")
            
            parts = query.data.split('_')
            category_id = int(parts[2])
            icon_code = parts[3]
            
            # Map icon codes to emojis
            icon_map = {
                "folder": "📁", "folder2": "🗂", "folder3": "📂", "folder4": "🗃",
                "chart": "📊", "graph": "📈", "graph2": "📉", "briefcase": "💼",
                "music": "🎵", "music2": "🎶", "mic": "🎤", "headphone": "🎧",
                "movie": "🎬", "camera": "🎥", "video": "📹", "image": "🖼",
                "document": "📄", "note": "📝", "clipboard": "📋", "book": "📓",
                "computer": "💻", "settings": "⚙️", "tools": "🔧", "tools2": "🛠",
                "mobile": "📱", "phone": "📞", "disk": "💾", "desktop": "🖥",
                "game": "🎮", "target": "🎯", "art": "🎨", "sparkle": "✨"
            }
            
            new_icon = icon_map.get(icon_code, "📁")
            
            # Update category
            success = await self.db.update_category(category_id, icon=new_icon)
            
            if success:
                category = await self.db.get_category_by_id(category_id)
                text = f"✅ **آیکون با موفقیت تغییر یافت**\n\n"
                text += f"📁 **دسته:** {category.display_name}\n"
                text += f"🎨 **آیکون جدید:** {new_icon}\n\n"
                text += f"💡 آیکون در همه جا به‌روزرسانی شد!"
                
                keyboard = KeyboardBuilder.build_cancel_keyboard(f"edit_category_menu_{category_id}")
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                await query.edit_message_text("❌ خطا در تنظیم آیکون!")
                
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def show_thumbnail_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show thumbnail management options"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            category_id = int(query.data.split('_')[3])
            
            category = await self.db.get_category_by_id(category_id)
            if not category:
                await query.edit_message_text("دسته‌بندی یافت نشد!")
                return
            
            text = f"🖼 **مدیریت تامپنیل '{category.display_name}'**\n\n"
            
            if category.thumbnail_file_id:
                text += f"✅ **وضعیت:** تامپنیل تنظیم شده\n\n"
                text += f"💡 می‌توانید تامپنیل جدید آپلود کنید یا موجود را حذف کنید."
            else:
                text += f"❌ **وضعیت:** تامپنیل تنظیم نشده\n\n"
                text += f"💡 تصویری برای نمایش بهتر دسته آپلود کنید."
            
            keyboard = KeyboardBuilder.build_thumbnail_options_keyboard(category_id)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def start_thumbnail_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start thumbnail upload process"""
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
                action_state='uploading_thumbnail',
                temp_data=safe_json_dumps({'category_id': category_id})
            )
            
            text = f"📸 **آپلود تامپنیل برای '{category.display_name}'**\n\n"
            text += f"💡 **راهنما:**\n"
            text += f"• تصویری با کیفیت مناسب ارسال کنید\n"
            text += f"• حداکثر حجم: 10 مگابایت\n"
            text += f"• فرمت‌های پشتیبانی: JPG, PNG, WebP\n"
            text += f"• ابعاد پیشنهادی: مربعی (300x300 پیکسل)\n\n"
            text += f"🖼 تصویر مورد نظر را ارسال کنید:"
            
            keyboard = KeyboardBuilder.build_cancel_keyboard(f"set_cat_thumbnail_{category_id}")
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def remove_thumbnail(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove category thumbnail"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update, "در حال حذف تامپنیل...")
            
            category_id = int(query.data.split('_')[2])
            
            success = await self.db.update_category(category_id, thumbnail_file_id="")
            
            if success:
                category = await self.db.get_category_by_id(category_id)
                text = f"🗑 **تامپنیل حذف شد**\n\n"
                text += f"📁 **دسته:** {category.display_name}\n\n"
                text += f"✅ تامپنیل با موفقیت حذف شد."
                
                keyboard = KeyboardBuilder.build_cancel_keyboard(f"edit_category_menu_{category_id}")
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                await query.edit_message_text("❌ خطا در حذف تامپنیل!")
                
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def set_category_tags(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start setting category tags"""
        try:
            query = update.callback_query
            await self.answer_callback_query(update)
            
            category_id = int(query.data.split('_')[3])
            user_id = update.effective_user.id
            
            category = await self.db.get_category_by_id(category_id)
            if not category:
                await query.edit_message_text("دسته‌بندی یافت نشد!")
                return
            
            await self.update_user_session(
                user_id,
                action_state='setting_category_tags',
                temp_data=safe_json_dumps({'category_id': category_id})
            )
            
            text = f"🏷 **تنظیم برچسب‌های '{category.display_name}'**\n\n"
            
            current_tags = category.tags_list
            if current_tags:
                text += f"🔄 **برچسب‌های فعلی:** {', '.join(current_tags)}\n\n"
            
            text += f"💡 **راهنما:**\n"
            text += f"• برچسب‌ها را با کاما جدا کنید\n"
            text += f"• مثال: موزیک, صوتی, mp3, آهنگ\n"
            text += f"• برای پاک کردن همه برچسب‌ها 'پاک' بنویسید\n\n"
            text += f"🏷 برچسب‌های جدید را وارد کنید:"
            
            keyboard = KeyboardBuilder.build_cancel_keyboard(f"edit_category_menu_{category_id}")
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def process_category_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process category name edit"""
        try:
            user_id = update.effective_user.id
            session = await self.get_user_session(user_id)
            temp_data = safe_json_loads(session.temp_data)
            
            category_id = temp_data.get('category_id')
            new_name = update.message.text.strip()
            
            if not new_name or len(new_name) < 1:
                await update.message.reply_text(self.messages['invalid_input'])
                return
            
            success = await self.db.update_category(category_id, name=new_name)
            
            await self.reset_user_state(user_id)
            
            if success:
                category = await self.db.get_category_by_id(category_id)
                keyboard = KeyboardBuilder.build_category_edit_menu_keyboard(category_id)
                
                await update.message.reply_text(
                    f"✅ نام دسته به '{category.display_name}' تغییر یافت!",
                    reply_markup=keyboard
                )
            else:
                await update.message.reply_text("❌ خطا در ویرایش نام دسته!")
                
        except Exception as e:
            logger.error(f"Error processing category name: {e}")
            await update.message.reply_text(self.messages['error_occurred'])
    
    async def process_category_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process category description edit"""
        try:
            user_id = update.effective_user.id
            session = await self.get_user_session(user_id)
            temp_data = safe_json_loads(session.temp_data)
            
            category_id = temp_data.get('category_id')
            new_description = update.message.text.strip()
            
            # Handle delete command
            description_to_save = "" if new_description.lower() in ['حذف', 'delete', 'پاک'] else new_description
            
            success = await self.db.update_category(category_id, description=description_to_save)
            
            await self.reset_user_state(user_id)
            
            if success:
                category = await self.db.get_category_by_id(category_id)
                keyboard = KeyboardBuilder.build_category_edit_menu_keyboard(category_id)
                
                message = "✅ توضیحات دسته حذف شد!" if not description_to_save else "✅ توضیحات دسته با موفقیت به‌روزرسانی شد!"
                
                await update.message.reply_text(message, reply_markup=keyboard)
            else:
                await update.message.reply_text("❌ خطا در ویرایش توضیحات!")
                
        except Exception as e:
            logger.error(f"Error processing category description: {e}")
            await update.message.reply_text(self.messages['error_occurred'])
    
    async def process_thumbnail_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process thumbnail image upload"""
        try:
            user_id = update.effective_user.id
            session = await self.get_user_session(user_id)
            temp_data = safe_json_loads(session.temp_data)
            
            category_id = temp_data.get('category_id')
            
            if not update.message.photo:
                await update.message.reply_text("❌ لطفا یک تصویر ارسال کنید!")
                return
            
            # Get the largest photo
            photo = update.message.photo[-1]
            
            # Check file size (10MB limit)
            if photo.file_size > 10 * 1024 * 1024:
                await update.message.reply_text("❌ حجم تصویر بیش از 10 مگابایت است!")
                return
            
            success = await self.db.update_category(category_id, thumbnail_file_id=photo.file_id)
            
            await self.reset_user_state(user_id)
            
            if success:
                category = await self.db.get_category_by_id(category_id)
                keyboard = KeyboardBuilder.build_category_edit_menu_keyboard(category_id)
                
                await update.message.reply_text(
                    f"✅ تامپنیل دسته '{category.display_name}' با موفقیت تنظیم شد!",
                    reply_markup=keyboard
                )
            else:
                await update.message.reply_text("❌ خطا در تنظیم تامپنیل!")
                
        except Exception as e:
            logger.error(f"Error processing thumbnail upload: {e}")
            await update.message.reply_text(self.messages['error_occurred'])
    
    async def process_category_tags(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process category tags setting"""
        try:
            user_id = update.effective_user.id
            session = await self.get_user_session(user_id)
            temp_data = safe_json_loads(session.temp_data)
            
            category_id = temp_data.get('category_id')
            tags_text = update.message.text.strip()
            
            # Handle clear command
            if tags_text.lower() in ['پاک', 'حذف', 'clear', 'delete']:
                tags_json = ""
            else:
                # Parse tags
                tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
                tags_json = json.dumps(tags, ensure_ascii=False) if tags else ""
            
            success = await self.db.update_category(category_id, tags=tags_json)
            
            await self.reset_user_state(user_id)
            
            if success:
                category = await self.db.get_category_by_id(category_id)
                keyboard = KeyboardBuilder.build_category_edit_menu_keyboard(category_id)
                
                if tags_json:
                    tags_list = json.loads(tags_json)
                    message = f"✅ برچسب‌های دسته تنظیم شد: {', '.join(tags_list)}"
                else:
                    message = "✅ برچسب‌های دسته پاک شد!"
                
                await update.message.reply_text(message, reply_markup=keyboard)
            else:
                await update.message.reply_text("❌ خطا در تنظیم برچسب‌ها!")
                
        except Exception as e:
            logger.error(f"Error processing category tags: {e}")
            await update.message.reply_text(self.messages['error_occurred'])