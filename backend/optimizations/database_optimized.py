"""
Production Database Configuration with Connection Pooling
==========================================================
Replaces backend/shared/database.py with optimized connection management
"""

import os
import logging
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class OptimizedDatabaseManager:
    """
    Production-ready database manager with:
    - Connection pooling
    - Query performance monitoring
    - Automatic connection recovery
    """
    
    def __init__(self):
        # Connection Pool Settings
        self.POOL_SIZE = 20              # Number of persistent connections
        self.MAX_OVERFLOW = 10           # Additional connections when pool exhausted
        self.POOL_TIMEOUT = 30           # Seconds to wait for available connection
        self.POOL_RECYCLE = 3600         # Recycle connections after 1 hour
        self.POOL_PRE_PING = True        # Test connections before using
        
        # Database Connection
        self.DATABASE_URL = os.getenv('DB_URI', 'postgresql://user:password@localhost:5432/sealevel')
        
        self._engine = None
        self._session_factory = None
        self._scoped_session = None
        self._query_metrics = {
            'total_queries': 0,
            'slow_queries': 0,
            'failed_queries': 0
        }
        
        self._initialize_engine()
        self._setup_event_listeners()
    
    def _initialize_engine(self):
        """Create SQLAlchemy engine with optimized pooling"""
        logger.info("Initializing database engine with connection pooling")
        
        self._engine = create_engine(
            self.DATABASE_URL,
            poolclass=QueuePool,
            pool_size=self.POOL_SIZE,
            max_overflow=self.MAX_OVERFLOW,
            pool_timeout=self.POOL_TIMEOUT,
            pool_recycle=self.POOL_RECYCLE,
            pool_pre_ping=self.POOL_PRE_PING,
            echo=False,
            # Connection arguments
            connect_args={
                'connect_timeout': 10,
                'options': f'-c statement_timeout=30000'
            }
        )
        
        # Create session factory
        self._session_factory = sessionmaker(
            bind=self._engine,
            autoflush=False,
            autocommit=False
        )
        
        self._scoped_session = scoped_session(self._session_factory)
        
        # Test connection
        self._test_connection()
        
        logger.info(f"Database engine initialized - Pool size: {self.POOL_SIZE}, Max overflow: {self.MAX_OVERFLOW}")
    
    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for monitoring"""
        
        @event.listens_for(self._engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
        
        @event.listens_for(self._engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, params, context, executemany):
            total_time = time.time() - conn.info['query_start_time'].pop()
            self._query_metrics['total_queries'] += 1
            
            # Log slow queries
            if total_time > 1.0:
                self._query_metrics['slow_queries'] += 1
                logger.warning(f"SLOW QUERY ({total_time:.2f}s): {statement[:200]}")
    
    def _test_connection(self):
        """Test database connectivity"""
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
            logger.info("Database connection test: SUCCESS")
        except Exception as e:
            logger.error(f"Database connection test: FAILED - {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions with automatic cleanup
        
        Usage:
            with db_manager.get_session() as session:
                result = session.execute(query)
        """
        session = self._scoped_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self._query_metrics['failed_queries'] += 1
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> list:
        """
        Execute query with connection pooling
        
        Args:
            query: SQL query string
            params: Query parameters
        
        Returns:
            List of result rows
        """
        params = params or {}
        
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text(query), params)
                rows = result.fetchall()
                return rows
                
        except Exception as e:
            self._query_metrics['failed_queries'] += 1
            logger.error(f"Query execution failed: {e}")
            raise
    
    def health_check(self):
        """Check database connectivity"""
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get query performance metrics"""
        pool_stats = {
            'pool_size': self._engine.pool.size(),
            'checked_in': self._engine.pool.checkedin(),
            'checked_out': self._engine.pool.checkedout(),
            'overflow': self._engine.pool.overflow()
        }
        
        return {
            **self._query_metrics,
            **pool_stats
        }
    
    def close(self):
        """Cleanup connections"""
        if self._scoped_session:
            self._scoped_session.remove()
        if self._engine:
            self._engine.dispose()
        logger.info("Database connections closed")

# Global instance (initialize once)
db_manager = OptimizedDatabaseManager()

# Convenience functions for backward compatibility
def get_session():
    """Get database session"""
    return db_manager.get_session()

def execute_query(query: str, params: dict = None):
    """Execute query with connection pooling"""
    return db_manager.execute_query(query, params)

def get_metrics():
    """Get performance metrics"""
    return db_manager.get_metrics()

# Legacy compatibility
engine = db_manager._engine
M = None  # Will be set by existing code
L = None  # Will be set by existing code
S = None  # Will be set by existing code