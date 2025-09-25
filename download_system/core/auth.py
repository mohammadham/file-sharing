#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Authentication and Authorization System
"""

import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import sys
from pathlib import Path
# Add bot directory to path
sys.path.append(str(Path(__file__).parent))
from core.models import Token, TokenType
from core.database import DatabaseManager

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthManager:
    """Authentication and authorization manager"""
    
    def __init__(self, secret_key: str, database: DatabaseManager):
        self.secret_key = secret_key
        self.db = database
        self.algorithm = "HS256"
    
    def hash_password(self, password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def generate_token_string(self) -> str:
        """Generate secure token string"""
        return secrets.token_urlsafe(32)
    
    def hash_token(self, token: str) -> str:
        """Hash token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    async def create_token(
        self,
        name: str,
        permissions: List[str],
        user_id: Optional[int] = None,
        expires_hours: Optional[int] = None,
        max_usage: Optional[int] = None,
        token_type: TokenType = TokenType.API
    ) -> tuple[str, Token]:
        """Create new API token"""
        
        # Generate token string
        token_string = self.generate_token_string()
        token_hash = self.hash_token(token_string)
        
        # Calculate expiration
        expires_at = None
        if expires_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        # Create token object
        token = Token(
            token_hash=token_hash,
            name=name,
            token_type=token_type,
            user_id=user_id,
            permissions=json.dumps(permissions),
            expires_at=expires_at,
            max_usage=max_usage,
            created_at=datetime.utcnow()
        )
        
        # Save to database
        success = await self.db.create_token(token)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create token"
            )
        
        return token_string, token
    
    async def validate_token(self, token_string: str) -> Optional[Token]:
        """Validate token and return token object"""
        if not token_string:
            return None
        
        token_hash = self.hash_token(token_string)
        token = await self.db.get_token(token_hash)
        
        if not token:
            return None
        
        # Check if token is active
        if not token.is_active:
            return None
        
        # Check expiration
        if token.expires_at and datetime.utcnow() > token.expires_at:
            return None
        
        # Check max usage
        if token.max_usage and token.usage_count >= token.max_usage:
            return None
        
        # Update usage statistics
        await self.db.update_token_usage(token_hash)
        
        return token
    
    def get_token_permissions(self, token: Token) -> List[str]:
        """Get permissions from token"""
        try:
            return json.loads(token.permissions) if token.permissions else []
        except json.JSONDecodeError:
            return []
    
    def check_permission(self, token: Token, required_permission: str) -> bool:
        """Check if token has required permission"""
        permissions = self.get_token_permissions(token)
        
        # Admin tokens have all permissions
        if token.token_type == TokenType.ADMIN:
            return True
        
        # Check specific permission
        return required_permission in permissions or "all" in permissions
    
    async def revoke_token(self, token_id: str) -> bool:
        """Revoke token"""
        return await self.db.deactivate_token(token_id)


class PermissionManager:
    """Manage permissions system"""
    
    # Available permissions
    PERMISSIONS = {
        # File operations
        "files.read": "Read file information",
        "files.download": "Download files",
        "files.upload": "Upload files",
        
        # Link operations  
        "links.create": "Create download links",
        "links.read": "View download links",
        "links.delete": "Delete download links",
        "links.stats": "View link statistics",
        
        # System operations
        "system.read": "View system information",
        "system.control": "Control system operations",
        "system.monitor": "Access monitoring data",
        
        # Admin operations
        "admin.tokens": "Manage API tokens",
        "admin.users": "Manage users",
        "admin.system": "Full system administration",
        
        # Special permissions
        "all": "All permissions (use carefully)"
    }
    
    @classmethod
    def get_default_permissions(cls, token_type: TokenType) -> List[str]:
        """Get default permissions for token type"""
        if token_type == TokenType.ADMIN:
            return ["all"]
        elif token_type == TokenType.API:
            return [
                "files.read",
                "files.download", 
                "links.create",
                "links.read",
                "links.stats"
            ]
        elif token_type == TokenType.USER:
            return [
                "files.read",
                "files.download",
                "links.read"
            ]
        else:
            return []
    
    @classmethod
    def validate_permissions(cls, permissions: List[str]) -> bool:
        """Validate that all permissions are valid"""
        return all(perm in cls.PERMISSIONS for perm in permissions)
    
    @classmethod
    def get_permission_description(cls, permission: str) -> str:
        """Get description for permission"""
        return cls.PERMISSIONS.get(permission, "Unknown permission")


# Dependency functions for FastAPI

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_auth_manager() -> AuthManager:
    """Get auth manager instance"""
    from config.settings import settings
    from core.database import DatabaseManager
    
    db = DatabaseManager()
    return AuthManager(settings.SECRET_KEY, db)

async def get_current_token(
    token_data = Depends(security),
    auth_manager: AuthManager = Depends(get_auth_manager)
) -> Token:
    """Get current valid token"""
    token_string = token_data.credentials
    
    token = await auth_manager.validate_token(token_string)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token

def require_permission(required_permission: str):
    """Create dependency that requires specific permission"""
    async def permission_checker(
        token: Token = Depends(get_current_token),
        auth_manager: AuthManager = Depends(get_auth_manager)
    ) -> Token:
        if not auth_manager.check_permission(token, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{required_permission}' required"
            )
        return token
    
    return permission_checker

# Utility functions

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    from config.settings import settings
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode JWT access token"""
    from config.settings import settings
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        return {}