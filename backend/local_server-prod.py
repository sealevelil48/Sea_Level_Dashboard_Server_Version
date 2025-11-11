from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
from lambdas.get_stations.main import lambda_handler as get_stations
from lambdas.get_yesterday_data.main import lambda_handler as get_yesterday_data
from lambdas.get_live_data.main import lambda_handler as get_live_data
from lambdas.get_data.main import lambda_handler as get_data
from lambdas.get_predictions.main import lambda_handler as get_predictions
from lambdas.get_station_map.main import lambda_handler as get_station_map

app = FastAPI()

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://www.govmap.gov.il", "http://your-server-ip:3000", "http://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Emulate /stations endpoint
@app.get("/stations")
async def stations():
    event = {}
    response = get_stations(event, None)
    return json.loads(response["body"])

# Emulate /yesterday/{station} endpoint
@app.get("/yesterday/{station}")
async def yesterday_data(station: str):
    event = {"pathParameters": {"station": station}}
    response = get_yesterday_data(event, None)
    return json.loads(response["body"])

# Emulate /live and /live/{station} endpoint
@app.get("/live")
async def live_data(station: str = None):
    event = {"pathParameters": {"station": station}} if station else {}
    response = get_live_data(event, None)
    return json.loads(response["body"])

# Emulate /data endpoint
@app.get("/data")
async def data(station: str = None, start_date: str = None, end_date: str = None, data_source: str = "default", show_anomalies: bool = False):
    event = {
        "queryStringParameters": {
            "station": station,
            "start_date": start_date,
            "end_date": end_date,
            "data_source": data_source,
            "show_anomalies": str(show_anomalies).lower()
        }
    }
    response = get_data(event, None)
    return json.loads(response["body"])

# Emulate /data/batch endpoint for multiple stations
@app.get("/data/batch")
@app.get("/api/data/batch")
async def data_batch(stations: str = None, start_date: str = None, end_date: str = None,
                     data_source: str = "default", show_anomalies: bool = False):
    """Batch endpoint to fetch data for multiple stations in a single query"""
    from lambdas.get_data.main import lambda_handler_batch

    event = {
        "queryStringParameters": {
            "stations": stations,
            "start_date": start_date,
            "end_date": end_date,
            "data_source": data_source,
            "show_anomalies": str(show_anomalies).lower()
        }
    }
    response = lambda_handler_batch(event, None)
    return json.loads(response["body"])

# Emulate /predictions endpoint
@app.get("/predictions")
async def predictions(station: str = None, model: str = "all"):
    event = {"queryStringParameters": {"station": station, "model": model}}
    response = get_predictions(event, None)
    return json.loads(response["body"])

# Emulate /stations/map endpoint
@app.get("/stations/map")
async def station_map():
    event = {}
    response = get_station_map(event, None)
    return json.loads(response["body"])

# Emulate /mapframe endpoint (for GOVMAP)
@app.get("/mapframe")
async def mapframe():
    # Simulate the GOVMAP iframe content
    try:
        with open("mapframe.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "<html><body><h1>Map frame not available</h1></body></html>"
    except Exception as e:
        return f"<html><body><h1>Error loading map frame: {e}</h1></body></html>"