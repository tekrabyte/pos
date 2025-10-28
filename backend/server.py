from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import asyncpg
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# PostgreSQL connection pool
db_pool = None

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Database connection
async def get_db():
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            host=os.environ.get('POSTGRES_HOST', 'localhost'),
            port=int(os.environ.get('POSTGRES_PORT', 5432)),
            user=os.environ.get('POSTGRES_USER', 'postgres'),
            password=os.environ.get('POSTGRES_PASSWORD', 'postgres'),
            database=os.environ.get('POSTGRES_DB', 'pos_db'),
            min_size=5,
            max_size=20
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

# Initialize database
@app.on_event("startup")
async def startup():
    pool = await get_db()
    async with pool.acquire() as conn:
        # Create tables
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                full_name VARCHAR(255),
                role_id INTEGER,
                outlet_id INTEGER,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                max_discount DECIMAL(5,2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS outlets (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                address TEXT,
                city VARCHAR(100),
                country VARCHAR(100),
                postal_code VARCHAR(20),
                is_main BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                parent_id INTEGER REFERENCES categories(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS brands (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                logo_url VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                sku VARCHAR(100) UNIQUE NOT NULL,
                price DECIMAL(12,2) NOT NULL,
                stock INTEGER DEFAULT 0,
                category_id INTEGER REFERENCES categories(id),
                brand_id INTEGER REFERENCES brands(id),
                description TEXT,
                image_url VARCHAR(500),
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                phone VARCHAR(50),
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                order_number VARCHAR(100) UNIQUE NOT NULL,
                customer_id INTEGER REFERENCES customers(id),
                outlet_id INTEGER REFERENCES outlets(id),
                user_id INTEGER REFERENCES users(id),
                total_amount DECIMAL(12,2) NOT NULL,
                payment_method VARCHAR(100),
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
                product_id INTEGER REFERENCES products(id),
                product_name VARCHAR(255),
                quantity INTEGER NOT NULL,
                price DECIMAL(12,2) NOT NULL,
                subtotal DECIMAL(12,2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS payment_methods (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                type VARCHAR(50) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                config JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS coupons (
                id SERIAL PRIMARY KEY,
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
        
        # Insert default data
        # Check if admin user exists
        admin_exists = await conn.fetchval('SELECT COUNT(*) FROM users WHERE username = $1', 'admin')
        if admin_exists == 0:
            await conn.execute(
                'INSERT INTO users (username, password, full_name, is_active) VALUES ($1, $2, $3, $4)',
                'admin', 'admin123', 'Administrator', True
            )
        
        # Check if default role exists
        role_exists = await conn.fetchval('SELECT COUNT(*) FROM roles')
        if role_exists == 0:
            await conn.execute(
                'INSERT INTO roles (name, max_discount) VALUES ($1, $2), ($3, $4), ($5, $6)',
                'Administrator', 100.00, 'Cashier', 10.00, 'Manager', 50.00
            )
        
        # Check if default outlet exists
        outlet_exists = await conn.fetchval('SELECT COUNT(*) FROM outlets')
        if outlet_exists == 0:
            await conn.execute(
                'INSERT INTO outlets (name, address, city, country, is_main) VALUES ($1, $2, $3, $4, $5)',
                'Main Store', 'Jl. Utama No. 1', 'Jakarta', 'Indonesia', True
            )

# Auth endpoints
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    pool = await get_db()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            'SELECT id, username, email, full_name, role_id, outlet_id FROM users WHERE username = $1 AND password = $2 AND is_active = TRUE',
            request.username, request.password
        )
        
        if user:
            return LoginResponse(
                success=True,
                user={
                    "id": user['id'],
                    "username": user['username'],
                    "email": user['email'],
                    "full_name": user['full_name'],
                    "role_id": user['role_id'],
                    "outlet_id": user['outlet_id']
                }
            )
        else:
            return LoginResponse(success=False, message="Invalid credentials")

# Product endpoints
@api_router.get("/products")
async def get_products(limit: int = 100, offset: int = 0):
    pool = await get_db()
    async with pool.acquire() as conn:
        products = await conn.fetch('''
            SELECT p.*, c.name as category_name, b.name as brand_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN brands b ON p.brand_id = b.id
            ORDER BY p.id DESC
            LIMIT $1 OFFSET $2
        ''', limit, offset)
        
        return [{**dict(p)} for p in products]

@api_router.get("/products/{product_id}")
async def get_product(product_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        product = await conn.fetchrow('''
            SELECT p.*, c.name as category_name, b.name as brand_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN brands b ON p.brand_id = b.id
            WHERE p.id = $1
        ''', product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return dict(product)

@api_router.post("/products")
async def create_product(product: Product):
    pool = await get_db()
    async with pool.acquire() as conn:
        result = await conn.fetchrow('''
            INSERT INTO products (name, sku, price, stock, category_id, brand_id, description, image_url, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id, name, sku, price, stock, category_id, brand_id, description, image_url, status, created_at, updated_at
        ''', product.name, product.sku, product.price, product.stock, product.category_id, 
           product.brand_id, product.description, product.image_url, product.status)
        
        return dict(result)

@api_router.put("/products/{product_id}")
async def update_product(product_id: int, product: Product):
    pool = await get_db()
    async with pool.acquire() as conn:
        result = await conn.fetchrow('''
            UPDATE products 
            SET name = $1, sku = $2, price = $3, stock = $4, category_id = $5, 
                brand_id = $6, description = $7, image_url = $8, status = $9, updated_at = CURRENT_TIMESTAMP
            WHERE id = $10
            RETURNING id, name, sku, price, stock, category_id, brand_id, description, image_url, status, created_at, updated_at
        ''', product.name, product.sku, product.price, product.stock, product.category_id,
           product.brand_id, product.description, product.image_url, product.status, product_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return dict(result)

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        result = await conn.execute('DELETE FROM products WHERE id = $1', product_id)
        if result == 'DELETE 0':
            raise HTTPException(status_code=404, detail="Product not found")
        return {"success": True, "message": "Product deleted"}

# Category endpoints
@api_router.get("/categories")
async def get_categories():
    pool = await get_db()
    async with pool.acquire() as conn:
        categories = await conn.fetch('SELECT * FROM categories ORDER BY id DESC')
        return [{**dict(c)} for c in categories]

@api_router.post("/categories")
async def create_category(category: Category):
    pool = await get_db()
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            'INSERT INTO categories (name, description, parent_id) VALUES ($1, $2, $3) RETURNING *',
            category.name, category.description, category.parent_id
        )
        return dict(result)

@api_router.put("/categories/{category_id}")
async def update_category(category_id: int, category: Category):
    pool = await get_db()
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            'UPDATE categories SET name = $1, description = $2, parent_id = $3 WHERE id = $4 RETURNING *',
            category.name, category.description, category.parent_id, category_id
        )
        if not result:
            raise HTTPException(status_code=404, detail="Category not found")
        return dict(result)

@api_router.delete("/categories/{category_id}")
async def delete_category(category_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        result = await conn.execute('DELETE FROM categories WHERE id = $1', category_id)
        if result == 'DELETE 0':
            raise HTTPException(status_code=404, detail="Category not found")
        return {"success": True, "message": "Category deleted"}

# Brand endpoints
@api_router.get("/brands")
async def get_brands():
    pool = await get_db()
    async with pool.acquire() as conn:
        brands = await conn.fetch('SELECT * FROM brands ORDER BY id DESC')
        return [{**dict(b)} for b in brands]

@api_router.post("/brands")
async def create_brand(brand: Brand):
    pool = await get_db()
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            'INSERT INTO brands (name, description, logo_url) VALUES ($1, $2, $3) RETURNING *',
            brand.name, brand.description, brand.logo_url
        )
        return dict(result)

@api_router.put("/brands/{brand_id}")
async def update_brand(brand_id: int, brand: Brand):
    pool = await get_db()
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            'UPDATE brands SET name = $1, description = $2, logo_url = $3 WHERE id = $4 RETURNING *',
            brand.name, brand.description, brand.logo_url, brand_id
        )
        if not result:
            raise HTTPException(status_code=404, detail="Brand not found")
        return dict(result)

@api_router.delete("/brands/{brand_id}")
async def delete_brand(brand_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        result = await conn.execute('DELETE FROM brands WHERE id = $1', brand_id)
        if result == 'DELETE 0':
            raise HTTPException(status_code=404, detail="Brand not found")
        return {"success": True, "message": "Brand deleted"}

# Customer endpoints
@api_router.get("/customers")
async def get_customers():
    pool = await get_db()
    async with pool.acquire() as conn:
        customers = await conn.fetch('SELECT * FROM customers ORDER BY id DESC')
        return [{**dict(c)} for c in customers]

@api_router.post("/customers")
async def create_customer(customer: Customer):
    pool = await get_db()
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            'INSERT INTO customers (name, email, phone, address) VALUES ($1, $2, $3, $4) RETURNING *',
            customer.name, customer.email, customer.phone, customer.address
        )
        return dict(result)

@api_router.put("/customers/{customer_id}")
async def update_customer(customer_id: int, customer: Customer):
    pool = await get_db()
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            'UPDATE customers SET name = $1, email = $2, phone = $3, address = $4 WHERE id = $5 RETURNING *',
            customer.name, customer.email, customer.phone, customer.address, customer_id
        )
        if not result:
            raise HTTPException(status_code=404, detail="Customer not found")
        return dict(result)

@api_router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        result = await conn.execute('DELETE FROM customers WHERE id = $1', customer_id)
        if result == 'DELETE 0':
            raise HTTPException(status_code=404, detail="Customer not found")
        return {"success": True, "message": "Customer deleted"}

# Order endpoints
@api_router.get("/orders")
async def get_orders():
    pool = await get_db()
    async with pool.acquire() as conn:
        orders = await conn.fetch('''
            SELECT o.*, c.name as customer_name, ou.name as outlet_name, u.username as user_name
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            LEFT JOIN outlets ou ON o.outlet_id = ou.id
            LEFT JOIN users u ON o.user_id = u.id
            ORDER BY o.id DESC
        ''')
        return [{**dict(o)} for o in orders]

@api_router.get("/orders/{order_id}")
async def get_order(order_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        order = await conn.fetchrow('''
            SELECT o.*, c.name as customer_name, ou.name as outlet_name, u.username as user_name
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            LEFT JOIN outlets ou ON o.outlet_id = ou.id
            LEFT JOIN users u ON o.user_id = u.id
            WHERE o.id = $1
        ''', order_id)
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        items = await conn.fetch('SELECT * FROM order_items WHERE order_id = $1', order_id)
        
        return {
            **dict(order),
            "items": [{**dict(i)} for i in items]
        }

@api_router.post("/orders")
async def create_order(order_req: CreateOrderRequest):
    pool = await get_db()
    async with pool.acquire() as conn:
        # Generate order number
        import random
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        
        # Create order
        async with conn.transaction():
            order = await conn.fetchrow('''
                INSERT INTO orders (order_number, customer_id, outlet_id, user_id, total_amount, payment_method, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
            ''', order_number, order_req.customer_id, order_req.outlet_id, order_req.user_id, 
               order_req.total_amount, order_req.payment_method, 'completed')
            
            # Create order items and update stock
            for item in order_req.items:
                await conn.execute('''
                    INSERT INTO order_items (order_id, product_id, product_name, quantity, price, subtotal)
                    VALUES ($1, $2, $3, $4, $5, $6)
                ''', order['id'], item.product_id, item.product_name, item.quantity, item.price, item.subtotal)
                
                # Update stock
                await conn.execute(
                    'UPDATE products SET stock = stock - $1 WHERE id = $2',
                    item.quantity, item.product_id
                )
            
            return dict(order)

# Outlet endpoints
@api_router.get("/outlets")
async def get_outlets():
    pool = await get_db()
    async with pool.acquire() as conn:
        outlets = await conn.fetch('SELECT * FROM outlets ORDER BY id DESC')
        return [{**dict(o)} for o in outlets]

@api_router.post("/outlets")
async def create_outlet(outlet: Outlet):
    pool = await get_db()
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            'INSERT INTO outlets (name, address, city, country, postal_code, is_main) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *',
            outlet.name, outlet.address, outlet.city, outlet.country, outlet.postal_code, outlet.is_main
        )
        return dict(result)

# Role endpoints
@api_router.get("/roles")
async def get_roles():
    pool = await get_db()
    async with pool.acquire() as conn:
        roles = await conn.fetch('SELECT * FROM roles ORDER BY id DESC')
        return [{**dict(r)} for r in roles]

@api_router.post("/roles")
async def create_role(role: Role):
    pool = await get_db()
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            'INSERT INTO roles (name, max_discount) VALUES ($1, $2) RETURNING *',
            role.name, role.max_discount
        )
        return dict(result)

# Payment method endpoints
@api_router.get("/payment-methods")
async def get_payment_methods():
    pool = await get_db()
    async with pool.acquire() as conn:
        methods = await conn.fetch('SELECT * FROM payment_methods WHERE is_active = TRUE ORDER BY id')
        return [{**dict(m)} for m in methods]

@api_router.post("/payment-methods")
async def create_payment_method(method: PaymentMethod):
    pool = await get_db()
    async with pool.acquire() as conn:
        config_json = json.dumps(method.config) if method.config else None
        result = await conn.fetchrow(
            'INSERT INTO payment_methods (name, type, is_active, config) VALUES ($1, $2, $3, $4) RETURNING *',
            method.name, method.type, method.is_active, config_json
        )
        return dict(result)

# Coupon endpoints
@api_router.get("/coupons")
async def get_coupons():
    pool = await get_db()
    async with pool.acquire() as conn:
        coupons = await conn.fetch('SELECT * FROM coupons ORDER BY id DESC')
        return [{**dict(c)} for c in coupons]

@api_router.post("/coupons")
async def create_coupon(coupon: Coupon):
    pool = await get_db()
    async with pool.acquire() as conn:
        result = await conn.fetchrow('''
            INSERT INTO coupons (code, discount_type, discount_value, min_purchase, max_discount, valid_from, valid_until, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *
        ''', coupon.code, coupon.discount_type, coupon.discount_value, coupon.min_purchase,
           coupon.max_discount, coupon.valid_from, coupon.valid_until, coupon.is_active)
        return dict(result)

# Analytics endpoints
@api_router.get("/analytics/overview")
async def get_analytics_overview():
    pool = await get_db()
    async with pool.acquire() as conn:
        total_revenue = await conn.fetchval('SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status = $1', 'completed')
        total_orders = await conn.fetchval('SELECT COUNT(*) FROM orders')
        total_products = await conn.fetchval('SELECT COUNT(*) FROM products')
        total_customers = await conn.fetchval('SELECT COUNT(*) FROM customers')
        
        # Recent orders
        recent_orders = await conn.fetch('''
            SELECT o.*, c.name as customer_name
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            ORDER BY o.created_at DESC
            LIMIT 10
        ''')
        
        # Top products
        top_products = await conn.fetch('''
            SELECT p.name, SUM(oi.quantity) as total_sold, SUM(oi.subtotal) as total_revenue
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            GROUP BY p.id, p.name
            ORDER BY total_sold DESC
            LIMIT 10
        ''')
        
        return {
            "total_revenue": float(total_revenue),
            "total_orders": total_orders,
            "total_products": total_products,
            "total_customers": total_customers,
            "recent_orders": [{**dict(o)} for o in recent_orders],
            "top_products": [{**dict(p)} for p in top_products]
        }

# QRIS endpoint (mock)
@api_router.post("/qris/generate")
async def generate_qris(request: dict):
    amount = request.get('amount', 0)
    product_name = request.get('product_name', 'Product')
    
    # Mock QRIS data
    qris_string = f"00020101021226660014ID.CO.QRIS.WWW0118MOCK{amount}000000000000000003MOCK520454995802ID5913Merchant Demo6007Jakarta61051234062070703A016304MOCK"
    
    return {
        "success": True,
        "qris_string": qris_string,
        "amount": amount,
        "product_name": product_name,
        "expired_at": (datetime.now() + timezone.utc).isoformat()
    }

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
        await db_pool.close()