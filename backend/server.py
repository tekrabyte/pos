from fastapi import FastAPI, APIRouter, HTTPException, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Set
from datetime import datetime, timezone, timedelta
import aiomysql
import json
import qrcode
import io
import base64
import secrets
import shutil
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create uploads directory
UPLOADS_DIR = ROOT_DIR / 'uploads' / 'payment_proofs'
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# MySQL connection pool
db_pool = None

# WebSocket connections for real-time notifications
websocket_connections: Set[WebSocket] = set()

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
    username: str = None
    password: str = None
    email: str = None

class LoginResponse(BaseModel):
    success: bool
    user: Optional[dict] = None
    token: Optional[str] = None
    message: Optional[str] = None

class CustomerRegister(BaseModel):
    name: str
    email: str
    password: str
    phone: str
    address: Optional[str] = None

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

class Table(BaseModel):
    id: Optional[int] = None
    table_number: str
    qr_code: Optional[str] = None
    qr_token: Optional[str] = None
    capacity: int = 4
    status: str = "available"
    created_at: Optional[datetime] = None

class OrderItem(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    price: float
    subtotal: float

class CreateOrderRequest(BaseModel):
    customer_id: Optional[int] = None
    table_id: Optional[int] = None
    order_type: str  # 'takeaway' or 'dine-in'
    items: List[OrderItem]
    payment_method: str  # 'qris' or 'bank_transfer'
    payment_proof: Optional[str] = None
    total_amount: float
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None

class OrderStatusUpdate(BaseModel):
    status: str  # pending, confirmed, cooking, ready, completed, cancelled
    payment_verified: Optional[bool] = None

# Helper functions
def row_to_dict(row, cursor):
    if row is None:
        return None
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))

def rows_to_dict(rows, cursor):
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in rows]

# WebSocket helper functions
async def broadcast_order_notification(message: dict):
    """Broadcast order notification to all connected WebSocket clients"""
    disconnected = set()
    for websocket in websocket_connections:
        try:
            await websocket.send_json(message)
        except:
            disconnected.add(websocket)
    
    # Remove disconnected clients
    websocket_connections.difference_update(disconnected)

# Initialize database
@app.on_event("startup")
async def startup():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Users table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    email VARCHAR(255),
                    full_name VARCHAR(255),
                    role VARCHAR(50) DEFAULT 'cashier',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Customers table (for takeaway orders)
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    phone VARCHAR(50),
                    address TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tables for dine-in
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS tables (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    table_number VARCHAR(50) UNIQUE NOT NULL,
                    qr_code TEXT,
                    qr_token VARCHAR(100) UNIQUE,
                    capacity INT DEFAULT 4,
                    status VARCHAR(50) DEFAULT 'available',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Categories
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
            
            # Products
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    sku VARCHAR(100) UNIQUE NOT NULL,
                    price DECIMAL(12,2) NOT NULL,
                    stock INT DEFAULT 0,
                    category_id INT,
                    description TEXT,
                    image_url VARCHAR(500),
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                )
            ''')
            
            # Orders
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    order_number VARCHAR(100) UNIQUE NOT NULL,
                    customer_id INT,
                    table_id INT,
                    order_type VARCHAR(50) NOT NULL,
                    customer_name VARCHAR(255),
                    customer_phone VARCHAR(50),
                    total_amount DECIMAL(12,2) NOT NULL,
                    payment_method VARCHAR(100),
                    payment_proof VARCHAR(500),
                    payment_verified BOOLEAN DEFAULT FALSE,
                    status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(id),
                    FOREIGN KEY (table_id) REFERENCES tables(id)
                )
            ''')
            
            # Order items
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
            
            # Bank accounts
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS bank_accounts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    bank_name VARCHAR(100) NOT NULL,
                    account_number VARCHAR(50) NOT NULL,
                    account_name VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await conn.commit()
            
            # Insert default admin
            await cursor.execute('SELECT COUNT(*) FROM users WHERE username = %s', ('admin',))
            admin_exists = (await cursor.fetchone())[0]
            if admin_exists == 0:
                await cursor.execute(
                    'INSERT INTO users (username, password, full_name, role, is_active) VALUES (%s, %s, %s, %s, %s)',
                    ('admin', 'admin123', 'Administrator', 'admin', True)
                )
            
            # Insert default bank account
            await cursor.execute('SELECT COUNT(*) FROM bank_accounts')
            bank_exists = (await cursor.fetchone())[0]
            if bank_exists == 0:
                await cursor.execute(
                    'INSERT INTO bank_accounts (bank_name, account_number, account_name, is_active) VALUES (%s, %s, %s, %s)',
                    ('BCA', '1234567890', 'POS MERCHANT', True)
                )
            
            await conn.commit()

