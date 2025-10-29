import secrets
import string
import re
import hashlib
from datetime import datetime, timedelta

def generate_password(length: int = 8) -> str:
    """
    Generate default password for new customer registration
    Default: 12345678
    """
    return "12345678"

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain_password) == hashed_password

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """
    Validate Indonesian phone number
    Accepts formats: 08xx, +628xx, 628xx
    """
    # Remove spaces and dashes
    phone = phone.replace(' ', '').replace('-', '')
    
    # Check Indonesian phone patterns
    patterns = [
        r'^08\d{8,11}$',        # 08xxxxxxxxxx
        r'^\+628\d{8,11}$',     # +628xxxxxxxxxx
        r'^628\d{8,11}$'        # 628xxxxxxxxxx
    ]
    
    return any(re.match(pattern, phone) for pattern in patterns)

def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to standard format (08xx)
    """
    phone = phone.replace(' ', '').replace('-', '')
    
    # Convert +628xx or 628xx to 08xx
    if phone.startswith('+62'):
        phone = '0' + phone[3:]
    elif phone.startswith('62'):
        phone = '0' + phone[2:]
    
    return phone

def generate_reset_token() -> str:
    """Generate secure reset token"""
    return secrets.token_urlsafe(32)

def generate_order_number() -> str:
    """Generate unique order number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = ''.join(secrets.choice(string.digits) for _ in range(4))
    return f"ORD-{timestamp}-{random_suffix}"

def calculate_discount(total: float, discount_type: str, discount_value: float, min_purchase: float = 0) -> dict:
    """
    Calculate discount amount
    
    Args:
        total: Order total amount
        discount_type: 'percentage' or 'nominal'
        discount_value: Discount value (e.g., 10 for 10% or 10000 for Rp 10,000)
        min_purchase: Minimum purchase requirement
    
    Returns:
        dict with discount_amount and final_total
    """
    # Check minimum purchase
    if total < min_purchase:
        return {
            'discount_amount': 0,
            'final_total': total,
            'error': f'Minimum pembelian Rp {min_purchase:,.0f} tidak terpenuhi'
        }
    
    discount_amount = 0
    
    if discount_type == 'percentage':
        discount_amount = total * (discount_value / 100)
    elif discount_type == 'nominal':
        discount_amount = discount_value
    
    # Ensure discount doesn't exceed total
    discount_amount = min(discount_amount, total)
    final_total = total - discount_amount
    
    return {
        'discount_amount': discount_amount,
        'final_total': final_total,
        'error': None
    }

def format_rupiah(amount: float) -> str:
    """Format number to Rupiah"""
    return f"Rp {amount:,.0f}".replace(',', '.')

def is_valid_coupon_code(code: str) -> bool:
    """Validate coupon code format"""
    # Coupon code should be 4-20 characters, alphanumeric and dash
    pattern = r'^[A-Z0-9-]{4,20}$'
    return re.match(pattern, code.upper()) is not None
