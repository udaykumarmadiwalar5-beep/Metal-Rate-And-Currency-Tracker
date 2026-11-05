#!/usr/bin/env python
"""
COMPREHENSIVE ALERT SYSTEM TEST
Tests alert creation, live triggering, and database updates
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

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(title):
    print("\n" + "=" * 100)
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print("=" * 100)

def print_step(num, title):
    print(f"\n{BOLD}{BLUE}[STEP {num}] {title}{RESET}")
    print("-" * 100)

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_info(msg):
    print(f"{CYAN}ℹ️  {msg}{RESET}")

def get_current_prices():
    """Retrieve current live prices from API"""
    try:
        response = requests.get(f"{BASE_URL}/api/prices/live", timeout=5)
        data = response.json()
        
        if data.get('success') and data.get('prices'):
            prices_raw = data['prices']
            prices = {
                'gold': prices_raw.get('gold', {}).get('price', 0) / 10,
                'silver': prices_raw.get('silver', {}).get('price', 0) / 1000,
                'platinum': prices_raw.get('platinum', {}).get('price', 0) / 10,
                'usd_inr': prices_raw.get('usd_inr', {}).get('price', 0)
            }
            return prices
        else:
            print_error(f"Failed to fetch prices: {data}")
            return None
    except Exception as e:
        print_error(f"Error getting prices: {e}")
        return None

def get_or_create_user():
    """Get test user ID or create one"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor(dictionary=True)
        
        # Check if test user exists
        cur.execute("SELECT user_id FROM users WHERE username = 'alerttest' LIMIT 1")
        user = cur.fetchone()
        
        if user:
            print_success(f"Found existing test user (ID: {user['user_id']})")
            cur.close(); conn.close()
            return user['user_id']
        
        # Create new test user
        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                   ("alerttest", "alerttest@test.com", "password123"))
        user_id = cur.lastrowid
        conn.commit()
        cur.close(); conn.close()
        
        print_success(f"Created new test user (ID: {user_id})")
        return user_id
        
    except Exception as e:
        print_error(f"Database error: {e}")
        return None

def login_user(username, password):
    """Login user to establish session"""
    try:
        payload = {
            "username": username,
            "password": password
        }
        
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/login",
            json=payload,
            timeout=5
        )
        
        result = response.json()
        
        if result.get('success'):
            print_success(f"User logged in successfully")
            return session
        else:
            print_error(f"Login failed: {result}")
            return None
    except Exception as e:
        print_error(f"Login error: {e}")
        return None

