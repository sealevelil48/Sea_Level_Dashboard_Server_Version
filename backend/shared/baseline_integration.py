"""
Baseline Integration Module
==========================
Integrates Southern Baseline Rules with existing data processing pipeline
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from .southern_baseline_rules import SouthernBaselineRules
    BASELINE_RULES_AVAILABLE = True
except ImportError:
    try:
        from southern_baseline_rules import SouthernBaselineRules
        BASELINE_RULES_AVAILABLE = True
    except ImportError:
        logger.warning("Southern Baseline Rules not available")
        BASELINE_RULES_AVAILABLE = False


class BaselineIntegratedProcessor:
    """Integrates Southern Baseline Rules with existing data processing"""
    
    def __init__(self, use_baseline_rules: bool = True):
        self.use_baseline_rules = use_baseline_rules and BASELINE_RULES_AVAILABLE
        self.rules_engine = SouthernBaselineRules() if self.use_baseline_rules else None
        
        if not self.use_baseline_rules:
            logger.warning("Running without Southern Baseline Rules")
    
    def process_data(self, df: pd.DataFrame, apply_corrections: bool = False) -> pd.DataFrame:
        """Process data with optional baseline rule application"""
        if df.empty:
            return df
        
        # Ensure required columns exist
        required_cols = ['Tab_DateTime', 'Station', 'Tab_Value_mDepthC1']
        if not all(col in df.columns for col in required_cols):
            logger.error(f"Missing required columns. Need: {required_cols}")
            return df
        
        # Apply baseline rules if enabled
        if self.use_baseline_rules:
            try:
                df = self.rules_engine.process_dataframe(df)
                
                # Optionally replace original values with corrections
                if apply_corrections:
                    df['Tab_Value_mDepthC1_Original'] = df['Tab_Value_mDepthC1']
                    df['Tab_Value_mDepthC1'] = df['Corrected_Value']
                    logger.info("Applied baseline corrections to data")
                
            except Exception as e:
                logger.error(f"Failed to apply baseline rules: {e}")
        else:
            # Fallback: add default columns
            df['Is_Outlier'] = False
            df['Corrected_Value'] = df['Tab_Value_mDepthC1']
            df['anomaly'] = 0
        
        return df
    
    def prepare_ml_training_data(self, df: pd.DataFrame, use_corrected: bool = True) -> pd.DataFrame:
        """Prepare data for ML model training with optional corrections"""
        if df.empty:
            return df
        
        # Apply baseline rules
        if self.use_baseline_rules:
            df = self.rules_engine.process_dataframe(df)
        
        # Decide which values to use
        if use_corrected and 'Corrected_Value' in df.columns:
            df['ML_Training_Value'] = df['Corrected_Value']
            logger.info("Using corrected values for ML training")
        else:
            df['ML_Training_Value'] = df['Tab_Value_mDepthC1']
            logger.info("Using original values for ML training")
        
        # Remove outliers from training data
        if 'Is_Outlier' in df.columns:
            df_clean = df[df['Is_Outlier'] == False].copy()
            removed = len(df) - len(df_clean)
            if removed > 0:
                logger.info(f"Removed {removed} outliers from ML training data")
            return df_clean
        
        return df
    
    def detect_anomalies_with_rules(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enhanced anomaly detection using baseline rules"""
        if not self.use_baseline_rules or df.empty:
            # Fallback to simple method
            df['anomaly'] = 0
            return df
        
        # Debug: Log input data
        logger.info(f"Processing {len(df)} records for anomaly detection")
        ashkelon_count = len(df[df['Station'] == 'Ashkelon'])
        logger.info(f"  Ashkelon records: {ashkelon_count}")
        
        # Use baseline rules for detection
        df = self.rules_engine.process_dataframe(df)
        
        # Add asynchronous outlier detection for Ashkelon
        async_outliers = self.rules_engine.detect_asynchronous_outliers(df)
        if not async_outliers.empty:
            # Merge async outliers with main results
            df = pd.concat([df, async_outliers], ignore_index=True)
            logger.info(f"Added {len(async_outliers)} asynchronous outliers (Ashkelon)")
        
        # Debug: Log outliers found
        outliers = df[df['Is_Outlier'] == True]
        logger.info(f"Enhanced rules detected {len(outliers)} outliers")
        for _, row in outliers.iterrows():
            excluded_flag = row.get('Excluded_From_Baseline', False)
            logger.info(f"  OUTLIER: {row['Station']} = {row['Tab_Value_mDepthC1']}m (excluded: {excluded_flag})")
        
        # Mark anomalies based on Is_Outlier flag
        if 'Is_Outlier' in df.columns:
            df['anomaly'] = df['Is_Outlier'].apply(lambda x: -1 if x else 0)
        else:
            df['anomaly'] = 0
        
        return df
    
    def get_correction_suggestions(self, df: pd.DataFrame) -> List[Dict]:
        """Get correction suggestions for all outliers"""
        if not self.use_baseline_rules or df.empty:
            return []
        
        suggestions = []
        
        # Group by timestamp to get baseline per timestamp
        for timestamp, group in df.groupby('Tab_DateTime'):
            baseline_value = group['Southern_Baseline'].iloc[0] if 'Southern_Baseline' in group.columns else None
            
            if pd.isna(baseline_value):
                continue
            
            # Check each station
            for _, row in group.iterrows():
                if row.get('Is_Outlier', False):
                    suggestion = self.rules_engine.get_correction_suggestion(
                        station=row['Station'],
                        actual_value=row['Tab_Value_mDepthC1'],
                        baseline=baseline_value
                    )
                    suggestion['timestamp'] = timestamp
                    suggestions.append(suggestion)
        
        return suggestions
    
    def generate_validation_report(self, df: pd.DataFrame) -> Dict:
        """Generate comprehensive validation report"""
        if not self.use_baseline_rules:
            return {
                'error': 'Baseline rules not available',
                'timestamp': datetime.now().isoformat()
            }
        
        return self.rules_engine.validate_multi_station_data(df)


