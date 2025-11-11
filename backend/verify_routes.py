"""Verify which routes are available on the server"""
import requests

BASE_URL = "http://127.0.0.1:30886"

print("Checking API documentation...")
try:
    response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
    if response.status_code == 200:
        openapi_spec = response.json()
        print("\nAvailable API routes:")
        paths = openapi_spec.get('paths', {})
        for path in sorted(paths.keys()):
            methods = list(paths[path].keys())
            print(f"  {path:40s} {', '.join(methods).upper()}")

        # Check if batch endpoint exists
        if '/api/data/batch' in paths:
            print("\n✓ Batch endpoint is registered!")
        else:
            print("\n✗ Batch endpoint NOT found!")
            print("\nServer needs to be restarted to pick up the new route.")
            print("Please restart the backend server:")
            print("  1. Stop the current server (Ctrl+C)")
            print("  2. Run: python backend/local_server.py")
    else:
        print(f"OpenAPI spec not available (status {response.status_code})")
except Exception as e:
    print(f"Error: {e}")
