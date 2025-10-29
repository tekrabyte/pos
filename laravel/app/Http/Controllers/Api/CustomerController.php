<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Customer;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Validator;

class CustomerController extends Controller
{
    public function index()
    {
        $customers = Customer::all();
        
        return response()->json([
            'success' => true,
            'customers' => $customers
        ]);
    }

    public function show($id)
    {
        $customer = Customer::with(['orders', 'ratings'])->find($id);
        
        if (!$customer) {
            return response()->json([
                'success' => false,
                'message' => 'Pelanggan tidak ditemukan'
            ], 404);
        }
        
        return response()->json([
            'success' => true,
            'customer' => $customer
        ]);
    }

    public function store(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'name' => 'required|string|max:255',
            'email' => 'required|email|unique:customers,email',
            'phone' => 'required|string',
            'address' => 'nullable|string',
            'password' => 'nullable|string|min:6',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        $customer = Customer::create([
            'name' => $request->name,
            'email' => $request->email,
            'phone' => $request->phone,
            'address' => $request->address,
            'password' => Hash::make($request->password ?? 'password123'),
            'email_verified' => false,
        ]);
        
        return response()->json([
            'success' => true,
            'message' => 'Pelanggan berhasil ditambahkan',
            'customer' => $customer
        ], 201);
    }

    public function update(Request $request, $id)
    {
        $customer = Customer::find($id);
        
        if (!$customer) {
            return response()->json([
                'success' => false,
                'message' => 'Pelanggan tidak ditemukan'
            ], 404);
        }

        $validator = Validator::make($request->all(), [
            'name' => 'required|string|max:255',
            'email' => 'required|email|unique:customers,email,' . $id,
            'phone' => 'required|string',
            'address' => 'nullable|string',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        $customer->update($request->only(['name', 'email', 'phone', 'address']));
        
        return response()->json([
            'success' => true,
            'message' => 'Pelanggan berhasil diupdate',
            'customer' => $customer
        ]);
    }

    public function destroy($id)
    {
        $customer = Customer::find($id);
        
        if (!$customer) {
            return response()->json([
                'success' => false,
                'message' => 'Pelanggan tidak ditemukan'
            ], 404);
        }
        
        $customer->delete();
        
        return response()->json([
            'success' => true,
            'message' => 'Pelanggan berhasil dihapus'
        ]);
    }
}
