<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Brand;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

class BrandController extends Controller
{
    public function index()
    {
        $brands = Brand::all();
        
        return response()->json([
            'success' => true,
            'brands' => $brands
        ]);
    }

    public function show($id)
    {
        $brand = Brand::with('products')->find($id);
        
        if (!$brand) {
            return response()->json([
                'success' => false,
                'message' => 'Brand tidak ditemukan'
            ], 404);
        }
        
        return response()->json([
            'success' => true,
            'brand' => $brand
        ]);
    }

    public function store(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'name' => 'required|string|max:255',
            'description' => 'nullable|string',
            'logo_url' => 'nullable|string',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        $brand = Brand::create($request->all());
        
        return response()->json([
            'success' => true,
            'message' => 'Brand berhasil ditambahkan',
            'brand' => $brand
        ], 201);
    }

    public function update(Request $request, $id)
    {
        $brand = Brand::find($id);
        
        if (!$brand) {
            return response()->json([
                'success' => false,
                'message' => 'Brand tidak ditemukan'
            ], 404);
        }

        $validator = Validator::make($request->all(), [
            'name' => 'required|string|max:255',
            'description' => 'nullable|string',
            'logo_url' => 'nullable|string',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        $brand->update($request->all());
        
        return response()->json([
            'success' => true,
            'message' => 'Brand berhasil diupdate',
            'brand' => $brand
        ]);
    }

    public function destroy($id)
    {
        $brand = Brand::find($id);
        
        if (!$brand) {
            return response()->json([
                'success' => false,
                'message' => 'Brand tidak ditemukan'
            ], 404);
        }
        
        $brand->delete();
        
        return response()->json([
            'success' => true,
            'message' => 'Brand berhasil dihapus'
        ]);
    }
}
