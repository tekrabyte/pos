#!/usr/bin/env python3
"""
Laravel POS API Testing Suite
Tests all major API endpoints as specified in the review request
"""

import requests
import json
import time
from datetime import datetime

class LaravelPOSAPITester:
    def __init__(self, base_url="https://crud-flow-optimize.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.test_results = []
        
    def log_test(self, test_name, success, message, response_time=None, status_code=None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'response_time': response_time,
            'status_code': status_code,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if response_time:
            print(f"    Response time: {response_time:.3f}s")
        if status_code:
            print(f"    Status code: {status_code}")
        print()
    
    def make_request(self, method, endpoint, data=None, use_auth=False):
        """Make HTTP request with error handling"""
        url = f"{self.api_url}{endpoint}"
        headers = self.headers.copy()
        
        if use_auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            start_time = time.time()
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response_time = time.time() - start_time
            
            return response, response_time
            
        except requests.exceptions.RequestException as e:
            return None, 0
    
    def test_health_check(self):
        """Test API health check endpoint"""
        response, response_time = self.make_request('GET', '/health')
        
        if response is None:
            self.log_test("Health Check", False, "Connection failed")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('status') == 'OK':
                    self.log_test("Health Check", True, "API is running", response_time, response.status_code)
                    return True
                else:
                    self.log_test("Health Check", False, f"Unexpected response: {data}", response_time, response.status_code)
                    return False
            except json.JSONDecodeError:
                self.log_test("Health Check", False, "Invalid JSON response", response_time, response.status_code)
                return False
        else:
            self.log_test("Health Check", False, f"HTTP {response.status_code}", response_time, response.status_code)
            return False
    
    def test_staff_login(self):
        """Test staff login with admin credentials"""
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response, response_time = self.make_request('POST', '/auth/staff/login', login_data)
        
        if response is None:
            self.log_test("Staff Login", False, "Connection failed")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success') and data.get('token'):
                    self.token = data['token']
                    user_info = data.get('user', {})
                    self.log_test("Staff Login", True, f"Login successful for user: {user_info.get('username')}", response_time, response.status_code)
                    return True
                else:
                    self.log_test("Staff Login", False, f"Login failed: {data.get('message', 'Unknown error')}", response_time, response.status_code)
                    return False
            except json.JSONDecodeError:
                self.log_test("Staff Login", False, "Invalid JSON response", response_time, response.status_code)
                return False
        else:
            try:
                error_data = response.json()
                self.log_test("Staff Login", False, f"HTTP {response.status_code}: {error_data.get('message', 'Login failed')}", response_time, response.status_code)
            except:
                self.log_test("Staff Login", False, f"HTTP {response.status_code}: Login failed", response_time, response.status_code)
            return False
    
    def test_authenticated_me(self):
        """Test authenticated /me endpoint"""
        if not self.token:
            self.log_test("Authenticated Me", False, "No token available - login first")
            return False
        
        response, response_time = self.make_request('GET', '/auth/staff/me', use_auth=True)
        
        if response is None:
            self.log_test("Authenticated Me", False, "Connection failed")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success') and data.get('user'):
                    user = data['user']
                    self.log_test("Authenticated Me", True, f"User data retrieved: {user.get('username', 'N/A')}", response_time, response.status_code)
                    return True
                else:
                    self.log_test("Authenticated Me", False, f"Invalid response structure: {data}", response_time, response.status_code)
                    return False
            except json.JSONDecodeError:
                self.log_test("Authenticated Me", False, "Invalid JSON response", response_time, response.status_code)
                return False
        else:
            self.log_test("Authenticated Me", False, f"HTTP {response.status_code}: Authentication failed", response_time, response.status_code)
            return False
    
    def test_logout(self):
        """Test logout endpoint"""
        if not self.token:
            self.log_test("Logout", False, "No token available - login first")
            return False
        
        response, response_time = self.make_request('POST', '/auth/staff/logout', use_auth=True)
        
        if response is None:
            self.log_test("Logout", False, "Connection failed")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success'):
                    self.log_test("Logout", True, "Logout successful", response_time, response.status_code)
                    # Keep token for other tests
                    return True
                else:
                    self.log_test("Logout", False, f"Logout failed: {data.get('message', 'Unknown error')}", response_time, response.status_code)
                    return False
            except json.JSONDecodeError:
                self.log_test("Logout", False, "Invalid JSON response", response_time, response.status_code)
                return False
        else:
            self.log_test("Logout", False, f"HTTP {response.status_code}: Logout failed", response_time, response.status_code)
            return False
    
    def test_products_endpoint(self):
        """Test GET /api/products"""
        response, response_time = self.make_request('GET', '/products')
        
        if response is None:
            self.log_test("Products List", False, "Connection failed")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and data.get('success'):
                    products = data.get('data', [])
                    self.log_test("Products List", True, f"Retrieved {len(products)} products", response_time, response.status_code)
                    return True
                elif isinstance(data, list):
                    self.log_test("Products List", True, f"Retrieved {len(data)} products", response_time, response.status_code)
                    return True
                else:
                    self.log_test("Products List", False, f"Unexpected response format: {type(data)}", response_time, response.status_code)
                    return False
            except json.JSONDecodeError:
                self.log_test("Products List", False, "Invalid JSON response", response_time, response.status_code)
                return False
        else:
            self.log_test("Products List", False, f"HTTP {response.status_code}", response_time, response.status_code)
            return False
    
    def test_categories_endpoint(self):
        """Test GET /api/categories"""
        response, response_time = self.make_request('GET', '/categories')
        
        if response is None:
            self.log_test("Categories List", False, "Connection failed")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and data.get('success'):
                    categories = data.get('data', [])
                    self.log_test("Categories List", True, f"Retrieved {len(categories)} categories", response_time, response.status_code)
                    return True
                elif isinstance(data, list):
                    self.log_test("Categories List", True, f"Retrieved {len(data)} categories", response_time, response.status_code)
                    return True
                else:
                    self.log_test("Categories List", False, f"Unexpected response format: {type(data)}", response_time, response.status_code)
                    return False
            except json.JSONDecodeError:
                self.log_test("Categories List", False, "Invalid JSON response", response_time, response.status_code)
                return False
        else:
            self.log_test("Categories List", False, f"HTTP {response.status_code}", response_time, response.status_code)
            return False
    
    def test_brands_endpoint(self):
        """Test GET /api/brands"""
        response, response_time = self.make_request('GET', '/brands')
        
        if response is None:
            self.log_test("Brands List", False, "Connection failed")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and data.get('success'):
                    brands = data.get('data', [])
                    self.log_test("Brands List", True, f"Retrieved {len(brands)} brands", response_time, response.status_code)
                    return True
                elif isinstance(data, list):
                    self.log_test("Brands List", True, f"Retrieved {len(data)} brands", response_time, response.status_code)
                    return True
                else:
                    self.log_test("Brands List", False, f"Unexpected response format: {type(data)}", response_time, response.status_code)
                    return False
            except json.JSONDecodeError:
                self.log_test("Brands List", False, "Invalid JSON response", response_time, response.status_code)
                return False
        else:
            self.log_test("Brands List", False, f"HTTP {response.status_code}", response_time, response.status_code)
            return False
    
    def test_orders_endpoint(self):
        """Test GET /api/orders"""
        response, response_time = self.make_request('GET', '/orders')
        
        if response is None:
            self.log_test("Orders List", False, "Connection failed")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and data.get('success'):
                    orders = data.get('data', [])
                    self.log_test("Orders List", True, f"Retrieved {len(orders)} orders", response_time, response.status_code)
                    return True
                elif isinstance(data, list):
                    self.log_test("Orders List", True, f"Retrieved {len(data)} orders", response_time, response.status_code)
                    return True
                else:
                    self.log_test("Orders List", False, f"Unexpected response format: {type(data)}", response_time, response.status_code)
                    return False
            except json.JSONDecodeError:
                self.log_test("Orders List", False, "Invalid JSON response", response_time, response.status_code)
                return False
        else:
            self.log_test("Orders List", False, f"HTTP {response.status_code}", response_time, response.status_code)
            return False
    
    def test_tables_endpoint(self):
        """Test GET /api/tables"""
        response, response_time = self.make_request('GET', '/tables')
        
        if response is None:
            self.log_test("Tables List", False, "Connection failed")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and data.get('success'):
                    tables = data.get('data', [])
                    self.log_test("Tables List", True, f"Retrieved {len(tables)} tables", response_time, response.status_code)
                    return True
                elif isinstance(data, list):
                    self.log_test("Tables List", True, f"Retrieved {len(data)} tables", response_time, response.status_code)
                    return True
                else:
                    self.log_test("Tables List", False, f"Unexpected response format: {type(data)}", response_time, response.status_code)
                    return False
            except json.JSONDecodeError:
                self.log_test("Tables List", False, "Invalid JSON response", response_time, response.status_code)
                return False
        else:
            self.log_test("Tables List", False, f"HTTP {response.status_code}", response_time, response.status_code)
            return False
    
    def test_dashboard_stats(self):
        """Test GET /api/dashboard/stats"""
        response, response_time = self.make_request('GET', '/dashboard/stats')
        
        if response is None:
            self.log_test("Dashboard Stats", False, "Connection failed")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success') and data.get('stats'):
                    stats = data['stats']
                    self.log_test("Dashboard Stats", True, f"Stats retrieved with keys: {list(stats.keys())}", response_time, response.status_code)
                    return True
                else:
                    self.log_test("Dashboard Stats", False, f"Invalid response structure: {data}", response_time, response.status_code)
                    return False
            except json.JSONDecodeError:
                self.log_test("Dashboard Stats", False, "Invalid JSON response", response_time, response.status_code)
                return False
        else:
            self.log_test("Dashboard Stats", False, f"HTTP {response.status_code}", response_time, response.status_code)
            return False
    
    def test_analytics_endpoint(self):
        """Test GET /api/analytics"""
        response, response_time = self.make_request('GET', '/analytics')
        
        if response is None:
            self.log_test("Analytics", False, "Connection failed")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success') and data.get('analytics'):
                    analytics = data['analytics']
                    self.log_test("Analytics", True, f"Analytics retrieved with keys: {list(analytics.keys())}", response_time, response.status_code)
                    return True
                else:
                    self.log_test("Analytics", False, f"Invalid response structure: {data}", response_time, response.status_code)
                    return False
            except json.JSONDecodeError:
                self.log_test("Analytics", False, "Invalid JSON response", response_time, response.status_code)
                return False
        else:
            self.log_test("Analytics", False, f"HTTP {response.status_code}", response_time, response.status_code)
            return False
    
    def test_customers_endpoint(self):
        """Test GET /api/customers"""
        response, response_time = self.make_request('GET', '/customers')
        
        if response is None:
            self.log_test("Customers List", False, "Connection failed")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and data.get('success'):
                    customers = data.get('data', [])
                    self.log_test("Customers List", True, f"Retrieved {len(customers)} customers", response_time, response.status_code)
                    return True
                elif isinstance(data, list):
                    self.log_test("Customers List", True, f"Retrieved {len(data)} customers", response_time, response.status_code)
                    return True
                else:
                    self.log_test("Customers List", False, f"Unexpected response format: {type(data)}", response_time, response.status_code)
                    return False
            except json.JSONDecodeError:
                self.log_test("Customers List", False, "Invalid JSON response", response_time, response.status_code)
                return False
        else:
            self.log_test("Customers List", False, f"HTTP {response.status_code}", response_time, response.status_code)
            return False
    
    def test_coupons_endpoint(self):
        """Test GET /api/coupons"""
        response, response_time = self.make_request('GET', '/coupons')
        
        if response is None:
            self.log_test("Coupons List", False, "Connection failed")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and data.get('success'):
                    coupons = data.get('data', [])
                    self.log_test("Coupons List", True, f"Retrieved {len(coupons)} coupons", response_time, response.status_code)
                    return True
                elif isinstance(data, list):
                    self.log_test("Coupons List", True, f"Retrieved {len(data)} coupons", response_time, response.status_code)
                    return True
                else:
                    self.log_test("Coupons List", False, f"Unexpected response format: {type(data)}", response_time, response.status_code)
                    return False
            except json.JSONDecodeError:
                self.log_test("Coupons List", False, "Invalid JSON response", response_time, response.status_code)
                return False
        else:
            self.log_test("Coupons List", False, f"HTTP {response.status_code}", response_time, response.status_code)
            return False
    
    def test_outlets_endpoint(self):
        """Test GET /api/outlets"""
        response, response_time = self.make_request('GET', '/outlets')
        
        if response is None:
            self.log_test("Outlets List", False, "Connection failed")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and data.get('success'):
                    outlets = data.get('data', [])
                    self.log_test("Outlets List", True, f"Retrieved {len(outlets)} outlets", response_time, response.status_code)
                    return True
                elif isinstance(data, list):
                    self.log_test("Outlets List", True, f"Retrieved {len(data)} outlets", response_time, response.status_code)
                    return True
                else:
                    self.log_test("Outlets List", False, f"Unexpected response format: {type(data)}", response_time, response.status_code)
                    return False
            except json.JSONDecodeError:
                self.log_test("Outlets List", False, "Invalid JSON response", response_time, response.status_code)
                return False
        else:
            self.log_test("Outlets List", False, f"HTTP {response.status_code}", response_time, response.status_code)
            return False
    
    def test_payment_methods_endpoint(self):
        """Test GET /api/payment-methods"""
        response, response_time = self.make_request('GET', '/payment-methods')
        
        if response is None:
            self.log_test("Payment Methods List", False, "Connection failed")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and data.get('success'):
                    payment_methods = data.get('data', [])
                    self.log_test("Payment Methods List", True, f"Retrieved {len(payment_methods)} payment methods", response_time, response.status_code)
                    return True
                elif isinstance(data, list):
                    self.log_test("Payment Methods List", True, f"Retrieved {len(data)} payment methods", response_time, response.status_code)
                    return True
                else:
                    self.log_test("Payment Methods List", False, f"Unexpected response format: {type(data)}", response_time, response.status_code)
                    return False
            except json.JSONDecodeError:
                self.log_test("Payment Methods List", False, "Invalid JSON response", response_time, response.status_code)
                return False
        else:
            self.log_test("Payment Methods List", False, f"HTTP {response.status_code}", response_time, response.status_code)
            return False
    
    def run_all_tests(self):
        """Run all API tests"""
        print("=" * 60)
        print("LARAVEL POS API TESTING SUITE")
        print("=" * 60)
        print()
        
        # Test sequence
        tests = [
            ("Health Check", self.test_health_check),
            ("Staff Login", self.test_staff_login),
            ("Authenticated Me", self.test_authenticated_me),
            ("Logout", self.test_logout),
            ("Products List", self.test_products_endpoint),
            ("Categories List", self.test_categories_endpoint),
            ("Brands List", self.test_brands_endpoint),
            ("Orders List", self.test_orders_endpoint),
            ("Tables List", self.test_tables_endpoint),
            ("Dashboard Stats", self.test_dashboard_stats),
            ("Analytics", self.test_analytics_endpoint),
            ("Customers List", self.test_customers_endpoint),
            ("Coupons List", self.test_coupons_endpoint),
            ("Outlets List", self.test_outlets_endpoint),
            ("Payment Methods List", self.test_payment_methods_endpoint),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log_test(test_name, False, f"Exception: {str(e)}")
                failed += 1
        
        # Summary
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {passed + failed}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed / (passed + failed) * 100):.1f}%")
        print()
        
        # Failed tests details
        if failed > 0:
            print("FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"❌ {result['test']}: {result['message']}")
        
        # Response time analysis
        response_times = [r['response_time'] for r in self.test_results if r['response_time'] and r['success']]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            print(f"\nRESPONSE TIME ANALYSIS:")
            print(f"Average: {avg_time:.3f}s")
            print(f"Maximum: {max_time:.3f}s")
            print(f"All under 2s: {'✅ Yes' if max_time < 2.0 else '❌ No'}")
        
        return passed, failed

def main():
    """Main test execution"""
    tester = LaravelPOSAPITester()
    passed, failed = tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()