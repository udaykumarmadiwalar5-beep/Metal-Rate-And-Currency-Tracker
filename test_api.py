#!/usr/bin/env python3
"""Quick test of live metal price API"""
import requests
import json

BASE_URL = "http://localhost:5000"

print("Testing Live Metal Price Tracking System")
print("=" * 80)

# Test 1: Live Prices
print("\n[TEST 1] /api/prices/live")
try:
    r = requests.get(f"{BASE_URL}/api/prices/live", timeout=5)
    d = r.json()
    
    print(f"Status: {r.status_code}")
    print(f"Success: {d.get('success')}")
    
    if d.get('success'):
        prices = d.get('prices', {})
        print(f"\nBase Prices:")
        print(f"  Gold:       ₹{prices.get('gold'):>12,.2f} per 10g")
        print(f"  Silver:     ₹{prices.get('silver'):>12,.2f} per gram")
        print(f"  Platinum:   ₹{prices.get('platinum'):>12,.2f} per gram")
        print(f"  USD/INR:    {prices.get('usd_inr'):>12,.2f}")
        
        regional = d.get('regional_prices', {})
        print(f"\nRegional Pricing: {len(regional)} states/UTs")
        
        if len(regional) > 0:
            states_list = list(regional.keys())[:3]
            for state in states_list:
                print(f"  {state}: Gold ₹{regional[state].get('gold', 0):,.2f}")

except Exception as e:
    print(f"Error: {e}")

# Test 2: Chart Data
print("\n[TEST 2] /api/prices/chart?metal=gold&range=1d")
try:
    r = requests.get(f"{BASE_URL}/api/prices/chart?metal=gold&range=1d", timeout=5)
    d = r.json()
    
    print(f"Status: {r.status_code}")
    if d.get('success'):
        gold_data = d.get('data', {}).get('gold', {})
        line_pts = gold_data.get('line', [])
        ohlc_pts = gold_data.get('ohlc', [])
        
        print(f"Line points: {len(line_pts)}")
        print(f"OHLC candles: {len(ohlc_pts)}")
        
        if line_pts:
            print(f"Latest: {line_pts[-1]}")

except Exception as e:
    print(f"Error: {e}")

# Test 3: News
print("\n[TEST 3] /api/news")
try:
    r = requests.get(f"{BASE_URL}/api/news", timeout=5)
    d = r.json()
    
    print(f"Status: {r.status_code}")
    if d.get('success'):
        articles = d.get('data', [])
        print(f"Articles: {len(articles)}")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
print("✅ System Test Complete")
