
import json
import logging
import sys
import os

# Add paths for shared modules
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, backend_dir)

try:
    from shared.database import engine
    from sqlalchemy import text
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"[ERROR] Database import error in get_live_data: {e}")
    DATABASE_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    """Lambda handler for get_live_data"""
    try:
        path_params = event.get('pathParameters') or {}
        station = path_params.get('station')

        if not DATABASE_AVAILABLE:
            # Demo response
            demo_data = [
                {
                    "Station": station or "Demo Station",
                    "Tab_Value_mDepthC1": 1.234,
                    "Tab_DateTime": "2024-01-01T12:00:00Z"
                }
            ]
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"station": station or 'all', "data": demo_data})
            }

        # Real database query for latest data
        try:
            if station:
                # Get latest data for specific station
                sql_query = '''
                    SELECT l."Station", m."Tab_Value_mDepthC1", m."Tab_DateTime"
                    FROM "Monitors_info2" m
                    JOIN "Locations" l ON m."Tab_TabularTag" = l."Tab_TabularTag"
                    WHERE l."Station" = :station
                    ORDER BY m."Tab_DateTime" DESC
                    LIMIT 1
                '''
                params = {'station': station}
            else:
                # Get latest data for all stations
                sql_query = '''
                    SELECT DISTINCT ON (l."Station") 
                           l."Station", m."Tab_Value_mDepthC1", m."Tab_DateTime"
                    FROM "Monitors_info2" m
                    JOIN "Locations" l ON m."Tab_TabularTag" = l."Tab_TabularTag"
                    ORDER BY l."Station", m."Tab_DateTime" DESC
                    LIMIT 10
                '''
                params = {}

            with engine.connect() as connection:
                result = connection.execute(text(sql_query), params)
                data = []
                for row in result:
                    data.append({
                        "Station": row[0],
                        "Tab_Value_mDepthC1": float(row[1]) if row[1] is not None else None,
                        "Tab_DateTime": row[2].isoformat() if row[2] else None
                    })

                return {
                    "statusCode": 200,
                    "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                    "body": json.dumps({"station": station or 'all', "data": data})
                }

        except Exception as e:
            logger.error(f"Database error in get_live_data: {e}")
            # Fallback to demo data
            demo_data = [{
                "Station": station or "Error Station",
                "Tab_Value_mDepthC1": 1.234,
                "Tab_DateTime": "2024-01-01T12:00:00Z",
                "error": str(e)
            }]
            return {
                "statusCode": 503,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"station": station or 'all', "data": demo_data, "error": "Database error"})
            }

    except Exception as e:
        logger.error(f"Error in get_live_data lambda: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error"})
        }