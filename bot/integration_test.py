#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration Test for Telegram Bot
Tests the actual bot workflow including the critical upload file button
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add bot directory to path
sys.path.append(str(Path(__file__).parent))

from telegram import Update, User, Chat, Message, CallbackQuery, Document
from telegram.ext import ContextTypes
from unittest.mock import AsyncMock, MagicMock
from bot_main import TelegramFileBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationTester:
    """Integration test for bot workflow"""
    
    def __init__(self):
        self.bot = TelegramFileBot()
        self.test_user_id = 99999
        self.test_chat_id = 88888
        
    def create_mock_update(self, text=None, callback_data=None, document=None):
        """Create mock update object"""
        user = User(
            id=self.test_user_id,
            is_bot=False,
            first_name="TestUser",
            username="testuser"
        )
        
        chat = Chat(
            id=self.test_chat_id,
            type="private"
        )
        
        update = MagicMock(spec=Update)
        update.effective_user = user
        update.effective_chat = chat
        
        if text:
            # Text message
            message = MagicMock(spec=Message)
            message.text = text
            message.message_id = 123
            message.reply_text = AsyncMock()
            message.document = None
            message.photo = None
            message.video = None
            message.audio = None
            update.message = message
            update.callback_query = None
        elif callback_data:
            # Callback query
            callback_query = MagicMock(spec=CallbackQuery)
            callback_query.data = callback_data
            callback_query.answer = AsyncMock()
            callback_query.edit_message_text = AsyncMock()
            callback_query.from_user = user
            update.callback_query = callback_query
            update.message = None
        elif document:
            # Document message
            message = MagicMock(spec=Message)
            message.document = document
            message.photo = None
            message.video = None
            message.audio = None
            message.message_id = 456
            message.reply_text = AsyncMock()
            update.message = message
            update.callback_query = None
        
        return update
    
    def create_mock_context(self):
        """Create mock context"""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.bot = MagicMock()
        context.bot.forward_message = AsyncMock()
        context.bot.send_message = AsyncMock()
        
        # Mock forwarded message response
        forwarded_message = MagicMock()
        forwarded_message.message_id = 999
        context.bot.forward_message.return_value = forwarded_message
        
        return context
    
    async def test_complete_workflow(self):
        """Test complete bot workflow"""
        print("🚀 Starting Complete Bot Workflow Test")
        print("=" * 50)
        
        # Initialize database
        await self.bot.db.init_database()
        
        # Step 1: Test /start command
        print("\n1️⃣ Testing /start command...")
        update = self.create_mock_update(text="/start")
        context = self.create_mock_context()
        
        await self.bot.start_command(update, context)
        
        # Verify welcome message was sent
        assert update.message.reply_text.called, "Welcome message should be sent"
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0] if call_args and call_args[0] else ""
        assert "سلام" in message_text, "Welcome message should contain greeting"
        assert "مدیریت فایل" in message_text, "Welcome message should mention file management"
        print("✅ /start command works correctly")
        
        # Step 2: Test category navigation
        print("\n2️⃣ Testing category navigation...")
        update = self.create_mock_update(callback_data="cat_1")
        context = self.create_mock_context()
        
        await self.bot.handle_callback_query(update, context)
        
        assert update.callback_query.answer.called, "Category callback should be answered"
        assert update.callback_query.edit_message_text.called, "Category view should be shown"
        print("✅ Category navigation works correctly")
        
        # Step 3: Test CRITICAL upload file button
        print("\n3️⃣ Testing CRITICAL upload file button...")
        update = self.create_mock_update(callback_data="upload_1")
        context = self.create_mock_context()
        
        await self.bot.handle_callback_query(update, context)
        
        # Verify upload prompt was shown
        assert update.callback_query.answer.called, "Upload callback should be answered"
        assert update.callback_query.edit_message_text.called, "Upload prompt should be shown"
        
        # Check the upload message content
        call_args = update.callback_query.edit_message_text.call_args
        if call_args:
            message_text = call_args[0][0] if call_args[0] else ""
            assert "آپلود فایل" in message_text, "Upload message should contain upload text"
            assert "راهنما" in message_text, "Upload message should contain instructions"
            assert "50 مگابایت" in message_text, "Upload message should mention size limit"
            print("✅ Upload file button shows correct prompt")
        else:
            raise AssertionError("Upload prompt message not found")
        
        # Verify user session is set correctly for upload
        session = await self.bot.db.get_user_session(self.test_user_id)
        assert session.current_category == 1, "User should be in correct category for upload"
        print("✅ User session updated correctly for upload")
        
        # Step 4: Test actual file upload
        print("\n4️⃣ Testing actual file upload...")
        
        # Create mock document
        document = MagicMock(spec=Document)
        document.file_name = "test_document.pdf"
        document.file_size = 1024 * 1024  # 1MB
        document.file_id = "test_file_id_12345"
        document.mime_type = "application/pdf"
        
        update = self.create_mock_update(document=document)
        context = self.create_mock_context()
        
        await self.bot.file_handler.handle_file_upload(update, context)
        
        # Verify file was processed
        assert context.bot.forward_message.called, "File should be forwarded to storage channel"
        assert update.message.reply_text.called, "Success message should be sent"
        
        # Check success message
        call_args = update.message.reply_text.call_args
        if call_args:
            message_text = call_args[0][0] if call_args[0] else ""
            assert "موفقیت" in message_text, "Success message should contain success text"
            assert "test_document.pdf" in message_text, "Success message should contain filename"
            print("✅ File upload processed successfully")
        
        # Verify file was saved to database
        files = await self.bot.db.get_files(1, limit=10)
        uploaded_file = None
        for file in files:
            if file.file_name == "test_document.pdf":
                uploaded_file = file
                break
        
        assert uploaded_file is not None, "File should be saved to database"
        assert uploaded_file.file_size == 1024 * 1024, "File size should be correct"
        assert uploaded_file.category_id == 1, "File should be in correct category"
        print("✅ File saved to database correctly")
        
        # Step 5: Test view files button
        print("\n5️⃣ Testing view files button...")
        update = self.create_mock_update(callback_data="files_1")
        context = self.create_mock_context()
        
        await self.bot.handle_callback_query(update, context)
        
        assert update.callback_query.answer.called, "Files callback should be answered"
        assert update.callback_query.edit_message_text.called, "Files list should be shown"
        
        # Check if uploaded file appears in the list
        call_args = update.callback_query.edit_message_text.call_args
        if call_args:
            message_text = call_args[0][0] if call_args[0] else ""
            assert "test_document.pdf" in message_text, "Uploaded file should appear in files list"
            print("✅ View files button shows uploaded file")
        
        # Step 6: Test other buttons
        print("\n6️⃣ Testing other buttons...")
        
        # Test broadcast button
        update = self.create_mock_update(callback_data="broadcast_menu")
        await self.bot.handle_callback_query(update, context)
        assert update.callback_query.edit_message_text.called, "Broadcast menu should be shown"
        print("✅ Broadcast button works")
        
        # Test search button
        update = self.create_mock_update(callback_data="search")
        await self.bot.handle_callback_query(update, context)
        assert update.callback_query.edit_message_text.called, "Search prompt should be shown"
        print("✅ Search button works")
        
        # Test stats button
        update = self.create_mock_update(callback_data="stats")
        await self.bot.handle_callback_query(update, context)
        assert update.callback_query.edit_message_text.called, "Stats should be shown"
        print("✅ Stats button works")
        
        print("\n" + "=" * 50)
        print("🎉 COMPLETE WORKFLOW TEST PASSED!")
        print("✅ All critical functionality is working:")
        print("   • /start command shows main menu")
        print("   • Category navigation works")
        print("   • 📤 Upload file button shows correct prompt (CRITICAL FIX VERIFIED)")
        print("   • File upload processing works")
        print("   • 📁 View files button shows uploaded files")
        print("   • Broadcast, search, and stats buttons work")
        print("\n🔧 The previous 'دستور نامشخص' (Unknown command) error has been FIXED!")
        
        return True

async def main():
    """Main test function"""
    tester = IntegrationTester()
    try:
        success = await tester.test_complete_workflow()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        logger.error("Integration test failed", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))