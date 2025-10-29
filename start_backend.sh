#!/bin/bash

# POS System Startup Script
# Starts the Fiber backend server

echo "🚀 Starting POS System..."

# Check if Go is installed
if [ ! -f "/usr/local/go/bin/go" ]; then
    echo "❌ Go is not installed at /usr/local/go"
    echo "Installing Go 1.23.4..."
    cd /tmp
    wget -q https://go.dev/dl/go1.23.4.linux-arm64.tar.gz
    sudo rm -rf /usr/local/go
    sudo tar -C /usr/local -xzf go1.23.4.linux-arm64.tar.gz
    echo "✅ Go installed"
fi

# Navigate to backend directory
cd /app/backend

# Build the server if binary doesn't exist
if [ ! -f "./server" ]; then
    echo "📦 Building server..."
    /usr/local/go/bin/go build -o server .
    echo "✅ Server built successfully"
fi

# Kill existing server if running
pkill -f "./server" 2>/dev/null

# Start the server
echo "🔥 Starting Fiber backend on port 8001..."
./server > /var/log/fiber-backend.log 2>&1 &
SERVER_PID=$!

# Wait a moment for server to start
sleep 2

# Check if server is running
if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Backend server started successfully (PID: $SERVER_PID)"
    echo "📍 Health check: http://localhost:8001/api/health"
    
    # Test health endpoint
    HEALTH=$(curl -s http://localhost:8001/api/health | grep -o "\"status\":\"OK\"")
    if [ ! -z "$HEALTH" ]; then
        echo "✅ Health check passed!"
    else
        echo "⚠️  Health check failed - server may still be starting"
    fi
else
    echo "❌ Failed to start server"
    echo "Check logs: tail -f /var/log/fiber-backend.log"
    exit 1
fi

echo ""
echo "🎉 POS System is ready!"
echo "📖 API Docs: http://localhost:8001/api/health"
echo "📊 Dashboard: http://localhost:3000"
echo "📝 Logs: tail -f /var/log/fiber-backend.log"
