"""
Test script for batch endpoint functionality
Compares single station queries vs batch query to verify correctness
"""
import requests
import json
import time
import sys
from datetime import datetime, timedelta

# Set UTF-8 encoding for console output
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configuration
BASE_URL = "http://127.0.0.1:30886"
TEST_STATIONS = ["Haifa", "Acre", "Ashdod"]
START_DATE = "2024-01-01"
END_DATE = "2024-01-07"

def test_single_station_queries():
    """Test existing single-station endpoint (baseline)"""
    print("\n" + "="*60)
    print("TEST 1: Single Station Queries (Sequential)")
    print("="*60)

    all_results = {}
    total_time = 0

    for station in TEST_STATIONS:
        start_time = time.time()
        url = f"{BASE_URL}/api/data?station={station}&start_date={START_DATE}&end_date={END_DATE}"
        print(f"\n[{station}] Fetching data...")

        try:
            response = requests.get(url, timeout=30)
            elapsed = time.time() - start_time
            total_time += elapsed

            if response.status_code == 200:
                data = response.json()
                all_results[station] = data
                print(f"  ✓ Success: {len(data)} records in {elapsed:.2f}s")
            else:
                print(f"  ✗ Failed: HTTP {response.status_code}")
                all_results[station] = []
        except Exception as e:
            print(f"  ✗ Error: {e}")
            all_results[station] = []

    print(f"\n{'─'*60}")
    print(f"Total Time (Sequential): {total_time:.2f}s")
    print(f"Total Records: {sum(len(v) for v in all_results.values())}")

    return all_results, total_time

