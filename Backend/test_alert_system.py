#!/usr/bin/env python
"""
ALERT SYSTEM END-TO-END TEST
Tests alert creation, triggering, and database updates
"""

import requests
import json
import mysql.connector
from datetime import datetime
import time

BASE_URL = "http://127.0.0.1:5001"
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Uday@2004",
    "database": "metalcur"
}

def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_step(num, title):
    print(f"\n[STEP {num}] {title}")
    print("-" * 80)

def get_current_prices():
    """Retrieve current live prices from API"""
    try:
        response = requests.get(f"{BASE_URL}/api/prices/live", timeout=5)
        data = response.json()
        
        if data.get('success') and data.get('prices'):
            prices_raw = data['prices']
            # Extract just the price values
            prices = {
                'gold': prices_raw.get('gold', {}).get('price', 0) / 10,  # Convert to per gram
                'silver': prices_raw.get('silver', {}).get('price', 0) / 1000,  # Convert to per gram
                'platinum': prices_raw.get('platinum', {}).get('price', 0) / 10,  # Convert to per gram
                'usd_inr': prices_raw.get('usd_inr', {}).get('price', 0)
            }
            return prices
        else:
            print(f"❌ Failed to fetch prices: {data}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def get_user_id():
    """Get test user ID (first user in database)"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT user_id FROM users LIMIT 1")
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            return user['user_id']
        else:
            print("❌ No users found in database. Please create a user first.")
            return None
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None

def create_alert(user_id, metal_type, condition_type, target_price):
    """Create a demo alert via API"""
    try:
        payload = {
            "metal_type": metal_type,
            "condition_type": condition_type,
            "target_price": target_price
        }
        
        response = requests.post(
            f"{BASE_URL}/api/alerts",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        result = response.json()
        
        if result.get('success'):
            alert_id = result.get('alert_id')
            print(f"✅ Alert created successfully!")
            print(f"   Alert ID: {alert_id}")
            print(f"   Metal: {metal_type}")
            print(f"   Condition: {condition_type}")
            print(f"   Target Price: ₹{target_price:,.2f}")
            return alert_id
        else:
            print(f"❌ Failed to create alert: {result}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def verify_alert_in_db(alert_id, user_id):
    """Check alert was stored in database"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM alerts WHERE alert_id = %s AND user_id = %s",
            (alert_id, user_id)
        )
        alert = cur.fetchone()
        cur.close()
        conn.close()
        
        if alert:
            print(f"✅ Alert found in database!")
            print(f"   Alert ID: {alert['alert_id']}")
            print(f"   Metal Type: {alert['metal_type']}")
            print(f"   Condition: {alert['condition_type']}")
            print(f"   Target Price: ₹{float(alert['target_price']):,.2f}")
            print(f"   Status: {alert['status']}")
            print(f"   Created: {alert['created_at']}")
            return alert
        else:
            print(f"❌ Alert not found in database!")
            return None
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None

def trigger_alerts_manually():
    """Trigger alert check manually (don't wait 2 minutes)"""
    try:
        response = requests.get(f"{BASE_URL}/api/admin/trigger_alerts", timeout=5)
        result = response.text
        print(f"✅ Manual trigger response: {result}")
        return True
    except Exception as e:
        print(f"❌ Error triggering alerts: {e}")
        return False

