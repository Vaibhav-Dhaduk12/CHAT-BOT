#!/usr/bin/env python
"""
Start the Chatbot Web Server

This script launches the FastAPI web server for the AI chatbot interface.

Usage:
    python start_server.py
    
Then visit: http://localhost:8000

"""

import subprocess
import sys
import webbrowser
from pathlib import Path
import time

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║          🤖 Phoenix Insurance AI Chatbot - Web Interface           ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    # Check if uvicorn is installed
    try:
        import uvicorn
    except ImportError:
        print("❌ FastAPI/Uvicorn not installed. Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn"])
    
    print("""
    📚 Before running the server, make sure you've crawled your website:
    
    python run_pipeline.py \\
        --url "https://viphub.phoenixins.mu/" \\
        --chatbot-id "phoenix_insurance_bot" \\
        --max-pages 50 \\
        --max-depth 3
    
    ───────────────────────────────────────────────────────────────────
    """)
    
    print("\n🚀 Starting FastAPI server...\n")
    print("   📱 Web Interface: http://localhost:8000")
    print("   📖 API Docs:      http://localhost:8000/docs")
    print("   ⚙️  ReDoc:         http://localhost:8000/redoc")
    print("\n💡 Press Ctrl+C to stop the server\n")
    
    # Wait a moment then open browser
    time.sleep(2)
    try:
        webbrowser.open("http://localhost:8000")
    except:
        pass
    
    # Start server
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "api.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ])

if __name__ == "__main__":
    main()
