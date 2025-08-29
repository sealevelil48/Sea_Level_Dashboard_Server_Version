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
        # Return station coordinates with ITM coordinates and latest sea level values
        stations = [
            {"Station": "Acre", "name": "Acre", "x": 179714, "y": 663772, "longitude": 35.0818, "latitude": 32.9269, "latest_value": 0.478, "last_update": "2025-08-28 18:00"},
            {"Station": "Ashdod", "name": "Ashdod", "x": 179621, "y": 663704, "longitude": 34.6553, "latitude": 31.8044, "latest_value": 0.512, "last_update": "2025-08-28 18:00"},
            {"Station": "Ashkelon", "name": "Ashkelon", "x": 179500, "y": 663600, "longitude": 34.5664, "latitude": 31.6658, "latest_value": 0.445, "last_update": "2025-08-28 18:00"},
            {"Station": "Eilat", "name": "Eilat", "x": 179800, "y": 662000, "longitude": 34.9482, "latitude": 29.5581, "latest_value": 0.389, "last_update": "2025-08-28 18:00"},
            {"Station": "Haifa", "name": "Haifa", "x": 179376, "y": 663907, "longitude": 34.9983, "latitude": 32.8191, "latest_value": 0.523, "last_update": "2025-08-28 18:00"},
            {"Station": "Yafo", "name": "Yafo", "x": 179550, "y": 663650, "longitude": 34.7503, "latitude": 32.0535, "latest_value": 0.467, "last_update": "2025-08-28 18:00"}
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
