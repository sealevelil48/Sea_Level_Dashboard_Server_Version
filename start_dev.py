#!/usr/bin/env python3
"""
Sea Level Monitoring System - Development Server Starter
Starts both backend and frontend development servers
"""

import os
import sys
import subprocess
import time
import threading
import webbrowser
from pathlib import Path

def run_backend():
    """Start the backend server."""
    backend_dir = Path("backend")
    
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return
    
    # Check if virtual environment exists
    venv_dir = backend_dir / "venv"
    if os.name == 'nt':  # Windows
        python_path = venv_dir / "Scripts" / "python.exe"
    else:  # Unix/Linux/macOS
        python_path = venv_dir / "bin" / "python"
    
    # Use system python if venv doesn't exist
    if not python_path.exists():
        python_path = sys.executable
        print("⚠️ Using system Python (virtual environment not found)")
    
    print("🐍 Starting backend server...")
    try:
        subprocess.run([
            str(python_path), 
            "local_server.py"
        ], cwd=backend_dir)
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")
    except Exception as e:
        print(f"❌ Backend server error: {e}")

def run_frontend():
    """Start the frontend development server."""
    frontend_dir = Path("frontend")
    
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return
    
    # Check if node_modules exists
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("📦 Installing frontend dependencies...")
        try:
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
        except subprocess.CalledProcessError:
            print("❌ Failed to install frontend dependencies")
            return
    
    print("⚛️ Starting frontend server...")
    try:
        subprocess.run(["npm", "start"], cwd=frontend_dir)
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped")
    except Exception as e:
        print(f"❌ Frontend server error: {e}")

def check_ports():
    """Check if required ports are available."""
    import socket
    
    def is_port_open(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    if is_port_open(8000):
        print("⚠️ Port 8000 is already in use (backend)")
        return False
    
    if is_port_open(3000):
        print("⚠️ Port 3000 is already in use (frontend)")
        return False
    
    return True

def open_browser():
    """Open browser after a delay."""
    time.sleep(5)  # Wait for servers to start
    try:
        webbrowser.open('http://localhost:3000')
        print("🌐 Opened browser at http://localhost:3000")
    except:
        print("🌐 Please open http://localhost:3000 in your browser")

def main():
    """Main function to start development servers."""
    print("🌊 Sea Level Monitoring System - Development Mode")
    print("=" * 55)
    
    # Check if ports are available
    if not check_ports():
        print("❌ Required ports are in use. Please stop other services.")
        sys.exit(1)
    
    # Check if environment files exist
    backend_env = Path("backend/.env")
    if not backend_env.exists():
        print("⚠️ Backend .env file not found. Run setup_project.py first.")
        print("Creating basic .env file...")
        with open(backend_env, 'w') as f:
            f.write("# Basic configuration - please update with your settings\n")
            f.write("DB_URI=postgresql://username:password@localhost:5432/sealevel_monitoring\n")
            f.write("API_HOST=0.0.0.0\n")
            f.write("API_PORT=8000\n")
            f.write("DEBUG=true\n")
    
    frontend_env = Path("frontend/.env")
    if not frontend_env.exists():
        print("⚠️ Frontend .env file not found. Creating default...")
        with open(frontend_env, 'w') as f:
            f.write("REACT_APP_API_URL=http://localhost:8000\n")
    
    print("\n🚀 Starting development servers...")
    print("📍 Backend will run on: http://localhost:8000")
    print("📍 Frontend will run on: http://localhost:3000")
    print("📍 API Documentation: http://localhost:8000/docs")
    print("\n⏹️ Press Ctrl+C to stop both servers")
    print("-" * 55)
    
    try:
        # Start browser opener in background
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Start backend in background thread
        backend_thread = threading.Thread(target=run_backend, daemon=True)
        backend_thread.start()
        
        # Give backend time to start
        time.sleep(2)
        
        # Start frontend in main thread (so Ctrl+C works)
        run_frontend()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down development servers...")
        print("✅ Development session ended")

if __name__ == "__main__":
    main()