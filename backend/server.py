#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
import os
from typing import List, Dict, Any, Optional
import uvicorn
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Xendit service
try:
    from xendit_service import xendit_service
    from payment_models import (
        QRISPaymentRequest,
        VirtualAccountRequest,
        EWalletPaymentRequest
    )
    XENDIT_ENABLED = True
except Exception as e:
    print(f"Warning: Xendit not enabled: {e}")
    XENDIT_ENABLED = False

app = FastAPI(title="POS API with Xendit", version="2.0.0")

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

@app.get("/api/health")
async def health_check():
    return {
        "status": "OK",
        "message": "POS API with Xendit is running",
        "version": "2.0.0",
        "xendit_enabled": XENDIT_ENABLED and bool(os.getenv("XENDIT_API_KEY"))
    }

@app.get("/api/payment-methods")
async def get_payment_methods(channel_id: Optional[str] = None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check columns
        cursor.execute("DESCRIBE payment_methods")
        columns = [row["Field"] for row in cursor.fetchall()]
        
        # Build query
        base_columns = ["id", "name", "type", "is_active"]
        optional_columns = ["config", "created_at", "updated_at", "channel_id", "channel_code", "display_name", "display_order", "min_amount", "max_amount"]
        
        available_columns = base_columns + [col for col in optional_columns if col in columns]
        
        if channel_id and "channel_id" in columns:
            query = f"SELECT {', '.join(available_columns)} FROM payment_methods WHERE is_active = TRUE AND (channel_id = %s OR channel_id = 'all') ORDER BY display_order, id"
            cursor.execute(query, (channel_id,))
        else:
            query = f"SELECT {', '.join(available_columns)} FROM payment_methods WHERE is_active = TRUE ORDER BY display_order, id"
            cursor.execute(query)
        
        methods = []
        for row in cursor.fetchall():
            method = {
                "id": row["id"],
                "name": row["name"],
                "type": row["type"],
                "is_active": row["is_active"],
            }
            
            # Add optional columns
            for col in optional_columns:
                if col in row:
                    if col in ["created_at", "updated_at"] and row[col]:
                        method[col] = row[col].isoformat()
                    elif col == "config" and row[col]:
                        try:
                            method[col] = json.loads(row[col])
                        except:
                            method[col] = row[col]
                    else:
                        method[col] = row[col]
        
            methods.append(method)
        
        cursor.close()
        conn.close()
        
        return {"success": True, "payment_methods": methods}
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ========== XENDIT ENDPOINTS ==========

if XENDIT_ENABLED:
    
    @app.post("/api/xendit/payments/qris")
    async def create_qris_payment(request: QRISPaymentRequest):
        try:
            reference_id = f"qris_{request.channel_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            
            result = xendit_service.create_qris_payment(
                amount=request.amount,
                reference_id=reference_id,
                channel_id=request.channel_id
            )
            
            if not result.get("success"):
                raise HTTPException(status_code=500, detail=result.get("error"))
            
            # Store in DB
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO xendit_payments 
                (reference_id, payment_id, payment_type, channel_code, amount, status, order_id, 
                 customer_name, channel_id, metadata, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                reference_id, result["payment_id"], "qris", "QRIS",
                request.amount, result["status"], request.order_id,
                request.customer_name, request.channel_id,
                json.dumps({"qr_string": result["qr_string"]})
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
                "amount": request.amount
            }
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @app.post("/api/xendit/payments/virtual-account")
    async def create_va_payment(request: VirtualAccountRequest):
        try:
            reference_id = f"va_{request.bank_code}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            
            result = xendit_service.create_virtual_account(
                amount=request.amount,
                reference_id=reference_id,
                bank_code=request.bank_code,
                customer_name=request.customer_name or "Customer"
            )
            
            if not result.get("success"):
                raise HTTPException(status_code=500, detail=result.get("error"))
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO xendit_payments 
                (reference_id, payment_id, payment_type, channel_code, amount, status, order_id, 
                 customer_name, channel_id, metadata, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                reference_id, result["payment_id"], "virtual_account", request.bank_code,
                request.amount, result["status"], request.order_id,
                request.customer_name, request.channel_id,
                json.dumps({"account_number": result["account_number"], "bank_name": result["bank_name"]})
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
                "status": result["status"],
                "amount": request.amount
            }
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @app.post("/api/xendit/payments/ewallet")
    async def create_ewallet_payment(request: EWalletPaymentRequest):
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
                raise HTTPException(status_code=500, detail=result.get("error"))
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO xendit_payments 
                (reference_id, payment_id, payment_type, channel_code, amount, status, order_id, 
                 customer_name, channel_id, metadata, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                reference_id, result["payment_id"], "ewallet", request.wallet_type,
                request.amount, result["status"], request.order_id,
                request.customer_name, request.channel_id,
                json.dumps({"redirect_url": result["redirect_url"]})
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
                "amount": request.amount
            }
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @app.get("/api/xendit/payments/{payment_id}/status")
    async def get_payment_status(payment_id: str):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT * FROM xendit_payments 
                WHERE payment_id = %s OR reference_id = %s
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
                    "metadata": json.loads(payment["metadata"]) if payment["metadata"] else {},
                    "created_at": payment["created_at"].isoformat() if payment["created_at"] else None
                }
            }
        except Exception as e:
            print(f"Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @app.post("/api/xendit/webhook")
    async def xendit_webhook(request: Request, x_callback_token: Optional[str] = Header(None)):
        try:
            body = await request.body()
            payload = body.decode('utf-8')
            
            # Verify token
            expected_token = os.getenv("XENDIT_WEBHOOK_TOKEN", "")
            if x_callback_token != expected_token:
                raise HTTPException(status_code=401, detail="Unauthorized")
            
            data = json.loads(payload)
            print(f"Xendit webhook: {json.dumps(data, indent=2)}")
            
            # Update payment
            conn = get_db_connection()
            cursor = conn.cursor()
            
            external_id = data.get("external_id") or data.get("reference_id")
            payment_id = data.get("id")
            status = data.get("status", "PENDING")
            paid_amount = data.get("paid_amount") or data.get("amount", 0)
            
            if external_id:
                cursor.execute("""
                    UPDATE xendit_payments 
                    SET status = %s, paid_amount = %s,
                        paid_at = CASE WHEN %s IN ('PAID', 'SETTLED', 'COMPLETED') THEN NOW() ELSE paid_at END,
                        webhook_data = %s, updated_at = NOW()
                    WHERE reference_id = %s OR payment_id = %s
                """, (status, paid_amount, status, payload, external_id, payment_id))
                
                # Update order if paid
                if status in ['PAID', 'SETTLED', 'COMPLETED']:
                    cursor.execute("""
                        UPDATE orders o
                        JOIN xendit_payments xp ON o.id = xp.order_id
                        SET o.payment_verified = TRUE, o.status = 'confirmed'
                        WHERE xp.reference_id = %s OR xp.payment_id = %s
                    """, (external_id, payment_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return {"success": True, "message": "Webhook processed"}
        except Exception as e:
            print(f"Webhook error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    print(f"Starting POS API with Xendit on port {port}")
    print(f"Xendit enabled: {XENDIT_ENABLED}")
    uvicorn.run(app, host="0.0.0.0", port=port)