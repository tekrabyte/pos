#!/usr/bin/env python3
"""
Backend API Testing Suite for QR Scan & Dine POS System
Tests all backend endpoints according to priority order
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

print(f"Testing backend at: {API_BASE_URL}")

class PosApiTester:
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
                self.log_test("Staff Login", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Staff Login", False, f"Exception: {str(e)}")
            
        return False
        
    def test_customer_register(self):
        """Test customer registration with email (PRIORITY TEST)"""
        print("\n=== Testing Customer Registration with Email (FIXED) ===")
        
        try:
            # Use the specific test data from review request
            customer_data = {
                "name": "Test Customer Email",
                "email": "tekrabyte@gmail.com",
                "phone": "081234567890",
                "address": "Test Address"
            }
            
            response = self.session.post(f"{API_BASE_URL}/auth/customer/register", 
                json=customer_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.customer_id = data.get("customer_id")
                    self.customer_email = customer_data["email"]
                    # Password is auto-generated, we'll get it from temp_password if email fails
                    self.customer_password = data.get("temp_password")
                    
                    # Check expected response fields
                    expected_fields = ["success", "customer_id", "message", "email_sent"]
                    missing_fields = [field for field in expected_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test("Customer Registration", False, f"Missing fields: {missing_fields}")
                        return False
                    
                    email_sent = data.get("email_sent", False)
                    message = f"Registration successful, customer_id: {self.customer_id}, email_sent: {email_sent}"
                    if not email_sent and data.get("temp_password"):
                        message += f", temp_password provided: {data['temp_password'][:3]}***"
                        self.customer_password = data["temp_password"]
                    
                    self.log_test("Customer Registration", True, message)
                    return True
                else:
                    self.log_test("Customer Registration", False, f"Registration failed: {data}")
            else:
                self.log_test("Customer Registration", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Customer Registration", False, f"Exception: {str(e)}")
            
        return False
        
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
    
    def run_all_tests(self):
        """Run all tests in priority order"""
        print("🚀 Starting Backend API Tests for QR Scan & Dine POS System")
        print("=" * 60)
        
        # Priority 1: Authentication
        self.test_staff_login()
        self.test_customer_register()
        self.test_customer_login()
        
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

if __name__ == "__main__":
    tester = PosApiTester()
    tester.run_all_tests()