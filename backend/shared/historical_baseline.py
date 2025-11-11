"""
Historical Baseline Fallback Module
Provides smarter baseline calculation when same-timestamp southern data is missing.
"""

import pandas as pd 
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class HistoricalBaselineProvider:
    """
    Provides historical baseline values when current timestamp lacks southern stations.
    Uses recent history and weighted averaging.
    """
    
    def __init__(self, lookback_hours: int = 72):
        """
        Initialize provider with lookback window.
        
        Args:
            lookback_hours: How far back to look for baseline values
        """
        self.lookback_hours = lookback_hours
    
    def get_historical_baseline(self, df: pd.DataFrame, 
                              timestamp: pd.Timestamp,
                              min_sources: int = 2) -> Tuple[Optional[float], int]:
        """
        Calculate historical baseline for a timestamp when current data is insufficient.
        
        Args:
            df: DataFrame with historical data (must include earlier timestamps)
            timestamp: The timestamp needing a baseline value
            min_sources: Minimum number of southern stations needed
            
        Returns:
            Tuple of (baseline_value, num_sources) or (None, 0) if no valid baseline
        """
        if df.empty:
            return None, 0
            
        # Ensure DataFrame has required columns
        required_cols = ['Tab_DateTime', 'Station', 'Tab_Value_mDepthC1']
        if not all(col in df.columns for col in required_cols):
            logger.error(f"Missing required columns. Need: {required_cols}")
            return None, 0
            
        # Convert timestamp to pandas timestamp if needed
        if not isinstance(timestamp, pd.Timestamp):
            timestamp = pd.to_datetime(timestamp)
            
        # Calculate lookback window
        start_time = timestamp - pd.Timedelta(hours=self.lookback_hours)
        
        # Filter to southern stations in lookback window
        southern_stations = ['Yafo', 'Ashdod', 'Ashkelon']
        historical_data = df[
            (df['Tab_DateTime'] >= start_time) & 
            (df['Tab_DateTime'] < timestamp) & 
            (df['Station'].isin(southern_stations))
        ].copy()
        
        if len(historical_data) < min_sources:
            return None, 0
            
        # Group by station and get last known value for each
        last_values = historical_data.groupby('Station')['Tab_Value_mDepthC1'].last()
        
        if len(last_values) < min_sources:
            return None, 0
            
        # Weight more recent values higher
        time_weights = historical_data.groupby('Station').apply(
            lambda x: np.exp(-(timestamp - x['Tab_DateTime'].max()).total_seconds() / 3600)
        )
        
        # Calculate weighted average baseline
        weighted_values = last_values * time_weights
        historical_baseline = weighted_values.sum() / time_weights.sum()
        
        return historical_baseline, len(last_values)
    
    def enhance_baseline_calculation(self, df: pd.DataFrame,
                                   current_baseline: Optional[float],
                                   current_sources: int,
                                   timestamp: pd.Timestamp,
                                   min_sources: int = 2) -> Tuple[Optional[float], int]:
        """
        Enhance baseline calculation by falling back to historical when needed.
        
        Args:
            df: DataFrame with historical data
            current_baseline: The current-timestamp baseline (if any)
            current_sources: Number of sources used for current baseline
            timestamp: The timestamp being processed
            min_sources: Minimum number of sources needed for valid baseline
            
        Returns:
            Tuple of (best_baseline, num_sources)
        """
        # If current baseline is good, use it
        if current_baseline is not None and current_sources >= min_sources:
            return current_baseline, current_sources
            
        # Try historical fallback
        historical_baseline, historical_sources = self.get_historical_baseline(
            df, timestamp, min_sources
        )
        
        if historical_baseline is not None:
            logger.info(
                f"Using historical baseline {historical_baseline:.3f}m from "
                f"{historical_sources} sources (last {self.lookback_hours}h)"
            )
            return historical_baseline, historical_sources
            
        # If both current and historical fail, return best available
        if current_baseline is not None:
            return current_baseline, current_sources
            
        return None, 0

# Example usage
if __name__ == "__main__":
    # Sample data with missing southern stations
    data = pd.DataFrame({
        'Tab_DateTime': pd.date_range('2025-11-06', periods=24, freq='H'),
        'Station': ['Yafo', 'Ashdod', 'Haifa'] * 8,
        'Tab_Value_mDepthC1': [0.320, 0.318, 0.663] * 8
    })
    
    provider = HistoricalBaselineProvider(lookback_hours=24)
    
    # Test historical baseline
    timestamp = pd.Timestamp('2025-11-06 12:00:00')
    baseline, sources = provider.enhance_baseline_calculation(
        df=data,
        current_baseline=None,  # Simulate missing current baseline
        current_sources=1,      # Only one southern station available
        timestamp=timestamp
    )
    
    print(f"\nHistorical Baseline Test")
    print(f"Timestamp: {timestamp}")
    print(f"Baseline: {baseline:.3f}m from {sources} sources")