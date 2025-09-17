
"""
Web routes for File-Sharing Bot
Integrated with FastAPI server for file streaming
"""

from aiohttp import web
import json
import asyncio
import subprocess
import os
import signal
import sys
import pathlib
PARENT_PATH = pathlib.Path(__file__).parent.resolve()
if PARENT_PATH not in ["",None] :
    sys.path.append(PARENT_PATH)
    from config import TEMP_PATH, CHANNEL_ID, ADMINS, APP_PATH, DATABASE_PATH
else:
    #DATABASE_PATH = os.getenv("DATABASE_PATH", "/app/data/file_sharing_bot.db")
    APP_PATH = os.getenv("APP_PATH", "/app")

routes = web.RouteTableDef()

# Global variable to store FastAPI server process
fastapi_process = None

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response({
        "message": "UltroidOfficial File Sharing Bot",
        "version": "2.0.0",
        "features": {
            "categories": "✅ Active",
            "streaming": "✅ Active", 
            "api_server": "✅ Running on port 8000",
            "database": "SQLite"
        },
        "endpoints": {
            "api_docs": "http://localhost:8000/docs",
            "stream": "http://localhost:8000/stream/{link_code}",
            "download": "http://localhost:8000/download/{link_code}",
            "file_info": "http://localhost:8000/info/{link_code}"
        }
    })

@routes.get("/api/status")
async def api_status_handler(request):
    """Check API server status"""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8000/health') as resp:
                if resp.status == 200:
                    health_data = await resp.json()
                    return web.json_response({
                        "status": "healthy",
                        "api_server": health_data
                    })
                else:
                    return web.json_response({
                        "status": "unhealthy",
                        "error": "API server not responding"
                    }, status=503)
    except Exception as e:
        return web.json_response({
            "status": "error",
            "error": str(e)
        }, status=500)

@routes.post("/api/restart")
async def restart_api_handler(request):
    """Restart FastAPI server"""
    global fastapi_process
    
    try:
        # Stop existing process
        if fastapi_process and fastapi_process.poll() is None:
            fastapi_process.terminate()
            fastapi_process.wait()
        
        # Start new process
        fastapi_process = await start_fastapi_server()
        
        return web.json_response({
            "status": "success",
            "message": "API server restarted successfully"
        })
    except Exception as e:
        return web.json_response({
            "status": "error", 
            "error": str(e)
        }, status=500)

async def start_fastapi_server():
    """Start FastAPI server as background process"""
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "api_server:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ], 
        cwd= APP_PATH,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
        )
        
        # Give it a moment to start
        await asyncio.sleep(2)
        
        # Check if process started successfully
        if process.poll() is None:
            print("✅ FastAPI server started successfully on port 8000")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ FastAPI server failed to start: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting FastAPI server: {e}")
        return None

async def web_server():
    """Create web application with integrated FastAPI server"""
    global fastapi_process
    
    # Start FastAPI server
    print("🚀 Starting FastAPI server...")
    fastapi_process = await start_fastapi_server()
    
    # Create aiohttp app
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    
    # Add cleanup handler
    async def cleanup_handler(app):
        if fastapi_process and fastapi_process.poll() is None:
            print("🛑 Stopping FastAPI server...")
            fastapi_process.terminate()
            fastapi_process.wait()
    
    web_app.on_cleanup.append(cleanup_handler)
    
    return web_app

# Handle cleanup on exit
def signal_handler(signum, frame):
    global fastapi_process
    if fastapi_process and fastapi_process.poll() is None:
        print("🛑 Stopping FastAPI server...")
        fastapi_process.terminate()
        fastapi_process.wait()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
