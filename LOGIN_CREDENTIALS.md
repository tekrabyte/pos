# 🔐 Login Credentials - POS System

## Default Staff/Admin Login

### ✅ Working Credentials (TESTED)

```
Username: admin
Password: admin123
```

**Role:** Administrator (Full Access)

---

## 🧪 How to Test Login

### Method 1: Via Browser
1. Buka: `https://payment-portal-101.preview.emergentagent.com/staff/login`
2. Enter credentials:
   - Username: `admin`
   - Password: `admin123`
3. Click "Login"
4. Should redirect to `/dashboard`

### Method 2: Via cURL (Backend Direct)
```bash
curl -X POST http://localhost:8001/api/auth/staff/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Expected Response:**
```json
{
  "success": true,
  "token": "eyJhbGci...",
  "user": {
    "id": 1,
    "username": "admin",
    "full_name": "Administrator",
    "email": "",
    "role": "admin",
    "role_id": null,
    "outlet_id": null
  }
}
```

---

## ⚠️ Important Notes

### Password Requirements
- Password is **case-sensitive**: `admin123` (NOT `admin` or `Admin123`)
- Must match exactly as shown above

### Common Login Issues

#### ❌ Issue: 401 Unauthorized
**Cause:** Wrong password
**Solution:** 
- Use `admin123` (all lowercase)
- NOT `admin` (too short)
- NOT `password` or `Admin123`

#### ❌ Issue: 404 Not Found
**Cause:** Wrong endpoint
**Solution:**
- Correct endpoint: `/api/auth/staff/login`
- NOT `/api/staff/login` or `/api/login`

#### ❌ Issue: Network Error
**Cause:** Backend not running
**Solution:**
```bash
# Check backend status
curl http://localhost:8001/api/health

# If not running, start it
cd /app/backend && ./server > /var/log/fiber-backend.log 2>&1 &
```

---

## 🔄 How to Create New Staff Users

Currently, users must be created directly in the database. To add a new staff user:

### Option 1: Via Database (MySQL)
```sql
-- Connect to database
mysql -h srv1412.hstgr.io -P 3306 -u u215947863_pos_dev -p'Pos_dev123#' u215947863_pos_dev

-- Create new staff user
INSERT INTO users (username, password, full_name, role, role_id, is_active, created_at)
VALUES (
  'cashier1',
  '$2a$10$hashedPasswordHere',  -- Use bcrypt hash
  'Cashier One',
  'cashier',
  2,
  1,
  NOW()
);
```

### Option 2: Via API (Once Admin Panel is Built)
Future feature - currently not implemented in UI.

---

## 🔐 Password Security

### Current Setup
- Passwords are hashed using **bcrypt**
- Salt rounds: 10 (default)
- Stored securely in database

### Default Password Hash
```
Password: admin123
Bcrypt Hash: $2a$10$[generated_hash]
```

**DO NOT store passwords in plain text!**

---

## 📝 Customer Login (Separate)

For customer-facing app:

```
Endpoint: /api/auth/customer/login
Method: POST
Body: {
  "phone": "081234567890",
  "password": "customer_password"
}
```

**Note:** Customer login uses phone number instead of username.

---

## 🚨 Troubleshooting

### Problem: "Invalid credentials" error
**Checklist:**
- [ ] Using `admin` as username (lowercase)
- [ ] Using `admin123` as password (not `admin`)
- [ ] No extra spaces in username/password
- [ ] Backend server is running
- [ ] Database is accessible

### Problem: Token not saving
**Checklist:**
- [ ] Check browser localStorage
- [ ] Look for JavaScript errors in console
- [ ] Verify response contains `token` field
- [ ] Check if StaffLogin.jsx saves to localStorage

### Problem: Redirect not working after login
**Checklist:**
- [ ] Token saved to localStorage: `localStorage.getItem('token')`
- [ ] User saved to localStorage: `localStorage.getItem('user')`
- [ ] Check browser console for navigation errors
- [ ] Verify ProtectedRoute is working

---

## 📞 Need Help?

If login still fails after trying above credentials:

1. **Check backend logs:**
```bash
tail -50 /var/log/fiber-backend.log
```

2. **Verify database connection:**
```bash
curl http://localhost:8001/api/health
```

3. **Test with cURL first** (to isolate frontend vs backend issues)

4. **Check browser console** for detailed error messages

---

## ✅ Quick Test Checklist

- [ ] Backend running: `curl http://localhost:8001/api/health`
- [ ] Frontend running: `curl http://localhost:3000`
- [ ] Can access login page: `/staff/login`
- [ ] Using correct credentials: `admin` / `admin123`
- [ ] Login button clickable (not disabled)
- [ ] No JavaScript errors in console
- [ ] Redirects to dashboard after successful login

---

**Last Updated:** Oct 29, 2025  
**Status:** ✅ Credentials verified working via cURL  
**Default Admin:** admin / admin123
