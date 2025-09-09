#!/usr/bin/env python3
"""
Development Server Quick Start Script
Handles both backend and frontend startup with proper error checking
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def check_python_deps():
    """Check if required Python packages are installed"""
    print("🔍 Checking Python dependencies...")
    
    required = ['fastapi', 'uvicorn', 'pandas', 'sqlalchemy', 'psycopg2']
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg.replace('-', '_'))
            print(f"✅ {pkg}")
        except ImportError:
            missing.append(pkg)
            print(f"❌ {pkg}")
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    
    return True

def check_node_deps():
    """Check if Node.js and npm are available"""
    print("\n🔍 Checking Node.js dependencies...")
    
    try:
        # Check Node.js
        result = subprocess.run(['node', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ Node.js: {result.stdout.strip()}")
        else:
            print("❌ Node.js not found")
            return False
            
        # Check npm
        result = subprocess.run(['npm', '--version'], 
                              capture_output=True, text=True, timeout=5, shell=True)
        if result.returncode == 0:
            print(f"✅ npm: {result.stdout.strip()}")
        else:
            print("❌ npm not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Node.js/npm check failed: {e}")
        return False

def start_backend():
    """Start the backend server"""
    print("\n🚀 Starting Backend Server...")
    
    backend_dir = Path(__file__).parent / "backend"
    
    try:
        # Start backend server
        cmd = [sys.executable, "local_server.py", "--host", "0.0.0.0", "--port", "8000"]
        
        process = subprocess.Popen(
            cmd,
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit to see if it starts successfully
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ Backend server started on http://localhost:8000")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Backend failed to start:")
            print(f"   stdout: {stdout}")
            print(f"   stderr: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        return None

def start_frontend():
    """Start the frontend server"""
    print("\n🎨 Starting Frontend Server...")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    if not frontend_dir.exists():
        print(f"❌ Frontend directory not found: {frontend_dir}")
        return None
    
    try:
        # Check if node_modules exists, install if not
        node_modules = frontend_dir / "node_modules"
        if not node_modules.exists():
            print("📦 Installing npm packages...")
            result = subprocess.run(['npm', 'install'], 
                                  cwd=frontend_dir, 
                                  capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                print(f"❌ npm install failed: {result.stderr}")
                return None
            print("✅ npm packages installed")
        
        # Start frontend
        env = os.environ.copy()
        env['BROWSER'] = 'none'  # Prevent auto-opening browser
        
        process = subprocess.Popen(
            ['npm', 'start'],
            cwd=frontend_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for frontend to start
        print("⏳ Waiting for frontend to start...")
        time.sleep(10)
        
        if process.poll() is None:
            print("✅ Frontend server started on http://localhost:3000")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Frontend failed to start:")
            print(f"   stdout: {stdout}")
            print(f"   stderr: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        return None

def main():
    """Main function"""
    print("🌊 Sea Level Dashboard - Development Startup")
    print("=" * 60)
    
    # Check dependencies
    if not check_python_deps():
        print("\n❌ Python dependencies missing. Please install them first.")
        return
    
    if not check_node_deps():
        print("\n❌ Node.js dependencies missing. Please install Node.js and npm.")
        return
    
    print("\n✅ All dependencies available!")
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        print("\n❌ Failed to start backend server")
        return
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        print("\n❌ Failed to start frontend server")
        if backend_process:
            backend_process.terminate()
        return
    
    print("\n" + "=" * 60)
    print("🎉 Both servers started successfully!")
    print("📊 Backend API: http://localhost:8000")
    print("🌐 Frontend App: http://localhost:3000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("=" * 60)
    
    # Open browser
    try:
        time.sleep(2)
        webbrowser.open("http://localhost:3000")
        print("🌐 Browser opened automatically")
    except:
        print("⚠️  Could not open browser automatically")
    
    print("\nPress Ctrl+C to stop both servers...")
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend process stopped unexpectedly")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend process stopped unexpectedly")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        
        if frontend_process:
            frontend_process.terminate()
            print("✅ Frontend server stopped")
            
        if backend_process:
            backend_process.terminate()
            print("✅ Backend server stopped")
        
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()