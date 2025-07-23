#!/usr/bin/env python3
"""
Startup script for the Property Management Voice Assistant.
Handles both development and production environments.
"""

import os
import sys
import uvicorn

def main():
    """Start the FastAPI application with uvicorn."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    
    # Check if we're in development mode
    debug = os.getenv("DEBUG", "False").lower() == "true"
    reload = debug or "--reload" in sys.argv
    
    print(f"Starting Property Management Voice Assistant on {host}:{port}")
    print(f"Debug mode: {debug}, Auto-reload: {reload}")
    
    # Start the uvicorn server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()