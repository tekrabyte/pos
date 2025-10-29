<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\PaymentMethod;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

class PaymentMethodController extends Controller
{
    public function index()
    {
        $methods = PaymentMethod::all();
        
        return response()->json([
            'success' => true,
            'payment_methods' => $methods
        ]);
    }

    public function show($id)
    {
        $method = PaymentMethod::find($id);
        
        if (!$method) {
            return response()->json([
                'success' => false,
                'message' => 'Metode pembayaran tidak ditemukan'
            ], 404);
        }
        
        return response()->json([
            'success' => true,
            'payment_method' => $method
        ]);
    }

    public function store(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'name' => 'required|string|max:100',
            'type' => 'required|string|in:cash,qris,card,transfer',
            'is_active' => 'nullable|boolean',
            'config' => 'nullable|array',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        $method = PaymentMethod::create($request->all());
        
        return response()->json([
            'success' => true,
            'message' => 'Metode pembayaran berhasil ditambahkan',
            'payment_method' => $method
        ], 201);
    }

    public function update(Request $request, $id)
    {
        $method = PaymentMethod::find($id);
        
        if (!$method) {
            return response()->json([
                'success' => false,
                'message' => 'Metode pembayaran tidak ditemukan'
            ], 404);
        }

        $validator = Validator::make($request->all(), [
            'name' => 'required|string|max:100',
            'type' => 'required|string|in:cash,qris,card,transfer',
            'is_active' => 'nullable|boolean',
            'config' => 'nullable|array',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        $method->update($request->all());
        
        return response()->json([
            'success' => true,
            'message' => 'Metode pembayaran berhasil diupdate',
            'payment_method' => $method
        ]);
    }

    public function destroy($id)
    {
        $method = PaymentMethod::find($id);
        
        if (!$method) {
            return response()->json([
                'success' => false,
                'message' => 'Metode pembayaran tidak ditemukan'
            ], 404);
        }
        
        $method->delete();
        
        return response()->json([
            'success' => true,
            'message' => 'Metode pembayaran berhasil dihapus'
        ]);
    }
}