def test_batch_query():
    """Test new batch endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Batch Query (Single Request)")
    print("="*60)

    stations_param = ",".join(TEST_STATIONS)
    url = f"{BASE_URL}/api/data/batch?stations={stations_param}&start_date={START_DATE}&end_date={END_DATE}"

    print(f"\n[BATCH] Fetching data for {len(TEST_STATIONS)} stations...")

    start_time = time.time()
    try:
        response = requests.get(url, timeout=30)
        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()

            # Get headers
            agg_level = response.headers.get('X-Aggregation-Level', 'N/A')
            record_count = response.headers.get('X-Record-Count', 'N/A')
            stations_count = response.headers.get('X-Stations-Count', 'N/A')

            print(f"  ✓ Success: {len(data)} total records in {elapsed:.2f}s")
            print(f"  • Aggregation Level: {agg_level}")
            print(f"  • Stations Count: {stations_count}")
            print(f"  • Record Count Header: {record_count}")

            # Group by station
            batch_results = {}
            for record in data:
                station = record.get('Station')
                if station not in batch_results:
                    batch_results[station] = []
                batch_results[station].append(record)

            print(f"\n  Records by Station:")
            for station in TEST_STATIONS:
                count = len(batch_results.get(station, []))
                print(f"    • {station}: {count} records")

            return batch_results, elapsed
        else:
            print(f"  ✗ Failed: HTTP {response.status_code}")
            print(f"  Response: {response.text}")
            return {}, elapsed

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  ✗ Error: {e}")
        return {}, elapsed

def compare_results(single_results, batch_results):
    """Compare single vs batch results"""
    print("\n" + "="*60)
    print("TEST 3: Data Validation")
    print("="*60)

    all_match = True

    for station in TEST_STATIONS:
        single_data = single_results.get(station, [])
        batch_data = batch_results.get(station, [])

        print(f"\n[{station}]")
        print(f"  Single Query: {len(single_data)} records")
        print(f"  Batch Query:  {len(batch_data)} records")

        if len(single_data) == len(batch_data):
            print(f"  ✓ Record count matches")
        else:
            print(f"  ✗ Record count MISMATCH")
            all_match = False

        # Compare a few sample records if available
        if single_data and batch_data:
            # Compare first record
            single_first = single_data[0]
            batch_first = batch_data[0]

            # Check key fields
            key_fields = ['Tab_DateTime', 'Tab_Value_mDepthC1']
            fields_match = True
            for field in key_fields:
                if field in single_first and field in batch_first:
                    if single_first[field] == batch_first[field]:
                        print(f"  ✓ First record {field} matches: {single_first[field]}")
                    else:
                        print(f"  ✗ First record {field} MISMATCH:")
                        print(f"      Single: {single_first[field]}")
                        print(f"      Batch:  {batch_first[field]}")
                        fields_match = False
                        all_match = False

    return all_match

def test_error_handling():
    """Test error cases"""
    print("\n" + "="*60)
    print("TEST 4: Error Handling")
    print("="*60)

    # Test 1: Empty stations list
    print("\n[Test 4.1] Empty stations list")
    url = f"{BASE_URL}/api/data/batch?stations=&start_date={START_DATE}&end_date={END_DATE}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 404:
            print("  ✓ Correctly returned 404 for empty stations")
        else:
            print(f"  ✗ Expected 404, got {response.status_code}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # Test 2: Invalid station
    print("\n[Test 4.2] Invalid station name")
    url = f"{BASE_URL}/api/data/batch?stations=InvalidStation&start_date={START_DATE}&end_date={END_DATE}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code in [404, 200]:  # 200 with empty data is also acceptable
            data = response.json() if response.status_code == 200 else []
            if isinstance(data, list) and len(data) == 0:
                print("  ✓ Correctly returned empty result for invalid station")
            elif isinstance(data, dict) and data.get('message') == 'No data found':
                print("  ✓ Correctly returned 'No data found' message")
            else:
                print(f"  ? Returned data: {data}")
        else:
            print(f"  ? Status: {response.status_code}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # Test 3: Single station in batch (should work)
    print("\n[Test 4.3] Single station in batch endpoint")
    url = f"{BASE_URL}/api/data/batch?stations=Haifa&start_date={START_DATE}&end_date={END_DATE}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Successfully returned {len(data)} records for single station")
        else:
            print(f"  ✗ Failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

def check_server_status():
    """Check if the server is running"""
    print("\n" + "="*60)
    print("CHECKING SERVER STATUS")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/api/stations", timeout=5)
        if response.status_code == 200:
            print(f"✓ Server is running at {BASE_URL}")
            return True
        else:
            print(f"✗ Server returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to server at {BASE_URL}")
        print("  Please start the backend server first:")
        print("  python backend/local_server-prod.py")
        return False
    except Exception as e:
        print(f"✗ Error checking server: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("BATCH ENDPOINT TEST SUITE")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Test Stations: {', '.join(TEST_STATIONS)}")
    print(f"Date Range: {START_DATE} to {END_DATE}")

    # Check if server is running
    if not check_server_status():
        return

    try:
        # Test 1: Single station queries
        single_results, single_time = test_single_station_queries()

        # Test 2: Batch query
        batch_results, batch_time = test_batch_query()

        # Test 3: Compare results
        if single_results and batch_results:
            results_match = compare_results(single_results, batch_results)
        else:
            results_match = False
            print("\n✗ Cannot compare results - one or both queries failed")

        # Test 4: Error handling
        test_error_handling()

        # Performance summary
        print("\n" + "="*60)
        print("PERFORMANCE SUMMARY")
        print("="*60)
        print(f"Sequential Queries: {single_time:.2f}s")
        print(f"Batch Query:        {batch_time:.2f}s")

        if batch_time > 0 and single_time > 0:
            improvement = ((single_time - batch_time) / single_time) * 100
            speedup = single_time / batch_time
            print(f"Improvement:        {improvement:.1f}% faster")
            print(f"Speedup Factor:     {speedup:.2f}x")

        # Final verdict
        print("\n" + "="*60)
        print("FINAL VERDICT")
        print("="*60)

        if results_match and batch_time < single_time:
            print("✓ ALL TESTS PASSED")
            print("✓ Batch endpoint is faster and returns correct data")
        elif results_match:
            print("⚠ Data is correct but performance needs review")
        else:
            print("✗ TESTS FAILED - Data mismatch or errors occurred")

    except Exception as e:
        print(f"\n✗ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
