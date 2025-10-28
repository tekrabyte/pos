from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import aiomysql
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MySQL connection pool
db_pool = None

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Database connection
async def get_db():
    global db_pool
    if db_pool is None:
        db_pool = await aiomysql.create_pool(
            host=os.environ.get('MYSQL_HOST', 'localhost'),
            port=int(os.environ.get('MYSQL_PORT', 3306)),
            user=os.environ.get('MYSQL_USER', 'root'),
            password=os.environ.get('MYSQL_PASSWORD', ''),
            db=os.environ.get('MYSQL_DB', 'pos_db'),
            autocommit=False,
            minsize=5,
            maxsize=20
        )
    return db_pool

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    user: Optional[dict] = None
    message: Optional[str] = None

class Product(BaseModel):
    id: Optional[int] = None
    name: str
    sku: str
    price: float
    stock: int
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Category(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    created_at: Optional[datetime] = None

class Brand(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    created_at: Optional[datetime] = None

class Customer(BaseModel):
    id: Optional[int] = None
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: Optional[datetime] = None

class Order(BaseModel):
    id: Optional[int] = None
    order_number: str
    customer_id: Optional[int] = None
    outlet_id: Optional[int] = None
    user_id: Optional[int] = None
    total_amount: float
    payment_method: str
    status: str = "pending"
    created_at: Optional[datetime] = None

class OrderItem(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    price: float
    subtotal: float

class CreateOrderRequest(BaseModel):
    customer_id: Optional[int] = None
    outlet_id: int
    user_id: int
    items: List[OrderItem]
    payment_method: str
    total_amount: float

class Outlet(BaseModel):
    id: Optional[int] = None
    name: str
    address: str
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    is_main: bool = False
    created_at: Optional[datetime] = None

class Role(BaseModel):
    id: Optional[int] = None
    name: str
    max_discount: float = 0.0
    created_at: Optional[datetime] = None

class PaymentMethod(BaseModel):
    id: Optional[int] = None
    name: str
    type: str
    is_active: bool = True
    config: Optional[dict] = None
    created_at: Optional[datetime] = None

class Coupon(BaseModel):
    id: Optional[int] = None
    code: str
    discount_type: str
    discount_value: float
    min_purchase: Optional[float] = None
    max_discount: Optional[float] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

# Helper function to convert row to dict
def row_to_dict(row, cursor):
    if row is None:
        return None
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))

def rows_to_dict(rows, cursor):
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in rows]

