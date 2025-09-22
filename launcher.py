#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 سیستم راه‌اندازی ربات تلگرام و سیستم دانلود پیشرفته
"""

import subprocess
import time
import sys
import json
from pathlib import Path

def print_banner():
    """نمایش بنر سیستم"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║             🤖 سیستم راه‌اندازی ربات تلگرام و دانلود                 ║
║                         نسخه 1.0.0                                  ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

def check_system_status():
    """بررسی وضعیت سیستم‌ها"""
    print("🔍 بررسی وضعیت سیستم‌ها...")
    
    try:
        result = subprocess.run(['supervisorctl', 'status'], 
                              capture_output=True, text=True)
        
        status_lines = result.stdout.strip().split('\n')
        services = {}
        
        for line in status_lines:
            if 'telegram_bot' in line or 'download_system' in line:
                parts = line.split()
                service_name = parts[0]
                status = parts[1]
                services[service_name] = status
        
        return services
        
    except Exception as e:
        print(f"❌ خطا در بررسی وضعیت: {e}")
        return {}

def start_services():
    """راه‌اندازی سرویس‌ها"""
    print("🚀 راه‌اندازی سرویس‌ها...")
    
    services = ['telegram_bot', 'download_system']
    
    for service in services:
        print(f"   ⚡ راه‌اندازی {service}...")
        try:
            result = subprocess.run(['supervisorctl', 'start', service], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ {service} راه‌اندازی شد")
            else:
                print(f"   ⚠️ {service} در حال اجرا است یا خطایی رخ داد")
        except Exception as e:
            print(f"   ❌ خطا در راه‌اندازی {service}: {e}")

def stop_services():
    """توقف سرویس‌ها"""
    print("🛑 توقف سرویس‌ها...")
    
    services = ['telegram_bot', 'download_system']
    
    for service in services:
        print(f"   🔴 توقف {service}...")
        try:
            result = subprocess.run(['supervisorctl', 'stop', service], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ {service} متوقف شد")
            else:
                print(f"   ⚠️ {service} در حال اجرا نیست یا خطایی رخ داد")
        except Exception as e:
            print(f"   ❌ خطا در توقف {service}: {e}")

def restart_services():
    """ری‌استارت سرویس‌ها"""
    print("🔄 ری‌استارت سرویس‌ها...")
    
    services = ['telegram_bot', 'download_system']
    
    for service in services:
        print(f"   🔄 ری‌استارت {service}...")
        try:
            result = subprocess.run(['supervisorctl', 'restart', service], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ {service} ری‌استارت شد")
            else:
                print(f"   ⚠️ خطا در ری‌استارت {service}")
        except Exception as e:
            print(f"   ❌ خطا در ری‌استارت {service}: {e}")

def show_logs(service_name=None):
    """نمایش لاگ‌ها"""
    if service_name:
        print(f"📋 نمایش لاگ {service_name}...")
        log_files = {
            'bot': '/var/log/supervisor/bot.out.log',
            'download': '/var/log/supervisor/download_system.out.log'
        }
        
        log_file = log_files.get(service_name)
        if log_file and Path(log_file).exists():
            try:
                result = subprocess.run(['tail', '-n', '20', log_file], 
                                      capture_output=True, text=True)
                print(result.stdout)
            except Exception as e:
                print(f"❌ خطا در نمایش لاگ: {e}")
        else:
            print(f"❌ فایل لاگ یافت نشد: {log_file}")
    else:
        print("📋 لاگ‌های موجود:")
        print("   • bot - لاگ ربات تلگرام")
        print("   • download - لاگ سیستم دانلود")

def test_systems():
    """تست سیستم‌ها"""
    print("🧪 تست سیستم‌ها...")
    
    # تست سیستم دانلود
    print("   🔬 تست سیستم دانلود...")
    try:
        import requests
        response = requests.get('http://localhost:8001/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ سیستم دانلود: {data.get('status', 'نامشخص')}")
        else:
            print(f"   ❌ سیستم دانلود: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ سیستم دانلود در دسترس نیست: {e}")
    
    # تست ربات تلگرام
    print("   🔬 تست ربات تلگرام...")
    status = check_system_status()
    bot_status = status.get('telegram_bot', 'UNKNOWN')
    if bot_status == 'RUNNING':
        print("   ✅ ربات تلگرام: در حال اجرا")
    else:
        print(f"   ❌ ربات تلگرام: {bot_status}")

def create_admin_token():
    """ایجاد توکن ادمین"""
    print("🔑 ایجاد توکن ادمین...")
    
    script_path = Path("/app/download_system/create_admin_token.py")
    if script_path.exists():
        try:
            result = subprocess.run(['python', str(script_path)], 
                                  capture_output=True, text=True, 
                                  cwd="/app/download_system")
            print(result.stdout)
            if result.stderr:
                print(f"⚠️ هشدار: {result.stderr}")
        except Exception as e:
            print(f"❌ خطا در ایجاد توکن: {e}")
    else:
        print("❌ فایل ایجاد توکن یافت نشد!")

def show_system_info():
    """نمایش اطلاعات سیستم"""
    print("ℹ️  اطلاعات سیستم:")
    
    # وضعیت سرویس‌ها
    services = check_system_status()
    print("\n📊 وضعیت سرویس‌ها:")
    for service, status in services.items():
        emoji = "✅" if status == "RUNNING" else "❌"
        print(f"   {emoji} {service}: {status}")
    
    # اطلاعات فایل‌ها
    print("\n📁 فایل‌های مهم:")
    important_files = [
        ("/app/bot/bot_main.py", "فایل اصلی ربات"),
        ("/app/download_system/main.py", "فایل اصلی سیستم دانلود"),
        ("/app/bot/bot_database.db", "دیتابیس ربات"),
        ("/app/download_system/download_system.db", "دیتابیس سیستم دانلود")
    ]
    
    for file_path, description in important_files:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"   ✅ {description}: {size} bytes")
        else:
            print(f"   ❌ {description}: یافت نشد")

def main():
    """تابع اصلی"""
    print_banner()
    
    if len(sys.argv) < 2:
        print("استفاده:")
        print("  python launcher.py [command]")
        print("\nدستورات موجود:")
        print("  start      - راه‌اندازی سیستم‌ها")
        print("  stop       - توقف سیستم‌ها")
        print("  restart    - ری‌استارت سیستم‌ها")
        print("  status     - نمایش وضعیت")
        print("  logs [bot|download] - نمایش لاگ‌ها")
        print("  test       - تست سیستم‌ها")
        print("  token      - ایجاد توکن ادمین")
        print("  info       - اطلاعات سیستم")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'start':
        start_services()
    elif command == 'stop':
        stop_services()
    elif command == 'restart':
        restart_services()
    elif command == 'status':
        services = check_system_status()
        print("📊 وضعیت سرویس‌ها:")
        for service, status in services.items():
            emoji = "✅" if status == "RUNNING" else "❌"
            print(f"   {emoji} {service}: {status}")
    elif command == 'logs':
        service = sys.argv[2] if len(sys.argv) > 2 else None
        show_logs(service)
    elif command == 'test':
        test_systems()
    elif command == 'token':
        create_admin_token()
    elif command == 'info':
        show_system_info()
    else:
        print(f"❌ دستور نامشخص: {command}")

if __name__ == "__main__":
    main()