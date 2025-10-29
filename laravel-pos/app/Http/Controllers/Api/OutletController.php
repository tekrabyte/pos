<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Outlet;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

class OutletController extends Controller
{
    public function index()
    {
        $outlets = Outlet::all();
        
        return response()->json([
            'success' => true,
            'outlets' => $outlets
        ]);
    }

    public function show($id)
    {
        $outlet = Outlet::with(['users', 'orders'])->find($id);
        
        if (!$outlet) {
            return response()->json([
                'success' => false,
                'message' => 'Outlet tidak ditemukan'
            ], 404);
        }
        
        return response()->json([
            'success' => true,
            'outlet' => $outlet
        ]);
    }

    public function store(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'name' => 'required|string|max:255',
            'address' => 'nullable|string',
            'city' => 'nullable|string',
            'country' => 'nullable|string',
            'postal_code' => 'nullable|string',
            'is_main' => 'nullable|boolean',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        $outlet = Outlet::create($request->all());
        
        return response()->json([
            'success' => true,
            'message' => 'Outlet berhasil ditambahkan',
            'outlet' => $outlet
        ], 201);
    }

    public function update(Request $request, $id)
    {
        $outlet = Outlet::find($id);
        
        if (!$outlet) {
            return response()->json([
                'success' => false,
                'message' => 'Outlet tidak ditemukan'
            ], 404);
        }

        $validator = Validator::make($request->all(), [
            'name' => 'required|string|max:255',
            'address' => 'nullable|string',
            'city' => 'nullable|string',
            'country' => 'nullable|string',
            'postal_code' => 'nullable|string',
            'is_main' => 'nullable|boolean',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        $outlet->update($request->all());
        
        return response()->json([
            'success' => true,
            'message' => 'Outlet berhasil diupdate',
            'outlet' => $outlet
        ]);
    }

    public function destroy($id)
    {
        $outlet = Outlet::find($id);
        
        if (!$outlet) {
            return response()->json([
                'success' => false,
                'message' => 'Outlet tidak ditemukan'
            ], 404);
        }
        
        $outlet->delete();
        
        return response()->json([
            'success' => true,
            'message' => 'Outlet berhasil dihapus'
        ]);
    }
}
