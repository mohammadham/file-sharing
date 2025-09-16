"""
FastAPI server for file streaming and download endpoints
Integrated with File-Sharing Bot with Admin Panel Support
"""
from fastapi import FastAPI, HTTPException, Response, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
import aiofiles
import tempfile
from datetime import datetime
import uuid
import requests
import mimetypes

from telegram_downloader_integration import TelegramDownloader
from database.sqlite_database import (
    get_file_by_link_code, get_file, add_file, create_file_link,
    get_files_by_category, get_categories, create_category, delete_category,
    full_userbase, del_user, present_user
)
from config import TEMP_PATH, CHANNEL_ID, ADMINS

# Create temp directory
TEMP_DIR = Path(TEMP_PATH)
TEMP_DIR.mkdir(exist_ok=True, parents=True)

app = FastAPI(title="UxB File Sharing API", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for admin panel
try:
    app.mount("/admin", StaticFiles(directory="/app/web_admin", html=True), name="admin")
except:
    print("Warning: Could not mount admin static files")

# Mount mini app static files
try:
    app.mount("/miniapp", StaticFiles(directory="/app/telegram_miniapp", html=True), name="miniapp")
except:
    print("Warning: Could not mount miniapp static files")

# Initialize Telegram Downloader
try:
    downloader = TelegramDownloader()
except Exception as e:
    print(f"Warning: Could not initialize TelegramDownloader: {e}")
    downloader = None

# Admin authentication middleware
def verify_admin(user_id: int = 0):
    """Simple admin verification - in production use proper authentication"""
    if user_id not in ADMINS and user_id != 0:  # 0 for development
        raise HTTPException(status_code=403, detail="Access denied")
    return True

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "UxB File Sharing API", 
        "version": "2.0.0",
        "endpoints": {
            "stream": "/stream/{link_code}",
            "download": "/download/{link_code}",
            "file_info": "/info/{link_code}",
            "admin_panel": "/admin/",
            "api_docs": "/docs"
        }
    }

# Redirect to admin panel
@app.get("/admin/")
async def admin_panel():
    """Serve admin panel"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="0; url=/admin/admin_panel.html">
        <title>Redirecting to Admin Panel</title>
    </head>
    <body>
        <p>Redirecting to admin panel...</p>
    </body>
    </html>
    """)

# ===================
# ADMIN API ENDPOINTS
# ===================

