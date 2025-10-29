# Bug Fix Documentation - POS System

## Date: October 29, 2025

---

## 📋 Issues Summary

The POS System application experienced several critical errors preventing proper functionality:

1. **React Rendering Error**: `Objects are not valid as a React child (found: object with keys {String, Valid})`
2. **Undefined API Error**: All API calls going to `/undefined/...`
3. **Products Filter Error**: `products.filter is not a function`
4. **Coupons 404 Error**: Endpoint `/api/coupons/available` not found

---

## 🔧 Fixes Applied

### 1. React Object Rendering Error

**📌 Problem:**
- Go backend was returning `sql.NullString` types that serialize as objects `{String: "value", Valid: true}`
- React cannot render these objects as text
- Error occurred when trying to display `user.full_name` in Layout component

**✅ Solution:**
- Added helper functions to convert `sql.NullString` to plain strings:
  - `getNullString()` - Convert sql.NullString to string
  - `getNullInt()` - Convert sql.NullInt64 to *int
  - `getNullBool()` - Convert sql.NullBool to *bool
  - `getNullTime()` - Convert sql.NullTime to *string

- Updated `StaffLogin` handler in `/app/backend/handlers.go` (lines 185-196):
```go
return c.JSON(fiber.Map{
    "success": true,
    "token":   token,
    "user": fiber.Map{
        "id":        user.ID,
        "full_name": getNullString(user.FullName),  // ✅ Fixed
        "username":  user.Username,
        "email":     getNullString(user.Email),     // ✅ Fixed
        "role":      roleStr,
        "role_id":   getNullInt(user.RoleID),       // ✅ Added
        "outlet_id": getNullInt(user.OutletID),     // ✅ Added
    },
})
```

- Updated `GetCurrentUser` handler in `/app/backend/handlers.go` (lines 198-230):
```go
return c.JSON(fiber.Map{
    "success": true,
    "user": fiber.Map{
        "id":         user.ID,
        "full_name":  getNullString(user.FullName),
        "username":   user.Username,
        "email":      getNullString(user.Email),
        "role":       getNullString(user.Role),
        "role_id":    getNullInt(user.RoleID),
        "outlet_id":  getNullInt(user.OutletID),
        "is_active":  getNullBool(user.IsActive),
        "created_at": getNullTime(user.CreatedAt),
    },
})
```

**📁 Files Modified:**
- `/app/backend/handlers.go`

---

### 2. API Calls to /undefined/...

**📌 Problem:**
- Frontend was missing `.env` file
- `process.env.REACT_APP_BACKEND_URL` was returning `undefined`
- All API calls became `/undefined/products`, `/undefined/coupons`, etc.
- Caused 404 errors on all endpoints

**✅ Solution:**
- Created `/app/frontend/.env` file with configuration:
```env
REACT_APP_BACKEND_URL=/api
```

- Using relative path `/api` to:
  - Avoid CORS issues
  - Route requests through same domain
  - Let nginx proxy automatically route to backend port 8001

**📁 Files Created:**
- `/app/frontend/.env`

**⚠️ Important Note:**
- React only reads environment variables at **build/start time**, not runtime
- Any `.env` changes require **frontend restart**:
```bash
pkill -f "yarn start"
cd /app/frontend && yarn start > /var/log/frontend.log 2>&1 &
```

---

### 3. Route Ordering - Coupons Available 404

**📌 Problem:**
- Route `/api/coupons/available` was defined AFTER `/api/coupons/:id`
- Router treated "available" as an ID parameter
- Caused 404 error

**✅ Solution:**
- Moved route `/api/coupons/available` BEFORE `/api/coupons/:id` in `/app/backend/routes.go`:

```go
// Coupons - correct order
api.Get("/coupons/available", GetAvailableCoupons)  // ✅ Specific route first
api.Get("/coupons", GetCoupons)
api.Get("/coupons/:id", GetCoupon)                   // ✅ Dynamic route last
api.Post("/coupons", AuthMiddleware, CreateCoupon)
api.Put("/coupons/:id", AuthMiddleware, UpdateCoupon)
api.Delete("/coupons/:id", AuthMiddleware, DeleteCoupon)
```

**📁 Files Modified:**
- `/app/backend/routes.go` (lines 76-82)

**💡 Route Ordering Principle:**
- More specific routes must be defined BEFORE routes with dynamic parameters
- Pattern: `/resource/specific` → `/resource` → `/resource/:id`

---

### 4. Frontend Array Handling

**📌 Problem:**
- Backend returns wrapped response: `{success: true, products: [...]}`
- Frontend was setting state to entire response object
- Caused `.filter is not a function` error because products wasn't an array

**✅ Solution:**
- Extract array from response.data in all components:

**CustomerMenu.jsx:**
```javascript
const fetchProducts = async () => {
  const response = await axiosInstance.get('/products');
  setProducts(response.data.products || []); // ✅ Extract array
};

const fetchCategories = async () => {
  const response = await axiosInstance.get('/categories');
  setCategories(response.data.categories || []); // ✅ Extract array
};
```

**Kiosk.jsx:**
```javascript
const response = await axiosInstance.get('/products');
setProducts(response.data.products || []);
```

