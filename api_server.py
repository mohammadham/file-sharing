"""
FastAPI server for file streaming and download endpoints
Integrated with UxB-File-Sharing Bot
"""
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio
from pathlib import Path
from typing import Optional
import aiofiles
import tempfile
from datetime import datetime

from telegram_downloader_integration import TelegramDownloader
from database.sqlite_database import get_file_by_link_code, get_file
from config import TEMP_PATH, CHANNEL_ID

# Create temp directory
TEMP_DIR = Path(TEMP_PATH)
TEMP_DIR.mkdir(exist_ok=True, parents=True)

app = FastAPI(title="UxB File Sharing API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Telegram Downloader
try:
    downloader = TelegramDownloader()
except Exception as e:
    print(f"Warning: Could not initialize TelegramDownloader: {e}")
    downloader = None

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "UxB File Sharing API", 
        "version": "1.0.0",
        "endpoints": {
            "stream": "/stream/{link_code}",
            "download": "/download/{link_code}",
            "file_info": "/info/{link_code}"
        }
    }

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