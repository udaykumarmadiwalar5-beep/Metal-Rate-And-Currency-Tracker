#!/usr/bin/env python3
import requests
import json
import time

time.sleep(2)

# Test 1: Live prices endpoint
print("\n🔍 Testing /api/prices/live endpoint...")
try:
    r = requests.get('http://localhost:5000/api/prices/live', timeout=5)
    print(f"Status: {r.status_code}")
    data = r.json()
    print(f"✅ Live Prices Response:")
    print(f"  - Base Prices: Gold ₹{data['success'].get('prices', {}).get('gold')}/g")
    print(f"  - Regional States Supported: {len(data['success'].get('regional_prices', {}))}")
    if data['success'].get('regional_prices'):
        states = list(data['success']['regional_prices'].keys())[:3]
        print(f"  - Sample States: {states}")
        for state in states:
            prices = data['success']['regional_prices'][state]
            print(f"    - {state}: Gold ₹{prices['gold']}/g")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Regional pricing for specific state
print("\n🔍 Testing /api/prices/regional endpoint...")
try:
    r = requests.get('http://localhost:5000/api/prices/regional?state=Maharashtra', timeout=5)
    print(f"Status: {r.status_code}")
    data = r.json()
    if data.get('success'):
        print(f"✅ Maharashtra Prices:")
        prices = data['success'].get('prices', {})
        print(f"  - Gold: ₹{prices.get('gold')}/g")
        print(f"  - Silver: ₹{prices.get('silver')}/g")
        print(f"  - Platinum: ₹{prices.get('platinum')}/g")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Chart data
print("\n🔍 Testing /api/prices/chart endpoint...")
try:
    r = requests.get('http://localhost:5000/api/prices/chart?metal=gold&range=1d', timeout=5)
    print(f"Status: {r.status_code}")
    data = r.json()
    if data.get('success'):
        gold_data = data['success'].get('data', {}).get('gold', {})
        print(f"✅ Gold Chart Data:")
        print(f"  - Data Points: {len(gold_data.get('line', []))}")
        if gold_data.get('line'):
            print(f"  - Latest: {gold_data['line'][-1]}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n✅ All tests completed!")
