#!/usr/bin/env python3

"""
POS System Backend API with Xendit Payment Integration
Handles QRIS, Virtual Account, E-wallet payments, and webhooks
"""

from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import mysql.connector
import os
from typing import List, Dict, Any, Optional
import uvicorn
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import payment services
from xendit_service import xendit_service
from payment_models import (
    QRISPaymentRequest,
    VirtualAccountRequest,
    EWalletPaymentRequest,
    PaymentMethodConfig
)

app = FastAPI(title="POS System API with Xendit", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "srv1412.hstgr.io"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "u215947863_pos_dev"),
        password=os.getenv("DB_PASSWORD", "Pos_dev123#"),
        database=os.getenv("DB_NAME", "u215947863_pos_dev")
    )


# ========== HEALTH CHECK ==========
@app.get("/api/health")
async def health_check():
    return {
        "status": "OK",
        "message": "POS System API with Xendit is running",
        "version": "2.0.0",
        "xendit_enabled": bool(os.getenv("XENDIT_API_KEY"))
    }


# ========== XENDIT PAYMENT ENDPOINTS ==========

@app.post("/api/xendit/payments/qris")
async def create_qris_payment(request: QRISPaymentRequest):
    """
    Create a QRIS payment
    """
    try:
        reference_id = f"qris_{request.channel_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        result = xendit_service.create_qris_payment(
            amount=request.amount,
            reference_id=reference_id,
            channel_id=request.channel_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to create QRIS payment"))
        
        # Store payment in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO xendit_payments 
            (reference_id, payment_id, payment_type, channel_code, amount, status, order_id, 
             customer_name, channel_id, metadata, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            reference_id,
            result["payment_id"],
            "qris",
            "QRIS",
            request.amount,
            result["status"],
            request.order_id,
            request.customer_name,
            request.channel_id,
            json.dumps({"qr_string": result["qr_string"], "expired_at": result.get("expired_at")})
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "payment_id": result["payment_id"],
            "reference_id": reference_id,
            "qr_string": result["qr_string"],
            "status": result["status"],
            "amount": request.amount,
            "expired_at": result.get("expired_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating QRIS payment: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create QRIS payment: {str(e)}")


@app.post("/api/xendit/payments/virtual-account")
async def create_virtual_account_payment(request: VirtualAccountRequest):
    """
    Create a Virtual Account payment
    """
    try:
        reference_id = f"va_{request.bank_code}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        result = xendit_service.create_virtual_account(
            amount=request.amount,
            reference_id=reference_id,
            bank_code=request.bank_code,
            customer_name=request.customer_name or "Customer"
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to create Virtual Account"))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO xendit_payments 
            (reference_id, payment_id, payment_type, channel_code, amount, status, order_id, 
             customer_name, channel_id, metadata, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            reference_id,
            result["payment_id"],
            "virtual_account",
            request.bank_code,
            request.amount,
            result["status"],
            request.order_id,
            request.customer_name,
            request.channel_id,
            json.dumps({
                "account_number": result["account_number"],
                "bank_name": result["bank_name"],
                "expired_at": result.get("expired_at")
            })
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "payment_id": result["payment_id"],
            "reference_id": reference_id,
            "account_number": result["account_number"],
            "bank_code": request.bank_code,
            "bank_name": result["bank_name"],
            "customer_name": result["customer_name"],
            "status": result["status"],
            "amount": request.amount,
            "expired_at": result.get("expired_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating Virtual Account: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create Virtual Account: {str(e)}")


@app.post("/api/xendit/payments/ewallet")
async def create_ewallet_payment(request: EWalletPaymentRequest):
    """
    Create an E-wallet payment
    """
    try:
        reference_id = f"ewallet_{request.wallet_type}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        result = xendit_service.create_ewallet_payment(
            amount=request.amount,
            reference_id=reference_id,
            wallet_type=request.wallet_type,
            success_url=request.success_url,
            failure_url=request.failure_url
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to create E-wallet payment"))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO xendit_payments 
            (reference_id, payment_id, payment_type, channel_code, amount, status, order_id, 
             customer_name, channel_id, metadata, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            reference_id,
            result["payment_id"],
            "ewallet",
            request.wallet_type,
            request.amount,
            result["status"],
            request.order_id,
            request.customer_name,
            request.channel_id,
            json.dumps({
                "redirect_url": result["redirect_url"],
                "wallet_type": request.wallet_type
            })
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "payment_id": result["payment_id"],
            "reference_id": reference_id,
            "redirect_url": result["redirect_url"],
            "status": result["status"],
            "amount": request.amount,
            "wallet_type": request.wallet_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating E-wallet payment: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create E-wallet payment: {str(e)}")


@app.get("/api/xendit/payments/{payment_id}/status")
async def get_payment_status(payment_id: str):
    """
    Get payment status from database
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM xendit_payments WHERE payment_id = %s OR reference_id = %s
        """, (payment_id, payment_id))
        
        payment = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        return {
            "success": True,
            "payment": {
                "id": payment["id"],
                "payment_id": payment["payment_id"],
                "reference_id": payment["reference_id"],
                "payment_type": payment["payment_type"],
                "channel_code": payment["channel_code"],
                "amount": float(payment["amount"]),
                "status": payment["status"],
                "order_id": payment["order_id"],
                "customer_name": payment["customer_name"],
                "metadata": json.loads(payment["metadata"]) if payment["metadata"] else {},
                "created_at": payment["created_at"].isoformat() if payment["created_at"] else None,
                "paid_at": payment["paid_at"].isoformat() if payment["paid_at"] else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting payment status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get payment status: {str(e)}")


@app.post("/api/xendit/webhook")
async def handle_xendit_webhook(request: Request, x_callback_token: Optional[str] = Header(None)):
    """
    Handle webhooks from Xendit
    """
    try:
        body = await request.body()
        payload = body.decode('utf-8')
        
        # Verify webhook token
        expected_token = os.getenv("XENDIT_WEBHOOK_TOKEN", "")
        if x_callback_token != expected_token:
            print(f"Webhook token mismatch")
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        data = json.loads(payload)
        print(f"Webhook received: {json.dumps(data, indent=2)}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        external_id = data.get("external_id") or data.get("reference_id")
        payment_id = data.get("id")
        
        if external_id:
            status = data.get("status", "PENDING")
            paid_amount = data.get("paid_amount") or data.get("amount", 0)
            
            cursor.execute("""
                UPDATE xendit_payments 
                SET status = %s, 
                    paid_amount = %s,
                    paid_at = CASE WHEN %s IN ('PAID', 'SETTLED', 'COMPLETED') THEN NOW() ELSE paid_at END,
                    webhook_data = %s,
                    updated_at = NOW()
                WHERE reference_id = %s OR payment_id = %s
            """, (status, paid_amount, status, payload, external_id, payment_id))
            
            if status in ['PAID', 'SETTLED', 'COMPLETED']:
                cursor.execute("""
                    UPDATE orders o
                    JOIN xendit_payments xp ON o.id = xp.order_id
                    SET o.payment_verified = TRUE,
                        o.status = 'confirmed'
                    WHERE xp.reference_id = %s OR xp.payment_id = %s
                """, (external_id, payment_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"success": True, "message": "Webhook processed"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing webhook: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


# ========== PAYMENT METHODS ==========

@app.get("/api/payment-methods")
async def get_payment_methods(channel_id: Optional[str] = None):
    """
    Get available payment methods
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if channel_id:
            cursor.execute("""
                SELECT * FROM payment_methods 
                WHERE is_active = TRUE 
                AND (channel_id = %s OR channel_id = 'all')
                ORDER BY display_order, id
            """, (channel_id,))
        else:
            cursor.execute("""
                SELECT * FROM payment_methods 
                WHERE is_active = TRUE
                ORDER BY display_order, id
            """)
        
        methods = cursor.fetchall()
        cursor.close()
        conn.close()
        
        for method in methods:
            if method.get("config"):
                try:
                    method["config"] = json.loads(method["config"])
                except:
                    method["config"] = {}
            if method.get("created_at"):
                method["created_at"] = method["created_at"].isoformat()
        
        return {"success": True, "payment_methods": methods}
        
    except Exception as e:
        print(f"Error getting payment methods: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/xendit/available-banks")
async def get_available_banks():
    """
    Get list of available banks for Virtual Account
    """
    return {
        "success": True,
        "banks": [
            {"code": "BCA", "name": "Bank Central Asia"},
            {"code": "BNI", "name": "Bank Negara Indonesia"},
            {"code": "BRI", "name": "Bank Rakyat Indonesia"},
            {"code": "MANDIRI", "name": "Bank Mandiri"},
            {"code": "PERMATA", "name": "Bank Permata"},
            {"code": "BSI", "name": "Bank Syariah Indonesia"},
        ]
    }


@app.get("/api/xendit/available-ewallets")
async def get_available_ewallets():
    """
    Get list of available e-wallets
    """
    return {
        "success": True,
        "ewallets": [
            {"code": "OVO", "name": "OVO"},
            {"code": "DANA", "name": "DANA"},
            {"code": "LINKAJA", "name": "LinkAja"},
            {"code": "SHOPEEPAY", "name": "ShopeePay"},
        ]
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    print(f"Starting POS System API with Xendit on port {port}")
    print(f"Xendit enabled: {bool(os.getenv('XENDIT_API_KEY'))}")
    uvicorn.run(app, host="0.0.0.0", port=port)
