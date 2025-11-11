"""
Southern Baseline Rules for Sea Level Monitoring - ENHANCED VERSION
====================================================================
Implements the official Israeli sea level monitoring rules with enhanced validation:

ENHANCEMENT: Southern Station Cross-Validation
- Validates southern stations against each other BEFORE baseline calculation
- Excludes stations that deviate >5cm from other southern stations
- Ensures robust baseline for all downstream calculations

Rules:
- Southern gauges (Yafo, Ashdod, Ashkelon) show the same average level (baseline)
- Haifa gauge: 4 cm higher than southern baseline
- Acre gauge: 8 cm higher than southern baseline
- Eilat gauge: 17 cm higher than southern baseline

This module provides:
1. Southern station cross-validation (NEW!)
2. Baseline calculation from validated southern gauges
3. Outlier detection based on expected offsets
4. Correction suggestions for outliers
5. Integration with ML models
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class SouthernBaselineRules:
    """
    Implements the Southern Baseline Rules for sea level monitoring
    with enhanced cross-validation of southern stations
    """
    
    # Station configurations
    SOUTHERN_STATIONS = ['Yafo', 'Ashdod', 'Ashkelon']
    NORTHERN_STATIONS = ['Haifa', 'Acre']
    ALL_STATIONS = SOUTHERN_STATIONS + NORTHERN_STATIONS + ['Eilat']
    
    # Expected offsets from southern baseline (in meters)
    # Updated based on actual MSL differences: Eilat +28.16cm vs expected +17cm
    STATION_OFFSETS = {
        'Yafo': 0.00,
        'Ashdod': 0.00,
        'Ashkelon': 0.00,
        'Haifa': 0.04,
        'Acre': 0.08,
        'Eilat': 0.28  # Updated from 0.17 to 0.28 based on actual MSL difference
    }
    
    # Tolerance levels for outlier detection (in meters)
    TOLERANCE = {
        'southern': 0.03,  # 3cm for southern gauges
        'northern': 0.05,  # 5cm for northern gauges
        'eilat': 0.06      # 6cm for Eilat
    }
    
    # ✨ NEW: Validation threshold for southern station cross-validation
    SOUTHERN_VALIDATION_THRESHOLD = 0.05  # 5cm = 0.05m
    
    def __init__(self):
        """Initialize the rules engine"""
        self.stats = {
            'total_records': 0,
            'outliers_detected': 0,
            'corrections_applied': 0,
            'baseline_calculations': 0,
            'southern_validations': 0,
            'southern_exclusions': 0
        }
    
    def validate_southern_stations(self, row: pd.Series, 
                                   exclude_station: Optional[str] = None) -> Tuple[List[str], List[float]]:
        """
        ✨ NEW METHOD: Validate southern stations against each other
        
        This method ensures that southern stations are consistent with each other
        before using them for baseline calculation. A station is only included if
        it's within 5cm of at least one other southern station.
        
        Args:
            row: DataFrame row with station columns
            exclude_station: Optional station to explicitly exclude
            
        Returns:
            Tuple of (valid_station_names, valid_station_values)
            
        Example:
            Input: Yafo=0.320m, Ashdod=0.318m, Ashkelon=0.380m
            Process:
                - Ashkelon (0.380) differs from Yafo (0.320) by 0.06m > 0.05m threshold
                - Ashkelon (0.380) differs from Ashdod (0.318) by 0.062m > 0.05m threshold
                - Ashkelon is excluded
            Output: (['Yafo', 'Ashdod'], [0.320, 0.318])
        """
        self.stats['southern_validations'] += 1
        
        # Step 1: Collect all available southern station data
        station_data = {}
        for station in self.SOUTHERN_STATIONS:
            # Skip explicitly excluded station
            if exclude_station and station == exclude_station:
                logger.debug(f"⊘ Skipping {station} (explicitly excluded)")
                continue
                
            # Collect station value if available
            if station in row.index and pd.notna(row[station]):
                value = float(row[station])
                station_data[station] = value
                logger.debug(f"  {station}: {value:.3f}m")
        
        # If we have 0 or 1 stations, no validation needed
        if len(station_data) <= 1:
            valid_stations = list(station_data.keys())
            valid_values = list(station_data.values())
            return valid_stations, valid_values
        
        # Step 2: Validate each station against all others
        valid_stations = []
        valid_values = []
        excluded_stations = []
        
        for station, value in station_data.items():
            # Check if this station is within 5cm of ANY other station
            agreement_count = 0
            
            for other_station, other_value in station_data.items():
                if station == other_station:
                    continue
                    
                deviation = abs(value - other_value)
                
                if deviation <= self.SOUTHERN_VALIDATION_THRESHOLD:
                    agreement_count += 1
                    logger.debug(f"  ✓ {station} ({value:.3f}m) within 5cm of {other_station} ({other_value:.3f}m) - deviation: {deviation*100:.1f}cm")
                else:
                    logger.debug(f"  ✗ {station} ({value:.3f}m) exceeds 5cm from {other_station} ({other_value:.3f}m) - deviation: {deviation*100:.1f}cm")
            
            # Require majority agreement (at least half of other stations)
            required_agreements = max(1, len(station_data) // 2)
            is_valid = agreement_count >= required_agreements
            
            if is_valid:
                valid_stations.append(station)
                valid_values.append(value)
            else:
                excluded_stations.append(station)
                self.stats['southern_exclusions'] += 1
                logger.warning(f"⚠️  {station} excluded from baseline: deviates >{self.SOUTHERN_VALIDATION_THRESHOLD*100:.0f}cm from all other southern stations (value: {value:.3f}m)")
        
        # Log results
        if excluded_stations:
            logger.info(f"🔍 Southern validation: Using {valid_stations} (excluded: {excluded_stations})")
        else:
            logger.debug(f"✅ All southern stations validated: {valid_stations}")
        
        return valid_stations, valid_values
    
    def detect_asynchronous_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect outliers in asynchronous data (like Ashkelon) using time windows
        """
        results = []
        ashkelon_data = df[df['Station'] == 'Ashkelon'].copy()
        
        for _, ashkelon_row in ashkelon_data.iterrows():
            timestamp = ashkelon_row['Tab_DateTime']
            ashkelon_value = ashkelon_row['Tab_Value_mDepthC1']
            
            # Find nearby southern station data (within 1 hour)
            target_time = pd.to_datetime(timestamp)
            window_start = target_time - pd.Timedelta(hours=1)
            window_end = target_time + pd.Timedelta(hours=1)
            
            # Ensure datetime column is properly converted
            df_copy = df.copy()
            df_copy['Tab_DateTime'] = pd.to_datetime(df_copy['Tab_DateTime'])
            
            nearby_data = df_copy[
                (df_copy['Tab_DateTime'] >= window_start) & 
                (df_copy['Tab_DateTime'] <= window_end) &
                (df_copy['Station'].isin(['Yafo', 'Ashdod']))
            ]
            
            if len(nearby_data) >= 2:
                # Calculate baseline from nearby data
                baseline_values = []
                for station in ['Yafo', 'Ashdod']:
                    station_data = nearby_data[nearby_data['Station'] == station]
                    if not station_data.empty:
                        baseline_values.append(station_data['Tab_Value_mDepthC1'].mean())
                
                if len(baseline_values) >= 2:
                    baseline = np.mean(baseline_values)
                    expected_value = baseline  # Ashkelon should match southern baseline
                    deviation = abs(ashkelon_value - expected_value)
                    is_outlier = deviation > self.SOUTHERN_VALIDATION_THRESHOLD
                    
                    if is_outlier:
                        self.stats['outliers_detected'] += 1
                        logger.info(f"🔴 OUTLIER: Ashkelon = {ashkelon_value:.3f}m (expected {expected_value:.3f}m, deviation {deviation*100:.1f}cm) - ASYNC DETECTION")
                    
                    results.append({
                        'Tab_DateTime': timestamp,
                        'Station': 'Ashkelon',
                        'Tab_Value_mDepthC1': ashkelon_value,
                        'Expected_Value': expected_value,
                        'Baseline': baseline,
                        'Deviation': deviation,
                        'Is_Outlier': is_outlier,
                        'Excluded_From_Baseline': is_outlier
                    })
        
        return pd.DataFrame(results)
    
    def calculate_southern_baseline(self, row: pd.Series, 
                                    exclude_station: Optional[str] = None) -> Tuple[Optional[float], int, List[str]]:
        """
        Calculate the southern baseline from validated southern gauges
        
        ENHANCEMENT: Now validates southern stations against each other FIRST
        
        Args:
            row: DataFrame row with station columns
            exclude_station: Optional station to exclude (e.g., for sensitivity analysis)
            
        Returns:
            Tuple of (baseline_value, num_sources, source_stations)
            
        Process:
            1. Validate southern stations against each other (NEW!)
            2. Apply exclude_station filter if specified
            3. Calculate baseline from valid stations
            4. Use median for 3+ stations, mean for 2 stations
            
        Example with your problematic data:
            Input: Yafo=0.320m, Ashdod=0.318m, Ashkelon=0.380m
            Step 1 - Validation: Ashkelon excluded (deviates >5cm)
            Step 2 - Stations used: Yafo, Ashdod
            Step 3 - Baseline: (0.320 + 0.318) / 2 = 0.319m
            Output: (0.319, 2, ['Yafo', 'Ashdod'])
        """
        # ✨ Step 1: Validate southern stations against each other
        valid_stations, valid_values = self.validate_southern_stations(row, exclude_station)
        
        if not valid_values:
            logger.debug("No valid southern stations available for baseline")
            return None, 0, []
        
        # ✨ Step 2: Calculate baseline from validated stations
        if len(valid_values) >= 3:
            # Use median for 3+ stations (more robust to outliers)
            baseline = np.median(valid_values)
            method = "median"
        else:
            # Use mean for 1-2 stations
            baseline = np.mean(valid_values)
            method = "mean"
        
        self.stats['baseline_calculations'] += 1
        
        logger.debug(f"📊 Baseline: {baseline:.3f}m from {len(valid_values)} stations ({method}): {valid_stations}")
        
        return baseline, len(valid_values), valid_stations
    
    def get_expected_value(self, station: str, baseline: float) -> float:
        """
        Get expected sea level for a station based on southern baseline
        
        Args:
            station: Station name
            baseline: Southern baseline value
            
        Returns:
            Expected sea level value
        """
        if station not in self.STATION_OFFSETS:
            logger.warning(f"Unknown station: {station}")
            return baseline
        
        return baseline + self.STATION_OFFSETS[station]
    
    def get_tolerance(self, station: str) -> float:
        """
        Get outlier detection tolerance for a station
        
        Args:
            station: Station name
            
        Returns:
            Tolerance in meters
        """
        if station in self.SOUTHERN_STATIONS:
            return self.TOLERANCE['southern']
        elif station == 'Eilat':
            return self.TOLERANCE['eilat']
        else:  # Northern stations
            return self.TOLERANCE['northern']
    
    def detect_outlier(self, station: str, actual_value: float, 
                      expected_value: float) -> Tuple[bool, float]:
        """
        Detect if a station reading is an outlier
        
        Args:
            station: Station name
            actual_value: Measured value
            expected_value: Expected value from baseline
            
        Returns:
            Tuple of (is_outlier, deviation)
        """
        if pd.isna(actual_value) or pd.isna(expected_value):
            return False, 0.0
        
        deviation = abs(actual_value - expected_value)
        tolerance = self.get_tolerance(station)
        is_outlier = deviation > tolerance
        
        if is_outlier:
            self.stats['outliers_detected'] += 1
        
        return is_outlier, deviation
    
    def process_row_with_validation(self, row: pd.Series) -> Dict:
        """
        Process a single row/timestamp with enhanced validation
        
        This is the main processing method that:
        1. Validates southern stations
        2. Calculates baseline
        3. Detects outliers for all stations
        4. Flags excluded stations as outliers
        
        Args:
            row: DataFrame row with station readings
            
        Returns:
            Dictionary with results for each station
        """
        results = {}
        
        # Get validation results to identify excluded stations
        valid_stations, valid_values = self.validate_southern_stations(row)
        excluded_southern_stations = [s for s in self.SOUTHERN_STATIONS 
                                    if s in row.index and pd.notna(row[s]) and s not in valid_stations]
        
        # Calculate validated baseline
        baseline, num_sources, source_stations = self.calculate_southern_baseline(row)
        
        if baseline is None:
            logger.warning("Cannot process row: no valid baseline available")
            return results
        
        # Process each station
        for station in self.ALL_STATIONS:
            if station not in row.index or pd.isna(row[station]):
                continue
            
            actual_value = float(row[station])
            expected_value = self.get_expected_value(station, baseline)
            
            # Check if this station was excluded from southern validation
            if station in excluded_southern_stations:
                # Excluded southern stations are automatically outliers
                is_outlier = True
                deviation = abs(actual_value - expected_value)
                self.stats['outliers_detected'] += 1
                logger.info(f"🔴 OUTLIER: {station} = {actual_value:.3f}m (expected {expected_value:.3f}m, deviation {deviation*100:.1f}cm) - EXCLUDED from baseline")
            else:
                # Normal outlier detection
                is_outlier, deviation = self.detect_outlier(station, actual_value, expected_value)
                if is_outlier:
                    logger.info(f"🔴 OUTLIER: {station} = {actual_value:.3f}m (expected {expected_value:.3f}m, deviation {deviation*100:.1f}cm)")
            
            results[station] = {
                'actual': actual_value,
                'expected': expected_value,
                'baseline': baseline,
                'baseline_sources': num_sources,
                'baseline_stations': source_stations,
                'deviation': deviation,
                'is_outlier': is_outlier,
                'tolerance': self.get_tolerance(station),
                'excluded_from_baseline': station in excluded_southern_stations
            }
        
        return results
    
    def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process entire dataframe with enhanced southern baseline validation
        
        Args:
            df: DataFrame with columns: Tab_DateTime, Station, Tab_Value_mDepthC1
            
        Returns:
            Enhanced DataFrame with additional columns:
                - Expected_Value: Expected value based on baseline
                - Baseline: Southern baseline value
                - Baseline_Sources: Number of stations used for baseline
                - Baseline_Stations: List of stations used
                - Deviation: Absolute deviation from expected
                - Is_Outlier: Boolean flag
                - Tolerance: Detection threshold
        """
        logger.info(f"🔄 Processing {len(df)} records with enhanced validation")
        
        # Create pivot table with stations as columns
        pivot_df = df.pivot_table(
            index='Tab_DateTime',
            columns='Station',
            values='Tab_Value_mDepthC1'
        )
        
        # Process each timestamp
        results_list = []
        
        for timestamp, row in pivot_df.iterrows():
            row_results = self.process_row_with_validation(row)
            
            # Flatten results back to long format
            for station, result in row_results.items():
                results_list.append({
                    'Tab_DateTime': timestamp,
                    'Station': station,
                    'Tab_Value_mDepthC1': result['actual'],
                    'Expected_Value': result['expected'],
                    'Baseline': result['baseline'],
                    'Baseline_Sources': result['baseline_sources'],
                    'Baseline_Stations': ', '.join(result['baseline_stations']),
                    'Deviation': result['deviation'],
                    'Is_Outlier': result['is_outlier'],
                    'Tolerance': result['tolerance'],
                    'Excluded_From_Baseline': result.get('excluded_from_baseline', False)
                })
        
        # Create results dataframe
        results_df = pd.DataFrame(results_list)
        
        # Log statistics
        outliers = results_df[results_df['Is_Outlier']].groupby('Station').size()
        logger.info(f"📊 Results: {self.stats['outliers_detected']} outliers detected")
        logger.info(f"📊 Southern validations: {self.stats['southern_validations']}, Exclusions: {self.stats['southern_exclusions']}")
        if len(outliers) > 0:
            logger.info(f"📊 Outliers by station:\n{outliers}")
        
        return results_df
    
    def get_validation_stats(self) -> Dict:
        """
        Get validation statistics
        
        Returns:
            Dictionary with validation metrics
        """
        return {
            'total_validations': self.stats['southern_validations'],
            'total_exclusions': self.stats['southern_exclusions'],
            'exclusion_rate': (
                self.stats['southern_exclusions'] / self.stats['southern_validations'] * 100
                if self.stats['southern_validations'] > 0 else 0
            ),
            'outliers_detected': self.stats['outliers_detected'],
            'baseline_calculations': self.stats['baseline_calculations']
        }


# ============================================================================
# STANDALONE TESTING - Run this file directly to test with your data
# ============================================================================

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("="*80)
    print("TESTING ENHANCED SOUTHERN BASELINE RULES")
    print("="*80)
    print()
    
    # Test Case: Your problematic Nov 6, 2025 data
    print("Test Case: November 6, 2025 - Haifa & Ashkelon Outliers")
    print("-" * 80)
    
    test_data = pd.DataFrame({
        'Tab_DateTime': ['2025-11-06 00:00:00'] * 5,
        'Station': ['Yafo', 'Ashdod', 'Ashkelon', 'Haifa', 'Acre'],
        'Tab_Value_mDepthC1': [0.320, 0.318, 0.380, 0.663, 0.395]
    })
    
    print("\nInput Data:")
    print(test_data[['Station', 'Tab_Value_mDepthC1']])
    print()
    
    # Process with enhanced rules
    rules = SouthernBaselineRules()
    results = rules.process_dataframe(test_data)
    
    print("\nResults:")
    print(results[['Station', 'Tab_Value_mDepthC1', 'Expected_Value', 'Baseline', 
                   'Baseline_Stations', 'Deviation', 'Is_Outlier']])
    
    print("\nValidation Statistics:")
    stats = rules.get_validation_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\nExpected Behavior:")
    print("  1. Ashkelon (0.380m) should be excluded from baseline calculation")
    print("     - Deviates >5cm from both Yafo (0.320m) and Ashdod (0.318m)")
    print("  2. Baseline should be calculated from Yafo + Ashdod only: 0.319m")
    print("  3. Haifa (0.663m) should be flagged as outlier")
    print("     - Expected: 0.319m + 0.04m = 0.359m")
    print("     - Actual: 0.663m")
    print("     - Deviation: 0.304m > 0.05m tolerance")
    
    print("\n" + "="*80)