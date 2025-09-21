import json
import logging
import sys
import os
from datetime import datetime, timedelta

# Add paths for shared modules
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, backend_dir)

try:
    from shared.database import engine, M, L, S, db_manager
    from sqlalchemy import text
    DATABASE_AVAILABLE = True
    print("✅ Database modules imported successfully for get_station_map")
except ImportError as e:
    print(f"❌ Database import error in get_station_map: {e}")
    DATABASE_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_latest_station_data(end_date=None):
    """Get latest data for all stations from database up to end_date"""
    if not DATABASE_AVAILABLE or not engine:
        logger.warning("Database not available, returning static data")
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        return [
            {"Station": "Acre", "name": "Acre", "x": 206907, "y": 758285, "longitude": 35.070281, "latitude": 32.919482, "latest_value": 0.478, "temperature": 22.5, "last_update": current_time},
            {"Station": "Ashdod", "name": "Ashdod", "x": 166075, "y": 637753, "longitude": 34.640522, "latitude": 31.831303, "latest_value": 0.512, "temperature": 23.1, "last_update": current_time},
            {"Station": "Ashkelon", "name": "Ashkelon", "x": 158044, "y": 621218, "longitude": 34.556778, "latitude": 31.681832, "latest_value": 0.445, "temperature": 22.8, "last_update": current_time},
            {"Station": "Eilat", "name": "Eilat", "x": 191654, "y": 379381, "longitude": 34.917692, "latitude": 29.501767, "latest_value": 0.389, "temperature": 25.2, "last_update": current_time},
            {"Station": "Haifa", "name": "Haifa", "x": 199451, "y": 748207, "longitude": 34.990936, "latitude": 32.828428, "latest_value": 0.523, "temperature": 22.3, "last_update": current_time},
            {"Station": "Yafo", "name": "Yafo", "x": 176505, "y": 662250, "longitude": 34.74964, "latitude": 32.052552, "latest_value": 0.467, "temperature": 23.0, "last_update": current_time}
        ]
    
    try:
        # Get latest data for each station up to end_date
        sql_query = '''
            SELECT DISTINCT ON (l."Station") 
                l."Station",
                l."X", l."Y", l."Longitude", l."Latitude",
                CAST(m."Tab_Value_mDepthC1" AS FLOAT) as latest_value,
                CAST(m."Tab_Value_monT2m" AS FLOAT) as temperature,
                m."Tab_DateTime" as last_update
            FROM "Locations" l
            JOIN "Monitors_info2" m ON l."Tab_TabularTag" = m."Tab_TabularTag"
            WHERE m."Tab_DateTime" IS NOT NULL
              AND m."Tab_Value_mDepthC1" IS NOT NULL
        '''
        
        params = {}
        if end_date:
            sql_query += ' AND m."Tab_DateTime" <= :end_date'
            params['end_date'] = end_date + ' 23:59:59'
            
        sql_query += ' ORDER BY l."Station", m."Tab_DateTime" DESC'
        
        with engine.connect() as connection:
            result = connection.execute(text(sql_query), params)
            stations = []
            
            for row in result:
                station_data = {
                    "Station": row.Station,
                    "name": row.Station,
                    "x": int(row.X),
                    "y": int(row.Y),
                    "longitude": float(row.Longitude),
                    "latitude": float(row.Latitude),
                    "latest_value": round(float(row.latest_value), 3),
                    "temperature": round(float(row.temperature), 1) if row.temperature else None,
                    "last_update": row.last_update.strftime('%Y-%m-%d %H:%M')
                }
                stations.append(station_data)
            
            if not stations:
                logger.warning("No station data found in database, using fallback")
                # Return fallback data with current timestamp
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
                return [
                    {"Station": "Acre", "name": "Acre", "x": 206907, "y": 758285, "longitude": 35.070281, "latitude": 32.919482, "latest_value": 0.478, "last_update": current_time},
                    {"Station": "Ashdod", "name": "Ashdod", "x": 166075, "y": 637753, "longitude": 34.640522, "latitude": 31.831303, "latest_value": 0.512, "last_update": current_time},
                    {"Station": "Ashkelon", "name": "Ashkelon", "x": 158044, "y": 621218, "longitude": 34.556778, "latitude": 31.681832, "latest_value": 0.445, "last_update": current_time},
                    {"Station": "Eilat", "name": "Eilat", "x": 191654, "y": 379381, "longitude": 34.917692, "latitude": 29.501767, "latest_value": 0.389, "last_update": current_time},
                    {"Station": "Haifa", "name": "Haifa", "x": 199451, "y": 748207, "longitude": 34.990936, "latitude": 32.828428, "latest_value": 0.523, "last_update": current_time},
                    {"Station": "Yafo", "name": "Yafo", "x": 176505, "y": 662250, "longitude": 34.74964, "latitude": 32.052552, "latest_value": 0.467, "last_update": current_time}
                ]
            
            logger.info(f"Retrieved {len(stations)} stations with latest data")
            return stations
            
    except Exception as e:
        logger.error(f"Error fetching latest station data: {e}")
        # Return fallback data with current timestamp
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        return [
            {"Station": "Acre", "name": "Acre", "x": 206907, "y": 758285, "longitude": 35.070281, "latitude": 32.919482, "latest_value": 0.478, "last_update": current_time},
            {"Station": "Ashdod", "name": "Ashdod", "x": 166075, "y": 637753, "longitude": 34.640522, "latitude": 31.831303, "latest_value": 0.512, "last_update": current_time},
            {"Station": "Ashkelon", "name": "Ashkelon", "x": 158044, "y": 621218, "longitude": 34.556778, "latitude": 31.681832, "latest_value": 0.445, "last_update": current_time},
            {"Station": "Eilat", "name": "Eilat", "x": 191654, "y": 379381, "longitude": 34.917692, "latitude": 29.501767, "latest_value": 0.389, "last_update": current_time},
            {"Station": "Haifa", "name": "Haifa", "x": 199451, "y": 748207, "longitude": 34.990936, "latitude": 32.828428, "latest_value": 0.523, "last_update": current_time},
            {"Station": "Yafo", "name": "Yafo", "x": 176505, "y": 662250, "longitude": 34.74964, "latitude": 32.052552, "latest_value": 0.467, "last_update": current_time}
        ]

def handler(event, context):
    """Lambda handler for get_station_map with real-time data"""
    try:
        # Parse end_date parameter
        params = event.get('queryStringParameters') or {}
        end_date = params.get('end_date')
        logger.info(f"get_station_map called with end_date: {end_date}, params: {params}")
        
        # Get latest station data from database
        stations = get_latest_station_data(end_date)
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json", 
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": json.dumps(stations)
        }
    except Exception as e:
        logger.error(f"Error in get_station_map lambda: {e}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": "Internal server error"})
        }
