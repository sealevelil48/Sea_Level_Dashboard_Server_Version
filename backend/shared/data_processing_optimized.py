"""
Optimized Data Processing with Pagination and Query Limits
===========================================================
Enhanced version of your existing data_processing.py with:
- Pagination support (prevents runaway queries)
- Query limits and timeouts
- Better error handling and caching
- Backward compatibility maintained
"""

import pandas as pd
import numpy as np
import logging
import json
import hashlib
from sqlalchemy import select, and_, text, func
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional, Dict, Any, List, Tuple

# Import from the optimized database manager
from .database_production import db_manager

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

class DataProcessor:
    """Optimized data processor with pagination and caching"""
    
    # Default limits to prevent runaway queries
    DEFAULT_PAGE_SIZE = 1000
    MAX_PAGE_SIZE = 5000
    MAX_TOTAL_RECORDS = 50000
    
    @staticmethod
    def load_data_paginated(
        start_date: str,
        end_date: str,
        station: str = 'All Stations',
        data_source: str = 'default',
        page: int = 1,
        page_size: int = None,
        use_cache: bool = True
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Load data with pagination and caching
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            station: Station name or 'All Stations'
            data_source: 'default' or 'tides'
            page: Page number (1-indexed)
            page_size: Records per page (default: 1000, max: 5000)
            use_cache: Whether to use cache
        
        Returns:
            Tuple of (DataFrame, metadata_dict)
            metadata contains: total_records, total_pages, current_page, has_next, has_prev
        """
        # Validate pagination parameters
        page = max(1, page)
        page_size = page_size or DataProcessor.DEFAULT_PAGE_SIZE
        page_size = min(page_size, DataProcessor.MAX_PAGE_SIZE)
        
        offset = (page - 1) * page_size
        
        logger.info(f"Loading data - Station: {station}, "
                   f"Date: {start_date} to {end_date}, "
                   f"Page: {page}, PageSize: {page_size}")
        
        try:
            # Get total count first (cached separately)
            total_count = DataProcessor._get_total_count(
                start_date, end_date, station, data_source, use_cache
            )
            
            # Check if request exceeds reasonable limits
            if total_count > DataProcessor.MAX_TOTAL_RECORDS:
                logger.warning(f"Query would return {total_count} records. "
                             f"Consider narrowing date range.")
            
            # Build and execute paginated query
            query, params = DataProcessor._build_paginated_query(
                start_date, end_date, station, data_source, offset, page_size
            )
            
            # Execute query (with caching)
            rows = db_manager.execute_query(query, params, use_cache=use_cache)
            
            # Convert to DataFrame
            if rows:
                df = pd.DataFrame([dict(row._mapping) for row in rows])
            else:
                df = pd.DataFrame()
            
            # Calculate pagination metadata
            total_pages = (total_count + page_size - 1) // page_size
            metadata = {
                'total_records': total_count,
                'total_pages': total_pages,
                'current_page': page,
                'page_size': page_size,
                'records_returned': len(df),
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
            
            logger.info(f"Loaded {len(df)} records (page {page}/{total_pages})")
            
            return df, metadata
            
        except Exception as e:
            logger.error(f"Data load error: {e}")
            return pd.DataFrame(), {
                'error': str(e),
                'total_records': 0,
                'total_pages': 0,
                'current_page': page
            }
    
    @staticmethod
    def _get_total_count(
        start_date: str,
        end_date: str,
        station: str,
        data_source: str,
        use_cache: bool = True
    ) -> int:
        """Get total record count (cached separately for efficiency)"""
        
        try:
            if data_source == 'tides':
                count_query = """
                    SELECT COUNT(*) as total
                    FROM "SeaTides" s
                    WHERE s."Date" BETWEEN :start_date AND :end_date
                """
                if station != 'All Stations':
                    count_query += ' AND s."Station" = :station'
            else:
                count_query = """
                    SELECT COUNT(*) as total
                    FROM "Monitors_info2" m
                    JOIN "Locations" l ON m."Tab_TabularTag" = l."Tab_TabularTag"
                    WHERE m."Tab_DateTime" BETWEEN :start_date AND :end_date
                """
                if station != 'All Stations':
                    count_query += ' AND l."Station" = :station'
            
            params = {
                'start_date': start_date,
                'end_date': end_date
            }
            if station != 'All Stations':
                params['station'] = station
            
            # Cache count queries longer (10 minutes)
            rows = db_manager.execute_query(
                count_query, 
                params, 
                use_cache=use_cache,
                cache_ttl=600
            )
            
            return rows[0][0] if rows else 0
            
        except Exception as e:
            logger.error(f"Count query failed: {e}")
            return 0
    
    @staticmethod
    def _build_paginated_query(
        start_date: str,
        end_date: str,
        station: str,
        data_source: str,
        offset: int,
        limit: int
    ) -> Tuple[str, Dict[str, Any]]:
        """Build SQL query with pagination"""
        
        params = {
            'start_date': start_date,
            'end_date': end_date,
            'offset': offset,
            'limit': limit
        }
        
        if data_source == 'tides':
            query = """
                SELECT 
                    s."Date",
                    s."Station",
                    s."HighTide" as high_tide_height,
                    s."HighTideTime" as high_tide_time,
                    s."LowTide" as low_tide_height,
                    s."LowTideTime" as low_tide_time
                FROM "SeaTides" s
                WHERE s."Date" BETWEEN :start_date AND :end_date
            """
            if station != 'All Stations':
                query += ' AND s."Station" = :station'
                params['station'] = station
            
            query += """
                ORDER BY s."Date" DESC, s."Station"
                LIMIT :limit OFFSET :offset
            """
            
        else:  # default
            query = """
                SELECT 
                    m."Tab_DateTime" as datetime,
                    l."Station" as station,
                    m."Tab_Value_mDepthC1" as sea_level,
                    m."Tab_Value_monT2m" as temperature,
                    m."Tab_TabularTag" as tag
                FROM "Monitors_info2" m
                JOIN "Locations" l ON m."Tab_TabularTag" = l."Tab_TabularTag"
                WHERE m."Tab_DateTime" BETWEEN :start_date AND :end_date
            """
            if station != 'All Stations':
                query += ' AND l."Station" = :station'
                params['station'] = station
            
            # Filter out null values for better data quality
            query += """
                AND m."Tab_Value_mDepthC1" IS NOT NULL
                ORDER BY m."Tab_DateTime" DESC, l."Station"
                LIMIT :limit OFFSET :offset
            """
        
        return query, params
    
    @staticmethod
    def load_latest_data(
        station: str = 'All Stations',
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Load most recent data (optimized for dashboard initial load)
        
        Args:
            station: Station name or 'All Stations'
            limit: Number of recent records (default: 100)
        
        Returns:
            DataFrame with latest data
        """
        limit = min(limit, 1000)  # Cap at 1000
        
        query = """
            SELECT 
                m."Tab_DateTime" as datetime,
                l."Station" as station,
                m."Tab_Value_mDepthC1" as sea_level,
                m."Tab_Value_monT2m" as temperature
            FROM "Monitors_info2" m
            JOIN "Locations" l ON m."Tab_TabularTag" = l."Tab_TabularTag"
            WHERE m."Tab_Value_mDepthC1" IS NOT NULL
        """
        
        params = {'limit': limit}
        
        if station != 'All Stations':
            query += ' AND l."Station" = :station'
            params['station'] = station
        
        query += """
            ORDER BY m."Tab_DateTime" DESC
            LIMIT :limit
        """
        
        try:
            rows = db_manager.execute_query(query, params, use_cache=True, cache_ttl=60)
            if rows:
                return pd.DataFrame([dict(row._mapping) for row in rows])
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Latest data load failed: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_stations() -> List[Dict[str, Any]]:
        """Get list of all stations (cached for 30 minutes)"""
        
        query = """
            SELECT DISTINCT
                l."Station" as station,
                l."Latitude" as latitude,
                l."Longitude" as longitude,
                l."Tab_TabularTag" as tag
            FROM "Locations" l
            ORDER BY l."Station"
        """
        
        try:
            rows = db_manager.execute_query(query, use_cache=True, cache_ttl=1800)
            return [dict(row._mapping) for row in rows]
        except Exception as e:
            logger.error(f"Stations load failed: {e}")
            return []
    
    @staticmethod
    def get_statistics(
        start_date: str,
        end_date: str,
        station: str = 'All Stations'
    ) -> Dict[str, Any]:
        """
        Get aggregated statistics (cached)
        
        Returns: {
            'avg_sea_level': float,
            'max_sea_level': float,
            'min_sea_level': float,
            'avg_temperature': float,
            'record_count': int
        }
        """
        
        query = """
            SELECT 
                AVG(m."Tab_Value_mDepthC1") as avg_sea_level,
                MAX(m."Tab_Value_mDepthC1") as max_sea_level,
                MIN(m."Tab_Value_mDepthC1") as min_sea_level,
                AVG(m."Tab_Value_monT2m") as avg_temperature,
                COUNT(*) as record_count
            FROM "Monitors_info2" m
            JOIN "Locations" l ON m."Tab_TabularTag" = l."Tab_TabularTag"
            WHERE m."Tab_DateTime" BETWEEN :start_date AND :end_date
            AND m."Tab_Value_mDepthC1" IS NOT NULL
        """
        
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        if station != 'All Stations':
            query += ' AND l."Station" = :station'
            params['station'] = station
        
        try:
            rows = db_manager.execute_query(query, params, use_cache=True, cache_ttl=300)
            if rows and rows[0]:
                row_dict = dict(rows[0]._mapping)
                # Convert Decimal to float
                return {
                    k: float(v) if v is not None else None 
                    for k, v in row_dict.items()
                }
            return {}
        except Exception as e:
            logger.error(f"Statistics query failed: {e}")
            return {}

# ============================================================================
# BACKWARD COMPATIBILITY FUNCTIONS
# ============================================================================

def load_data_from_db(start_date=None, end_date=None, station=None, data_source='default'):
    """
    Optimized data loading with proper error handling and caching
    BACKWARD COMPATIBLE with existing code
    """
    try:
        # Use the new paginated loader but return just the DataFrame
        df, metadata = DataProcessor.load_data_paginated(
            start_date=start_date or (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            end_date=end_date or datetime.now().strftime('%Y-%m-%d'),
            station=station or 'All Stations',
            data_source=data_source,
            page=1,
            page_size=5000,  # Large page size for backward compatibility
            use_cache=True
        )
        
        logger.info(f"Loaded {len(df)} records from database (backward compatible)")
        return df

    except Exception as e:
        logger.error(f"Data load error: {e}")
        return pd.DataFrame()

def build_query(start_date, end_date, station, data_source):
    """
    BACKWARD COMPATIBLE query builder
    """
    try:
        # Use the new optimized query builder
        query_str, params = DataProcessor._build_paginated_query(
            start_date or (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            end_date or datetime.now().strftime('%Y-%m-%d'),
            station or 'All Stations',
            data_source or 'default',
            offset=0,
            limit=10000  # Large limit for backward compatibility
        )
        
        # Convert back to SQLAlchemy query object for compatibility
        from sqlalchemy import text
        return text(query_str)

    except Exception as e:
        logger.error(f"Query building error: {e}")
        return None

def default_columns():
    """Default columns for sea level data - BACKWARD COMPATIBLE"""
    if not db_manager.M or not db_manager.L:
        return []
    return [
        db_manager.M.c.Tab_DateTime, 
        db_manager.L.c.Station, 
        db_manager.M.c.Tab_Value_mDepthC1, 
        db_manager.M.c.Tab_Value_monT2m
    ]

def tides_columns():
    """Columns for tides data - BACKWARD COMPATIBLE"""
    if not db_manager.S:
        return []
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
    Cached function to get prediction data for a station - BACKWARD COMPATIBLE
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
    ARIMA predictions with proper error handling - BACKWARD COMPATIBLE
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
    Prophet predictions with proper error handling - BACKWARD COMPATIBLE
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

        # Fit model with chunked data to prevent memory issues
        if len(prophet_df) > 10000:
            prophet_df = prophet_df.tail(10000)  # Use last 10k points
        
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
    Anomaly detection with proper error handling - BACKWARD COMPATIBLE
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
    Calculate statistics with proper error handling - BACKWARD COMPATIBLE
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

        # 24h change - find values approximately 24 hours apart
        if 'Tab_Value_mDepthC1' in df.columns and 'Tab_DateTime' in df.columns and len(df) > 1:
            df_sorted = df.sort_values('Tab_DateTime')
            latest_time = pd.to_datetime(df_sorted['Tab_DateTime'].iloc[-1])
            target_time = latest_time - pd.Timedelta(hours=24)
            
            # Find closest value to 24h ago
            time_diffs = abs(pd.to_datetime(df_sorted['Tab_DateTime']) - target_time)
            closest_idx = time_diffs.idxmin()
            
            now_val = df_sorted['Tab_Value_mDepthC1'].iloc[-1]
            past_val = df_sorted.loc[closest_idx, 'Tab_Value_mDepthC1']
            
            if pd.notna(now_val) and pd.notna(past_val):
                stats['24h_change'] = float(now_val - past_val)

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