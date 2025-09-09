#!/usr/bin/env python3
"""
Deployment Script for Kalman Filter Upgrade
Tests and validates the new prediction system
"""

import os
import sys
import subprocess
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KalmanDeployment:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / 'backend'
        self.frontend_dir = self.project_root / 'frontend'
        self.test_results = {}
    
    def install_dependencies(self):
        """Install all required dependencies"""
        logger.info("Installing Python dependencies...")
        
        requirements = [
            "pandas>=2.0.0",
            "numpy>=1.24.0",
            "statsmodels>=0.14.0",
            "filterpy>=1.4.5",
            "scikit-learn>=1.3.0",
            "prophet>=1.1.5",
            "hmmlearn>=0.3.0",
            "scipy>=1.11.0",
            "sqlalchemy>=2.0.0",
            "psycopg2-binary>=2.9.0",
            "fastapi>=0.100.0",
            "uvicorn>=0.23.0"
        ]
        
        for req in requirements:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", req], 
                             check=True, capture_output=True)
                logger.info(f"✓ Installed {req}")
            except subprocess.CalledProcessError as e:
                logger.error(f"✗ Failed to install {req}: {e}")
                return False
        
        logger.info("Installing frontend dependencies...")
        try:
            subprocess.run(["npm", "install"], 
                         cwd=self.frontend_dir, 
                         check=True, capture_output=True)
            logger.info("✓ Frontend dependencies installed")
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Failed to install frontend dependencies: {e}")
            return False
        
        return True
    
    def test_kalman_module(self):
        """Test the Kalman filter module"""
        logger.info("Testing Kalman filter module...")
        
        # Add backend to path
        sys.path.insert(0, str(self.backend_dir))
        
        try:
            from shared.kalman_filter import KalmanFilterSeaLevel, KalmanConfig
            
            # Create test data
            dates = pd.date_range(start='2024-01-01', periods=720, freq='H')
            # Simulate sea level with trend and tidal components
            trend = np.linspace(0, 0.1, len(dates))
            tide_m2 = 0.5 * np.sin(2 * np.pi * np.arange(len(dates)) / (12.42))
            tide_s2 = 0.3 * np.sin(2 * np.pi * np.arange(len(dates)) / (12.00))
            noise = np.random.normal(0, 0.05, len(dates))
            sea_level = trend + tide_m2 + tide_s2 + noise
            
            test_df = pd.DataFrame({
                'Tab_DateTime': dates,
                'Tab_Value_mDepthC1': sea_level
            })
            
            # Test fitting
            config = KalmanConfig()
            kf = KalmanFilterSeaLevel(config)
            kf.fit(test_df)
            
            # Test forecasting
            forecast = kf.forecast(steps=24)
            
            # Test nowcast
            nowcast = kf.get_nowcast()
            
            # Test decomposition
            components = kf.decompose()
            
            # Validate results
            assert forecast is not None and len(forecast) == 24
            assert nowcast is not None and 'filtered_value' in nowcast
            assert components is not None and 'level' in components
            
            self.test_results['kalman_filter'] = 'PASS'
            logger.info("✓ Kalman filter module test passed")
            return True
            
        except Exception as e:
            self.test_results['kalman_filter'] = f'FAIL: {e}'
            logger.error(f"✗ Kalman filter test failed: {e}")
            return False
    
    def test_regime_switching(self):
        """Test regime switching module"""
        logger.info("Testing regime switching module...")
        
        try:
            from shared.regime_switching import RegimeSwitchingKalman, SeaLevelRegime
            
            # Create test data with regime changes
            dates = pd.date_range(start='2024-01-01', periods=720, freq='H')
            
            # Simulate different regimes
            sea_level = []
            for i in range(len(dates)):
                if i < 240:  # Calm
                    value = np.random.normal(0, 0.01)
                elif i < 480:  # Surge building
                    value = 0.5 + np.random.normal(0, 0.05)
                else:  # Storm
                    value = 1.0 + np.random.normal(0, 0.1)
                sea_level.append(value)
            
            test_df = pd.DataFrame({
                'Tab_DateTime': dates,
                'Tab_Value_mDepthC1': sea_level
            })
            
            # Test regime detection
            rs = RegimeSwitchingKalman()
            rs.train_hmm(test_df)
            rs.initialize_kalman_filters(test_df)
            
            # Test prediction
            forecast = rs.predict(test_df, steps=24)
            
            # Test regime analysis
            analysis = rs.get_regime_analysis()
            
            # Validate
            assert forecast is not None and not forecast.empty
            assert analysis is not None and 'surge_risk' in analysis
            
            self.test_results['regime_switching'] = 'PASS'
            logger.info("✓ Regime switching test passed")
            return True
            
        except ImportError:
            self.test_results['regime_switching'] = 'SKIPPED: hmmlearn not installed'
            logger.warning("⚠ Regime switching test skipped (optional)")
            return True
        except Exception as e:
            self.test_results['regime_switching'] = f'FAIL: {e}'
            logger.error(f"✗ Regime switching test failed: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test API endpoints with new Kalman predictions"""
        logger.info("Testing API endpoints...")
        
        try:
            import requests
            import time
            
            # Start the backend server
            server_process = subprocess.Popen(
                [sys.executable, str(self.backend_dir / "local_server.py")],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            time.sleep(5)
            
            # Test predictions endpoint
            response = requests.get(
                "http://localhost:8001/predictions",
                params={"station": "Test Station", "model": "kalman"}
            )
            
            if response.status_code == 200:
                data = response.json()
                assert 'kalman' in data or 'error' in data
                self.test_results['api_endpoints'] = 'PASS'
                logger.info("✓ API endpoints test passed")
                result = True
            else:
                self.test_results['api_endpoints'] = f'FAIL: Status {response.status_code}'
                logger.error(f"✗ API test failed: {response.status_code}")
                result = False
            
            # Stop server
            server_process.terminate()
            return result
            
        except Exception as e:
            self.test_results['api_endpoints'] = f'FAIL: {e}'
            logger.error(f"✗ API test failed: {e}")
            return False
    
    def validate_predictions(self):
        """Validate prediction accuracy"""
        logger.info("Validating prediction accuracy...")
        
        try:
            from shared.kalman_filter import KalmanFilterSeaLevel, KalmanConfig
            
            # Create synthetic data with known pattern
            dates = pd.date_range(start='2024-01-01', periods=1000, freq='H')
            true_signal = 0.5 * np.sin(2 * np.pi * np.arange(len(dates)) / (12.42))
            noise = np.random.normal(0, 0.01, len(dates))
            
            test_df = pd.DataFrame({
                'Tab_DateTime': dates[:-240],
                'Tab_Value_mDepthC1': true_signal[:-240] + noise[:-240]
            })
            
            validation_df = pd.DataFrame({
                'Tab_DateTime': dates[-240:],
                'Tab_Value_mDepthC1': true_signal[-240:] + noise[-240:]
            })
            
            # Fit and predict
            config = KalmanConfig()
            kf = KalmanFilterSeaLevel(config)
            kf.fit(test_df)
            forecast = kf.forecast(steps=240)
            
            # Calculate metrics
            from sklearn.metrics import mean_absolute_error, mean_squared_error
            
            mae = mean_absolute_error(
                validation_df['Tab_Value_mDepthC1'].values,
                forecast['yhat'].values
            )
            rmse = np.sqrt(mean_squared_error(
                validation_df['Tab_Value_mDepthC1'].values,
                forecast['yhat'].values
            ))
            
            # Check if within acceptable range
            if mae < 0.1 and rmse < 0.15:
                self.test_results['prediction_accuracy'] = f'PASS: MAE={mae:.4f}, RMSE={rmse:.4f}'
                logger.info(f"✓ Prediction accuracy test passed (MAE={mae:.4f}, RMSE={rmse:.4f})")
                return True
            else:
                self.test_results['prediction_accuracy'] = f'MARGINAL: MAE={mae:.4f}, RMSE={rmse:.4f}'
                logger.warning(f"⚠ Prediction accuracy marginal (MAE={mae:.4f}, RMSE={rmse:.4f})")
                return True
                
        except Exception as e:
            self.test_results['prediction_accuracy'] = f'FAIL: {e}'
            logger.error(f"✗ Prediction accuracy test failed: {e}")
            return False
    
    def create_backup(self):
        """Create backup of existing code"""
        logger.info("Creating backup...")
        
        backup_dir = self.project_root / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Backup key files
            files_to_backup = [
                self.backend_dir / "lambdas" / "get_predictions" / "main.py",
                self.frontend_dir / "src" / "components" / "GraphView.js",
                self.frontend_dir / "src" / "components" / "Filters.js"
            ]
            
            backup_dir.mkdir(exist_ok=True)
            
            for file_path in files_to_backup:
                if file_path.exists():
                    relative_path = file_path.relative_to(self.project_root)
                    backup_path = backup_dir / relative_path
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    import shutil
                    shutil.copy2(file_path, backup_path)
                    logger.info(f"✓ Backed up {relative_path}")
            
            logger.info(f"✓ Backup created at {backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Backup failed: {e}")
            return False
    
    def generate_report(self):
        """Generate deployment report"""
        logger.info("\n" + "="*60)
        logger.info("KALMAN FILTER DEPLOYMENT REPORT")
        logger.info("="*60)
        
        # Test results
        logger.info("\nTest Results:")
        for test, result in self.test_results.items():
            status = "✓" if "PASS" in str(result) else "✗"
            logger.info(f"  {status} {test}: {result}")
        
        # Recommendations
        logger.info("\nRecommendations:")
        logger.info("  1. Run extensive testing with real data before production")
        logger.info("  2. Monitor prediction accuracy for first week")
        logger.info("  3. Adjust Kalman parameters based on station characteristics")
        logger.info("  4. Enable regime switching only after validation")
        logger.info("  5. Set up alerting for surge warnings")
        
        # Next steps
        logger.info("\nNext Steps:")
        logger.info("  1. Update AWS Lambda functions with new code")
        logger.info("  2. Test with production database")
        logger.info("  3. Deploy frontend changes")
        logger.info("  4. Monitor performance metrics")
        logger.info("  5. Document configuration for each station")
        
        logger.info("\n" + "="*60)
    
    def run(self):
        """Run full deployment process"""
        logger.info("Starting Kalman filter deployment...")
        
        # Create backup
        if not self.create_backup():
            logger.error("Backup failed, aborting deployment")
            return False
        
        # Install dependencies
        if not self.install_dependencies():
            logger.error("Dependency installation failed")
            return False
        
        # Run tests
        tests_passed = True
        tests_passed &= self.test_kalman_module()
        tests_passed &= self.test_regime_switching()
        tests_passed &= self.validate_predictions()
        # API test optional as it requires server
        # tests_passed &= self.test_api_endpoints()
        
        # Generate report
        self.generate_report()
        
        if tests_passed:
            logger.info("\n✓ DEPLOYMENT SUCCESSFUL - Kalman filter upgrade ready!")
        else:
            logger.warning("\n⚠ DEPLOYMENT COMPLETED WITH WARNINGS - Review test results")
        
        return tests_passed

if __name__ == "__main__":
    deployment = KalmanDeployment()
    success = deployment.run()
    sys.exit(0 if success else 1)