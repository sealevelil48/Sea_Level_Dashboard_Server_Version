# backend/shared/data_processing.py
import pandas as pd
import numpy as np
import logging
import json
from sqlalchemy import select, and_, text, func
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional, Dict, Any
from .database import db_manager

logger = logging.getLogger(__name__)

# Import ML libraries with error handling
try:
    from statsmodels.tsa.arima.model import ARIMA
    ARIMA_AVAILABLE = True
except ImportError:
    logger.warning("ARIMA not available - predictions will be disabled")
    ARIMA_AVAILABLE = False

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    logger.warning("Prophet not available - predictions will be disabled")
    PROPHET_AVAILABLE = False

try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    logger.warning("Scikit-learn not available - anomaly detection will be disabled")
    SKLEARN_AVAILABLE = False

def load_data_from_db(start_date=None, end_date=None, station=None, data_source='default'):
    """
    Optimized data loading with proper error handling and caching
    """
    try:
        # Generate cache key for this query
        cache_key = f"query:{hash(str([start_date, end_date, station, data_source]))}"
        
        # Try cache first
        cached_data = db_manager.get_from_cache(cache_key)
        if cached_data:
            try:
                return pd.read_json(cached_data, orient='records')
            except Exception as e:
                logger.warning(f"Failed to parse cached data: {e}")
        
        # Validate inputs
        if not all([db_manager.M, db_manager.L, db_manager.S]):
            logger.error("Database tables not properly loaded")
            return pd.DataFrame()
        
        # Build and execute query
        sql_query_obj = build_query(start_date, end_date, station, data_source)
        if sql_query_obj is None:
            logger.error("Failed to build query")
            return pd.DataFrame()

        df_chunks = []
        with db_manager.engine.connect() as connection:
            result = connection.execute(sql_query_obj)
            
            # Process data in chunks for memory efficiency
            while True:
                chunk = result.fetchmany(10000)
                if not chunk:
                    break
                df_chunk = pd.DataFrame(chunk, columns=result.keys())
                df_chunks.append(df_chunk)

        if not df_chunks:
            return pd.DataFrame()
        
        df = pd.concat(df_chunks, ignore_index=True)
        
        # Cache the result (5 minutes TTL)
        try:
            cache_data = df.to_json(orient='records', date_format='iso')
            db_manager.set_cache(cache_key, cache_data, 300)
        except Exception as e:
            logger.warning(f"Failed to cache query result: {e}")
        
        logger.info(f"Loaded {len(df)} records from database")
        return df

    except Exception as e:
        logger.error(f"Data load error: {e}")
        return pd.DataFrame()

def build_query(start_date, end_date, station, data_source):
    """
    Optimized query builder with proper parameter handling
    """
    try:
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if station and station != 'All Stations':
            params['station'] = station

        stmt = None
        table_for_date_filter = None
        date_col_name = None

        if data_source == 'tides':
            cols_to_select = tides_columns()
            table_for_date_filter = db_manager.S
            date_col_name = 'Date'
            stmt = select(*cols_to_select).select_from(db_manager.S)
        else:
            cols_to_select = default_columns()
            join_condition = db_manager.M.c.Tab_TabularTag == db_manager.L.c.Tab_TabularTag
            stmt = select(*cols_to_select).select_from(db_manager.M.join(db_manager.L, join_condition))
            table_for_date_filter = db_manager.M
            date_col_name = 'Tab_DateTime'

        # Apply date filters
        if start_date:
            stmt = stmt.where(table_for_date_filter.c[date_col_name] >= params['start_date'])
        if end_date:
            stmt = stmt.where(table_for_date_filter.c[date_col_name] <= params['end_date'])

        # Apply station filter
        if data_source == 'default' and 'station' in params:
            stmt = stmt.where(db_manager.L.c.Station == params['station'])
        elif data_source == 'tides' and 'station' in params:
            stmt = stmt.where(db_manager.S.c.Station == params['station'])

        # Add ordering
        if date_col_name and table_for_date_filter is not None:
            stmt = stmt.order_by(table_for_date_filter.c[date_col_name])

        return stmt

    except Exception as e:
        logger.error(f"Query building error: {e}")
        return None

def default_columns():
    """Default columns for sea level data"""
    return [
        db_manager.M.c.Tab_DateTime, 
        db_manager.L.c.Station, 
        db_manager.M.c.Tab_Value_mDepthC1, 
        db_manager.M.c.Tab_Value_monT2m
    ]

def tides_columns():
    """Columns for tides data"""
    return [
        db_manager.S.c.Date, 
        db_manager.S.c.Station, 
        db_manager.S.c.HighTide, 
        db_manager.S.c.HighTideTime,
        db_manager.S.c.HighTideTemp, 
        db_manager.S.c.LowTide, 
        db_manager.S.c.LowTideTime,
        db_manager.S.c.LowTideTemp, 
        db_manager.S.c.MeasurementCount
    ]

