#!/usr/bin/env python3
"""
Test Asynchronous Ashkelon Outlier Detection
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import pandas as pd
from shared.southern_baseline_rules import SouthernBaselineRules

def test_ashkelon_async():
    print("=" * 60)
    print("TESTING ASYNCHRONOUS ASHKELON DETECTION")
    print("=" * 60)
    
    # Create test data with Ashkelon at different timestamps
    test_data = pd.DataFrame({
        'Tab_DateTime': [
            '2025-11-06 10:00:00',  # Yafo, Ashdod
            '2025-11-06 10:00:00',
            '2025-11-06 10:30:00',  # Ashkelon (30 min later, high value)
            '2025-11-06 10:00:00',  # Other stations
            '2025-11-06 10:00:00',
            '2025-11-06 10:00:00'
        ],
        'Station': ['Yafo', 'Ashdod', 'Ashkelon', 'Haifa', 'Acre', 'Eilat'],
        'Tab_Value_mDepthC1': [0.320, 0.318, 1.500, 0.360, 0.400, 0.600]  # Ashkelon very high
    })
    
    print("Test data:")
    for _, row in test_data.iterrows():
        print(f"  {row['Station']}: {row['Tab_Value_mDepthC1']}m at {row['Tab_DateTime']}")
    
    # Test asynchronous detection
    rules = SouthernBaselineRules()
    async_results = rules.detect_asynchronous_outliers(test_data)
    
    print(f"\nAsynchronous detection results:")
    print(f"  Records processed: {len(async_results)}")
    
    if not async_results.empty:
        for _, row in async_results.iterrows():
            print(f"  {row['Station']}: {row['Tab_Value_mDepthC1']}m")
            print(f"    Expected: {row['Expected_Value']:.3f}m")
            print(f"    Deviation: {row['Deviation']*100:.1f}cm")
            print(f"    Is Outlier: {row['Is_Outlier']}")
            print(f"    Excluded: {row['Excluded_From_Baseline']}")
    else:
        print("  No asynchronous outliers detected")
    
    print("=" * 60)

    # --- Automated Assertions (for CI/CD) ---
    # 1) Results must not be empty (we expect at least Ashkelon)
    assert not async_results.empty, "Asynchronous results should not be empty"

    # 2) There must be a row for Station 'Ashkelon'
    assert 'Ashkelon' in async_results['Station'].values, "Ashkelon must be present in detection results"

    # 3) Ashkelon row must be flagged as an outlier
    ashkelon_row = async_results[async_results['Station'] == 'Ashkelon'].iloc[0]
    assert bool(ashkelon_row.get('Is_Outlier', False)) is True, "Ashkelon should be marked as Is_Outlier == True"

    # 4) Optional: Excluded_From_Baseline should be False
    if 'Excluded_From_Baseline' in ashkelon_row:
        assert bool(ashkelon_row['Excluded_From_Baseline']) is False, "Ashkelon should not be excluded from baseline"

    # 5) Optional: Verify Deviation and Expected_Value are numeric and present
    if 'Deviation' in ashkelon_row:
        assert pd.notna(ashkelon_row['Deviation']), "Deviation should be numeric"
        assert isinstance(ashkelon_row['Deviation'], (float, int)), "Deviation must be numeric type"
    if 'Expected_Value' in ashkelon_row:
        assert pd.notna(ashkelon_row['Expected_Value']), "Expected_Value should be numeric"
        assert isinstance(ashkelon_row['Expected_Value'], (float, int)), "Expected_Value must be numeric type"

    print("✓ All assertions passed!")

if __name__ == "__main__":
    test_ashkelon_async()