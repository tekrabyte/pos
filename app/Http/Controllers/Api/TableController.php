<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Table;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;
use SimpleSoftwareIO\QrCode\Facades\QrCode;
use Illuminate\Support\Str;

class TableController extends Controller
{
    public function index()
    {
        $tables = Table::all();
        
        return response()->json([
            'success' => true,
            'tables' => $tables
        ]);
    }

    public function show($id)
    {
        $table = Table::with('orders')->find($id);
        
        if (!$table) {
            return response()->json([
                'success' => false,
                'message' => 'Meja tidak ditemukan'
            ], 404);
        }
        
        return response()->json([
            'success' => true,
            'table' => $table
        ]);
    }

    public function store(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'table_number' => 'required|string|unique:tables,table_number',
            'capacity' => 'nullable|integer|min:1',
            'status' => 'nullable|string',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        // Generate QR token
        $qrToken = Str::random(32);
        
        // Generate QR Code (Base64 PNG)
        $qrCode = base64_encode(QrCode::format('png')
            ->size(300)
            ->generate(config('app.url') . '/kiosk?table=' . $qrToken));
        
        $table = Table::create([
            'table_number' => $request->table_number,
            'qr_code' => $qrCode,
            'qr_token' => $qrToken,
            'capacity' => $request->capacity ?? 4,
            'status' => $request->status ?? 'available',
        ]);
        
        return response()->json([
            'success' => true,
            'message' => 'Meja berhasil ditambahkan',
            'table' => $table
        ], 201);
    }

    public function update(Request $request, $id)
    {
        $table = Table::find($id);
        
        if (!$table) {
            return response()->json([
                'success' => false,
                'message' => 'Meja tidak ditemukan'
            ], 404);
        }

        $validator = Validator::make($request->all(), [
            'table_number' => 'required|string|unique:tables,table_number,' . $id,
            'capacity' => 'nullable|integer|min:1',
            'status' => 'nullable|string',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        $table->update($request->only(['table_number', 'capacity', 'status']));
        
        return response()->json([
            'success' => true,
            'message' => 'Meja berhasil diupdate',
            'table' => $table
        ]);
    }

    public function destroy($id)
    {
        $table = Table::find($id);
        
        if (!$table) {
            return response()->json([
                'success' => false,
                'message' => 'Meja tidak ditemukan'
            ], 404);
        }
        
        $table->delete();
        
        return response()->json([
            'success' => true,
            'message' => 'Meja berhasil dihapus'
        ]);
    }

    public function regenerateQr($id)
    {
        $table = Table::find($id);
        
        if (!$table) {
            return response()->json([
                'success' => false,
                'message' => 'Meja tidak ditemukan'
            ], 404);
        }
        
        // Generate new QR token
        $qrToken = Str::random(32);
        
        // Generate new QR Code
        $qrCode = base64_encode(QrCode::format('png')
            ->size(300)
            ->generate(config('app.url') . '/kiosk?table=' . $qrToken));
        
        $table->qr_code = $qrCode;
        $table->qr_token = $qrToken;
        $table->save();
        
        return response()->json([
            'success' => true,
            'message' => 'QR Code berhasil di-regenerate',
            'table' => $table
        ]);
    }
}