@app.get("/api/admin/stats")
async def get_admin_stats():
    """Get dashboard statistics"""
    try:
        # Count files
        files = await get_files_by_category(None)
        total_files = len(files)
        
        # Count users
        users = await full_userbase()
        total_users = len(users)
        
        # Calculate total size
        total_size = sum(file.get('file_size', 0) for file in files)
        
        # Mock download count - replace with real data
        total_downloads = sum(file.get('download_count', 0) for file in files)
        
        return {
            "total_files": total_files,
            "total_users": total_users,
            "total_downloads": total_downloads,
            "total_size": total_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/recent-activities")
async def get_recent_activities():
    """Get recent activities for dashboard"""
    # Mock data - replace with real activity logging
    activities = [
        {
            "type": "فایل جدید",
            "description": "فایل example.pdf آپلود شد",
            "timestamp": datetime.now().isoformat()
        },
        {
            "type": "کاربر جدید", 
            "description": "کاربر جدید عضو شد",
            "timestamp": datetime.now().isoformat()
        }
    ]
    return activities

@app.get("/api/admin/files")
async def get_admin_files():
    """Get all files for admin management"""
    try:
        files = await get_files_by_category(None)
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/files/{file_id}")
async def delete_admin_file(file_id: str, admin: bool = Depends(verify_admin)):
    """Delete a file"""
    try:
        file_info = await get_file(file_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Here you would implement file deletion logic
        # For now, just return success
        return {"message": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/files/{file_id}/links")
async def generate_admin_links(file_id: str, admin: bool = Depends(verify_admin)):
    """Generate download links for a file"""
    try:
        file_info = await get_file(file_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Generate new links
        stream_code = str(uuid.uuid4())
        download_code = str(uuid.uuid4())
        
        await create_file_link(file_id, "stream", stream_code)
        await create_file_link(file_id, "download", download_code)
        
        return {
            "stream_link": f"http://localhost:8000/stream/{stream_code}",
            "download_link": f"http://localhost:8000/download/{download_code}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/categories")
async def get_admin_categories():
    """Get all categories"""
    try:
        categories = await get_categories()
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/categories")
async def create_admin_category(
    name: str = Form(...),
    description: str = Form(""),
    parent_id: Optional[str] = Form(None),
    admin: bool = Depends(verify_admin)
):
    """Create a new category"""
    try:
        category_id = await create_category(
            name=name,
            description=description,
            parent_id=parent_id,
            created_by=1  # Admin user ID
        )
        return {"id": category_id, "message": "Category created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/categories/{category_id}")
async def delete_admin_category(category_id: str, admin: bool = Depends(verify_admin)):
    """Delete a category"""
    try:
        await delete_category(category_id)
        return {"message": "Category deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/users")
async def get_admin_users():
    """Get all users"""
    try:
        user_ids = await full_userbase()
        users = []
        for user_id in user_ids:
            users.append({
                "id": user_id,
                "is_verified": True,  # Mock data
                "created_at": datetime.now().isoformat()
            })
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/users/{user_id}")
async def delete_admin_user(user_id: int, admin: bool = Depends(verify_admin)):
    """Delete a user"""
    try:
        await del_user(user_id)
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/upload-file")
async def upload_file_admin(
    file: UploadFile = File(...),
    category_id: Optional[str] = Form(None),
    description: str = Form(""),
    admin: bool = Depends(verify_admin)
):
    """Upload file via admin panel"""
    try:
        # Save uploaded file temporarily
        temp_path = TEMP_DIR / f"{uuid.uuid4()}_{file.filename}"
        
        async with aiofiles.open(temp_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Get file info
        file_size = len(content)
        mime_type = mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
        
        # Upload to Telegram (simplified - you'd implement actual Telegram upload)
        message_id = 12345  # Mock message ID
        chat_id = str(CHANNEL_ID)
        
        # Add to database
        file_id = await add_file(
            original_name=file.filename,
            file_name=file.filename,
            message_id=message_id,
            chat_id=chat_id,
            file_size=file_size,
            mime_type=mime_type,
            category_id=category_id,
            description=description,
            uploaded_by=1
        )
        
        # Clean up temp file
        temp_path.unlink()
        
        return {"id": file_id, "message": "File uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/upload-url")
async def upload_url_admin(
    url: str = Form(...),
    category_id: Optional[str] = Form(None),
    description: str = Form(""),
    admin: bool = Depends(verify_admin)
):
    """Upload file from URL via admin panel"""
    try:
        # Download file from URL
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Extract filename from URL or generate one
        filename = url.split('/')[-1] or f"file_{int(datetime.now().timestamp())}"
        temp_path = TEMP_DIR / f"{uuid.uuid4()}_{filename}"
        
        # Save downloaded file
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Get file info
        file_size = temp_path.stat().st_size
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        
        # Upload to Telegram (simplified)
        message_id = 12346  # Mock message ID
        chat_id = str(CHANNEL_ID)
        
        # Add to database
        file_id = await add_file(
            original_name=filename,
            file_name=filename,
            message_id=message_id,
            chat_id=chat_id,
            file_size=file_size,
            mime_type=mime_type,
            category_id=category_id,
            description=description,
            uploaded_by=1
        )
        
        # Clean up temp file
        temp_path.unlink()
        
        return {"id": file_id, "message": "File uploaded from URL successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/logs")
async def get_admin_logs():
    """Get system logs"""
    try:
        log_file = "/app/codeflixbots.txt"
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                # Get last 100 lines
                lines = f.readlines()
                return ''.join(lines[-100:])
        return "No logs found"
    except Exception as e:
        return f"Error reading logs: {str(e)}"

@app.get("/stream/{link_code}")
async def stream_file(link_code: str):
    """
    Stream file directly from Telegram without saving to server
    This is the direct/stream download method
    """
    if not downloader:
        raise HTTPException(status_code=503, detail="Telegram downloader not available")
    
    # Get file info from database
    file_info = await get_file_by_link_code(link_code)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found or link expired")
    
    # Check if link is expired
    if file_info['expires_at']:
        expires_at = datetime.fromisoformat(file_info['expires_at'])
        if datetime.now() > expires_at:
            raise HTTPException(status_code=410, detail="Download link has expired")
    
    # Check download limit
    if file_info['max_downloads'] > 0 and file_info['download_count'] >= file_info['max_downloads']:
        raise HTTPException(status_code=429, detail="Download limit exceeded")
    
    try:
        # Get file stream from Telegram
        chat_id = file_info['chat_id']
        message_id = file_info['message_id']
        
        # Create streaming generator
        async def file_stream():
            try:
                async for chunk in downloader.stream_telegram_file(chat_id, message_id):
                    yield chunk
            except Exception as e:
                print(f"Streaming error: {e}")
                raise HTTPException(status_code=500, detail="Error streaming file")
        
        # Set appropriate headers
        headers = {
            'Content-Disposition': f'attachment; filename="{file_info["original_name"]}"',
            'Content-Type': file_info['mime_type'] or 'application/octet-stream',
        }
        
        if file_info['file_size'] > 0:
            headers['Content-Length'] = str(file_info['file_size'])
        
        return StreamingResponse(
            file_stream(),
            media_type=file_info['mime_type'] or 'application/octet-stream',
            headers=headers
        )
        
    except Exception as e:
        print(f"Stream error: {e}")
        raise HTTPException(status_code=500, detail="Error streaming file from Telegram")

@app.get("/download/{link_code}")
async def download_file(link_code: str):
    """
    Download file by first saving to server then serving
    This is the indirect download method
    """
    if not downloader:
        raise HTTPException(status_code=503, detail="Telegram downloader not available")
    
    # Get file info from database
    file_info = await get_file_by_link_code(link_code)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found or link expired")
    
    # Check if link is expired
    if file_info['expires_at']:
        expires_at = datetime.fromisoformat(file_info['expires_at'])
        if datetime.now() > expires_at:
            raise HTTPException(status_code=410, detail="Download link has expired")
    
    # Check download limit
    if file_info['max_downloads'] > 0 and file_info['download_count'] >= file_info['max_downloads']:
        raise HTTPException(status_code=429, detail="Download limit exceeded")
    
    try:
        # Download file to temporary location
        chat_id = file_info['chat_id']
        message_id = file_info['message_id']
        
        # Create unique temp file path
        temp_filename = f"{link_code}_{file_info['original_name']}"
        temp_path = TEMP_DIR / temp_filename
        
        # Check if file already exists in temp
        if not temp_path.exists():
            # Download from Telegram
            download_results = downloader.download_by_message_ids(
                entity=chat_id,
                message_ids=[message_id],
                output_dir=str(TEMP_DIR),
                overwrite=True
            )
            
            if not download_results or "error" in download_results[0]:
                raise HTTPException(status_code=500, detail="Failed to download file from Telegram")
        
        # Serve the downloaded file
        if temp_path.exists():
            return FileResponse(
                path=str(temp_path),
                filename=file_info['original_name'],
                media_type=file_info['mime_type'] or 'application/octet-stream'
            )
        else:
            raise HTTPException(status_code=500, detail="File download failed")
            
    except Exception as e:
        print(f"Download error: {e}")
        raise HTTPException(status_code=500, detail="Error downloading file")

@app.get("/info/{link_code}")
async def get_file_info(link_code: str):
    """
    Get file information without downloading
    """
    file_info = await get_file_by_link_code(link_code)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found or link expired")
    
    # Check if link is expired
    if file_info['expires_at']:
        expires_at = datetime.fromisoformat(file_info['expires_at'])
        if datetime.now() > expires_at:
            raise HTTPException(status_code=410, detail="Download link has expired")
    
    return {
        "file_name": file_info['original_name'],
        "file_size": file_info['file_size'],
        "mime_type": file_info['mime_type'],
        "description": file_info['description'],
        "created_at": file_info['created_at'],
        "download_count": file_info['download_count'],
        "max_downloads": file_info['max_downloads'],
        "link_type": file_info['link_type']
    }

@app.delete("/temp/{filename}")
async def cleanup_temp_file(filename: str):
    """
    Clean up temporary files (admin only)
    """
    temp_path = TEMP_DIR / filename
    if temp_path.exists():
        temp_path.unlink()
        return {"message": "File deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.get("/temp/cleanup")
async def cleanup_old_temp_files(max_age_hours: int = 24):
    """
    Clean up old temporary files
    """
    import time
    current_time = time.time()
    deleted_count = 0
    
    for temp_file in TEMP_DIR.iterdir():
        if temp_file.is_file():
            file_age = current_time - temp_file.stat().st_mtime
            if file_age > (max_age_hours * 3600):  # Convert hours to seconds
                temp_file.unlink()
                deleted_count += 1
    
    return {"message": f"Deleted {deleted_count} old temporary files"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "telegram_downloader": "available" if downloader else "unavailable"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)