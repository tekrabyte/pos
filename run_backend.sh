#!/bin/bash

# Laravel Backend Startup Script

cd /app

# Start Laravel development server on port 8001
php artisan serve --host=0.0.0.0 --port=8001
