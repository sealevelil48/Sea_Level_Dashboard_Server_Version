"""Simple test to debug the endpoint responses"""
import requests
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:30886"

print("Testing /api/data endpoint...")
url = f"{BASE_URL}/api/data?station=Haifa&start_date=2024-01-01&end_date=2024-01-07"
print(f"URL: {url}\n")

try:
    response = requests.get(url, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Response Length: {len(response.text)}")
    print(f"Response Text (first 500 chars):\n{response.text[:500]}")

    if response.text:
        try:
            data = response.json()
            print(f"\nJSON parsed successfully: {type(data)}")
            if isinstance(data, list):
                print(f"Number of records: {len(data)}")
                if data:
                    print(f"First record: {data[0]}")
            elif isinstance(data, dict):
                print(f"Response dict keys: {data.keys()}")
        except Exception as e:
            print(f"\nJSON parsing error: {e}")
    else:
        print("\nResponse is empty!")

except Exception as e:
    print(f"Request error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Testing /api/data/batch endpoint...")
url = f"{BASE_URL}/api/data/batch?stations=Haifa,Acre&start_date=2024-01-01&end_date=2024-01-07"
print(f"URL: {url}\n")

try:
    response = requests.get(url, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Response Length: {len(response.text)}")
    print(f"Response Text (first 500 chars):\n{response.text[:500]}")

    if response.text:
        try:
            data = response.json()
            print(f"\nJSON parsed successfully: {type(data)}")
            if isinstance(data, list):
                print(f"Number of records: {len(data)}")
                if data:
                    print(f"First record: {data[0]}")
            elif isinstance(data, dict):
                print(f"Response dict keys: {data.keys()}")
        except Exception as e:
            print(f"\nJSON parsing error: {e}")
    else:
        print("\nResponse is empty!")

except Exception as e:
    print(f"Request error: {e}")
    import traceback
    traceback.print_exc()
