#!/usr/bin/env python3
"""
Test script for NewsAPI integration in MetaTracker
Run this to verify your NewsAPI configuration is working correctly
"""

import requests
import sys
import os
from datetime import datetime

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_info(msg):
    print(f"{BLUE}ℹ️  {msg}{RESET}")

def test_backend_running():
    """Check if backend server is running"""
    try:
        response = requests.get("http://localhost:5000/test", timeout=3)
        if response.text == "Server is working!":
            print_success("Backend server is running on http://localhost:5000")
            return True
    except requests.exceptions.ConnectionError:
        print_error("Backend server is NOT running")
        print_warning("Start the server with: python app.py")
        return False
    except Exception as e:
        print_error(f"Error checking server: {e}")
        return False

def test_news_api_endpoint():
    """Test the /api/news endpoint"""
    try:
        response = requests.get("http://localhost:5000/api/news", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                news_count = len(data.get("data", []))
                print_success(f"News API endpoint working! Found {news_count} articles")
                
                if news_count > 0:
                    print_info(f"Latest article: {data['data'][0].get('title', 'No title')[:80]}...")
                    print_info(f"Source: {data['data'][0].get('source', 'Unknown')}")
                    print_info(f"Published: {data['data'][0].get('published_at', 'Unknown')}")
                else:
                    print_warning("No news articles found in database yet")
                    print_warning("Wait a few minutes for the scheduled job to fetch news")
                return True
            else:
                print_error(f"API returned error: {data.get('error', 'Unknown')}")
                return False
        else:
            print_error(f"API returned status code: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print_error("Request timed out - server may be slow")
        return False
    except Exception as e:
        print_error(f"Error testing news endpoint: {e}")
        return False

def test_database_connection():
    """Test database connection via backend"""
    try:
        response = requests.get("http://localhost:5000/api/prices/live", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print_success("Database connection working!")
                prices = data.get("prices", {})
                print_info(f"Gold: ₹{prices.get('gold', 'N/A')}/g")
                print_info(f"Silver: ₹{prices.get('silver', 'N/A')}/g")
                print_info(f"Platinum: ₹{prices.get('platinum', 'N/A')}/g")
                return True
        return False
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        return False

def check_news_table():
    """Check if market_news table has data"""
    try:
        response = requests.get("http://localhost:5000/api/news", timeout=5)
        if response.status_code == 200:
            data = response.json()
            count = len(data.get("data", []))
            if count > 0:
                print_success(f"Market news table has {count} articles")
                return True
            else:
                print_warning("Market news table is empty (waiting for first fetch)")
                return False
    except:
        return False

def main():
    print(f"\n{BLUE}{'='*60}")
    print(f"MetaTracker NewsAPI Integration Test")
    print(f"{'='*60}{RESET}\n")
    
    print(f"{BLUE}Testing Backend Setup...{RESET}\n")
    
    # Test 1: Backend running
    if not test_backend_running():
        print_error("\n❌ Cannot proceed without running backend server!")
        print("Start the server with: python Backend/app.py")
        sys.exit(1)
    
    print()
    
    # Test 2: Database connection
    print(f"{BLUE}Testing Database...{RESET}\n")
    test_database_connection()
    
    print()
    
    # Test 3: News API endpoint
    print(f"{BLUE}Testing News API...{RESET}\n")
    if test_news_api_endpoint():
        print_success("\n✅ NewsAPI Integration is working!")
    else:
        print_error("\n❌ NewsAPI endpoint is not responding correctly")
    
    print()
    
    # Summary
    print(f"{BLUE}{'='*60}")
    print("Summary")
    print(f"{'='*60}{RESET}\n")
    
    check_news_table()
    
    print_info("Scheduled Tasks:")
    print("  • Price updates: Every 5 minutes")
    print("  • News fetching: Every 30 minutes")
    print("  • Alert checks: Every 2 minutes")
    
    print()
    print_info("To view real-time news in your frontend:")
    print("  • Call: GET /api/news")
    print("  • Returns: Latest market news articles")
    
    print()
    print_success("Test completed!\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
