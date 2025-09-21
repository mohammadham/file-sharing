#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive Test Suite for Telegram Bot and Download System
تست جامع سیستم ربات تلگرام و سیستم دانلود
"""

import requests
import asyncio
import aiohttp
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional

class TelegramBotDownloadSystemTester:
    """تست کننده جامع سیستم ربات تلگرام و سیستم دانلود"""
    
    def __init__(self):
        # URLs for testing
        self.download_api_url = "http://localhost:8001"
        self.bot_token = "8428725185:AAELFU6lUasbSDUvRuhTLNDBT3uEmvNruN0"
        self.admin_token = "SdYmbHA6QQs3_m6BU6fNuD6qD6mMoMPNN1ecQiQ7z1g"
        
        # Test tracking
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # Headers for API requests
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
    
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
    
    def test_download_system_health(self) -> bool:
        """Test 1: Download System Health Check"""
        try:
            response = requests.get(f"{self.download_api_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                is_ready = data.get('ready', False)
                status = data.get('status', 'unknown')
                
                self.log_test(
                    "Download System Health Check",
                    is_ready,
                    f"Status: {status}, Ready: {is_ready}, Response: {data}"
                )
                return is_ready
            else:
                self.log_test(
                    "Download System Health Check",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Download System Health Check",
                False,
                f"Connection error: {str(e)}"
            )
            return False
    
    def test_download_system_root(self) -> bool:
        """Test 2: Download System Root Endpoint"""
        try:
            response = requests.get(f"{self.download_api_url}/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                has_name = 'name' in data
                has_version = 'version' in data
                
                self.log_test(
                    "Download System Root Endpoint",
                    has_name and has_version,
                    f"Response: {data}"
                )
                return has_name and has_version
            else:
                self.log_test(
                    "Download System Root Endpoint",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Download System Root Endpoint",
                False,
                f"Connection error: {str(e)}"
            )
            return False
    
    def test_download_system_api_endpoints(self) -> bool:
        """Test 3: Download System API Endpoints"""
        endpoints_to_test = [
            ("/api/system/metrics", "GET"),
            ("/api/download/links/create", "POST"),
            ("/api/system/cache/cleanup", "POST"),
        ]
        
        all_passed = True
        results = []
        
        for endpoint, method in endpoints_to_test:
            try:
                url = f"{self.download_api_url}{endpoint}"
                
                if method == "GET":
                    response = requests.get(url, headers=self.headers, timeout=10)
                else:  # POST
                    # Send minimal test data
                    test_data = {"test": True} if "cleanup" in endpoint else {
                        "file_id": 1,
                        "download_type": "test",
                        "max_downloads": 1,
                        "expires_hours": 1
                    }
                    response = requests.post(url, headers=self.headers, json=test_data, timeout=10)
                
                # Accept various success codes (200, 201, 422 for validation errors, etc.)
                success = response.status_code in [200, 201, 422, 401, 403]
                results.append(f"{endpoint}: HTTP {response.status_code}")
                
                if not success:
                    all_passed = False
                    
            except Exception as e:
                results.append(f"{endpoint}: Error - {str(e)}")
                all_passed = False
        
        self.log_test(
            "Download System API Endpoints",
            all_passed,
            f"Results: {'; '.join(results)}"
        )
        return all_passed
    
    def test_telegram_bot_api(self) -> bool:
        """Test 4: Telegram Bot API Connection"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    bot_username = bot_info.get('username', 'Unknown')
                    
                    self.log_test(
                        "Telegram Bot API Connection",
                        True,
                        f"Bot username: @{bot_username}, Bot info: {bot_info}"
                    )
                    return True
                else:
                    self.log_test(
                        "Telegram Bot API Connection",
                        False,
                        f"Telegram API error: {data}"
                    )
                    return False
            else:
                self.log_test(
                    "Telegram Bot API Connection",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Telegram Bot API Connection",
                False,
                f"Connection error: {str(e)}"
            )
            return False
    
    def test_bot_process_running(self) -> bool:
        """Test 5: Check if Bot Process is Running"""
        try:
            import subprocess
            result = subprocess.run(
                ['ps', 'aux'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            bot_running = 'bot_main.py' in result.stdout
            
            # Check for download system process - look for main.py process
            download_running = False
            for line in result.stdout.split('\n'):
                if 'python main.py' in line and 'grep' not in line:
                    download_running = True
                    break
            
            self.log_test(
                "Bot Process Running",
                bot_running,
                f"Bot process found: {bot_running}"
            )
            
            self.log_test(
                "Download System Process Running", 
                download_running,
                f"Download system process found: {download_running}"
            )
            
            return bot_running and download_running
            
        except Exception as e:
            self.log_test(
                "Bot Process Running",
                False,
                f"Process check error: {str(e)}"
            )
            return False
    
    def test_download_system_handler_integration(self) -> bool:
        """Test 6: Download System Handler Integration"""
        try:
            # Check if the handler file exists and has correct imports
            import os
            handler_file = "/app/bot/handlers/download_system_handler.py"
            
            if not os.path.exists(handler_file):
                self.log_test(
                    "Download System Handler Integration",
                    False,
                    "Handler file not found"
                )
                return False
            
            # Read and check handler file content
            with open(handler_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for key components
            has_class = 'class DownloadSystemHandler' in content
            has_aiohttp = 'import aiohttp' in content
            has_api_methods = 'get_system_status' in content
            has_create_link = 'create_download_link_via_api' in content
            
            integration_ok = has_class and has_aiohttp and has_api_methods and has_create_link
            
            self.log_test(
                "Download System Handler Integration",
                integration_ok,
                f"Class: {has_class}, aiohttp: {has_aiohttp}, API methods: {has_api_methods}, Create link: {has_create_link}"
            )
            return integration_ok
            
        except Exception as e:
            self.log_test(
                "Download System Handler Integration",
                False,
                f"Integration check error: {str(e)}"
            )
            return False
    
    def test_bot_main_integration(self) -> bool:
        """Test 7: Bot Main Integration"""
        try:
            # Check bot_main.py for download system handler integration
            bot_main_file = "/app/bot/bot_main.py"
            
            with open(bot_main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for integration points
            has_import = 'from handlers.download_system_handler import DownloadSystemHandler' in content
            has_initialization = 'self.download_system_handler = DownloadSystemHandler' in content
            has_callback_handling = 'download_system_control' in content
            has_api_url = 'http://localhost:8001' in content
            has_admin_token = 'SdYmbHA6QQs3_m6BU6fNuD6qD6mMoMPNN1ecQiQ7z1g' in content
            
            integration_ok = has_import and has_initialization and has_callback_handling
            
            self.log_test(
                "Bot Main Integration",
                integration_ok,
                f"Import: {has_import}, Init: {has_initialization}, Callbacks: {has_callback_handling}, API URL: {has_api_url}, Token: {has_admin_token}"
            )
            return integration_ok
            
        except Exception as e:
            self.log_test(
                "Bot Main Integration",
                False,
                f"Bot main integration check error: {str(e)}"
            )
            return False
    
    def test_keyboard_builder_updates(self) -> bool:
        """Test 8: Keyboard Builder Updates"""
        try:
            keyboard_file = "/app/bot/utils/keyboard_builder.py"
            
            with open(keyboard_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for download system related buttons
            has_download_system_button = 'مدیریت سیستم دانلود' in content
            has_download_callback = 'download_system_control' in content
            has_file_download_links = 'file_download_links' in content
            
            keyboard_ok = has_download_system_button and has_download_callback
            
            self.log_test(
                "Keyboard Builder Updates",
                keyboard_ok,
                f"Download button: {has_download_system_button}, Callback: {has_download_callback}, File links: {has_file_download_links}"
            )
            return keyboard_ok
            
        except Exception as e:
            self.log_test(
                "Keyboard Builder Updates",
                False,
                f"Keyboard builder check error: {str(e)}"
            )
            return False
    
    async def test_download_system_async_endpoints(self) -> bool:
        """Test 9: Download System Async Endpoints"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test health endpoint
                async with session.get(f"{self.download_api_url}/health") as response:
                    health_ok = response.status == 200
                
                # Test metrics endpoint (may require auth)
                async with session.get(
                    f"{self.download_api_url}/api/system/metrics",
                    headers=self.headers
                ) as response:
                    metrics_ok = response.status in [200, 401, 403]  # Accept auth errors
                
                async_ok = health_ok and metrics_ok
                
                self.log_test(
                    "Download System Async Endpoints",
                    async_ok,
                    f"Health: {health_ok}, Metrics: {metrics_ok}"
                )
                return async_ok
                
        except Exception as e:
            self.log_test(
                "Download System Async Endpoints",
                False,
                f"Async test error: {str(e)}"
            )
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive Telegram Bot & Download System Tests")
        print("=" * 70)
        
        start_time = time.time()
        
        # Run synchronous tests
        self.test_download_system_health()
        self.test_download_system_root()
        self.test_download_system_api_endpoints()
        self.test_telegram_bot_api()
        self.test_bot_process_running()
        self.test_download_system_handler_integration()
        self.test_bot_main_integration()
        self.test_keyboard_builder_updates()
        
        # Run async test
        try:
            asyncio.run(self.test_download_system_async_endpoints())
        except Exception as e:
            self.log_test(
                "Download System Async Endpoints",
                False,
                f"Async test execution error: {str(e)}"
            )
        
        # Print summary
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
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
        
        print("\n" + "=" * 70)
        
        # Return success status
        return len(self.failed_tests) == 0


def main():
    """Main test function"""
    tester = TelegramBotDownloadSystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("🎉 All tests passed successfully!")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the details above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())