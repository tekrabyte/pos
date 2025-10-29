<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;
use Illuminate\Support\Facades\Storage;

class PaymentSettingController extends Controller
{
    private $qrisSettingsFile = 'payment_settings/qris.json';

    public function getQrisSettings()
    {
        try {
            // Check if settings file exists
            if (Storage::disk('local')->exists($this->qrisSettingsFile)) {
                $settings = json_decode(Storage::disk('local')->get($this->qrisSettingsFile), true);
            } else {
                // Default settings
                $settings = [
                    'enabled' => false,
                    'merchant_id' => '',
                    'merchant_name' => '',
                    'qris_image' => '',
                ];
            }

            return response()->json([
                'success' => true,
                'settings' => $settings
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Gagal mengambil settings QRIS: ' . $e->getMessage()
            ], 500);
        }
    }

    public function updateQrisSettings(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'enabled' => 'required|boolean',
            'merchant_id' => 'nullable|string',
            'merchant_name' => 'nullable|string',
            'qris_image' => 'nullable|string',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        try {
            $settings = [
                'enabled' => $request->enabled,
                'merchant_id' => $request->merchant_id ?? '',
                'merchant_name' => $request->merchant_name ?? '',
                'qris_image' => $request->qris_image ?? '',
                'updated_at' => now()->toDateTimeString()
            ];

            // Ensure directory exists
            $directory = dirname($this->qrisSettingsFile);
            if (!Storage::disk('local')->exists($directory)) {
                Storage::disk('local')->makeDirectory($directory);
            }

            // Save settings to file
            Storage::disk('local')->put($this->qrisSettingsFile, json_encode($settings, JSON_PRETTY_PRINT));

            return response()->json([
                'success' => true,
                'message' => 'Settings QRIS berhasil diupdate',
                'settings' => $settings
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Gagal update settings QRIS: ' . $e->getMessage()
            ], 500);
        }
    }
}
