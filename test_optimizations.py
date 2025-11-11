"""Simple verification tests for Tier 1 optimizations"""
import requests
import time
import json
import os

BACKEND_URL = "http://127.0.0.1:30886"
TEST_STATIONS = ["Haifa", "Acre", "Ashdod"]

print("\n" + "="*60)
print("TIER 1 OPTIMIZATION VERIFICATION")
print("="*60 + "\n")

# Test 1: Backend Health
print("TEST 1: Backend Health Check...")
try:
    r = requests.get(f"{BACKEND_URL}/health", timeout=5)
    if r.status_code == 200:
        print("PASS - Backend is running")
    else:
        print(f"FAIL - Backend returned {r.status_code}")
except:
    print("FAIL - Backend not accessible")
    print("Start with: python backend/local_server-prod.py")
    exit(1)

# Test 2: Batch Endpoint
print("\nTEST 2: Batch Endpoint Check...")
try:
    url = f"{BACKEND_URL}/data/batch?stations=Haifa"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        print(f"PASS - Batch endpoint works ({len(r.json())} records)")
    else:
        print(f"FAIL - Batch endpoint returned {r.status_code}")
except Exception as e:
    print(f"FAIL - {e}")

# Test 3: Performance Comparison
print("\nTEST 3: Performance Comparison...")
stations_str = ",".join(TEST_STATIONS)

# Batch timing
start = time.time()
batch_url = f"{BACKEND_URL}/data/batch?stations={stations_str}"
r = requests.get(batch_url, timeout=30)
batch_time = (time.time() - start) * 1000

# Sequential timing
seq_time = 0
for station in TEST_STATIONS:
    start = time.time()
    url = f"{BACKEND_URL}/api/data?station={station}"
    requests.get(url, timeout=30)
    seq_time += (time.time() - start) * 1000

improvement = ((seq_time - batch_time) / seq_time) * 100
print(f"Sequential: {seq_time:.0f}ms")
print(f"Batch:      {batch_time:.0f}ms")
print(f"Improvement: {improvement:.1f}% faster ({seq_time-batch_time:.0f}ms saved)")

if improvement > 50:
    print("PASS - Excellent performance improvement!")
else:
    print(f"WARNING - Only {improvement:.1f}% improvement")

# Test 4: Bundle Size
print("\nTEST 4: Bundle Size Check...")
build_dir = "frontend/build/static/js"
if os.path.exists(build_dir):
    main_bundles = [f for f in os.listdir(build_dir) if f.startswith('main.')]
    if main_bundles:
        bundle_path = os.path.join(build_dir, main_bundles[0])
        size_mb = os.path.getsize(bundle_path) / (1024 * 1024)
        print(f"Main bundle: {size_mb:.2f} MB")
        if size_mb < 2.0:
            print("PASS - Bundle size optimized")
        else:
            print("WARNING - Bundle size large")
    else:
        print("SKIP - No bundle found")
else:
    print("SKIP - Build directory not found")

# Test 5: Dependencies
print("\nTEST 5: Dependencies Check...")
try:
    with open("frontend/package.json") as f:
        pkg = json.load(f)
    deps = pkg.get('dependencies', {})

    if 'moment' not in deps:
        print("PASS - moment.js removed")
    else:
        print("FAIL - moment.js still present")

    if 'date-fns' in deps:
        print("PASS - date-fns present")
    else:
        print("FAIL - date-fns missing")
except:
    print("SKIP - Could not check dependencies")

print("\n" + "="*60)
print("VERIFICATION COMPLETE")
print("="*60 + "\n")
