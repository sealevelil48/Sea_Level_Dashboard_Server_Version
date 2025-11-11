"""Test historical baseline fallback functionality"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from shared.southern_baseline_rules import SouthernBaselineRules
from shared.historical_baseline import HistoricalBaselineProvider

def test_historical_fallback():
    # Create test data with missing stations over time
    dates = pd.date_range('2025-11-06', periods=24, freq='H')
    data = []
    
    # Add historical data (good baseline available)
    for t in dates[:-1]:  # All but last hour
        data.extend([
            {'Tab_DateTime': t, 'Station': 'Yafo', 'Tab_Value_mDepthC1': 0.320},
            {'Tab_DateTime': t, 'Station': 'Ashdod', 'Tab_Value_mDepthC1': 0.318},
            {'Tab_DateTime': t, 'Station': 'Ashkelon', 'Tab_Value_mDepthC1': 0.315}
        ])
    
    # Add current data with missing stations
    current_time = dates[-1]
    data.extend([
        {'Tab_DateTime': current_time, 'Station': 'Yafo', 'Tab_Value_mDepthC1': 0.320},  # Only one southern
        {'Tab_DateTime': current_time, 'Station': 'Haifa', 'Tab_Value_mDepthC1': 0.663}  # Test outlier
    ])
    
    df = pd.DataFrame(data)
    
    # Test with historical fallback enabled
    rules = SouthernBaselineRules(use_historical_fallback=True)
    result = rules.process_dataframe(df)
    
    # Check current timestamp results
    current_results = result[result['Tab_DateTime'] == current_time]
    
    print("\n=== Historical Baseline Fallback Test ===")
    print(f"\nTimestamp: {current_time}")
    print("\nResults with historical fallback:")
    print(current_results[['Station', 'Tab_Value_mDepthC1', 'Southern_Baseline', 
                          'Expected_Value', 'Is_Outlier', 'Corrected_Value']].to_string())
    
    # Test without historical fallback
    rules_no_fallback = SouthernBaselineRules(use_historical_fallback=False)
    result_no_fallback = rules_no_fallback.process_dataframe(df)
    current_results_no_fallback = result_no_fallback[result_no_fallback['Tab_DateTime'] == current_time]
    
    print("\nResults without historical fallback:")
    print(current_results_no_fallback[['Station', 'Tab_Value_mDepthC1', 'Southern_Baseline',
                                     'Expected_Value', 'Is_Outlier', 'Corrected_Value']].to_string())
    
    return current_results, current_results_no_fallback

if __name__ == "__main__":
    current_results, current_results_no_fallback = test_historical_fallback()