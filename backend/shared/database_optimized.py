# backend/shared/database.py - OPTIMIZED VERSION
import os
import logging
import warnings
import time
import json
import hashlib
from sqlalchemy import create_engine, MetaData, Table, Column, text
from sqlalchemy.types import TypeDecorator, String
from sqlalchemy.exc import SAWarning
from sqlalchemy.pool import QueuePool
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

# Redis import with fallback
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available - caching disabled")

# Database URI from environment
DB_URI = os.getenv('DB_URI')
if not DB_URI:
    logger.warning("DB_URI not set. Check .env file. Using demo mode.")
    DB_URI = None

# Custom TypeDecorator for PostgreSQL POINT type
class PointType(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return f"{value[0]},{value[1]}" if value else None

    def process_result_value(self, value, dialect):
        return tuple(map(float, value.split(','))) if value else None

# Optimized DatabaseManager class
class OptimizedDatabaseManager:
    def __init__(self):
        # Enhanced connection pool settings
        self.POOL_SIZE = 20
        self.MAX_OVERFLOW = 10
        self.POOL_TIMEOUT = 30
        self.POOL_RECYCLE = 3600
        self.POOL_PRE_PING = True
        
        # Redis settings
        self.REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
        self.REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
        self.CACHE_DEFAULT_TTL = 300
        
        self.engine = None
        self.M = None
        self.L = None
        self.S = None
        self._redis_client = None
        self._query_metrics = {
            'total_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'slow_queries': 0
        }
        
        if DB_URI:
            self._initialize_engine()
            self._initialize_redis()
            self._load_tables()
    
    def _initialize_engine(self):
        """Create optimized SQLAlchemy engine"""
        print(f"Connecting to database: {DB_URI[:50]}...")
        try:
            self.engine = create_engine(
                DB_URI,
                poolclass=QueuePool,
                pool_size=self.POOL_SIZE,
                max_overflow=self.MAX_OVERFLOW,
                pool_timeout=self.POOL_TIMEOUT,
                pool_recycle=self.POOL_RECYCLE,
                pool_pre_ping=self.POOL_PRE_PING,
                echo=False,
                connect_args={
                    'connect_timeout': 10,
                    'options': f'-c statement_timeout=30000'
                }
            )
            print("✅ OPTIMIZED Database engine created successfully")
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            self.engine = None
    
    def _initialize_redis(self):
        """Initialize Redis cache"""
        if not REDIS_AVAILABLE:
            return
            
        try:
            self._redis_client = redis.Redis(
                host=self.REDIS_HOST,
                port=self.REDIS_PORT,
                db=0,
                decode_responses=False,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            self._redis_client.ping()
            
            # Configure memory limits
            try:
                self._redis_client.config_set('maxmemory', '512mb')
                self._redis_client.config_set('maxmemory-policy', 'allkeys-lru')
            except:
                pass  # Ignore if we can't set config
            
            print("✅ Redis cache initialized")
            
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}. Continuing without cache.")
            self._redis_client = None
    
    def _load_tables(self):
        """Load database tables"""
        if not self.engine:
            return
            
        try:
            metadata = MetaData()
            
            self.M = Table('Monitors_info2', metadata,
                          Column('Tab_TabularTag', String),
                          autoload_with=self.engine,
                          extend_existing=True)
            
            self.L = Table('Locations', metadata,
                          Column('locations', PointType()),
                          Column('Station', String),
                          autoload_with=self.engine,
                          extend_existing=True)
            
            self.S = Table('SeaTides', metadata,
                          autoload_with=self.engine,
                          extend_existing=True)
            
            logger.info("✅ Database tables loaded successfully.")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            self.M = self.L = self.S = None
    
    def health_check(self):
        """Check database connectivity"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def execute_query(self, query: str, params: dict = None, use_cache: bool = True, cache_ttl: int = None):
        """Execute query with optional caching"""
        params = params or {}
        cache_ttl = cache_ttl or self.CACHE_DEFAULT_TTL
        
        # Generate cache key
        cache_key = None
        if use_cache:
            cache_data = f"{query}_{json.dumps(params, sort_keys=True)}"
            cache_key = f"query:{hashlib.md5(cache_data.encode()).hexdigest()}"
            
            # Check cache
            cached_result = self.get_from_cache(cache_key)
            if cached_result is not None:
                return cached_result
        
        # Execute query
        start_time = time.time()
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params)
                rows = result.fetchall()
                
                duration = time.time() - start_time
                self._query_metrics['total_queries'] += 1
                
                if duration > 1.0:
                    self._query_metrics['slow_queries'] += 1
                    logger.warning(f"SLOW QUERY ({duration:.2f}s): {query[:100]}")
                
                # Cache result
                if use_cache and cache_key and rows:
                    self.set_cache(cache_key, rows, cache_ttl)
                
                return rows
                
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def get_from_cache(self, key: str):
        """Get from Redis cache"""
        if not self._redis_client:
            return None
        
        try:
            cached = self._redis_client.get(key)
            if cached:
                self._query_metrics['cache_hits'] += 1
                return json.loads(cached)
            else:
                self._query_metrics['cache_misses'] += 1
                return None
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
            return None
    
    def set_cache(self, key: str, data, ttl: int = 300):
        """Set Redis cache"""
        if not self._redis_client or not data:
            return
        
        try:
            # Convert rows to JSON serializable format
            if hasattr(data[0], '_mapping'):
                json_data = json.dumps([dict(row._mapping) for row in data])
            else:
                json_data = json.dumps(data, default=str)
            
            self._redis_client.setex(key, ttl, json_data)
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")
    
    def get_metrics(self):
        """Get performance metrics"""
        metrics = dict(self._query_metrics)
        
        if self.engine:
            try:
                pool = self.engine.pool
                metrics.update({
                    'pool_size': pool.size(),
                    'checked_in': pool.checkedin(),
                    'checked_out': pool.checkedout(),
                    'overflow': pool.overflow()
                })
            except:
                pass
        
        # Calculate cache hit rate
        total_cache_requests = metrics['cache_hits'] + metrics['cache_misses']
        if total_cache_requests > 0:
            hit_rate = (metrics['cache_hits'] / total_cache_requests) * 100
            metrics['cache_hit_rate'] = f"{hit_rate:.1f}%"
        else:
            metrics['cache_hit_rate'] = "0%"
        
        return metrics

# Create global instances for backward compatibility
try:
    if DB_URI:
        db_manager = OptimizedDatabaseManager()
        engine = db_manager.engine
        M = db_manager.M
        L = db_manager.L
        S = db_manager.S
        metadata = MetaData()
        
        print("✅ OPTIMIZED Database connection established!")
    else:
        print("⚠️  No database URI provided - running in demo mode")
        db_manager = None
        engine = None
        M, L, S = None, None, None
        metadata = MetaData()
        
except Exception as e:
    logger.error(f"❌ Database setup failed: {e}")
    print(f"❌ Database error: {e}")
    db_manager = None
    engine = None
    M, L, S = None, None, None
    metadata = MetaData()