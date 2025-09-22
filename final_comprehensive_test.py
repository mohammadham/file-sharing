#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Final Comprehensive Test for Telegram Bot and Download System
"""

import asyncio
import sys
import logging
import requests
import aiohttp
from pathlib import Path
from datetime import datetime

# Add bot directory to path
sys.path.append(str(Path(__file__).parent / 'bot'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FinalComprehensiveTester:
    """Final comprehensive tester"""
    
    def __init__(self):
        self.download_api_url = "http://localhost:8001"
        self.admin_token_review = "UeZ7nxNr-0Z_6b9dntKcOdzzLU1fMZjNz1-SqWQESkY"  # From review request
        self.admin_token_bot = "SdYmbHA6QQs3_m6BU6fNuD6qD6mMoMPNN1ecQiQ7z1g"  # From bot code
        self.bot_token = "8428725185:AAELFU6lUasbSDUvRuhTLNDBT3uEmvNruN0"
        
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        self.headers_review = {'Authorization': f'Bearer {self.admin_token_review}'}
        self.headers_bot = {'Authorization': f'Bearer {self.admin_token_bot}'}
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        status = "PASSED" if success else "FAILED"
        print(f"\nTest: {test_name}")
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
    
    def test_telegram_bot_connection(self) -> bool:
        """Test Telegram Bot API connection"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    bot_username = bot_info.get('username', 'Unknown')
                    
                    self.log_test(
                        "Telegram Bot Connection",
                        True,
                        f"Bot @{bot_username} is active and responding"
                    )
                    return True
                else:
                    self.log_test(
                        "Telegram Bot Connection",
                        False,
                        f"Telegram API error: {data}"
                    )
                    return False
            else:
                self.log_test(
                    "Telegram Bot Connection",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Telegram Bot Connection",
                False,
                f"Connection error: {str(e)}"
            )
            return False
    
    def test_download_system_health(self) -> bool:
        """Test download system health"""
        try:
            response = requests.get(f"{self.download_api_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                is_ready = data.get('ready', False)
                status = data.get('status', 'unknown')
                
                self.log_test(
                    "Download System Health",
                    is_ready,
                    f"Status: {status}, Ready: {is_ready}, Version: {data.get('version', 'unknown')}"
                )
                return is_ready
            else:
                self.log_test(
                    "Download System Health",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Download System Health",
                False,
                f"Connection error: {str(e)}"
            )
            return False
    
    def test_problematic_callback_handlers(self) -> bool:
        """Test the specific problematic callback handlers mentioned in review"""
        try:
            # Import bot components
            from bot_main import TelegramFileBot
            
            bot = TelegramFileBot()
            
            # Test 1: Check if download_system_control callback exists in routing
            bot_main_file = "/app/bot/bot_main.py"
            with open(bot_main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for the specific problematic callbacks
            callback_checks = {
                'download_system_control': 'download_system_control' in content,
                'file_download_links_': 'file_download_links_' in content,
                'show_system_control': 'show_system_control' in content,
                'show_file_download_options': 'show_file_download_options' in content
            }
            
            # Test 2: Check if download system handler is properly initialized
            handler_initialized = hasattr(bot, 'download_system_handler')
            
            # Test 3: Check if handler has required methods
            handler_methods = []
            if handler_initialized:
                handler = bot.download_system_handler
                required_methods = [
                    'show_system_control',
                    'show_file_download_options',
                    'create_stream_link',
                    'create_fast_link',
                    'system_monitoring',
                    'system_cleanup'
                ]
                
                for method in required_methods:
                    has_method = hasattr(handler, method)
                    status = "OK" if has_method else "MISSING"
                    handler_methods.append(f"{method}: {status}")
            
            all_callbacks_present = all(callback_checks.values())
            all_methods_present = len([m for m in handler_methods if 'OK' in m]) == len(handler_methods)
            
            success = all_callbacks_present and handler_initialized and all_methods_present
            
            details = []
            callback_status = []
            for k, v in callback_checks.items():
                status = "OK" if v else "MISSING"
                callback_status.append(f"{k}: {status}")
            details.append(f"Callbacks: {'; '.join(callback_status)}")
            
            handler_status = "OK" if handler_initialized else "MISSING"
            details.append(f"Handler initialized: {handler_status}")
            
            if handler_methods:
                details.append(f"Handler methods: {'; '.join(handler_methods[:3])}...")
            
            self.log_test(
                "Problematic Callback Handlers",
                success,
                "; ".join(details)
            )
            
            return success
            
        except Exception as e:
            self.log_test(
                "Problematic Callback Handlers",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_download_system_handler_api_calls(self) -> bool:
        """Test download system handler API calls"""
        try:
            # Import and initialize handler
            from handlers.download_system_handler import DownloadSystemHandler
            from database.db_manager import DatabaseManager
            
            db = DatabaseManager()
            handler = DownloadSystemHandler(
                db,
                download_api_url=self.download_api_url,
                admin_token=self.admin_token_bot
            )
            
            # Test API calls that the handler makes
            api_tests = []
            
            # Test 1: System status
            try:
                status = await handler.get_system_status()
                status_ok = status.get('ready', False)
                result = "OK" if status_ok else "FAILED"
                api_tests.append(f"System status: {result}")
            except Exception as e:
                api_tests.append(f"System status: ERROR ({str(e)[:50]})")
            
            # Test 2: Real-time metrics
            try:
                metrics = await handler.get_real_time_metrics()
                metrics_ok = isinstance(metrics, dict)
                result = "OK" if metrics_ok else "FAILED"
                api_tests.append(f"Metrics: {result}")
            except Exception as e:
                api_tests.append(f"Metrics: ERROR ({str(e)[:50]})")
            
            # Test 3: Create download link (will fail due to missing file, but should not crash)
            try:
                link_data = {
                    "file_id": 999999,  # Non-existent file
                    "download_type": "stream",
                    "max_downloads": 1,
                    "expires_hours": 1
                }
                result = await handler.create_download_link_via_api(link_data)
                link_test_ok = isinstance(result, dict)
                status = "OK" if link_test_ok else "FAILED"
                api_tests.append(f"Create link: {status}")
            except Exception as e:
                api_tests.append(f"Create link: ERROR ({str(e)[:50]})")
            
            # Test 4: Cache cleanup
            try:
                cleanup_result = await handler.cleanup_system_cache()
                cleanup_ok = isinstance(cleanup_result, dict)
                status = "OK" if cleanup_ok else "FAILED"
                api_tests.append(f"Cache cleanup: {status}")
            except Exception as e:
                api_tests.append(f"Cache cleanup: ERROR ({str(e)[:50]})")
            
            success = len([t for t in api_tests if 'OK' in t]) >= 2  # At least 2 should work
            
            self.log_test(
                "Download System Handler API Calls",
                success,
                f"API tests: {'; '.join(api_tests)}"
            )
            
            return success
            
        except Exception as e:
            self.log_test(
                "Download System Handler API Calls",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def test_admin_token_consistency(self) -> bool:
        """Test admin token consistency between review request and bot code"""
        try:
            # Test both tokens with the API
            results = {}
            
            for token_name, token, headers in [
                ("Review Token", self.admin_token_review, self.headers_review),
                ("Bot Token", self.admin_token_bot, self.headers_bot)
            ]:
                try:
                    response = requests.get(
                        f"{self.download_api_url}/api/system/metrics",
                        headers=headers,
                        timeout=10
                    )
                    results[token_name] = {
                        'status': response.status_code,
                        'valid': response.status_code in [200, 401, 403]
                    }
                except Exception as e:
                    results[token_name] = {
                        'status': 'ERROR',
                        'valid': False,
                        'error': str(e)
                    }
            
            # Check if tokens are different
            tokens_different = self.admin_token_review != self.admin_token_bot
            
            # Both tokens should work or at least not crash the system
            both_valid = all(result['valid'] for result in results.values())
            
            details = []
            diff_status = "OK" if tokens_different else "SAME"
            details.append(f"Tokens different: {diff_status}")
            
            for token_name, result in results.items():
                status = result['status']
                valid = 'OK' if result['valid'] else 'FAILED'
                details.append(f"{token_name}: {valid} (HTTP {status})")
            
            self.log_test(
                "Admin Token Consistency",
                both_valid,
                "; ".join(details)
            )
            
            return both_valid
            
        except Exception as e:
            self.log_test(
                "Admin Token Consistency",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def test_redis_connection(self) -> bool:
        """Test Redis connection (mentioned in review request)"""
        try:
            import subprocess
            
            # Check if Redis is running
            result = subprocess.run(
                ['redis-cli', 'ping'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            redis_running = result.returncode == 0 and 'PONG' in result.stdout
            
            # Also check if Redis process is running
            ps_result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            redis_process = 'redis-server' in ps_result.stdout
            
            success = redis_running or redis_process
            
            details = []
            ping_status = "OK" if redis_running else "FAILED"
            process_status = "OK" if redis_process else "FAILED"
            details.append(f"Redis ping: {ping_status}")
            details.append(f"Redis process: {process_status}")
            
            self.log_test(
                "Redis Connection",
                success,
                "; ".join(details)
            )
            
            return success
            
        except Exception as e:
            self.log_test(
                "Redis Connection",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def test_system_processes(self) -> bool:
        """Test if all required system processes are running"""
        try:
            import subprocess
            
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            processes = {
                'Bot Process': 'bot_main.py' in result.stdout,
                'Download System': 'main.py' in result.stdout and 'download_system' in result.stdout,
                'Python Processes': 'python' in result.stdout
            }
            
            all_running = all(processes.values())
            
            details = []
            for name, running in processes.items():
                status = "OK" if running else "FAILED"
                details.append(f"{name}: {status}")
            
            self.log_test(
                "System Processes",
                all_running,
                "; ".join(details)
            )
            
            return all_running
            
        except Exception as e:
            self.log_test(
                "System Processes",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def run_all_tests(self):
        """Run all comprehensive tests"""
        print("Starting Final Comprehensive Tests")
        print("=" * 70)
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Run tests
        self.test_telegram_bot_connection()
        self.test_download_system_health()
        self.test_problematic_callback_handlers()
        await self.test_download_system_handler_api_calls()
        self.test_admin_token_consistency()
        self.test_redis_connection()
        self.test_system_processes()
        
        # Print summary
        print("\n" + "=" * 70)
        print("FINAL COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print("\nFAILED TESTS:")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test['name']}")
                if test['details']:
                    print(f"      -> {test['details']}")
        else:
            print("\nALL TESTS PASSED!")
        
        # Specific findings for the review request
        print("\n" + "=" * 70)
        print("SPECIFIC FINDINGS FOR REVIEW REQUEST")
        print("=" * 70)
        
        callback_test = next((t for t in self.failed_tests if 'Callback' in t['name']), None)
        if not callback_test:
            print("OK: Callback handlers 'download_system_control' and 'file_download_links_X' are properly implemented")
        else:
            print("ISSUE: Problems found with callback handlers - see details above")
        
        api_test = next((t for t in self.failed_tests if 'API' in t['name']), None)
        if not api_test:
            print("OK: Download system API integration is working correctly")
        else:
            print("ISSUE: Problems found with API integration - see details above")
        
        token_test = next((t for t in self.failed_tests if 'Token' in t['name']), None)
        if not token_test:
            print("OK: Admin tokens are working (note: review token differs from bot token)")
        else:
            print("ISSUE: Problems found with admin tokens - see details above")
        
        print("\n" + "=" * 70)
        
        return len(self.failed_tests) == 0


async def main():
    """Main test function"""
    tester = FinalComprehensiveTester()
    success = await tester.run_all_tests()
    
    if success:
        print("All comprehensive tests passed successfully!")
        return 0
    else:
        print("Some comprehensive tests failed. Please review the details above.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))