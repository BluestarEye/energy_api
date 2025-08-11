import os
import logging
import time
import pandas as pd
from urllib import response
import requests

BASE_URL = "http://localhost:8000"  # Update if hosted elsewhere

# Sample request payload that should match your loaded pricing data
payload = {
    "start_month": "August 2025",
    "utility": "Oncor",
    "zipcode": "75078",  # Example ZIP code
    #"congestion_zone": "HOUSTON",
    "load_factor": "HI",
    "annual_volume": 300000
}

def ensure_zip_map():
    os.makedirs("pricing_data", exist_ok=True)
    path = os.path.join("pricing_data", "ZipCodeMap.xlsx")
    # Minimal map: Houston ZIP -> HOUSTON
    df = pd.DataFrame({
        "Zip": ["75078"],
        "Zone": ["NORTH"]
    })
    df.to_excel(path, index=False, engine="openpyxl")
    # Tell the server to reload the map
    r = requests.post(f"{BASE_URL}/debug/reload-zip-map", timeout=10)
    assert r.status_code == 200, f"reload-zip-map failed: {r.status_code} {r.text}"
    data = r.json()
    assert data.get("loaded_rows", 0) >= 1, f"expected >=1 loaded_rows, got {data}"

# Test the /get-prices endpoint
def test_get_prices():
    ensure_zip_map()  # Ensure ZIP map is loaded
    url = f"{BASE_URL}/get-prices"
    response = requests.post(url, json=payload)
    assert response.status_code == 200, f"Failed with status: {response.status_code}, body: {response.text}"
    data = response.json()
    print("Received", len(data), "price results")
    for row in data:
        print(row)

# Test the debug endpoint to inspect filtering
#def test_debug_filters():
#    print("Payload:", payload)
#    url = f"{BASE_URL}/debug-pricing-filters"
#    response = requests.post(url, json=payload)
#    #assert response.status_code == 200
#    print("Status Code:", response.status_code)
#    print("Response Text:", response.text)
#    if response.status_code != 200:
#        print("Error: could not retrieve debug filters.")
#        return  # <--- Prevent accessing undefined `debug_data`

#    debug_data = response.json()
#    for rep, result in debug_data.items():
#        print(f"\nDebug Filter Matches for {rep}:")
#        print(f"  Match Count: {result['match_count']}")
#        print(f"  Sample: {result['sample']}")

if __name__ == "__main__":
    print("--- Testing /get-prices ---")
    test_get_prices()
    #print("\n--- Testing /debug-pricing-filters ---")
    #test_debug_filters()
