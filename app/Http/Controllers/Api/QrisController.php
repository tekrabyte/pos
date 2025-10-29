<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;
use Illuminate\Support\Str;

class QrisController extends Controller
{
    public function generate(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'amount' => 'required|numeric|min:0',
            'order_id' => 'nullable|string',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        // Generate dummy QRIS code (in production, integrate with real QRIS provider)
        $qrisCode = 'QRIS-' . strtoupper(Str::random(16));
        $expiresAt = now()->addMinutes(15);
        
        // Generate QR code data (simplified)
        $qrData = [
            'merchant_id' => config('app.merchant_id', 'MERCHANT001'),
            'amount' => $request->amount,
            'order_id' => $request->order_id ?? 'ORD-' . time(),
            'qris_code' => $qrisCode,
            'expires_at' => $expiresAt->toIso8601String()
        ];

        return response()->json([
            'success' => true,
            'qris_code' => $qrisCode,
            'qr_data' => json_encode($qrData),
            'amount' => $request->amount,
            'expires_at' => $expiresAt->toDateTimeString(),
            'message' => 'QRIS berhasil di-generate'
        ]);
    }

    public function checkStatus(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'qris_code' => 'required|string',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        // Mock payment status check
        // In production, check with actual QRIS provider
        return response()->json([
            'success' => true,
            'status' => 'pending', // pending, paid, expired
            'message' => 'Status pembayaran QRIS'
        ]);
    }
}
