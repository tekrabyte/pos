#!/usr/bin/env python3
"""
Backend API CRUD Validation Testing Suite for QR Scan & Dine POS System
PRIORITY: Test CRUD endpoints for 422 errors and validation issues
"""

import requests
import json
import time

# Use the correct backend URL from frontend .env
API_BASE_URL = "https://speedy-app-fix.preview.emergentagent.com/api"

print(f"🎯 PRIORITY TESTING: CRUD Endpoints for 422 Errors")
print(f"Testing backend at: {API_BASE_URL}")
print("="*70)

class CrudErrorTester:
    def __init__(self):
        self.session = requests.Session()
        self.staff_token = None
        self.test_results = {}
        self.error_422_found = []
        self.validation_errors = []
        
    def log_test(self, test_name, success, message="", response_data=None, status_code=None):
        """Log test results with focus on 422 errors"""
        if status_code == 422:
            self.error_422_found.append(f"{test_name}: {message}")
            status = "🔍 422 ERROR FOUND"
        elif status_code and status_code >= 400:
            self.validation_errors.append(f"{test_name}: HTTP {status_code} - {message}")
            status = "⚠️ ERROR"
        else:
            status = "✅ PASS" if success else "❌ FAIL"
            
        print(f"{status} {test_name}: {message}")
        self.test_results[test_name] = {
            "success": success,
            "message": message,
            "response_data": response_data,
            "status_code": status_code
        }
        
    def test_staff_login(self):
        """Test staff/admin authentication"""
        print("\n=== Testing Staff Authentication ===")
        
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/staff/login", 
                json={"username": "admin", "password": "admin123"})
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("token"):
                    self.staff_token = data["token"]
                    self.log_test("Staff Login", True, f"Login successful, token received")
                    return True
                else:
                    self.log_test("Staff Login", False, f"Login failed: {data.get('message', 'Unknown error')}")
            else:
                self.log_test("Staff Login", False, f"HTTP {response.status_code}: {response.text}", status_code=response.status_code)
                
        except Exception as e:
            self.log_test("Staff Login", False, f"Exception: {str(e)}")
            
        return False
        
    def test_order_creation_validation_errors(self):
        """PRIORITY: Test Order Creation for 422 errors and validation issues"""
        print("\n🔥 PRIORITY: Testing Order Creation Validation Errors")
        
        # Test 1: Missing required fields
        print("\n--- Test 1: Order with missing required fields ---")
        try:
            invalid_order = {}  # Empty order
            response = self.session.post(f"{API_BASE_URL}/orders", json=invalid_order)
            self.log_test("Order Creation - Missing Fields", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Order Creation - Missing Fields", False, f"Exception: {str(e)}")
            
        # Test 2: Invalid order_type
        print("\n--- Test 2: Order with invalid order_type ---")
        try:
            invalid_order = {
                "order_type": "invalid_type",  # Should be 'takeaway' or 'dine-in'
                "items": [],
                "payment_method": "qris",
                "total_amount": 50000
            }
            response = self.session.post(f"{API_BASE_URL}/orders", json=invalid_order)
            self.log_test("Order Creation - Invalid Type", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Order Creation - Invalid Type", False, f"Exception: {str(e)}")
            
        # Test 3: Takeaway without customer_id
        print("\n--- Test 3: Takeaway order without customer_id ---")
        try:
            invalid_order = {
                "order_type": "takeaway",
                "items": [{"product_id": 1, "product_name": "Test", "quantity": 1, "price": 25000, "subtotal": 25000}],
                "payment_method": "qris",
                "total_amount": 25000
                # Missing customer_id for takeaway
            }
            response = self.session.post(f"{API_BASE_URL}/orders", json=invalid_order)
            self.log_test("Order Creation - Takeaway No Customer", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Order Creation - Takeaway No Customer", False, f"Exception: {str(e)}")
            
        # Test 4: Dine-in without table_id
        print("\n--- Test 4: Dine-in order without table_id ---")
        try:
            invalid_order = {
                "order_type": "dine-in",
                "items": [{"product_id": 1, "product_name": "Test", "quantity": 1, "price": 25000, "subtotal": 25000}],
                "payment_method": "qris",
                "total_amount": 25000
                # Missing table_id for dine-in
            }
            response = self.session.post(f"{API_BASE_URL}/orders", json=invalid_order)
            self.log_test("Order Creation - Dine-in No Table", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Order Creation - Dine-in No Table", False, f"Exception: {str(e)}")
            
        # Test 5: Empty items array
        print("\n--- Test 5: Order with empty items ---")
        try:
            invalid_order = {
                "customer_id": 1,
                "order_type": "takeaway",
                "items": [],  # Empty items
                "payment_method": "qris",
                "total_amount": 0
            }
            response = self.session.post(f"{API_BASE_URL}/orders", json=invalid_order)
            self.log_test("Order Creation - Empty Items", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Order Creation - Empty Items", False, f"Exception: {str(e)}")
            
        # Test 6: Invalid payment method
        print("\n--- Test 6: Order with invalid payment method ---")
        try:
            invalid_order = {
                "customer_id": 1,
                "order_type": "takeaway",
                "items": [{"product_id": 1, "product_name": "Test", "quantity": 1, "price": 25000, "subtotal": 25000}],
                "payment_method": "invalid_payment",  # Invalid payment method
                "total_amount": 25000
            }
            response = self.session.post(f"{API_BASE_URL}/orders", json=invalid_order)
            self.log_test("Order Creation - Invalid Payment", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Order Creation - Invalid Payment", False, f"Exception: {str(e)}")
            
        # Test 7: Negative total amount
        print("\n--- Test 7: Order with negative total amount ---")
        try:
            invalid_order = {
                "customer_id": 1,
                "order_type": "takeaway",
                "items": [{"product_id": 1, "product_name": "Test", "quantity": 1, "price": 25000, "subtotal": 25000}],
                "payment_method": "qris",
                "total_amount": -1000  # Negative amount
            }
            response = self.session.post(f"{API_BASE_URL}/orders", json=invalid_order)
            self.log_test("Order Creation - Negative Amount", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Order Creation - Negative Amount", False, f"Exception: {str(e)}")
            
        # Test 8: Valid takeaway order (should work)
        print("\n--- Test 8: Valid takeaway order ---")
        try:
            valid_order = {
                "customer_id": 1,
                "order_type": "takeaway",
                "items": [{"product_id": 1, "product_name": "Test Product", "quantity": 2, "price": 25000, "subtotal": 50000}],
                "payment_method": "qris",
                "total_amount": 50000,
                "customer_name": "John Doe",
                "customer_phone": "081234567890"
            }
            response = self.session.post(f"{API_BASE_URL}/orders", json=valid_order)
            if response.status_code == 200:
                self.log_test("Order Creation - Valid Takeaway", True, 
                             f"Order created successfully", status_code=response.status_code)
            else:
                self.log_test("Order Creation - Valid Takeaway", False, 
                             f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Order Creation - Valid Takeaway", False, f"Exception: {str(e)}")
            
        # Test 9: Valid dine-in order (should work)
        print("\n--- Test 9: Valid dine-in order ---")
        try:
            valid_order = {
                "table_id": 1,
                "order_type": "dine-in",
                "items": [{"product_id": 1, "product_name": "Test Product", "quantity": 1, "price": 25000, "subtotal": 25000}],
                "payment_method": "bank_transfer",
                "total_amount": 25000,
                "customer_name": "Walk-in Customer",
                "customer_phone": "081987654321"
            }
            response = self.session.post(f"{API_BASE_URL}/orders", json=valid_order)
            if response.status_code == 200:
                self.log_test("Order Creation - Valid Dine-in", True, 
                             f"Order created successfully", status_code=response.status_code)
            else:
                self.log_test("Order Creation - Valid Dine-in", False, 
                             f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Order Creation - Valid Dine-in", False, f"Exception: {str(e)}")
            
    def test_order_status_update_validation(self):
        """PRIORITY: Test Order Status Update for 422 errors"""
        print("\n🔥 PRIORITY: Testing Order Status Update Validation")
        
        # Test 1: Invalid status value
        print("\n--- Test 1: Update with invalid status ---")
        try:
            invalid_status = {"status": "invalid_status"}
            response = self.session.put(f"{API_BASE_URL}/orders/1/status", json=invalid_status)
            self.log_test("Order Status - Invalid Status", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Order Status - Invalid Status", False, f"Exception: {str(e)}")
            
        # Test 2: Missing status field
        print("\n--- Test 2: Update with missing status field ---")
        try:
            invalid_status = {"payment_verified": True}  # Missing status
            response = self.session.put(f"{API_BASE_URL}/orders/1/status", json=invalid_status)
            self.log_test("Order Status - Missing Status", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Order Status - Missing Status", False, f"Exception: {str(e)}")
            
        # Test 3: Non-existent order ID
        print("\n--- Test 3: Update non-existent order ---")
        try:
            valid_status = {"status": "confirmed"}
            response = self.session.put(f"{API_BASE_URL}/orders/99999/status", json=valid_status)
            self.log_test("Order Status - Non-existent Order", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Order Status - Non-existent Order", False, f"Exception: {str(e)}")
            
        # Test 4: Valid status update (should work)
        print("\n--- Test 4: Valid status update ---")
        try:
            valid_status = {"status": "confirmed", "payment_verified": True}
            response = self.session.put(f"{API_BASE_URL}/orders/1/status", json=valid_status)
            if response.status_code == 200:
                self.log_test("Order Status - Valid Update", True, 
                             f"Status updated successfully", status_code=response.status_code)
            else:
                self.log_test("Order Status - Valid Update", False, 
                             f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Order Status - Valid Update", False, f"Exception: {str(e)}")
            
    def test_product_crud_validation(self):
        """PRIORITY: Test Product CRUD for 422 errors"""
        print("\n🔥 PRIORITY: Testing Product CRUD Validation")
        
        # Test 1: Create product with missing required fields
        print("\n--- Test 1: Create product missing required fields ---")
        try:
            invalid_product = {"name": "Test Product"}  # Missing sku, price
            response = self.session.post(f"{API_BASE_URL}/products", json=invalid_product)
            self.log_test("Product Create - Missing Fields", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Product Create - Missing Fields", False, f"Exception: {str(e)}")
            
        # Test 2: Create product with invalid price
        print("\n--- Test 2: Create product with invalid price ---")
        try:
            invalid_product = {
                "name": "Test Product",
                "sku": "TEST123",
                "price": "invalid_price",  # Should be number
                "stock": 10
            }
            response = self.session.post(f"{API_BASE_URL}/products", json=invalid_product)
            self.log_test("Product Create - Invalid Price", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Product Create - Invalid Price", False, f"Exception: {str(e)}")
            
        # Test 3: Create product with negative stock
        print("\n--- Test 3: Create product with negative stock ---")
        try:
            invalid_product = {
                "name": "Test Product",
                "sku": "TEST123",
                "price": 25000,
                "stock": -10  # Negative stock
            }
            response = self.session.post(f"{API_BASE_URL}/products", json=invalid_product)
            self.log_test("Product Create - Negative Stock", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Product Create - Negative Stock", False, f"Exception: {str(e)}")
            
        # Test 4: Update non-existent product
        print("\n--- Test 4: Update non-existent product ---")
        try:
            valid_product = {
                "name": "Updated Product",
                "sku": "UPD123",
                "price": 30000,
                "stock": 20
            }
            response = self.session.put(f"{API_BASE_URL}/products/99999", json=valid_product)
            self.log_test("Product Update - Non-existent", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Product Update - Non-existent", False, f"Exception: {str(e)}")
            
        # Test 5: Delete non-existent product
        print("\n--- Test 5: Delete non-existent product ---")
        try:
            response = self.session.delete(f"{API_BASE_URL}/products/99999")
            self.log_test("Product Delete - Non-existent", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Product Delete - Non-existent", False, f"Exception: {str(e)}")
            
        # Test 6: Valid product creation (should work)
        print("\n--- Test 6: Valid product creation ---")
        try:
            valid_product = {
                "name": f"Test Product {int(time.time() % 1000)}",
                "sku": f"SKU{int(time.time())}",
                "price": 25000.0,
                "stock": 100,
                "category_id": 1,
                "description": "Test product for validation",
                "status": "active"
            }
            response = self.session.post(f"{API_BASE_URL}/products", json=valid_product)
            if response.status_code == 200:
                self.log_test("Product Create - Valid", True, 
                             f"Product created successfully", status_code=response.status_code)
            else:
                self.log_test("Product Create - Valid", False, 
                             f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Product Create - Valid", False, f"Exception: {str(e)}")
            
    def test_category_crud_validation(self):
        """PRIORITY: Test Category CRUD for 422 errors"""
        print("\n🔥 PRIORITY: Testing Category CRUD Validation")
        
        # Test 1: Create category with missing name
        print("\n--- Test 1: Create category missing name ---")
        try:
            invalid_category = {"description": "Test description"}  # Missing name
            response = self.session.post(f"{API_BASE_URL}/categories", json=invalid_category)
            self.log_test("Category Create - Missing Name", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Category Create - Missing Name", False, f"Exception: {str(e)}")
            
        # Test 2: Create category with empty name
        print("\n--- Test 2: Create category with empty name ---")
        try:
            invalid_category = {"name": "", "description": "Test"}  # Empty name
            response = self.session.post(f"{API_BASE_URL}/categories", json=invalid_category)
            self.log_test("Category Create - Empty Name", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Category Create - Empty Name", False, f"Exception: {str(e)}")
            
        # Test 3: Update non-existent category
        print("\n--- Test 3: Update non-existent category ---")
        try:
            valid_category = {"name": "Updated Category", "description": "Updated"}
            response = self.session.put(f"{API_BASE_URL}/categories/99999", json=valid_category)
            self.log_test("Category Update - Non-existent", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Category Update - Non-existent", False, f"Exception: {str(e)}")
            
        # Test 4: Delete non-existent category
        print("\n--- Test 4: Delete non-existent category ---")
        try:
            response = self.session.delete(f"{API_BASE_URL}/categories/99999")
            self.log_test("Category Delete - Non-existent", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Category Delete - Non-existent", False, f"Exception: {str(e)}")
            
        # Test 5: Valid category creation (should work)
        print("\n--- Test 5: Valid category creation ---")
        try:
            valid_category = {
                "name": f"Test Category {int(time.time() % 1000)}",
                "description": "Test category for validation"
            }
            response = self.session.post(f"{API_BASE_URL}/categories", json=valid_category)
            if response.status_code == 200:
                self.log_test("Category Create - Valid", True, 
                             f"Category created successfully", status_code=response.status_code)
            else:
                self.log_test("Category Create - Valid", False, 
                             f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Category Create - Valid", False, f"Exception: {str(e)}")
            
    def test_table_crud_validation(self):
        """PRIORITY: Test Table CRUD for 422 errors"""
        print("\n🔥 PRIORITY: Testing Table CRUD Validation")
        
        # Test 1: Create table with missing table_number
        print("\n--- Test 1: Create table missing table_number ---")
        try:
            invalid_table = {"capacity": 4}  # Missing table_number
            response = self.session.post(f"{API_BASE_URL}/tables", json=invalid_table)
            self.log_test("Table Create - Missing Number", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Table Create - Missing Number", False, f"Exception: {str(e)}")
            
        # Test 2: Create table with invalid capacity
        print("\n--- Test 2: Create table with invalid capacity ---")
        try:
            invalid_table = {
                "table_number": "T001",
                "capacity": "invalid"  # Should be number
            }
            response = self.session.post(f"{API_BASE_URL}/tables", json=invalid_table)
            self.log_test("Table Create - Invalid Capacity", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Table Create - Invalid Capacity", False, f"Exception: {str(e)}")
            
        # Test 3: Delete non-existent table
        print("\n--- Test 3: Delete non-existent table ---")
        try:
            response = self.session.delete(f"{API_BASE_URL}/tables/99999")
            self.log_test("Table Delete - Non-existent", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Table Delete - Non-existent", False, f"Exception: {str(e)}")
            
        # Test 4: Valid table creation (should work)
        print("\n--- Test 4: Valid table creation ---")
        try:
            valid_table = {
                "table_number": f"T{int(time.time() % 1000)}",
                "capacity": 4,
                "status": "available"
            }
            response = self.session.post(f"{API_BASE_URL}/tables", json=valid_table)
            if response.status_code == 200:
                self.log_test("Table Create - Valid", True, 
                             f"Table created successfully", status_code=response.status_code)
            else:
                self.log_test("Table Create - Valid", False, 
                             f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Table Create - Valid", False, f"Exception: {str(e)}")
            
    def test_customer_reset_password_validation(self):
        """PRIORITY: Test Customer Reset Password for 422 errors"""
        print("\n🔥 PRIORITY: Testing Customer Reset Password Validation")
        
        # Test 1: Reset password for non-existent customer
        print("\n--- Test 1: Reset password for non-existent customer ---")
        try:
            valid_request = {"new_password": "newpass123"}
            response = self.session.post(f"{API_BASE_URL}/admin/customers/99999/reset-password", json=valid_request)
            self.log_test("Reset Password - Non-existent Customer", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Reset Password - Non-existent Customer", False, f"Exception: {str(e)}")
            
        # Test 2: Reset password with too short password
        print("\n--- Test 2: Reset password too short ---")
        try:
            invalid_request = {"new_password": "123"}  # Too short
            response = self.session.post(f"{API_BASE_URL}/admin/customers/1/reset-password", json=invalid_request)
            self.log_test("Reset Password - Too Short", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Reset Password - Too Short", False, f"Exception: {str(e)}")
            
        # Test 3: Reset password with invalid JSON
        print("\n--- Test 3: Reset password with invalid JSON ---")
        try:
            response = self.session.post(f"{API_BASE_URL}/admin/customers/1/reset-password", 
                                       data="invalid json", 
                                       headers={'Content-Type': 'application/json'})
            self.log_test("Reset Password - Invalid JSON", False, 
                         f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Reset Password - Invalid JSON", False, f"Exception: {str(e)}")
            
        # Test 4: Valid reset password (should work)
        print("\n--- Test 4: Valid reset password ---")
        try:
            valid_request = {"new_password": "newpass123"}
            response = self.session.post(f"{API_BASE_URL}/admin/customers/1/reset-password", json=valid_request)
            if response.status_code == 200:
                self.log_test("Reset Password - Valid", True, 
                             f"Password reset successfully", status_code=response.status_code)
            else:
                self.log_test("Reset Password - Valid", False, 
                             f"Response: {response.text}", status_code=response.status_code)
        except Exception as e:
            self.log_test("Reset Password - Valid", False, f"Exception: {str(e)}")
            
    def run_crud_validation_tests(self):
        """Run all CRUD validation tests to find 422 errors"""
        print("🎯 STARTING CRUD VALIDATION TESTS - Finding 422 Errors and Validation Issues")
        print("="*80)
        
        # First get authentication token
        self.test_staff_login()
        
        # PRIORITY TESTS from review request
        self.test_order_creation_validation_errors()
        self.test_order_status_update_validation()
        self.test_product_crud_validation()
        self.test_category_crud_validation()
        self.test_table_crud_validation()
        self.test_customer_reset_password_validation()
        
        # Print detailed summary
        self.print_detailed_summary()
        
    def print_detailed_summary(self):
        """Print detailed test summary with focus on 422 errors"""
        print("\n" + "="*80)
        print("📊 CRUD VALIDATION TEST RESULTS - 422 ERROR ANALYSIS")
        print("="*80)
        
        total = len(self.test_results)
        passed = sum(1 for result in self.test_results.values() if result["success"])
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Show 422 errors found
        if self.error_422_found:
            print(f"\n🔍 422 ERRORS FOUND ({len(self.error_422_found)}):")
            for error in self.error_422_found:
                print(f"   🔍 {error}")
        else:
            print("\n✅ NO 422 ERRORS FOUND")
            
        # Show other validation errors
        if self.validation_errors:
            print(f"\n⚠️ OTHER VALIDATION ERRORS ({len(self.validation_errors)}):")
            for error in self.validation_errors:
                print(f"   ⚠️ {error}")
        else:
            print("\n✅ NO OTHER VALIDATION ERRORS FOUND")
            
        # Show all test results
        print(f"\n📋 DETAILED TEST RESULTS:")
        for test_name, result in self.test_results.items():
            status_code = result.get("status_code", "")
            status_info = f" (HTTP {status_code})" if status_code else ""
            
            if result["success"]:
                print(f"✅ {test_name}: {result['message']}{status_info}")
            else:
                print(f"❌ {test_name}: {result['message']}{status_info}")
                
        # Summary of findings
        print(f"\n🎯 SUMMARY OF FINDINGS:")
        print(f"   • 422 Validation Errors Found: {len(self.error_422_found)}")
        print(f"   • Other HTTP Errors Found: {len(self.validation_errors)}")
        print(f"   • Total Endpoints Tested: {total}")
        
        if self.error_422_found or self.validation_errors:
            print(f"\n⚠️ RECOMMENDATION: Review the endpoints with validation errors above")
            print(f"   These may need better input validation or error handling")
        else:
            print(f"\n✅ EXCELLENT: No validation errors found in CRUD endpoints")

if __name__ == "__main__":
    tester = CrudErrorTester()
    
    # Run the CRUD validation tests as requested
    tester.run_crud_validation_tests()