<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\StoreBanner;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

class StoreBannerController extends Controller
{
    public function index()
    {
        $banners = StoreBanner::where('is_active', true)
            ->orderBy('display_order')
            ->get();
        
        return response()->json([
            'success' => true,
            'banners' => $banners
        ]);
    }

    public function all()
    {
        $banners = StoreBanner::orderBy('display_order')->get();
        
        return response()->json([
            'success' => true,
            'banners' => $banners
        ]);
    }

    public function show($id)
    {
        $banner = StoreBanner::find($id);
        
        if (!$banner) {
            return response()->json([
                'success' => false,
                'message' => 'Banner tidak ditemukan'
            ], 404);
        }
        
        return response()->json([
            'success' => true,
            'banner' => $banner
        ]);
    }

    public function store(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'title' => 'required|string|max:255',
            'subtitle' => 'nullable|string|max:255',
            'image_url' => 'nullable|string',
            'link_url' => 'nullable|string',
            'button_text' => 'nullable|string|max:50',
            'display_order' => 'nullable|integer',
            'is_active' => 'nullable|boolean',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        $banner = StoreBanner::create($request->all());
        
        return response()->json([
            'success' => true,
            'message' => 'Banner berhasil ditambahkan',
            'banner' => $banner
        ], 201);
    }

    public function update(Request $request, $id)
    {
        $banner = StoreBanner::find($id);
        
        if (!$banner) {
            return response()->json([
                'success' => false,
                'message' => 'Banner tidak ditemukan'
            ], 404);
        }

        $validator = Validator::make($request->all(), [
            'title' => 'required|string|max:255',
            'subtitle' => 'nullable|string|max:255',
            'image_url' => 'nullable|string',
            'link_url' => 'nullable|string',
            'button_text' => 'nullable|string|max:50',
            'display_order' => 'nullable|integer',
            'is_active' => 'nullable|boolean',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        $banner->update($request->all());
        
        return response()->json([
            'success' => true,
            'message' => 'Banner berhasil diupdate',
            'banner' => $banner
        ]);
    }

    public function destroy($id)
    {
        $banner = StoreBanner::find($id);
        
        if (!$banner) {
            return response()->json([
                'success' => false,
                'message' => 'Banner tidak ditemukan'
            ], 404);
        }
        
        $banner->delete();
        
        return response()->json([
            'success' => true,
            'message' => 'Banner berhasil dihapus'
        ]);
    }
}
