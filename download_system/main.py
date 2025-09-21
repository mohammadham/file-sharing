#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main entry point for Enterprise Download System
"""

import asyncio
import uvicorn
from config.settings import settings


def main():
    """Main function"""
    print(f"🚀 Starting {settings.APP_NAME} v{settings.VERSION}")
    
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        loop="asyncio"
    )


if __name__ == "__main__":
    main()