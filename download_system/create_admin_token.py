#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Create initial admin token for testing
"""

import asyncio
import sys
sys.path.append('.')

from core.database import DatabaseManager
from core.auth import AuthManager, TokenType
from config.settings import settings


async def create_admin_token():
    """Create admin token"""
    
    # Initialize database
    db = DatabaseManager()
    await db.init_database()
    
    # Initialize auth manager
    auth = AuthManager(settings.SECRET_KEY, db)
    
    try:
        # Create admin token
        token_string, token = await auth.create_token(
            name="Initial Admin Token",
            permissions=["all"],  # All permissions
            token_type=TokenType.ADMIN,
            expires_hours=24*30  # 30 days
        )
        
        print(f"✅ Admin token created successfully!")
        print(f"🔑 Token: {token_string}")
        print(f"📝 Token ID: {token.id}")
        print(f"⏰ Expires: {token.expires_at}")
        print(f"\n📋 Usage:")
        print(f"   Authorization: Bearer {token_string}")
        print(f"\n🔗 Test with:")
        print(f"   curl -H 'Authorization: Bearer {token_string}' http://localhost:8001/api/auth/validate")
        
    except Exception as e:
        print(f"❌ Error creating token: {e}")


if __name__ == "__main__":
    asyncio.run(create_admin_token())