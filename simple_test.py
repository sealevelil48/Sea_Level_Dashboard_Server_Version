#!/usr/bin/env python3
"""
Simple Performance Test for Sea Level Dashboard
"""

import requests
import time
import statistics

def test_endpoint(name, url, runs=5):
    """Test an endpoint multiple times"""
    print(f"\nTesting {name}...")
    
    times = []
    for i in range(runs):
        try:
            start = time.time()
            response = requests.get(url, timeout=30)
            duration = (time.time() - start) * 1000  # ms
            
            if response.status_code == 200:
                times.append(duration)
                print(f"  Run {i+1}: {duration:.0f}ms")
            else:
                print(f"  Run {i+1}: ERROR {response.status_code}")
                
        except Exception as e:
            print(f"  Run {i+1}: EXCEPTION {str(e)}")
    
    if times:
        avg = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"  Results:")
        print(f"    Average: {avg:.0f}ms")
        print(f"    Min: {min_time:.0f}ms")
        print(f"    Max: {max_time:.0f}ms")
        
        return avg
    
    return 0

def main():
    base_url = "http://localhost:30886"
    
    print("=" * 60)
    print("SEA LEVEL DASHBOARD - PERFORMANCE TEST")
    print("=" * 60)
    
    # Test endpoints
    endpoints = [
        ("Health Check", "/api/health"),
        ("Stations", "/api/stations"),
        ("Data (Small)", "/api/data?station=Haifa&limit=100"),
        ("Data (Large)", "/api/data?station=All Stations&limit=500"),
    ]
    
    results = {}
    for name, endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        avg_time = test_endpoint(name, url)
        results[name] = avg_time
    
    # Test caching
    print(f"\nTesting Cache Effectiveness...")
    url = f"{base_url}/api/data?station=Haifa&limit=100"
    
    # First request (potential cache miss)
    start = time.time()
    response1 = requests.get(url)
    time1 = (time.time() - start) * 1000
    print(f"  First request: {time1:.0f}ms")
    
    # Second request (potential cache hit)
    start = time.time()
    response2 = requests.get(url)
    time2 = (time.time() - start) * 1000
    print(f"  Second request: {time2:.0f}ms")
    
    if time1 > 0 and time2 > 0:
        improvement = ((time1 - time2) / time1) * 100
        print(f"  Cache improvement: {improvement:.1f}%")
    
    # Summary
    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)
    
    for name, avg_time in results.items():
        if avg_time > 0:
            status = "EXCELLENT" if avg_time < 200 else "GOOD" if avg_time < 500 else "NEEDS WORK"
            print(f"{name:20} {avg_time:6.0f}ms  {status}")
    
    print("\nExpected improvements from database indexes:")
    print("- Data queries should be 60-70% faster than before")
    print("- With Redis caching, repeated queries will be 80% faster")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()