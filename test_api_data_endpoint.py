#!/usr/bin/env python3
"""
Comprehensive test script for /api/data endpoint
Tests various scenarios to identify potential issues
"""

import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:30886"

def test_endpoint(name, url, expected_status=200):
    """Test an endpoint and return results"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    start = time.time()
    try:
        response = requests.get(url, timeout=30)
        duration = time.time() - start
        
        print(f"Status: {response.status_code} (expected: {expected_status})")
        print(f"Duration: {duration:.2f}s")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list):
                    print(f"Records: {len(data)}")
                    if data:
                        print(f"First record: {data[0]}")
                        print(f"Last record: {data[-1]}")
                        print(f"Keys: {list(data[0].keys())}")
                elif isinstance(data, dict):
                    print(f"Response: {json.dumps(data, indent=2)[:500]}")
            except json.JSONDecodeError as e:
                print(f"JSON Error: {e}")
                print(f"Response text: {response.text[:500]}")
        else:
            print(f"Error response: {response.text[:500]}")
        
        return response.status_code == expected_status
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return False

def main():
    """Run all tests"""
    
    print("="*60)
    print("TESTING /api/data ENDPOINT")
    print("="*60)
    
    tests = []
    
    # Test 1: Basic request with all parameters
    tests.append(test_endpoint(
        "Basic request - Single station",
        f"{BASE_URL}/api/data?station=Acre&start_date=2025-11-01&end_date=2025-11-02&limit=100"
    ))
    
    # Test 2: All Stations
    tests.append(test_endpoint(
        "All Stations",
        f"{BASE_URL}/api/data?station=All%20Stations&start_date=2025-11-01&end_date=2025-11-02&limit=100"
    ))
    
    # Test 3: No parameters (should return recent data)
    tests.append(test_endpoint(
        "No parameters",
        f"{BASE_URL}/api/data"
    ))
    
    # Test 4: Invalid station (should return 404)
    tests.append(test_endpoint(
        "Invalid station",
        f"{BASE_URL}/api/data?station=InvalidStation&start_date=2025-11-01&end_date=2025-11-02",
        expected_status=404
    ))
    
    # Test 5: Invalid date format (should return 400)
    tests.append(test_endpoint(
        "Invalid date format",
        f"{BASE_URL}/api/data?station=Acre&start_date=invalid&end_date=2025-11-02",
        expected_status=400
    ))
    
    # Test 6: Large date range (should use aggregation)
    tests.append(test_endpoint(
        "Large date range (90+ days)",
        f"{BASE_URL}/api/data?station=Acre&start_date=2025-01-01&end_date=2025-11-12"
    ))
    
    # Test 7: CORS headers
    print(f"\n{'='*60}")
    print(f"TEST: CORS Headers")
    print(f"{'='*60}")
    try:
        response = requests.options(f"{BASE_URL}/api/data", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        print(f"CORS Status: {response.status_code}")
        print(f"CORS Headers: {dict(response.headers)}")
    except Exception as e:
        print(f"CORS Test Error: {e}")
    
    # Test 8: Batch endpoint
    tests.append(test_endpoint(
        "Batch endpoint - Multiple stations",
        f"{BASE_URL}/api/data/batch?stations=Acre,Yafo&start_date=2025-11-01&end_date=2025-11-02"
    ))
    
    # Test 9: Database connection via health endpoint
    tests.append(test_endpoint(
        "Health check",
        f"{BASE_URL}/api/health"
    ))
    
    # Summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    passed = sum(tests)
    total = len(tests)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED!")
    else:
        print(f"\n✗ SOME TESTS FAILED ({total - passed} failures)")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
