"""
FastAPI Proxy Server for Laravel POS API
This server proxies all requests to the Laravel PHP backend running on port 8000
"""

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
from typing import Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Laravel POS API Proxy",
    description="FastAPI proxy for Laravel POS API",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Laravel backend URL
LARAVEL_URL = os.getenv("LARAVEL_URL", "http://127.0.0.1:8000")

# HTTP client for proxying requests
client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        response = await client.get(f"{LARAVEL_URL}/api/health")
        if response.status_code == 200:
            data = response.json()
            return JSONResponse(content=data, status_code=200)
        else:
            return JSONResponse(
                content={
                    "status": "ERROR",
                    "message": "Laravel backend is not responding correctly",
                    "laravel_status_code": response.status_code
                },
                status_code=503
            )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            content={
                "status": "ERROR",
                "message": f"Cannot connect to Laravel backend: {str(e)}"
            },
            status_code=503
        )


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_laravel(path: str, request: Request):
    """
    Proxy all /api requests to Laravel backend
    """
    try:
        # Get the full URL
        url = f"{LARAVEL_URL}/api/{path}"
        
        # Get query parameters
        query_params = dict(request.query_params)
        
        # Get headers (exclude host and content-length as they'll be set by httpx)
        headers = {
            key: value for key, value in request.headers.items()
            if key.lower() not in ["host", "content-length"]
        }
        
        # Get request body
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
            except Exception as e:
                logger.error(f"Error reading request body: {str(e)}")
        
        # Make the proxied request
        logger.info(f"Proxying {request.method} request to: {url}")
        
        response = await client.request(
            method=request.method,
            url=url,
            params=query_params,
            headers=headers,
            content=body
        )
        
        # Return the response
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        return JSONResponse(
            content={
                "success": False,
                "message": f"Error connecting to Laravel backend: {str(e)}"
            },
            status_code=502
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JSONResponse(
            content={
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            },
            status_code=500
        )


@app.on_event("shutdown")
async def shutdown_event():
    """Close HTTP client on shutdown"""
    await client.aclose()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
