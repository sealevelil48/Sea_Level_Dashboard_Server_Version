#!/usr/bin/env python3
"""
Requirements Check Script
Verifies all dependencies and system requirements
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """Check Python version"""
    print("🐍 Python Version Check:")
    version = sys.version_info
    print(f"   Current: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print("   ✅ Python version OK")
        return True
    else:
        print("   ❌ Python 3.8+ required")
        return False

def check_backend_requirements():
    """Check backend Python requirements"""
    print("\n📦 Backend Requirements Check:")
    
    requirements_file = Path(__file__).parent / "backend" / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"   ❌ requirements.txt not found: {requirements_file}")
        return False
    
    # Read requirements
    with open(requirements_file, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    missing = []
    for req in requirements:
        # Extract package name (before ==, >=, etc.)
        package_name = req.split('==')[0].split('>=')[0].split('<=')[0].strip()
        
        try:
            # Handle special cases
            if package_name == 'psycopg2-binary':
                importlib.import_module('psycopg2')
            elif package_name == 'python-dotenv':
                importlib.import_module('dotenv')
            else:
                importlib.import_module(package_name)
            print(f"   ✅ {package_name}")
        except ImportError:
            missing.append(req)
            print(f"   ❌ {package_name}")
    
    if missing:
        print(f"\n   ⚠️  Missing packages:")
        for pkg in missing:
            print(f"      - {pkg}")
        print(f"\n   💡 Install with: pip install {' '.join(missing)}")
        return False
    
    return True

def check_frontend_requirements():
    """Check frontend Node.js requirements"""
    print("\n🌐 Frontend Requirements Check:")
    
    # Check Node.js
    try:
        result = subprocess.run(['node', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"   ✅ Node.js: {version}")
            
            # Check if version is adequate (v16+)
            version_num = int(version.replace('v', '').split('.')[0])
            if version_num < 16:
                print(f"   ⚠️  Node.js 16+ recommended (current: {version})")
        else:
            print("   ❌ Node.js not found")
            return False
    except Exception as e:
        print(f"   ❌ Node.js check failed: {e}")
        return False
    
    # Check npm
    try:
        result = subprocess.run(['npm', '--version'], 
                              capture_output=True, text=True, timeout=5, shell=True)
        if result.returncode == 0:
            print(f"   ✅ npm: {result.stdout.strip()}")
        else:
            print("   ❌ npm not found")
            return False
    except Exception as e:
        print(f"   ❌ npm check failed: {e}")
        return False
    
    # Check package.json
    frontend_dir = Path(__file__).parent / "frontend"
    package_json = frontend_dir / "package.json"
    
    if package_json.exists():
        print(f"   ✅ package.json found")
        
        # Check if node_modules exists
        node_modules = frontend_dir / "node_modules"
        if node_modules.exists():
            print(f"   ✅ node_modules installed")
        else:
            print(f"   ⚠️  node_modules not found - run 'npm install' in frontend/")
    else:
        print(f"   ❌ package.json not found: {package_json}")
        return False
    
    return True

def check_database_connection():
    """Check database connectivity"""
    print("\n🗄️  Database Connection Check:")
    
    env_file = Path(__file__).parent / "backend" / ".env"
    if not env_file.exists():
        print(f"   ❌ .env file not found: {env_file}")
        print("   💡 Create .env file with DB_URI setting")
        return False
    
    # Load environment
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
        
        db_uri = os.getenv('DB_URI')
        if db_uri:
            print(f"   ✅ DB_URI configured")
            
            # Try to connect
            try:
                from sqlalchemy import create_engine, text
                engine = create_engine(db_uri)
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                print(f"   ✅ Database connection successful")
                return True
            except Exception as e:
                print(f"   ❌ Database connection failed: {e}")
                print(f"   💡 Check if PostgreSQL is running and credentials are correct")
                return False
        else:
            print(f"   ❌ DB_URI not found in .env")
            return False
            
    except Exception as e:
        print(f"   ❌ Environment check failed: {e}")
        return False

def check_ports():
    """Check if required ports are available"""
    print("\n🔌 Port Availability Check:")
    
    import socket
    
    ports_to_check = [
        (8000, "Backend API"),
        (3000, "Frontend Dev Server"),
        (5432, "PostgreSQL Database")
    ]
    
    for port, description in ports_to_check:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"   ⚠️  Port {port} ({description}) is in use")
        else:
            print(f"   ✅ Port {port} ({description}) is available")

def main():
    """Main check function"""
    print("🌊 Sea Level Dashboard - Requirements Check")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Backend Requirements", check_backend_requirements),
        ("Frontend Requirements", check_frontend_requirements),
        ("Database Connection", check_database_connection),
        ("Port Availability", check_ports)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"   ❌ {name} check failed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("📋 Summary:")
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} - {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All checks passed! You're ready to run the application.")
        print("💡 Run: python start_dev.py")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("💡 Install missing dependencies and check configuration.")

if __name__ == "__main__":
    main()