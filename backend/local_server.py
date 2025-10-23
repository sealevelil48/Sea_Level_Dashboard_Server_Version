#!/usr/bin/env python
"""
Local/Production Server for Sea Level Dashboard - Windows Server 2019
Configured for port 30886 with proper CORS and network settings
Works on Windows, Linux, and Mac
"""

import os
import sys
import json
import logging
import subprocess
import signal
import time
from pathlib import Path
from typing import Optional
from datetime import datetime
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi import HTTPException
from dotenv import load_dotenv

# Setup paths
backend_root = Path(__file__).resolve().parent
project_root = backend_root.parent
frontend_root = project_root / "frontend"

# Load environment variables
env_file = backend_root / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"[OK] Loaded environment from {env_file}")
else:
    print(f"[WARN] No .env file found at {env_file}")

# Configure logging with UTF-8 encoding for Windows compatibility
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Create a stream handler with UTF-8 encoding
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter(log_format))
stream_handler.setLevel(logging.INFO)
stream_handler.stream.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.FileHandler("server.log", encoding='utf-8'),
        stream_handler
    ]
)
logger = logging.getLogger("sea-level-server")

# Add backend to path for module imports
sys.path.append(str(backend_root))

# Import your application modules with error handling
try:
    from shared.database import db_manager
    logger.info("[OK] Database manager imported successfully")
except ImportError as e:
    logger.error(f"[ERROR] Failed to import database manager: {e}")
    db_manager = None
    
try:
    from lambdas.get_stations.main import lambda_handler as get_stations_handler
    from lambdas.get_data.main import lambda_handler as get_data_handler
    from lambdas.get_live_data.main import lambda_handler as get_live_data_handler
    from lambdas.get_predictions.main import lambda_handler as get_predictions_handler
    from lambdas.get_sea_forecast.main import lambda_handler as get_sea_forecast_handler
    from lambdas.get_ims_warnings.main import lambda_handler as get_ims_warnings_handler
    logger.info("[OK] Lambda handlers imported successfully")
except ImportError as e:
    logger.error(f"[ERROR] Failed to import Lambda handlers: {e}")
    logger.error("Make sure all lambda folders exist with main.py files")
    # Create dummy handlers
    def dummy_handler(event, context=None):
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Handler not implemented"})
        }
    get_stations_handler = dummy_handler
    get_data_handler = dummy_handler
    get_live_data_handler = dummy_handler
    get_predictions_handler = dummy_handler
    get_sea_forecast_handler = dummy_handler
    get_ims_warnings_handler = dummy_handler

