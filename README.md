# POS System API - Fiber (Golang)

Modern Point of Sale API built with Go Fiber framework and MySQL database.

## 🚀 Tech Stack

- **Backend**: Go 1.23.4 + Fiber v2
- **Database**: MySQL (Remote)
- **Frontend**: React + Tailwind CSS
- **Authentication**: JWT

## 📁 Project Structure

```
/app/
├── backend/           # Fiber Go backend
│   ├── main.go       # Server entry point
│   ├── database.go   # Database connection
│   ├── models.go     # Data models
│   ├── routes.go     # API routes
│   ├── handlers.go   # Request handlers
│   └── server        # Compiled binary
├── frontend/         # React frontend
└── public/           # Static files
```

## 🔧 Setup & Installation

### Prerequisites
- Go 1.23+ installed at `/usr/local/go`
- MySQL database
- Node.js & Yarn

### Environment Variables

Create `/app/backend/.env`:
```env
DB_HOST=your_db_host
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
JWT_SECRET=your_jwt_secret_key
PORT=8001
```

### Build & Run

```bash
# Build backend
cd /app/backend
/usr/local/go/bin/go build -o server .

# Run backend
./server

# Run frontend (in another terminal)
cd /app/frontend
yarn start
```

## 📡 API Endpoints

### Authentication
- `POST /api/auth/staff/login` - Staff login
- `GET /api/auth/staff/me` - Get current user (protected)
- `POST /api/auth/staff/logout` - Logout (protected)

### Products
- `GET /api/products` - List all products
- `GET /api/products/:id` - Get single product
- `POST /api/products` - Create product (protected)
- `PUT /api/products/:id` - Update product (protected)
- `DELETE /api/products/:id` - Delete product (protected)

### Categories
- `GET /api/categories` - List all categories
- `GET /api/categories/:id` - Get single category
- `POST /api/categories` - Create category (protected)
- `PUT /api/categories/:id` - Update category (protected)
- `DELETE /api/categories/:id` - Delete category (protected)

### Brands
- `GET /api/brands` - List all brands
- `GET /api/brands/:id` - Get single brand

### Orders
- `GET /api/orders` - List all orders
- `GET /api/orders/:id` - Get single order
- `PUT /api/orders/:id/status` - Update order status (protected)

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics (protected)
- `GET /api/analytics` - Get analytics data (protected)

### Other Resources
- `/api/tables` - Table management
- `/api/customers` - Customer management
- `/api/coupons` - Coupon management
- `/api/outlets` - Outlet management
- `/api/payment-methods` - Payment methods

## 🔐 Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Default Credentials
- Username: `admin`
- Password: `admin123`

## 🧪 Testing

```bash
# Health check
curl http://localhost:8001/api/health

# Login
curl -X POST http://localhost:8001/api/auth/staff/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Get products
curl http://localhost:8001/api/products
```

## 📊 Database Schema

### Users Table
- id, username, password, email, full_name
- role, role_id, outlet_id, is_active
- created_at

### Products Table
- id, name, sku, price, stock
- category_id, brand_id, description
- image_url, status
- created_at, updated_at

### Orders Table
- id, order_number, customer_id, table_id
- order_type, customer_name, customer_phone
- outlet_id, user_id, total_amount
- payment_method, payment_verified, status
- coupon_id, discount_amount
- created_at, completed_at

## 🚀 Deployment

The server runs on port 8001 by default. Make sure to:
1. Set proper environment variables
2. Configure database connection
3. Update JWT secret for production
4. Enable HTTPS in production

## 📝 Development Notes

- All timestamps use MySQL's TIMESTAMP format
- Password hashing uses bcrypt
- CORS is enabled for all origins (configure for production)
- Database connection pooling is configured
- Automatic reconnection on connection loss

## 🛠️ Future Enhancements

- Complete CRUD operations for all resources
- File upload for product images
- Advanced filtering and pagination
- Real-time order updates with WebSocket
- Report generation
- Multi-outlet support

## 📄 License

MIT License

---

**Built with ❤️ using Go Fiber**