def check_alert_after_trigger(alert_id, user_id):
    """Check if alert status changed to 'triggered'"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM alerts WHERE alert_id = %s AND user_id = %s",
            (alert_id, user_id)
        )
        alert = cur.fetchone()
        cur.close()
        conn.close()
        
        if alert:
            print(f"✅ Alert found after trigger!")
            print(f"   Status: {alert['status']}")
            
            if alert['status'] == 'triggered':
                print(f"   ✅✅ ALERT TRIGGERED SUCCESSFULLY! ✅✅")
                return True
            else:
                print(f"   ⚠️ Status is '{alert['status']}' (expected 'triggered')")
                return False
        else:
            print(f"❌ Alert not found!")
            return None
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None

def main():
    print_header("ALERT SYSTEM END-TO-END TEST")
    
    # STEP 1: Get current prices
    print_step(1, "Retrieve Current Live Prices")
    prices = get_current_prices()
    
    if not prices:
        print("❌ Could not get prices. Aborting test.")
        return
    
    gold_price = prices.get('gold', 0) * 10  # Convert to per 10g
    silver_price = prices.get('silver', 0) * 1000  # Convert to per kg
    
    print(f"\n📊 Current Prices:")
    print(f"   Gold (per 10g):  ₹{gold_price:,.2f}")
    print(f"   Silver (per kg): ₹{silver_price:,.2f}")
    
    # STEP 2: Get user ID
    print_step(2, "Get Test User")
    user_id = get_user_id()
    
    if not user_id:
        print("❌ Could not get user. Aborting test.")
        return
    
    print(f"✅ Using User ID: {user_id}")
    
    # STEP 3: Create test alert
    print_step(3, "Create Demo Alert (GOLD BELOW - will trigger immediately)")
    
    # Set target BELOW current price so it triggers immediately
    target_price = gold_price - 100
    
    print(f"\n📍 Alert Configuration:")
    print(f"   Metal: GOLD")
    print(f"   Condition: BELOW")
    print(f"   Current Price: ₹{gold_price:,.2f}")
    print(f"   Target Price: ₹{target_price:,.2f}")
    print(f"   ➜ Current ({gold_price}) is ABOVE Target ({target_price})")
    print(f"   ➜ Alert will trigger when price goes BELOW ₹{target_price:,.2f}")
    print(f"   ➜ Since current is already above, this test alert should trigger immediately!")
    
    alert_id = create_alert(user_id, "gold", "below", target_price)
    
    if not alert_id:
        print("❌ Could not create alert. Aborting test.")
        return
    
    # STEP 4: Verify alert in database
    print_step(4, "Verify Alert in Database (Before Trigger)")
    alert_before = verify_alert_in_db(alert_id, user_id)
    
    if not alert_before:
        print("❌ Alert not saved. Aborting test.")
        return
    
    print(f"\n✅ Alert Status BEFORE trigger: {alert_before['status']}")
    
    # STEP 5: Manually trigger alert check
    print_step(5, "Manually Trigger Alert Check")
    print("🔔 Calling /api/admin/trigger_alerts endpoint...")
    
    time.sleep(1)  # Small delay
    trigger_alerts_manually()
    
    time.sleep(2)  # Give database time to update
    
    # STEP 6: Check database after trigger
    print_step(6, "Check Alert Status After Trigger")
    print("🔍 Checking database for status change...")
    
    alert_after = check_alert_after_trigger(alert_id, user_id)
    
    if alert_after is True:
        print(f"\n🎉🎉🎉 TEST PASSED! Alert triggered successfully! 🎉🎉🎉")
    elif alert_after is False:
        print(f"\n❌ TEST FAILED! Alert status did not change to 'triggered'")
    else:
        print(f"\n❌ TEST FAILED! Could not verify alert")
    
    # STEP 7: Summary
    print_step(7, "Test Summary")
    print(f"\n📋 Results:")
    print(f"   Alert ID: {alert_id}")
    print(f"   User ID: {user_id}")
    print(f"   Metal: GOLD")
    print(f"   Condition: BELOW ₹{target_price:,.2f}")
    print(f"   Current Price: ₹{gold_price:,.2f}")
    
    if alert_after is True:
        print(f"\n✅ STATUS BEFORE: {alert_before['status']}")
        print(f"✅ STATUS AFTER:  {alert_after if isinstance(alert_after, str) else 'triggered'}")
        print(f"\n🎉 ALERT SYSTEM IS WORKING CORRECTLY! 🎉")
    else:
        print(f"\n❌ ALERT SYSTEM HAS ISSUES - Status did not change")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
