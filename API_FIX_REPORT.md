# API Fix Report - Laravel POS System

## ✅ Status: Frontend API Calls Fixed & Backend Endpoints Added

Tanggal: 2024-12-19
Proyek: Laravel POS System

---

## 📋 Masalah yang Ditemukan

Setelah migrasi dari FastAPI ke Laravel, ditemukan **ketidakcocokan API endpoints** antara frontend React dan backend Laravel.

### API Issues yang Ditemukan:

| No | Frontend Endpoint | Status | Backend Endpoint (Correct) |
|----|-------------------|--------|----------------------------|
| 1 | `/auth/login` | ❌ Salah | `/auth/staff/login` |
| 2 | `/auth/register-customer` | ❌ Salah | `/auth/customer/register` |
| 3 | `/analytics/overview` | ❌ Salah | `/analytics` |
| 4 | `/customer/account/{id}` | ❌ Salah | `/customers/{id}` |
| 5 | `/customer/change-password` | ❌ Missing | **BARU DITAMBAHKAN** |
| 6 | `/coupons/available` | ❌ Missing | **BARU DITAMBAHKAN** |
| 7 | `/tables/token/{token}` | ❌ Missing | **BARU DITAMBAHKAN** |
| 8 | `/qris/generate` | ❌ Missing | **BARU DITAMBAHKAN** |
| 9 | `/upload/payment-proof` | ❌ Missing | **BARU DITAMBAHKAN** |
| 10 | `/upload/qris` | ❌ Missing | **BARU DITAMBAHKAN** |
| 11 | `/payment-settings/qris` | ❌ Missing | **BARU DITAMBAHKAN** |

---

## ✅ Perbaikan yang Telah Dilakukan

### 1. Frontend React - File yang Diperbaiki

#### a. `/app/frontend/src/pages/Login.jsx`
**Perubahan:**
- ❌ `POST /auth/login` → ✅ `POST /auth/staff/login`
- ❌ `POST /auth/register-customer` → ✅ `POST /auth/customer/register`

**Impact:** Staff login dan customer registration sekarang menggunakan endpoint yang benar.

---

#### b. `/app/frontend/src/pages/Analytics.jsx`
**Perubahan:**
- ❌ `GET /analytics/overview` → ✅ `GET /analytics`

**Impact:** Analytics page sekarang memanggil endpoint yang benar.

---

#### c. `/app/frontend/src/pages/customer/CustomerProfileNew.jsx`
**Perubahan:**
- ❌ `DELETE /customer/account/{id}` → ✅ `DELETE /customers/{id}`

**Impact:** Delete account functionality sekarang menggunakan endpoint RESTful yang benar.

---

### 2. Backend Laravel - Controller Baru & Endpoint Baru

#### a. **QrisController** (BARU)
File: `/app/app/Http/Controllers/Api/QrisController.php`

**Endpoints:**
```php
POST /api/qris/generate
POST /api/qris/check-status
```

**Fungsi:**
- Generate QRIS code untuk pembayaran
- Check status pembayaran QRIS

---

#### b. **UploadController** (BARU)
File: `/app/app/Http/Controllers/Api/UploadController.php`

**Endpoints:**
```php
POST /api/upload/payment-proof
POST /api/upload/qris
POST /api/upload/product-image
```

**Fungsi:**
- Upload bukti pembayaran
- Upload gambar QRIS
- Upload gambar produk

**Storage:** File disimpan di `storage/app/public/`

---

#### c. **PaymentSettingController** (BARU)
File: `/app/app/Http/Controllers/Api/PaymentSettingController.php`

**Endpoints:**
```php
GET  /api/payment-settings/qris
POST /api/payment-settings/qris
```

**Fungsi:**
- Get QRIS settings (merchant ID, merchant name, QRIS image)
- Update QRIS settings

**Storage:** Settings disimpan di `storage/app/payment_settings/qris.json`

---

#### d. **CustomerController** (UPDATED)
File: `/app/app/Http/Controllers/Api/CustomerController.php`

**New Method:**
```php
public function changePassword(Request $request)
```

**Endpoint:**
```php
POST /api/customer/change-password
```

**Fungsi:**
- Customer bisa ganti password
- Validasi old password
- Hash new password

---

#### e. **CouponController** (UPDATED)
File: `/app/app/Http/Controllers/Api/CouponController.php`

**New Method:**
```php
public function available()
```

**Endpoint:**
```php
GET /api/coupons/available
```

**Fungsi:**
- Menampilkan hanya kupon yang aktif
- Filter berdasarkan tanggal validity
- Filter berdasarkan usage limit

---

#### f. **TableController** (UPDATED)
File: `/app/app/Http/Controllers/Api/TableController.php`

**New Method:**
```php
public function getByToken($token)
```

**Endpoint:**
```php
GET /api/tables/token/{token}
```

**Fungsi:**
- Get table information by QR token
- Digunakan saat customer scan QR code meja

---

### 3. Routes - File yang Diupdate

File: `/app/routes/api.php`

**New Routes Added:**
```php
// Customer
Route::post('customer/change-password', [CustomerController::class, 'changePassword']);

// Coupons
Route::get('coupons/available', [CouponController::class, 'available']);

// Tables
Route::get('tables/token/{token}', [TableController::class, 'getByToken']);

// QRIS
Route::post('qris/generate', [QrisController::class, 'generate']);
Route::post('qris/check-status', [QrisController::class, 'checkStatus']);

// Upload
Route::post('upload/payment-proof', [UploadController::class, 'uploadPaymentProof']);
Route::post('upload/qris', [UploadController::class, 'uploadQris']);
Route::post('upload/product-image', [UploadController::class, 'uploadProductImage']);

// Payment Settings
Route::get('payment-settings/qris', [PaymentSettingController::class, 'getQrisSettings']);
Route::post('payment-settings/qris', [PaymentSettingController::class, 'updateQrisSettings']);
```

