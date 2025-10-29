#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
import os
from typing import List, Dict, Any
import uvicorn

app = FastAPI(title="Laravel POS API", version="1.0.0")

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
        "message": "Laravel POS API is running",
        "version": "1.0.0"
    }

@app.get("/api/payment-methods")
async def get_payment_methods():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT id, name, type, is_active, created_at, updated_at FROM payment_methods ORDER BY created_at DESC"
        cursor.execute(query)
        
        methods = []
        for row in cursor.fetchall():
            methods.append({
                "id": row["id"],
                "name": row["name"],
                "type": row["type"],
                "is_active": row["is_active"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            })
        
        cursor.close()
        conn.close()
        
        return {"success": True, "payment_methods": methods}
        
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)