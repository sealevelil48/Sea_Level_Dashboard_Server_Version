# backend/tests/performance/test_performance.py
import pytest
import time
import requests
import concurrent.futures
import os

class TestPerformance:
    
    @pytest.fixture
    def api_base_url(self):
        return os.getenv('API_BASE_URL', 'http://localhost:8000')
    
    def test_response_time_stations(self, api_base_url):
        """Test /stations endpoint response time"""
        start_time = time.time()
        response = requests.get(f"{api_base_url}/stations")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 5.0  # Should respond within 5 seconds
    
    def test_concurrent_requests(self, api_base_url):
        """Test handling of concurrent requests"""
        def make_request():
            response = requests.get(f"{api_base_url}/stations")
            return response.status_code
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        assert all(status == 200 for status in results)
    
    def test_large_data_query_performance(self, api_base_url):
        """Test performance of large data queries"""
        params = {
            'station': 'Station1',
            'start_date': '2023-01-01',
            'end_date': '2024-01-01',  # 1 year of data
            'data_source': 'default'
        }
        
        start_time = time.time()
        response = requests.get(f"{api_base_url}/data", params=params)
        end_time = time.time()
        
        # Should complete within 30 seconds even for large queries
        assert (end_time - start_time) < 30.0
        # Should return 200 or 404 (if no data)
        assert response.status_code in [200, 404]