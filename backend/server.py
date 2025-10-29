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
        
        # First, let's check what columns exist
        cursor.execute("DESCRIBE payment_methods")
        columns = [row["Field"] for row in cursor.fetchall()]
        print(f"Available columns: {columns}")
        
        # Build query based on available columns
        base_columns = ["id", "name", "type", "is_active"]
        optional_columns = ["config", "created_at", "updated_at"]
        
        available_columns = base_columns + [col for col in optional_columns if col in columns]
        query = f"SELECT {', '.join(available_columns)} FROM payment_methods ORDER BY id DESC"
        print(f"Query: {query}")
        cursor.execute(query)
        
        methods = []
        for row in cursor.fetchall():
            method = {
                "id": row["id"],
                "name": row["name"],
                "type": row["type"],
                "is_active": row["is_active"],
            }
            
            # Add optional columns if they exist
            if "config" in row:
                method["config"] = row["config"]
            else:
                method["config"] = None
                
            if "created_at" in row and row["created_at"]:
                method["created_at"] = row["created_at"].isoformat()
            else:
                method["created_at"] = None
                
            if "updated_at" in row and row["updated_at"]:
                method["updated_at"] = row["updated_at"].isoformat()
            else:
                method["updated_at"] = None
                
            methods.append(method)
        
        cursor.close()
        conn.close()
        
        return {"success": True, "payment_methods": methods}
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        print(f"Internal server error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)