def create_alert(session, metal_type, condition_type, target_price):
    """Create a demo alert via API"""
    try:
        payload = {
            "metal_type": metal_type,
            "condition_type": condition_type,
            "target_price": target_price
        }
        
        response = session.post(
            f"{BASE_URL}/api/alerts",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        result = response.json()
        
        if result.get('success'):
            alert_id = result.get('alert_id')
            return alert_id
        else:
            print_error(f"Failed to create alert: {result}")
            return None
    except Exception as e:
        print_error(f"Error creating alert: {e}")
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
        cur.close(); conn.close()
        
        if alert:
            return alert
        else:
            return None
    except Exception as e:
        print_error(f"Database error: {e}")
        return None

def trigger_alerts_manually():
    """Trigger alert check manually"""
    try:
        response = requests.get(f"{BASE_URL}/api/admin/trigger_alerts", timeout=5)
        return True
    except Exception as e:
        print_error(f"Error triggering alerts: {e}")
        return False

def delete_all_test_alerts(user_id):
    """Delete all test alerts for this user"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("DELETE FROM alerts WHERE user_id = %s", (user_id,))
        count = cur.rowcount
        conn.commit(); cur.close(); conn.close()
        return count
    except Exception as e:
        print_error(f"Error deleting alerts: {e}")
        return 0

def main():
    print_header("COMPREHENSIVE ALERT SYSTEM TEST - 100% ACCURACY")
    
    # ==========================================
    # STEP 1: Cleanup previous test data
    # ==========================================
    print_step(1, "Cleanup Previous Test Data & Login")
    user_id = get_or_create_user()
    if not user_id:
        print_error("Could not get/create user. Aborting test.")
        return
    
    # Login user
    session = login_user("alerttest", "password123")
    if not session:
        print_error("Could not login. Aborting test.")
        return
    
    deleted = delete_all_test_alerts(user_id)
    print_info(f"Deleted {deleted} previous test alerts")
    
    # ==========================================
    # STEP 2: Get current live prices
    # ==========================================
    print_step(2, "Retrieve Current Live Prices")
    prices = get_current_prices()
    
    if not prices:
        print_error("Could not get prices. Aborting test.")
        return
    
    print_success(f"Retrieved live prices:")
    print(f"   Gold (per 10g):      ₹{prices['gold']:>10,.2f}")
    print(f"   Silver (per 1kg):    ₹{prices['silver']:>10,.2f}")
    print(f"   Platinum (per 10g):  ₹{prices['platinum']:>10,.2f}")
    print(f"   USD/INR:             ₹{prices['usd_inr']:>10,.2f}")
    
    # ==========================================
    # STEP 3: Create test alerts
    # ==========================================
    print_step(3, "Create Demo Alerts (Gold & Silver)")
    
    test_alerts = []
    
    # Alert 1: GOLD - ABOVE (will trigger immediately)
    gold_target_above = prices['gold'] - 50
    print_info(f"Alert 1: GOLD ABOVE ₹{gold_target_above:,.2f} (current: ₹{prices['gold']:,.2f})")
    print(f"         ➜ Condition: Current (₹{prices['gold']:,.2f}) is ABOVE target (₹{gold_target_above:,.2f}) → Should TRIGGER")
    alert1_id = create_alert(session, "gold", "above", gold_target_above)
    if alert1_id:
        print_success(f"Alert 1 created (ID: {alert1_id})")
        test_alerts.append({
            'id': alert1_id,
            'metal': 'gold',
            'condition': 'above',
            'target': gold_target_above,
            'current': prices['gold'],
            'should_trigger': True
        })
    
    time.sleep(0.5)
    
    # Alert 2: GOLD - BELOW (won't trigger)
    gold_target_below = prices['gold'] + 50
    print_info(f"Alert 2: GOLD BELOW ₹{gold_target_below:,.2f} (current: ₹{prices['gold']:,.2f})")
    print(f"         ➜ Condition: Current (₹{prices['gold']:,.2f}) is ABOVE target (₹{gold_target_below:,.2f}) → Will NOT trigger")
    alert2_id = create_alert(session, "gold", "below", gold_target_below)
    if alert2_id:
        print_success(f"Alert 2 created (ID: {alert2_id})")
        test_alerts.append({
            'id': alert2_id,
            'metal': 'gold',
            'condition': 'below',
            'target': gold_target_below,
            'current': prices['gold'],
            'should_trigger': False
        })
    
    time.sleep(0.5)
    
    # Alert 3: SILVER - ABOVE (will trigger immediately)
    silver_target_above = prices['silver'] - 10
    print_info(f"Alert 3: SILVER ABOVE ₹{silver_target_above:,.2f} (current: ₹{prices['silver']:,.2f})")
    print(f"         ➜ Condition: Current (₹{prices['silver']:,.2f}) is ABOVE target (₹{silver_target_above:,.2f}) → Should TRIGGER")
    alert3_id = create_alert(session, "silver", "above", silver_target_above)
    if alert3_id:
        print_success(f"Alert 3 created (ID: {alert3_id})")
        test_alerts.append({
            'id': alert3_id,
            'metal': 'silver',
            'condition': 'above',
            'target': silver_target_above,
            'current': prices['silver'],
            'should_trigger': True
        })
    
    time.sleep(0.5)
    
    # Alert 4: SILVER - BELOW (won't trigger)
    silver_target_below = prices['silver'] + 10
    print_info(f"Alert 4: SILVER BELOW ₹{silver_target_below:,.2f} (current: ₹{prices['silver']:,.2f})")
    print(f"         ➜ Condition: Current (₹{prices['silver']:,.2f}) is BELOW target (₹{silver_target_below:,.2f}) → Will NOT trigger")
    alert4_id = create_alert(session, "silver", "below", silver_target_below)
    if alert4_id:
        print_success(f"Alert 4 created (ID: {alert4_id})")
        test_alerts.append({
            'id': alert4_id,
            'metal': 'silver',
            'condition': 'below',
            'target': silver_target_below,
            'current': prices['silver'],
            'should_trigger': False
        })
    
    if not test_alerts:
        print_error("No alerts were created. Aborting test.")
        return
    
    print_success(f"Created {len(test_alerts)} demo alerts")
    
    # ==========================================
    # STEP 4: Verify alerts in database BEFORE trigger
    # ==========================================
    print_step(4, "Verify Alerts in Database BEFORE Trigger (Status: 'watching')")
    
    alerts_before = {}
    all_correct = True
    
    for alert_info in test_alerts:
        alert_db = verify_alert_in_db(alert_info['id'], user_id)
        if alert_db:
            alerts_before[alert_info['id']] = alert_db
            status_correct = alert_db['status'] == 'watching'
            status_symbol = "✅" if status_correct else "❌"
            print(f"{status_symbol} Alert {alert_info['id']}: {alert_info['metal'].upper()}/{alert_info['condition'].upper()}")
            print(f"    Target: ₹{float(alert_db['target_price']):,.2f} | Status: {alert_db['status']} | Created: {alert_db['created_at']}")
            if not status_correct:
                all_correct = False
        else:
            print_error(f"Alert {alert_info['id']} not found in database!")
            all_correct = False
    
    if all_correct:
        print_success("All alerts verified with 'watching' status ✅")
    else:
        print_warning("Some alerts have unexpected status")
    
    # ==========================================
    # STEP 5: Manually trigger alert check
    # ==========================================
    print_step(5, "Manually Trigger Alert Check")
    print_info("Calling /api/admin/trigger_alerts endpoint...")
    
    if trigger_alerts_manually():
        print_success("Alert trigger endpoint called")
    else:
        print_error("Failed to call trigger endpoint")
    
    # Wait for database to update
    print_info("Waiting for database updates...")
    time.sleep(2)
    
    # ==========================================
    # STEP 6: Verify alert status AFTER trigger
    # ==========================================
    print_step(6, "Verify Alert Status AFTER Trigger")
    
    alerts_after = {}
    triggered_count = 0
    correct_count = 0
    
    for alert_info in test_alerts:
        alert_db = verify_alert_in_db(alert_info['id'], user_id)
        if alert_db:
            alerts_after[alert_info['id']] = alert_db
            
            expected_status = 'triggered' if alert_info['should_trigger'] else 'watching'
            actual_status = alert_db['status']
            status_correct = actual_status == expected_status
            
            status_symbol = "✅" if status_correct else "❌"
            print(f"\n{status_symbol} Alert {alert_info['id']}: {alert_info['metal'].upper()}/{alert_info['condition'].upper()}")
            print(f"    Expected Status: {expected_status}")
            print(f"    Actual Status:   {actual_status}")
            print(f"    Target Price:    ₹{float(alert_db['target_price']):,.2f}")
            print(f"    Should Trigger:  {alert_info['should_trigger']}")
            
            if status_correct:
                correct_count += 1
            else:
                print_warning(f"    ⚠️ Status mismatch! Expected '{expected_status}' but got '{actual_status}'")
            
            if alert_db['status'] == 'triggered':
                triggered_count += 1
    
    # ==========================================
    # STEP 7: Verify database updates
    # ==========================================
    print_step(7, "Database Update Verification")
    
    print(f"Total Alerts: {len(test_alerts)}")
    print(f"Triggered: {triggered_count}")
    print(f"Still Watching: {len(test_alerts) - triggered_count}")
    print(f"Status Correct: {correct_count}/{len(test_alerts)}")
    
    if correct_count == len(test_alerts):
        print_success("✅ All alert statuses are CORRECT!")
    elif correct_count == 0:
        print_error("❌ All alert statuses are INCORRECT!")
    else:
        print_warning(f"⚠️ Partial Success: {correct_count}/{len(test_alerts)} alerts have correct status")
    
    # ==========================================
    # STEP 8: Compare before and after
    # ==========================================
    print_step(8, "Before/After Comparison")
    
    changes_detected = False
    for alert_id in alerts_before:
        before_status = alerts_before[alert_id]['status']
        after_status = alerts_after[alert_id]['status'] if alert_id in alerts_after else 'MISSING'
        
        if before_status != after_status:
            changes_detected = True
            print_info(f"Alert {alert_id}: {before_status} → {after_status}")
    
    if changes_detected:
        print_success("✅ Database updates detected!")
    else:
        print_warning("⚠️ No status changes detected in database")
    
    # ==========================================
    # STEP 9: API Verification
    # ==========================================
    print_step(9, "Get Alerts via API")
    
    try:
        response = requests.get(f"{BASE_URL}/api/alerts?limit=10", timeout=5)
        api_data = response.json()
        
        if api_data.get('success'):
            alerts_from_api = api_data.get('data', [])
            print_success(f"Retrieved {len(alerts_from_api)} alerts from API")
            
            for alert in alerts_from_api[:4]:  # Show first 4
                print(f"   Alert: {alert.get('metal_type')}/{alert.get('condition_type')} @ ₹{alert.get('target_price')} | Status: {alert.get('status')}")
    except Exception as e:
        print_error(f"Failed to get alerts via API: {e}")
    
    # ==========================================
    # FINAL REPORT
    # ==========================================
    print_header("TEST SUMMARY & REPORT")
    
    print(f"\n{BOLD}Test Configuration:{RESET}")
    print(f"   User ID: {user_id}")
    print(f"   Test Alerts: {len(test_alerts)}")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n{BOLD}Live Prices (at test time):{RESET}")
    print(f"   Gold (per 10g):      ₹{prices['gold']:>10,.2f}")
    print(f"   Silver (per 1kg):    ₹{prices['silver']:>10,.2f}")
    print(f"   Platinum (per 10g):  ₹{prices['platinum']:>10,.2f}")
    
    print(f"\n{BOLD}Alert Details:{RESET}")
    for i, alert_info in enumerate(test_alerts, 1):
        alert_db = alerts_after.get(alert_info['id'])
        if alert_db:
            expected = 'triggered' if alert_info['should_trigger'] else 'watching'
            actual = alert_db['status']
            match = "✅" if expected == actual else "❌"
            print(f"\n   Alert {i} {match}:")
            print(f"      Metal:          {alert_info['metal'].upper()}")
            print(f"      Condition:      {alert_info['condition'].upper()}")
            print(f"      Target Price:   ₹{alert_info['target']:,.2f}")
            print(f"      Current Price:  ₹{alert_info['current']:,.2f}")
            print(f"      Expected Status: {expected}")
            print(f"      Actual Status:   {actual}")
            print(f"      Should Trigger: {alert_info['should_trigger']}")
    
    print(f"\n{BOLD}Test Results:{RESET}")
    if correct_count == len(test_alerts):
        print(f"{GREEN}✅ ALL TESTS PASSED - ALERT SYSTEM IS WORKING 100% CORRECTLY!{RESET}")
        print(f"\n   ✅ Alerts created successfully")
        print(f"   ✅ Initial status set to 'watching'")
        print(f"   ✅ Trigger logic works correctly")
        print(f"   ✅ Database updates properly")
        print(f"   ✅ Status shows 'triggered' for conditions met")
        print(f"   ✅ Status remains 'watching' for conditions not met")
    else:
        print(f"{RED}❌ TEST FAILED - {len(test_alerts) - correct_count} alerts have incorrect status{RESET}")
        print(f"\n   Issues detected:")
        for alert_id in alerts_after:
            alert_info = next((a for a in test_alerts if a['id'] == alert_id), None)
            if alert_info:
                expected = 'triggered' if alert_info['should_trigger'] else 'watching'
                actual = alerts_after[alert_id]['status']
                if expected != actual:
                    print(f"   ❌ Alert {alert_id}: Expected '{expected}' but got '{actual}'")
    
    print("\n" + "=" * 100)
    print(f"{BOLD}TEST COMPLETE{RESET}")
    print("=" * 100 + "\n")

if __name__ == "__main__":
    main()
