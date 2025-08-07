#!/usr/bin/env python3
"""
Simple startup script for A2A Platform.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Main startup function."""
    try:
        # Import and run the app
        from simple_app import app, settings
        import uvicorn
        
        print("=" * 60)
        print("🚀 JEECG A2A Platform - Simplified Version")
        print(f"📍 Server: {settings.HOST}:{settings.PORT}")
        print(f"🔗 Web Interface: http://{settings.HOST}:{settings.PORT}")
        print(f"🔗 Health Check: http://{settings.HOST}:{settings.PORT}/health")
        print(f"🔗 API Docs: http://{settings.HOST}:{settings.PORT}/docs")
        print("=" * 60)
        
        # Start server
        uvicorn.run(
            app,
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.RELOAD,
            log_level=settings.LOG_LEVEL.lower(),
            access_log=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
