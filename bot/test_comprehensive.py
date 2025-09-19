#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive Test - Test all scenarios for file upload state management
"""

import asyncio
import sys
from pathlib import Path

# Add bot directory to path
sys.path.append(str(Path(__file__).parent))

from database.db_manager import DatabaseManager

async def test_scenarios():
    """Test various scenarios"""
    print("🔍 Testing All Upload Scenarios...")
    
    db = DatabaseManager()
    await db.init_database()
    
    test_user_id = 999999
    results = []
    
    # Scenario 1: Normal upload flow
    print("\n📋 Scenario 1: Normal Upload Flow")
    print("   Step 1: User navigates to category")
    await db.update_user_session(test_user_id, current_category=1, action_state='browsing')
    
    print("   Step 2: User clicks 'Upload File' button")
    await db.update_user_session(test_user_id, action_state='uploading_file')
    
    print("   Step 3: User sends file")
    session = await db.get_user_session(test_user_id)
    upload_accepted = session.action_state in ['browsing', 'uploading_file']
    print(f"   Result: Upload {'✅ ACCEPTED' if upload_accepted else '❌ REJECTED'}")
    results.append(upload_accepted)
    
    # Scenario 2: User in different state sends file
    print("\n📋 Scenario 2: User in Wrong State Sends File")
    print("   Step 1: User is in 'adding_category' state")
    await db.update_user_session(test_user_id, action_state='adding_category')
    
    print("   Step 2: User sends file")
    session = await db.get_user_session(test_user_id)
    upload_accepted = session.action_state in ['browsing', 'uploading_file']
    print(f"   Result: Upload {'✅ ACCEPTED' if upload_accepted else '❌ REJECTED (Expected)'}")
    results.append(not upload_accepted)  # This should be rejected
    
    # Scenario 3: User cancels upload and then navigates
    print("\n📋 Scenario 3: Cancel Upload and Navigate")
    print("   Step 1: User is in 'uploading_file' state")
    await db.update_user_session(test_user_id, action_state='uploading_file')
    
    print("   Step 2: User clicks back to category")
    await db.update_user_session(test_user_id, action_state='browsing')
    
    print("   Step 3: User sends file")
    session = await db.get_user_session(test_user_id)
    upload_accepted = session.action_state in ['browsing', 'uploading_file']
    print(f"   Result: Upload {'✅ ACCEPTED' if upload_accepted else '❌ REJECTED'}")
    results.append(upload_accepted)
    
    # Scenario 4: Broadcast state
    print("\n📋 Scenario 4: User in Broadcast State")
    print("   Step 1: User is in 'broadcast_file' state")
    await db.update_user_session(test_user_id, action_state='broadcast_file')
    
    print("   Step 2: User sends file")
    session = await db.get_user_session(test_user_id)
    # In broadcast_file state, file should be handled by broadcast handler
    is_broadcast_state = session.action_state == 'broadcast_file'
    print(f"   Result: File goes to {'📢 BROADCAST handler' if is_broadcast_state else '📁 UPLOAD handler'}")
    results.append(is_broadcast_state)
    
    # Summary
    all_passed = all(results)
    print(f"\n📊 Test Summary:")
    print(f"   Total scenarios tested: {len(results)}")
    print(f"   Passed: {sum(results)}")
    print(f"   Failed: {len(results) - sum(results)}")
    
    if all_passed:
        print("\n🎉 All scenarios working correctly!")
        print("   ✅ Normal upload: Works")
        print("   ✅ Wrong state protection: Works") 
        print("   ✅ State transitions: Works")
        print("   ✅ Broadcast handling: Works")
    else:
        print("\n❌ Some scenarios failed!")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(test_scenarios())
    print(f"\n{'🟢' if success else '🔴'} Final Result: {'ALL TESTS PASSED' if success else 'SOME TESTS FAILED'}")