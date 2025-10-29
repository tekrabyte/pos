<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Facades\Validator;
use Illuminate\Support\Str;

class UploadController extends Controller
{
    public function uploadPaymentProof(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'file' => 'required|image|mimes:jpeg,png,jpg|max:2048',
            'order_id' => 'required|string',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        try {
            $file = $request->file('file');
            $filename = 'payment_proof_' . time() . '_' . Str::random(8) . '.' . $file->getClientOriginalExtension();
            
            // Store in public/uploads/payment_proofs directory
            $path = $file->storeAs('payment_proofs', $filename, 'public');
            $url = Storage::url($path);

            return response()->json([
                'success' => true,
                'message' => 'Bukti pembayaran berhasil diupload',
                'file_path' => $path,
                'file_url' => $url,
                'filename' => $filename
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Gagal upload file: ' . $e->getMessage()
            ], 500);
        }
    }

    public function uploadQris(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'file' => 'required|image|mimes:jpeg,png,jpg|max:2048',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        try {
            $file = $request->file('file');
            $filename = 'qris_' . time() . '_' . Str::random(8) . '.' . $file->getClientOriginalExtension();
            
            // Store in public/uploads/qris directory
            $path = $file->storeAs('qris', $filename, 'public');
            $url = Storage::url($path);

            return response()->json([
                'success' => true,
                'message' => 'QRIS image berhasil diupload',
                'file_path' => $path,
                'file_url' => $url,
                'filename' => $filename
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Gagal upload file: ' . $e->getMessage()
            ], 500);
        }
    }

    public function uploadProductImage(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'file' => 'required|image|mimes:jpeg,png,jpg|max:2048',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        try {
            $file = $request->file('file');
            $filename = 'product_' . time() . '_' . Str::random(8) . '.' . $file->getClientOriginalExtension();
            
            // Store in public/uploads/products directory
            $path = $file->storeAs('products', $filename, 'public');
            $url = Storage::url($path);

            return response()->json([
                'success' => true,
                'message' => 'Product image berhasil diupload',
                'file_path' => $path,
                'file_url' => $url,
                'filename' => $filename
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Gagal upload file: ' . $e->getMessage()
            ], 500);
        }
    }
}
