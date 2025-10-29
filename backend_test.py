#!/usr/bin/env python3
"""
Backend API Testing Suite for QR Scan & Dine POS System
PRIORITY: Test CRUD endpoints for 422 errors and validation issues
"""

import requests
import json
import os
import sys
from pathlib import Path
import time
import websocket
import threading
from io import BytesIO

# Load environment variables
sys.path.append('/app/backend')
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

# Use the backend URL from review request
API_BASE_URL = "https://qrscan-dine-1.preview.emergentagent.com/api"

print(f"🎯 PRIORITY TESTING: CRUD Endpoints for 422 Errors")
print(f"Testing backend at: {API_BASE_URL}")
print("="*70)

class CrudErrorTester:
    def __init__(self):
        self.session = requests.Session()
        self.staff_token = None
        self.customer_token = None
        self.customer_id = None
        self.table_id = None
        self.category_id = None
        self.product_id = None
        self.order_id = None
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
    # Old methods removed - focusing on CRUD validation testing
        
    def get_existing_customer_for_testing(self):
        """Get existing customer for testing reset password functionality"""
        try:
            # Try to get existing customers (this might not be available, but let's try)
            # For now, we'll use a known customer ID from the database
            # Based on the review request, we know tekrabyte@gmail.com should exist
            self.customer_email = "tekrabyte@gmail.com"
            # We'll try to find the customer_id by attempting a login with a wrong password
            # and checking if we get "password salah" vs "email tidak ditemukan"
            
            # Try a test login to see if email exists
            response = self.session.post(f"{API_BASE_URL}/auth/customer/login", 
                json={"email": "tekrabyte@gmail.com", "password": "wrongpassword"})
            
            if response.status_code == 200:
                data = response.json()
                if not data.get("success") and "password salah" in data.get("message", "").lower():
                    # Email exists, we can use it for testing. Let's assume customer_id = 1 for testing
                    self.customer_id = 1  # This is an assumption, but we need it for testing
                    print(f"Found existing customer email: {self.customer_email}")
                    
        except Exception as e:
            print(f"Could not get existing customer: {str(e)}")
            pass
        
    def test_customer_login(self):
        """Test customer login"""
        print("\n=== Testing Customer Login ===")
        
        if not hasattr(self, 'customer_email'):
            self.log_test("Customer Login", False, "No customer registered for login test")
            return False
            
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/customer/login", 
                json={"email": self.customer_email, "password": self.customer_password})
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("token"):
                    self.customer_token = data["token"]
                    self.log_test("Customer Login", True, f"Login successful, token received")
                    return True
                else:
                    self.log_test("Customer Login", False, f"Login failed: {data.get('message', 'Unknown error')}")
            else:
                self.log_test("Customer Login", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Customer Login", False, f"Exception: {str(e)}")
            
        return False
        
    def test_create_table(self):
        """Test table creation with QR code"""
        print("\n=== Testing Table Creation ===")
        
        try:
            table_data = {
                "table_number": f"T{int(time.time() % 1000)}",
                "capacity": 4,
                "status": "available"
            }
            
            response = self.session.post(f"{API_BASE_URL}/tables", json=table_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("id") and data.get("qr_code"):
                    self.table_id = data["id"]
                    qr_code = data["qr_code"]
                    if qr_code.startswith("data:image/png;base64,"):
                        self.log_test("Table Creation", True, f"Table created with ID {self.table_id}, QR code generated")
                        return True
                    else:
                        self.log_test("Table Creation", False, "QR code format invalid")
                else:
                    self.log_test("Table Creation", False, f"Missing required fields in response: {data}")
            else:
                self.log_test("Table Creation", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Table Creation", False, f"Exception: {str(e)}")
            
        return False
        
    def test_get_tables(self):
        """Test getting all tables"""
        print("\n=== Testing Get Tables ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/tables")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Get Tables", True, f"Retrieved {len(data)} tables")
                    return True
                else:
                    self.log_test("Get Tables", False, f"Expected list, got: {type(data)}")
            else:
                self.log_test("Get Tables", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get Tables", False, f"Exception: {str(e)}")
            
        return False
        
    def test_get_table_by_id(self):
        """Test getting specific table"""
        print("\n=== Testing Get Table by ID ===")
        
        if not self.table_id:
            self.log_test("Get Table by ID", False, "No table ID available")
            return False
            
        try:
            response = self.session.get(f"{API_BASE_URL}/tables/{self.table_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("id") == self.table_id:
                    self.log_test("Get Table by ID", True, f"Retrieved table {self.table_id}")
                    return True
                else:
                    self.log_test("Get Table by ID", False, f"ID mismatch: expected {self.table_id}, got {data.get('id')}")
            else:
                self.log_test("Get Table by ID", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get Table by ID", False, f"Exception: {str(e)}")
            
        return False
        
    def test_create_category(self):
        """Test category creation"""
        print("\n=== Testing Category Creation ===")
        
        try:
            category_data = {
                "name": f"Test Category {int(time.time() % 1000)}",
                "description": "Test category for API testing"
            }
            
            response = self.session.post(f"{API_BASE_URL}/categories", json=category_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("id"):
                    self.category_id = data["id"]
                    self.log_test("Category Creation", True, f"Category created with ID {self.category_id}")
                    return True
                else:
                    self.log_test("Category Creation", False, f"No ID in response: {data}")
            else:
                self.log_test("Category Creation", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Category Creation", False, f"Exception: {str(e)}")
            
        return False
        
    def test_get_categories(self):
        """Test getting all categories"""
        print("\n=== Testing Get Categories ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/categories")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Get Categories", True, f"Retrieved {len(data)} categories")
                    return True
                else:
                    self.log_test("Get Categories", False, f"Expected list, got: {type(data)}")
            else:
                self.log_test("Get Categories", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get Categories", False, f"Exception: {str(e)}")
            
        return False
        
    def test_create_product(self):
        """Test product creation"""
        print("\n=== Testing Product Creation ===")
        
        try:
            product_data = {
                "name": f"Test Product {int(time.time() % 1000)}",
                "sku": f"SKU{int(time.time())}",
                "price": 25000.0,
                "stock": 100,
                "category_id": self.category_id,
                "description": "Test product for API testing",
                "status": "active"
            }
            
            response = self.session.post(f"{API_BASE_URL}/products", json=product_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("id"):
                    self.product_id = data["id"]
                    self.log_test("Product Creation", True, f"Product created with ID {self.product_id}")
                    return True
                else:
                    self.log_test("Product Creation", False, f"No ID in response: {data}")
            else:
                self.log_test("Product Creation", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Product Creation", False, f"Exception: {str(e)}")
            
        return False
        
    def test_get_products(self):
        """Test getting all products"""
        print("\n=== Testing Get Products ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/products")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Get Products", True, f"Retrieved {len(data)} products")
                    return True
                else:
                    self.log_test("Get Products", False, f"Expected list, got: {type(data)}")
            else:
                self.log_test("Get Products", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get Products", False, f"Exception: {str(e)}")
            
        return False
        
    def test_create_takeaway_order(self):
        """Test creating takeaway order"""
        print("\n=== Testing Takeaway Order Creation ===")
        
        if not self.customer_id or not self.product_id:
            self.log_test("Takeaway Order Creation", False, "Missing customer_id or product_id")
            return False
            
        try:
            order_data = {
                "customer_id": self.customer_id,
                "order_type": "takeaway",
                "items": [
                    {
                        "product_id": self.product_id,
                        "product_name": "Test Product",
                        "quantity": 2,
                        "price": 25000.0,
                        "subtotal": 50000.0
                    }
                ],
                "payment_method": "qris",
                "total_amount": 50000.0,
                "customer_name": "John Doe",
                "customer_phone": "081234567890"
            }
            
            response = self.session.post(f"{API_BASE_URL}/orders", json=order_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("id"):
                    self.order_id = data["id"]
                    self.log_test("Takeaway Order Creation", True, f"Order created with ID {self.order_id}")
                    return True
                else:
                    self.log_test("Takeaway Order Creation", False, f"No ID in response: {data}")
            else:
                self.log_test("Takeaway Order Creation", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Takeaway Order Creation", False, f"Exception: {str(e)}")
            
        return False
        
    def test_create_dinein_order(self):
        """Test creating dine-in order"""
        print("\n=== Testing Dine-in Order Creation ===")
        
        if not self.table_id or not self.product_id:
            self.log_test("Dine-in Order Creation", False, "Missing table_id or product_id")
            return False
            
        try:
            order_data = {
                "table_id": self.table_id,
                "order_type": "dine-in",
                "items": [
                    {
                        "product_id": self.product_id,
                        "product_name": "Test Product",
                        "quantity": 1,
                        "price": 25000.0,
                        "subtotal": 25000.0
                    }
                ],
                "payment_method": "bank_transfer",
                "total_amount": 25000.0,
                "customer_name": "Walk-in Customer",
                "customer_phone": "081987654321"
            }
            
            response = self.session.post(f"{API_BASE_URL}/orders", json=order_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("id"):
                    self.log_test("Dine-in Order Creation", True, f"Dine-in order created with ID {data['id']}")
                    return True
                else:
                    self.log_test("Dine-in Order Creation", False, f"No ID in response: {data}")
            else:
                self.log_test("Dine-in Order Creation", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Dine-in Order Creation", False, f"Exception: {str(e)}")
            
        return False
        
    def test_get_orders(self):
        """Test getting all orders"""
        print("\n=== Testing Get Orders ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/orders")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Get Orders", True, f"Retrieved {len(data)} orders")
                    return True
                else:
                    self.log_test("Get Orders", False, f"Expected list, got: {type(data)}")
            else:
                self.log_test("Get Orders", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get Orders", False, f"Exception: {str(e)}")
            
        return False
        
    def test_get_order_by_id(self):
        """Test getting specific order with items"""
        print("\n=== Testing Get Order by ID ===")
        
        if not self.order_id:
            self.log_test("Get Order by ID", False, "No order ID available")
            return False
            
        try:
            response = self.session.get(f"{API_BASE_URL}/orders/{self.order_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("id") == self.order_id and "items" in data:
                    self.log_test("Get Order by ID", True, f"Retrieved order {self.order_id} with {len(data['items'])} items")
                    return True
                else:
                    self.log_test("Get Order by ID", False, f"Missing order details or items: {data}")
            else:
                self.log_test("Get Order by ID", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get Order by ID", False, f"Exception: {str(e)}")
            
        return False
        
    def test_update_order_status(self):
        """Test updating order status"""
        print("\n=== Testing Order Status Update ===")
        
        if not self.order_id:
            self.log_test("Order Status Update", False, "No order ID available")
            return False
            
        try:
            status_data = {
                "status": "confirmed",
                "payment_verified": True
            }
            
            response = self.session.put(f"{API_BASE_URL}/orders/{self.order_id}/status", 
                json=status_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "confirmed":
                    self.log_test("Order Status Update", True, f"Order status updated to confirmed")
                    return True
                else:
                    self.log_test("Order Status Update", False, f"Status not updated: {data}")
            else:
                self.log_test("Order Status Update", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Order Status Update", False, f"Exception: {str(e)}")
            
        return False
        
    def test_pending_orders_count(self):
        """Test getting pending orders count"""
        print("\n=== Testing Pending Orders Count ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/orders/stats/pending")
            
            if response.status_code == 200:
                data = response.json()
                if "count" in data and isinstance(data["count"], int):
                    self.log_test("Pending Orders Count", True, f"Pending orders count: {data['count']}")
                    return True
                else:
                    self.log_test("Pending Orders Count", False, f"Invalid response format: {data}")
            else:
                self.log_test("Pending Orders Count", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Pending Orders Count", False, f"Exception: {str(e)}")
            
        return False
        
    def test_generate_qris(self):
        """Test QRIS generation"""
        print("\n=== Testing QRIS Generation ===")
        
        try:
            qris_data = {
                "amount": 50000,
                "order_number": "TEST-ORDER-001",
                "merchant_id": "TESTMERCHANT001"
            }
            
            response = self.session.post(f"{API_BASE_URL}/qris/generate", json=qris_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("qr_code_image"):
                    qr_image = data["qr_code_image"]
                    if qr_image.startswith("data:image/png;base64,"):
                        self.log_test("QRIS Generation", True, f"QRIS generated for amount {data['amount']}")
                        return True
                    else:
                        self.log_test("QRIS Generation", False, "Invalid QR code format")
                else:
                    self.log_test("QRIS Generation", False, f"Missing required fields: {data}")
            else:
                self.log_test("QRIS Generation", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("QRIS Generation", False, f"Exception: {str(e)}")
            
        return False
        
    def test_get_bank_accounts(self):
        """Test getting bank accounts"""
        print("\n=== Testing Get Bank Accounts ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/bank-accounts")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Get Bank Accounts", True, f"Retrieved {len(data)} bank accounts")
                    return True
                else:
                    self.log_test("Get Bank Accounts", False, f"Expected list, got: {type(data)}")
            else:
                self.log_test("Get Bank Accounts", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get Bank Accounts", False, f"Exception: {str(e)}")
            
        return False
        
    def test_upload_payment_proof(self):
        """Test payment proof upload"""
        print("\n=== Testing Payment Proof Upload ===")
        
        try:
            # Create a simple test image file
            test_image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\xcc\xdb\x1d\x00\x00\x00\x00IEND\xaeB`\x82'
            
            files = {
                'file': ('test_payment.png', BytesIO(test_image_content), 'image/png')
            }
            
            response = self.session.post(f"{API_BASE_URL}/upload/payment-proof", files=files)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("filename") and data.get("url"):
                    self.log_test("Payment Proof Upload", True, f"File uploaded: {data['filename']}")
                    return True
                else:
                    self.log_test("Payment Proof Upload", False, f"Missing required fields: {data}")
            else:
                self.log_test("Payment Proof Upload", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Payment Proof Upload", False, f"Exception: {str(e)}")
            
        return False
        
    def test_admin_reset_password_auto_generate(self):
        """Test admin reset customer password - auto generate mode (PRIORITY TEST)"""
        print("\n=== Testing Admin Reset Customer Password - Auto Generate Mode (NEW) ===")
        
        if not self.customer_id:
            self.log_test("Admin Reset Password Auto", False, "No customer_id available")
            return False
            
        try:
            # Test with empty body (auto-generate mode)
            response = self.session.post(f"{API_BASE_URL}/admin/customers/{self.customer_id}/reset-password")
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["success", "message", "email_sent"]
                missing_fields = [field for field in expected_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Admin Reset Password Auto", False, f"Missing fields: {missing_fields}")
                    return False
                
                if data.get("success"):
                    email_sent = data.get("email_sent", False)
                    message = f"Auto-generate reset successful, email_sent: {email_sent}"
                    
                    # If email failed, temp_password should be shown
                    if not email_sent and data.get("temp_password"):
                        message += f", temp_password provided: {data['temp_password'][:3]}***"
                        self.customer_password = data["temp_password"]  # Update for login test
                    
                    self.log_test("Admin Reset Password Auto", True, message)
                    return True
                else:
                    self.log_test("Admin Reset Password Auto", False, f"Reset failed: {data}")
            else:
                self.log_test("Admin Reset Password Auto", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Reset Password Auto", False, f"Exception: {str(e)}")
            
        return False
        
    def test_admin_reset_password_custom(self):
        """Test admin reset customer password - custom password mode (PRIORITY TEST)"""
        print("\n=== Testing Admin Reset Customer Password - Custom Password Mode (NEW) ===")
        
        if not self.customer_id:
            self.log_test("Admin Reset Password Custom", False, "No customer_id available")
            return False
            
        try:
            # Test with custom password
            custom_password = "CustomPass123"
            request_data = {
                "new_password": custom_password
            }
            
            response = self.session.post(f"{API_BASE_URL}/admin/customers/{self.customer_id}/reset-password", 
                json=request_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.customer_password = custom_password  # Update for login test
                    email_sent = data.get("email_sent", False)
                    message = f"Custom password reset successful, email_sent: {email_sent}"
                    self.log_test("Admin Reset Password Custom", True, message)
                    return True
                else:
                    self.log_test("Admin Reset Password Custom", False, f"Reset failed: {data}")
            else:
                self.log_test("Admin Reset Password Custom", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Reset Password Custom", False, f"Exception: {str(e)}")
            
        return False
        
    def test_admin_reset_password_validation(self):
        """Test admin reset password validation - password too short (PRIORITY TEST)"""
        print("\n=== Testing Admin Reset Password Validation - Password Too Short ===")
        
        if not self.customer_id:
            self.log_test("Admin Reset Password Validation", False, "No customer_id available")
            return False
            
        try:
            # Test with password too short (should fail)
            request_data = {
                "new_password": "12345"  # Only 5 characters, should fail
            }
            
            response = self.session.post(f"{API_BASE_URL}/admin/customers/{self.customer_id}/reset-password", 
                json=request_data)
            
            if response.status_code == 400:
                data = response.json()
                error_message = data.get("detail", "")
                if "Password minimal 6 karakter" in error_message:
                    self.log_test("Admin Reset Password Validation", True, f"Validation working: {error_message}")
                    return True
                else:
                    self.log_test("Admin Reset Password Validation", False, f"Wrong error message: {error_message}")
            else:
                self.log_test("Admin Reset Password Validation", False, f"Expected HTTP 400, got {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Reset Password Validation", False, f"Exception: {str(e)}")
            
        return False
        
    def test_customer_login_after_reset(self):
        """Test customer login after password reset (PRIORITY TEST)"""
        print("\n=== Testing Customer Login After Password Reset ===")
        
        if not hasattr(self, 'customer_email') or not self.customer_password:
            self.log_test("Customer Login After Reset", False, "No customer email or password available")
            return False
            
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/customer/login", 
                json={"email": self.customer_email, "password": self.customer_password})
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("token"):
                    self.customer_token = data["token"]
                    self.log_test("Customer Login After Reset", True, f"Login successful with reset password, token received")
                    return True
                else:
                    self.log_test("Customer Login After Reset", False, f"Login failed: {data.get('message', 'Unknown error')}")
            else:
                self.log_test("Customer Login After Reset", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Customer Login After Reset", False, f"Exception: {str(e)}")
            
        return False

    def test_delete_table(self):
        """Test table deletion"""
        print("\n=== Testing Table Deletion ===")
        
        if not self.table_id:
            self.log_test("Table Deletion", False, "No table ID available")
            return False
            
        try:
            response = self.session.delete(f"{API_BASE_URL}/tables/{self.table_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test("Table Deletion", True, f"Table {self.table_id} deleted successfully")
                    return True
                else:
                    self.log_test("Table Deletion", False, f"Deletion failed: {data}")
            else:
                self.log_test("Table Deletion", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Table Deletion", False, f"Exception: {str(e)}")
            
        return False
        
    def test_websocket_connection(self):
        """Test WebSocket connection (basic connectivity test)"""
        print("\n=== Testing WebSocket Connection ===")
        
        try:
            # Convert HTTP URL to WebSocket URL
            ws_url = API_BASE_URL.replace("https://", "wss://").replace("http://", "ws://") + "/ws/orders"
            
            connected = False
            message_received = False
            
            def on_open(ws):
                nonlocal connected
                connected = True
                print(f"WebSocket connected to {ws_url}")
                
            def on_message(ws, message):
                nonlocal message_received
                message_received = True
                print(f"WebSocket message received: {message}")
                
            def on_error(ws, error):
                print(f"WebSocket error: {error}")
                
            def on_close(ws, close_status_code, close_msg):
                print("WebSocket connection closed")
            
            # Create WebSocket connection with timeout
            ws = websocket.WebSocketApp(ws_url,
                                      on_open=on_open,
                                      on_message=on_message,
                                      on_error=on_error,
                                      on_close=on_close)
            
            # Run WebSocket in a separate thread with timeout
            def run_ws():
                ws.run_forever()
                
            ws_thread = threading.Thread(target=run_ws)
            ws_thread.daemon = True
            ws_thread.start()
            
            # Wait for connection
            time.sleep(3)
            
            if connected:
                # Send a test message
                ws.send("test")
                time.sleep(1)
                ws.close()
                
                self.log_test("WebSocket Connection", True, "WebSocket connection established successfully")
                return True
            else:
                self.log_test("WebSocket Connection", False, "Failed to establish WebSocket connection")
                return False
                
        except Exception as e:
            self.log_test("WebSocket Connection", False, f"Exception: {str(e)}")
            return False
    
    def run_priority_tests(self):
        """Run PRIORITY tests from review request"""
        print("🎯 Starting PRIORITY Backend API Tests - Email & Password Reset Features")
        print("=" * 70)
        
        # PRIORITY TESTS (from review request)
        print("\n🔥 PRIORITY TESTS - Email & Password Reset Features")
        self.test_customer_register()  # Test 1: Customer Registration with Email (FIXED)
        self.test_admin_reset_password_auto_generate()  # Test 2: Admin Reset - Auto Generate
        self.test_admin_reset_password_custom()  # Test 3: Admin Reset - Custom Password  
        self.test_admin_reset_password_validation()  # Test 4: Validation - Password Too Short
        self.test_customer_login_after_reset()  # Test 5: Customer Login After Reset
        
        # Print summary
        self.print_summary()
        
    def run_all_tests(self):
        """Run all tests in priority order"""
        print("🚀 Starting Backend API Tests for QR Scan & Dine POS System")
        print("=" * 60)
        
        # Priority 1: Authentication
        self.test_staff_login()
        self.test_customer_register()
        self.test_customer_login()
        
        # PRIORITY TESTS (from review request)
        print("\n🔥 PRIORITY TESTS - Email & Password Reset Features")
        self.test_admin_reset_password_auto_generate()
        self.test_admin_reset_password_custom()
        self.test_admin_reset_password_validation()
        self.test_customer_login_after_reset()
        
        # Priority 2: Table Management
        self.test_create_table()
        self.test_get_tables()
        self.test_get_table_by_id()
        
        # Priority 3: Products & Categories
        self.test_create_category()
        self.test_get_categories()
        self.test_create_product()
        self.test_get_products()
        
        # Priority 4: Orders
        self.test_create_takeaway_order()
        self.test_create_dinein_order()
        self.test_get_orders()
        self.test_get_order_by_id()
        self.test_update_order_status()
        self.test_pending_orders_count()
        
        # Priority 5: Payment
        self.test_generate_qris()
        self.test_get_bank_accounts()
        self.test_upload_payment_proof()
        
        # Priority 6: WebSocket (Optional)
        self.test_websocket_connection()
        
        # Cleanup
        self.test_delete_table()
        
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
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