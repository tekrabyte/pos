#!/usr/bin/env python3
"""
Detailed Laravel POS API Testing - Data Integrity Check
"""

import requests
import json

def test_api_response_structure():
    """Test API response structure and data integrity"""
    base_url = "http://localhost:8001/api"
    
    print("=" * 60)
    print("DETAILED API RESPONSE STRUCTURE TEST")
    print("=" * 60)
    
    # Test login first to get token
    login_response = requests.post(f"{base_url}/auth/staff/login", 
                                 json={"username": "admin", "password": "admin123"})
    
    if login_response.status_code == 200:
        login_data = login_response.json()
        token = login_data.get('token')
        print(f"✅ Login successful. Token obtained.")
        print(f"   User: {login_data.get('user', {}).get('username')}")
        print(f"   Role: {login_data.get('user', {}).get('role')}")
        print()
    else:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    # Test endpoints with detailed response analysis
    endpoints = [
        ("/products", "Products"),
        ("/categories", "Categories"), 
        ("/brands", "Brands"),
        ("/orders", "Orders"),
        ("/tables", "Tables"),
        ("/customers", "Customers"),
        ("/coupons", "Coupons"),
        ("/outlets", "Outlets"),
        ("/payment-methods", "Payment Methods"),
        ("/dashboard/stats", "Dashboard Stats"),
        ("/analytics", "Analytics")
    ]
    
    for endpoint, name in endpoints:
        print(f"Testing {name} ({endpoint}):")
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   Response type: {type(data)}")
                    
                    if isinstance(data, dict):
                        print(f"   Keys: {list(data.keys())}")
                        if 'success' in data:
                            print(f"   Success: {data['success']}")
                        if 'data' in data:
                            data_items = data['data']
                            if isinstance(data_items, list):
                                print(f"   Data count: {len(data_items)}")
                                if len(data_items) > 0:
                                    print(f"   Sample item keys: {list(data_items[0].keys()) if isinstance(data_items[0], dict) else 'Not a dict'}")
                        elif 'stats' in data:
                            stats = data['stats']
                            print(f"   Stats keys: {list(stats.keys())}")
                        elif 'analytics' in data:
                            analytics = data['analytics']
                            print(f"   Analytics keys: {list(analytics.keys())}")
                    elif isinstance(data, list):
                        print(f"   List length: {len(data)}")
                        if len(data) > 0:
                            print(f"   Sample item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")
                    
                    print(f"   ✅ Valid JSON response")
                    
                except json.JSONDecodeError:
                    print(f"   ❌ Invalid JSON response")
                    print(f"   Raw response: {response.text[:200]}...")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw error: {response.text[:200]}...")
                    
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
        
        print()

if __name__ == "__main__":
    test_api_response_structure()