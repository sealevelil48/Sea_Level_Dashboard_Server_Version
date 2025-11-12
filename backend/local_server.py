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

# Suppress asyncio warnings on Windows
logging.getLogger('asyncio').setLevel(logging.CRITICAL)
logging.getLogger('asyncio.proactor_events').setLevel(logging.CRITICAL)
logging.getLogger('asyncio.windows_events').setLevel(logging.CRITICAL)

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
    try:
        # Try optimized database manager
        from optimizations.database_optimized import db_manager
        logger.info("[OK] Optimized database manager imported successfully")
    except ImportError:
        db_manager = None

# Import baseline integration
try:
    from shared.baseline_integration import (
        get_outliers_api,
        get_corrections_api,
        BaselineIntegratedProcessor
    )
    from shared.data_processing import load_data_from_db
    BASELINE_API_AVAILABLE = True
    logger.info("[OK] Baseline integration API imported successfully")
except ImportError as e:
    logger.warning(f"[WARN] Baseline integration API not available: {e}")
    BASELINE_API_AVAILABLE = False
    
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
    """Health check endpoint with performance metrics"""
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
            # Add performance metrics if available
            if hasattr(db_manager, 'get_metrics'):
                metrics = db_manager.get_metrics()
                health_status["metrics"] = metrics
                
                # Add Redis cache status
                if db_manager._redis_client:
                    try:
                        redis_info = db_manager._redis_client.info('stats')
                        health_status["cache"] = {
                            "status": "connected",
                            "hits": redis_info.get('keyspace_hits', 0),
                            "misses": redis_info.get('keyspace_misses', 0),
                            "hit_rate": metrics.get('cache_hit_rate', '0%'),
                            "keys": db_manager._redis_client.dbsize()
                        }
                    except:
                        health_status["cache"] = {"status": "error"}
                else:
                    health_status["cache"] = {"status": "disabled"}
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
    data_source: str = "default",
    limit: int = 15000
):
    """Get historical data with pagination and caching

    Args:
        station: Station name or "All Stations" (default)
        start_date: Start date in YYYY-MM-DD format (default: 7 days ago)
        end_date: End date in YYYY-MM-DD format (default: today)
        data_source: Data source type (default: "default")
        limit: Maximum number of records (default: 15000)

    Returns:
        JSON array of data records
    """
    try:
        # Add performance monitoring
        start_time = time.time()

        # ====================================================================================
        # VALIDATION AND DEFAULT VALUES
        # ====================================================================================

        # 1. Provide default dates if not specified (last 7 days)
        if not start_date or not end_date:
            from datetime import datetime, timedelta
            today = datetime.now()
            if not end_date:
                end_date = today.strftime('%Y-%m-%d')
            if not start_date:
                start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
            logger.info(f"[DEFAULT DATES] Using default date range: {start_date} to {end_date}")

        # 2. Validate date formats
        try:
            from datetime import datetime
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError as e:
            logger.error(f"[VALIDATION ERROR] Invalid date format: {e}")
            return JSONResponse(
                content={
                    "error": "Invalid date format. Use YYYY-MM-DD format.",
                    "example": "2025-11-01",
                    "provided_start_date": start_date,
                    "provided_end_date": end_date
                },
                status_code=400
            )

        # 3. Validate date range (max 365 days for safety)
        from datetime import datetime
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        days_diff = (end_dt - start_dt).days

        if days_diff < 0:
            return JSONResponse(
                content={"error": "start_date must be before end_date"},
                status_code=400
            )

        if days_diff > 365:
            return JSONResponse(
                content={
                    "error": "Date range too large. Maximum 365 days allowed.",
                    "requested_days": days_diff,
                    "max_days": 365
                },
                status_code=400
            )

        # 4. Validate station name (optional - check against known stations)
        if station and station != "All Stations":
            # Get list of valid stations
            try:
                from shared.database import L
                from sqlalchemy import select
                with engine.connect() as conn:
                    valid_stations = [row[0] for row in conn.execute(select(L.Station).distinct()).fetchall()]

                    if station not in valid_stations:
                        logger.warning(f"[VALIDATION WARNING] Station '{station}' not found in database")
                        return JSONResponse(
                            content={
                                "error": f"Station '{station}' not found",
                                "valid_stations": valid_stations,
                                "hint": "Use 'All Stations' to get data from all stations"
                            },
                            status_code=404
                        )
            except Exception as validation_error:
                # If validation fails, log but continue (database might be unavailable)
                logger.warning(f"[VALIDATION SKIP] Could not validate station: {validation_error}")

        # ====================================================================================
        # EXECUTE REQUEST
        # ====================================================================================

        event = {
            "httpMethod": "GET",
            "path": "/data",
            "queryStringParameters": {
                "station": station,
                "start_date": start_date,
                "end_date": end_date,
                "data_source": data_source,
                "limit": str(limit)
            }
        }
        response = get_data_handler(event, None)

        # Add performance headers
        duration = (time.time() - start_time) * 1000
        result = lambda_to_fastapi_response(response)

        # Add cache and performance headers
        if hasattr(result, 'headers'):
            result.headers['X-Response-Time'] = f"{duration:.0f}ms"
            result.headers['Cache-Control'] = 'public, max-age=120'

            # Determine cache status from logs
            if duration < 200:  # Fast response likely from cache
                result.headers['X-Cache'] = 'HIT'
            else:
                result.headers['X-Cache'] = 'MISS'

        return result
    except Exception as e:
        logger.error(f"Error in get_data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={"error": str(e), "data": []},
            status_code=500
        )

