#!/usr/bin/env python3
"""
Final Verification Test for Laravel POS API
Checks all success criteria from the review request
"""

import requests
import json
import time

def final_verification():
    """Final verification against all success criteria"""
    base_url = "http://localhost:8001/api"
    
    print("=" * 70)
    print("FINAL VERIFICATION TEST - SUCCESS CRITERIA CHECK")
    print("=" * 70)
    
    results = {
        'all_endpoints_200': True,
        'jwt_auth_working': True,
        'response_format_correct': True,
        'no_server_errors': True,
        'response_times': []
    }
    
    # 1. Test Authentication Flow
    print("1. AUTHENTICATION TESTING")
    print("-" * 30)
    
    # Login
    start_time = time.time()
    login_response = requests.post(f"{base_url}/auth/staff/login", 
                                 json={"username": "admin", "password": "admin123"})
    login_time = time.time() - start_time
    results['response_times'].append(login_time)
    
    if login_response.status_code == 200:
        login_data = login_response.json()
        token = login_data.get('token')
        if token and login_data.get('success'):
            print(f"✅ Staff login successful (JWT token generated)")
            print(f"   Response time: {login_time:.3f}s")
        else:
            print(f"❌ Login response missing token or success flag")
            results['jwt_auth_working'] = False
    else:
        print(f"❌ Login failed: HTTP {login_response.status_code}")
        results['all_endpoints_200'] = False
        results['jwt_auth_working'] = False
        return results
    
    # Test authenticated endpoint
    headers = {'Authorization': f'Bearer {token}'}
    start_time = time.time()
    me_response = requests.get(f"{base_url}/auth/staff/me", headers=headers)
    me_time = time.time() - start_time
    results['response_times'].append(me_time)
    
    if me_response.status_code == 200:
        me_data = me_response.json()
        if me_data.get('success') and me_data.get('user'):
            print(f"✅ Authenticated /me endpoint working")
            print(f"   Response time: {me_time:.3f}s")
        else:
            print(f"❌ /me endpoint response format incorrect")
            results['response_format_correct'] = False
    else:
        print(f"❌ /me endpoint failed: HTTP {me_response.status_code}")
        results['all_endpoints_200'] = False
    
    # Test logout
    start_time = time.time()
    logout_response = requests.post(f"{base_url}/auth/staff/logout", headers=headers)
    logout_time = time.time() - start_time
    results['response_times'].append(logout_time)
    
    if logout_response.status_code == 200:
        logout_data = logout_response.json()
        if logout_data.get('success'):
            print(f"✅ Logout endpoint working")
            print(f"   Response time: {logout_time:.3f}s")
        else:
            print(f"❌ Logout response format incorrect")
            results['response_format_correct'] = False
    else:
        print(f"❌ Logout failed: HTTP {logout_response.status_code}")
        results['all_endpoints_200'] = False
    
    print()
    
    # 2. Test All Required Endpoints
    print("2. ENDPOINT TESTING")
    print("-" * 30)
    
    endpoints = [
        ("/products", "Products"),
        ("/categories", "Categories"),
        ("/brands", "Brands"),
        ("/orders", "Orders"),
        ("/tables", "Tables"),
        ("/dashboard/stats", "Dashboard Stats"),
        ("/analytics", "Analytics"),
        ("/customers", "Customers"),
        ("/coupons", "Coupons"),
        ("/outlets", "Outlets"),
        ("/payment-methods", "Payment Methods")
    ]
    
    for endpoint, name in endpoints:
        start_time = time.time()
        response = requests.get(f"{base_url}{endpoint}")
        response_time = time.time() - start_time
        results['response_times'].append(response_time)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success') == True:
                    print(f"✅ {name}: HTTP 200, correct format")
                    print(f"   Response time: {response_time:.3f}s")
                else:
                    print(f"❌ {name}: Missing success=true in response")
                    results['response_format_correct'] = False
            except json.JSONDecodeError:
                print(f"❌ {name}: Invalid JSON response")
                results['response_format_correct'] = False
                results['no_server_errors'] = False
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            results['all_endpoints_200'] = False
            if response.status_code >= 500:
                results['no_server_errors'] = False
    
    print()
    
    # 3. Performance Analysis
    print("3. PERFORMANCE ANALYSIS")
    print("-" * 30)
    
    avg_time = sum(results['response_times']) / len(results['response_times'])
    max_time = max(results['response_times'])
    under_2s = all(t < 2.0 for t in results['response_times'])
    
    print(f"Average response time: {avg_time:.3f}s")
    print(f"Maximum response time: {max_time:.3f}s")
    print(f"All responses under 2s: {'✅ Yes' if under_2s else '❌ No'}")
    
    if not under_2s:
        slow_endpoints = [i for i, t in enumerate(results['response_times']) if t >= 2.0]
        print(f"Slow endpoints (≥2s): {len(slow_endpoints)} out of {len(results['response_times'])}")
    
    print()
    
    # 4. Final Summary
    print("4. SUCCESS CRITERIA SUMMARY")
    print("-" * 30)
    
    criteria = [
        ("All endpoints return 200 OK", results['all_endpoints_200']),
        ("JWT authentication working correctly", results['jwt_auth_working']),
        ("Response format matches {success: true, data: ...}", results['response_format_correct']),
        ("No server errors or exceptions", results['no_server_errors']),
        ("Average response time < 2 seconds", avg_time < 2.0)
    ]
    
    all_passed = True
    for criterion, passed in criteria:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {criterion}")
        if not passed:
            all_passed = False
    
    print()
    print("=" * 70)
    if all_passed:
        print("🎉 ALL SUCCESS CRITERIA MET - LARAVEL POS API IS WORKING CORRECTLY")
    else:
        print("⚠️  SOME SUCCESS CRITERIA NOT MET - SEE DETAILS ABOVE")
    print("=" * 70)
    
    return results

if __name__ == "__main__":
    final_verification()