# API endpoint helpers
def get_outliers_api(df: pd.DataFrame) -> Dict:
    """Get outlier information formatted for API response with Enhanced Validation"""
    if df.empty:
        return {
            'total_records': 0,
            'outliers_detected': 0,
            'outlier_percentage': 0,
            'validation': {
                'total_validations': 0,
                'total_exclusions': 0,
                'exclusion_rate': 0,
                'outliers_detected': 0,
                'baseline_calculations': 0
            },
            'outliers': [],
            'timestamp': datetime.now().isoformat()
        }
    
    # Limit processing for performance
    if len(df) > 3000:
        logger.warning(f"Large dataset for outlier API ({len(df)} records), limiting to 3000 most recent")
        df = df.sort_values('Tab_DateTime').tail(3000)
    
    processor = BaselineIntegratedProcessor()
    df_processed = processor.detect_anomalies_with_rules(df)
    
    # Get validation statistics from the enhanced rules engine
    validation_stats = {
        'total_validations': 0,
        'total_exclusions': 0,
        'exclusion_rate': 0,
        'outliers_detected': 0,
        'baseline_calculations': 0
    }
    
    if processor.use_baseline_rules and processor.rules_engine:
        validation_stats = processor.rules_engine.get_validation_stats()
        logger.info(f"Enhanced validation stats: {validation_stats}")
    
    outliers = df_processed[df_processed.get('Is_Outlier', False) == True]
    
    # Limit outliers returned to prevent response size issues
    if len(outliers) > 500:
        logger.warning(f"Too many outliers ({len(outliers)}), limiting to 500 most recent")
        outliers = outliers.sort_values('Tab_DateTime').tail(500)
    
    # Convert datetime columns to strings for JSON serialization
    outliers_dict = outliers.copy()
    for col in outliers_dict.columns:
        if outliers_dict[col].dtype == 'datetime64[ns]' or 'datetime' in str(outliers_dict[col].dtype).lower():
            outliers_dict[col] = outliers_dict[col].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    return {
        'total_records': len(df_processed),
        'outliers_detected': len(outliers),
        'outlier_percentage': round(len(outliers) / len(df_processed) * 100, 2) if len(df_processed) > 0 else 0,
        'validation': validation_stats,  # ✨ NEW: Enhanced validation statistics
        'outliers': outliers_dict.to_dict('records'),
        'timestamp': datetime.now().isoformat()
    }


