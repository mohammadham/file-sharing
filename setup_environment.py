#!/usr/bin/env python3
"""
Environment setup script for UxB-File-Sharing Bot
This script sets up the environment and initializes all components
"""

import os
import sys
import asyncio
import sqlite3
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    directories = [
        "/app/data",
        "/app/temp",
        "/app/logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def setup_database():
    """Initialize SQLite database"""
    try:
        from database.sqlite_database import db
        print("✅ SQLite database initialized successfully")
        
        # Check if default categories exist
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM categories")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count > 0:
            print(f"✅ Found {count} categories in database")
        else:
            print("⚠️  No categories found - default categories will be created on first run")
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    
    return True

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        "pyrogram",
        "TgCrypto", 
        "pyromod",
        "aiohttp",
        "fastapi",
        "uvicorn",
        "requests"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.lower().replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - Not found")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install missing packages using: pip install <package_name>")
        return False
    
    print("✅ All dependencies are installed")
    return True

def setup_environment_variables():
    """Check and setup environment variables"""
    required_vars = [
        "TG_BOT_TOKEN",
        "API_ID", 
        "API_HASH",
        "CHANNEL_ID"
    ]
    
    optional_vars = {
        "USE_SQLITE": "True",
        "DATABASE_PATH": "/app/data/file_sharing_bot.db",
        "TEMP_PATH": "/app/temp",
        "PORT": "8080"
    }
    
    missing_vars = []
    
    print("📋 Checking environment variables:")
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            print(f"❌ {var} - Not set")
        else:
            print(f"✅ {var} - Set")
    
    for var, default in optional_vars.items():
        if not os.getenv(var):
            os.environ[var] = default
            print(f"⚙️  {var} - Set to default: {default}")
        else:
            print(f"✅ {var} - Set to: {os.getenv(var)}")
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set the following environment variables:")
        for var in missing_vars:
            print(f"export {var}='your_value_here'")
        return False
    
    return True

def test_telegram_uploader():
    """Test if telegram-uploader is available"""
    try:
        from telegram_uploader import create_client
        print("✅ telegram-uploader is available")
        return True
    except ImportError:
        print("⚠️  telegram-uploader not found - URL upload feature will be disabled")
        return False

async def test_api_server():
    """Test if API server can be started"""
    try:
        import uvicorn
        from api_server import app
        print("✅ API server components are available")
        return True
    except Exception as e:
        print(f"⚠️  API server test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 UxB-File-Sharing Bot Environment Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Setup steps
    steps = [
        ("Creating directories", create_directories),
        ("Checking dependencies", check_dependencies),
        ("Setting up environment variables", setup_environment_variables),
        ("Initializing database", setup_database),
        ("Testing telegram-uploader", test_telegram_uploader),
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        try:
            if asyncio.iscoroutinefunction(step_func):
                result = asyncio.run(step_func())
            else:
                result = step_func()
            
            if not result:
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ {step_name} failed: {e}")
            failed_steps.append(step_name)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Setup Summary:")
    
    if not failed_steps:
        print("✅ All setup steps completed successfully!")
        print("\n🚀 You can now start the bot using:")
        print("   python main.py")
        print("\n📖 Available commands for admins:")
        print("   /categories - Manage file categories")
        print("   /streamlink - Generate streaming links")
        print("   /category_links - Generate category-based links")
        print("   /bulk_upload - Bulk upload from URLs")
        print("   /batch - Create batch download links")
        print("   /genlink - Generate single file links")
    else:
        print(f"⚠️  Some steps failed: {', '.join(failed_steps)}")
        print("Please fix the issues and run the setup again.")
        
        if "Checking dependencies" in failed_steps:
            print("\n💡 To install dependencies:")
            print("   pip install -r requirements.txt")
        
        if "Setting up environment variables" in failed_steps:
            print("\n💡 Create a .env file or set environment variables:")
            print("   TG_BOT_TOKEN=your_bot_token")
            print("   API_ID=your_api_id") 
            print("   API_HASH=your_api_hash")
            print("   CHANNEL_ID=your_channel_id")

if __name__ == "__main__":
    main()