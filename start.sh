#!/bin/bash

# Laravel POS System Startup Script

cd /app

# Clear caches
php artisan config:clear
php artisan route:clear
php artisan view:clear

# Start Laravel development server on port 8001
php artisan serve --host=0.0.0.0 --port=8001
