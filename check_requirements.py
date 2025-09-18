#!/usr/bin/env python3
"""
Sea Level Monitoring System - Requirements Checker
Validates system requirements and dependencies
"""

import sys
import subprocess
import importlib
import json
from pathlib import Path

def check_python_version():
    """Check Python version."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (requires 3.8+)")
        return False

def check_node_version():
    """Check Node.js version."""
    print("📦 Checking Node.js version...")
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            version_num = int(version.replace('v', '').split('.')[0])
            if version_num >= 16:
                print(f"✅ Node.js {version}")
                return True
            else:
                print(f"❌ Node.js {version} (requires 16+)")
                return False
        else:
            print("❌ Node.js not found")
            return False
    except FileNotFoundError:
        print("❌ Node.js not found")
        return False

def check_npm_version():
    """Check npm version."""
    print("📦 Checking npm version...")
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ npm {version}")
            return True
        else:
            print("❌ npm not found")
            return False
    except FileNotFoundError:
        print("❌ npm not found")
        return False

def check_python_packages():
    """Check Python package requirements."""
    print("🔍 Checking Python packages...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'pandas',
        'numpy',
        'requests',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (missing)")
            missing_packages.append(package)
    
    return len(missing_packages) == 0, missing_packages

def check_frontend_dependencies():
    """Check frontend dependencies."""
    print("🔍 Checking frontend dependencies...")
    
    frontend_dir = Path("frontend")
    package_json = frontend_dir / "package.json"
    node_modules = frontend_dir / "node_modules"
    
    if not package_json.exists():
        print("❌ Frontend package.json not found")
        return False
    
    if not node_modules.exists():
        print("❌ Frontend node_modules not found (run npm install)")
        return False
    
    try:
        with open(package_json, 'r') as f:
            package_data = json.load(f)
        
        dependencies = package_data.get('dependencies', {})
        required_deps = ['react', 'react-dom', 'bootstrap', 'plotly.js', 'axios']
        
        missing_deps = []
        for dep in required_deps:
            if dep in dependencies:
                print(f"✅ {dep}")
            else:
                print(f"❌ {dep} (missing)")
                missing_deps.append(dep)
        
        return len(missing_deps) == 0
    
    except Exception as e:
        print(f"❌ Error checking frontend dependencies: {e}")
        return False

def check_database_connection():
    """Check database connection (optional)."""
    print("🗄️ Checking database connection...")
    
    try:
        import psycopg2
        print("✅ PostgreSQL driver available")
        
        # Try to read connection string from .env
        env_file = Path("backend/.env")
        if env_file.exists():
            with open(env_file, 'r') as f:
                content = f.read()
                if 'DB_URI=' in content:
                    print("✅ Database configuration found")
                else:
                    print("⚠️ Database configuration not found in .env")
        else:
            print("⚠️ Backend .env file not found")
        
        return True
    
    except ImportError:
        print("❌ PostgreSQL driver not installed (psycopg2)")
        return False

def check_project_structure():
    """Check project structure."""
    print("📁 Checking project structure...")
    
    required_dirs = [
        "backend",
        "frontend",
        "backend/lambdas",
        "backend/shared",
        "frontend/src",
        "frontend/public"
    ]
    
    required_files = [
        "backend/local_server.py",
        "backend/requirements.txt",
        "frontend/package.json",
        "frontend/src/App.js"
    ]
    
    all_good = True
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ (missing)")
            all_good = False
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (missing)")
            all_good = False
    
    return all_good

def main():
    """Main requirements check function."""
    print("🌊 Sea Level Monitoring System - Requirements Check")
    print("=" * 60)
    
    checks = []
    
    # System requirements
    checks.append(("Python Version", check_python_version()))
    checks.append(("Node.js Version", check_node_version()))
    checks.append(("npm Version", check_npm_version()))
    
    # Project structure
    checks.append(("Project Structure", check_project_structure()))
    
    # Python packages
    python_packages_ok, missing_packages = check_python_packages()
    checks.append(("Python Packages", python_packages_ok))
    
    # Frontend dependencies
    checks.append(("Frontend Dependencies", check_frontend_dependencies()))
    
    # Database (optional)
    checks.append(("Database Setup", check_database_connection()))
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(checks)
    
    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nResult: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All requirements satisfied! You can run the application.")
        print("\nNext steps:")
        print("1. Run: python start_dev.py")
        print("2. Open: http://localhost:3000")
    else:
        print("\n⚠️ Some requirements are missing.")
        
        if not python_packages_ok and missing_packages:
            print(f"\nInstall missing Python packages:")
            print(f"pip install {' '.join(missing_packages)}")
        
        print("\nRun setup_project.py to fix common issues:")
        print("python setup_project.py")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)