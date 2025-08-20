#!/usr/bin/env python3
"""
Database Connection Debug Script
Run this to test database connectivity
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_database_connection():
    print("🔍 Testing Database Connection...")
    
    try:
        from backend.shared.database import engine, db_manager
        
        if not engine:
            print("❌ Database engine not initialized")
            return False
            
        # Test connection
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Database connection successful")
            
        # Test tables
        if db_manager:
            print(f"✅ Database manager initialized")
            print(f"   - Monitors table: {'✅' if db_manager.M is not None else '❌'}")
            print(f"   - Locations table: {'✅' if db_manager.L is not None else '❌'}")
            print(f"   - SeaTides table: {'✅' if db_manager.S is not None else '❌'}")
            
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_environment():
    print("\n🔍 Testing Environment Variables...")
    
    env_file = Path(__file__).parent / "backend" / ".env"
    if env_file.exists():
        print(f"✅ .env file found: {env_file}")
        
        from dotenv import load_dotenv
        load_dotenv(env_file)
        
        db_uri = os.getenv('DB_URI')
        if db_uri:
            print(f"✅ DB_URI found: {db_uri[:50]}...")
        else:
            print("❌ DB_URI not found in .env")
    else:
        print(f"❌ .env file not found: {env_file}")

def test_dependencies():
    print("\n🔍 Testing Python Dependencies...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'pandas', 'sqlalchemy', 
        'psycopg2', 'python-dotenv', 'redis'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Missing")

if __name__ == "__main__":
    print("🌊 Sea Level Dashboard - Debug Script")
    print("=" * 50)
    
    test_environment()
    test_dependencies()
    test_database_connection()
    
    print("\n" + "=" * 50)
    print("Debug complete. Check results above.")