# AUTH ENDPOINTS

# Admin/Staff Login
@api_router.post("/auth/staff/login", response_model=LoginResponse)
async def staff_login(request: LoginRequest):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'SELECT id, username, email, full_name, role FROM users WHERE username = %s AND password = %s',
                (request.username, request.password)
            )
            user = await cursor.fetchone()
            
            if user:
                user_dict = row_to_dict(user, cursor)
                return LoginResponse(
                    success=True,
                    user=user_dict,
                    token=secrets.token_urlsafe(32)
                )
            else:
                return LoginResponse(success=False, message="Invalid credentials")

# Customer Register
@api_router.post("/auth/customer/register")
async def customer_register(customer: CustomerRegister):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Check if email exists
            await cursor.execute('SELECT COUNT(*) FROM customers WHERE email = %s', (customer.email,))
            exists = (await cursor.fetchone())[0]
            if exists > 0:
                raise HTTPException(status_code=400, detail="Email already registered")
            
            await cursor.execute(
                'INSERT INTO customers (name, email, password, phone, address) VALUES (%s, %s, %s, %s, %s)',
                (customer.name, customer.email, customer.password, customer.phone, customer.address)
            )
            customer_id = cursor.lastrowid
            await conn.commit()
            
            return {"success": True, "customer_id": customer_id, "message": "Registration successful"}

# Customer Login
@api_router.post("/auth/customer/login", response_model=LoginResponse)
async def customer_login(request: LoginRequest):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'SELECT id, name, email, phone, address FROM customers WHERE email = %s AND password = %s',
                (request.email, request.password)
            )
            customer = await cursor.fetchone()
            
            if customer:
                customer_dict = row_to_dict(customer, cursor)
                return LoginResponse(
                    success=True,
                    user=customer_dict,
                    token=secrets.token_urlsafe(32)
                )
            else:
                return LoginResponse(success=False, message="Invalid credentials")

# WEBSOCKET ENDPOINT

@api_router.websocket("/ws/orders")
async def websocket_orders(websocket: WebSocket):
    await websocket.accept()
    websocket_connections.add(websocket)
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            # Echo back or handle client messages if needed
            await websocket.send_json({"status": "connected"})
    except WebSocketDisconnect:
        websocket_connections.discard(websocket)
    except Exception as e:
        websocket_connections.discard(websocket)

# TABLE MANAGEMENT

@api_router.get("/tables")
async def get_tables():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM tables ORDER BY table_number')
            tables = await cursor.fetchall()
            return rows_to_dict(tables, cursor)

