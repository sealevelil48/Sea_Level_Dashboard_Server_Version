#!/usr/bin/env python3
"""
Performance Testing Script for Sea Level Dashboard
Measures API response times and identifies bottlenecks
"""

import time
import requests
import json
import statistics
from datetime import datetime, timedelta
import concurrent.futures
import sys

class PerformanceTester:
    def __init__(self, base_url="http://127.0.0.1:30886"):
        self.base_url = base_url
        self.results = {}
        
    def measure_endpoint(self, endpoint, params=None, iterations=5):
        """Measure response time for an endpoint"""
        times = []
        errors = 0
        
        print(f"\n[TEST] Testing {endpoint}...")
        
        for i in range(iterations):
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=30)
                end_time = time.time()
                
                duration = (end_time - start_time) * 1000  # Convert to milliseconds
                times.append(duration)
                
                status = "[OK]" if response.status_code == 200 else "[FAIL]"
                print(f"  Attempt {i+1}: {duration:.0f}ms {status}")
                
                if response.status_code != 200:
                    errors += 1
                    
            except requests.exceptions.Timeout:
                print(f"  Attempt {i+1}: TIMEOUT (>30s) [FAIL]")
                errors += 1
            except Exception as e:
                print(f"  Attempt {i+1}: ERROR - {str(e)} [FAIL]")
                errors += 1
        
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            
            self.results[endpoint] = {
                'avg_ms': avg_time,
                'min_ms': min_time,
                'max_ms': max_time,
                'success_rate': ((iterations - errors) / iterations) * 100,
                'raw_times': times
            }
            
            print(f"  [STATS] Average: {avg_time:.0f}ms | Min: {min_time:.0f}ms | Max: {max_time:.0f}ms")
            print(f"  [RATE] Success Rate: {((iterations - errors) / iterations) * 100:.1f}%")
        else:
            print(f"  [FAIL] All requests failed")
            self.results[endpoint] = {
                'avg_ms': 0,
                'min_ms': 0,
                'max_ms': 0,
                'success_rate': 0,
                'raw_times': []
            }
    
    def test_concurrent_load(self, endpoint, concurrent_requests=10):
        """Test concurrent request handling"""
        print(f"\n[LOAD] Testing concurrent load ({concurrent_requests} requests) for {endpoint}...")
        
        def make_request():
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                end_time = time.time()
                return {
                    'duration': (end_time - start_time) * 1000,
                    'status_code': response.status_code,
                    'success': response.status_code == 200
                }
            except Exception as e:
                return {
                    'duration': 30000,  # Timeout
                    'status_code': 0,
                    'success': False,
                    'error': str(e)
                }
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(concurrent_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        end_time = time.time()
        
        total_time = (end_time - start_time) * 1000
        successful_requests = sum(1 for r in results if r['success'])
        avg_response_time = statistics.mean([r['duration'] for r in results if r['success']])
        
        print(f"  [TIME] Total Time: {total_time:.0f}ms")
        print(f"  [SUCCESS] Successful Requests: {successful_requests}/{concurrent_requests}")
        print(f"  [AVG] Average Response Time: {avg_response_time:.0f}ms")
        print(f"  [RPS] Requests/Second: {(successful_requests / (total_time / 1000)):.1f}")
        
        return {
            'total_time_ms': total_time,
            'successful_requests': successful_requests,
            'avg_response_time_ms': avg_response_time,
            'requests_per_second': successful_requests / (total_time / 1000)
        }
    
    def run_full_test_suite(self):
        """Run comprehensive performance tests"""
        print("[PERF] Sea Level Dashboard Performance Test Suite")
        print("=" * 60)
        
        # Test individual endpoints
        endpoints_to_test = [
            ('/api/health', None),
            ('/api/stations', None),
            ('/api/data', {
                'station': 'All Stations',
                'start_date': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                'end_date': datetime.now().strftime('%Y-%m-%d'),
                'data_source': 'default'
            }),
            ('/api/sea-forecast', None),
            ('/api/predictions', {
                'stations': 'Acre',
                'model': 'kalman',
                'steps': '72'
            })
        ]
        
        for endpoint, params in endpoints_to_test:
            self.measure_endpoint(endpoint, params)
        
        # Test concurrent load
        print("\n" + "=" * 60)
        print("[CONCURRENT] CONCURRENT LOAD TESTING")
        print("=" * 60)
        
        concurrent_results = {}
        for endpoint, _ in endpoints_to_test[:3]:  # Test first 3 endpoints
            concurrent_results[endpoint] = self.test_concurrent_load(endpoint, 5)
        
        # Generate report
        self.generate_report(concurrent_results)
    
    def generate_report(self, concurrent_results=None):
        """Generate performance report"""
        print("\n" + "=" * 60)
        print("[REPORT] PERFORMANCE ANALYSIS REPORT")
        print("=" * 60)
        
        # Individual endpoint performance
        print("\n[ENDPOINTS] ENDPOINT PERFORMANCE:")
        print("-" * 40)
        
        for endpoint, data in self.results.items():
            status = "[FAST]" if data['avg_ms'] < 1000 else "[MED]" if data['avg_ms'] < 3000 else "[SLOW]"
            print(f"{status} {endpoint}")
            print(f"   Average: {data['avg_ms']:.0f}ms")
            print(f"   Range: {data['min_ms']:.0f}ms - {data['max_ms']:.0f}ms")
            print(f"   Success Rate: {data['success_rate']:.1f}%")
            print()
        
        # Performance classification
        print("[CLASSIFICATION] PERFORMANCE CLASSIFICATION:")
        print("-" * 40)
        
        fast_endpoints = [ep for ep, data in self.results.items() if data['avg_ms'] < 1000]
        medium_endpoints = [ep for ep, data in self.results.items() if 1000 <= data['avg_ms'] < 3000]
        slow_endpoints = [ep for ep, data in self.results.items() if data['avg_ms'] >= 3000]
        
        print(f"[FAST] Fast (< 1s): {len(fast_endpoints)} endpoints")
        for ep in fast_endpoints:
            print(f"   - {ep}")
        
        print(f"\n[MEDIUM] Medium (1-3s): {len(medium_endpoints)} endpoints")
        for ep in medium_endpoints:
            print(f"   - {ep}")
        
        print(f"\n[SLOW] Slow (> 3s): {len(slow_endpoints)} endpoints")
        for ep in slow_endpoints:
            print(f"   - {ep}")
        
        # Concurrent performance
        if concurrent_results:
            print("\n[CONCURRENT] CONCURRENT LOAD PERFORMANCE:")
            print("-" * 40)
            
            for endpoint, data in concurrent_results.items():
                print(f"[ENDPOINT] {endpoint}")
                print(f"   Requests/Second: {data['requests_per_second']:.1f}")
                print(f"   Average Response: {data['avg_response_time_ms']:.0f}ms")
                print()
        
        # Recommendations
        print("[RECOMMENDATIONS] OPTIMIZATION RECOMMENDATIONS:")
        print("-" * 40)
        
        if slow_endpoints:
            print("[CRITICAL] CRITICAL - Slow Endpoints (> 3s):")
            for ep in slow_endpoints:
                avg_time = self.results[ep]['avg_ms']
                print(f"   - {ep} ({avg_time:.0f}ms) - Needs immediate optimization")
        
        if medium_endpoints:
            print("\n[MEDIUM] MEDIUM - Moderate Endpoints (1-3s):")
            for ep in medium_endpoints:
                avg_time = self.results[ep]['avg_ms']
                print(f"   - {ep} ({avg_time:.0f}ms) - Consider caching/optimization")
        
        # Overall assessment
        total_endpoints = len(self.results)
        fast_percentage = (len(fast_endpoints) / total_endpoints) * 100
        
        print(f"\n[SCORE] OVERALL PERFORMANCE SCORE:")
        print(f"   Fast Endpoints: {fast_percentage:.1f}%")
        
        if fast_percentage >= 80:
            print("   [EXCELLENT] EXCELLENT - Most endpoints perform well")
        elif fast_percentage >= 60:
            print("   [GOOD] GOOD - Some optimization needed")
        elif fast_percentage >= 40:
            print("   [FAIR] FAIR - Significant optimization required")
        else:
            print("   [POOR] POOR - Major performance issues detected")
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'endpoint_results': self.results,
                'concurrent_results': concurrent_results or {},
                'summary': {
                    'total_endpoints': total_endpoints,
                    'fast_endpoints': len(fast_endpoints),
                    'medium_endpoints': len(medium_endpoints),
                    'slow_endpoints': len(slow_endpoints),
                    'performance_score': fast_percentage
                }
            }, f, indent=2)
        
        print(f"\n[SAVED] Results saved to: {filename}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://127.0.0.1:30886"
    
    print(f"[TARGET] Testing Sea Level Dashboard at: {base_url}")
    
    tester = PerformanceTester(base_url)
    
    try:
        tester.run_full_test_suite()
    except KeyboardInterrupt:
        print("\n\n[STOP] Test interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
    
    print("\n[SUCCESS] Performance testing completed!")

if __name__ == "__main__":
    main()