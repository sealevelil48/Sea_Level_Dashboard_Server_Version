#!/usr/bin/env python3
"""
Test Enhanced Southern Baseline Rules
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import pandas as pd
from shared.baseline_integration import get_outliers_api

def test_enhanced_rules():
    print("=" * 60)
    print("TESTING ENHANCED SOUTHERN BASELINE RULES")
    print("=" * 60)
    
    # Test Case 1: Normal data (all southern stations within 5cm)
    print("\nTest Case 1: Normal southern stations")
    normal_data = pd.DataFrame({
        'Tab_DateTime': ['2025-11-06 00:00:00'] * 6,
        'Station': ['Yafo', 'Ashdod', 'Ashkelon', 'Haifa', 'Acre', 'Eilat'],
        'Tab_Value_mDepthC1': [0.320, 0.318, 0.322, 0.360, 0.400, 0.490]
    })
    
    result1 = get_outliers_api(normal_data)
    print(f"  Total records: {result1['total_records']}")
    print(f"  Outliers detected: {result1['outliers_detected']}")
    print(f"  Validation exclusions: {result1['validation']['total_exclusions']}")
    print("  Outliers:")
    for outlier in result1['outliers']:
        excluded = outlier.get('Excluded_From_Baseline', False)
        print(f"    {outlier['Station']}: {outlier['Tab_Value_mDepthC1']}m (excluded: {excluded})")
    
    # Test Case 2: Ashkelon outlier (should be excluded)
    print("\nTest Case 2: Ashkelon as outlier (should be excluded)")
    outlier_data = pd.DataFrame({
        'Tab_DateTime': ['2025-11-06 00:00:00'] * 6,
        'Station': ['Yafo', 'Ashdod', 'Ashkelon', 'Haifa', 'Acre', 'Eilat'],
        'Tab_Value_mDepthC1': [0.320, 0.318, 0.595, 0.674, 0.401, 0.091]  # Ashkelon much higher
    })
    
    result2 = get_outliers_api(outlier_data)
    print(f"  Total records: {result2['total_records']}")
    print(f"  Outliers detected: {result2['outliers_detected']}")
    print(f"  Validation exclusions: {result2['validation']['total_exclusions']}")
    print("  Outliers:")
    for outlier in result2['outliers']:
        excluded = outlier.get('Excluded_From_Baseline', False)
        print(f"    {outlier['Station']}: {outlier['Tab_Value_mDepthC1']}m (excluded: {excluded})")
    
    # Test Case 3: Real November 6th data structure
    print("\nTest Case 3: Simulated real data structure")
    real_data = pd.DataFrame({
        'Tab_DateTime': ['2025-11-06 00:00:00'] * 5,  # No Ashkelon at this timestamp
        'Station': ['Yafo', 'Ashdod', 'Haifa', 'Acre', 'Eilat'],
        'Tab_Value_mDepthC1': [0.329, 0.321, 0.674, 0.401, 0.091]
    })
    
    result3 = get_outliers_api(real_data)
    print(f"  Total records: {result3['total_records']}")
    print(f"  Outliers detected: {result3['outliers_detected']}")
    print(f"  Validation exclusions: {result3['validation']['total_exclusions']}")
    print("  Outliers:")
    for outlier in result3['outliers']:
        excluded = outlier.get('Excluded_From_Baseline', False)
        print(f"    {outlier['Station']}: {outlier['Tab_Value_mDepthC1']}m (excluded: {excluded})")
    
    print("\n" + "=" * 60)
    print("CONCLUSION:")
    if result2['validation']['total_exclusions'] > 0:
        print("✅ Enhanced validation is working - Ashkelon excluded when it's an outlier")
    else:
        print("❌ Enhanced validation not working - Ashkelon not excluded")
    
    if result3['validation']['total_exclusions'] == 0:
        print("✅ No exclusions when Ashkelon data is missing (expected)")
    else:
        print("❌ Unexpected exclusions when Ashkelon data is missing")
    print("=" * 60)

if __name__ == "__main__":
    test_enhanced_rules()