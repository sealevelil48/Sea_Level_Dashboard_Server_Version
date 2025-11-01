# backend/lambdas/get_data/main.py - Fixed version with proper data cleaning
import json
import logging
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add paths for shared modules
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, backend_dir)

try:
    from shared.database import engine, M, L, S, db_manager
    from sqlalchemy import text
    DATABASE_AVAILABLE = True
    print("✅ Database modules imported successfully for get_data")
except ImportError as e:
    print(f"❌ Database import error in get_data: {e}")
    DATABASE_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_numeric_data(df):
    """Clean numeric data by replacing inf/nan values"""
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_columns:
        # Replace infinity values with NaN first
        df[col] = df[col].replace([np.inf, -np.inf], np.nan)
        
        # For sea level data, we can interpolate or use forward fill
        if 'mDepth' in col or 'Value' in col:
            # Try interpolation first
            df[col] = df[col].interpolate(method='linear', limit_direction='both')
            # Fill any remaining NaN with forward/backward fill
            df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
            # If still NaN, use 0
            df[col] = df[col].fillna(0)
        else:
            # For other numeric columns, just fill with 0
            df[col] = df[col].fillna(0)
    
    return df

def load_data_from_db(start_date=None, end_date=None, station=None, data_source='default', limit=15000):
    """Load data from database using raw SQL with proper data cleaning"""
    if not DATABASE_AVAILABLE or not engine:
        logger.warning("Database not available, returning demo data")
        return pd.DataFrame([
            {
                "Tab_DateTime": "2024-01-01T12:00:00Z",
                "Station": station or "Demo Station",
                "Tab_Value_mDepthC1": 1.234,
                "Tab_Value_monT2m": 20.5,
                "anomaly": 0
            }
        ])
    
    try:
        # Build raw SQL query
        if data_source == 'tides':
            sql_query = '''
                SELECT "Date", "Station", "HighTide", "HighTideTime", "HighTideTemp", 
                       "LowTide", "LowTideTime", "LowTideTemp", "MeasurementCount",
                       0 as anomaly
                FROM "SeaTides"
                WHERE 1=1
            '''
            params = {}
            
            if station and station != 'All Stations':
                sql_query += ' AND "Station" = :station'
                params['station'] = station
            if start_date:
                sql_query += ' AND "Date" >= :start_date'
                params['start_date'] = start_date
            if end_date:
                sql_query += ' AND "Date" <= :end_date'
                params['end_date'] = end_date
            
            sql_query += ' ORDER BY "Date" ASC LIMIT :limit'
            params['limit'] = limit
                
        else:
            # Default sea level data
            sql_query = '''
                SELECT m."Tab_DateTime", l."Station", 
                       CAST(m."Tab_Value_mDepthC1" AS FLOAT) as "Tab_Value_mDepthC1",
                       CAST(m."Tab_Value_monT2m" AS FLOAT) as "Tab_Value_monT2m",
                       0 as anomaly
                FROM "Monitors_info2" m
                JOIN "Locations" l ON m."Tab_TabularTag" = l."Tab_TabularTag"
                WHERE 1=1
            '''
            params = {}
            
            if station and station != 'All Stations':
                sql_query += ' AND l."Station" = :station'
                params['station'] = station
            if start_date:
                sql_query += ' AND m."Tab_DateTime" >= :start_date'
                params['start_date'] = start_date + ' 00:00:00'
            if end_date:
                sql_query += ' AND m."Tab_DateTime" <= :end_date'
                params['end_date'] = end_date + ' 23:59:59'
                
            sql_query += ' ORDER BY m."Tab_DateTime" ASC LIMIT :limit'
            params['limit'] = limit
            
        # Execute query
        with engine.connect() as connection:
            result = connection.execute(text(sql_query), params)
            df = pd.DataFrame(result.fetchall())
            
            if not df.empty:
                # Set column names
                df.columns = result.keys()
                
                # Clean numeric data
                df = clean_numeric_data(df)
                
                # Process anomalies if requested
                if 'anomaly' not in df.columns:
                    df['anomaly'] = 0
                    
            logger.info(f"Loaded {len(df)} rows for station={station}, data_source={data_source}")
            return df
            
    except Exception as e:
        logger.error(f"Error loading data from database: {e}")
        return pd.DataFrame()