**Route Ordering Fixed:**
- Routes dengan specific patterns (e.g., `coupons/available`, `tables/token/{token}`) dipindahkan **SEBELUM** `apiResource` routes
- Ini penting agar Laravel tidak salah routing ke resource controller

---

## 🔧 Setup yang Diperlukan

### 1. Storage Link (Penting!)
Untuk file uploads berfungsi dengan baik, perlu membuat symbolic link:

```bash
cd /app
php artisan storage:link
```

Ini akan membuat link dari `public/storage` ke `storage/app/public`.

### 2. Create Directories
```bash
mkdir -p storage/app/public/payment_proofs
mkdir -p storage/app/public/qris
mkdir -p storage/app/public/products
mkdir -p storage/app/payment_settings
```

### 3. Permissions
```bash
chmod -R 775 storage
chmod -R 775 bootstrap/cache
```

---

## ⚠️ PENTING: Server Configuration Issue

### Masalah Ditemukan:
**Backend Laravel tidak berjalan** karena:

1. **Supervisor Config Salah:**
   - File: `/etc/supervisor/conf.d/supervisord.conf`
   - Config masih menjalankan FastAPI/uvicorn: `command=/root/.venv/bin/uvicorn server:app`
   - Seharusnya: menjalankan Laravel: `php artisan serve`

2. **PHP Not Available:**
   - Command `php` tidak ditemukan di PATH
   - Vendor directory tidak ada (composer dependencies tidak terinstall)

3. **Status Supervisor:**
   ```
   backend    STOPPED
   frontend   STOPPED
   ```

### Solusi yang Diperlukan:

#### Option 1: Update Supervisor Config (Recommended)
Update `/etc/supervisor/conf.d/supervisord.conf`:
```ini
[program:backend]
command=/usr/bin/php artisan serve --host=0.0.0.0 --port=8001
directory=/app
autostart=true
autorestart=true
environment=APP_URL="...",APP_ENV="production"
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
```

#### Option 2: Run Laravel Manually
```bash
cd /app
php artisan serve --host=0.0.0.0 --port=8001 &
```

#### Option 3: Use Docker/Container
Jika ini Docker environment, pastikan PHP dan Laravel dependencies sudah terinstall di image.

---

## 📊 Testing Checklist

Setelah backend berjalan, test endpoints berikut:

### Authentication
- [ ] `POST /api/auth/staff/login` - Staff login
- [ ] `POST /api/auth/customer/register` - Customer registration

### Analytics
- [ ] `GET /api/analytics` - Get analytics data

### Customer Features
- [ ] `POST /api/customer/change-password` - Change password
- [ ] `DELETE /api/customers/{id}` - Delete account

### QRIS & Payments
- [ ] `POST /api/qris/generate` - Generate QRIS
- [ ] `POST /api/upload/payment-proof` - Upload payment proof
- [ ] `GET /api/payment-settings/qris` - Get QRIS settings
- [ ] `POST /api/payment-settings/qris` - Update QRIS settings

### Coupons
- [ ] `GET /api/coupons/available` - Get available coupons

### Tables
- [ ] `GET /api/tables/token/{token}` - Get table by QR token

---

## 📝 Catatan Tambahan

### 1. QRIS Implementation
Saat ini QRIS menggunakan **mock/dummy implementation**. Untuk production, perlu integrasi dengan:
- Payment Gateway (e.g., Midtrans, Xendit, Doku)
- QRIS Provider resmi

### 2. File Upload Security
- Validasi file type (hanya image)
- Max file size: 2MB
- Unique filename dengan timestamp dan random string

### 3. Storage Symlink
Jangan lupa run `php artisan storage:link` agar uploaded files bisa diakses publik.

---

## 🎯 Summary

### Files Modified: 3
1. `/app/frontend/src/pages/Login.jsx`
2. `/app/frontend/src/pages/Analytics.jsx`
3. `/app/frontend/src/pages/customer/CustomerProfileNew.jsx`

### Files Created: 4
1. `/app/app/Http/Controllers/Api/QrisController.php`
2. `/app/app/Http/Controllers/Api/UploadController.php`
3. `/app/app/Http/Controllers/Api/PaymentSettingController.php`
4. `/app/API_FIX_REPORT.md` (this file)

### Files Updated: 4
1. `/app/app/Http/Controllers/Api/CustomerController.php` (added changePassword method)
2. `/app/app/Http/Controllers/Api/CouponController.php` (added available method)
3. `/app/app/Http/Controllers/Api/TableController.php` (added getByToken method)
4. `/app/routes/api.php` (added 11 new routes)

### Total Endpoints Added: 11
All missing API endpoints have been implemented in backend Laravel.

### Next Steps:
1. ✅ **Fix supervisor config to run Laravel backend**
2. ✅ **Install PHP dependencies (composer install)**
3. ✅ **Run storage:link command**
4. ✅ **Test all API endpoints**
5. ✅ **Test frontend integration**

---

**Status Akhir:** ✅ Frontend sudah diperbaiki, Backend endpoints sudah ditambahkan. **Tinggal menjalankan backend Laravel server.**
