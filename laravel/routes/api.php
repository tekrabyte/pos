<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\StaffAuthController;
use App\Http\Controllers\Api\CustomerAuthController;
use App\Http\Controllers\Api\ProductController;
use App\Http\Controllers\Api\CategoryController;
use App\Http\Controllers\Api\BrandController;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
*/

// Health Check
Route::get('/health', function () {
    return response()->json([
        'status' => 'OK',
        'message' => 'Laravel POS API is running',
        'timestamp' => now()->toDateTimeString()
    ]);
});

/*
|--------------------------------------------------------------------------
| Authentication Routes
|--------------------------------------------------------------------------
*/

// Staff Auth
Route::prefix('auth/staff')->group(function () {
    Route::post('/login', [StaffAuthController::class, 'login']);
    Route::middleware('auth:api')->group(function () {
        Route::get('/me', [StaffAuthController::class, 'me']);
        Route::post('/logout', [StaffAuthController::class, 'logout']);
    });
});

// Customer Auth
Route::prefix('auth/customer')->group(function () {
    Route::post('/login', [CustomerAuthController::class, 'login']);
    Route::post('/register', [CustomerAuthController::class, 'register']);
    Route::post('/forgot-password', [CustomerAuthController::class, 'forgotPassword']);
    Route::post('/reset-password', [CustomerAuthController::class, 'resetPassword']);
    
    Route::middleware('auth:api')->group(function () {
        Route::get('/me', [CustomerAuthController::class, 'me']);
        Route::post('/logout', [CustomerAuthController::class, 'logout']);
    });
});

/*
|--------------------------------------------------------------------------
| Product Management Routes
|--------------------------------------------------------------------------
*/
Route::apiResource('products', ProductController::class);
Route::apiResource('categories', CategoryController::class);
Route::apiResource('brands', BrandController::class);

/*
|--------------------------------------------------------------------------
| Order Management Routes (To be implemented)
|--------------------------------------------------------------------------
*/
// Route::apiResource('orders', OrderController::class);
// Route::apiResource('tables', TableController::class);

/*
|--------------------------------------------------------------------------
| Customer Management Routes (To be implemented)
|--------------------------------------------------------------------------
*/
// Route::apiResource('customers', CustomerController::class);
// Route::apiResource('coupons', CouponController::class);

/*
|--------------------------------------------------------------------------
| Settings Routes (To be implemented)
|--------------------------------------------------------------------------
*/
// Route::apiResource('outlets', OutletController::class);
// Route::apiResource('roles', RoleController::class);
// Route::apiResource('payment-methods', PaymentMethodController::class);
// Route::apiResource('payment-settings', PaymentSettingController::class);
// Route::apiResource('bank-accounts', BankAccountController::class);

/*
|--------------------------------------------------------------------------
| Store & Banner Routes (To be implemented)
|--------------------------------------------------------------------------
*/
// Route::get('store-settings', [StoreSettingController::class, 'index']);
// Route::put('store-settings', [StoreSettingController::class, 'update']);
// Route::apiResource('store-banners', StoreBannerController::class);

/*
|--------------------------------------------------------------------------
| Analytics & Dashboard Routes (To be implemented)
|--------------------------------------------------------------------------
*/
// Route::get('dashboard/stats', [DashboardController::class, 'stats']);
// Route::get('analytics', [AnalyticsController::class, 'index']);
