# backend/tests/integration/test_api_integration.py
import pytest
import requests
import os

class TestAPIIntegration:
    
    @pytest.fixture
    def api_base_url(self):
        return os.getenv('API_BASE_URL', 'http://localhost:8000')
    
    def test_get_stations_endpoint(self, api_base_url):
        """Test /stations endpoint"""
        response = requests.get(f"{api_base_url}/stations")
        
        assert response.status_code == 200
        data = response.json()
        assert 'stations' in data
        assert isinstance(data['stations'], list)
    
    def test_get_live_data_endpoint(self, api_base_url):
        """Test /live endpoint"""
        response = requests.get(f"{api_base_url}/live")
        
        assert response.status_code == 200
        data = response.json()
        assert 'data' in data
    
    def test_get_data_with_parameters(self, api_base_url):
        """Test /data endpoint with parameters"""
        params = {
            'station': 'Station1',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
            'data_source': 'default'
        }
        
        response = requests.get(f"{api_base_url}/data", params=params)
        
        # Should return 200 or 404 (if no data)
        assert response.status_code in [200, 404]
    
    def test_get_predictions_endpoint(self, api_base_url):
        """Test /predictions endpoint"""
        params = {
            'station': 'Station1',
            'model': 'all'
        }
        
        response = requests.get(f"{api_base_url}/predictions", params=params)
        
        assert response.status_code == 200
        data = response.json()
        # Should have arima and/or prophet keys
        assert any(key in data for key in ['arima', 'prophet'])