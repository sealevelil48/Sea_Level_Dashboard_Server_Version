# backend/tests/test_lambda_get_data.py
import json
import pytest
from unittest.mock import patch, MagicMock
from lambdas.get_data.main import handler, validate_parameters

class TestGetDataLambda:
    
    def test_validate_parameters_valid_input(self):
        """Test parameter validation with valid input"""
        params = {
            'station': 'Station1',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
            'data_source': 'default',
            'show_anomalies': 'true'
        }
        
        result, error = validate_parameters(params)
        
        assert error is None
        assert result['station'] == 'Station1'
        assert result['start_date'] == '2024-01-01'
        assert result['end_date'] == '2024-01-31'
        assert result['data_source'] == 'default'
        assert result['show_anomalies'] is True
    
    def test_validate_parameters_invalid_date(self):
        """Test parameter validation with invalid date"""
        params = {
            'start_date': 'invalid-date'
        }
        
        result, error = validate_parameters(params)
        
        assert result is None
        assert 'Invalid start_date format' in error
    
    def test_validate_parameters_missing_station_for_default(self):
        """Test parameter validation when station is missing for default data source"""
        params = {
            'data_source': 'default'
        }
        
        result, error = validate_parameters(params)
        
        assert result is None
        assert 'Station parameter is required' in error
    
    def test_handler_cors_options_request(self):
        """Test CORS preflight request handling"""
        event = {
            'httpMethod': 'OPTIONS'
        }
        
        response = handler(event, None)
        
        assert response['statusCode'] == 200
        assert 'Access-Control-Allow-Origin' in response['headers']
    
    @patch('lambdas.get_data.main.load_data_from_db')
    @patch('lambdas.get_data.main.db_manager')
    def test_handler_successful_request(self, mock_db, mock_load_data):
        """Test successful data request"""
        # Setup mocks
        mock_db.health_check.return_value = True
        mock_db.get_from_cache.return_value = None
        
        # Mock DataFrame
        import pandas as pd
        mock_df = pd.DataFrame({
            'Tab_DateTime': ['2024-01-01'],
            'Station': ['Station1'],
            'Tab_Value_mDepthC1': [1.5]
        })
        mock_load_data.return_value = mock_df
        
        event = {
            'queryStringParameters': {
                'station': 'Station1',
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
                'data_source': 'default'
            }
        }
        
        response = handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body) == 1
        assert body[0]['Station'] == 'Station1'