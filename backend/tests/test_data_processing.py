# backend/tests/test_data_processing.py
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from shared.data_processing import (
    load_data_from_db, 
    detect_anomalies, 
    calculate_stats,
    arima_predict,
    prophet_predict
)

class TestDataProcessing:
    
    def test_load_data_from_db_empty_result(self):
        """Test loading data when no results are found"""
        with patch('shared.data_processing.db_manager') as mock_db:
            mock_db.engine.connect.return_value.__enter__.return_value.execute.return_value.fetchmany.return_value = []
            
            result = load_data_from_db()
            assert result.empty
    
    def test_detect_anomalies_empty_dataframe(self):
        """Test anomaly detection with empty DataFrame"""
        df = pd.DataFrame()
        result = detect_anomalies(df)
        assert result.empty
    
    def test_detect_anomalies_normal_data(self):
        """Test anomaly detection with normal data"""
        df = pd.DataFrame({
            'Tab_Value_mDepthC1': np.random.normal(0, 1, 100)
        })
        
        result = detect_anomalies(df)
        assert 'anomaly' in result.columns
        assert len(result) == 100
        # Should have some anomalies but not too many
        anomaly_count = sum(result['anomaly'] == -1)
        assert 0 <= anomaly_count <= 10
    
    def test_calculate_stats_empty_dataframe(self):
        """Test stats calculation with empty DataFrame"""
        df = pd.DataFrame()
        stats = calculate_stats(df)
        
        expected = {
            'current_level': None,
            '24h_change': None,
            'avg_temp': None,
            'anomalies': None
        }
        assert stats == expected
    
    def test_calculate_stats_valid_data(self):
        """Test stats calculation with valid data"""
        df = pd.DataFrame({
            'Tab_Value_mDepthC1': [1.0, 1.5, 2.0],
            'Tab_Value_monT2m': [20.0, 21.0, 22.0],
            'anomaly': [0, -1, 0]
        })
        
        stats = calculate_stats(df)
        
        assert stats['current_level'] == 2.0
        assert stats['24h_change'] == 1.0  # 2.0 - 1.0
        assert stats['avg_temp'] == 21.0
        assert stats['anomalies'] == 1
    
    @patch('shared.data_processing.ARIMA_AVAILABLE', False)
    def test_arima_predict_not_available(self):
        """Test ARIMA prediction when library not available"""
        result = arima_predict('test_station')
        assert result is None
    
    @patch('shared.data_processing.PROPHET_AVAILABLE', False)
    def test_prophet_predict_not_available(self):
        """Test Prophet prediction when library not available"""
        result = prophet_predict('test_station')
        assert result.empty