#!/usr/bin/env python3
"""
Xendit Payment Integration Service
Handles QRIS, Virtual Account, and E-wallet payments
"""

import os
import xendit
from xendit import Xendit
from typing import Dict, Any, Optional
import json
import hmac
import hashlib
from datetime import datetime

# Initialize Xendit client
XENDIT_API_KEY = os.getenv("XENDIT_API_KEY", "")
XENDIT_WEBHOOK_TOKEN = os.getenv("XENDIT_WEBHOOK_TOKEN", "")

# Initialize Xendit client
xendit_instance = Xendit(api_key=XENDIT_API_KEY)


class XenditService:
    """Service class for handling Xendit payment operations"""
    
    def __init__(self):
        self.api_key = XENDIT_API_KEY
        self.webhook_token = XENDIT_WEBHOOK_TOKEN
        xendit.api_key = self.api_key
    
    def create_qris_payment(self, amount: float, reference_id: str, channel_id: str = "pos_main") -> Dict[str, Any]:
        """
        Create a QRIS payment
        
        Args:
            amount: Payment amount in IDR
            reference_id: Unique reference ID for the payment
            channel_id: Channel identifier (pos_main, dine_in, takeaway)
        
        Returns:
            Dict containing payment details including QR code string
        """
        try:
            # Create invoice for QRIS
            invoice_data = {
                "external_id": reference_id,
                "amount": int(amount),
                "payer_email": "customer@pos-system.com",
                "description": f"Payment for order {reference_id}",
                "invoice_duration": 86400,  # 24 hours
                "currency": "IDR",
                "payment_methods": ["QRIS"]
            }
            
            invoice = xendit.Invoice.create(**invoice_data)
            
            return {
                "success": True,
                "payment_id": invoice["id"],
                "reference_id": reference_id,
                "qr_string": invoice["invoice_url"],
                "status": invoice["status"],
                "amount": amount,
                "expired_at": invoice["expiry_date"],
                "channel_code": "QRIS"
            }
        except Exception as e:
            print(f"Error creating QRIS payment: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_virtual_account(self, amount: float, reference_id: str, bank_code: str, 
                               customer_name: str = "Customer") -> Dict[str, Any]:
        """
        Create a Virtual Account payment
        
        Args:
            amount: Payment amount in IDR
            reference_id: Unique reference ID
            bank_code: Bank code (BCA, BNI, BRI, MANDIRI, PERMATA)
            customer_name: Customer name for the VA
        
        Returns:
            Dict containing VA details including account number
        """
        try:
            va_data = {
                "external_id": reference_id,
                "bank_code": bank_code,
                "name": customer_name,
                "expected_amount": int(amount),
                "is_closed": True,  # Closed VA with exact amount
                "is_single_use": True
            }
            
            va = xendit.VirtualAccount.create(**va_data)
            
            return {
                "success": True,
                "payment_id": va["id"],
                "reference_id": reference_id,
                "account_number": va["account_number"],
                "bank_code": bank_code,
                "bank_name": self._get_bank_name(bank_code),
                "customer_name": customer_name,
                "status": va["status"],
                "amount": amount,
                "expired_at": va["expiration_date"] if "expiration_date" in va else None
            }
        except Exception as e:
            print(f"Error creating Virtual Account: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_ewallet_payment(self, amount: float, reference_id: str, wallet_type: str,
                               success_url: str, failure_url: str) -> Dict[str, Any]:
        """
        Create an E-wallet payment (OVO, DANA, LinkAja, GoPay, ShopeePay)
        
        Args:
            amount: Payment amount in IDR
            reference_id: Unique reference ID
            wallet_type: Type of e-wallet (OVO, DANA, LINKAJA, etc)
            success_url: URL to redirect on success
            failure_url: URL to redirect on failure
        
        Returns:
            Dict containing e-wallet payment details including redirect URL
        """
        try:
            ewallet_data = {
                "external_id": reference_id,
                "amount": int(amount),
                "phone": "08123456789",  # Placeholder, should be from customer
                "ewallet_type": wallet_type.upper(),
                "callback_url": success_url,
                "redirect_url": success_url
            }
            
            charge = xendit.EWallet.create_ewallet_charge(**ewallet_data)
            
            return {
                "success": True,
                "payment_id": charge["id"] if "id" in charge else charge["charge_id"],
                "reference_id": reference_id,
                "redirect_url": charge["actions"]["desktop_web_checkout_url"] if "actions" in charge else charge["checkout_url"],
                "status": charge["status"],
                "amount": amount,
                "wallet_type": wallet_type
            }
        except Exception as e:
            print(f"Error creating E-wallet payment: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_payment_status(self, payment_id: str, payment_type: str = "invoice") -> Dict[str, Any]:
        """
        Get payment status
        
        Args:
            payment_id: Xendit payment ID
            payment_type: Type of payment (invoice, va, ewallet)
        
        Returns:
            Dict containing payment status
        """
        try:
            if payment_type == "invoice":
                invoice = xendit.Invoice.get(invoice_id=payment_id)
                return {
                    "success": True,
                    "payment_id": payment_id,
                    "status": invoice["status"],
                    "amount": invoice["amount"]
                }
            elif payment_type == "va":
                va = xendit.VirtualAccount.get(fixed_virtual_account_id=payment_id)
                return {
                    "success": True,
                    "payment_id": payment_id,
                    "status": va["status"],
                    "amount": va["expected_amount"]
                }
            else:
                return {
                    "success": False,
                    "error": "Unsupported payment type"
                }
        except Exception as e:
            print(f"Error getting payment status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify webhook signature from Xendit
        
        Args:
            payload: Raw webhook payload
            signature: Signature from webhook header
        
        Returns:
            True if signature is valid
        """
        try:
            expected_signature = hmac.new(
                self.webhook_token.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            print(f"Error verifying webhook signature: {e}")
            return False
    
    def _get_bank_name(self, bank_code: str) -> str:
        """Get full bank name from code"""
        bank_names = {
            "BCA": "Bank Central Asia",
            "BNI": "Bank Negara Indonesia",
            "BRI": "Bank Rakyat Indonesia",
            "MANDIRI": "Bank Mandiri",
            "PERMATA": "Bank Permata",
            "BSI": "Bank Syariah Indonesia",
            "BJB": "Bank BJB",
            "CIMB": "CIMB Niaga"
        }
        return bank_names.get(bank_code, bank_code)


# Create singleton instance
xendit_service = XenditService()
