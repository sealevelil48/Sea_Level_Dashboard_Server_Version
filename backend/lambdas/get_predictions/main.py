# backend/lambdas/get_predictions/main.py
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
    from shared.database import engine, db_manager
    from sqlalchemy import text
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"❌ Database import error in get_predictions: {e}")
    DATABASE_AVAILABLE = False

# Import prediction libraries
try:
    from statsmodels.tsa.arima.model import ARIMA
    ARIMA_AVAILABLE = True
except ImportError:
    ARIMA_AVAILABLE = False
    print("⚠️ ARIMA not available")

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("⚠️ Prophet not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_prediction_data(station, days_back=30):
    """Get historical data for predictions"""
    if not DATABASE_AVAILABLE or not engine:
        return pd.DataFrame()
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        sql_query = '''
            SELECT m."Tab_DateTime", m."Tab_Value_mDepthC1"
            FROM "Monitors_info2" m
            JOIN "Locations" l ON m."Tab_TabularTag" = l."Tab_TabularTag"
            WHERE l."Station" = :station
            AND m."Tab_DateTime" >= :start_date
            AND m."Tab_DateTime" <= :end_date
            AND m."Tab_Value_mDepthC1" IS NOT NULL
            ORDER BY m."Tab_DateTime"
        '''
        
        with engine.connect() as connection:
            result = connection.execute(text(sql_query), {
                'station': station,
                'start_date': start_date,
                'end_date': end_date
            })
            df = pd.DataFrame(result.fetchall())
            if not df.empty:
                df.columns = ['Tab_DateTime', 'Tab_Value_mDepthC1']
                df['Tab_DateTime'] = pd.to_datetime(df['Tab_DateTime'])
                # Clean data
                df = df.dropna()
                df = df[~df['Tab_Value_mDepthC1'].isin([np.inf, -np.inf])]
            return df
    except Exception as e:
        logger.error(f"Error getting prediction data: {e}")
        return pd.DataFrame()

def arima_predict(station, steps=240):
    """Generate ARIMA predictions (10 days = 240 hours)"""
    if not ARIMA_AVAILABLE:
        logger.warning("ARIMA not available")
        return None
    
    try:
        df = get_prediction_data(station, days_back=30)
        if df.empty or len(df) < 24:
            logger.warning(f"Not enough data for ARIMA prediction: {len(df)} points")
            return None
        
        # Resample to hourly if needed
        df = df.set_index('Tab_DateTime')
        hourly_data = df['Tab_Value_mDepthC1'].resample('H').mean().fillna(method='ffill')
        
        # Fit ARIMA model
        model = ARIMA(hourly_data, order=(5, 1, 0))
        model_fit = model.fit()
        
        # Make predictions
        forecast = model_fit.forecast(steps=steps)
        
        return forecast.tolist()
        
    except Exception as e:
        logger.error(f"ARIMA prediction failed: {e}")
        return None

def prophet_predict(station, steps=240):
    """Generate Prophet predictions"""
    if not PROPHET_AVAILABLE:
        logger.warning("Prophet not available")
        return None
    
    try:
        df = get_prediction_data(station, days_back=90)  # Prophet needs more data
        if df.empty or len(df) < 24:
            logger.warning(f"Not enough data for Prophet prediction: {len(df)} points")
            return None
        
        # Prepare data for Prophet
        prophet_df = pd.DataFrame({
            'ds': df['Tab_DateTime'],
            'y': df['Tab_Value_mDepthC1']
        })
        
        # Create and fit model
        model = Prophet(daily_seasonality=True, yearly_seasonality=False)
        model.fit(prophet_df)
        
        # Make future dataframe
        future = model.make_future_dataframe(periods=steps, freq='H')
        forecast = model.predict(future)
        
        # Get only future predictions
        future_forecast = forecast[forecast['ds'] > prophet_df['ds'].max()][['ds', 'yhat']]
        
        # Convert to required format
        result = []
        for _, row in future_forecast.iterrows():
            result.append({
                'ds': row['ds'].isoformat(),
                'yhat': float(row['yhat'])
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Prophet prediction failed: {e}")
        return None

def handler(event, context):
    """Lambda handler for predictions"""
    try:
        # Parse parameters
        params = event.get('queryStringParameters') or {}
        station = params.get('station')
        models = params.get('model', 'all').split(',')
        
        if not station:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({"error": "Station parameter is required"})
            }
        
        logger.info(f"Generating predictions for station={station}, models={models}")
        
        results = {}
        
        # Generate ARIMA predictions
        if 'arima' in models or 'all' in models:
            arima_result = arima_predict(station)
            if arima_result:
                results['arima'] = arima_result
            else:
                results['arima'] = []
        
        # Generate Prophet predictions
        if 'prophet' in models or 'all' in models:
            prophet_result = prophet_predict(station)
            if prophet_result:
                results['prophet'] = prophet_result
            else:
                results['prophet'] = []
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": json.dumps(results)
        }
        
    except Exception as e:
        logger.error(f"Error in predictions handler: {e}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": str(e)})
        }