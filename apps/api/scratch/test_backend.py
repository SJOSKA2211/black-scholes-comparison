import json

import requests

BASE_URL = "http://localhost"  # Through Nginx

def test_health() -> None:
    print("Testing /health...")
    try:
        response = requests.get(f"{BASE_URL}/health", verify=False)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def test_root() -> None:
    print("\nTesting /...")
    try:
        response = requests.get(f"{BASE_URL}/", verify=False)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_health()
    test_root()
