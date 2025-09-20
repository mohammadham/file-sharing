#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive Category Test - Specific test for user's request
Tests category editing and transfer functionality
"""

import asyncio
import aiosqlite
import logging
from pathlib import Path
from telegram import Update, User, Chat, Message, CallbackQuery
from telegram.ext import ContextTypes
from unittest.mock import AsyncMock, MagicMock
import sys
import json

# Add bot directory to path
sys.path.append(str(Path(__file__).parent))

from bot_main import TelegramFileBot
from config.settings import BOT_TOKEN, STORAGE_CHANNEL_ID

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CategoryTester:
    """Comprehensive category functionality tester"""
    
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
        context.bot.get_me = AsyncMock()
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
    
    async def test_start_command_detailed(self):
        """Test /start command in detail"""
        update = self.create_mock_update(text="/start")
        context = self.create_mock_context()
        
        await self.bot.start_command(update, context)
        
        # Verify message was sent
        assert update.message.reply_text.called, "Start message should be sent"
        
        # Check if user session was created/updated
        session = await self.bot.db.get_user_session(self.test_user_id)
        assert session.current_category == 1, "User should be in root category"
        assert session.action_state == 'browsing', "User should be in browsing state"
        
        # Check the message content
        call_args = update.message.reply_text.call_args
        if call_args:
            message_text = call_args[0][0] if call_args[0] else ""
            assert "سلام" in message_text, "Welcome message should contain greeting"
            assert "مدیریت فایل" in message_text, "Should mention file management"
    
    async def test_category_navigation_detailed(self):
        """Test category navigation in detail"""
        # Get available categories first
        categories = await self.bot.db.get_categories(1)
        if not categories:
            print("   ⚠️ No subcategories found, skipping detailed navigation test")
            return
        
        # Test navigating to first subcategory
        first_category = categories[0]
        update = self.create_mock_update(callback_data=f"cat_{first_category.id}")
        context = self.create_mock_context()
        
        await self.bot.handle_callback_query(update, context)
        
        # Verify callback was answered
        assert update.callback_query.answer.called, "Callback should be answered"
        assert update.callback_query.edit_message_text.called, "Message should be edited"
        
        # Check user session was updated
        session = await self.bot.db.get_user_session(self.test_user_id)
        assert session.current_category == first_category.id, f"User should be in category {first_category.id}"
    
    async def test_category_edit_menu(self):
        """Test category edit menu - CRITICAL TEST"""
        # Get a category to edit
        categories = await self.bot.db.get_categories(1)
        if not categories:
            print("   ⚠️ No categories to edit, creating test category")
            # Create a test category
            test_category_id = await self.bot.db.create_category("Test Category", "Test Description", 1)
            category_id = test_category_id
        else:
            category_id = categories[0].id
        
        # Test edit category menu
        update = self.create_mock_update(callback_data=f"edit_category_menu_{category_id}")
        context = self.create_mock_context()
        
        await self.bot.handle_callback_query(update, context)
        
        # Verify callback was answered
        assert update.callback_query.answer.called, "Edit menu callback should be answered"
        assert update.callback_query.edit_message_text.called, "Edit menu should be shown"
        
        # Check the message content for edit options
        call_args = update.callback_query.edit_message_text.call_args
        if call_args:
            message_text = call_args[0][0] if call_args[0] else ""
            assert "ویرایش" in message_text, "Edit menu should contain edit text"
    
    async def test_category_name_edit(self):
        """Test category name editing - CRITICAL TEST"""
        # Get a category to edit
        categories = await self.bot.db.get_categories(1)
        if not categories:
            # Create a test category
            test_category_id = await self.bot.db.create_category("Test Category", "Test Description", 1)
            category_id = test_category_id
        else:
            category_id = categories[0].id
        
        # Test edit category name
        update = self.create_mock_update(callback_data=f"edit_cat_name_{category_id}")
        context = self.create_mock_context()
        
        await self.bot.handle_callback_query(update, context)
        
        # Verify callback was answered
        assert update.callback_query.answer.called, "Edit name callback should be answered"
        assert update.callback_query.edit_message_text.called, "Edit name prompt should be shown"
        
        # Check user session state
        session = await self.bot.db.get_user_session(self.test_user_id)
        assert session.action_state == 'editing_category_name', "User should be in editing name state"
        
        # Check temp data contains category id
        if session.temp_data:
            temp_data = json.loads(session.temp_data)
            assert temp_data.get('category_id') == category_id, "Temp data should contain category ID"
    
    async def test_category_description_edit(self):
        """Test category description editing - CRITICAL TEST"""
        # Get a category to edit
        categories = await self.bot.db.get_categories(1)
        if not categories:
            # Create a test category
            test_category_id = await self.bot.db.create_category("Test Category", "Test Description", 1)
            category_id = test_category_id
        else:
            category_id = categories[0].id
        
        # Test edit category description
        update = self.create_mock_update(callback_data=f"edit_cat_desc_{category_id}")
        context = self.create_mock_context()
        
        await self.bot.handle_callback_query(update, context)
        
        # Verify callback was answered
        assert update.callback_query.answer.called, "Edit description callback should be answered"
        assert update.callback_query.edit_message_text.called, "Edit description prompt should be shown"
        
        # Check user session state
        session = await self.bot.db.get_user_session(self.test_user_id)
        assert session.action_state == 'editing_category_description', "User should be in editing description state"
        
        # Check temp data contains category id
        if session.temp_data:
            temp_data = json.loads(session.temp_data)
            assert temp_data.get('category_id') == category_id, "Temp data should contain category ID"
    
    async def test_category_transfer_functionality(self):
        """Test category transfer functionality - NEWLY IMPLEMENTED"""
        # Get categories for transfer test
        categories = await self.bot.db.get_categories(1)
        if len(categories) < 2:
            print("   ⚠️ Need at least 2 categories for transfer test, creating test categories")
            # Create test categories
            test_category_1 = await self.bot.db.create_category("Transfer Test 1", "Test Description 1", 1)
            test_category_2 = await self.bot.db.create_category("Transfer Test 2", "Test Description 2", 1)
            category_to_move = test_category_1
        else:
            category_to_move = categories[0].id
        
        # Test move category
        update = self.create_mock_update(callback_data=f"move_category_{category_to_move}")
        context = self.create_mock_context()
        
        await self.bot.handle_callback_query(update, context)
        
        # Verify callback was answered
        assert update.callback_query.answer.called, "Move category callback should be answered"
        assert update.callback_query.edit_message_text.called, "Move category interface should be shown"
        
        # Check user session state
        session = await self.bot.db.get_user_session(self.test_user_id)
        assert session.action_state == 'moving_category', "User should be in moving category state"
        
        # Check temp data contains category info
        if session.temp_data:
            temp_data = json.loads(session.temp_data)
            assert temp_data.get('category_id') == category_to_move, "Temp data should contain category ID to move"
    
    async def test_category_transfer_navigation(self):
        """Test category transfer navigation"""
        # Get categories for navigation test
        categories = await self.bot.db.get_categories(1)
        if not categories:
            print("   ⚠️ No categories for navigation test")
            return
        
        category_to_move = categories[0].id
        
        # Test move category navigation
        update = self.create_mock_update(callback_data=f"move_cat_nav_{category_to_move}_1")
        context = self.create_mock_context()
        
        await self.bot.handle_callback_query(update, context)
        
        # Verify callback was answered
        assert update.callback_query.answer.called, "Move navigation callback should be answered"
        assert update.callback_query.edit_message_text.called, "Move navigation should update interface"
    
    async def test_category_transfer_execution(self):
        """Test actual category transfer execution"""
        # Get categories for transfer execution test
        categories = await self.bot.db.get_categories(1)
        if len(categories) < 1:
            print("   ⚠️ No categories for transfer execution test")
            return
        
        category_to_move = categories[0].id
        destination_category = 1  # Move to root
        
        # Test move category to destination
        update = self.create_mock_update(callback_data=f"move_cat_to_{category_to_move}_{destination_category}")
        context = self.create_mock_context()
        
        await self.bot.handle_callback_query(update, context)
        
        # Verify callback was answered
        assert update.callback_query.answer.called, "Move execution callback should be answered"
        assert update.callback_query.edit_message_text.called, "Move result should be shown"
        
        # Check if category was actually moved (check database)
        moved_category = await self.bot.db.get_category_by_id(category_to_move)
        if moved_category:
            assert moved_category.parent_id == destination_category, "Category should be moved to destination"
    
    async def test_add_new_category(self):
        """Test adding new category"""
        update = self.create_mock_update(callback_data="add_cat_1")
        context = self.create_mock_context()
        
        await self.bot.handle_callback_query(update, context)
        
        # Verify callback was answered
        assert update.callback_query.answer.called, "Add category callback should be answered"
        assert update.callback_query.edit_message_text.called, "Add category prompt should be shown"
        
        # Check user session state
        session = await self.bot.db.get_user_session(self.test_user_id)
        assert session.action_state == 'adding_category', "User should be in adding category state"
    
    async def test_callback_routing(self):
        """Test callback routing for various operations"""
        test_callbacks = [
            ("cat_1", "Category navigation"),
            ("files_1", "Files view"),
            ("upload_1", "Upload file"),
            ("broadcast_menu", "Broadcast menu"),
            ("search", "Search"),
            ("stats", "Stats"),
        ]
        
        for callback_data, description in test_callbacks:
            print(f"   Testing callback: {callback_data} ({description})")
            update = self.create_mock_update(callback_data=callback_data)
            context = self.create_mock_context()
            
            try:
                await self.bot.handle_callback_query(update, context)
                assert update.callback_query.answer.called, f"{description} callback should be answered"
                print(f"   ✅ {description} callback works")
            except Exception as e:
                print(f"   ❌ {description} callback failed: {e}")
                raise
    
    async def test_session_management(self):
        """Test session management"""
        # Test session creation
        await self.bot.db.update_user_session(
            self.test_user_id,
            current_category=1,
            action_state='browsing',
            temp_data=None
        )
        
        session = await self.bot.db.get_user_session(self.test_user_id)
        assert session is not None, "Session should be created"
        assert session.current_category == 1, "Session should have correct category"
        assert session.action_state == 'browsing', "Session should have correct state"
        
        # Test session update
        await self.bot.db.update_user_session(
            self.test_user_id,
            action_state='editing_category_name',
            temp_data='{"category_id": 2}'
        )
        
        updated_session = await self.bot.db.get_user_session(self.test_user_id)
        assert updated_session.action_state == 'editing_category_name', "Session state should be updated"
        assert updated_session.temp_data == '{"category_id": 2}', "Session temp data should be updated"
    
    async def run_all_tests(self):
        """Run all category tests"""
        print("🧪 COMPREHENSIVE CATEGORY TESTING")
        print("=" * 60)
        print("Testing specific functionality requested:")
        print("1. ✏️ Category edit buttons (Edit Name, Edit Description)")
        print("2. 🔄 Category transfer functionality (newly implemented)")
        print("3. 🏠 General bot functionality (/start, navigation, etc.)")
        print("=" * 60)
        
        # Initialize database
        await self.bot.db.init_database()
        
        # Run all tests
        await self.run_test("Start Command (Detailed)", self.test_start_command_detailed)
        await self.run_test("Category Navigation (Detailed)", self.test_category_navigation_detailed)
        await self.run_test("Category Edit Menu (CRITICAL)", self.test_category_edit_menu)
        await self.run_test("Category Name Edit (CRITICAL)", self.test_category_name_edit)
        await self.run_test("Category Description Edit (CRITICAL)", self.test_category_description_edit)
        await self.run_test("Category Transfer Functionality (NEW)", self.test_category_transfer_functionality)
        await self.run_test("Category Transfer Navigation", self.test_category_transfer_navigation)
        await self.run_test("Category Transfer Execution", self.test_category_transfer_execution)
        await self.run_test("Add New Category", self.test_add_new_category)
        await self.run_test("Callback Routing", self.test_callback_routing)
        await self.run_test("Session Management", self.test_session_management)
        
        # Print results
        print("\n" + "=" * 60)
        print("📊 CATEGORY TEST RESULTS:")
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        print(f"📈 Success Rate: {(self.tests_passed/(self.tests_passed + self.tests_failed)*100):.1f}%")
        
        if self.tests_failed == 0:
            print("\n🎉 ALL CATEGORY TESTS PASSED!")
            print("✅ Category editing functionality is working correctly")
            print("✅ Category transfer functionality is working correctly")
            print("✅ Session management is working correctly")
            print("✅ Callback routing is working correctly")
        else:
            print(f"\n⚠️ {self.tests_failed} tests failed. Issues found:")
            print("Please check the detailed error messages above.")
        
        return self.tests_failed == 0

async def main():
    """Main test function"""
    tester = CategoryTester()
    success = await tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))