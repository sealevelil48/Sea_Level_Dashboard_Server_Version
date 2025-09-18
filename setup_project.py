#!/usr/bin/env python3
"""
Sea Level Monitoring System - Project Setup Script
Automated setup for development environment
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, cwd=None, check=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            check=check,
            capture_output=True,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {command}")
        print(f"Error: {e.stderr}")
        return None

def check_prerequisites():
    """Check if required tools are installed."""
    print("🔍 Checking prerequisites...")
    
    # Check Python
    try:
        python_version = subprocess.check_output([sys.executable, "--version"], text=True).strip()
        print(f"✅ {python_version}")
    except:
        print("❌ Python not found")
        return False
    
    # Check Node.js
    result = run_command("node --version", check=False)
    if result and result.returncode == 0:
        print(f"✅ Node.js {result.stdout.strip()}")
    else:
        print("❌ Node.js not found - please install Node.js 16+")
        return False
    
    # Check npm
    result = run_command("npm --version", check=False)
    if result and result.returncode == 0:
        print(f"✅ npm {result.stdout.strip()}")
    else:
        print("❌ npm not found")
        return False
    
    return True

def setup_backend():
    """Set up the backend environment."""
    print("\n🐍 Setting up backend...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return False
    
    # Create virtual environment if it doesn't exist
    venv_dir = backend_dir / "venv"
    if not venv_dir.exists():
        print("📦 Creating virtual environment...")
        result = run_command(f"{sys.executable} -m venv venv", cwd=backend_dir)
        if not result:
            return False
    
    # Determine activation script
    if os.name == 'nt':  # Windows
        activate_script = venv_dir / "Scripts" / "activate.bat"
        pip_path = venv_dir / "Scripts" / "pip.exe"
    else:  # Unix/Linux/macOS
        activate_script = venv_dir / "bin" / "activate"
        pip_path = venv_dir / "bin" / "pip"
    
    # Install requirements
    requirements_file = backend_dir / "requirements.txt"
    if requirements_file.exists():
        print("📦 Installing backend dependencies...")
        result = run_command(f"{pip_path} install -r requirements.txt", cwd=backend_dir)
        if not result:
            return False
    else:
        print("⚠️ Backend requirements.txt not found")
    
    # Copy environment file
    env_example = backend_dir / ".env.example"
    env_file = backend_dir / ".env"
    
    if env_example.exists() and not env_file.exists():
        print("📝 Creating backend .env file...")
        shutil.copy(env_example, env_file)
        print("⚠️ Please edit backend/.env with your database credentials")
    
    print("✅ Backend setup complete")
    return True

def setup_frontend():
    """Set up the frontend environment."""
    print("\n⚛️ Setting up frontend...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    # Install npm dependencies
    package_json = frontend_dir / "package.json"
    if package_json.exists():
        print("📦 Installing frontend dependencies...")
        result = run_command("npm install", cwd=frontend_dir)
        if not result:
            return False
    else:
        print("❌ Frontend package.json not found")
        return False
    
    # Copy environment file
    env_example = frontend_dir / ".env.example"
    env_file = frontend_dir / ".env"
    
    if env_example.exists() and not env_file.exists():
        print("📝 Creating frontend .env file...")
        shutil.copy(env_example, env_file)
    elif not env_file.exists():
        print("📝 Creating default frontend .env file...")
        with open(env_file, 'w') as f:
            f.write("REACT_APP_API_URL=http://localhost:8000\n")
            f.write("REACT_APP_WS_URL=ws://localhost:8000/ws\n")
    
    print("✅ Frontend setup complete")
    return True

def create_project_files():
    """Create missing project files."""
    print("\n📄 Creating project files...")
    
    # Create root .env.example if it doesn't exist
    root_env_example = Path(".env.example")
    if not root_env_example.exists():
        print("📝 Root .env.example already created")
    
    # Create requirements.txt if it doesn't exist
    root_requirements = Path("requirements.txt")
    if not root_requirements.exists():
        print("📝 Root requirements.txt already created")
    
    print("✅ Project files ready")

def display_next_steps():
    """Display next steps for the user."""
    print("\n🎉 Setup complete! Next steps:")
    print("\n1. Configure your database:")
    print("   - Edit backend/.env with your PostgreSQL credentials")
    print("   - Ensure PostgreSQL is running")
    print("\n2. Start the development servers:")
    print("   - Backend: python start_dev.py")
    print("   - Or manually:")
    print("     cd backend && python local_server.py")
    print("     cd frontend && npm start")
    print("\n3. Access the application:")
    print("   - Frontend: http://localhost:3000")
    print("   - Backend API: http://localhost:8000")
    print("   - API Docs: http://localhost:8000/docs")
    print("\n4. For production deployment:")
    print("   - See README.md for detailed instructions")

def main():
    """Main setup function."""
    print("🌊 Sea Level Monitoring System - Setup")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites check failed. Please install missing tools.")
        sys.exit(1)
    
    # Setup backend
    if not setup_backend():
        print("\n❌ Backend setup failed")
        sys.exit(1)
    
    # Setup frontend
    if not setup_frontend():
        print("\n❌ Frontend setup failed")
        sys.exit(1)
    
    # Create project files
    create_project_files()
    
    # Display next steps
    display_next_steps()
    
    print("\n✅ Project setup completed successfully!")

if __name__ == "__main__":
    main()