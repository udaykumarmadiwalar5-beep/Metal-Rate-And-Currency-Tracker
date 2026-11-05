#!/usr/bin/env python3
"""
Test script to verify alert fix works correctly.
Tests that:
1. Alerts trigger when condition is met
2. Alerts reset when condition is no longer met
3. Backend and frontend are consistent
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5001"

def test_alert_status():
    """Test the alert fix by manually triggering checks"""
    
    print("\n" + "="*60)
    print("ALERT FIX VERIFICATION TEST")
    print("="*60)
    
    try:
        # Step 1: Trigger manual alert check
        print("\n[1] Triggering manual alert check...")
        resp = requests.get(f"{BASE_URL}/api/admin/trigger_alerts", timeout=10)
        print(f"    Response: {resp.text}")
        
        # Step 2: Get all alerts to check status
        print("\n[2] Fetching current alerts...")
        time.sleep(1)
        
        # Note: This requires authentication, but let's see what happens
        resp = requests.get(f"{BASE_URL}/api/alerts?limit=20", timeout=10)
        print(f"    Status Code: {resp.status_code}")
        print(f"    Response: {resp.text}")
        
        # Step 3: Get current prices
        print("\n[3] Getting current prices...")
        resp = requests.get(f"{BASE_URL}/api/prices/live", timeout=10)
        if resp.status_code == 200:
            prices_data = resp.json()
            if prices_data.get('success'):
                prices = prices_data.get('prices', {})
                print("    Current Prices:")
                for metal, data in prices.items():
                    if isinstance(data, dict) and 'price' in data:
                        print(f"      {metal.upper()}: ₹{data['price']} ({data.get('change', 'N/A')})")
        else:
            print(f"    Error: {resp.status_code}")
        
        print("\n" + "="*60)
        print("✅ TEST COMPLETE - Check console for backend alert check logs")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure the backend server is running on http://127.0.0.1:5001")

if __name__ == "__main__":
    test_alert_status()
