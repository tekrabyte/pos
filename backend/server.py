from fastapi import FastAPI, APIRouter, HTTPException, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
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

# Import custom modules
from email_service import email_service
from utils import (
    generate_password, hash_password, verify_password,
    validate_email, validate_phone, normalize_phone,
    generate_reset_token, generate_order_number,
    calculate_discount, is_valid_coupon_code
)

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
    email: EmailStr
    phone: str
    address: Optional[str] = None
    # Password will be auto-generated, no need to input

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ApplyCouponRequest(BaseModel):
    coupon_code: str

class RatingRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    review: Optional[str] = None

class StoreSettingsUpdate(BaseModel):
    store_name: Optional[str] = None
    store_description: Optional[str] = None
    banner_url: Optional[str] = None
    logo_url: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    opening_hours: Optional[str] = None
    is_open: Optional[bool] = None

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
    coupon_code: Optional[str] = None  # New: optional coupon code

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
            
            # Outlets
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
            
            # Roles
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS roles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    max_discount DECIMAL(5,2) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Payment Methods
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
            
            # Brands
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS brands (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    logo_url VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Coupons
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS coupons (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    code VARCHAR(50) UNIQUE NOT NULL,
                    discount_type VARCHAR(20) NOT NULL,
                    discount_value DECIMAL(10,2) NOT NULL,
                    min_purchase DECIMAL(12,2) DEFAULT 0,
                    max_discount DECIMAL(12,2),
                    valid_from DATETIME,
                    valid_until DATETIME,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Payment Settings
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS payment_settings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    setting_key VARCHAR(100) UNIQUE NOT NULL,
                    setting_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
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
            
            # Insert default outlet
            await cursor.execute('SELECT COUNT(*) FROM outlets')
            outlet_exists = (await cursor.fetchone())[0]
            if outlet_exists == 0:
                await cursor.execute(
                    'INSERT INTO outlets (name, address, city, country, postal_code, is_main) VALUES (%s, %s, %s, %s, %s, %s)',
                    ('Main Restaurant', 'Jl. Sudirman No. 123', 'Jakarta', 'Indonesia', '12190', True)
                )
            
            # Insert default roles
            await cursor.execute('SELECT COUNT(*) FROM roles')
            roles_exist = (await cursor.fetchone())[0]
            if roles_exist == 0:
                roles_data = [
                    ('Admin', 100.00),
                    ('Manager', 50.00),
                    ('Cashier', 10.00)
                ]
                for role_name, max_discount in roles_data:
                    await cursor.execute(
                        'INSERT INTO roles (name, max_discount) VALUES (%s, %s)',
                        (role_name, max_discount)
                    )
            
            # Insert default payment methods
            await cursor.execute('SELECT COUNT(*) FROM payment_methods')
            payment_methods_exist = (await cursor.fetchone())[0]
            if payment_methods_exist == 0:
                payment_methods_data = [
                    ('QRIS', 'qr_code', True, '{"provider": "QRIS", "merchant_id": "POSMERCHANT001"}'),
                    ('Bank Transfer', 'bank_transfer', True, '{"banks": ["BCA", "BNI", "Mandiri"]}'),
                    ('Cash', 'cash', True, '{}')
                ]
                for name, type_val, is_active, config in payment_methods_data:
                    await cursor.execute(
                        'INSERT INTO payment_methods (name, type, is_active, config) VALUES (%s, %s, %s, %s)',
                        (name, type_val, is_active, config)
                    )
            
            # Insert default brands
            await cursor.execute('SELECT COUNT(*) FROM brands')
            brands_exist = (await cursor.fetchone())[0]
            if brands_exist == 0:
                brands_data = [
                    ('House Brand', 'Restaurant house brand products', None),
                    ('Premium Selection', 'Premium quality products', None),
                    ('Local Favorites', 'Local specialty products', None)
                ]
                for name, description, logo_url in brands_data:
                    await cursor.execute(
                        'INSERT INTO brands (name, description, logo_url) VALUES (%s, %s, %s)',
                        (name, description, logo_url)
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

# Customer Register (Auto-generate password & send email)
@api_router.post("/auth/customer/register")
async def customer_register(customer: CustomerRegister):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Validate email format
            if not validate_email(customer.email):
                raise HTTPException(status_code=400, detail="Format email tidak valid")
            
            # Validate phone format
            if not validate_phone(customer.phone):
                raise HTTPException(status_code=400, detail="Format nomor telepon tidak valid (gunakan format 08xx)")
            
            # Normalize phone number
            normalized_phone = normalize_phone(customer.phone)
            
            # Check if email exists
            await cursor.execute('SELECT COUNT(*) FROM customers WHERE email = %s', (customer.email,))
            exists = (await cursor.fetchone())[0]
            if exists > 0:
                raise HTTPException(status_code=400, detail="Email sudah terdaftar")
            
            # Check if phone exists
            await cursor.execute('SELECT COUNT(*) FROM customers WHERE phone = %s', (normalized_phone,))
            exists = (await cursor.fetchone())[0]
            if exists > 0:
                raise HTTPException(status_code=400, detail="Nomor telepon sudah terdaftar")
            
            # Auto-generate password
            plain_password = generate_password()
            hashed_pwd = hash_password(plain_password)
            
            # Insert customer
            await cursor.execute(
                'INSERT INTO customers (name, email, password, phone, address, email_verified) VALUES (%s, %s, %s, %s, %s, %s)',
                (customer.name, customer.email, hashed_pwd, normalized_phone, customer.address, False)
            )
            customer_id = cursor.lastrowid
            await conn.commit()
            
            # Send welcome email with password
            email_sent = email_service.send_welcome_email(
                to_email=customer.email,
                name=customer.name,
                password=plain_password
            )
            
            return {
                "success": True,
                "customer_id": customer_id,
                "message": "Registrasi berhasil! Password telah dikirim ke email Anda.",
                "email_sent": email_sent,
                "temp_password": plain_password if not email_sent else None  # Show password if email failed
            }

# Customer Login
@api_router.post("/auth/customer/login", response_model=LoginResponse)
async def customer_login(request: LoginRequest):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Get customer by email
            await cursor.execute(
                'SELECT id, name, email, phone, address, password FROM customers WHERE email = %s',
                (request.email,)
            )
            customer = await cursor.fetchone()
            
            if customer:
                customer_dict = row_to_dict(customer, cursor)
                stored_password = customer_dict.pop('password')  # Remove password from response
                
                # Verify password
                if verify_password(request.password, stored_password):
                    return LoginResponse(
                        success=True,
                        user=customer_dict,
                        token=secrets.token_urlsafe(32)
                    )
            
            return LoginResponse(success=False, message="Email atau password salah")

# Forgot Password - Request Reset
@api_router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Check if customer exists
            await cursor.execute(
                'SELECT id, name, email FROM customers WHERE email = %s',
                (request.email,)
            )
            customer = await cursor.fetchone()
            
            if not customer:
                # Don't reveal if email exists or not (security)
                return {"success": True, "message": "Jika email terdaftar, link reset password telah dikirim"}
            
            customer_dict = row_to_dict(customer, cursor)
            
            # Generate reset token
            reset_token = generate_reset_token()
            expires_at = datetime.now() + timedelta(hours=1)
            
            # Save token to database
            await cursor.execute(
                'UPDATE customers SET password_reset_token = %s, password_reset_expires = %s WHERE id = %s',
                (reset_token, expires_at, customer_dict['id'])
            )
            await conn.commit()
            
            # Send reset email
            email_sent = email_service.send_password_reset_email(
                to_email=customer_dict['email'],
                name=customer_dict['name'],
                reset_token=reset_token
            )
            
            return {
                "success": True,
                "message": "Link reset password telah dikirim ke email Anda",
                "email_sent": email_sent
            }

# Reset Password - With Token
@api_router.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Find customer with valid token
            await cursor.execute(
                '''SELECT id, name, email FROM customers 
                   WHERE password_reset_token = %s 
                   AND password_reset_expires > NOW()''',
                (request.token,)
            )
            customer = await cursor.fetchone()
            
            if not customer:
                raise HTTPException(status_code=400, detail="Token tidak valid atau sudah kadaluarsa")
            
            # Hash new password
            hashed_pwd = hash_password(request.new_password)
            
            # Update password and clear reset token
            await cursor.execute(
                '''UPDATE customers 
                   SET password = %s, password_reset_token = NULL, password_reset_expires = NULL
                   WHERE id = %s''',
                (hashed_pwd, customer[0])
            )
            await conn.commit()
            
            return {"success": True, "message": "Password berhasil direset"}

# STORE SETTINGS ENDPOINTS

@api_router.get("/store-settings")
async def get_store_settings():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM store_settings LIMIT 1')
            result = await cursor.fetchone()
            if result:
                return row_to_dict(result, cursor)
            return {
                "store_name": "QR Scan & Dine",
                "rating": 4.5,
                "total_reviews": 0
            }

@api_router.put("/store-settings")
async def update_store_settings(settings: StoreSettingsUpdate):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            update_fields = []
            values = []
            
            for field, value in settings.dict(exclude_unset=True).items():
                if value is not None:
                    update_fields.append(f"{field} = %s")
                    values.append(value)
            
            if update_fields:
                query = f"UPDATE store_settings SET {', '.join(update_fields)} WHERE id = 1"
                await cursor.execute(query, values)
                await conn.commit()
            
            return {"success": True, "message": "Store settings updated"}

@api_router.get("/store-banners")
async def get_store_banners():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'SELECT * FROM store_banners WHERE is_active = TRUE ORDER BY display_order'
            )
            results = await cursor.fetchall()
            return [row_to_dict(row, cursor) for row in results]

# COUPON ENDPOINTS

@api_router.get("/coupons/available")
async def get_available_coupons():
    """Get active and valid coupons for customers"""
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                '''SELECT code, discount_type, discount_value, min_purchase, max_discount, 
                          start_date, end_date, usage_limit, used_count
                   FROM coupons 
                   WHERE is_active = TRUE 
                   AND (start_date IS NULL OR start_date <= NOW())
                   AND (end_date IS NULL OR end_date >= NOW())
                   AND (usage_limit = 0 OR used_count < usage_limit)
                   ORDER BY discount_value DESC'''
            )
            results = await cursor.fetchall()
            return [row_to_dict(row, cursor) for row in results]

@api_router.post("/coupons/validate")
async def validate_coupon(request: ApplyCouponRequest, total_amount: float):
    """Validate coupon code and calculate discount"""
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Get coupon details
            await cursor.execute(
                '''SELECT * FROM coupons 
                   WHERE code = %s 
                   AND is_active = TRUE
                   AND (start_date IS NULL OR start_date <= NOW())
                   AND (end_date IS NULL OR end_date >= NOW())
                   AND (usage_limit = 0 OR used_count < usage_limit)''',
                (request.coupon_code.upper(),)
            )
            coupon = await cursor.fetchone()
            
            if not coupon:
                raise HTTPException(status_code=400, detail="Kode kupon tidak valid atau sudah tidak berlaku")
            
            coupon_dict = row_to_dict(coupon, cursor)
            
            # Calculate discount
            discount_result = calculate_discount(
                total=total_amount,
                discount_type=coupon_dict['discount_type'],
                discount_value=float(coupon_dict['discount_value']),
                min_purchase=float(coupon_dict['min_purchase']) if coupon_dict['min_purchase'] else 0
            )
            
            if discount_result['error']:
                raise HTTPException(status_code=400, detail=discount_result['error'])
            
            # Apply max discount if set
            if coupon_dict['max_discount'] and discount_result['discount_amount'] > float(coupon_dict['max_discount']):
                discount_result['discount_amount'] = float(coupon_dict['max_discount'])
                discount_result['final_total'] = total_amount - discount_result['discount_amount']
            
            return {
                "success": True,
                "coupon": coupon_dict,
                "original_amount": total_amount,
                "discount_amount": discount_result['discount_amount'],
                "final_total": discount_result['final_total']
            }

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

@api_router.post("/tables/regenerate-qr")
async def regenerate_all_qr_codes():
    """Regenerate QR codes for all tables with current FRONTEND_URL"""
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Get all tables
            await cursor.execute('SELECT id, table_number, qr_token FROM tables')
            tables = await cursor.fetchall()
            
            if not tables:
                return {"success": True, "message": "No tables to update", "updated_count": 0}
            
            # Get frontend URL from environment
            frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
            updated_count = 0
            
            for table in tables:
                table_id = table[0]
                qr_token = table[2]
                
                # Generate new QR code with current frontend URL
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
                
                # Update table with new QR code
                await cursor.execute(
                    'UPDATE tables SET qr_code = %s WHERE id = %s',
                    (qr_code_data, table_id)
                )
                updated_count += 1
            
            await conn.commit()
            
            return {
                "success": True, 
                "message": f"Successfully regenerated QR codes for {updated_count} tables",
                "updated_count": updated_count,
                "frontend_url": frontend_url
            }

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
            # Check if product is used in any orders
            await cursor.execute('SELECT COUNT(*) FROM order_items WHERE product_id = %s', (product_id,))
            order_count = (await cursor.fetchone())[0]
            
            if order_count > 0:
                # Soft delete - just mark as inactive/deleted
                await cursor.execute('UPDATE products SET status = %s WHERE id = %s', ('deleted', product_id))
                await conn.commit()
                return {"success": True, "message": "Product marked as deleted (used in existing orders)"}
            else:
                # Hard delete if not used
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
            # Generate order number using utility
            order_number = generate_order_number()
            
            original_amount = order_req.total_amount
            discount_amount = 0
            coupon_id = None
            
            # Handle coupon if provided
            if order_req.coupon_code:
                await cursor.execute(
                    '''SELECT * FROM coupons 
                       WHERE code = %s 
                       AND is_active = TRUE
                       AND (start_date IS NULL OR start_date <= NOW())
                       AND (end_date IS NULL OR end_date >= NOW())
                       AND (usage_limit = 0 OR used_count < usage_limit)''',
                    (order_req.coupon_code.upper(),)
                )
                coupon = await cursor.fetchone()
                
                if coupon:
                    coupon_dict = row_to_dict(coupon, cursor)
                    coupon_id = coupon_dict['id']
                    
                    # Calculate discount
                    discount_result = calculate_discount(
                        total=original_amount,
                        discount_type=coupon_dict['discount_type'],
                        discount_value=float(coupon_dict['discount_value']),
                        min_purchase=float(coupon_dict['min_purchase']) if coupon_dict['min_purchase'] else 0
                    )
                    
                    if not discount_result['error']:
                        discount_amount = discount_result['discount_amount']
                        
                        # Apply max discount if set
                        if coupon_dict['max_discount'] and discount_amount > float(coupon_dict['max_discount']):
                            discount_amount = float(coupon_dict['max_discount'])
                        
                        # Update coupon usage count
                        await cursor.execute(
                            'UPDATE coupons SET used_count = used_count + 1 WHERE id = %s',
                            (coupon_id,)
                        )
            
            final_amount = original_amount - discount_amount
            
            try:
                await cursor.execute('''
                    INSERT INTO orders (order_number, customer_id, table_id, order_type, customer_name, customer_phone, 
                                       original_amount, discount_amount, total_amount, coupon_id, coupon_code,
                                       payment_method, payment_proof, status, estimated_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (order_number, order_req.customer_id, order_req.table_id, order_req.order_type, 
                      order_req.customer_name, order_req.customer_phone, original_amount, discount_amount,
                      final_amount, coupon_id, order_req.coupon_code, order_req.payment_method, 
                      order_req.payment_proof, 'pending', 30))
                
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
                    "total_amount": float(final_amount),
                    "discount_amount": float(discount_amount),
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

# ORDER RATING
@api_router.post("/orders/{order_id}/rating")
async def rate_order(order_id: int, rating_req: RatingRequest, customer_id: int):
    """Customer can rate completed order"""
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Check if order exists and belongs to customer
            await cursor.execute(
                'SELECT status, customer_id FROM orders WHERE id = %s',
                (order_id,)
            )
            order = await cursor.fetchone()
            
            if not order:
                raise HTTPException(status_code=404, detail="Order tidak ditemukan")
            
            if order[1] != customer_id:
                raise HTTPException(status_code=403, detail="Anda tidak memiliki akses ke order ini")
            
            if order[0] != 'completed':
                raise HTTPException(status_code=400, detail="Hanya order yang sudah selesai yang bisa diberi rating")
            
            # Check if already rated
            await cursor.execute(
                'SELECT id FROM order_ratings WHERE order_id = %s',
                (order_id,)
            )
            if await cursor.fetchone():
                raise HTTPException(status_code=400, detail="Order ini sudah diberi rating")
            
            # Insert rating
            await cursor.execute(
                'INSERT INTO order_ratings (order_id, customer_id, rating, review) VALUES (%s, %s, %s, %s)',
                (order_id, customer_id, rating_req.rating, rating_req.review)
            )
            
            # Update store average rating
            await cursor.execute('SELECT AVG(rating), COUNT(*) FROM order_ratings')
            avg_rating, total_reviews = await cursor.fetchone()
            
            await cursor.execute(
                'UPDATE store_settings SET rating = %s, total_reviews = %s WHERE id = 1',
                (round(float(avg_rating), 1), total_reviews)
            )
            
            await conn.commit()
            
            return {"success": True, "message": "Terima kasih atas rating Anda!"}

@api_router.get("/orders/{order_id}/tracking")
async def track_order(order_id: int):
    """Get order tracking details"""
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''
                SELECT o.*, c.name as customer_name_db, t.table_number,
                       r.rating, r.review
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                LEFT JOIN tables t ON o.table_id = t.id
                LEFT JOIN order_ratings r ON o.id = r.order_id
                WHERE o.id = %s
            ''', (order_id,))
            order = await cursor.fetchone()
            
            if not order:
                raise HTTPException(status_code=404, detail="Order tidak ditemukan")
            
            order_dict = row_to_dict(order, cursor)
            
            # Get order items
            await cursor.execute(
                'SELECT * FROM order_items WHERE order_id = %s',
                (order_id,)
            )
            items = await cursor.fetchall()
            order_dict['items'] = [row_to_dict(item, cursor) for item in items]
            
            # Calculate progress percentage
            status_progress = {
                'pending': 20,
                'confirmed': 40,
                'cooking': 60,
                'ready': 80,
                'completed': 100,
                'cancelled': 0
            }
            order_dict['progress'] = status_progress.get(order_dict['status'], 0)
            
            return order_dict

# DASHBOARD STATS
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get today's sales and order statistics"""
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            today = datetime.now().date()
            
            # Today's total sales
            await cursor.execute('''
                SELECT COALESCE(SUM(total_amount), 0) as total_sales,
                       COUNT(*) as total_orders
                FROM orders
                WHERE DATE(created_at) = %s
            ''', (today,))
            sales_data = await cursor.fetchone()
            
            # Orders by status today
            await cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM orders
                WHERE DATE(created_at) = %s
                GROUP BY status
            ''', (today,))
            status_counts = {row[0]: row[1] for row in await cursor.fetchall()}
            
            # Orders by type today
            await cursor.execute('''
                SELECT order_type, COUNT(*) as count
                FROM orders
                WHERE DATE(created_at) = %s
                GROUP BY order_type
            ''', (today,))
            type_counts = {row[0]: row[1] for row in await cursor.fetchall()}
            
            # Pending orders (all time)
            await cursor.execute('SELECT COUNT(*) FROM orders WHERE status = %s', ('pending',))
            pending_count = (await cursor.fetchone())[0]
            
            return {
                "today": {
                    "total_sales": float(sales_data[0]),
                    "total_orders": sales_data[1],
                    "by_status": status_counts,
                    "by_type": type_counts
                },
                "pending_orders": pending_count
            }

# ADMIN - CUSTOMER MANAGEMENT

class ResetPasswordRequest(BaseModel):
    new_password: Optional[str] = None  # If None, auto-generate

@api_router.post("/admin/customers/{customer_id}/reset-password")
async def admin_reset_customer_password(customer_id: int, request: ResetPasswordRequest = None):
    """Admin can reset customer password and send new one via email"""
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Get customer info
            await cursor.execute(
                'SELECT id, name, email FROM customers WHERE id = %s',
                (customer_id,)
            )
            customer = await cursor.fetchone()
            
            if not customer:
                raise HTTPException(status_code=404, detail="Customer tidak ditemukan")
            
            customer_dict = row_to_dict(customer, cursor)
            
            # Use custom password or auto-generate
            if request and request.new_password:
                # Custom password from admin
                new_password = request.new_password
                if len(new_password) < 6:
                    raise HTTPException(status_code=400, detail="Password minimal 6 karakter")
            else:
                # Auto-generate password
                new_password = generate_password()
            
            hashed_pwd = hash_password(new_password)
            
            # Update password
            await cursor.execute(
                'UPDATE customers SET password = %s WHERE id = %s',
                (hashed_pwd, customer_id)
            )
            await conn.commit()
            
            # Send email with new password
            email_sent = email_service.send_new_password_email(
                to_email=customer_dict['email'],
                name=customer_dict['name'],
                new_password=new_password
            )
            
            return {
                "success": True,
                "message": "Password berhasil direset dan dikirim ke email customer",
                "email_sent": email_sent,
                "temp_password": new_password if not email_sent else None
            }

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

@api_router.post("/bank-accounts")
async def create_bank_account(account: dict):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'INSERT INTO bank_accounts (account_name, bank_name, account_number, is_active) VALUES (%s, %s, %s, %s)',
                (account.get('account_name'), account.get('bank_name'), account.get('account_number'), account.get('is_active', True))
            )
            account_id = cursor.lastrowid
            await conn.commit()
            
            await cursor.execute('SELECT * FROM bank_accounts WHERE id = %s', (account_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.delete("/bank-accounts/{account_id}")
async def delete_bank_account(account_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('DELETE FROM bank_accounts WHERE id = %s', (account_id,))
            await conn.commit()
            return {"success": True, "message": "Bank account deleted"}

# PAYMENT SETTINGS (QRIS)

@api_router.get("/payment-settings/qris")
async def get_qris_settings():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM payment_settings WHERE setting_key = "qris" LIMIT 1')
            result = await cursor.fetchone()
            if result:
                row_dict = row_to_dict(result, cursor)
                # Parse JSON value
                import json
                return json.loads(row_dict['setting_value'])
            return None

@api_router.post("/payment-settings/qris")
async def save_qris_settings(settings: dict):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            import json
            settings_json = json.dumps(settings)
            
            # Check if exists
            await cursor.execute('SELECT id FROM payment_settings WHERE setting_key = "qris"')
            existing = await cursor.fetchone()
            
            if existing:
                await cursor.execute(
                    'UPDATE payment_settings SET setting_value = %s WHERE setting_key = "qris"',
                    (settings_json,)
                )
            else:
                await cursor.execute(
                    'INSERT INTO payment_settings (setting_key, setting_value) VALUES (%s, %s)',
                    ('qris', settings_json)
                )
            
            await conn.commit()
            return {"success": True, "message": "QRIS settings saved"}

@api_router.post("/upload/qris")
async def upload_qris_image(file: UploadFile = File(...)):
    """Upload QRIS image"""
    try:
        # Create qris uploads directory
        qris_dir = UPLOADS_DIR.parent / 'qris'
        qris_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1]
        filename = f"qris_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
        file_path = qris_dir / filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return URL
        return {
            "success": True,
            "filename": filename,
            "url": f"{os.environ.get('FRONTEND_URL')}/uploads/qris/{filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

# BRANDS

@api_router.get("/brands")
async def get_brands():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM brands ORDER BY id DESC')
            brands = await cursor.fetchall()
            return rows_to_dict(brands, cursor)

@api_router.post("/brands")
async def create_brand(brand: dict):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'INSERT INTO brands (name, description, logo_url) VALUES (%s, %s, %s)',
                (brand.get('name'), brand.get('description'), brand.get('logo_url'))
            )
            brand_id = cursor.lastrowid
            await conn.commit()
            
            await cursor.execute('SELECT * FROM brands WHERE id = %s', (brand_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.get("/brands/{brand_id}")
async def get_brand(brand_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM brands WHERE id = %s', (brand_id,))
            brand = await cursor.fetchone()
            if not brand:
                raise HTTPException(status_code=404, detail="Brand not found")
            return row_to_dict(brand, cursor)

@api_router.put("/brands/{brand_id}")
async def update_brand(brand_id: int, brand: dict):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'UPDATE brands SET name = %s, description = %s, logo_url = %s WHERE id = %s',
                (brand.get('name'), brand.get('description'), brand.get('logo_url'), brand_id)
            )
            await conn.commit()
            
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
            return {"success": True, "message": "Brand deleted"}

# CUSTOMERS CRUD

@api_router.get("/customers")
async def get_customers():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT id, name, email, phone, address, created_at FROM customers ORDER BY id DESC')
            customers = await cursor.fetchall()
            return rows_to_dict(customers, cursor)

@api_router.post("/customers")
async def create_customer_admin(customer: dict):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Check if email exists
            await cursor.execute('SELECT id FROM customers WHERE email = %s', (customer.get('email'),))
            if await cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email already registered")
            
            await cursor.execute(
                'INSERT INTO customers (name, email, password, phone, address) VALUES (%s, %s, %s, %s, %s)',
                (customer.get('name'), customer.get('email'), customer.get('password', 'password123'), customer.get('phone'), customer.get('address'))
            )
            customer_id = cursor.lastrowid
            await conn.commit()
            
            await cursor.execute('SELECT id, name, email, phone, address, created_at FROM customers WHERE id = %s', (customer_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.get("/customers/{customer_id}")
async def get_customer(customer_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT id, name, email, phone, address, created_at FROM customers WHERE id = %s', (customer_id,))
            customer = await cursor.fetchone()
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")
            return row_to_dict(customer, cursor)

@api_router.put("/customers/{customer_id}")
async def update_customer(customer_id: int, customer: dict):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'UPDATE customers SET name = %s, email = %s, phone = %s, address = %s WHERE id = %s',
                (customer.get('name'), customer.get('email'), customer.get('phone'), customer.get('address'), customer_id)
            )
            await conn.commit()
            
            await cursor.execute('SELECT id, name, email, phone, address, created_at FROM customers WHERE id = %s', (customer_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('DELETE FROM customers WHERE id = %s', (customer_id,))
            await conn.commit()
            return {"success": True, "message": "Customer deleted"}

# COUPONS

@api_router.get("/coupons")
async def get_coupons():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM coupons ORDER BY id DESC')
            coupons = await cursor.fetchall()
            return rows_to_dict(coupons, cursor)

@api_router.post("/coupons")
async def create_coupon(coupon: dict):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'INSERT INTO coupons (code, discount_type, discount_value, min_purchase, max_discount, valid_from, valid_until, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                (coupon.get('code'), coupon.get('discount_type'), coupon.get('discount_value'), 
                 coupon.get('min_purchase'), coupon.get('max_discount'), 
                 coupon.get('valid_from'), coupon.get('valid_until'), coupon.get('is_active', True))
            )
            coupon_id = cursor.lastrowid
            await conn.commit()
            
            await cursor.execute('SELECT * FROM coupons WHERE id = %s', (coupon_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.get("/coupons/{coupon_id}")
async def get_coupon(coupon_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM coupons WHERE id = %s', (coupon_id,))
            coupon = await cursor.fetchone()
            if not coupon:
                raise HTTPException(status_code=404, detail="Coupon not found")
            return row_to_dict(coupon, cursor)

@api_router.put("/coupons/{coupon_id}")
async def update_coupon(coupon_id: int, coupon: dict):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'UPDATE coupons SET code = %s, discount_type = %s, discount_value = %s, min_purchase = %s, max_discount = %s, valid_from = %s, valid_until = %s, is_active = %s WHERE id = %s',
                (coupon.get('code'), coupon.get('discount_type'), coupon.get('discount_value'),
                 coupon.get('min_purchase'), coupon.get('max_discount'),
                 coupon.get('valid_from'), coupon.get('valid_until'), coupon.get('is_active'), coupon_id)
            )
            await conn.commit()
            
            await cursor.execute('SELECT * FROM coupons WHERE id = %s', (coupon_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.delete("/coupons/{coupon_id}")
async def delete_coupon(coupon_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('DELETE FROM coupons WHERE id = %s', (coupon_id,))
            await conn.commit()
            return {"success": True, "message": "Coupon deleted"}

# OUTLETS

@api_router.get("/outlets")
async def get_outlets():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM outlets ORDER BY id DESC')
            outlets = await cursor.fetchall()
            return rows_to_dict(outlets, cursor)

@api_router.post("/outlets")
async def create_outlet(outlet: dict):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'INSERT INTO outlets (name, address, city, country, postal_code, is_main) VALUES (%s, %s, %s, %s, %s, %s)',
                (outlet.get('name'), outlet.get('address'), outlet.get('city'), 
                 outlet.get('country'), outlet.get('postal_code'), outlet.get('is_main', False))
            )
            outlet_id = cursor.lastrowid
            await conn.commit()
            
            await cursor.execute('SELECT * FROM outlets WHERE id = %s', (outlet_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.put("/outlets/{outlet_id}")
async def update_outlet(outlet_id: int, outlet: dict):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'UPDATE outlets SET name = %s, address = %s, city = %s, country = %s, postal_code = %s, is_main = %s WHERE id = %s',
                (outlet.get('name'), outlet.get('address'), outlet.get('city'), 
                 outlet.get('country'), outlet.get('postal_code'), outlet.get('is_main', False), outlet_id)
            )
            await conn.commit()
            
            await cursor.execute('SELECT * FROM outlets WHERE id = %s', (outlet_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.delete("/outlets/{outlet_id}")
async def delete_outlet(outlet_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('DELETE FROM outlets WHERE id = %s', (outlet_id,))
            await conn.commit()
            return {"success": True, "message": "Outlet deleted"}

# ROLES

@api_router.get("/roles")
async def get_roles():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM roles ORDER BY id DESC')
            roles = await cursor.fetchall()
            return rows_to_dict(roles, cursor)

@api_router.post("/roles")
async def create_role(role: dict):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'INSERT INTO roles (name, max_discount) VALUES (%s, %s)',
                (role.get('name'), role.get('max_discount', 0))
            )
            role_id = cursor.lastrowid
            await conn.commit()
            
            await cursor.execute('SELECT * FROM roles WHERE id = %s', (role_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.put("/roles/{role_id}")
async def update_role(role_id: int, role: dict):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                'UPDATE roles SET name = %s, max_discount = %s WHERE id = %s',
                (role.get('name'), role.get('max_discount', 0), role_id)
            )
            await conn.commit()
            
            await cursor.execute('SELECT * FROM roles WHERE id = %s', (role_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.delete("/roles/{role_id}")
async def delete_role(role_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('DELETE FROM roles WHERE id = %s', (role_id,))
            await conn.commit()
            return {"success": True, "message": "Role deleted"}

# PAYMENT METHODS

@api_router.get("/payment-methods")
async def get_payment_methods():
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM payment_methods ORDER BY id DESC')
            methods = await cursor.fetchall()
            return rows_to_dict(methods, cursor)

@api_router.post("/payment-methods")
async def create_payment_method(method: dict):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            config_json = json.dumps(method.get('config')) if method.get('config') else None
            await cursor.execute(
                'INSERT INTO payment_methods (name, type, is_active, config) VALUES (%s, %s, %s, %s)',
                (method.get('name'), method.get('type'), method.get('is_active', True), config_json)
            )
            method_id = cursor.lastrowid
            await conn.commit()
            
            await cursor.execute('SELECT * FROM payment_methods WHERE id = %s', (method_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.get("/payment-methods/{method_id}")
async def get_payment_method(method_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM payment_methods WHERE id = %s', (method_id,))
            method = await cursor.fetchone()
            if not method:
                raise HTTPException(status_code=404, detail="Payment method not found")
            return row_to_dict(method, cursor)

@api_router.put("/payment-methods/{method_id}")
async def update_payment_method(method_id: int, method: dict):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            config_json = json.dumps(method.get('config')) if method.get('config') else None
            await cursor.execute(
                'UPDATE payment_methods SET name = %s, type = %s, is_active = %s, config = %s WHERE id = %s',
                (method.get('name'), method.get('type'), method.get('is_active', True), config_json, method_id)
            )
            await conn.commit()
            
            await cursor.execute('SELECT * FROM payment_methods WHERE id = %s', (method_id,))
            result = await cursor.fetchone()
            return row_to_dict(result, cursor)

@api_router.delete("/payment-methods/{method_id}")
async def delete_payment_method(method_id: int):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('DELETE FROM payment_methods WHERE id = %s', (method_id,))
            await conn.commit()
            return {"success": True, "message": "Payment method deleted"}

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