def get_corrections_api(df: pd.DataFrame) -> Dict:
    """Get correction suggestions formatted for API response"""
    processor = BaselineIntegratedProcessor()
    df_processed = processor.detect_anomalies_with_rules(df)
    suggestions = processor.get_correction_suggestions(df_processed)
    
    # Convert any datetime objects in suggestions to strings
    for suggestion in suggestions:
        if 'timestamp' in suggestion and hasattr(suggestion['timestamp'], 'strftime'):
            suggestion['timestamp'] = suggestion['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    
    return {
        'total_suggestions': len(suggestions),
        'suggestions': suggestions,
        'timestamp': datetime.now().isoformat()
    }


# Integration helper functions for existing code
def integrate_with_kalman_filter(df: pd.DataFrame, use_corrections: bool = True) -> pd.DataFrame:
    """Prepare data for Kalman filter with baseline corrections"""
    processor = BaselineIntegratedProcessor()
    df_clean = processor.prepare_ml_training_data(df, use_corrected=use_corrections)
    
    # Kalman filter expects specific column names
    if 'ML_Training_Value' in df_clean.columns:
        df_clean['Tab_Value_mDepthC1'] = df_clean['ML_Training_Value']
    
    return df_clean


def integrate_with_arima(df: pd.DataFrame, use_corrections: bool = True) -> pd.DataFrame:
    """Prepare data for ARIMA with baseline corrections"""
    processor = BaselineIntegratedProcessor()
    df_clean = processor.prepare_ml_training_data(df, use_corrected=use_corrections)
    
    # ARIMA works better with clean, corrected data
    if 'ML_Training_Value' in df_clean.columns:
        df_clean['Tab_Value_mDepthC1'] = df_clean['ML_Training_Value']
    
    return df_clean


def enhance_dashboard_data(df: pd.DataFrame, include_corrections: bool = True) -> pd.DataFrame:
    """Enhance dashboard data with baseline rule information"""
    processor = BaselineIntegratedProcessor()
    df_enhanced = processor.process_data(df, apply_corrections=False)
    
    if not include_corrections:
        # Remove correction columns for simpler display
        cols_to_drop = [col for col in df_enhanced.columns 
                       if any(x in col for x in ['Expected', 'Corrected', 'Deviation'])]
        df_enhanced = df_enhanced.drop(columns=cols_to_drop, errors='ignore')
    
    return df_enhanced


# Example usage
if __name__ == "__main__":
    # Test integration
    sample_data = pd.DataFrame({
        'Tab_DateTime': ['2025-11-06 00:00:00'] * 5,
        'Station': ['Yafo', 'Ashdod', 'Ashkelon', 'Haifa', 'Acre'],
        'Tab_Value_mDepthC1': [0.320, 0.318, 0.315, 0.663, 0.395]
    })
    
    processor = BaselineIntegratedProcessor()
    
    print("\n=== Baseline Integration Test ===")
    result = processor.process_data(sample_data)
    print(result[['Station', 'Tab_Value_mDepthC1', 'Expected_Value', 
                  'Is_Outlier', 'Corrected_Value']])
    
    print("\n=== Correction Suggestions ===")
    suggestions = processor.get_correction_suggestions(result)
    for s in suggestions:
        print(f"{s['station']}: {s['message']}")
    
    print("\n=== Validation Report ===")
    report = processor.generate_validation_report(sample_data)
    print(f"Total records: {report['total_records']}")
    print(f"Outliers by station: {report['outliers_by_station']}")