def detect_anomalies(df):
    """Simple anomaly detection using IQR method"""
    if 'Tab_Value_mDepthC1' not in df.columns or df.empty:
        return df
        
    try:
        # Get valid values only
        valid_values = df['Tab_Value_mDepthC1'].dropna()
        
        if len(valid_values) > 10:  # Need enough data for IQR
            Q1 = valid_values.quantile(0.25)
            Q3 = valid_values.quantile(0.75)
            IQR = Q3 - Q1
            
            # Define outlier bounds
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Mark anomalies using vectorized operations
            df['anomaly'] = np.where(
                (df['Tab_Value_mDepthC1'].notna()) & 
                ((df['Tab_Value_mDepthC1'] < lower_bound) | (df['Tab_Value_mDepthC1'] > upper_bound)), 
                -1, 0
            )
            
            logger.info(f"Detected {sum(df['anomaly'] == -1)} anomalies")
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        df['anomaly'] = 0
        
    return df

def lambda_handler(event, context):
    """Lambda handler for get_data with proper data cleaning"""
    try:
        # Parse parameters
        params = event.get('queryStringParameters') or {}
        station = params.get('station')
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        data_source = params.get('data_source', 'default')
        show_anomalies = params.get('show_anomalies', 'false').lower() == 'true'
        limit = int(params.get('limit', 15000))  # Increased default for full week coverage
        
        # Validate and cap limit - but allow unlimited for All Stations
        if limit <= 0:
            limit = 15000
        if limit > 50000 and station != 'All Stations':
            limit = 50000  # Increased safety cap for longer date ranges

        logger.info(f"get_data called with: station={station}, start_date={start_date}, "
                   f"end_date={end_date}, data_source={data_source}")

        # Load data with limit
        df = load_data_from_db(start_date, end_date, station, data_source, limit)
        
        # Apply anomaly detection if requested
        if show_anomalies and data_source == 'default':
            df = detect_anomalies(df)
        
        if df.empty:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json", 
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "message": "No data found",
                    "details": {
                        "station": station or "All Stations",
                        "start_date": start_date,
                        "end_date": end_date,
                        "data_source": data_source
                    }
                })
            }

        # Convert to JSON-serializable format
        df_json = df.copy()
        
        # Convert datetime and date columns to proper format
        for col in df_json.columns:
            if data_source == 'tides':
                if col == 'Date':
                    # Format date as DD/MM/YYYY only
                    df_json[col] = pd.to_datetime(df_json[col]).dt.strftime('%d/%m/%Y')
                elif 'Time' in col and pd.api.types.is_datetime64_any_dtype(df_json[col]):
                    # Format tide times as HH:MM only
                    df_json[col] = df_json[col].dt.strftime('%H:%M')
                elif pd.api.types.is_datetime64_any_dtype(df_json[col]):
                    df_json[col] = df_json[col].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            else:
                if pd.api.types.is_datetime64_any_dtype(df_json[col]):
                    df_json[col] = df_json[col].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Clean numeric columns - replace inf/nan with valid values
        numeric_cols = df_json.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            df_json[col] = df_json[col].replace([np.inf, -np.inf], np.nan)
            df_json[col] = df_json[col].fillna(0)
        
        # Convert to records format
        response_data = df_json.to_dict('records')
        
        # Final check for any remaining invalid values
        response_json = json.dumps(response_data, default=str)  # Use default=str for any remaining objects
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json", 
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": response_json
        }
        
    except Exception as e:
        logger.error(f"Error in get_data lambda: {e}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": f"Internal server error: {str(e)}",
                "station": station
            })
        }
