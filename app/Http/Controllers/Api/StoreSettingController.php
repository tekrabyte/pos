<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\StoreSetting;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

class StoreSettingController extends Controller
{
    public function index()
    {
        $settings = StoreSetting::first();
        
        if (!$settings) {
            $settings = StoreSetting::create([
                'store_name' => 'POS System',
                'store_description' => 'Point of Sale System',
                'is_open' => true,
                'rating' => 4.5,
                'total_reviews' => 0,
            ]);
        }
        
        return response()->json([
            'success' => true,
            'store_settings' => $settings
        ]);
    }

    public function update(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'store_name' => 'nullable|string|max:255',
            'store_description' => 'nullable|string',
            'banner_url' => 'nullable|string',
            'logo_url' => 'nullable|string',
            'address' => 'nullable|string',
            'phone' => 'nullable|string',
            'email' => 'nullable|email',
            'is_open' => 'nullable|boolean',
            'opening_hours' => 'nullable|array',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        $settings = StoreSetting::first();
        
        if (!$settings) {
            $settings = StoreSetting::create($request->all());
        } else {
            $settings->update($request->all());
        }
        
        return response()->json([
            'success' => true,
            'message' => 'Pengaturan toko berhasil diupdate',
            'store_settings' => $settings
        ]);
    }
}
