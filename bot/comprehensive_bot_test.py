#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive Telegram Bot Test
Tests all major functionality including the critical upload file button
"""

import asyncio
import aiosqlite
import logging
from pathlib import Path
from telegram import Update, User, Chat, Message, CallbackQuery
from telegram.ext import ContextTypes
from unittest.mock import AsyncMock, MagicMock
import sys

# Add bot directory to path
sys.path.append(str(Path(__file__).parent))

from bot_main import TelegramFileBot
from config.settings import BOT_TOKEN, STORAGE_CHANNEL_ID

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BotTester:
    """Comprehensive bot functionality tester"""
    
    def __init__(self):
        self.bot = TelegramFileBot()
        self.test_user_id = 12345
        self.test_chat_id = 67890
        self.tests_passed = 0
        self.tests_failed = 0
        
    def create_mock_update(self, text=None, callback_data=None, user_id=None):
        """Create mock update object"""
        user_id = user_id or self.test_user_id
        
        # Create mock user
        user = User(
            id=user_id,
            is_bot=False,
            first_name="Test",
            username="testuser"
        )
        
        # Create mock chat
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
            message.reply_text = AsyncMock()
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
        
        return update
    
    def create_mock_context(self):
        """Create mock context"""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.bot = MagicMock()
        context.bot.forward_message = AsyncMock()
        context.bot.send_message = AsyncMock()
        return context
    
    async def run_test(self, test_name, test_func):
        """Run individual test"""
        try:
            print(f"\n🔍 Testing: {test_name}")
            await test_func()
            print(f"✅ PASSED: {test_name}")
            self.tests_passed += 1
        except Exception as e:
            print(f"❌ FAILED: {test_name} - {str(e)}")
            self.tests_failed += 1
            logger.error(f"Test failed: {test_name}", exc_info=True)
    
    async def test_start_command(self):
        """Test /start command"""
        update = self.create_mock_update(text="/start")
        context = self.create_mock_context()
        
        await self.bot.start_command(update, context)
        
        # Verify message was sent
        assert update.message.reply_text.called, "Start message should be sent"
        
        # Check if user session was created/updated
        session = await self.bot.db.get_user_session(self.test_user_id)
        assert session.current_category == 1, "User should be in root category"
        assert session.action_state == 'browsing', "User should be in browsing state"
    
    async def test_category_navigation(self):
        """Test category navigation"""
        update = self.create_mock_update(callback_data="cat_1")
        context = self.create_mock_context()
        
        await self.bot.handle_callback_query(update, context)
        
        # Verify callback was answered
        assert update.callback_query.answer.called, "Callback should be answered"
        assert update.callback_query.edit_message_text.called, "Message should be edited"
    
    async def test_upload_file_button(self):
        """Test the critical upload file button functionality"""
        # Test upload button callback
        update = self.create_mock_update(callback_data="upload_1")
        context = self.create_mock_context()
        
        await self.bot.handle_callback_query(update, context)
        
        # Verify the upload prompt was shown
        assert update.callback_query.answer.called, "Upload callback should be answered"
        assert update.callback_query.edit_message_text.called, "Upload prompt should be shown"
        
        # Check if the message contains upload instructions
        call_args = update.callback_query.edit_message_text.call_args
        if call_args:
            message_text = call_args[0][0] if call_args[0] else ""
            assert "آپلود فایل" in message_text, "Upload message should contain upload text"
            assert "راهنما" in message_text, "Upload message should contain instructions"
        
        # Verify user session is updated for current category
        session = await self.bot.db.get_user_session(self.test_user_id)
        assert session.current_category == 1, "User should be in correct category for upload"
    
    async def test_view_files_button(self):
        """Test view files button"""
        update = self.create_mock_update(callback_data="files_1")
        context = self.create_mock_context()
        
        await self.bot.handle_callback_query(update, context)
        
        # Verify files view was shown
        assert update.callback_query.answer.called, "Files callback should be answered"
        assert update.callback_query.edit_message_text.called, "Files list should be shown"
    
    async def test_broadcast_button(self):
        """Test broadcast menu button"""
        update = self.create_mock_update(callback_data="broadcast_menu")
        context = self.create_mock_context()
        
        await self.bot.handle_callback_query(update, context)
        
        # Verify broadcast menu was shown
        assert update.callback_query.answer.called, "Broadcast callback should be answered"
        assert update.callback_query.edit_message_text.called, "Broadcast menu should be shown"
    
    async def test_search_button(self):
        """Test search button"""
        update = self.create_mock_update(callback_data="search")
        context = self.create_mock_context()
        
        await self.bot.handle_callback_query(update, context)
        
        # Verify search prompt was shown
        assert update.callback_query.answer.called, "Search callback should be answered"
        assert update.callback_query.edit_message_text.called, "Search prompt should be shown"
        
        # Check user state
        session = await self.bot.db.get_user_session(self.test_user_id)
        assert session.action_state == 'searching', "User should be in searching state"
    
    async def test_stats_button(self):
        """Test stats button"""
        update = self.create_mock_update(callback_data="stats")
        context = self.create_mock_context()
        
        await self.bot.handle_callback_query(update, context)
        
        # Verify stats were shown
        assert update.callback_query.answer.called, "Stats callback should be answered"
        assert update.callback_query.edit_message_text.called, "Stats should be shown"
    
    async def test_unknown_command_handling(self):
        """Test that unknown commands are handled properly"""
        update = self.create_mock_update(callback_data="unknown_command")
        context = self.create_mock_context()
        
        await self.bot.handle_callback_query(update, context)
        
        # Should answer with error message, not crash
        assert update.callback_query.answer.called, "Unknown command should be answered"
    
    async def test_file_upload_simulation(self):
        """Test file upload handling"""
        # First set user to upload state
        await self.bot.db.update_user_session(
            self.test_user_id,
            current_category=1,
            action_state='browsing'
        )
        
        # Create mock file message
        update = self.create_mock_update()
        context = self.create_mock_context()
        
        # Mock document
        document = MagicMock()
        document.file_name = "test_file.pdf"
        document.file_size = 1024 * 1024  # 1MB
        document.file_id = "test_file_id_123"
        document.mime_type = "application/pdf"
        
        message = MagicMock(spec=Message)
        message.document = document
        message.photo = None
        message.video = None
        message.audio = None
        message.reply_text = AsyncMock()
        
        update.message = message
        update.callback_query = None
        
        # Mock forward message response
        forwarded_message = MagicMock()
        forwarded_message.message_id = 999
        context.bot.forward_message.return_value = forwarded_message
        
        await self.bot.message_handler.handle_file_message(update, context)
        
        # Verify file was processed
        assert context.bot.forward_message.called, "File should be forwarded to storage"
        assert update.message.reply_text.called, "Success message should be sent"
    
    async def test_database_operations(self):
        """Test database operations"""
        # Test category operations
        categories = await self.bot.db.get_categories(1)
        assert len(categories) > 0, "Should have categories"
        
        # Test user session operations
        session = await self.bot.db.get_user_session(self.test_user_id)
        assert session is not None, "Should have user session"
        
        # Test category retrieval
        root_category = await self.bot.db.get_category_by_id(1)
        assert root_category is not None, "Should have root category"
        assert "فایل" in root_category.name, "Root category should be files category"
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting Comprehensive Bot Tests")
        print("=" * 50)
        
        # Initialize database
        await self.bot.db.init_database()
        
        # Run all tests
        await self.run_test("Database Operations", self.test_database_operations)
        await self.run_test("Start Command", self.test_start_command)
        await self.run_test("Category Navigation", self.test_category_navigation)
        await self.run_test("Upload File Button (CRITICAL)", self.test_upload_file_button)
        await self.run_test("View Files Button", self.test_view_files_button)
        await self.run_test("Broadcast Button", self.test_broadcast_button)
        await self.run_test("Search Button", self.test_search_button)
        await self.run_test("Stats Button", self.test_stats_button)
        await self.run_test("Unknown Command Handling", self.test_unknown_command_handling)
        await self.run_test("File Upload Simulation", self.test_file_upload_simulation)
        
        # Print results
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS:")
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        print(f"📈 Success Rate: {(self.tests_passed/(self.tests_passed + self.tests_failed)*100):.1f}%")
        
        if self.tests_failed == 0:
            print("\n🎉 ALL TESTS PASSED! Bot functionality is working correctly.")
        else:
            print(f"\n⚠️  {self.tests_failed} tests failed. Please check the issues above.")
        
        return self.tests_failed == 0

async def main():
    """Main test function"""
    tester = BotTester()
    success = await tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))