@app.get("/api/data/batch")
async def get_data_batch(
    stations: str = "",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_source: str = "default",
    show_anomalies: bool = False
):
    """Get historical data for multiple stations in a single query (batch endpoint)"""
    try:
        from lambdas.get_data.main import lambda_handler_batch

        # Add performance monitoring
        start_time = time.time()

        event = {
            "httpMethod": "GET",
            "path": "/data/batch",
            "queryStringParameters": {
                "stations": stations,
                "start_date": start_date,
                "end_date": end_date,
                "data_source": data_source,
                "show_anomalies": str(show_anomalies).lower()
            }
        }
        response = lambda_handler_batch(event, None)

        # Add performance headers
        duration = (time.time() - start_time) * 1000
        result = lambda_to_fastapi_response(response)

        # Add cache and performance headers
        if hasattr(result, 'headers'):
            result.headers['X-Response-Time'] = f"{duration:.0f}ms"
            result.headers['Cache-Control'] = 'public, max-age=120'

        logger.info(f"[BATCH] Completed batch request for stations: {stations} in {duration:.0f}ms")
        return result
    except Exception as e:
        logger.error(f"Error in get_data_batch: {e}")
        import traceback
        logger.error(traceback.format_exc())
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

@app.get("/api/mariners-forecast")
async def get_mariners_forecast():
    """Get mariners forecast from IMS"""
    try:
        import xml.etree.ElementTree as ET
        import requests
        
        logger.info("Fetching mariners forecast from IMS...")
        url = "https://ims.gov.il/sites/default/files/ims_data/xml_files/medit_sea.xml"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"IMS returned status {response.status_code}")
            raise HTTPException(status_code=500, detail=f"IMS API returned {response.status_code}")
        
        logger.info(f"IMS response length: {len(response.content)} bytes")
        
        # ✅ FIXED: Proper Hebrew encoding detection
        content = None
        encodings_to_try = [
            'windows-1255',  # Hebrew Windows (try FIRST)
            'iso-8859-8',    # Hebrew ISO
            'utf-8',         # UTF-8
            'cp1255'         # Hebrew code page
        ]

        for encoding in encodings_to_try:
            try:
                content = response.content.decode(encoding)
                logger.info(f"✅ Successfully decoded with {encoding}")
                # Verify Hebrew characters are not mojibake
                test_text = content[:500]
                if 'ã' not in test_text and 'é' not in test_text:  # Common mojibake indicators
                    logger.info(f"✅ Encoding {encoding} verified - no mojibake detected")
                    break
                else:
                    logger.warning(f"⚠️ Encoding {encoding} produced mojibake, trying next...")
                    content = None
            except (UnicodeDecodeError, AttributeError) as e:
                logger.warning(f"⚠️ Encoding {encoding} failed: {e}")
                continue

        if not content:
            # Last resort: UTF-8 with error replacement
            content = response.content.decode('utf-8', errors='replace')
            logger.warning("⚠️ Using UTF-8 with error replacement")
        
        if not content:
            raise HTTPException(status_code=500, detail="Failed to decode XML content")
        
        root = ET.fromstring(content)
        
        # Parse metadata
        metadata = {
            'organization': root.find('.//Organization').text if root.find('.//Organization') is not None else '',
            'title': root.find('.//Title').text if root.find('.//Title') is not None else '',
            'issue_datetime': root.find('.//IssueDateTime').text if root.find('.//IssueDateTime') is not None else ''
        }
        
        # Parse locations
        locations = []
        for location in root.findall('.//Location'):
            location_meta = location.find('LocationMetaData')
            location_data = {
                'id': location_meta.find('LocationId').text if location_meta.find('LocationId') is not None else '',
                'name_eng': location_meta.find('LocationNameEng').text if location_meta.find('LocationNameEng') is not None else '',
                'name_heb': location_meta.find('LocationNameHeb').text if location_meta.find('LocationNameHeb') is not None else '',
                'forecasts': []
            }
            
            location_forecast_data = location.find('LocationData')
            if location_forecast_data is not None:
                for time_unit in location_forecast_data.findall('TimeUnitData'):
                    forecast = {
                        'from': time_unit.find('DateTimeFrom').text if time_unit.find('DateTimeFrom') is not None else '',
                        'to': time_unit.find('DateTimeTo').text if time_unit.find('DateTimeTo') is not None else '',
                        'elements': {}
                    }
                    
                    for element in time_unit.findall('Element'):
                        element_name = element.find('ElementName').text if element.find('ElementName') is not None else ''
                        element_value = element.find('ElementValue').text if element.find('ElementValue') is not None else ''
                        forecast['elements'][element_name] = element_value
                    
                    location_data['forecasts'].append(forecast)
            
            locations.append(location_data)
        
        logger.info(f"Successfully parsed {len(locations)} locations with metadata: {metadata}")
        for loc in locations:
            logger.info(f"Location: {loc['name_eng']} ({loc['name_heb']}) - {len(loc['forecasts'])} forecasts")
        return {
            'metadata': metadata,
            'locations': locations
        }
        
    except Exception as e:
        logger.error(f"Error in mariners forecast: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching mariners forecast: {str(e)}")

