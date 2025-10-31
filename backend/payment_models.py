#!/usr/bin/env python3
"""
Payment Models and Database Schema
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class PaymentRequest(BaseModel):
    """Base payment request model"""
    amount: float = Field(..., gt=0, description="Payment amount in IDR")
    order_id: Optional[int] = Field(None, description="Order ID")
    channel_id: str = Field(default="pos_main", description="Channel ID (pos_main, dine_in, takeaway)")
    customer_name: Optional[str] = Field(default="Customer", description="Customer name")
    customer_phone: Optional[str] = Field(None, description="Customer phone")
    notes: Optional[str] = Field(None, description="Additional notes")


class QRISPaymentRequest(PaymentRequest):
    """QRIS payment request"""
    pass


class VirtualAccountRequest(PaymentRequest):
    """Virtual Account payment request"""
    bank_code: str = Field(..., description="Bank code (BCA, BNI, BRI, MANDIRI, etc)")


class EWalletPaymentRequest(PaymentRequest):
    """E-wallet payment request"""
    wallet_type: str = Field(..., description="E-wallet type (OVO, DANA, LINKAJA, GOPAY, SHOPEEPAY)")
    success_url: str = Field(default="http://localhost:3000/payment-success")
    failure_url: str = Field(default="http://localhost:3000/payment-failed")


class PaymentMethodConfig(BaseModel):
    """Payment method configuration"""
    id: Optional[int] = None
    name: str
    type: str  # qris, va, ewallet, cash
    channel_code: str  # QRIS, BCA, BNI, OVO, etc
    display_name: str
    enabled: bool = True
    min_amount: float = 1000
    max_amount: float = 10000000
    channel_id: str = "all"  # all, pos_main, dine_in, takeaway
    icon_url: Optional[str] = None
    display_order: int = 0
    config: Optional[Dict[str, Any]] = None


class XenditSettings(BaseModel):
    """Xendit configuration settings"""
    api_key: str
    webhook_token: str
    environment: str = "development"  # development, production
    enabled: bool = True
