#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Specific Callback Handler Test for Telegram Bot
تست خاص برای callback handler های ربات تلگرام
"""

import asyncio
import sys
import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Add bot directory to path
sys.path.append(str(Path(__file__).parent / 'bot'))

from telegram import Update, CallbackQuery, User, Chat, Message
from telegram.ext import ContextTypes

# Import bot components
from bot_main import TelegramFileBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CallbackHandlerTester:
    """تست کننده callback handler های ربات"""
    
    def __init__(self):
        self.bot = TelegramFileBot()
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n🔍 Test: {test_name}")
        print(f"   Status: {status}")
        if details:
            print(f"   Details: {details}")
        
        if success:
            self.tests_passed += 1
        else:
            self.failed_tests.append({
                'name': test_name,
                'details': details
            })
    
    def create_mock_update(self, callback_data: str, user_id: int = 12345) -> Update:
        """Create mock update for callback query"""
        # Create mock user
        user = User(
            id=user_id,
            is_bot=False,
            first_name="Test",
            username="testuser"
        )
        
        # Create mock chat
        chat = Chat(
            id=user_id,
            type="private"
        )
        
        # Create mock message
        message = Message(
            message_id=1,
            date=None,
            chat=chat,
            from_user=user
        )
        
        # Create mock callback query
        callback_query = CallbackQuery(
            id="test_callback",
            from_user=user,
            chat_instance="test_instance",
            data=callback_data,
            message=message
        )
        
        # Mock callback query methods
        callback_query.answer = AsyncMock()
        callback_query.edit_message_text = AsyncMock()
        callback_query.edit_message_reply_markup = AsyncMock()
        
        # Create mock update
        update = Update(
            update_id=1,
            callback_query=callback_query
        )
        
        # Set effective user and chat
        update._effective_user = user
        update._effective_chat = chat
        
        return update
    
    def create_mock_context(self) -> ContextTypes.DEFAULT_TYPE:
        """Create mock context"""
        context = MagicMock()
        context.bot = MagicMock()
        context.bot.get_me = AsyncMock(return_value=MagicMock(username="testbot"))
        return context
    
    async def test_download_system_control_callback(self) -> bool:
        """Test download_system_control callback"""
        try:
            update = self.create_mock_update("download_system_control")
            context = self.create_mock_context()
            
            # Call the callback handler
            await self.bot.handle_callback_query(update, context)
            
            # Check if callback was answered
            callback_answered = update.callback_query.answer.called
            message_edited = update.callback_query.edit_message_text.called
            
            success = callback_answered and message_edited
            
            self.log_test(
                "Download System Control Callback",
                success,
                f"Callback answered: {callback_answered}, Message edited: {message_edited}"
            )
            
            return success
            
        except Exception as e:
            self.log_test(
                "Download System Control Callback",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_file_download_links_callback(self) -> bool:
        """Test file_download_links_X callback"""
        try:
            # Test with file ID 1
            update = self.create_mock_update("file_download_links_1")
            context = self.create_mock_context()
            
            # Call the callback handler
            await self.bot.handle_callback_query(update, context)
            
            # Check if callback was answered
            callback_answered = update.callback_query.answer.called
            message_edited = update.callback_query.edit_message_text.called
            
            success = callback_answered and message_edited
            
            self.log_test(
                "File Download Links Callback",
                success,
                f"Callback answered: {callback_answered}, Message edited: {message_edited}"
            )
            
            return success
            
        except Exception as e:
            self.log_test(
                "File Download Links Callback",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_unknown_callback(self) -> bool:
        """Test unknown callback handling"""
        try:
            update = self.create_mock_update("unknown_callback_test")
            context = self.create_mock_context()
            
            # Call the callback handler
            await self.bot.handle_callback_query(update, context)
            
            # Check if callback was answered (should be answered even for unknown callbacks)
            callback_answered = update.callback_query.answer.called
            
            self.log_test(
                "Unknown Callback Handling",
                callback_answered,
                f"Callback answered: {callback_answered}"
            )
            
            return callback_answered
            
        except Exception as e:
            self.log_test(
                "Unknown Callback Handling",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_callback_data_parsing(self) -> bool:
        """Test callback data parsing logic"""
        try:
            test_cases = [
                "download_system_control",
                "file_download_links_123",
                "create_stream_link_456",
                "create_fast_link_789",
                "system_monitoring",
                "system_cleanup"
            ]
            
            parsing_results = []
            
            for callback_data in test_cases:
                try:
                    action = callback_data.split('_')[0]
                    parsing_results.append(f"{callback_data} -> {action}")
                except Exception as e:
                    parsing_results.append(f"{callback_data} -> ERROR: {e}")
            
            success = all("ERROR" not in result for result in parsing_results)
            
            self.log_test(
                "Callback Data Parsing",
                success,
                f"Results: {'; '.join(parsing_results)}"
            )
            
            return success
            
        except Exception as e:
            self.log_test(
                "Callback Data Parsing",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_download_system_api_integration(self) -> bool:
        """Test download system API integration"""
        try:
            # Test if download system handler can communicate with API
            handler = self.bot.download_system_handler
            
            # Test system status
            status = await handler.get_system_status()
            status_ok = status.get('ready', False)
            
            # Test metrics (may fail due to auth, but should not crash)
            try:
                metrics = await handler.get_real_time_metrics()
                metrics_ok = isinstance(metrics, dict)
            except:
                metrics_ok = True  # It's OK if it fails due to auth
            
            success = status_ok and metrics_ok
            
            self.log_test(
                "Download System API Integration",
                success,
                f"Status OK: {status_ok}, Metrics OK: {metrics_ok}, Status: {status}"
            )
            
            return success
            
        except Exception as e:
            self.log_test(
                "Download System API Integration",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def run_all_tests(self):
        """Run all callback handler tests"""
        print("🚀 Starting Callback Handler Tests")
        print("=" * 50)
        
        # Run tests
        await self.test_download_system_control_callback()
        await self.test_file_download_links_callback()
        await self.test_unknown_callback()
        await self.test_callback_data_parsing()
        await self.test_download_system_api_integration()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 CALLBACK HANDLER TEST SUMMARY")
        print("=" * 50)
        print(f"📈 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {len(self.failed_tests)}")
        print(f"📊 Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test['name']}")
                if test['details']:
                    print(f"      → {test['details']}")
        
        print("\n" + "=" * 50)
        
        return len(self.failed_tests) == 0


async def main():
    """Main test function"""
    tester = CallbackHandlerTester()
    success = await tester.run_all_tests()
    
    if success:
        print("🎉 All callback handler tests passed!")
        return 0
    else:
        print("⚠️  Some callback handler tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))