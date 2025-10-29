<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\StaffAuthController;
use App\Http\Controllers\Api\CustomerAuthController;
use App\Http\Controllers\Api\ProductController;
use App\Http\Controllers\Api\CategoryController;
use App\Http\Controllers\Api\BrandController;
use App\Http\Controllers\Api\OrderController;
use App\Http\Controllers\Api\TableController;
use App\Http\Controllers\Api\CustomerController;
use App\Http\Controllers\Api\CouponController;
use App\Http\Controllers\Api\OutletController;
use App\Http\Controllers\Api\RoleController;
use App\Http\Controllers\Api\PaymentMethodController;
use App\Http\Controllers\Api\BankAccountController;
use App\Http\Controllers\Api\StoreSettingController;
use App\Http\Controllers\Api\StoreBannerController;
use App\Http\Controllers\Api\DashboardController;
use App\Http\Controllers\Api\QrisController;
use App\Http\Controllers\Api\UploadController;
use App\Http\Controllers\Api\PaymentSettingController;

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
        'timestamp' => now()->toDateTimeString(),
        'version' => '1.0.0'
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
| Order Management Routes
|--------------------------------------------------------------------------
*/
Route::apiResource('orders', OrderController::class);
Route::put('orders/{id}/status', [OrderController::class, 'updateStatus']);

Route::apiResource('tables', TableController::class);
Route::post('tables/{id}/regenerate-qr', [TableController::class, 'regenerateQr']);

/*
|--------------------------------------------------------------------------
| Customer Management Routes
|--------------------------------------------------------------------------
*/
Route::apiResource('customers', CustomerController::class);
Route::post('customer/change-password', [CustomerController::class, 'changePassword']);

Route::apiResource('coupons', CouponController::class);
Route::get('coupons/available', [CouponController::class, 'available']);
Route::post('coupons/validate', [CouponController::class, 'validate']);

/*
|--------------------------------------------------------------------------
| Settings Routes
|--------------------------------------------------------------------------
*/
Route::apiResource('outlets', OutletController::class);
Route::apiResource('roles', RoleController::class);
Route::apiResource('payment-methods', PaymentMethodController::class);
Route::apiResource('bank-accounts', BankAccountController::class);

/*
|--------------------------------------------------------------------------
| Store & Banner Routes
|--------------------------------------------------------------------------
*/
Route::get('store-settings', [StoreSettingController::class, 'index']);
Route::put('store-settings', [StoreSettingController::class, 'update']);

Route::get('store-banners', [StoreBannerController::class, 'index']);
Route::get('store-banners/all', [StoreBannerController::class, 'all']);
Route::apiResource('banners', StoreBannerController::class)->except(['index']);

/*
|--------------------------------------------------------------------------
| Analytics & Dashboard Routes
|--------------------------------------------------------------------------
*/
Route::get('dashboard/stats', [DashboardController::class, 'stats']);
Route::get('analytics', [DashboardController::class, 'analytics']);

/*
|--------------------------------------------------------------------------
| QRIS Routes
|--------------------------------------------------------------------------
*/
Route::post('qris/generate', [QrisController::class, 'generate']);
Route::post('qris/check-status', [QrisController::class, 'checkStatus']);

/*
|--------------------------------------------------------------------------
| Upload Routes
|--------------------------------------------------------------------------
*/
Route::post('upload/payment-proof', [UploadController::class, 'uploadPaymentProof']);
Route::post('upload/qris', [UploadController::class, 'uploadQris']);
Route::post('upload/product-image', [UploadController::class, 'uploadProductImage']);

/*
|--------------------------------------------------------------------------
| Payment Settings Routes
|--------------------------------------------------------------------------
*/
Route::get('payment-settings/qris', [PaymentSettingController::class, 'getQrisSettings']);
Route::post('payment-settings/qris', [PaymentSettingController::class, 'updateQrisSettings']);
