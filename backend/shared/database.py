# backend/shared/database.py
import os
import logging
import warnings
from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy.types import TypeDecorator, String
from sqlalchemy.exc import SAWarning
from dotenv import load_dotenv

# Suppress specific warnings about POINT type
warnings.filterwarnings("ignore", 
                       category=SAWarning, 
                       message="Did not recognize type 'point' of column 'locations'")

# Load environment variables from the correct path
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URI from environment
DB_URI = os.getenv('DB_URI')
if not DB_URI:
    logger.warning("DB_URI not set. Check .env file. Using demo mode.")
    DB_URI = None

# Create SQLAlchemy engine only if DB_URI is available
engine = None
if DB_URI:
    print(f"Connecting to database: {DB_URI[:50]}...")
    try:
        engine = create_engine(
            DB_URI, 
            pool_pre_ping=True, 
            pool_size=5, 
            max_overflow=10, 
            pool_recycle=1800,
            echo=False  # Set to True for SQL debugging
        )
        print("✅ Database engine created successfully")
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        engine = None
else:
    print("⚠️  No database URI provided - running in demo mode")

metadata = MetaData()

# Custom TypeDecorator for PostgreSQL POINT type
class PointType(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return f"{value[0]},{value[1]}" if value else None

    def process_result_value(self, value, dialect):
        return tuple(map(float, value.split(','))) if value else None

# Simple db_manager class for compatibility
class DatabaseManager:
    def __init__(self):
        self.engine = engine
        self.M = None
        self.L = None
        self.S = None
        self._redis_client = None
        self._load_tables()
    
    def _load_tables(self):
        """Load database tables"""
        try:
            self.M = Table('Monitors_info2', metadata,
                          Column('Tab_TabularTag', String),
                          autoload_with=engine,
                          extend_existing=True)
            
            self.L = Table('Locations', metadata,
                          Column('locations', PointType()),
                          Column('Station', String),
                          autoload_with=engine,
                          extend_existing=True)
            
            self.S = Table('SeaTides', metadata,
                          autoload_with=engine,
                          extend_existing=True)
            
            logger.info("✅ Database tables loaded successfully.")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            self.M = self.L = self.S = None
    
    def health_check(self):
        """Check database connectivity"""
        try:
            from sqlalchemy import text
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()  # Actually fetch the result
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_from_cache(self, key):
        """Mock cache get (no Redis in local dev)"""
        return None
    
    def set_cache(self, key, value, ttl=300):
        """Mock cache set (no Redis in local dev)"""
        pass

# Create global instances for backward compatibility
try:
    db_manager = DatabaseManager()
    M = db_manager.M
    L = db_manager.L
    S = db_manager.S
    
    print("✅ Database connection established!")
    
except Exception as e:
    logger.error(f"❌ Database setup failed: {e}")
    print(f"❌ Database error: {e}")
    db_manager = None
    M, L, S = None, None, None