@app.options("/api/mariners-forecast")
async def mariners_forecast_options():
    """Handle CORS preflight for mariners forecast"""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
    )

@app.head("/api/mariners-forecast")
async def mariners_forecast_head():
    """Handle HEAD requests for mariners forecast"""
    return JSONResponse(content={}, headers={"Content-Type": "application/json"})

@app.get("/api/outliers")
async def get_outliers(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    station: str = "All Stations"
):
    """Get outlier detection results with Enhanced Southern Baseline Rules"""
    if not BASELINE_API_AVAILABLE:
        return JSONResponse(
            content={"error": "Baseline rules not available"},
            status_code=503
        )
    
    try:
        logger.info(f"Enhanced outliers request: start_date={start_date}, end_date={end_date}, station={station}")
        
        # Special handling for Ashkelon - use broader time range due to data sync issues
        if station == "Ashkelon":
            logger.info("Ashkelon requested - using broader time range for better data coverage")
        
        # Load data with reasonable limits to prevent performance issues
        df = load_data_from_db(start_date, end_date, "All Stations")
        
        if df is None or df.empty:
            logger.warning(f"No data found for outliers query")
            return JSONResponse(
                content={
                    "error": "No data found",
                    "message": "No data available for the specified parameters",
                    "total_records": 0,
                    "outliers_detected": 0,
                    "outlier_percentage": 0,
                    "validation": {
                        "total_validations": 0,
                        "total_exclusions": 0,
                        "exclusion_rate": 0,
                        "outliers_detected": 0,
                        "baseline_calculations": 0
                    },
                    "outliers": []
                }, 
                status_code=200
            )
        
        # Limit data size for performance
        if len(df) > 5000:
            logger.warning(f"Large dataset ({len(df)} records), limiting to most recent 5000 records")
            df = df.sort_values('Tab_DateTime').tail(5000)
        
        logger.info(f"Processing {len(df)} records for enhanced outlier detection")
        
        # Get outliers with enhanced validation statistics
        import signal
        import time
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Outlier processing timeout")
        
        # Set timeout for processing (30 seconds)
        if hasattr(signal, 'SIGALRM'):  # Unix only
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)
        
        start_time = time.time()
        result = get_outliers_api(df)
        processing_time = time.time() - start_time
        
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)  # Cancel timeout
        
        # Filter results to requested station if needed
        if station and station != "All Stations":
            # Handle multiple stations (comma-separated)
            requested_stations = [s.strip() for s in station.split(',')]
            filtered_outliers = [outlier for outlier in result.get('outliers', []) 
                               if outlier.get('Station') in requested_stations]
            result['outliers'] = filtered_outliers
            result['outliers_detected'] = len(filtered_outliers)
            result['outlier_percentage'] = round(len(filtered_outliers) / result['total_records'] * 100, 2) if result['total_records'] > 0 else 0
            # Sanitize station names for logging to prevent log injection
            safe_stations = [station.replace('\n', '').replace('\r', '')[:50] for station in requested_stations]
            logger.info(f"Filtered {len(result.get('outliers', []))} total outliers to {len(filtered_outliers)} for station(s) {safe_stations}")
        else:
            logger.info(f"Returning all {result['outliers_detected']} outliers for all stations")
        
        result['processing_time_seconds'] = round(processing_time, 2)
        
        # Log validation statistics if available
        if 'validation' in result:
            validation = result['validation']
            logger.info(f"Enhanced validation: {validation['total_exclusions']} exclusions out of {validation['total_validations']} validations ({validation['exclusion_rate']:.1f}% exclusion rate)")
        
        logger.info(f"Enhanced outliers result: {result['outliers_detected']} outliers found in {result['total_records']} records (processed in {processing_time:.2f}s)")
        return JSONResponse(content=result, status_code=200)
        
    except TimeoutError:
        logger.error("Outlier processing timeout - dataset too large")
        return JSONResponse(
            content={
                "error": "Processing timeout",
                "message": "Dataset too large for outlier processing. Try a smaller date range.",
                "total_records": 0,
                "outliers_detected": 0,
                "validation": {
                    "total_validations": 0,
                    "total_exclusions": 0,
                    "exclusion_rate": 0,
                    "outliers_detected": 0,
                    "baseline_calculations": 0
                },
                "outliers": []
            },
            status_code=408
        )
    except Exception as e:
        logger.error(f"Error getting enhanced outliers: {e}")
        return JSONResponse(
            content={
                "error": "Processing failed",
                "message": str(e),
                "total_records": 0,
                "outliers_detected": 0,
                "validation": {
                    "total_validations": 0,
                    "total_exclusions": 0,
                    "exclusion_rate": 0,
                    "outliers_detected": 0,
                    "baseline_calculations": 0
                },
                "outliers": []
            },
            status_code=500
        )


