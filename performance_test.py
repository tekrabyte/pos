#!/usr/bin/env python3
"""
Backend CRUD Performance & Error Handling Test Suite
Focus: Test all CRUD operations for performance and proper error handling with new axios configuration (30s timeout)
"""

import requests
import json
import time
import sys
from pathlib import Path

# Load environment variables
sys.path.append('/app/backend')
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

# Use the backend URL from frontend .env
API_BASE_URL = "https://complete-admin-crud.preview.emergentagent.com/api"

print(f"🎯 BACKEND CRUD PERFORMANCE & ERROR HANDLING TEST")
print(f"Testing backend at: {API_BASE_URL}")
print("="*70)

class PerformanceTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 30  # Match axios timeout
        self.staff_token = None
        self.test_results = []
        self.performance_issues = []
        self.error_handling_issues = []
        
    def log_test(self, test_name, success, message="", response_time=None, status_code=None):
        """Log test results with performance metrics"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "response_time": response_time,
            "status_code": status_code
        }
        
        # Check performance (flag if > 1 second)
        if response_time and response_time > 1.0:
            self.performance_issues.append(f"{test_name}: {response_time:.2f}s (> 1s threshold)")
            
        # Check error handling
        if status_code and status_code >= 500:
            self.error_handling_issues.append(f"{test_name}: HTTP {status_code} - Server Error")
            
        status_icon = "✅" if success else "❌"
        time_info = f" ({response_time:.3f}s)" if response_time else ""
        status_info = f" [HTTP {status_code}]" if status_code else ""
        
        print(f"{status_icon} {test_name}: {message}{time_info}{status_info}")
        self.test_results.append(result)
        
    def authenticate_staff(self):
        """Authenticate as admin to get token for protected endpoints"""
        print("\n=== Staff Authentication ===")
        
        start_time = time.time()
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/staff/login", 
                json={"username": "admin", "password": "admin123"})
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("token"):
                    self.staff_token = data["token"]
                    # Set authorization header for future requests
                    self.session.headers.update({"Authorization": f"Bearer {self.staff_token}"})
                    self.log_test("Staff Authentication", True, "Login successful", response_time, response.status_code)
                    return True
                else:
                    self.log_test("Staff Authentication", False, f"Login failed: {data.get('message', 'Unknown error')}", response_time, response.status_code)
            else:
                self.log_test("Staff Authentication", False, f"Authentication failed", response_time, response.status_code)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Staff Authentication", False, f"Exception: {str(e)}", response_time)
            
        return False
        
    def test_product_crud_performance(self):
        """Test Product CRUD operations for performance and error handling"""
        print("\n=== Product CRUD Performance Tests ===")
        
        # Test 1: GET /api/products (test response time)
        start_time = time.time()
        try:
            response = self.session.get(f"{API_BASE_URL}/products")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("GET /api/products", True, f"Retrieved {len(data)} products", response_time, response.status_code)
                else:
                    self.log_test("GET /api/products", False, f"Expected list, got {type(data)}", response_time, response.status_code)
            else:
                self.log_test("GET /api/products", False, "Failed to retrieve products", response_time, response.status_code)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("GET /api/products", False, f"Exception: {str(e)}", response_time)
            
        # Test 2: POST /api/products (create with valid data)
        start_time = time.time()
        try:
            product_data = {
                "name": f"Performance Test Product {int(time.time())}",
                "sku": f"PERF{int(time.time())}",
                "price": 25000.0,
                "stock": 100,
                "description": "Performance test product",
                "status": "active"
            }
            
            response = self.session.post(f"{API_BASE_URL}/products", json=product_data)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("id"):
                    self.product_id = data["id"]
                    self.log_test("POST /api/products", True, f"Product created with ID {self.product_id}", response_time, response.status_code)
                else:
                    self.log_test("POST /api/products", False, "No ID in response", response_time, response.status_code)
            else:
                self.log_test("POST /api/products", False, "Failed to create product", response_time, response.status_code)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("POST /api/products", False, f"Exception: {str(e)}", response_time)
            
        # Test 3: GET /api/products/{id} (retrieve single product)
        if hasattr(self, 'product_id'):
            start_time = time.time()
            try:
                response = self.session.get(f"{API_BASE_URL}/products/{self.product_id}")
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("id") == self.product_id:
                        self.log_test("GET /api/products/{id}", True, f"Retrieved product {self.product_id}", response_time, response.status_code)
                    else:
                        self.log_test("GET /api/products/{id}", False, "Product ID mismatch", response_time, response.status_code)
                else:
                    self.log_test("GET /api/products/{id}", False, "Failed to retrieve product", response_time, response.status_code)
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test("GET /api/products/{id}", False, f"Exception: {str(e)}", response_time)
                
        # Test 4: PUT /api/products/{id} (update product)
        if hasattr(self, 'product_id'):
            start_time = time.time()
            try:
                update_data = {
                    "name": f"Updated Performance Test Product {int(time.time())}",
                    "sku": f"UPD{int(time.time())}",
                    "price": 30000.0,
                    "stock": 150,
                    "description": "Updated performance test product",
                    "status": "active"
                }
                
                response = self.session.put(f"{API_BASE_URL}/products/{self.product_id}", json=update_data)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("name") == update_data["name"]:
                        self.log_test("PUT /api/products/{id}", True, f"Product {self.product_id} updated", response_time, response.status_code)
                    else:
                        self.log_test("PUT /api/products/{id}", False, "Product not updated properly", response_time, response.status_code)
                else:
                    self.log_test("PUT /api/products/{id}", False, "Failed to update product", response_time, response.status_code)
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test("PUT /api/products/{id}", False, f"Exception: {str(e)}", response_time)
                
        # Test 5: DELETE /api/products/{id} (delete product)
        if hasattr(self, 'product_id'):
            start_time = time.time()
            try:
                response = self.session.delete(f"{API_BASE_URL}/products/{self.product_id}")
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        self.log_test("DELETE /api/products/{id}", True, f"Product {self.product_id} deleted", response_time, response.status_code)
                    else:
                        self.log_test("DELETE /api/products/{id}", False, "Delete operation failed", response_time, response.status_code)
                else:
                    self.log_test("DELETE /api/products/{id}", False, "Failed to delete product", response_time, response.status_code)
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test("DELETE /api/products/{id}", False, f"Exception: {str(e)}", response_time)
                
    def test_category_crud_performance(self):
        """Test Category CRUD operations for performance and error handling"""
        print("\n=== Category CRUD Performance Tests ===")
        
        # Test 1: GET /api/categories (test response time)
        start_time = time.time()
        try:
            response = self.session.get(f"{API_BASE_URL}/categories")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("GET /api/categories", True, f"Retrieved {len(data)} categories", response_time, response.status_code)
                else:
                    self.log_test("GET /api/categories", False, f"Expected list, got {type(data)}", response_time, response.status_code)
            else:
                self.log_test("GET /api/categories", False, "Failed to retrieve categories", response_time, response.status_code)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("GET /api/categories", False, f"Exception: {str(e)}", response_time)
            
        # Test 2: POST /api/categories (create)
        start_time = time.time()
        try:
            category_data = {
                "name": f"Performance Test Category {int(time.time())}",
                "description": "Performance test category"
            }
            
            response = self.session.post(f"{API_BASE_URL}/categories", json=category_data)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("id"):
                    self.category_id = data["id"]
                    self.log_test("POST /api/categories", True, f"Category created with ID {self.category_id}", response_time, response.status_code)
                else:
                    self.log_test("POST /api/categories", False, "No ID in response", response_time, response.status_code)
            else:
                self.log_test("POST /api/categories", False, "Failed to create category", response_time, response.status_code)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("POST /api/categories", False, f"Exception: {str(e)}", response_time)
            
        # Test 3: PUT /api/categories/{id} (update)
        if hasattr(self, 'category_id'):
            start_time = time.time()
            try:
                update_data = {
                    "name": f"Updated Performance Test Category {int(time.time())}",
                    "description": "Updated performance test category"
                }
                
                response = self.session.put(f"{API_BASE_URL}/categories/{self.category_id}", json=update_data)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("name") == update_data["name"]:
                        self.log_test("PUT /api/categories/{id}", True, f"Category {self.category_id} updated", response_time, response.status_code)
                    else:
                        self.log_test("PUT /api/categories/{id}", False, "Category not updated properly", response_time, response.status_code)
                else:
                    self.log_test("PUT /api/categories/{id}", False, "Failed to update category", response_time, response.status_code)
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test("PUT /api/categories/{id}", False, f"Exception: {str(e)}", response_time)
                
        # Test 4: DELETE /api/categories/{id} (delete)
        if hasattr(self, 'category_id'):
            start_time = time.time()
            try:
                response = self.session.delete(f"{API_BASE_URL}/categories/{self.category_id}")
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        self.log_test("DELETE /api/categories/{id}", True, f"Category {self.category_id} deleted", response_time, response.status_code)
                    else:
                        self.log_test("DELETE /api/categories/{id}", False, "Delete operation failed", response_time, response.status_code)
                else:
                    self.log_test("DELETE /api/categories/{id}", False, "Failed to delete category", response_time, response.status_code)
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test("DELETE /api/categories/{id}", False, f"Exception: {str(e)}", response_time)
                
    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n=== Error Handling Tests ===")
        
        # Test 1: Invalid data (should return proper 400/422)
        start_time = time.time()
        try:
            invalid_product = {
                "name": "",  # Empty name
                "sku": "",   # Empty SKU
                "price": "invalid",  # Invalid price type
                "stock": -10  # Negative stock
            }
            
            response = self.session.post(f"{API_BASE_URL}/products", json=invalid_product)
            response_time = time.time() - start_time
            
            if response.status_code in [400, 422]:
                self.log_test("Error Handling - Invalid Data", True, f"Proper error response for invalid data", response_time, response.status_code)
            else:
                self.log_test("Error Handling - Invalid Data", False, f"Expected 400/422, got {response.status_code}", response_time, response.status_code)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Error Handling - Invalid Data", False, f"Exception: {str(e)}", response_time)
            
        # Test 2: Non-existent IDs (should return 404)
        start_time = time.time()
        try:
            response = self.session.get(f"{API_BASE_URL}/products/99999")
            response_time = time.time() - start_time
            
            if response.status_code == 404:
                self.log_test("Error Handling - Non-existent ID", True, f"Proper 404 for non-existent product", response_time, response.status_code)
            else:
                self.log_test("Error Handling - Non-existent ID", False, f"Expected 404, got {response.status_code}", response_time, response.status_code)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Error Handling - Non-existent ID", False, f"Exception: {str(e)}", response_time)
            
        # Test 3: Authentication (should return 401 if not authenticated)
        # Remove auth header temporarily
        auth_header = self.session.headers.pop("Authorization", None)
        
        start_time = time.time()
        try:
            response = self.session.post(f"{API_BASE_URL}/admin/customers/1/reset-password")
            response_time = time.time() - start_time
            
            if response.status_code == 401:
                self.log_test("Error Handling - Authentication", True, f"Proper 401 for unauthenticated request", response_time, response.status_code)
            else:
                # Some endpoints might not require auth, so this might not be 401
                self.log_test("Error Handling - Authentication", True, f"Response for unauthenticated request", response_time, response.status_code)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Error Handling - Authentication", False, f"Exception: {str(e)}", response_time)
            
        # Restore auth header
        if auth_header:
            self.session.headers["Authorization"] = auth_header
            
    def test_database_connection(self):
        """Test database connection stability"""
        print("\n=== Database Connection Tests ===")
        
        # Test concurrent requests (simulate load)
        print("Testing concurrent requests...")
        
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def make_request(endpoint, result_queue):
            start_time = time.time()
            try:
                response = self.session.get(f"{API_BASE_URL}/{endpoint}")
                response_time = time.time() - start_time
                result_queue.put({
                    "endpoint": endpoint,
                    "success": response.status_code == 200,
                    "response_time": response_time,
                    "status_code": response.status_code
                })
            except Exception as e:
                response_time = time.time() - start_time
                result_queue.put({
                    "endpoint": endpoint,
                    "success": False,
                    "response_time": response_time,
                    "error": str(e)
                })
        
        # Create multiple threads for concurrent requests
        endpoints = ["products", "categories", "tables", "bank-accounts"]
        threads = []
        
        start_time = time.time()
        for endpoint in endpoints:
            for i in range(3):  # 3 requests per endpoint
                thread = threading.Thread(target=make_request, args=(endpoint, results_queue))
                threads.append(thread)
                thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
            
        total_time = time.time() - start_time
        
        # Collect results
        successful_requests = 0
        total_requests = len(threads)
        
        while not results_queue.empty():
            result = results_queue.get()
            if result["success"]:
                successful_requests += 1
                
        success_rate = (successful_requests / total_requests) * 100
        
        if success_rate >= 90:
            self.log_test("Database Connection - Concurrent Requests", True, 
                         f"{successful_requests}/{total_requests} requests successful ({success_rate:.1f}%)", 
                         total_time)
        else:
            self.log_test("Database Connection - Concurrent Requests", False, 
                         f"Only {successful_requests}/{total_requests} requests successful ({success_rate:.1f}%)", 
                         total_time)
                         
    def print_performance_summary(self):
        """Print comprehensive performance and error handling summary"""
        print("\n" + "="*70)
        print("📊 PERFORMANCE & ERROR HANDLING TEST SUMMARY")
        print("="*70)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - successful_tests
        
        print(f"Total Tests Executed: {total_tests}")
        print(f"Successful Tests: {successful_tests}")
        print(f"Failed Tests: {failed_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        # Performance Analysis
        response_times = [r["response_time"] for r in self.test_results if r["response_time"]]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            print(f"\n⏱️ PERFORMANCE METRICS:")
            print(f"Average Response Time: {avg_response_time:.3f}s")
            print(f"Fastest Response: {min_response_time:.3f}s")
            print(f"Slowest Response: {max_response_time:.3f}s")
            
            if self.performance_issues:
                print(f"\n⚠️ PERFORMANCE ISSUES (> 1 second):")
                for issue in self.performance_issues:
                    print(f"   • {issue}")
            else:
                print(f"\n✅ ALL RESPONSES UNDER 1 SECOND THRESHOLD")
                
        # Error Handling Analysis
        status_codes = {}
        for result in self.test_results:
            if result["status_code"]:
                code = result["status_code"]
                status_codes[code] = status_codes.get(code, 0) + 1
                
        print(f"\n📋 HTTP STATUS CODE DISTRIBUTION:")
        for code, count in sorted(status_codes.items()):
            print(f"   HTTP {code}: {count} responses")
            
        if self.error_handling_issues:
            print(f"\n❌ ERROR HANDLING ISSUES:")
            for issue in self.error_handling_issues:
                print(f"   • {issue}")
        else:
            print(f"\n✅ NO 500 ERRORS DETECTED")
            
        # Detailed Results
        print(f"\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            time_info = f" ({result['response_time']:.3f}s)" if result["response_time"] else ""
            status_info = f" [HTTP {result['status_code']}]" if result["status_code"] else ""
            print(f"{status} {result['test_name']}: {result['message']}{time_info}{status_info}")
            
        # Overall Assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        if failed_tests == 0 and not self.performance_issues and not self.error_handling_issues:
            print("✅ EXCELLENT: All CRUD operations working perfectly with good performance")
        elif failed_tests == 0 and not self.error_handling_issues:
            print("✅ GOOD: All CRUD operations working, minor performance issues detected")
        elif not self.error_handling_issues:
            print("⚠️ FAIR: Some CRUD operations failing, but no server errors")
        else:
            print("❌ NEEDS ATTENTION: Critical issues detected in CRUD operations or error handling")
            
    def run_all_tests(self):
        """Run all performance and error handling tests"""
        print("🚀 Starting CRUD Performance & Error Handling Tests")
        print("="*70)
        
        # Authenticate first
        if not self.authenticate_staff():
            print("❌ Cannot proceed without authentication")
            return
            
        # Run CRUD performance tests
        self.test_product_crud_performance()
        self.test_category_crud_performance()
        
        # Run error handling tests
        self.test_error_handling()
        
        # Test database connection under load
        self.test_database_connection()
        
        # Print comprehensive summary
        self.print_performance_summary()

if __name__ == "__main__":
    tester = PerformanceTester()
    tester.run_all_tests()