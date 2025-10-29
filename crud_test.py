#!/usr/bin/env python3
"""
Laravel POS API CRUD Testing
Tests CREATE, UPDATE, DELETE operations for products
"""

import requests
import json
import time
from datetime import datetime

class LaravelPOSCRUDTester:
    def __init__(self):
        self.api_url = "https://crud-flow-optimize.preview.emergentagent.com/api"
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
                response = requests.get(url, headers=headers, timeout=15)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=15)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=15)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=15)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response_time = time.time() - start_time
            
            return response, response_time
            
        except requests.exceptions.RequestException as e:
            return None, 0
    
    def login(self):
        """Login to get authentication token"""
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response, response_time = self.make_request('POST', '/auth/staff/login', login_data)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if data.get('success') and data.get('token'):
                    self.token = data['token']
                    self.log_test("Login", True, "Authentication successful", response_time, response.status_code)
                    return True
            except json.JSONDecodeError:
                pass
        
        self.log_test("Login", False, "Authentication failed", response_time, response.status_code if response else None)
        return False
    
    def test_create_product(self):
        """Test POST /api/products"""
        if not self.token:
            self.log_test("Create Product", False, "No authentication token")
            return False, None
        
        product_data = {
            "name": "Test Product API",
            "description": "Test product created via API testing",
            "price": 25000,
            "category_id": 1,
            "brand_id": 1,
            "stock": 100,
            "sku": f"TEST-{int(time.time())}",
            "status": "active"
        }
        
        response, response_time = self.make_request('POST', '/products', product_data, use_auth=True)
        
        if response is None:
            self.log_test("Create Product", False, "Connection failed")
            return False, None
        
        if response.status_code == 201 or response.status_code == 200:
            try:
                data = response.json()
                if data.get('success') and (data.get('data') or data.get('product')):
                    product_data = data.get('data') or data.get('product')
                    product_id = product_data.get('id')
                    self.log_test("Create Product", True, f"Product created with ID: {product_id}", response_time, response.status_code)
                    return True, product_id
                else:
                    self.log_test("Create Product", False, f"Invalid response structure: {data}", response_time, response.status_code)
                    return False, None
            except json.JSONDecodeError:
                self.log_test("Create Product", False, "Invalid JSON response", response_time, response.status_code)
                return False, None
        else:
            try:
                error_data = response.json()
                self.log_test("Create Product", False, f"HTTP {response.status_code}: {error_data.get('message', 'Creation failed')}", response_time, response.status_code)
            except:
                self.log_test("Create Product", False, f"HTTP {response.status_code}: Creation failed", response_time, response.status_code)
            return False, None
    
    def test_update_product(self, product_id):
        """Test PUT /api/products/{id}"""
        if not self.token or not product_id:
            self.log_test("Update Product", False, "No authentication token or product ID")
            return False
        
        update_data = {
            "name": "Updated Test Product API",
            "description": "Updated test product via API testing",
            "price": 30000,
            "category_id": 1,
            "brand_id": 1,
            "stock": 150,
            "sku": f"UPDATED-{int(time.time())}",
            "status": "active"
        }
        
        response, response_time = self.make_request('PUT', f'/products/{product_id}', update_data, use_auth=True)
        
        if response is None:
            self.log_test("Update Product", False, "Connection failed")
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success'):
                    self.log_test("Update Product", True, f"Product {product_id} updated successfully", response_time, response.status_code)
                    return True
                else:
                    self.log_test("Update Product", False, f"Update failed: {data.get('message', 'Unknown error')}", response_time, response.status_code)
                    return False
            except json.JSONDecodeError:
                self.log_test("Update Product", False, "Invalid JSON response", response_time, response.status_code)
                return False
        else:
            try:
                error_data = response.json()
                self.log_test("Update Product", False, f"HTTP {response.status_code}: {error_data.get('message', 'Update failed')}", response_time, response.status_code)
            except:
                self.log_test("Update Product", False, f"HTTP {response.status_code}: Update failed", response_time, response.status_code)
            return False
    
    def test_delete_product(self, product_id):
        """Test DELETE /api/products/{id}"""
        if not self.token or not product_id:
            self.log_test("Delete Product", False, "No authentication token or product ID")
            return False
        
        response, response_time = self.make_request('DELETE', f'/products/{product_id}', use_auth=True)
        
        if response is None:
            self.log_test("Delete Product", False, "Connection failed")
            return False
        
        if response.status_code == 200 or response.status_code == 204:
            try:
                if response.status_code == 204:
                    self.log_test("Delete Product", True, f"Product {product_id} deleted successfully", response_time, response.status_code)
                    return True
                else:
                    data = response.json()
                    if data.get('success'):
                        self.log_test("Delete Product", True, f"Product {product_id} deleted successfully", response_time, response.status_code)
                        return True
                    else:
                        self.log_test("Delete Product", False, f"Delete failed: {data.get('message', 'Unknown error')}", response_time, response.status_code)
                        return False
            except json.JSONDecodeError:
                # For 204 responses, no JSON is expected
                if response.status_code == 204:
                    self.log_test("Delete Product", True, f"Product {product_id} deleted successfully", response_time, response.status_code)
                    return True
                else:
                    self.log_test("Delete Product", False, "Invalid JSON response", response_time, response.status_code)
                    return False
        else:
            try:
                error_data = response.json()
                self.log_test("Delete Product", False, f"HTTP {response.status_code}: {error_data.get('message', 'Delete failed')}", response_time, response.status_code)
            except:
                self.log_test("Delete Product", False, f"HTTP {response.status_code}: Delete failed", response_time, response.status_code)
            return False
    
    def run_crud_tests(self):
        """Run all CRUD tests"""
        print("=" * 60)
        print("LARAVEL POS API CRUD TESTING")
        print("=" * 60)
        print()
        
        # Login first
        if not self.login():
            print("❌ Cannot proceed without authentication")
            return
        
        # Test CRUD operations
        print("Testing Product CRUD Operations...")
        print("-" * 40)
        
        # CREATE
        success, product_id = self.test_create_product()
        
        if success and product_id:
            # UPDATE
            self.test_update_product(product_id)
            
            # DELETE
            self.test_delete_product(product_id)
        else:
            print("❌ Skipping UPDATE and DELETE tests due to CREATE failure")
        
        # Summary
        print("=" * 60)
        print("CRUD TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r['success'])
        failed = len(self.test_results) - passed
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed / len(self.test_results) * 100):.1f}%")
        
        # Response time analysis
        response_times = [r['response_time'] for r in self.test_results if r['response_time'] and r['success']]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            print(f"\nRESPONSE TIME ANALYSIS:")
            print(f"Average: {avg_time:.3f}s")
            print(f"Maximum: {max_time:.3f}s")

def main():
    """Main test execution"""
    tester = LaravelPOSCRUDTester()
    tester.run_crud_tests()

if __name__ == "__main__":
    main()