#!/usr/bin/env python3
"""
Performance Testing Script for Sea Level Dashboard
==================================================
Tests all optimizations and provides detailed performance metrics
"""

import requests
import time
import statistics
import json
import sys
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

class PerformanceTester:
    def __init__(self, base_url="http://localhost:30886"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {}
    
    def test_endpoint(self, name, url, runs=10, params=None):
        """Test an endpoint multiple times and collect metrics"""
        print(f"\n🧪 Testing {name}...")
        
        times = []
        errors = 0
        
        for i in range(runs):
            try:
                start = time.time()
                response = self.session.get(url, params=params, timeout=30)
                duration = (time.time() - start) * 1000  # ms
                
                if response.status_code == 200:
                    times.append(duration)
                    print(f"  Run {i+1}: {duration:.0f}ms ✓")
                else:
                    errors += 1
                    print(f"  Run {i+1}: ERROR {response.status_code} ✗")
                    
            except Exception as e:
                errors += 1
                print(f"  Run {i+1}: EXCEPTION {str(e)} ✗")
        
        if times:
            result = {
                'avg': statistics.mean(times),
                'min': min(times),
                'max': max(times),
                'p50': statistics.median(times),
                'p95': statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times),
                'success_rate': (len(times) / runs) * 100,
                'errors': errors
            }
        else:
            result = {
                'avg': 0,
                'min': 0,
                'max': 0,
                'p50': 0,
                'p95': 0,
                'success_rate': 0,
                'errors': errors
            }
        
        self.results[name] = result
        
        print(f"  📊 Results:")
        print(f"     Average: {result['avg']:.0f}ms")
        print(f"     P95: {result['p95']:.0f}ms")
        print(f"     Success Rate: {result['success_rate']:.1f}%")
        
        return result
    
    def test_caching_effectiveness(self):
        """Test cache hit/miss performance"""
        print(f"\n🔄 Testing Cache Effectiveness...")
        
        url = f"{self.base_url}/api/data"
        params = {"station": "Haifa", "limit": 100}
        
        # First request (cache miss)
        print("  First request (cache miss):")
        start = time.time()
        response1 = self.session.get(url, params=params)
        time1 = (time.time() - start) * 1000
        print(f"    {time1:.0f}ms")
        
        # Second request (cache hit)
        print("  Second request (cache hit):")
        start = time.time()
        response2 = self.session.get(url, params=params)
        time2 = (time.time() - start) * 1000
        print(f"    {time2:.0f}ms")
        
        if time1 > 0 and time2 > 0:
            improvement = ((time1 - time2) / time1) * 100
            print(f"  📈 Cache improvement: {improvement:.1f}%")
            
            self.results['cache_effectiveness'] = {
                'cache_miss_time': time1,
                'cache_hit_time': time2,
                'improvement_percent': improvement
            }
        
        return time1, time2
    
    def test_concurrent_load(self, concurrent_users=10):
        """Test performance under concurrent load"""
        print(f"\n👥 Testing Concurrent Load ({concurrent_users} users)...")
        
        url = f"{self.base_url}/api/data"
        params = {"station": "All Stations", "limit": 500}
        
        def make_request():
            try:
                start = time.time()
                response = self.session.get(url, params=params, timeout=30)
                duration = (time.time() - start) * 1000
                return {
                    'duration': duration,
                    'status': response.status_code,
                    'success': response.status_code == 200
                }
            except Exception as e:
                return {
                    'duration': 30000,  # timeout
                    'status': 0,
                    'success': False,
                    'error': str(e)
                }
        
        # Execute concurrent requests
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_request) for _ in range(concurrent_users)]
            results = [future.result() for future in as_completed(futures)]
        total_time = time.time() - start_time
        
        # Analyze results
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        if successful:
            durations = [r['duration'] for r in successful]
            avg_duration = statistics.mean(durations)
            max_duration = max(durations)
        else:
            avg_duration = 0
            max_duration = 0
        
        success_rate = (len(successful) / len(results)) * 100
        
        print(f"  📊 Concurrent Load Results:")
        print(f"     Total Time: {total_time:.1f}s")
        print(f"     Success Rate: {success_rate:.1f}%")
        print(f"     Average Response: {avg_duration:.0f}ms")
        print(f"     Max Response: {max_duration:.0f}ms")
        print(f"     Failed Requests: {len(failed)}")
        
        self.results['concurrent_load'] = {
            'users': concurrent_users,
            'total_time': total_time,
            'success_rate': success_rate,
            'avg_response': avg_duration,
            'max_response': max_duration,
            'failed_requests': len(failed)
        }
        
        return success_rate, avg_duration
    
    def get_system_metrics(self):
        """Get system performance metrics"""
        print(f"\n📊 Getting System Metrics...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/metrics", timeout=10)
            if response.status_code == 200:
                metrics = response.json()
                print(f"  Database Metrics:")
                
                db_metrics = metrics.get('database', {})
                print(f"    Total Queries: {db_metrics.get('total_queries', 'N/A')}")
                print(f"    Cache Hit Rate: {db_metrics.get('cache_hit_rate', 'N/A')}")
                print(f"    Slow Queries: {db_metrics.get('slow_queries', 'N/A')}")
                print(f"    Pool Size: {db_metrics.get('pool_size', 'N/A')}")
                print(f"    Checked Out: {db_metrics.get('checked_out', 'N/A')}")
                
                self.results['system_metrics'] = metrics
                return metrics
            else:
                print(f"  ❌ Failed to get metrics: {response.status_code}")
                return None
        except Exception as e:
            print(f"  ❌ Error getting metrics: {e}")
            return None
    
    def run_full_test_suite(self):
        """Run complete performance test suite"""
        print("=" * 80)
        print("🚀 SEA LEVEL DASHBOARD - PERFORMANCE TEST SUITE")
        print("=" * 80)
        print(f"Testing server: {self.base_url}")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test individual endpoints
        endpoints = [
            ("Health Check", "/api/health", None),
            ("Stations", "/api/stations", None),
            ("Data (Small)", "/api/data", {"station": "Haifa", "limit": 100}),
            ("Data (Large)", "/api/data", {"station": "All Stations", "limit": 1000}),
            ("Latest Data", "/api/latest", {"station": "Haifa", "limit": 50}),
            ("Sea Forecast", "/api/sea-forecast", None),
        ]
        
        for name, endpoint, params in endpoints:
            url = f"{self.base_url}{endpoint}"
            self.test_endpoint(name, url, runs=5, params=params)
        
        # Test caching
        self.test_caching_effectiveness()
        
        # Test concurrent load
        self.test_concurrent_load(concurrent_users=5)
        
        # Get system metrics
        self.get_system_metrics()
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate performance report"""
        print("\n" + "=" * 80)
        print("📋 PERFORMANCE REPORT")
        print("=" * 80)
        
        # Overall performance
        print("\n🎯 ENDPOINT PERFORMANCE:")
        print("-" * 50)
        for name, result in self.results.items():
            if isinstance(result, dict) and 'avg' in result:
                status = "✅ EXCELLENT" if result['avg'] < 200 else "⚠️ NEEDS IMPROVEMENT" if result['avg'] < 1000 else "❌ POOR"
                print(f"{name:20} {result['avg']:6.0f}ms  {status}")
        
        # Cache effectiveness
        if 'cache_effectiveness' in self.results:
            cache = self.results['cache_effectiveness']
            print(f"\n🔄 CACHE EFFECTIVENESS:")
            print("-" * 50)
            print(f"Cache Miss:     {cache['cache_miss_time']:6.0f}ms")
            print(f"Cache Hit:      {cache['cache_hit_time']:6.0f}ms")
            print(f"Improvement:    {cache['improvement_percent']:6.1f}%")
            
            if cache['improvement_percent'] > 70:
                print("✅ Cache is working excellently!")
            elif cache['improvement_percent'] > 40:
                print("⚠️ Cache is working but could be better")
            else:
                print("❌ Cache may not be working properly")
        
        # Concurrent load
        if 'concurrent_load' in self.results:
            load = self.results['concurrent_load']
            print(f"\n👥 CONCURRENT LOAD:")
            print("-" * 50)
            print(f"Success Rate:   {load['success_rate']:6.1f}%")
            print(f"Avg Response:   {load['avg_response']:6.0f}ms")
            
            if load['success_rate'] > 95 and load['avg_response'] < 500:
                print("✅ Excellent performance under load!")
            elif load['success_rate'] > 90:
                print("⚠️ Good performance, some room for improvement")
            else:
                print("❌ Poor performance under load")
        
        # System metrics
        if 'system_metrics' in self.results:
            metrics = self.results['system_metrics'].get('database', {})
            print(f"\n📊 SYSTEM HEALTH:")
            print("-" * 50)
            
            cache_hit_rate = metrics.get('cache_hit_rate', '0%')
            if isinstance(cache_hit_rate, str):
                cache_rate = float(cache_hit_rate.rstrip('%'))
            else:
                cache_rate = 0
            
            print(f"Cache Hit Rate: {cache_hit_rate}")
            print(f"Slow Queries:   {metrics.get('slow_queries', 'N/A')}")
            
            if cache_rate > 70:
                print("✅ Cache performance is excellent!")
            elif cache_rate > 50:
                print("⚠️ Cache performance is good")
            else:
                print("❌ Cache performance needs improvement")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        print("-" * 50)
        
        recommendations = []
        
        # Check data endpoint performance
        if 'Data (Small)' in self.results:
            if self.results['Data (Small)']['avg'] > 500:
                recommendations.append("• Apply database indexes for faster queries")
        
        # Check cache effectiveness
        if 'cache_effectiveness' in self.results:
            if self.results['cache_effectiveness']['improvement_percent'] < 50:
                recommendations.append("• Check Redis configuration and connectivity")
        
        # Check concurrent performance
        if 'concurrent_load' in self.results:
            if self.results['concurrent_load']['success_rate'] < 95:
                recommendations.append("• Increase connection pool size")
        
        if not recommendations:
            recommendations.append("• System performance is optimal! 🎉")
        
        for rec in recommendations:
            print(rec)
        
        print("\n" + "=" * 80)
        print(f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Save results to file
        with open('performance_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"📁 Results saved to: performance_test_results.json")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:30886"
    
    print(f"🧪 Starting performance tests for: {base_url}")
    
    tester = PerformanceTester(base_url)
    
    try:
        tester.run_full_test_suite()
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()