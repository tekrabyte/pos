<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Coupon;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;
use Carbon\Carbon;

class CouponController extends Controller
{
    public function index()
    {
        $coupons = Coupon::all();
        
        return response()->json([
            'success' => true,
            'coupons' => $coupons
        ]);
    }

    public function show($id)
    {
        $coupon = Coupon::find($id);
        
        if (!$coupon) {
            return response()->json([
                'success' => false,
                'message' => 'Kupon tidak ditemukan'
            ], 404);
        }
        
        return response()->json([
            'success' => true,
            'coupon' => $coupon
        ]);
    }

    public function store(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'code' => 'required|string|unique:coupons,code',
            'discount_type' => 'required|string|in:percentage,fixed',
            'discount_value' => 'required|numeric|min:0',
            'min_purchase' => 'nullable|numeric|min:0',
            'max_discount' => 'nullable|numeric|min:0',
            'start_date' => 'nullable|date',
            'end_date' => 'nullable|date|after:start_date',
            'usage_limit' => 'nullable|integer|min:0',
            'is_active' => 'nullable|boolean',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        $coupon = Coupon::create([
            'code' => strtoupper($request->code),
            'discount_type' => $request->discount_type,
            'discount_value' => $request->discount_value,
            'min_purchase' => $request->min_purchase,
            'max_discount' => $request->max_discount,
            'start_date' => $request->start_date,
            'end_date' => $request->end_date,
            'usage_limit' => $request->usage_limit,
            'used_count' => 0,
            'is_active' => $request->is_active ?? true,
        ]);
        
        return response()->json([
            'success' => true,
            'message' => 'Kupon berhasil ditambahkan',
            'coupon' => $coupon
        ], 201);
    }

    public function update(Request $request, $id)
    {
        $coupon = Coupon::find($id);
        
        if (!$coupon) {
            return response()->json([
                'success' => false,
                'message' => 'Kupon tidak ditemukan'
            ], 404);
        }

        $validator = Validator::make($request->all(), [
            'code' => 'required|string|unique:coupons,code,' . $id,
            'discount_type' => 'required|string|in:percentage,fixed',
            'discount_value' => 'required|numeric|min:0',
            'min_purchase' => 'nullable|numeric|min:0',
            'max_discount' => 'nullable|numeric|min:0',
            'start_date' => 'nullable|date',
            'end_date' => 'nullable|date|after:start_date',
            'usage_limit' => 'nullable|integer|min:0',
            'is_active' => 'nullable|boolean',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        $coupon->update($request->all());
        
        return response()->json([
            'success' => true,
            'message' => 'Kupon berhasil diupdate',
            'coupon' => $coupon
        ]);
    }

    public function destroy($id)
    {
        $coupon = Coupon::find($id);
        
        if (!$coupon) {
            return response()->json([
                'success' => false,
                'message' => 'Kupon tidak ditemukan'
            ], 404);
        }
        
        $coupon->delete();
        
        return response()->json([
            'success' => true,
            'message' => 'Kupon berhasil dihapus'
        ]);
    }

    public function validate(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'code' => 'required|string',
            'total_amount' => 'required|numeric|min:0',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        $coupon = Coupon::where('code', strtoupper($request->code))
            ->where('is_active', true)
            ->first();

        if (!$coupon) {
            return response()->json([
                'success' => false,
                'message' => 'Kupon tidak valid atau tidak aktif'
            ], 404);
        }

        // Check date validity
        $now = Carbon::now();
        if ($coupon->start_date && $now->lt($coupon->start_date)) {
            return response()->json([
                'success' => false,
                'message' => 'Kupon belum dapat digunakan'
            ], 400);
        }

        if ($coupon->end_date && $now->gt($coupon->end_date)) {
            return response()->json([
                'success' => false,
                'message' => 'Kupon sudah kadaluarsa'
            ], 400);
        }

        // Check usage limit
        if ($coupon->usage_limit && $coupon->used_count >= $coupon->usage_limit) {
            return response()->json([
                'success' => false,
                'message' => 'Kupon sudah mencapai batas penggunaan'
            ], 400);
        }

        // Check minimum purchase
        if ($coupon->min_purchase && $request->total_amount < $coupon->min_purchase) {
            return response()->json([
                'success' => false,
                'message' => 'Minimum pembelian Rp ' . number_format($coupon->min_purchase, 0, ',', '.') . ' untuk menggunakan kupon ini'
            ], 400);
        }

        // Calculate discount
        $discountAmount = 0;
        if ($coupon->discount_type === 'percentage') {
            $discountAmount = ($request->total_amount * $coupon->discount_value) / 100;
            if ($coupon->max_discount && $discountAmount > $coupon->max_discount) {
                $discountAmount = $coupon->max_discount;
            }
        } else {
            $discountAmount = $coupon->discount_value;
        }

        return response()->json([
            'success' => true,
            'message' => 'Kupon valid',
            'coupon' => $coupon,
            'discount_amount' => $discountAmount,
            'final_amount' => $request->total_amount - $discountAmount
        ]);
    }
}
