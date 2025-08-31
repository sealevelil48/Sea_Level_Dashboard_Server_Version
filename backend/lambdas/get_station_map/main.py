import json
import logging
import sys
import os

# Add paths for shared modules
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, backend_dir)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handler(event, context):
    """Lambda handler for get_station_map"""
    try:
        # Return station coordinates using exact ITM coordinates from database locations table
        stations = [
            {"Station": "Acre", "x": 206907, "y": 758285, "longitude": 35.070281, "latitude": 32.919482, "latest_value": 0.478, "last_update": "2025-08-28 00:00"},
            {"Station": "Ashdod", "x": 166075, "y": 637753, "longitude": 34.640522, "latitude": 31.831303, "latest_value": 0.512, "last_update": "2025-08-28 00:00"},
            {"Station": "Ashkelon", "x": 158044, "y": 621218, "longitude": 34.556778, "latitude": 31.681832, "latest_value": 0.445, "last_update": "2025-08-28 00:00"},
            {"Station": "Eilat", "x": 191654, "y": 379381, "longitude": 34.917692, "latitude": 29.501767, "latest_value": 0.389, "last_update": "2025-08-28 00:00"},
            {"Station": "Haifa", "x": 199451, "y": 748207, "longitude": 34.990936, "latitude": 32.828428, "latest_value": 0.523, "last_update": "2025-08-28 00:00"},
            {"Station": "Yafo", "x": 176505, "y": 662250, "longitude": 34.74964, "latitude": 32.052552, "latest_value": 0.467, "last_update": "2025-08-28 00:00"}
        ]
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(stations)
        }
    except Exception as e:
        logger.error(f"Error in get_station_map lambda: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error"})
        }
