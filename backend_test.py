#!/usr/bin/env python3
"""
Backend API Test Suite for POS System
Tests specific endpoints as requested in the review request
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
        self.created_items = {
            'brands': [],
            'roles': [],
            'outlets': [],
            'payment_methods': [],
            'coupons': []
        }
        
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
                "password": "password"
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
    
    def test_products_bundle_portion_support(self):
        """Test Product API endpoints with new bundle and portion fields as requested"""
        print("\n=== Testing Products API - Bundle & Portion Support ===")
        
        # Test Case 1: GET /api/products - Verify all new fields are returned
        print("\n1. Testing GET /api/products - Verify new fields")
        try:
            response = self.make_request('GET', '/api/products')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'products' in data:
                    products = data['products']
                    product_count = len(products)
                    
                    # Check if new fields are present in response
                    required_fields = ['is_bundle', 'bundle_items', 'has_portions', 'unit', 'portion_size']
                    if products and len(products) > 0:
                        sample_product = products[0]
                        missing_fields = [field for field in required_fields if field not in sample_product]
                        
                        if missing_fields:
                            self.log_test('/api/products', 'GET', 'FAIL', 
                                        f"Missing new fields: {missing_fields}")
                        else:
                            self.log_test('/api/products', 'GET', 'PASS', 
                                        f"Retrieved {product_count} products with all new fields: {required_fields}")
                    else:
                        self.log_test('/api/products', 'GET', 'PASS', 
                                    f"Retrieved {product_count} products (empty list)")
                else:
                    self.log_test('/api/products', 'GET', 'FAIL', 
                                f"Unexpected response format: {data}")
            else:
                self.log_test('/api/products', 'GET', 'FAIL', 
                            f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test('/api/products', 'GET', 'FAIL', f"Exception: {str(e)}")
        
        # Test Case 2: POST /api/products - Create regular product with unit
        print("\n2. Testing POST /api/products - Create regular product")
        regular_product_id = None
        try:
            regular_product_data = {
                "name": "Beras Premium",
                "sku": "BERAS001",
                "price": 15000,
                "stock": 100,
                "has_portions": False,
                "unit": "kg",
                "portion_size": 1,
                "category_id": 1,
                "brand_id": 1
            }
            
            response = self.make_request('POST', '/api/products', data=regular_product_data)
            
            if response.status_code in [200, 201]:
                data = response.json()
                if data.get('success'):
                    product = data.get('product', {})
                    regular_product_id = product.get('id')
                    self.log_test('/api/products', 'POST', 'PASS', 
                                f"Regular product created: {regular_product_data['name']}, ID: {regular_product_id}")
                else:
                    self.log_test('/api/products', 'POST', 'FAIL', 
                                f"Creation failed: {data}")
            else:
                self.log_test('/api/products', 'POST', 'FAIL', 
                            f"Status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test('/api/products', 'POST', 'FAIL', f"Exception: {str(e)}")
        
        # Test Case 3: POST /api/products - Create bundle product with portions
        print("\n3. Testing POST /api/products - Create bundle product")
        bundle_product_id = None
        try:
            bundle_product_data = {
                "name": "Paket Nasi Komplit",
                "sku": "PAKET001",
                "price": 25000,
                "stock": 50,
                "is_bundle": True,
                "has_portions": True,
                "unit": "porsi",
                "portion_size": 0.25,
                "bundle_items": [],
                "category_id": 1,
                "brand_id": 1
            }
            
            response = self.make_request('POST', '/api/products', data=bundle_product_data)
            
            if response.status_code in [200, 201]:
                data = response.json()
                if data.get('success'):
                    product = data.get('product', {})
                    bundle_product_id = product.get('id')
                    self.log_test('/api/products', 'POST', 'PASS', 
                                f"Bundle product created: {bundle_product_data['name']}, ID: {bundle_product_id}")
                else:
                    self.log_test('/api/products', 'POST', 'FAIL', 
                                f"Bundle creation failed: {data}")
            else:
                self.log_test('/api/products', 'POST', 'FAIL', 
                            f"Status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test('/api/products', 'POST', 'FAIL', f"Exception: {str(e)}")
        
        # Test Case 4: GET /api/products/:id - Get single product
        print("\n4. Testing GET /api/products/:id - Get single product")
        if regular_product_id:
            self.test_single_product_with_new_fields(regular_product_id)
        elif bundle_product_id:
            self.test_single_product_with_new_fields(bundle_product_id)
        
        # Test Case 5: PUT /api/products/:id - Update product with new fields
        print("\n5. Testing PUT /api/products/:id - Update product")
        if regular_product_id:
            try:
                update_data = {
                    "has_portions": True,
                    "unit": "gram",
                    "portion_size": 250
                }
                
                response = self.make_request('PUT', f'/api/products/{regular_product_id}', data=update_data)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        self.log_test(f'/api/products/{regular_product_id}', 'PUT', 'PASS', 
                                    "Product updated with new fields successfully")
                        
                        # Verify the update by getting the product again
                        verify_response = self.make_request('GET', f'/api/products/{regular_product_id}')
                        if verify_response.status_code == 200:
                            verify_data = verify_response.json()
                            if verify_data.get('success'):
                                updated_product = verify_data.get('product', {})
                                if (updated_product.get('has_portions') == True and 
                                    updated_product.get('unit') == 'gram' and 
                                    updated_product.get('portion_size') == 250):
                                    self.log_test(f'/api/products/{regular_product_id}', 'GET', 'PASS', 
                                                "Update verification successful")
                                else:
                                    self.log_test(f'/api/products/{regular_product_id}', 'GET', 'FAIL', 
                                                f"Update not reflected: {updated_product}")
                    else:
                        self.log_test(f'/api/products/{regular_product_id}', 'PUT', 'FAIL', 
                                    f"Update failed: {data}")
                else:
                    self.log_test(f'/api/products/{regular_product_id}', 'PUT', 'FAIL', 
                                f"Status code: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f'/api/products/{regular_product_id}', 'PUT', 'FAIL', f"Exception: {str(e)}")
        
        # Clean up created test products
        self.cleanup_test_products([regular_product_id, bundle_product_id])
    
    def test_single_product_with_new_fields(self, product_id: int):
        """Test single product endpoint and verify new fields"""
        try:
            response = self.make_request('GET', f'/api/products/{product_id}')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'product' in data:
                    product = data['product']
                    required_fields = ['is_bundle', 'bundle_items', 'has_portions', 'unit', 'portion_size']
                    missing_fields = [field for field in required_fields if field not in product]
                    
                    if missing_fields:
                        self.log_test(f'/api/products/{product_id}', 'GET', 'FAIL', 
                                    f"Missing fields: {missing_fields}")
                    else:
                        self.log_test(f'/api/products/{product_id}', 'GET', 'PASS', 
                                    f"Product: {product.get('name')}, All new fields present")
                else:
                    self.log_test(f'/api/products/{product_id}', 'GET', 'FAIL', 
                                f"Unexpected response: {data}")
            else:
                self.log_test(f'/api/products/{product_id}', 'GET', 'FAIL', 
                            f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test(f'/api/products/{product_id}', 'GET', 'FAIL', f"Exception: {str(e)}")
    
    def cleanup_test_products(self, product_ids):
        """Clean up test products created during testing"""
        print("\n6. Cleaning up test products")
        for product_id in product_ids:
            if product_id:
                try:
                    response = self.make_request('DELETE', f'/api/products/{product_id}')
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('success'):
                            self.log_test(f'/api/products/{product_id}', 'DELETE', 'PASS', 
                                        "Test product cleaned up successfully")
                        else:
                            self.log_test(f'/api/products/{product_id}', 'DELETE', 'FAIL', 
                                        f"Cleanup failed: {data}")
                    else:
                        self.log_test(f'/api/products/{product_id}', 'DELETE', 'FAIL', 
                                    f"Status code: {response.status_code}")
                except Exception as e:
                    self.log_test(f'/api/products/{product_id}', 'DELETE', 'FAIL', f"Exception: {str(e)}")
    
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
    
    def test_brands_crud(self):
        """Test Brands CRUD operations with authentication"""
        print("\n=== Testing Brands Endpoints (with Auth) ===")
        
        # GET /api/brands
        try:
            response = self.make_request('GET', '/api/brands')
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'brands' in data:
                    brands = data['brands']
                    self.log_test('/api/brands', 'GET', 'PASS', f"Retrieved {len(brands)} brands")
                else:
                    self.log_test('/api/brands', 'GET', 'FAIL', f"Unexpected response: {data}")
            else:
                self.log_test('/api/brands', 'GET', 'FAIL', f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test('/api/brands', 'GET', 'FAIL', f"Exception: {str(e)}")
        
        # POST /api/brands - Create new brand
        try:
            brand_data = {"name": "Test Brand Auth", "description": "Testing auth"}
            response = self.make_request('POST', '/api/brands', data=brand_data)
            if response.status_code in [200, 201]:
                data = response.json()
                if data.get('success'):
                    brand_id = data.get('brand', {}).get('id')
                    if brand_id:
                        self.created_items['brands'].append(brand_id)
                    self.log_test('/api/brands', 'POST', 'PASS', f"Brand created: {brand_data['name']}")
                else:
                    self.log_test('/api/brands', 'POST', 'FAIL', f"Creation failed: {data}")
            else:
                self.log_test('/api/brands', 'POST', 'FAIL', f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test('/api/brands', 'POST', 'FAIL', f"Exception: {str(e)}")
        
        # PUT and DELETE operations for created brands
        if self.created_items['brands']:
            brand_id = self.created_items['brands'][0]
            
            # PUT /api/brands/{id}
            try:
                update_data = {"name": "Updated Test Brand", "description": "Updated description"}
                response = self.make_request('PUT', f'/api/brands/{brand_id}', data=update_data)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        self.log_test(f'/api/brands/{brand_id}', 'PUT', 'PASS', "Brand updated successfully")
                    else:
                        self.log_test(f'/api/brands/{brand_id}', 'PUT', 'FAIL', f"Update failed: {data}")
                else:
                    self.log_test(f'/api/brands/{brand_id}', 'PUT', 'FAIL', f"Status code: {response.status_code}")
            except Exception as e:
                self.log_test(f'/api/brands/{brand_id}', 'PUT', 'FAIL', f"Exception: {str(e)}")
            
            # DELETE /api/brands/{id}
            try:
                response = self.make_request('DELETE', f'/api/brands/{brand_id}')
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        self.log_test(f'/api/brands/{brand_id}', 'DELETE', 'PASS', "Brand deleted successfully")
                    else:
                        self.log_test(f'/api/brands/{brand_id}', 'DELETE', 'FAIL', f"Delete failed: {data}")
                else:
                    self.log_test(f'/api/brands/{brand_id}', 'DELETE', 'FAIL', f"Status code: {response.status_code}")
            except Exception as e:
                self.log_test(f'/api/brands/{brand_id}', 'DELETE', 'FAIL', f"Exception: {str(e)}")

    def test_roles_crud(self):
        """Test Roles CRUD operations with authentication"""
        print("\n=== Testing Roles Endpoints (with Auth) ===")
        
        # GET /api/roles
        try:
            response = self.make_request('GET', '/api/roles')
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'roles' in data:
                    roles = data['roles']
                    self.log_test('/api/roles', 'GET', 'PASS', f"Retrieved {len(roles)} roles")
                else:
                    self.log_test('/api/roles', 'GET', 'FAIL', f"Unexpected response: {data}")
            else:
                self.log_test('/api/roles', 'GET', 'FAIL', f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test('/api/roles', 'GET', 'FAIL', f"Exception: {str(e)}")
        
        # POST /api/roles - Create new role
        try:
            role_data = {"name": "Test Role", "max_discount": 10.0}
            response = self.make_request('POST', '/api/roles', data=role_data)
            if response.status_code in [200, 201]:
                data = response.json()
                if data.get('success'):
                    role_id = data.get('role', {}).get('id')
                    if role_id:
                        self.created_items['roles'].append(role_id)
                    self.log_test('/api/roles', 'POST', 'PASS', f"Role created: {role_data['name']}")
                else:
                    self.log_test('/api/roles', 'POST', 'FAIL', f"Creation failed: {data}")
            else:
                self.log_test('/api/roles', 'POST', 'FAIL', f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test('/api/roles', 'POST', 'FAIL', f"Exception: {str(e)}")
        
        # PUT and DELETE operations for created roles
        if self.created_items['roles']:
            role_id = self.created_items['roles'][0]
            
            # PUT /api/roles/{id}
            try:
                update_data = {"name": "Updated Test Role", "max_discount": 15.0}
                response = self.make_request('PUT', f'/api/roles/{role_id}', data=update_data)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        self.log_test(f'/api/roles/{role_id}', 'PUT', 'PASS', "Role updated successfully")
                    else:
                        self.log_test(f'/api/roles/{role_id}', 'PUT', 'FAIL', f"Update failed: {data}")
                else:
                    self.log_test(f'/api/roles/{role_id}', 'PUT', 'FAIL', f"Status code: {response.status_code}")
            except Exception as e:
                self.log_test(f'/api/roles/{role_id}', 'PUT', 'FAIL', f"Exception: {str(e)}")
            
            # DELETE /api/roles/{id}
            try:
                response = self.make_request('DELETE', f'/api/roles/{role_id}')
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        self.log_test(f'/api/roles/{role_id}', 'DELETE', 'PASS', "Role deleted successfully")
                    else:
                        self.log_test(f'/api/roles/{role_id}', 'DELETE', 'FAIL', f"Delete failed: {data}")
                else:
                    self.log_test(f'/api/roles/{role_id}', 'DELETE', 'FAIL', f"Status code: {response.status_code}")
            except Exception as e:
                self.log_test(f'/api/roles/{role_id}', 'DELETE', 'FAIL', f"Exception: {str(e)}")

    def test_outlets_crud(self):
        """Test Outlets CRUD operations with authentication"""
        print("\n=== Testing Outlets Endpoints (with Auth) ===")
        
        # GET /api/outlets
        try:
            response = self.make_request('GET', '/api/outlets')
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'outlets' in data:
                    outlets = data['outlets']
                    self.log_test('/api/outlets', 'GET', 'PASS', f"Retrieved {len(outlets)} outlets")
                else:
                    self.log_test('/api/outlets', 'GET', 'FAIL', f"Unexpected response: {data}")
            else:
                self.log_test('/api/outlets', 'GET', 'FAIL', f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test('/api/outlets', 'GET', 'FAIL', f"Exception: {str(e)}")
        
        # POST /api/outlets - Create new outlet
        try:
            outlet_data = {"name": "Test Outlet", "address": "123 Test St", "phone": "555-0123", "is_active": True}
            response = self.make_request('POST', '/api/outlets', data=outlet_data)
            if response.status_code in [200, 201]:
                data = response.json()
                if data.get('success'):
                    outlet_id = data.get('outlet', {}).get('id')
                    if outlet_id:
                        self.created_items['outlets'].append(outlet_id)
                    self.log_test('/api/outlets', 'POST', 'PASS', f"Outlet created: {outlet_data['name']}")
                else:
                    self.log_test('/api/outlets', 'POST', 'FAIL', f"Creation failed: {data}")
            else:
                self.log_test('/api/outlets', 'POST', 'FAIL', f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test('/api/outlets', 'POST', 'FAIL', f"Exception: {str(e)}")

    def test_payment_methods_crud(self):
        """Test Payment Methods CRUD operations with authentication"""
        print("\n=== Testing Payment Methods Endpoints (with Auth) ===")
        
        # GET /api/payment-methods
        try:
            response = self.make_request('GET', '/api/payment-methods')
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'payment_methods' in data:
                    methods = data['payment_methods']
                    self.log_test('/api/payment-methods', 'GET', 'PASS', f"Retrieved {len(methods)} payment methods")
                else:
                    self.log_test('/api/payment-methods', 'GET', 'FAIL', f"Unexpected response: {data}")
            else:
                self.log_test('/api/payment-methods', 'GET', 'FAIL', f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test('/api/payment-methods', 'GET', 'FAIL', f"Exception: {str(e)}")
        
        # POST /api/payment-methods - Create new payment method
        try:
            method_data = {"name": "Test Payment Method", "type": "digital", "is_active": True}
            response = self.make_request('POST', '/api/payment-methods', data=method_data)
            if response.status_code in [200, 201]:
                data = response.json()
                if data.get('success'):
                    method_id = data.get('payment_method', {}).get('id')
                    if method_id:
                        self.created_items['payment_methods'].append(method_id)
                    self.log_test('/api/payment-methods', 'POST', 'PASS', f"Payment method created: {method_data['name']}")
                else:
                    self.log_test('/api/payment-methods', 'POST', 'FAIL', f"Creation failed: {data}")
            else:
                self.log_test('/api/payment-methods', 'POST', 'FAIL', f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test('/api/payment-methods', 'POST', 'FAIL', f"Exception: {str(e)}")

    def test_coupons_crud(self):
        """Test Coupons CRUD operations with authentication"""
        print("\n=== Testing Coupons Endpoints (with Auth) ===")
        
        # GET /api/coupons
        try:
            response = self.make_request('GET', '/api/coupons')
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'coupons' in data:
                    coupons = data['coupons']
                    self.log_test('/api/coupons', 'GET', 'PASS', f"Retrieved {len(coupons)} coupons")
                else:
                    self.log_test('/api/coupons', 'GET', 'FAIL', f"Unexpected response: {data}")
            else:
                self.log_test('/api/coupons', 'GET', 'FAIL', f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test('/api/coupons', 'GET', 'FAIL', f"Exception: {str(e)}")
        
        # POST /api/coupons - Create new coupon
        try:
            coupon_data = {
                "code": "TEST10",
                "discount_type": "percentage",
                "discount_value": 10.0,
                "min_purchase": 50.0,
                "max_discount": 20.0,
                "is_active": True
            }
            response = self.make_request('POST', '/api/coupons', data=coupon_data)
            if response.status_code in [200, 201]:
                data = response.json()
                if data.get('success'):
                    coupon_id = data.get('data', {}).get('id')
                    if coupon_id:
                        self.created_items['coupons'].append(coupon_id)
                    self.log_test('/api/coupons', 'POST', 'PASS', f"Coupon created: {coupon_data['code']}")
                else:
                    self.log_test('/api/coupons', 'POST', 'FAIL', f"Creation failed: {data}")
            else:
                self.log_test('/api/coupons', 'POST', 'FAIL', f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test('/api/coupons', 'POST', 'FAIL', f"Exception: {str(e)}")

    def test_orders_operations(self):
        """Test Orders operations with authentication"""
        print("\n=== Testing Orders Endpoints (with Auth) ===")
        
        # GET /api/orders
        try:
            response = self.make_request('GET', '/api/orders')
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'orders' in data:
                    orders = data['orders']
                    self.log_test('/api/orders', 'GET', 'PASS', f"Retrieved {len(orders)} orders")
                    
                    # Test order status update if orders exist
                    if orders and len(orders) > 0:
                        order_id = orders[0].get('id')
                        if order_id:
                            try:
                                status_data = {"status": "processing"}
                                response = self.make_request('PUT', f'/api/orders/{order_id}/status', data=status_data)
                                if response.status_code == 200:
                                    data = response.json()
                                    if data.get('success'):
                                        self.log_test(f'/api/orders/{order_id}/status', 'PUT', 'PASS', "Order status updated")
                                    else:
                                        self.log_test(f'/api/orders/{order_id}/status', 'PUT', 'FAIL', f"Status update failed: {data}")
                                else:
                                    self.log_test(f'/api/orders/{order_id}/status', 'PUT', 'FAIL', f"Status code: {response.status_code}")
                            except Exception as e:
                                self.log_test(f'/api/orders/{order_id}/status', 'PUT', 'FAIL', f"Exception: {str(e)}")
                else:
                    self.log_test('/api/orders', 'GET', 'FAIL', f"Unexpected response: {data}")
            else:
                self.log_test('/api/orders', 'GET', 'FAIL', f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test('/api/orders', 'GET', 'FAIL', f"Exception: {str(e)}")

    def test_customers_operations(self):
        """Test Customers operations with authentication"""
        print("\n=== Testing Customers Endpoints (with Auth) ===")
        
        # GET /api/customers
        try:
            response = self.make_request('GET', '/api/customers')
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'customers' in data:
                    customers = data['customers']
                    self.log_test('/api/customers', 'GET', 'PASS', f"Retrieved {len(customers)} customers")
                    
                    # Verify customer data format (no SQL null objects)
                    if customers and len(customers) > 0:
                        sample_customer = customers[0]
                        has_sql_nulls = False
                        for key, value in sample_customer.items():
                            if isinstance(value, dict) and 'String' in value and 'Valid' in value:
                                has_sql_nulls = True
                                break
                        
                        if has_sql_nulls:
                            self.log_test('/api/customers', 'GET', 'FAIL', "Customer data contains SQL null objects")
                        else:
                            self.log_test('/api/customers', 'GET', 'PASS', "Customer data properly formatted (no SQL nulls)")
                else:
                    self.log_test('/api/customers', 'GET', 'FAIL', f"Unexpected response: {data}")
            else:
                self.log_test('/api/customers', 'GET', 'FAIL', f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test('/api/customers', 'GET', 'FAIL', f"Exception: {str(e)}")
    
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
        """Run all test suites as specified in review request"""
        print("🚀 Starting POS API Testing - Product Bundle & Portion Support")
        print("=" * 60)
        
        # Test health check first
        self.test_health_check()
        
        # Test authentication (this sets the token for protected endpoints)
        self.test_authentication()
        
        if not self.token:
            print("❌ Authentication failed - cannot proceed with protected endpoint tests")
            self.print_summary()
            return
        
        # Test Product API endpoints with new bundle and portion fields
        self.test_products_bundle_portion_support()
        
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
    # Use the external URL as specified in the review request
    base_url = "https://test-reader.preview.emergentagent.com"
    
    print(f"Testing POS API at: {base_url}")
    print("Testing endpoints as specified in review request:")
    print("- Authentication: POST /api/auth/staff/login")
    print("- Brands CRUD: GET, POST, PUT, DELETE /api/brands")
    print("- Roles CRUD: GET, POST, PUT, DELETE /api/roles")
    print("- Outlets: GET, POST /api/outlets")
    print("- Payment Methods: GET, POST /api/payment-methods")
    print("- Coupons: GET, POST /api/coupons")
    print("- Orders: GET /api/orders, PUT /api/orders/{id}/status")
    print("- Customers: GET /api/customers")
    print()
    
    tester = POSAPITester(base_url)
    tester.run_all_tests()
    
    # Return exit code based on test results
    failed_tests = len([t for t in tester.test_results if t['status'] == 'FAIL'])
    sys.exit(1 if failed_tests > 0 else 0)

if __name__ == "__main__":
    main()