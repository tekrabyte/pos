#!/usr/bin/env python3
"""
Menu Routes Testing for QR Scan & Dine POS System
Tests all endpoints that correspond to sidebar menu items
"""

import requests
import json
import sys
from pathlib import Path

# Get backend URL from frontend .env
frontend_env_path = Path('/app/frontend/.env')
backend_url = None
if frontend_env_path.exists():
    with open(frontend_env_path, 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                backend_url = line.split('=', 1)[1].strip()
                break

if not backend_url:
    backend_url = "http://localhost:8001"

API_BASE_URL = f"{backend_url}/api"

print(f"Testing menu route endpoints at: {API_BASE_URL}")

class MenuRouteTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = {}
        
    def log_test(self, test_name, success, message="", response_data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results[test_name] = {
            "success": success,
            "message": message,
            "response_data": response_data
        }
        
    def test_staff_login(self):
        """Test staff authentication first"""
        print("\n=== Testing Staff Authentication ===")
        
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/staff/login", 
                json={"username": "admin", "password": "admin123"})
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("token"):
                    self.log_test("Staff Login", True, f"Admin login successful")
                    return True
                else:
                    self.log_test("Staff Login", False, f"Login failed: {data.get('message', 'Unknown error')}")
            else:
                self.log_test("Staff Login", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Staff Login", False, f"Exception: {str(e)}")
            
        return False
        
    def test_outlets_endpoint(self):
        """Test GET /api/outlets (Outlet menu)"""
        print("\n=== Testing Outlets Endpoint ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/outlets")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("GET /api/outlets", True, f"Retrieved {len(data)} outlets")
                    return True
                else:
                    self.log_test("GET /api/outlets", False, f"Expected list, got: {type(data)}")
            else:
                self.log_test("GET /api/outlets", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/outlets", False, f"Exception: {str(e)}")
            
        return False
        
    def test_customers_endpoint(self):
        """Test GET /api/customers (Pelanggan menu)"""
        print("\n=== Testing Customers Endpoint ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/customers")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("GET /api/customers", True, f"Retrieved {len(data)} customers")
                    return True
                else:
                    self.log_test("GET /api/customers", False, f"Expected list, got: {type(data)}")
            else:
                self.log_test("GET /api/customers", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/customers", False, f"Exception: {str(e)}")
            
        return False
        
    def test_coupons_endpoint(self):
        """Test GET /api/coupons (Kupon menu)"""
        print("\n=== Testing Coupons Endpoint ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/coupons")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("GET /api/coupons", True, f"Retrieved {len(data)} coupons")
                    return True
                else:
                    self.log_test("GET /api/coupons", False, f"Expected list, got: {type(data)}")
            else:
                self.log_test("GET /api/coupons", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/coupons", False, f"Exception: {str(e)}")
            
        return False
        
    def test_roles_endpoint(self):
        """Test GET /api/roles (Roles menu)"""
        print("\n=== Testing Roles Endpoint ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/roles")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("GET /api/roles", True, f"Retrieved {len(data)} roles")
                    return True
                else:
                    self.log_test("GET /api/roles", False, f"Expected list, got: {type(data)}")
            else:
                self.log_test("GET /api/roles", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/roles", False, f"Exception: {str(e)}")
            
        return False
        
    def test_payment_methods_endpoint(self):
        """Test GET /api/payment-methods (Payment Settings menu)"""
        print("\n=== Testing Payment Methods Endpoint ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/payment-methods")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("GET /api/payment-methods", True, f"Retrieved {len(data)} payment methods")
                    return True
                else:
                    self.log_test("GET /api/payment-methods", False, f"Expected list, got: {type(data)}")
            else:
                self.log_test("GET /api/payment-methods", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/payment-methods", False, f"Exception: {str(e)}")
            
        return False
        
    def test_brands_endpoint(self):
        """Test GET /api/brands (Brand/Merek menu)"""
        print("\n=== Testing Brands Endpoint ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/brands")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("GET /api/brands", True, f"Retrieved {len(data)} brands")
                    return True
                else:
                    self.log_test("GET /api/brands", False, f"Expected list, got: {type(data)}")
            else:
                self.log_test("GET /api/brands", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/brands", False, f"Exception: {str(e)}")
            
        return False
        
    def test_analytics_endpoint(self):
        """Test GET /api/analytics/overview (Analytics menu)"""
        print("\n=== Testing Analytics Endpoint ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/analytics/overview")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total_revenue", "total_orders", "total_products", "total_customers"]
                if all(field in data for field in required_fields):
                    self.log_test("GET /api/analytics/overview", True, f"Analytics data retrieved with all required fields")
                    return True
                else:
                    missing = [field for field in required_fields if field not in data]
                    self.log_test("GET /api/analytics/overview", False, f"Missing fields: {missing}")
            else:
                self.log_test("GET /api/analytics/overview", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/analytics/overview", False, f"Exception: {str(e)}")
            
        return False
        
    def test_websocket_endpoint(self):
        """Test WebSocket /api/ws/orders connection"""
        print("\n=== Testing WebSocket Orders Endpoint ===")
        
        try:
            import websocket
            import threading
            import time
            
            # Convert HTTP URL to WebSocket URL
            ws_url = API_BASE_URL.replace("https://", "wss://").replace("http://", "ws://") + "/ws/orders"
            
            connected = False
            
            def on_open(ws):
                nonlocal connected
                connected = True
                
            def on_error(ws, error):
                print(f"WebSocket error: {error}")
                
            def on_close(ws, close_status_code, close_msg):
                pass
            
            # Create WebSocket connection
            ws = websocket.WebSocketApp(ws_url,
                                      on_open=on_open,
                                      on_error=on_error,
                                      on_close=on_close)
            
            # Run WebSocket in a separate thread
            def run_ws():
                ws.run_forever()
                
            ws_thread = threading.Thread(target=run_ws)
            ws_thread.daemon = True
            ws_thread.start()
            
            # Wait for connection
            time.sleep(2)
            
            if connected:
                ws.close()
                self.log_test("WebSocket /api/ws/orders", True, "WebSocket connection established")
                return True
            else:
                self.log_test("WebSocket /api/ws/orders", False, "Failed to establish WebSocket connection")
                return False
                
        except Exception as e:
            self.log_test("WebSocket /api/ws/orders", False, f"Exception: {str(e)}")
            return False
    
    def run_menu_route_tests(self):
        """Run all menu route tests"""
        print("🎯 Testing Menu Route Endpoints for QR Scan & Dine POS System")
        print("=" * 70)
        
        # First authenticate
        self.test_staff_login()
        
        # Test all menu route endpoints
        self.test_outlets_endpoint()
        self.test_customers_endpoint()
        self.test_coupons_endpoint()
        self.test_roles_endpoint()
        self.test_payment_methods_endpoint()
        self.test_brands_endpoint()
        self.test_analytics_endpoint()
        self.test_websocket_endpoint()
        
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 MENU ROUTE TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results.values() if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            status = "✅" if result["success"] else "❌"
            print(f"{status} {test_name}: {result['message']}")
        
        if total - passed > 0:
            print("\n⚠️  FAILED TESTS:")
            for test_name, result in self.test_results.items():
                if not result["success"]:
                    print(f"❌ {test_name}: {result['message']}")

if __name__ == "__main__":
    tester = MenuRouteTester()
    tester.run_menu_route_tests()