@lru_cache(maxsize=10)
def get_prediction_data(station: str) -> pd.DataFrame:
    """
    Cached function to get prediction data for a station
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    return load_data_from_db(
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        station=station,
        data_source='default'
    )

def arima_predict(station: str) -> Optional[list]:
    """
    ARIMA predictions with proper error handling
    """
    if not ARIMA_AVAILABLE:
        logger.warning("ARIMA not available")
        return None
    
    try:
        # Check cache first
        cache_key = f"arima_prediction:{station}"
        cached_prediction = db_manager.get_from_cache(cache_key)
        if cached_prediction:
            return json.loads(cached_prediction)
        
        df = get_prediction_data(station)
        if df.empty or 'Tab_Value_mDepthC1' not in df.columns:
            logger.warning(f"No data available for ARIMA prediction for station {station}")
            return None

        # Prepare data
        df['Tab_DateTime'] = pd.to_datetime(df['Tab_DateTime'])
        df = df.sort_values('Tab_DateTime').set_index('Tab_DateTime')

        # Resample to hourly data
        series_to_predict = df['Tab_Value_mDepthC1'].resample('H').mean().dropna()
        
        if len(series_to_predict) < 20:
            logger.warning(f"Not enough data points ({len(series_to_predict)}) for ARIMA prediction")
            return None

        # Fit model and predict
        model = ARIMA(series_to_predict, order=(5, 1, 0))
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=240)
        
        result = forecast.tolist()
        
        # Cache result for 1 hour
        db_manager.set_cache(cache_key, json.dumps(result), 3600)
        
        logger.info(f"ARIMA prediction completed for station {station}")
        return result
        
    except Exception as e:
        logger.error(f"ARIMA prediction failed for station {station}: {str(e)}")
        return None

def prophet_predict(station: str) -> Optional[pd.DataFrame]:
    """
    Prophet predictions with proper error handling
    """
    if not PROPHET_AVAILABLE:
        logger.warning("Prophet not available")
        return pd.DataFrame()
    
    try:
        # Check cache first
        cache_key = f"prophet_prediction:{station}"
        cached_prediction = db_manager.get_from_cache(cache_key)
        if cached_prediction:
            return pd.read_json(cached_prediction, orient='records')
        
        df = get_prediction_data(station)
        if df.empty or 'Tab_Value_mDepthC1' not in df.columns:
            logger.warning(f"No data available for Prophet prediction for station {station}")
            return pd.DataFrame()

        # Prepare data
        df['Tab_DateTime'] = pd.to_datetime(df['Tab_DateTime'])
        df = df.sort_values('Tab_DateTime').set_index('Tab_DateTime')

        # Resample and prepare for Prophet
        prophet_df = df['Tab_Value_mDepthC1'].resample('H').mean().reset_index()
        prophet_df = prophet_df.rename(columns={'Tab_DateTime': 'ds', 'Tab_Value_mDepthC1': 'y'})
        prophet_df = prophet_df[['ds', 'y']].dropna()

        if len(prophet_df) < 50:
            logger.warning(f"Not enough data points ({len(prophet_df)}) for Prophet prediction")
            return pd.DataFrame()

        # Fit model and predict
        model = Prophet(yearly_seasonality=True, daily_seasonality=True, growth='linear')
        model.fit(prophet_df)
        
        future = model.make_future_dataframe(periods=240, freq='H')
        if future.empty:
            logger.warning(f"Future dataframe is empty for station {station}")
            return pd.DataFrame()

        forecast = model.predict(future)
        if forecast is None or forecast.empty or 'yhat' not in forecast.columns:
            logger.warning(f"Forecast result is invalid for station {station}")
            return pd.DataFrame()

        result = forecast[['ds', 'yhat']]
        
        # Cache result for 1 hour
        cache_data = result.to_json(orient='records', date_format='iso')
        db_manager.set_cache(cache_key, cache_data, 3600)
        
        logger.info(f"Prophet prediction completed for station {station}")
        return result
        
    except Exception as e:
        logger.error(f"Prophet prediction failed for station {station}: {str(e)}")
        return pd.DataFrame()

def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Anomaly detection with proper error handling
    """
    if not SKLEARN_AVAILABLE:
        logger.warning("Scikit-learn not available")
        df['anomaly'] = 0
        return df
    
    if df.empty or 'Tab_Value_mDepthC1' not in df.columns:
        if 'anomaly' not in df.columns:
            df['anomaly'] = 0
        return df

    try:
        iso_forest = IsolationForest(contamination=0.01, random_state=42)
        X = df[['Tab_Value_mDepthC1']].values
        pred = iso_forest.fit_predict(X)
        df['anomaly'] = np.where(pred == -1, -1, 0)
        
        anomaly_count = np.sum(pred == -1)
        logger.info(f"Detected {anomaly_count} anomalies in {len(df)} records")
        
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        df['anomaly'] = 0
    
    return df

def calculate_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate statistics with proper error handling
    """
    stats = {
        'current_level': None,
        '24h_change': None,
        'avg_temp': None,
        'anomalies': None
    }

    if df.empty:
        return stats

    try:
        # Current level
        if 'Tab_Value_mDepthC1' in df.columns and not df['Tab_Value_mDepthC1'].empty:
            stats['current_level'] = float(df['Tab_Value_mDepthC1'].iloc[-1])

        # 24h change
        if 'Tab_Value_mDepthC1' in df.columns and len(df) > 1:
            now_val = df['Tab_Value_mDepthC1'].iloc[-1]
            yesterday_val = df['Tab_Value_mDepthC1'].iloc[0]
            if pd.notna(now_val) and pd.notna(yesterday_val):
                stats['24h_change'] = float(now_val - yesterday_val)

        # Average temperature
        if 'Tab_Value_monT2m' in df.columns:
            temp_mean = df['Tab_Value_monT2m'].mean()
            if pd.notna(temp_mean):
                stats['avg_temp'] = float(temp_mean)

        # Anomalies count
        if 'anomaly' in df.columns:
            anomaly_count = df[df['anomaly'] == -1].shape[0]
            stats['anomalies'] = int(anomaly_count)

    except Exception as e:
        logger.error(f"Error calculating stats: {e}")

    return stats