#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram Bot Interaction Test
تست تعامل با ربات تلگرام
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional

class TelegramBotInteractionTester:
    """تست کننده تعامل با ربات تلگرام"""
    
    def __init__(self):
        self.bot_token = "8428725185:AAELFU6lUasbSDUvRuhTLNDBT3uEmvNruN0"
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Test tracking
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
    
    def test_bot_info(self) -> bool:
        """Test 1: Get Bot Information"""
        try:
            response = requests.get(f"{self.base_url}/getMe", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    username = bot_info.get('username', 'Unknown')
                    first_name = bot_info.get('first_name', 'Unknown')
                    
                    self.log_test(
                        "Bot Information",
                        True,
                        f"Username: @{username}, Name: {first_name}, ID: {bot_info.get('id')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Bot Information",
                        False,
                        f"API returned error: {data}"
                    )
                    return False
            else:
                self.log_test(
                    "Bot Information",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Bot Information",
                False,
                f"Connection error: {str(e)}"
            )
            return False
    
    def test_webhook_info(self) -> bool:
        """Test 2: Get Webhook Information"""
        try:
            response = requests.get(f"{self.base_url}/getWebhookInfo", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    webhook_info = data.get('result', {})
                    webhook_url = webhook_info.get('url', '')
                    has_webhook = bool(webhook_url)
                    
                    self.log_test(
                        "Webhook Information",
                        True,
                        f"Webhook URL: {webhook_url if webhook_url else 'Not set (polling mode)'}, "
                        f"Pending updates: {webhook_info.get('pending_update_count', 0)}"
                    )
                    return True
                else:
                    self.log_test(
                        "Webhook Information",
                        False,
                        f"API returned error: {data}"
                    )
                    return False
            else:
                self.log_test(
                    "Webhook Information",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Webhook Information",
                False,
                f"Connection error: {str(e)}"
            )
            return False
    
    def test_bot_commands(self) -> bool:
        """Test 3: Get Bot Commands"""
        try:
            response = requests.get(f"{self.base_url}/getMyCommands", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    commands = data.get('result', [])
                    command_list = [f"/{cmd.get('command')} - {cmd.get('description')}" for cmd in commands]
                    
                    self.log_test(
                        "Bot Commands",
                        True,
                        f"Commands count: {len(commands)}, Commands: {'; '.join(command_list) if command_list else 'No commands set'}"
                    )
                    return True
                else:
                    self.log_test(
                        "Bot Commands",
                        False,
                        f"API returned error: {data}"
                    )
                    return False
            else:
                self.log_test(
                    "Bot Commands",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Bot Commands",
                False,
                f"Connection error: {str(e)}"
            )
            return False
    
    def test_bot_updates(self) -> bool:
        """Test 4: Check for Recent Updates (Non-intrusive)"""
        try:
            # Get updates with limit=1 and timeout=1 to avoid blocking
            response = requests.get(
                f"{self.base_url}/getUpdates", 
                params={'limit': 1, 'timeout': 1},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    updates = data.get('result', [])
                    
                    self.log_test(
                        "Bot Updates Check",
                        True,
                        f"Recent updates available: {len(updates)}, Bot is responsive to Telegram API"
                    )
                    return True
                else:
                    self.log_test(
                        "Bot Updates Check",
                        False,
                        f"API returned error: {data}"
                    )
                    return False
            else:
                self.log_test(
                    "Bot Updates Check",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Bot Updates Check",
                False,
                f"Connection error: {str(e)}"
            )
            return False
    
    def test_download_system_integration_callbacks(self) -> bool:
        """Test 5: Check Download System Integration in Bot Code"""
        try:
            # Check if the bot has the download system callbacks properly integrated
            bot_main_file = "/app/bot/bot_main.py"
            
            with open(bot_main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for specific download system callback handlers
            callbacks_to_check = [
                'download_system_control',
                'file_download_links_',
                'create_stream_link_',
                'create_fast_link_',
                'system_monitoring',
                'system_cleanup'
            ]
            
            found_callbacks = []
            for callback in callbacks_to_check:
                if callback in content:
                    found_callbacks.append(callback)
            
            integration_score = len(found_callbacks) / len(callbacks_to_check) * 100
            
            self.log_test(
                "Download System Integration Callbacks",
                integration_score >= 80,  # At least 80% of callbacks should be present
                f"Found {len(found_callbacks)}/{len(callbacks_to_check)} callbacks ({integration_score:.1f}%): {', '.join(found_callbacks)}"
            )
            return integration_score >= 80
            
        except Exception as e:
            self.log_test(
                "Download System Integration Callbacks",
                False,
                f"Integration check error: {str(e)}"
            )
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🤖 Starting Telegram Bot Interaction Tests")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all tests
        self.test_bot_info()
        self.test_webhook_info()
        self.test_bot_commands()
        self.test_bot_updates()
        self.test_download_system_integration_callbacks()
        
        # Print summary
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("📊 TELEGRAM BOT TEST SUMMARY")
        print("=" * 60)
        print(f"⏱  Duration: {duration:.2f} seconds")
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
        
        print("\n" + "=" * 60)
        
        # Return success status
        return len(self.failed_tests) == 0


def main():
    """Main test function"""
    tester = TelegramBotInteractionTester()
    success = tester.run_all_tests()
    
    if success:
        print("🎉 All Telegram bot tests passed successfully!")
        return 0
    else:
        print("⚠️  Some Telegram bot tests failed. Please check the details above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())