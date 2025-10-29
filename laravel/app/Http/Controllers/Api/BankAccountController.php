<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\BankAccount;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

class BankAccountController extends Controller
{
    public function index()
    {
        $accounts = BankAccount::all();
        
        return response()->json([
            'success' => true,
            'bank_accounts' => $accounts
        ]);
    }

    public function show($id)
    {
        $account = BankAccount::find($id);
        
        if (!$account) {
            return response()->json([
                'success' => false,
                'message' => 'Akun bank tidak ditemukan'
            ], 404);
        }
        
        return response()->json([
            'success' => true,
            'bank_account' => $account
        ]);
    }

    public function store(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'bank_name' => 'required|string|max:100',
            'account_number' => 'required|string|max:50',
            'account_name' => 'required|string|max:255',
            'is_active' => 'nullable|boolean',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        $account = BankAccount::create($request->all());
        
        return response()->json([
            'success' => true,
            'message' => 'Akun bank berhasil ditambahkan',
            'bank_account' => $account
        ], 201);
    }

    public function update(Request $request, $id)
    {
        $account = BankAccount::find($id);
        
        if (!$account) {
            return response()->json([
                'success' => false,
                'message' => 'Akun bank tidak ditemukan'
            ], 404);
        }

        $validator = Validator::make($request->all(), [
            'bank_name' => 'required|string|max:100',
            'account_number' => 'required|string|max:50',
            'account_name' => 'required|string|max:255',
            'is_active' => 'nullable|boolean',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        $account->update($request->all());
        
        return response()->json([
            'success' => true,
            'message' => 'Akun bank berhasil diupdate',
            'bank_account' => $account
        ]);
    }

    public function destroy($id)
    {
        $account = BankAccount::find($id);
        
        if (!$account) {
            return response()->json([
                'success' => false,
                'message' => 'Akun bank tidak ditemukan'
            ], 404);
        }
        
        $account->delete();
        
        return response()->json([
            'success' => true,
            'message' => 'Akun bank berhasil dihapus'
        ]);
    }
}
