#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Authentication API Routes
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer

from core.models import (
    TokenCreateRequest, TokenResponse, APIError,
    TokenType
)
from core.auth import (
    AuthManager, PermissionManager, get_auth_manager,
    get_current_token, require_permission
)

router = APIRouter()
security = HTTPBearer()


@router.post("/token/create", response_model=TokenResponse)
async def create_api_token(
    request: TokenCreateRequest,
    auth_manager: AuthManager = Depends(get_auth_manager),
    current_token = Depends(require_permission("admin.tokens"))
):
    """Create new API token"""
    
    # Validate permissions
    if not PermissionManager.validate_permissions(request.permissions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid permissions specified"
        )
    
    try:
        token_string, token = await auth_manager.create_token(
            name=request.name,
            permissions=request.permissions,
            expires_hours=request.expires_hours,
            max_usage=request.max_usage,
            token_type=TokenType.API
        )
        
        return TokenResponse(
            token_id=token.id,
            token=token_string,
            name=token.name,
            permissions=request.permissions,
            expires_at=token.expires_at,
            max_usage=token.max_usage,
            created_at=token.created_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create token: {str(e)}"
        )


@router.post("/validate")
async def validate_token(
    current_token = Depends(get_current_token),
    auth_manager: AuthManager = Depends(get_auth_manager)
):
    """Validate current token"""
    
    permissions = auth_manager.get_token_permissions(current_token)
    
    return {
        "valid": True,
        "token_id": current_token.id,
        "name": current_token.name,
        "token_type": current_token.token_type,
        "permissions": permissions,
        "usage_count": current_token.usage_count,
        "max_usage": current_token.max_usage,
        "expires_at": current_token.expires_at
    }


@router.delete("/token/{token_id}")
async def revoke_token(
    token_id: str,
    auth_manager: AuthManager = Depends(get_auth_manager),
    current_token = Depends(require_permission("admin.tokens"))
):
    """Revoke API token"""
    
    success = await auth_manager.revoke_token(token_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )
    
    return {"message": "Token revoked successfully"}


@router.get("/permissions")
async def get_available_permissions():
    """Get all available permissions"""
    
    return {
        "permissions": {
            perm: PermissionManager.get_permission_description(perm)
            for perm in PermissionManager.PERMISSIONS.keys()
        }
    }


@router.get("/permissions/defaults/{token_type}")
async def get_default_permissions(token_type: TokenType):
    """Get default permissions for token type"""
    
    return {
        "token_type": token_type,
        "default_permissions": PermissionManager.get_default_permissions(token_type)
    }