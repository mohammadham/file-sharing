#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Files API Routes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from core.models import FileInfoResponse, APIError
from core.auth import get_current_token, require_permission
from api.dependencies import get_download_manager

router = APIRouter()


@router.get("/info/{file_id}", response_model=FileInfoResponse)
async def get_file_info(
    file_id: int,
    current_token = Depends(require_permission("files.read")),
    download_manager = Depends(get_download_manager)
):
    """Get file information"""
    
    # Get file info from bot database
    file_info = await download_manager.get_file_info_from_bot_db(file_id)
    
    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FileInfoResponse(
        file_id=file_info['id'],
        file_name=file_info['file_name'],
        file_type=file_info['file_type'] or "unknown",
        file_size=file_info['file_size'] or 0,
        category_id=file_info['category_id'],
        category_name=file_info.get('category_name', 'Unknown'),
        uploaded_at=file_info['uploaded_at'],
        storage_message_id=file_info['storage_message_id']
    )


@router.get("/category/{category_id}")
async def get_category_files(
    category_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_token = Depends(require_permission("files.read"))
):
    """Get files in category"""
    
    try:
        # Connect to bot database to get files
        from pathlib import Path
        import aiosqlite
        
        bot_db_path = Path("/app/bot/bot_database.db")
        if not bot_db_path.exists():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Bot database not accessible"
            )
        
        async with aiosqlite.connect(bot_db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Get category info
            cursor = await db.execute(
                "SELECT * FROM categories WHERE id = ?", (category_id,)
            )
            category_row = await cursor.fetchone()
            
            if not category_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
            
            # Get files
            cursor = await db.execute('''
                SELECT f.*, c.name as category_name 
                FROM files f
                LEFT JOIN categories c ON f.category_id = c.id
                WHERE f.category_id = ?
                ORDER BY f.uploaded_at DESC
                LIMIT ? OFFSET ?
            ''', (category_id, limit, offset))
            
            files = await cursor.fetchall()
            
            # Get total count
            cursor = await db.execute(
                "SELECT COUNT(*) FROM files WHERE category_id = ?", (category_id,)
            )
            total_count = (await cursor.fetchone())[0]
        
        return {
            "category": {
                "id": category_row['id'],
                "name": category_row['name'],
                "description": category_row['description'] if category_row['description'] else ''
            },
            "files": [
                {
                    "file_id": file['id'],
                    "file_name": file['file_name'],
                    "file_type": file['file_type'],
                    "file_size": file['file_size'],
                    "uploaded_at": file['uploaded_at'],
                    "storage_message_id": file['storage_message_id']
                }
                for file in files
            ],
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(files) < total_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving files: {str(e)}"
        )


@router.get("/search")
async def search_files(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(default=20, ge=1, le=50),
    current_token = Depends(require_permission("files.read"))
):
    """Search files by name"""
    
    try:
        from pathlib import Path
        import aiosqlite
        
        bot_db_path = Path("/app/bot/bot_database.db")
        if not bot_db_path.exists():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Bot database not accessible"
            )
        
        async with aiosqlite.connect(bot_db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT f.*, c.name as category_name 
                FROM files f
                LEFT JOIN categories c ON f.category_id = c.id
                WHERE f.file_name LIKE ? OR f.description LIKE ?
                ORDER BY f.uploaded_at DESC
                LIMIT ?
            ''', (f'%{q}%', f'%{q}%', limit))
            
            files = await cursor.fetchall()
        
        return {
            "query": q,
            "results": [
                {
                    "file_id": file['id'],
                    "file_name": file['file_name'],
                    "file_type": file['file_type'],
                    "file_size": file['file_size'],
                    "category_name": file['category_name'],
                    "uploaded_at": file['uploaded_at'],
                    "storage_message_id": file['storage_message_id']
                }
                for file in files
            ],
            "count": len(files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching files: {str(e)}"
        )


@router.get("/categories")
async def get_categories(
    parent_id: Optional[int] = Query(default=None),
    current_token = Depends(require_permission("files.read"))
):
    """Get categories"""
    
    try:
        from pathlib import Path
        import aiosqlite
        
        bot_db_path = Path("/app/bot/bot_database.db")
        if not bot_db_path.exists():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Bot database not accessible"
            )
        
        async with aiosqlite.connect(bot_db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if parent_id is None:
                cursor = await db.execute('''
                    SELECT * FROM categories WHERE parent_id IS NULL ORDER BY name
                ''')
            else:
                cursor = await db.execute('''
                    SELECT * FROM categories WHERE parent_id = ? ORDER BY name
                ''', (parent_id,))
            
            categories = await cursor.fetchall()
        
        return {
            "parent_id": parent_id,
            "categories": [
                {
                    "id": cat['id'],
                    "name": cat['name'],
                    "description": cat['description'] if cat['description'] else '',
                    "parent_id": cat['parent_id'],
                    "created_at": cat['created_at'] if 'created_at' in cat.keys() else None
                }
                for cat in categories
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving categories: {str(e)}"
        )