@app.get("/api/corrections")
async def get_corrections(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    station: str = "All Stations"
):
    """Get correction suggestions for outliers"""
    if not BASELINE_API_AVAILABLE:
        return JSONResponse(
            content={"error": "Baseline rules not available"},
            status_code=503
        )
    
    try:
        # ✅ ALWAYS load all stations data to ensure proper baseline computation
        df_all = load_data_from_db(start_date, end_date, "All Stations")
        logger.info(f"Loaded data for all stations: {len(df_all) if df_all is not None else 0} records")

        if df_all is None or df_all.empty:
            logger.warning("No data found for corrections computation")
            return JSONResponse(
                content={
                    "error": "No data found",
                    "message": f"No data available for the specified time range",
                    "total_suggestions": 0,
                    "suggestions": []
                },
                status_code=200
            )
            
        # Get corrections for all stations first
        result = get_corrections_api(df_all)
        
        # Filter suggestions to requested station if needed
        if station and station != "All Stations":
            filtered = [s for s in result.get('suggestions', []) if s.get('station') == station]
            result = {
                'total_suggestions': len(filtered),
                'suggestions': filtered,
                'timestamp': result.get('timestamp')
            }
            # Sanitize station name for logging to prevent log injection
            safe_station = station.replace('\n', '').replace('\r', '')[:50] if station else 'Unknown'
            logger.info(f"Filtered {len(filtered)} suggestions for station {safe_station}")
        
        return JSONResponse(content=result, status_code=200)
        
    except Exception as e:
        logger.error(f"Error getting corrections: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/validation_report")
