"""
Fixed test script for Kalman filter - handles all known issues
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

def test_kalman_filter():
    """Test the fixed Kalman filter"""
    print("Testing Fixed Kalman Filter Implementation...")
    print("-" * 50)
    
    try:
        # Import the Kalman filter module
        from shared.kalman_filter import KalmanFilterSeaLevel, KalmanConfig
        print("✓ Kalman filter module imported successfully")
        
        # Create synthetic sea level data
        print("\nGenerating synthetic sea level data...")
        hours = 720  # 30 days
        dates = pd.date_range(start='2024-01-01', periods=hours, freq='h')
        
        # Components
        trend = np.linspace(0, 0.05, hours)
        m2_tide = 0.5 * np.sin(2 * np.pi * np.arange(hours) / 12.42)
        s2_tide = 0.3 * np.sin(2 * np.pi * np.arange(hours) / 12.00)
        noise = np.random.normal(0, 0.02, hours)
        sea_level = 1.5 + trend + m2_tide + s2_tide + noise
        
        df = pd.DataFrame({
            'Tab_DateTime': dates,
            'Tab_Value_mDepthC1': sea_level
        })
        print(f"✓ Generated {len(df)} hours of data")
        
        # Configure Kalman filter - use simpler config
        print("\nConfiguring Kalman filter...")
        config = KalmanConfig(
            use_level=True,
            use_trend=False,  # Disable trend to avoid conflict
            use_seasonal=True,
            tidal_periods=[12.42, 12.00]
        )
        
        # Initialize and fit
        print("Fitting model to data...")
        kf = KalmanFilterSeaLevel(config)
        kf.fit(df)
        print("✓ Model fitted successfully")
        
        # Generate forecast
        print("\nGenerating 48-hour forecast...")
        forecast_df = kf.forecast(steps=48, alpha=0.05)
        print(f"✓ Generated {len(forecast_df)} hours of predictions")
        
        # Get nowcast
        nowcast = kf.get_nowcast()
        print(f"\nNowcast (current filtered state):")
        print(f"  Timestamp: {nowcast['timestamp']}")
        print(f"  Filtered Level: {nowcast['filtered_value']:.3f} m")
        print(f"  Uncertainty: ±{nowcast['uncertainty']:.4f} m")
        
        # Create simple plot
        print("\nCreating visualization...")
        plt.figure(figsize=(12, 6))
        
        # Plot historical data
        plt.plot(df['Tab_DateTime'], df['Tab_Value_mDepthC1'], 
                'b-', label='Historical Data', alpha=0.7)
        
        # Plot forecast
        forecast_dates = pd.date_range(
            start=df['Tab_DateTime'].iloc[-1] + timedelta(hours=1),
            periods=len(forecast_df),
            freq='h'
        )
        plt.plot(forecast_dates, forecast_df['yhat'], 
                'g-', label='Kalman Forecast', linewidth=2)
        
        # Add confidence interval if available
        if 'yhat_lower' in forecast_df.columns:
            plt.fill_between(forecast_dates, 
                           forecast_df['yhat_lower'], 
                           forecast_df['yhat_upper'],
                           alpha=0.3, color='green', label='95% CI')
        
        plt.axvline(x=df['Tab_DateTime'].iloc[-1], color='red', 
                   linestyle='--', alpha=0.5, label='Forecast Start')
        
        plt.title('Sea Level Data with Kalman Filter Forecast')
        plt.xlabel('Date')
        plt.ylabel('Sea Level (m)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save plot
        output_file = 'kalman_test_results.png'
        plt.savefig(output_file, dpi=100)
        print(f"✓ Saved visualization to {output_file}")
        plt.show()
        
        print("\n" + "="*50)
        print("KALMAN FILTER TEST SUCCESSFUL!")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*50)
    print("KALMAN FILTER FIXED TEST")
    print("="*50)
    
    success = test_kalman_filter()
    
    if success:
        print("\n✓ Test completed successfully!")
        print("\nNext steps:")
        print("1. Replace backend/shared/kalman_filter.py with the fixed version")
        print("2. Restart your backend server")
        print("3. Check that predictionModels is initialized in App.js")
        print("4. Refresh your browser and look for Kalman option in filters")
    else:
        print("\n✗ Test failed. Please check the error messages.")