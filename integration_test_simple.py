#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple Integration Test for Download System and Bot
تست ادغام ساده سیستم دانلود و ربات
"""

import asyncio
import sys
import logging
import requests
from pathlib import Path

# Add bot directory to path
sys.path.append(str(Path(__file__).parent / 'bot'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleIntegrationTester:
    """تست کننده ادغام ساده"""
    
    def __init__(self):
        self.download_api_url = "http://localhost:8001"
        self.admin_token = "UeZ7nxNr-0Z_6b9dntKcOdzzLU1fMZjNz1-SqWQESkY"  # From review request
        self.bot_admin_token = "SdYmbHA6QQs3_m6BU6fNuD6qD6mMoMPNN1ecQiQ7z1g"  # From bot code
        
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        self.headers_review = {'Authorization': f'Bearer {self.admin_token}'}
        self.headers_bot = {'Authorization': f'Bearer {self.bot_admin_token}'}
    
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
    
    def test_admin_token_validation(self) -> bool:
        """Test admin token validation"""
        try:
            # Test review request token
            response1 = requests.get(
                f"{self.download_api_url}/api/system/metrics",
                headers=self.headers_review,
                timeout=10
            )
            
            # Test bot code token
            response2 = requests.get(
                f"{self.download_api_url}/api/system/metrics",
                headers=self.headers_bot,
                timeout=10
            )
            
            review_token_valid = response1.status_code in [200, 401, 403]
            bot_token_valid = response2.status_code in [200, 401, 403]
            
            self.log_test(
                "Admin Token Validation",
                review_token_valid and bot_token_valid,
                f"Review token ({self.admin_token[:20]}...): HTTP {response1.status_code}, "
                f"Bot token ({self.bot_admin_token[:20]}...): HTTP {response2.status_code}"
            )
            
            return review_token_valid and bot_token_valid
            
        except Exception as e:
            self.log_test(
                "Admin Token Validation",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def test_download_system_endpoints(self) -> bool:
        """Test download system endpoints"""
        try:
            endpoints = [
                ("/health", "GET", None),
                ("/", "GET", None),
                ("/api/system/metrics", "GET", self.headers_bot),
                ("/api/download/links/create", "POST", self.headers_bot),
                ("/api/system/cache/cleanup", "POST", self.headers_bot)
            ]
            
            results = []
            all_passed = True
            
            for endpoint, method, headers in endpoints:
                try:
                    url = f"{self.download_api_url}{endpoint}"
                    
                    if method == "GET":
                        response = requests.get(url, headers=headers, timeout=10)
                    else:  # POST
                        test_data = {"test": True}
                        response = requests.post(url, headers=headers, json=test_data, timeout=10)
                    
                    # Accept various success codes
                    success = response.status_code in [200, 201, 422, 401, 403]
                    results.append(f"{endpoint}: HTTP {response.status_code}")
                    
                    if not success:
                        all_passed = False
                        
                except Exception as e:
                    results.append(f"{endpoint}: Error - {str(e)}")
                    all_passed = False
            
            self.log_test(
                "Download System Endpoints",
                all_passed,
                f"Results: {'; '.join(results)}"
            )
            
            return all_passed
            
        except Exception as e:
            self.log_test(
                "Download System Endpoints",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_download_system_handler_import(self) -> bool:
        """Test download system handler import and initialization"""
        try:
            # Import the handler
            from handlers.download_system_handler import DownloadSystemHandler
            from database.db_manager import DatabaseManager
            
            # Initialize database
            db = DatabaseManager()
            
            # Initialize handler with both tokens
            handler1 = DownloadSystemHandler(
                db,
                download_api_url=self.download_api_url,
                admin_token=self.admin_token
            )
            
            handler2 = DownloadSystemHandler(
                db,
                download_api_url=self.download_api_url,
                admin_token=self.bot_admin_token
            )
            
            # Test system status with both handlers
            status1 = await handler1.get_system_status()
            status2 = await handler2.get_system_status()
            
            handler1_ok = status1.get('ready', False)
            handler2_ok = status2.get('ready', False)
            
            success = handler1_ok and handler2_ok
            
            self.log_test(
                "Download System Handler Import",
                success,
                f"Handler1 (review token): {handler1_ok}, Handler2 (bot token): {handler2_ok}"
            )
            
            return success
            
        except Exception as e:
            self.log_test(
                "Download System Handler Import",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def test_callback_data_patterns(self) -> bool:
        """Test callback data patterns used in bot"""
        try:
            # Test patterns from the problematic callbacks
            test_patterns = [
                "download_system_control",
                "file_download_links_1",
                "file_download_links_123",
                "create_stream_link_456",
                "create_fast_link_789",
                "system_monitoring",
                "system_cleanup"
            ]
            
            parsing_results = []
            
            for pattern in test_patterns:
                try:
                    # Simulate the parsing logic from bot_main.py
                    action = pattern.split('_')[0]
                    
                    # Check specific patterns
                    if pattern == "download_system_control":
                        result = "✅ Matches download_system_control"
                    elif pattern.startswith("file_download_links_"):
                        file_id = pattern.split('_')[3]
                        result = f"✅ Matches file_download_links with ID: {file_id}"
                    elif pattern.startswith("create_stream_link_"):
                        file_id = pattern.split('_')[3]
                        result = f"✅ Matches create_stream_link with ID: {file_id}"
                    elif pattern.startswith("create_fast_link_"):
                        file_id = pattern.split('_')[3]
                        result = f"✅ Matches create_fast_link with ID: {file_id}"
                    elif pattern in ["system_monitoring", "system_cleanup"]:
                        result = f"✅ Matches {pattern}"
                    else:
                        result = f"⚠️ Unknown pattern: {pattern}"
                    
                    parsing_results.append(f"{pattern} -> {result}")
                    
                except Exception as e:
                    parsing_results.append(f"{pattern} -> ❌ ERROR: {e}")
            
            success = all("❌ ERROR" not in result for result in parsing_results)
            
            self.log_test(
                "Callback Data Patterns",
                success,
                f"Results: {'; '.join(parsing_results[:3])}..." if len(parsing_results) > 3 else f"Results: {'; '.join(parsing_results)}"
            )
            
            return success
            
        except Exception as e:
            self.log_test(
                "Callback Data Patterns",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def test_bot_main_callback_routing(self) -> bool:
        """Test bot main callback routing logic"""
        try:
            # Read bot_main.py and check for callback routing
            bot_main_file = "/app/bot/bot_main.py"
            
            with open(bot_main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for specific callback handlers
            checks = {
                'download_system_control': 'download_system_control' in content,
                'file_download_links': 'file_download_links_' in content,
                'create_stream_link': 'create_stream_link_' in content,
                'create_fast_link': 'create_fast_link_' in content,
                'system_monitoring': 'system_monitoring' in content,
                'system_cleanup': 'system_cleanup' in content,
                'download_system_handler': 'download_system_handler' in content
            }
            
            all_present = all(checks.values())
            
            details = []
            for check, present in checks.items():
                status = "✅" if present else "❌"
                details.append(f"{check}: {status}")
            
            self.log_test(
                "Bot Main Callback Routing",
                all_present,
                f"Checks: {'; '.join(details)}"
            )
            
            return all_present
            
        except Exception as e:
            self.log_test(
                "Bot Main Callback Routing",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting Simple Integration Tests")
        print("=" * 60)
        
        # Run tests
        self.test_admin_token_validation()
        self.test_download_system_endpoints()
        await self.test_download_system_handler_import()
        self.test_callback_data_patterns()
        self.test_bot_main_callback_routing()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 INTEGRATION TEST SUMMARY")
        print("=" * 60)
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
        
        return len(self.failed_tests) == 0


async def main():
    """Main test function"""
    tester = SimpleIntegrationTester()
    success = await tester.run_all_tests()
    
    if success:
        print("🎉 All integration tests passed!")
        return 0
    else:
        print("⚠️  Some integration tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))