from urllib import response
import requests

BASE_URL = "http://localhost:8000"  # Update if hosted elsewhere

# Sample request payload that should match your loaded pricing data
payload = {
    "start_month": "August 2025",
    "utility": "Centerpoint",
    "congestion_zone": "HOUSTON",
    "load_factor": "HI",
    "annual_volume": 300000
}

# Test the /get-prices endpoint
def test_get_prices():
    url = f"{BASE_URL}/get-prices"
    response = requests.post(url, json=payload)
    assert response.status_code == 200, f"Failed with status: {response.status_code}, body: {response.text}"
    data = response.json()
    print("Received", len(data), "price results")
    for row in data:
        print(row)

# Test the debug endpoint to inspect filtering
def test_debug_filters():
    print("Payload:", payload)
    url = f"{BASE_URL}/debug-pricing-filters"
    response = requests.post(url, json=payload)
    #assert response.status_code == 200
    print("Status Code:", response.status_code)
    print("Response Text:", response.text)
    if response.status_code != 200:
        print("Error: could not retrieve debug filters.")
        return  # <--- Prevent accessing undefined `debug_data`

    debug_data = response.json()
    for rep, result in debug_data.items():
        print(f"\nDebug Filter Matches for {rep}:")
        print(f"  Match Count: {result['match_count']}")
        print(f"  Sample: {result['sample']}")

if __name__ == "__main__":
    print("--- Testing /get-prices ---")
    test_get_prices()
    print("\n--- Testing /debug-pricing-filters ---")
    test_debug_filters()