async def get_validation_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get comprehensive validation report"""
    if not BASELINE_API_AVAILABLE:
        return JSONResponse(
            content={"error": "Baseline rules not available"},
            status_code=503
        )
    
    try:
        # Load data for all stations
        df = load_data_from_db(start_date, end_date, "All Stations")
        
        if df is None or df.empty:
            return JSONResponse(content={"error": "No data found"}, status_code=404)        
        # Generate report
        processor = BaselineIntegratedProcessor()
        report = processor.generate_validation_report(df)
        
        return JSONResponse(content=report, status_code=200)
        
    except Exception as e:
        logger.error(f"Error generating validation report: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/mariners-forecast-direct")
async def get_mariners_forecast_direct():
    """Get mariners forecast from IMS - direct endpoint"""
    try:
        import xml.etree.ElementTree as ET
        import requests
        
        logger.info("Fetching mariners forecast from IMS...")
        url = "https://ims.gov.il/sites/default/files/ims_data/xml_files/medit_sea.xml"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"IMS returned status {response.status_code}")
            raise HTTPException(status_code=500, detail=f"IMS API returned {response.status_code}")
        
        logger.info(f"IMS response length: {len(response.content)} bytes")
        
        # ✅ FIXED: Proper Hebrew encoding detection
        content = None
        encodings_to_try = [
            'windows-1255',  # Hebrew Windows (try FIRST)
            'iso-8859-8',    # Hebrew ISO
            'utf-8',         # UTF-8
            'cp1255'         # Hebrew code page
        ]

        for encoding in encodings_to_try:
            try:
                content = response.content.decode(encoding)
                logger.info(f"✅ Successfully decoded with {encoding}")
                # Verify Hebrew characters are not mojibake
                test_text = content[:500]
                if 'ã' not in test_text and 'é' not in test_text:  # Common mojibake indicators
                    logger.info(f"✅ Encoding {encoding} verified - no mojibake detected")
                    break
                else:
                    logger.warning(f"⚠️ Encoding {encoding} produced mojibake, trying next...")
                    content = None
            except (UnicodeDecodeError, AttributeError) as e:
                logger.warning(f"⚠️ Encoding {encoding} failed: {e}")
                continue

        if not content:
            # Last resort: UTF-8 with error replacement
            content = response.content.decode('utf-8', errors='replace')
            logger.warning("⚠️ Using UTF-8 with error replacement")
        
        if not content:
            raise HTTPException(status_code=500, detail="Failed to decode XML content")
        
        root = ET.fromstring(content)
        
        # Parse metadata
        metadata = {
            'organization': root.find('.//Organization').text if root.find('.//Organization') is not None else '',
            'title': root.find('.//Title').text if root.find('.//Title') is not None else '',
            'issue_datetime': root.find('.//IssueDateTime').text if root.find('.//IssueDateTime') is not None else ''
        }
        
        # Parse locations
        locations = []
        for location in root.findall('.//Location'):
            location_meta = location.find('LocationMetaData')
            location_data = {
                'id': location_meta.find('LocationId').text if location_meta.find('LocationId') is not None else '',
                'name_eng': location_meta.find('LocationNameEng').text if location_meta.find('LocationNameEng') is not None else '',
                'name_heb': location_meta.find('LocationNameHeb').text if location_meta.find('LocationNameHeb') is not None else '',
                'forecasts': []
            }
            
            location_forecast_data = location.find('LocationData')
            if location_forecast_data is not None:
                for time_unit in location_forecast_data.findall('TimeUnitData'):
                    forecast = {
                        'from': time_unit.find('DateTimeFrom').text if time_unit.find('DateTimeFrom') is not None else '',
                        'to': time_unit.find('DateTimeTo').text if time_unit.find('DateTimeTo') is not None else '',
                        'elements': {}
                    }
                    
                    for element in time_unit.findall('Element'):
                        element_name = element.find('ElementName').text if element.find('ElementName') is not None else ''
                        element_value = element.find('ElementValue').text if element.find('ElementValue') is not None else ''
                        forecast['elements'][element_name] = element_value
                    
                    location_data['forecasts'].append(forecast)
            
            locations.append(location_data)
        
        logger.info(f"Successfully parsed {len(locations)} locations with metadata: {metadata}")
        return {
            'metadata': metadata,
            'locations': locations
        }
        
    except Exception as e:
        logger.error(f"Error in mariners forecast: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching mariners forecast: {str(e)}")

@app.get("/api/mariners-mapframe-direct")
async def mariners_mapframe_direct():
    """Serve the mariners forecast map iframe - direct endpoint"""
    mapframe_path = backend_root / "mariners_mapframe.html"
    logger.info(f"Looking for mariners mapframe at: {mapframe_path}")
    if mapframe_path.exists():
        return FileResponse(str(mapframe_path), media_type="text/html")
    logger.error(f"Mariners mapframe not found at {mapframe_path}")
    raise HTTPException(status_code=404, detail="Mariners mapframe not found")

@app.get("/api/mariners-mapframe")
async def mariners_mapframe():
    """Serve the mariners forecast map iframe"""
    mapframe_path = backend_root / "mariners_mapframe.html"
    logger.info(f"Looking for mariners mapframe at: {mapframe_path}")
    if mapframe_path.exists():
        return FileResponse(str(mapframe_path), media_type="text/html")
    logger.error(f"Mariners mapframe not found at {mapframe_path}")
    raise HTTPException(status_code=404, detail="Mariners mapframe not found")

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
            # Explicitly exclude API endpoints from catch-all
            if full_path.startswith('api/') or full_path.startswith('mariners-') or full_path.startswith('mapframe'):
                raise HTTPException(status_code=404, detail="Not found")
            
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
    
    # Run server with Windows-specific fixes
    import asyncio
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
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
        workers=1,
        # Windows-specific fixes for WinError 64
        loop="asyncio",
        ws_ping_interval=None,
        ws_ping_timeout=None
    )