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
        # Return actual station coordinates for Israel
        stations = [
            {"name": "Acre", "x": 35.0818, "y": 32.9269},
            {"name": "Ashdod", "x": 34.6553, "y": 31.8044},
            {"name": "Ashkelon", "x": 34.5664, "y": 31.6658},
            {"name": "Eilat", "x": 34.9482, "y": 29.5581},
            {"name": "Haifa", "x": 34.9983, "y": 32.8191},
            {"name": "Yafo", "x": 34.7503, "y": 32.0535}
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
