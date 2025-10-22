import json
import logging
import sys
import os

# Add paths for shared modules
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, backend_dir)

try:
    from shared.database import engine, L, db_manager
    from sqlalchemy import select, text
    DATABASE_AVAILABLE = True
    print("✅ Database modules imported successfully for get_stations")
except ImportError as e:
    print(f"❌ Database import error in get_stations: {e}")
    DATABASE_AVAILABLE = False
    engine = L = db_manager = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_all_stations_from_db():
    """Get all stations using raw SQL to avoid SQLAlchemy issues"""
    if not DATABASE_AVAILABLE or not engine:
        logger.warning("Database not available")
        return ['All Stations', 'Demo Station 1', 'Demo Station 2']
    
    try:
        # FIX: Use raw SQL instead of SQLAlchemy ORM
        sql_query = text('''
            SELECT DISTINCT "Station" 
            FROM "Locations" 
            WHERE "Station" IS NOT NULL 
            ORDER BY "Station"
        ''')
        
        with engine.connect() as connection:
            result = connection.execute(sql_query)
            stations = [row[0] for row in result if row[0] is not None]
            
            if not stations:
                logger.warning("No stations found")
                return ['All Stations', 'No stations found']
            
            return ['All Stations'] + stations
            
    except Exception as e:
        logger.error(f"Database error: {e}")
        return ['All Stations', f'Error: {str(e)[:30]}']

def lambda_handler(event, context):
    """Lambda handler for get_stations"""
    try:
        stations = get_all_stations_from_db()
        logger.info(f"Returning {len(stations)} stations")
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "stations": stations,
                "count": len(stations),
                "database_available": DATABASE_AVAILABLE
            })
        }
    except Exception as e:
        logger.error(f"Error in get_stations lambda: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": f"Internal server error: {str(e)}",
                "stations": ['All Stations', 'Error Station']
            })
        }
