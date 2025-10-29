#!/usr/bin/env python3
"""
Comprehensive test suite for Fiber (Golang) POS API backend
Tests all endpoints as specified in the review request
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

class POSAPITester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.token = None
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, endpoint: str, method: str, status: str, details: str = ""):
        """Log test results"""
        result = {
            'endpoint': endpoint,
            'method': method,
            'status': status,
            'details': details
        }
        self.test_results.append(result)
        status_symbol = "✅" if status == "PASS" else "❌"
        print(f"{status_symbol} {method} {endpoint} - {status}")
        if details:
            print(f"   Details: {details}")
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    headers: Optional[Dict] = None) -> requests.Response:
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}{endpoint}"
        
        # Add auth header if token exists
        if self.token and headers is None:
            headers = {}
        if self.token:
            headers = headers or {}
            headers['Authorization'] = f'Bearer {self.token}'
            
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            raise
    
    def test_health_check(self):
        """Test health check endpoint"""
        print("\n=== Testing Health Check ===")
        try:
            response = self.make_request('GET', '/api/health')
            
            if response.status_code == 200:
                data = response.json()
                if 'status' in data and data['status'] == 'OK':
                    self.log_test('/api/health', 'GET', 'PASS', 
                                f"Status: {data.get('status')}, Message: {data.get('message')}")
                else:
                    self.log_test('/api/health', 'GET', 'FAIL', 
                                f"Unexpected response format: {data}")
            else:
                self.log_test('/api/health', 'GET', 'FAIL', 
                            f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test('/api/health', 'GET', 'FAIL', f"Exception: {str(e)}")
    
    def test_authentication(self):
        """Test authentication endpoints"""
        print("\n=== Testing Authentication ===")
        
        # Test staff login
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            response = self.make_request('POST', '/api/auth/staff/login', data=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'token' in data:
                    self.token = data['token']
                    user_info = data.get('user', {})
                    self.log_test('/api/auth/staff/login', 'POST', 'PASS', 
                                f"Token received, User: {user_info.get('username')}")
                else:
                    self.log_test('/api/auth/staff/login', 'POST', 'FAIL', 
                                f"Login failed: {data}")
            else:
                self.log_test('/api/auth/staff/login', 'POST', 'FAIL', 
                            f"Status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test('/api/auth/staff/login', 'POST', 'FAIL', f"Exception: {str(e)}")
        
        # Test get current user (requires token)
        if self.token:
            try:
                response = self.make_request('GET', '/api/auth/staff/me')
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') and 'user' in data:
                        user = data['user']
                        self.log_test('/api/auth/staff/me', 'GET', 'PASS', 
                                    f"User ID: {user.get('id')}, Username: {user.get('username')}")
                    else:
                        self.log_test('/api/auth/staff/me', 'GET', 'FAIL', 
                                    f"Unexpected response: {data}")
                else:
                    self.log_test('/api/auth/staff/me', 'GET', 'FAIL', 
                                f"Status code: {response.status_code}")
                    
            except Exception as e:
                self.log_test('/api/auth/staff/me', 'GET', 'FAIL', f"Exception: {str(e)}")
        
        # Test logout
        if self.token:
            try:
                response = self.make_request('POST', '/api/auth/staff/logout')
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        self.log_test('/api/auth/staff/logout', 'POST', 'PASS', 
                                    f"Message: {data.get('message')}")
                    else:
                        self.log_test('/api/auth/staff/logout', 'POST', 'FAIL', 
                                    f"Logout failed: {data}")
                else:
                    self.log_test('/api/auth/staff/logout', 'POST', 'FAIL', 
                                f"Status code: {response.status_code}")
                    
            except Exception as e:
                self.log_test('/api/auth/staff/logout', 'POST', 'FAIL', f"Exception: {str(e)}")
    
    def test_products(self):
        """Test product endpoints"""
        print("\n=== Testing Products ===")
        
        # Test get all products
        try:
            response = self.make_request('GET', '/api/products')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'products' in data:
                    products = data['products']
                    product_count = len(products)
                    self.log_test('/api/products', 'GET', 'PASS', 
                                f"Retrieved {product_count} products")
                    
                    # Test get single product if products exist
                    if products and len(products) > 0:
                        first_product_id = products[0].get('id')
                        if first_product_id:
                            self.test_single_product(first_product_id)
                else:
                    self.log_test('/api/products', 'GET', 'FAIL', 
                                f"Unexpected response format: {data}")
            else:
                self.log_test('/api/products', 'GET', 'FAIL', 
                            f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test('/api/products', 'GET', 'FAIL', f"Exception: {str(e)}")
    
    def test_single_product(self, product_id: int):
        """Test single product endpoint"""
        try:
            response = self.make_request('GET', f'/api/products/{product_id}')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'product' in data:
                    product = data['product']
                    self.log_test(f'/api/products/{product_id}', 'GET', 'PASS', 
                                f"Product: {product.get('name')}, Price: {product.get('price')}")
                else:
                    self.log_test(f'/api/products/{product_id}', 'GET', 'FAIL', 
                                f"Unexpected response: {data}")
            else:
                self.log_test(f'/api/products/{product_id}', 'GET', 'FAIL', 
                            f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test(f'/api/products/{product_id}', 'GET', 'FAIL', f"Exception: {str(e)}")
    
    def test_categories(self):
        """Test category endpoints"""
        print("\n=== Testing Categories ===")
        
        try:
            response = self.make_request('GET', '/api/categories')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'categories' in data:
                    categories = data['categories']
                    category_count = len(categories)
                    self.log_test('/api/categories', 'GET', 'PASS', 
                                f"Retrieved {category_count} categories")
                else:
                    self.log_test('/api/categories', 'GET', 'FAIL', 
                                f"Unexpected response format: {data}")
            else:
                self.log_test('/api/categories', 'GET', 'FAIL', 
                            f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test('/api/categories', 'GET', 'FAIL', f"Exception: {str(e)}")
    
    def test_brands(self):
        """Test brand endpoints"""
        print("\n=== Testing Brands ===")
        
        try:
            response = self.make_request('GET', '/api/brands')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'brands' in data:
                    brands = data['brands']
                    brand_count = len(brands)
                    self.log_test('/api/brands', 'GET', 'PASS', 
                                f"Retrieved {brand_count} brands")
                else:
                    self.log_test('/api/brands', 'GET', 'FAIL', 
                                f"Unexpected response format: {data}")
            else:
                self.log_test('/api/brands', 'GET', 'FAIL', 
                            f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test('/api/brands', 'GET', 'FAIL', f"Exception: {str(e)}")
    
    def test_orders(self):
        """Test order endpoints"""
        print("\n=== Testing Orders ===")
        
        try:
            response = self.make_request('GET', '/api/orders')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'orders' in data:
                    orders = data['orders']
                    order_count = len(orders)
                    self.log_test('/api/orders', 'GET', 'PASS', 
                                f"Retrieved {order_count} orders")
                else:
                    self.log_test('/api/orders', 'GET', 'FAIL', 
                                f"Unexpected response format: {data}")
            else:
                self.log_test('/api/orders', 'GET', 'FAIL', 
                            f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test('/api/orders', 'GET', 'FAIL', f"Exception: {str(e)}")
    
    def test_tables(self):
        """Test table endpoints"""
        print("\n=== Testing Tables ===")
        
        try:
            response = self.make_request('GET', '/api/tables')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'tables' in data:
                    tables = data['tables']
                    table_count = len(tables)
                    self.log_test('/api/tables', 'GET', 'PASS', 
                                f"Retrieved {table_count} tables")
                else:
                    self.log_test('/api/tables', 'GET', 'FAIL', 
                                f"Unexpected response format: {data}")
            else:
                self.log_test('/api/tables', 'GET', 'FAIL', 
                            f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test('/api/tables', 'GET', 'FAIL', f"Exception: {str(e)}")
    
    def test_customers(self):
        """Test customer endpoints"""
        print("\n=== Testing Customers ===")
        
        try:
            response = self.make_request('GET', '/api/customers')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'customers' in data:
                    customers = data['customers']
                    customer_count = len(customers)
                    self.log_test('/api/customers', 'GET', 'PASS', 
                                f"Retrieved {customer_count} customers")
                else:
                    self.log_test('/api/customers', 'GET', 'FAIL', 
                                f"Unexpected response format: {data}")
            else:
                self.log_test('/api/customers', 'GET', 'FAIL', 
                            f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test('/api/customers', 'GET', 'FAIL', f"Exception: {str(e)}")
    
    def test_dashboard_analytics(self):
        """Test dashboard and analytics endpoints (requires authentication)"""
        print("\n=== Testing Dashboard & Analytics ===")
        
        if not self.token:
            print("⚠️  Skipping dashboard/analytics tests - no authentication token")
            return
        
        # Test dashboard stats
        try:
            response = self.make_request('GET', '/api/dashboard/stats')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'stats' in data:
                    stats = data['stats']
                    self.log_test('/api/dashboard/stats', 'GET', 'PASS', 
                                f"Stats retrieved: {list(stats.keys())}")
                else:
                    self.log_test('/api/dashboard/stats', 'GET', 'FAIL', 
                                f"Unexpected response: {data}")
            else:
                self.log_test('/api/dashboard/stats', 'GET', 'FAIL', 
                            f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test('/api/dashboard/stats', 'GET', 'FAIL', f"Exception: {str(e)}")
        
        # Test analytics
        try:
            response = self.make_request('GET', '/api/analytics')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'analytics' in data:
                    analytics = data['analytics']
                    self.log_test('/api/analytics', 'GET', 'PASS', 
                                f"Analytics retrieved: {list(analytics.keys())}")
                else:
                    self.log_test('/api/analytics', 'GET', 'FAIL', 
                                f"Unexpected response: {data}")
            else:
                self.log_test('/api/analytics', 'GET', 'FAIL', 
                            f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test('/api/analytics', 'GET', 'FAIL', f"Exception: {str(e)}")
    
    def test_payment_methods(self):
        """Test payment method endpoints"""
        print("\n=== Testing Payment Methods ===")
        
        try:
            response = self.make_request('GET', '/api/payment-methods')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'payment_methods' in data:
                    payment_methods = data['payment_methods']
                    method_count = len(payment_methods)
                    self.log_test('/api/payment-methods', 'GET', 'PASS', 
                                f"Retrieved {method_count} payment methods")
                else:
                    self.log_test('/api/payment-methods', 'GET', 'FAIL', 
                                f"Unexpected response format: {data}")
            else:
                self.log_test('/api/payment-methods', 'GET', 'FAIL', 
                            f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test('/api/payment-methods', 'GET', 'FAIL', f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Comprehensive POS API Testing")
        print("=" * 50)
        
        # Test basic endpoints first
        self.test_health_check()
        
        # Test authentication (this sets the token for protected endpoints)
        self.test_authentication()
        
        # Test data endpoints
        self.test_products()
        self.test_categories()
        self.test_brands()
        self.test_orders()
        self.test_tables()
        self.test_customers()
        self.test_payment_methods()
        
        # Test protected endpoints
        self.test_dashboard_analytics()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['status'] == 'PASS'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for test in self.test_results:
                if test['status'] == 'FAIL':
                    print(f"  ❌ {test['method']} {test['endpoint']}: {test['details']}")
        
        print("\n" + "=" * 50)

def main():
    """Main test execution"""
    # Use the external URL from frontend/.env
    base_url = "https://just-run-1.preview.emergentagent.com/api"
    
    print(f"Testing POS API at: {base_url}")
    
    tester = POSAPITester(base_url)
    tester.run_all_tests()
    
    # Return exit code based on test results
    failed_tests = len([t for t in tester.test_results if t['status'] == 'FAIL'])
    sys.exit(1 if failed_tests > 0 else 0)

if __name__ == "__main__":
    main()