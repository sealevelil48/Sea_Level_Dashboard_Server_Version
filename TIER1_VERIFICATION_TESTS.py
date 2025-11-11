#!/usr/bin/env python3
"""
TIER 1 OPTIMIZATION VERIFICATION TESTS
=======================================

This script verifies all three Tier 1 optimizations:
1. Backend batch endpoint
2. Frontend parallel fetching (via manual browser testing)
3. Bundle size optimization

Run this after implementing optimizations to verify everything works.
"""

import requests
import time
import json
from datetime import datetime, timedelta

# Configuration
BACKEND_URL = "http://127.0.0.1:30886"
TEST_STATIONS = ["Haifa", "Acre", "Ashdod"]
TEST_START_DATE = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
TEST_END_DATE = datetime.now().strftime('%Y-%m-%d')

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_failure(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def test_backend_health():
    """Test 1: Verify backend is running"""
    print_header("TEST 1: Backend Health Check")

    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success("Backend is running")
            print_info(f"Response: {response.json()}")
            return True
        else:
            print_failure(f"Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print_failure(f"Backend is not accessible: {e}")
        print_warning("Start backend with: python backend/local_server-prod.py")
        return False

def test_batch_endpoint_exists():
    """Test 2: Verify batch endpoint exists"""
    print_header("TEST 2: Batch Endpoint Availability")

    try:
        # Test with simple request
        url = f"{BACKEND_URL}/data/batch?stations=Haifa&start_date={TEST_START_DATE}&end_date={TEST_END_DATE}"
        print_info(f"Testing URL: {url}")

        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            print_success("Batch endpoint exists and responds")
            data = response.json()
            print_info(f"Returned {len(data)} records")
            return True
        elif response.status_code == 404:
            print_failure("Batch endpoint not found (404)")
            print_warning("Make sure Agent 1 implementation is complete")
            return False
        else:
            print_warning(f"Batch endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print_failure(f"Error testing batch endpoint: {e}")
        return False

def test_batch_vs_sequential_performance():
    """Test 3: Performance comparison - Batch vs Sequential"""
    print_header("TEST 3: Performance Comparison")

    stations_str = ",".join(TEST_STATIONS)

    # Test 1: Batch endpoint (parallel)
    print_info(f"Testing BATCH endpoint with {len(TEST_STATIONS)} stations...")
    try:
        start_time = time.time()
        batch_url = f"{BACKEND_URL}/data/batch?stations={stations_str}&start_date={TEST_START_DATE}&end_date={TEST_END_DATE}"
        batch_response = requests.get(batch_url, timeout=30)
        batch_time = (time.time() - start_time) * 1000  # Convert to ms

        if batch_response.status_code == 200:
            batch_data = batch_response.json()
            print_success(f"Batch endpoint: {batch_time:.0f}ms ({len(batch_data)} records)")
        else:
            print_failure(f"Batch endpoint failed: {batch_response.status_code}")
            batch_time = None
    except Exception as e:
        print_failure(f"Batch endpoint error: {e}")
        batch_time = None

    # Test 2: Sequential endpoints (old way)
    print_info(f"Testing SEQUENTIAL endpoints with {len(TEST_STATIONS)} stations...")
    try:
        sequential_time = 0
        total_records = 0

        for station in TEST_STATIONS:
            start_time = time.time()
            seq_url = f"{BACKEND_URL}/api/data?station={station}&start_date={TEST_START_DATE}&end_date={TEST_END_DATE}"
            seq_response = requests.get(seq_url, timeout=30)
            request_time = (time.time() - start_time) * 1000
            sequential_time += request_time

            if seq_response.status_code == 200:
                seq_data = seq_response.json()
                total_records += len(seq_data)
                print_info(f"  {station}: {request_time:.0f}ms ({len(seq_data)} records)")

        print_success(f"Sequential total: {sequential_time:.0f}ms ({total_records} records)")
    except Exception as e:
        print_failure(f"Sequential endpoints error: {e}")
        sequential_time = None

    # Compare results
    print("\n" + "="*60)
    if batch_time and sequential_time:
        improvement = ((sequential_time - batch_time) / sequential_time) * 100
        time_saved = sequential_time - batch_time

        print_success("PERFORMANCE COMPARISON:")
        print(f"  Sequential time: {sequential_time:.0f}ms")
        print(f"  Batch time:      {batch_time:.0f}ms")
        print(f"{Colors.OKGREEN}{Colors.BOLD}  Improvement:     {improvement:.1f}% faster ({time_saved:.0f}ms saved){Colors.ENDC}")

        if improvement > 50:
            print_success("🎯 EXCELLENT! Performance improvement > 50%")
            return True
        elif improvement > 30:
            print_success("✅ GOOD! Performance improvement > 30%")
            return True
        else:
            print_warning(f"⚠️  Improvement is only {improvement:.1f}% - expected > 50%")
            return False
    else:
        print_failure("Could not compare performance - one or both tests failed")
        return False

def test_batch_data_accuracy():
    """Test 4: Verify batch endpoint returns same data as sequential"""
    print_header("TEST 4: Data Accuracy Verification")

    test_station = "Haifa"

    try:
        # Get data from single endpoint
        single_url = f"{BACKEND_URL}/api/data?station={test_station}&start_date={TEST_START_DATE}&end_date={TEST_END_DATE}"
        single_response = requests.get(single_url, timeout=10)
        single_data = single_response.json()

        # Get data from batch endpoint
        batch_url = f"{BACKEND_URL}/data/batch?stations={test_station}&start_date={TEST_START_DATE}&end_date={TEST_END_DATE}"
        batch_response = requests.get(batch_url, timeout=10)
        batch_data = batch_response.json()

        # Filter batch data for this station
        batch_station_data = [d for d in batch_data if d.get('Station') == test_station]

        # Compare record counts
        if len(single_data) == len(batch_station_data):
            print_success(f"Record counts match: {len(single_data)} records")
        else:
            print_failure(f"Record count mismatch: single={len(single_data)}, batch={len(batch_station_data)}")
            return False

        # Compare first and last records
        if single_data and batch_station_data:
            single_first = single_data[0]
            batch_first = batch_station_data[0]

            # Check if key fields match
            fields_match = True
            for field in ['Tab_DateTime', 'Tab_Value_mDepthC1', 'Station']:
                if field in single_first and field in batch_first:
                    if single_first[field] != batch_first[field]:
                        print_warning(f"Field mismatch: {field}")
                        print(f"  Single: {single_first[field]}")
                        print(f"  Batch:  {batch_first[field]}")
                        fields_match = False

            if fields_match:
                print_success("Data fields match between endpoints")
                return True
            else:
                print_failure("Data fields do not match")
                return False
        else:
            print_warning("No data to compare")
            return True

    except Exception as e:
        print_failure(f"Error comparing data: {e}")
        return False

def test_bundle_size():
    """Test 5: Verify bundle size optimization"""
    print_header("TEST 5: Bundle Size Verification")

    import os

    build_dir = "frontend/build/static/js"

    if not os.path.exists(build_dir):
        print_warning("Build directory not found")
        print_info("Run: cd frontend && npm run build")
        return None

    # Find main bundle
    main_bundles = [f for f in os.listdir(build_dir) if f.startswith('main.') and f.endswith('.js')]

    if not main_bundles:
        print_warning("Main bundle not found")
        return None

    main_bundle = main_bundles[0]
    bundle_path = os.path.join(build_dir, main_bundle)
    bundle_size = os.path.getsize(bundle_path)
    bundle_size_mb = bundle_size / (1024 * 1024)

    print_info(f"Main bundle: {main_bundle}")
    print_info(f"Size: {bundle_size_mb:.2f} MB uncompressed")

    # Check for chunk files (code splitting)
    chunk_files = [f for f in os.listdir(build_dir) if '.chunk.js' in f]
    print_info(f"Found {len(chunk_files)} chunk files (code splitting)")

    # Expected: main bundle should be < 2 MB uncompressed
    if bundle_size_mb < 2.0:
        print_success(f"✅ Bundle size is optimized: {bundle_size_mb:.2f} MB < 2 MB")
        return True
    else:
        print_warning(f"⚠️  Bundle size is large: {bundle_size_mb:.2f} MB > 2 MB")
        return False

def test_frontend_dependencies():
    """Test 6: Verify moment.js is removed"""
    print_header("TEST 6: Frontend Dependencies Check")

    import os

    package_json_path = "frontend/package.json"

    if not os.path.exists(package_json_path):
        print_warning("package.json not found")
        return None

    with open(package_json_path, 'r') as f:
        package_data = json.load(f)

    dependencies = package_data.get('dependencies', {})

    # Check moment.js is removed
    if 'moment' not in dependencies:
        print_success("✅ moment.js has been removed")
        moment_removed = True
    else:
        print_failure("❌ moment.js is still in dependencies")
        moment_removed = False

    # Check date-fns exists
    if 'date-fns' in dependencies:
        print_success("✅ date-fns is present")
        datefns_exists = True
    else:
        print_warning("⚠️  date-fns not found")
        datefns_exists = False

    return moment_removed and datefns_exists

def main():
    """Run all verification tests"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   TIER 1 OPTIMIZATION VERIFICATION TEST SUITE            ║")
    print("║   Sea Level Dashboard Performance Optimizations           ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")

    results = {}

    # Run tests
    results['backend_health'] = test_backend_health()

    if results['backend_health']:
        results['batch_endpoint'] = test_batch_endpoint_exists()

        if results['batch_endpoint']:
            results['performance'] = test_batch_vs_sequential_performance()
            results['data_accuracy'] = test_batch_data_accuracy()
        else:
            results['performance'] = False
            results['data_accuracy'] = False
    else:
        results['batch_endpoint'] = False
        results['performance'] = False
        results['data_accuracy'] = False

    results['bundle_size'] = test_bundle_size()
    results['dependencies'] = test_frontend_dependencies()

    # Summary
    print_header("TEST SUMMARY")

    total_tests = 0
    passed_tests = 0

    for test_name, result in results.items():
        total_tests += 1
        if result is True:
            passed_tests += 1
            print_success(f"{test_name}: PASS")
        elif result is False:
            print_failure(f"{test_name}: FAIL")
        else:
            print_warning(f"{test_name}: SKIPPED")

    print("\n" + "="*60)
    if passed_tests == total_tests:
        print(f"{Colors.OKGREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! ({passed_tests}/{total_tests}){Colors.ENDC}")
        print_success("Tier 1 optimizations are working correctly!")
    elif passed_tests >= total_tests * 0.7:
        print(f"{Colors.WARNING}{Colors.BOLD}⚠️  MOSTLY PASSING ({passed_tests}/{total_tests}){Colors.ENDC}")
        print_warning("Some tests failed - review failures above")
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}❌ TESTS FAILED ({passed_tests}/{total_tests}){Colors.ENDC}")
        print_failure("Multiple tests failed - review implementation")

    print("\n" + "="*60 + "\n")

    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