@api_router.post("/tables")
async def create_table(table: Table):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Generate unique token for QR
            qr_token = secrets.token_urlsafe(16)
            
            # Get frontend URL from environment or use default
            frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
            
            # Generate QR code
            qr_data = f"{frontend_url}/customer/menu?table={qr_token}"
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
            qr_code_data = f"data:image/png;base64,{qr_code_base64}"
            
            await cursor.execute(
                'INSERT INTO tables (table_number, qr_code, qr_token, capacity, status) VALUES (%s, %s, %s, %s, %s)',
                (table.table_number, qr_code_data, qr_token, table.capacity, table.status)
            )
            table_id = cursor.lastrowid
            await conn.commit()
            
            await cursor.execute('SELECT * FROM tables WHERE id = %s', (table_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.get("/tables/{table_id}")
async def get_table(table_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM tables WHERE id = %s', (table_id,))
            table = await cursor.fetchone()
            if not table:
                raise HTTPException(status_code=404, detail="Table not found")
            return row_to_dict(table, cursor)

@api_router.get("/tables/token/{token}")
async def get_table_by_token(token: str):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM tables WHERE qr_token = %s', (token,))
            table = await cursor.fetchone()
            if not table:
                raise HTTPException(status_code=404, detail="Table not found")
            return row_to_dict(table, cursor)

@api_router.delete("/tables/{table_id}")
async def delete_table(table_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('DELETE FROM tables WHERE id = %s', (table_id,))
            await conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Table not found")
            return {"success": True, "message": "Table deleted"}

# PRODUCTS

@api_router.get("/products")
async def get_products(category_id: int = None):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            if category_id:
                await cursor.execute(
                    'SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.status = "active" AND p.category_id = %s ORDER BY p.id DESC',
                    (category_id,)
                )
            else:
                await cursor.execute(
                    'SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.status = "active" ORDER BY p.id DESC'
                )
            products = await cursor.fetchall()
            return rows_to_dict(products, cursor)

@api_router.post("/products")
async def create_product(product: Product):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'INSERT INTO products (name, sku, price, stock, category_id, description, image_url, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                (product.name, product.sku, product.price, product.stock, product.category_id, product.description, product.image_url, product.status)
            )
            product_id = cursor.lastrowid
            await conn.commit()
            
            await cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.get("/products/{product_id}")
async def get_product(product_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
            product = await cursor.fetchone()
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            return row_to_dict(product, cursor)

@api_router.put("/products/{product_id}")
async def update_product(product_id: int, product: Product):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'UPDATE products SET name = %s, sku = %s, price = %s, stock = %s, category_id = %s, description = %s, image_url = %s, status = %s WHERE id = %s',
                (product.name, product.sku, product.price, product.stock, product.category_id, product.description, product.image_url, product.status, product_id)
            )
            await conn.commit()
            
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
            return {"success": True, "message": "Product deleted"}

# CATEGORIES

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

@api_router.get("/categories/{category_id}")
async def get_category(category_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM categories WHERE id = %s', (category_id,))
            category = await cursor.fetchone()
            if not category:
                raise HTTPException(status_code=404, detail="Category not found")
            return row_to_dict(category, cursor)

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
            return {"success": True, "message": "Category deleted"}

# ORDERS

@api_router.post("/orders")
async def create_order(order_req: CreateOrderRequest):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Generate order number
            order_number = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(2).upper()}"
            
            try:
                await cursor.execute('''
                    INSERT INTO orders (order_number, customer_id, table_id, order_type, customer_name, customer_phone, 
                                       total_amount, payment_method, payment_proof, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (order_number, order_req.customer_id, order_req.table_id, order_req.order_type, 
                      order_req.customer_name, order_req.customer_phone, order_req.total_amount, 
                      order_req.payment_method, order_req.payment_proof, 'pending'))
                
                order_id = cursor.lastrowid
                
                # Create order items
                for item in order_req.items:
                    await cursor.execute(
                        'INSERT INTO order_items (order_id, product_id, product_name, quantity, price, subtotal) VALUES (%s, %s, %s, %s, %s, %s)',
                        (order_id, item.product_id, item.product_name, item.quantity, item.price, item.subtotal)
                    )
                    
                    # Update stock
                    await cursor.execute(
                        'UPDATE products SET stock = stock - %s WHERE id = %s',
                        (item.quantity, item.product_id)
                    )
                
                await conn.commit()
                
                await cursor.execute('SELECT * FROM orders WHERE id = %s', (order_id,))
                order = await cursor.fetchone()
                order_dict = row_to_dict(order, cursor)
                
                # Broadcast new order notification via WebSocket
                await broadcast_order_notification({
                    "type": "new_order",
                    "order_id": order_id,
                    "order_number": order_number,
                    "order_type": order_req.order_type,
                    "total_amount": float(order_req.total_amount),
                    "created_at": datetime.now().isoformat()
                })
                
                return order_dict
            except Exception as e:
                await conn.rollback()
                raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/orders")
async def get_orders(status: str = None, order_type: str = None):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = '''
                SELECT o.*, c.name as customer_name_from_db, t.table_number
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                LEFT JOIN tables t ON o.table_id = t.id
                WHERE 1=1
            '''
            params = []
            
            if status:
                query += ' AND o.status = %s'
                params.append(status)
            if order_type:
                query += ' AND o.order_type = %s'
                params.append(order_type)
            
            query += ' ORDER BY o.created_at DESC'
            
            await cursor.execute(query, params)
            orders = await cursor.fetchall()
            return rows_to_dict(orders, cursor)

@api_router.get("/orders/{order_id}")
async def get_order(order_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''
                SELECT o.*, c.name as customer_name_from_db, t.table_number
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                LEFT JOIN tables t ON o.table_id = t.id
                WHERE o.id = %s
            ''', (order_id,))
            order = await cursor.fetchone()
            
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            await cursor.execute('SELECT * FROM order_items WHERE order_id = %s', (order_id,))
            items = await cursor.fetchall()
            
            order_dict = row_to_dict(order, cursor)
            order_dict['items'] = rows_to_dict(items, cursor)
            return order_dict

@api_router.put("/orders/{order_id}/status")
async def update_order_status(order_id: int, update: OrderStatusUpdate):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            query = 'UPDATE orders SET status = %s'
            params = [update.status]
            
            if update.payment_verified is not None:
                query += ', payment_verified = %s'
                params.append(update.payment_verified)
            
            query += ' WHERE id = %s'
            params.append(order_id)
            
            await cursor.execute(query, params)
            await conn.commit()
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Order not found")
            
            await cursor.execute('SELECT * FROM orders WHERE id = %s', (order_id,))
            order = await cursor.fetchone()
            order_dict = row_to_dict(order, cursor)
            
            # Broadcast order status update via WebSocket
            await broadcast_order_notification({
                "type": "order_status_update",
                "order_id": order_id,
                "status": update.status,
                "payment_verified": update.payment_verified,
                "updated_at": datetime.now().isoformat()
            })
            
            return order_dict

@api_router.get("/orders/stats/pending")
async def get_pending_orders_count():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT COUNT(*) FROM orders WHERE status = %s', ('pending',))
            count = (await cursor.fetchone())[0]
            return {"count": count}

# PAYMENT PROOF UPLOAD

@api_router.post("/upload/payment-proof")
async def upload_payment_proof(file: UploadFile = File(...)):
    try:
        # Generate unique filename
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"{secrets.token_hex(16)}.{file_extension}"
        file_path = UPLOADS_DIR / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {"success": True, "filename": unique_filename, "url": f"/api/uploads/payment-proofs/{unique_filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/uploads/payment-proofs/{filename}")
async def get_payment_proof(filename: str):
    file_path = UPLOADS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

# BANK ACCOUNTS

@api_router.get("/bank-accounts")
async def get_bank_accounts():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM bank_accounts WHERE is_active = TRUE')
            accounts = await cursor.fetchall()
            return rows_to_dict(accounts, cursor)

# Analytics Endpoint
@api_router.get("/analytics/overview")
async def get_analytics_overview():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Get total revenue
            await cursor.execute('SELECT COALESCE(SUM(total_amount), 0) as total_revenue FROM orders WHERE status IN ("completed", "ready")')
            total_revenue_row = await cursor.fetchone()
            total_revenue = total_revenue_row[0] if total_revenue_row else 0
            
            # Get total orders
            await cursor.execute('SELECT COUNT(*) as total_orders FROM orders')
            total_orders_row = await cursor.fetchone()
            total_orders = total_orders_row[0] if total_orders_row else 0
            
            # Get total products
            await cursor.execute('SELECT COUNT(*) as total_products FROM products WHERE status = "active"')
            total_products_row = await cursor.fetchone()
            total_products = total_products_row[0] if total_products_row else 0
            
            # Get total customers
            await cursor.execute('SELECT COUNT(*) as total_customers FROM customers')
            total_customers_row = await cursor.fetchone()
            total_customers = total_customers_row[0] if total_customers_row else 0
            
            # Get recent orders (last 10)
            await cursor.execute('''
                SELECT o.id, o.order_number, o.total_amount, o.status, o.order_type, 
                       o.customer_name, o.created_at,
                       t.table_number
                FROM orders o
                LEFT JOIN tables t ON o.table_id = t.id
                ORDER BY o.created_at DESC
                LIMIT 10
            ''')
            recent_orders = await cursor.fetchall()
            recent_orders_list = rows_to_dict(recent_orders, cursor)
            
            # Get top products (best sellers)
            await cursor.execute('''
                SELECT p.id, p.name, p.price, SUM(oi.quantity) as total_sold
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                GROUP BY p.id, p.name, p.price
                ORDER BY total_sold DESC
                LIMIT 5
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

# QRIS Generation

@api_router.post("/qris/generate")
async def generate_qris(request: dict):
    import qrcode
    import io
    import base64
    
    amount = request.get('amount', 0)
    order_number = request.get('order_number', 'ORDER')
    merchant_id = request.get('merchant_id', 'POSMERCHANT001')
    
    qris_string = f"00020101021226660014ID.CO.QRIS.WWW0118{merchant_id}0215POSMERCHANT520454995802ID5913POS Merchant6007Jakarta610512340704{int(amount)}6304ABCD"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qris_string)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return {
        "success": True,
        "qris_string": qris_string,
        "qr_code_image": f"data:image/png;base64,{qr_code_base64}",
        "amount": amount,
        "order_number": order_number,
        "merchant_id": merchant_id,
        "expired_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
    }

@api_router.get("/")
async def root():
    return {"message": "POS API is running", "version": "2.0.0"}

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