**POSCashier.jsx:**
```javascript
const response = await axiosInstance.get('/products');
setProducts(response.data.products || []);
```

**CustomerOrders.jsx:**
```javascript
const response = await axiosInstance.get(`/orders?customer_id=${user.id}`);
setOrders(response.data.orders || []);
```

**📁 Files Modified:**
- `/app/frontend/src/pages/customer/CustomerMenu.jsx`
- `/app/frontend/src/pages/Kiosk.jsx`
- `/app/frontend/src/pages/POSCashier.jsx`
- `/app/frontend/src/pages/customer/CustomerOrders.jsx`

---

## 🚀 How to Rebuild & Restart Services

### Backend (Go Fiber)

```bash
# 1. Install Go (if not already installed)
cd /tmp
wget https://go.dev/dl/go1.23.4.linux-amd64.tar.gz
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf go1.23.4.linux-amd64.tar.gz

# 2. Build server
cd /app/backend
/usr/local/go/bin/go build -o server .

# 3. Stop & restart backend
pkill -f "./server"
./server > /var/log/fiber-backend.log 2>&1 &

# 4. Verify backend is running
curl http://localhost:8001/api/health
```

### Frontend (React)

```bash
# 1. Stop frontend
pkill -f "yarn start"
pkill -f "react-scripts"

# 2. Install dependencies (if needed)
cd /app/frontend
yarn install

# 3. Start frontend
yarn start > /var/log/frontend.log 2>&1 &

# 4. Verify frontend is running
curl http://localhost:3000
```

---

## 📊 Final Status

### ✅ Backend (Port 8001)
- ✅ Health check: `http://localhost:8001/api/health`
- ✅ All routes configured with correct ordering
- ✅ SQL null fields properly serialized
- ✅ Coupons available endpoint working
- ✅ Server binary rebuilt (Oct 29 22:28)

### ✅ Frontend (Port 3000)
- ✅ Environment variable set: `REACT_APP_BACKEND_URL=/api`
- ✅ Products API handling response correctly
- ✅ All API calls going to correct URLs
- ✅ No more `/undefined/...` errors

### ✅ All Issues Resolved
1. ✅ Route ordering fixed
2. ✅ User object serialization fixed in GetCurrentUser
3. ✅ User object serialization fixed in StaffLogin
4. ✅ Products array handling fixed
5. ✅ Backend URL environment variable set
6. ✅ Frontend restarted to load .env file

---

## 🔍 Testing Checklist

### Backend Testing
```bash
# Health check
curl http://localhost:8001/api/health

# Login test
curl -X POST http://localhost:8001/api/auth/staff/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# Products test
curl http://localhost:8001/api/products

# Coupons available test
curl http://localhost:8001/api/coupons/available
```

### Frontend Testing
1. Open browser console (F12)
2. Check for no `/undefined/...` errors
3. Verify API calls go to `/api/...`
4. Verify data displays correctly in UI
5. Test login and verify user info displays in Layout

---

## 📝 Important Notes for Developers

### Environment Variables
- **Backend**: Uses `.env` at `/app/backend/.env`
- **Frontend**: Uses `.env` at `/app/frontend/.env`
- ⚠️ **IMPORTANT**: Frontend must be restarted after `.env` changes!

### SQL Null Types in Go
- Always use helper functions:
  - `getNullString(sql.NullString)` → `string`
  - `getNullInt(sql.NullInt64)` → `*int`
  - `getNullBool(sql.NullBool)` → `*bool`
  - `getNullTime(sql.NullTime)` → `*string`

### Route Ordering Rules
1. Specific routes BEFORE dynamic routes
2. `/resource/action` → `/resource` → `/resource/:id`
3. Always test route ordering with curl

### Frontend Response Handling
- Backend returns wrapped response: `{success: true, data: {...}}`
- Always extract data: `response.data.products`, `response.data.orders`, etc.
- Use fallback: `response.data.products || []`

---

## 🐛 Troubleshooting

### If still getting `/undefined/...` errors:
```bash
# 1. Check .env file exists
ls -la /app/frontend/.env
cat /app/frontend/.env

# 2. Restart frontend
pkill -f "yarn start"
cd /app/frontend && yarn start > /var/log/frontend.log 2>&1 &

# 3. Check logs
tail -f /var/log/frontend.log
```

### If backend won't start:
```bash
# 1. Check logs
tail -50 /var/log/fiber-backend.log

# 2. Rebuild
cd /app/backend
/usr/local/go/bin/go build -o server .

# 3. Restart
pkill -f "./server"
./server > /var/log/fiber-backend.log 2>&1 &
```

### If React still errors "Objects are not valid as React child":
```bash
# 1. Clear localStorage in browser
localStorage.clear()

# 2. Login again to get fresh user object

# 3. Check backend response
curl -X POST http://localhost:8001/api/auth/staff/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq
```

---

## 📧 Contact & Support

If issues persist:
- Check logs: `/var/log/fiber-backend.log` and `/var/log/frontend.log`
- Verify services running: `ps aux | grep -E "(server|yarn)"`
- Test endpoints with curl as shown in Testing Checklist

---

**Documentation created by:** AI Assistant  
**Date:** October 29, 2025  
**Version:** 1.0
