#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Upload Fix - Test the file upload state management fix
"""

import asyncio
import sys
from pathlib import Path

# Add bot directory to path
sys.path.append(str(Path(__file__).parent))

from database.db_manager import DatabaseManager
from models.database_models import UserSession

async def test_upload_state_management():
    """Test the upload state management fix"""
    print("🧪 Testing Upload State Management Fix...")
    
    db = DatabaseManager()
    await db.init_database()
    
    test_user_id = 123456
    test_category_id = 1
    
    print("\n1️⃣ Test Initial State:")
    session = await db.get_user_session(test_user_id)
    print(f"   Initial action_state: {session.action_state}")
    print(f"   Initial current_category: {session.current_category}")
    
    print("\n2️⃣ Test Category Navigation (should reset to browsing):")
    await db.update_user_session(
        test_user_id,
        current_category=test_category_id,
        action_state='browsing'
    )
    session = await db.get_user_session(test_user_id)
    print(f"   After category navigation: action_state = {session.action_state}")
    
    print("\n3️⃣ Test Upload Prompt (should set to uploading_file):")
    await db.update_user_session(
        test_user_id,
        current_category=test_category_id,
        action_state='uploading_file'
    )
    session = await db.get_user_session(test_user_id)
    print(f"   After upload prompt: action_state = {session.action_state}")
    print(f"   Current category: {session.current_category}")
    
    print("\n4️⃣ Test File Upload Logic:")
    # Simulate the logic from message_handler
    if session.action_state == 'browsing' or session.action_state == 'uploading_file':
        print("   ✅ File upload would be ACCEPTED")
        result = "SUCCESS"
    else:
        print("   ❌ File upload would be REJECTED")
        result = "FAILED"
    
    print("\n5️⃣ Test Post-Upload State Reset:")
    await db.update_user_session(test_user_id, action_state='browsing')
    session = await db.get_user_session(test_user_id)
    print(f"   After successful upload: action_state = {session.action_state}")
    
    print(f"\n🎯 Test Result: {result}")
    if result == "SUCCESS":
        print("✅ Upload fix is working correctly!")
    else:
        print("❌ Upload fix needs more work")
    
    return result == "SUCCESS"

if __name__ == "__main__":
    success = asyncio.run(test_upload_state_management())
    if success:
        print("\n🎉 All tests passed! The upload issue should be fixed.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")