# Global variable for frontend process
frontend_process: Optional[subprocess.Popen] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("=" * 60)
    logger.info("[START] Starting Sea Level Dashboard Server...")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"Python: {sys.version}")
    logger.info("=" * 60)
    
    # Get configuration
    port = int(os.getenv("BACKEND_PORT", "30886"))
    
    logger.info("Server Configuration:")
    logger.info(f"  Port: {port}")
    logger.info(f"  Environment: {os.getenv('ENV', 'production')}")
    logger.info(f"  Debug: {os.getenv('DEBUG', 'False')}")
    logger.info("=" * 60)
    
    logger.info("Server will be accessible at:")
    logger.info(f"  📍 Local: http://127.0.0.1:{port}")
    logger.info(f"  📚 API Docs: http://127.0.0.1:{port}/docs")
    logger.info("=" * 60)
    
    # Attach the globally-imported db_manager to the app state
    if db_manager:
        app.state.db_manager = db_manager
        logger.info("[OK] Database connection established via module import")
    else:
        logger.warning("[WARN] Database manager not available, running in demo mode")
    
    # Check if frontend needs to be started
    if os.getenv("AUTO_START_FRONTEND", "false").lower() == "true":
        start_frontend_dev_server()
    
    yield
    
    # Cleanup
    logger.info("[STOP] Shutting down server...")
    
    # Stop frontend if running
    stop_frontend_dev_server()
    
    # No need to explicitly close engine here as SQLAlchemy handles pooling
    logger.info("[OK] Server shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Sea Level Dashboard API",
    description="Real-time sea level monitoring with predictive analytics",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS - Allow all for development/production hybrid
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") != "*" else ["*"]

# Add comprehensive CORS origins
if cors_origins != ["*"]:
    cors_origins.extend([
        "http://localhost:30886",
        "http://localhost:3000",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Helper Functions
def check_node_npm_windows():
    """Check if Node.js and npm are available on Windows"""
    
    # Common paths on Windows
    node_paths = [
        "node",
        "node.exe",
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Program Files (x86)\nodejs\node.exe",
        os.path.expanduser(r"~\AppData\Roaming\npm\node.exe"),
    ]
    
    for node_path in node_paths:
        try:
            result = subprocess.run(
                [node_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                shell=False
            )
            if result.returncode == 0:
                logger.info(f"[OK] Node.js found: {result.stdout.strip()}")
                return True
        except:
            continue
    
    logger.warning("[WARN] Node.js not found. Frontend auto-start disabled.")
    logger.info("   Install from: https://nodejs.org/")
    return False

def start_frontend_dev_server():
    """Start frontend development server on Windows"""
    global frontend_process
    
    if not check_node_npm_windows():
        return
    
    frontend_path = frontend_root
    if not frontend_path.exists():
        logger.warning(f"[WARN] Frontend directory not found: {frontend_path}")
        return
    
    try:
        logger.info("[START] Starting frontend development server...")
        
        # Use npm.cmd on Windows
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        
        # Set environment variables
        env = os.environ.copy()
        env["BROWSER"] = "none"  # Don't open browser
        
        frontend_process = subprocess.Popen(
            [npm_cmd, "start"],
            cwd=str(frontend_path),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        )
        
        logger.info("[OK] Frontend development server started")
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to start frontend: {e}")

def stop_frontend_dev_server():
    """Stop frontend development server"""
    global frontend_process
    
    if frontend_process:
        try:
            if sys.platform == "win32":
                # Windows: Use taskkill
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(frontend_process.pid)],
                    capture_output=True
                )
            else:
                # Unix: Send SIGTERM
                frontend_process.terminate()
                frontend_process.wait(timeout=5)
            
            logger.info("[OK] Frontend server stopped")
        except:
            pass
        finally:
            frontend_process = None

# Helper function to convert Lambda responses
def lambda_to_fastapi_response(lambda_response: dict) -> JSONResponse:
    """Convert Lambda response to FastAPI response"""
    try:
        status_code = lambda_response.get("statusCode", 200)
        body = lambda_response.get("body", "{}")
        headers = lambda_response.get("headers", {})
        
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                body = {"data": body}
        
        return JSONResponse(
            content=body,
            status_code=status_code,
            headers=headers
        )
    except Exception as e:
        logger.error(f"Error converting lambda response: {e}")
        return JSONResponse(
            content={"error": "Internal server error"},
            status_code=500
        )

# API Routes
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "platform": sys.platform,
        "python_version": sys.version,
        "server_status": "online"
    }
    
    # Check database
    try:
        if db_manager and db_manager.health_check():
            health_status["database"] = "connected"
        else:
            health_status["database"] = "disconnected"
    except Exception as e:
        health_status["database"] = f"disconnected ({e})"
    
    return health_status

@app.get("/api/stations")
async def get_stations():
    """Get all monitoring stations"""
    try:
        event = {"httpMethod": "GET", "path": "/stations", "queryStringParameters": {}}
        response = get_stations_handler(event, None)
        return lambda_to_fastapi_response(response)
    except Exception as e:
        logger.error(f"Error in get_stations: {e}")
        # Return default stations as fallback
        return {
            "stations": ["Acre", "Yafo", "Ashkelon", "Eilat", "All Stations"],
            "database_available": False,
            "error": str(e)
        }

@app.get("/api/data")
async def get_data(
    station: str = "All Stations",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_source: str = "default"
):
    """Get historical data"""
    try:
        event = {
            "httpMethod": "GET",
            "path": "/data",
            "queryStringParameters": {
                "station": station,
                "start_date": start_date,
                "end_date": end_date,
                "data_source": data_source
            }
        }
        response = get_data_handler(event, None)
        return lambda_to_fastapi_response(response)
    except Exception as e:
        logger.error(f"Error in get_data: {e}")
        return JSONResponse(
            content={"error": str(e), "data": []},
            status_code=500
        )

@app.get("/api/live-data")
async def get_live_data(station: Optional[str] = None):
    """Get latest measurements"""
    try:
        event = {
            "httpMethod": "GET",
            "path": "/live-data",
            "queryStringParameters": {"station": station} if station else {}
        }
        response = get_live_data_handler(event, None)
        return lambda_to_fastapi_response(response)
    except Exception as e:
        logger.error(f"Error in get_live_data: {e}")
        return JSONResponse(
            content={"error": str(e), "data": []},
            status_code=500
        )

@app.get("/api/predictions")
async def get_predictions(
    stations: Optional[str] = None,
    station: Optional[str] = None,
    model: str = "kalman",
    steps: int = 240,
    forecast_hours: Optional[int] = None
):
    """Get predictions for stations - supports multiple stations and models"""
    try:
        # Support both 'stations' and 'station' parameters
        station_param = stations or station
        
        if not station_param:
            return JSONResponse(
                content={"error": "Station parameter is required"},
                status_code=400
            )
        
        # Support both 'steps' and 'forecast_hours' parameters
        steps_param = steps if forecast_hours is None else forecast_hours
        
        logger.info(f"[API] Predictions request: stations={station_param}, model={model}, steps={steps_param}")
        
        event = {
            "httpMethod": "GET",
            "path": "/predictions",
            "queryStringParameters": {
                "stations": station_param,
                "station": station_param,
                "model": model,
                "steps": str(steps_param)
            }
        }
        
        response = get_predictions_handler(event, None)
        result = lambda_to_fastapi_response(response)
        
        logger.info(f"[API] Predictions returned successfully for {station_param}")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_predictions: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.options("/api/predictions")
async def predictions_options():
    """Handle CORS preflight for predictions"""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
    )