# Initialize database
@app.on_event("startup")
async def startup():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Create tables
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    email VARCHAR(255),
                    full_name VARCHAR(255),
                    role_id INT,
                    outlet_id INT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS roles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    max_discount DECIMAL(5,2) DEFAULT 0.00,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS outlets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    address TEXT,
                    city VARCHAR(100),
                    country VARCHAR(100),
                    postal_code VARCHAR(20),
                    is_main BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    parent_id INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES categories(id)
                )
            ''')
            
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS brands (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    logo_url VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    sku VARCHAR(100) UNIQUE NOT NULL,
                    price DECIMAL(12,2) NOT NULL,
                    stock INT DEFAULT 0,
                    category_id INT,
                    brand_id INT,
                    description TEXT,
                    image_url VARCHAR(500),
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories(id),
                    FOREIGN KEY (brand_id) REFERENCES brands(id)
                )
            ''')
            
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255),
                    phone VARCHAR(50),
                    address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    order_number VARCHAR(100) UNIQUE NOT NULL,
                    customer_id INT,
                    outlet_id INT,
                    user_id INT,
                    total_amount DECIMAL(12,2) NOT NULL,
                    payment_method VARCHAR(100),
                    status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(id),
                    FOREIGN KEY (outlet_id) REFERENCES outlets(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS order_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    order_id INT,
                    product_id INT,
                    product_name VARCHAR(255),
                    quantity INT NOT NULL,
                    price DECIMAL(12,2) NOT NULL,
                    subtotal DECIMAL(12,2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            ''')
            
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS payment_methods (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    config JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS coupons (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    code VARCHAR(100) UNIQUE NOT NULL,
                    discount_type VARCHAR(50) NOT NULL,
                    discount_value DECIMAL(12,2) NOT NULL,
                    min_purchase DECIMAL(12,2),
                    max_discount DECIMAL(12,2),
                    valid_from TIMESTAMP,
                    valid_until TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await conn.commit()
            
            # Insert default data
            await cursor.execute('SELECT COUNT(*) FROM users WHERE username = %s', ('admin',))
            admin_exists = (await cursor.fetchone())[0]
            if admin_exists == 0:
                await cursor.execute(
                    'INSERT INTO users (username, password, full_name, is_active) VALUES (%s, %s, %s, %s)',
                    ('admin', 'admin123', 'Administrator', True)
                )
            
            await cursor.execute('SELECT COUNT(*) FROM roles')
            role_exists = (await cursor.fetchone())[0]
            if role_exists == 0:
                await cursor.execute(
                    'INSERT INTO roles (name, max_discount) VALUES (%s, %s)',
                    ('Administrator', 100.00)
                )
                await cursor.execute(
                    'INSERT INTO roles (name, max_discount) VALUES (%s, %s)',
                    ('Cashier', 10.00)
                )
                await cursor.execute(
                    'INSERT INTO roles (name, max_discount) VALUES (%s, %s)',
                    ('Manager', 50.00)
                )
            
            await cursor.execute('SELECT COUNT(*) FROM outlets')
            outlet_exists = (await cursor.fetchone())[0]
            if outlet_exists == 0:
                await cursor.execute(
                    'INSERT INTO outlets (name, address, city, country, is_main) VALUES (%s, %s, %s, %s, %s)',
                    ('Main Store', 'Jl. Utama No. 1', 'Jakarta', 'Indonesia', True)
                )
            
            await conn.commit()

# Auth endpoints
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'SELECT id, username, email, full_name, role_id, outlet_id FROM users WHERE username = %s AND password = %s AND is_active = TRUE',
                (request.username, request.password)
            )
            user = await cursor.fetchone()
            
            if user:
                user_dict = row_to_dict(user, cursor)
                return LoginResponse(
                    success=True,
                    user=user_dict
                )
            else:
                return LoginResponse(success=False, message="Invalid credentials")

@api_router.post("/auth/register-customer")
async def register_customer(customer: Customer):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Check if email already exists
            if customer.email:
                await cursor.execute('SELECT COUNT(*) FROM customers WHERE email = %s', (customer.email,))
                exists = (await cursor.fetchone())[0]
                if exists > 0:
                    raise HTTPException(status_code=400, detail="Email already registered")
            
            await cursor.execute(
                'INSERT INTO customers (name, email, phone, address) VALUES (%s, %s, %s, %s)',
                (customer.name, customer.email, customer.phone, customer.address)
            )
            customer_id = cursor.lastrowid
            await conn.commit()
            
            await cursor.execute('SELECT * FROM customers WHERE id = %s', (customer_id,))
            result = await cursor.fetchone()
            return {"success": True, "customer": row_to_dict(result, cursor)}

# Product endpoints
@api_router.get("/products")
async def get_products(limit: int = 100, offset: int = 0):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''
                SELECT p.*, c.name as category_name, b.name as brand_name
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN brands b ON p.brand_id = b.id
                ORDER BY p.id DESC
                LIMIT %s OFFSET %s
            ''', (limit, offset))
            products = await cursor.fetchall()
            return rows_to_dict(products, cursor)

@api_router.get("/products/{product_id}")
async def get_product(product_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''
                SELECT p.*, c.name as category_name, b.name as brand_name
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN brands b ON p.brand_id = b.id
                WHERE p.id = %s
            ''', (product_id,))
            product = await cursor.fetchone()
            
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            
            return row_to_dict(product, cursor)

@api_router.post("/products")
async def create_product(product: Product):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''
                INSERT INTO products (name, sku, price, stock, category_id, brand_id, description, image_url, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (product.name, product.sku, product.price, product.stock, product.category_id, 
               product.brand_id, product.description, product.image_url, product.status))
            
            product_id = cursor.lastrowid
            await conn.commit()
            
            await cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.put("/products/{product_id}")
async def update_product(product_id: int, product: Product):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''
                UPDATE products 
                SET name = %s, sku = %s, price = %s, stock = %s, category_id = %s, 
                    brand_id = %s, description = %s, image_url = %s, status = %s
                WHERE id = %s
            ''', (product.name, product.sku, product.price, product.stock, product.category_id,
               product.brand_id, product.description, product.image_url, product.status, product_id))
            
            await conn.commit()
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Product not found")
            
            await cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('DELETE FROM products WHERE id = %s', (product_id,))
            await conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Product not found")
            return {"success": True, "message": "Product deleted"}

# Category endpoints
@api_router.get("/categories")
async def get_categories():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM categories ORDER BY id DESC')
            categories = await cursor.fetchall()
            return rows_to_dict(categories, cursor)

@api_router.post("/categories")
async def create_category(category: Category):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'INSERT INTO categories (name, description, parent_id) VALUES (%s, %s, %s)',
                (category.name, category.description, category.parent_id)
            )
            category_id = cursor.lastrowid
            await conn.commit()
            
            await cursor.execute('SELECT * FROM categories WHERE id = %s', (category_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.put("/categories/{category_id}")
async def update_category(category_id: int, category: Category):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'UPDATE categories SET name = %s, description = %s, parent_id = %s WHERE id = %s',
                (category.name, category.description, category.parent_id, category_id)
            )
            await conn.commit()
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Category not found")
            
            await cursor.execute('SELECT * FROM categories WHERE id = %s', (category_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.delete("/categories/{category_id}")
async def delete_category(category_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('DELETE FROM categories WHERE id = %s', (category_id,))
            await conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Category not found")
            return {"success": True, "message": "Category deleted"}

# Brand endpoints
@api_router.get("/brands")
async def get_brands():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM brands ORDER BY id DESC')
            brands = await cursor.fetchall()
            return rows_to_dict(brands, cursor)

@api_router.post("/brands")
async def create_brand(brand: Brand):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'INSERT INTO brands (name, description, logo_url) VALUES (%s, %s, %s)',
                (brand.name, brand.description, brand.logo_url)
            )
            brand_id = cursor.lastrowid
            await conn.commit()
            
            await cursor.execute('SELECT * FROM brands WHERE id = %s', (brand_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.put("/brands/{brand_id}")
async def update_brand(brand_id: int, brand: Brand):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'UPDATE brands SET name = %s, description = %s, logo_url = %s WHERE id = %s',
                (brand.name, brand.description, brand.logo_url, brand_id)
            )
            await conn.commit()
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Brand not found")
            
            await cursor.execute('SELECT * FROM brands WHERE id = %s', (brand_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.delete("/brands/{brand_id}")
async def delete_brand(brand_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('DELETE FROM brands WHERE id = %s', (brand_id,))
            await conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Brand not found")
            return {"success": True, "message": "Brand deleted"}

# Customer endpoints
@api_router.get("/customers")
async def get_customers():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM customers ORDER BY id DESC')
            customers = await cursor.fetchall()
            return rows_to_dict(customers, cursor)

@api_router.post("/customers")
async def create_customer(customer: Customer):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'INSERT INTO customers (name, email, phone, address) VALUES (%s, %s, %s, %s)',
                (customer.name, customer.email, customer.phone, customer.address)
            )
            customer_id = cursor.lastrowid
            await conn.commit()
            
            await cursor.execute('SELECT * FROM customers WHERE id = %s', (customer_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.put("/customers/{customer_id}")
async def update_customer(customer_id: int, customer: Customer):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'UPDATE customers SET name = %s, email = %s, phone = %s, address = %s WHERE id = %s',
                (customer.name, customer.email, customer.phone, customer.address, customer_id)
            )
            await conn.commit()
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Customer not found")
            
            await cursor.execute('SELECT * FROM customers WHERE id = %s', (customer_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('DELETE FROM customers WHERE id = %s', (customer_id,))
            await conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Customer not found")
            return {"success": True, "message": "Customer deleted"}

# Order endpoints
@api_router.get("/orders")
async def get_orders():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''
                SELECT o.*, c.name as customer_name, ou.name as outlet_name, u.username as user_name
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                LEFT JOIN outlets ou ON o.outlet_id = ou.id
                LEFT JOIN users u ON o.user_id = u.id
                ORDER BY o.id DESC
            ''')
            orders = await cursor.fetchall()
            return rows_to_dict(orders, cursor)

@api_router.get("/orders/{order_id}")
async def get_order(order_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''
                SELECT o.*, c.name as customer_name, ou.name as outlet_name, u.username as user_name
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                LEFT JOIN outlets ou ON o.outlet_id = ou.id
                LEFT JOIN users u ON o.user_id = u.id
                WHERE o.id = %s
            ''', (order_id,))
            order = await cursor.fetchone()
            
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            await cursor.execute('SELECT * FROM order_items WHERE order_id = %s', (order_id,))
            items = await cursor.fetchall()
            
            return {
                **row_to_dict(order, cursor),
                "items": rows_to_dict(items, cursor)
            }

@api_router.post("/orders")
async def create_order(order_req: CreateOrderRequest):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Generate order number
            import random
            order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            
            # Create order
            try:
                await cursor.execute('''
                    INSERT INTO orders (order_number, customer_id, outlet_id, user_id, total_amount, payment_method, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (order_number, order_req.customer_id, order_req.outlet_id, order_req.user_id, 
                   order_req.total_amount, order_req.payment_method, 'completed'))
                
                order_id = cursor.lastrowid
                
                # Create order items and update stock
                for item in order_req.items:
                    await cursor.execute('''
                        INSERT INTO order_items (order_id, product_id, product_name, quantity, price, subtotal)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (order_id, item.product_id, item.product_name, item.quantity, item.price, item.subtotal))
                    
                    # Update stock
                    await cursor.execute(
                        'UPDATE products SET stock = stock - %s WHERE id = %s',
                        (item.quantity, item.product_id)
                    )
                
                await conn.commit()
                
                await cursor.execute('SELECT * FROM orders WHERE id = %s', (order_id,))
                order = await cursor.fetchone()
                return row_to_dict(order, cursor)
            except Exception as e:
                await conn.rollback()
                raise HTTPException(status_code=500, detail=str(e))

# Outlet endpoints
@api_router.get("/outlets")
async def get_outlets():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM outlets ORDER BY id DESC')
            outlets = await cursor.fetchall()
            return rows_to_dict(outlets, cursor)

@api_router.post("/outlets")
async def create_outlet(outlet: Outlet):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'INSERT INTO outlets (name, address, city, country, postal_code, is_main) VALUES (%s, %s, %s, %s, %s, %s)',
                (outlet.name, outlet.address, outlet.city, outlet.country, outlet.postal_code, outlet.is_main)
            )
            outlet_id = cursor.lastrowid
            await conn.commit()
            
            await cursor.execute('SELECT * FROM outlets WHERE id = %s', (outlet_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

# Role endpoints
@api_router.get("/roles")
async def get_roles():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM roles ORDER BY id DESC')
            roles = await cursor.fetchall()
            return rows_to_dict(roles, cursor)

@api_router.post("/roles")
async def create_role(role: Role):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'INSERT INTO roles (name, max_discount) VALUES (%s, %s)',
                (role.name, role.max_discount)
            )
            role_id = cursor.lastrowid
            await conn.commit()
            
            await cursor.execute('SELECT * FROM roles WHERE id = %s', (role_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

# Payment method endpoints
@api_router.get("/payment-methods")
async def get_payment_methods():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM payment_methods WHERE is_active = TRUE ORDER BY id')
            methods = await cursor.fetchall()
            return rows_to_dict(methods, cursor)

@api_router.post("/payment-methods")
async def create_payment_method(method: PaymentMethod):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            config_json = json.dumps(method.config) if method.config else None
            await cursor.execute(
                'INSERT INTO payment_methods (name, type, is_active, config) VALUES (%s, %s, %s, %s)',
                (method.name, method.type, method.is_active, config_json)
            )
            method_id = cursor.lastrowid
            await conn.commit()
            
            await cursor.execute('SELECT * FROM payment_methods WHERE id = %s', (method_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

# Coupon endpoints
@api_router.get("/coupons")
async def get_coupons():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM coupons ORDER BY id DESC')
            coupons = await cursor.fetchall()
            return rows_to_dict(coupons, cursor)

@api_router.post("/coupons")
async def create_coupon(coupon: Coupon):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''
                INSERT INTO coupons (code, discount_type, discount_value, min_purchase, max_discount, valid_from, valid_until, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (coupon.code, coupon.discount_type, coupon.discount_value, coupon.min_purchase,
               coupon.max_discount, coupon.valid_from, coupon.valid_until, coupon.is_active))
            coupon_id = cursor.lastrowid
            await conn.commit()
            
            await cursor.execute('SELECT * FROM coupons WHERE id = %s', (coupon_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

# Analytics endpoints
@api_router.get("/analytics/overview")
async def get_analytics_overview():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status = %s', ('completed',))
            total_revenue = (await cursor.fetchone())[0]
            
            await cursor.execute('SELECT COUNT(*) FROM orders')
            total_orders = (await cursor.fetchone())[0]
            
            await cursor.execute('SELECT COUNT(*) FROM products')
            total_products = (await cursor.fetchone())[0]
            
            await cursor.execute('SELECT COUNT(*) FROM customers')
            total_customers = (await cursor.fetchone())[0]
            
            # Recent orders
            await cursor.execute('''
                SELECT o.*, c.name as customer_name
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                ORDER BY o.created_at DESC
                LIMIT 10
            ''')
            recent_orders = await cursor.fetchall()
            recent_orders_list = rows_to_dict(recent_orders, cursor)
            
            # Top products
            await cursor.execute('''
                SELECT p.name, SUM(oi.quantity) as total_sold, SUM(oi.subtotal) as total_revenue
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                GROUP BY p.id, p.name
                ORDER BY total_sold DESC
                LIMIT 10
            ''')
            top_products = await cursor.fetchall()
            top_products_list = rows_to_dict(top_products, cursor)
            
            return {
                "total_revenue": float(total_revenue),
                "total_orders": total_orders,
                "total_products": total_products,
                "total_customers": total_customers,
                "recent_orders": recent_orders_list,
                "top_products": top_products_list
            }

# QRIS endpoint with QR Code
@api_router.post("/qris/generate")
async def generate_qris(request: dict):
    import qrcode
    import io
    import base64
    
    amount = request.get('amount', 0)
    product_name = request.get('product_name', 'Product')
    merchant_id = request.get('merchant_id', 'ID1234567890')
    
    # Generate QRIS string (simplified format - dalam produksi gunakan QRIS standard)
    # Format: 00020101021226660014ID.CO.QRIS.WWW0118[merchant_id]0215[merchant_name]520454995802ID5913[merchant_name]6007Jakarta610512340704[amount]6304[checksum]
    qris_string = f"00020101021226660014ID.CO.QRIS.WWW0118{merchant_id}0215POSMERCHANT520454995802ID5913POS Merchant6007Jakarta610512340704{int(amount)}6304ABCD"
    
    # Generate QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qris_string)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return {
        "success": True,
        "qris_string": qris_string,
        "qr_code_image": f"data:image/png;base64,{qr_code_base64}",
        "amount": amount,
        "product_name": product_name,
        "merchant_id": merchant_id,
        "expired_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
    }

# Add timedelta import at top
from datetime import timedelta

@api_router.get("/")
async def root():
    return {"message": "POS API is running", "version": "1.0.0"}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown():
    global db_pool
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()
