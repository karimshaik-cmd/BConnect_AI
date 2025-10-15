#!/usr/bin/env python3
"""
Banking Chatbot - Single Production Server Launcher
This script builds the frontend and starts the combined server.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command, cwd=None, description=""):
    """Run a command and return success status."""
    print(f"🔄 {description}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    """Main launcher function."""
    print("🚀 Starting Banking Chatbot Production Server")
    print("=" * 50)

    # Get project root directory
    project_root = Path(__file__).parent

    # Step 1: Build frontend
    frontend_dir = project_root / "frontend"
    if not run_command("npm run build", cwd=frontend_dir, description="Building frontend"):
        print("❌ Frontend build failed. Exiting.")
        sys.exit(1)

    # Step 2: Start backend server
    backend_dir = project_root / "backend"
    print("🔄 Starting backend server...")
    print("📡 Server will be available at: http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)

    try:
        # Change to backend directory and run server
        os.chdir(backend_dir)
        subprocess.run([sys.executable, "server.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