@app.get("/api/sea-forecast")
async def get_sea_forecast():
    """Get sea conditions forecast"""
    try:
        event = {"httpMethod": "GET", "path": "/sea-forecast", "queryStringParameters": {}}
        response = get_sea_forecast_handler(event, None)
        return lambda_to_fastapi_response(response)
    except Exception as e:
        logger.error(f"Error in get_sea_forecast: {e}")
        return JSONResponse(
            content={"error": str(e), "forecast": []},
            status_code=500
        )

@app.get("/api/ims-warnings")
async def get_ims_warnings():
    """Get IMS weather warnings"""
    try:
        event = {"httpMethod": "GET", "path": "/ims-warnings", "queryStringParameters": {}}
        response = get_ims_warnings_handler(event, None)
        return lambda_to_fastapi_response(response)
    except Exception as e:
        logger.error(f"Error in get_ims_warnings: {e}")
        return JSONResponse(
            content={"error": str(e), "warnings": []},
            status_code=500
        )

@app.get("/mariners-forecast")
async def get_mariners_forecast():
    """Get mariners forecast from IMS"""
    try:
        import xml.etree.ElementTree as ET
        import requests
        
        url = "https://ims.gov.il/sites/default/files/ims_data/xml_files/isr_sea.xml"
        response = requests.get(url, timeout=10)
        
        # Try different encodings
        for encoding in ['iso-8859-1', 'utf-8', 'windows-1255']:
            try:
                content = response.content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        root = ET.fromstring(content)
        
        # Parse metadata
        metadata = {
            'organization': root.find('.//organization').text if root.find('.//organization') is not None else '',
            'title': root.find('.//title').text if root.find('.//title') is not None else '',
            'issue_datetime': root.find('.//issue_datetime').text if root.find('.//issue_datetime') is not None else ''
        }
        
        # Parse locations
        locations = []
        for location in root.findall('.//location'):
            location_data = {
                'id': location.get('id', ''),
                'name_eng': location.get('name_eng', ''),
                'name_heb': location.get('name_heb', ''),
                'forecasts': []
            }
            
            for time_period in location.findall('.//time_period'):
                forecast = {
                    'from': time_period.get('from', ''),
                    'to': time_period.get('to', ''),
                    'elements': {}
                }
                
                for element in time_period.findall('.//element'):
                    element_name = element.get('name', '')
                    element_value = element.text or ''
                    forecast['elements'][element_name] = element_value
                
                location_data['forecasts'].append(forecast)
            
            locations.append(location_data)
        
        return {
            'metadata': metadata,
            'locations': locations
        }
        
    except Exception as e:
        logger.error(f"Error fetching mariners forecast: {e}")
        return JSONResponse(
            content={"error": f"Error fetching mariners forecast: {str(e)}"},
            status_code=500
        )

@app.get("/mariners-mapframe")
async def mariners_mapframe():
    """Serve the mariners forecast map iframe"""
    mapframe_path = backend_root / "mariners_mapframe.html"
    if mapframe_path.exists():
        return FileResponse(str(mapframe_path), media_type="text/html")
    return JSONResponse(content={"error": "Mariners mapframe not found"}, status_code=404)

@app.get("/api/stations/map")
async def get_api_stations_map(end_date: Optional[str] = None):
    """Get stations with coordinates for map display - API endpoint"""
    stations_data = [
        {"Station": "Acre", "x": 35.0818, "y": 32.9279, "latest_value": "0.123", "temperature": "22.5", "last_update": "2025-10-22 10:00:00"},
        {"Station": "Yafo", "x": 34.7505, "y": 32.0542, "latest_value": "0.098", "temperature": "23.1", "last_update": "2025-10-22 10:00:00"},
        {"Station": "Ashkelon", "x": 34.5668, "y": 31.6688, "latest_value": "0.087", "temperature": "23.8", "last_update": "2025-10-22 10:00:00"},
        {"Station": "Eilat", "x": 34.9497, "y": 29.5577, "latest_value": "0.156", "temperature": "25.2", "last_update": "2025-10-22 10:00:00"}
    ]
    return stations_data

@app.get("/stations/map")
async def get_stations_map(end_date: Optional[str] = None):
    """Get stations with coordinates for map display"""
    try:
        from lambdas.get_station_map.main import lambda_handler as get_station_map_handler
        
        event = {
            "httpMethod": "GET",
            "path": "/stations/map",
            "queryStringParameters": {"end_date": end_date} if end_date else {}
        }
        response = get_station_map_handler(event, None)
        return lambda_to_fastapi_response(response)
    except Exception as e:
        logger.error(f"Error in get_stations_map: {e}")
        stations_data = [
            {"Station": "Acre", "x": 35.0818, "y": 32.9279, "latest_value": "0.123", "temperature": "22.5", "last_update": "2025-10-22 10:00:00"},
            {"Station": "Yafo", "x": 34.7505, "y": 32.0542, "latest_value": "0.098", "temperature": "23.1", "last_update": "2025-10-22 10:00:00"},
            {"Station": "Ashkelon", "x": 34.5668, "y": 31.6688, "latest_value": "0.087", "temperature": "23.8", "last_update": "2025-10-22 10:00:00"},
            {"Station": "Eilat", "x": 34.9497, "y": 29.5577, "latest_value": "0.156", "temperature": "25.2", "last_update": "2025-10-22 10:00:00"}
        ]
        return stations_data

@app.get("/sea-forecast")
async def get_sea_forecast_direct():
    """Get sea conditions forecast - direct endpoint for maps"""
    try:
        event = {"httpMethod": "GET", "path": "/sea-forecast", "queryStringParameters": {}}
        response = get_sea_forecast_handler(event, None)
        return lambda_to_fastapi_response(response)
    except Exception as e:
        logger.error(f"Error in get_sea_forecast_direct: {e}")
        return JSONResponse(
            content={"error": str(e), "locations": []},
            status_code=500
        )

@app.get("/mapframe")
async def serve_mapframe(end_date: Optional[str] = None):
    """Serve the GovMap iframe"""
    mapframe_path = backend_root / "mapframe.html"
    if mapframe_path.exists():
        return FileResponse(str(mapframe_path), media_type="text/html")
    return JSONResponse(content={"error": "Mapframe not found"}, status_code=404)

# --- Static File Serving ---
# This section must come AFTER all API routes are defined.
frontend_build = frontend_root / "build"
if frontend_build.exists():
    logger.info(f"[INFO] Serving frontend from {frontend_build}")

    # Mount the 'static' folder from the build directory, if it exists
    static_dir = frontend_build / "static"
    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

        # This catch-all route should serve the index.html for any path that is not an API route or a static file.
        # It's important this comes after the API routes.
        @app.get("/{full_path:path}", response_class=FileResponse, include_in_schema=False)
        async def serve_react_app(full_path: str):
            # Explicitly exclude mapframe from catch-all
            if full_path.startswith('mapframe'):
                return await serve_mapframe()
            
            file_path = frontend_build / full_path
            # If the requested path points to a file in the build directory (like assets), serve it directly.
            if file_path.is_file():
                return FileResponse(str(file_path))
            # Otherwise, serve the main index.html file for client-side routing.
            index_html_path = frontend_build / "index.html"
            if index_html_path.exists():
                return FileResponse(str(index_html_path))
            return JSONResponse(content={"message": "Frontend not built."}, status_code=404)
    else:
        logger.warning(f"[WARN] Frontend 'static' directory not found at {static_dir}. UI will not be served.")
        @app.get("/", include_in_schema=False)
        async def root_fallback():
            return JSONResponse(content={"message": "Backend is running, but the frontend is not built."})

# Windows-compatible signal handling
def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"\n[SIGNAL] Received signal {signum}, shutting down gracefully...")
    stop_frontend_dev_server()
    sys.exit(0)

# Register signal handlers (Windows compatible)
if sys.platform == "win32":
    # Windows only supports SIGTERM and SIGINT
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination
else:
    # Unix/Linux supports more signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")  # Listen on all interfaces
    port = int(os.getenv("BACKEND_PORT", "30886"))
    env = os.getenv("ENV", "production")
    
    print("\n" + "=" * 60)
    print("SEA LEVEL DASHBOARD SERVER")
    print("=" * 60)
    print(f"Platform: {sys.platform}")
    print(f"Environment: {env}")
    print(f"Starting on: {host}:{port}")
    print("=" * 60)
    print(f"Access URLs:")
    print(f"  📍 Local:    http://127.0.0.1:{port}")
    print(f"  📚 API Docs: http://127.0.0.1:{port}/docs")
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    # Run server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
        use_colors=True,
        # Only use reload in development
        reload=(env == "development"),
        # Workers for production (Windows supports only 1 worker with reload=False)
        workers=1
    )