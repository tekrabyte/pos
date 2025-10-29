<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Customer;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Mail;
use Illuminate\Support\Str;
use Tymon\JWTAuth\Facades\JWTAuth;
use Illuminate\Support\Facades\Validator;
use Carbon\Carbon;

class CustomerAuthController extends Controller
{
    /**
     * Customer Login
     */
    public function login(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'email' => 'required|email',
            'password' => 'required|string',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        $customer = Customer::where('email', $request->email)->first();

        if (!$customer || !Hash::check($request->password, $customer->password)) {
            return response()->json([
                'success' => false,
                'message' => 'Email atau password salah'
            ], 401);
        }

        // Generate JWT token
        $token = JWTAuth::fromUser($customer);

        return response()->json([
            'success' => true,
            'token' => $token,
            'user' => [
                'id' => $customer->id,
                'name' => $customer->name,
                'email' => $customer->email,
                'phone' => $customer->phone,
                'address' => $customer->address,
            ]
        ]);
    }

    /**
     * Customer Register
     */
    public function register(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'name' => 'required|string|max:255',
            'email' => 'required|email|unique:customers,email',
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

        // Auto-generate password
        $password = Str::random(10);

        $customer = Customer::create([
            'name' => $request->name,
            'email' => $request->email,
            'phone' => $request->phone,
            'address' => $request->address,
            'password' => Hash::make($password),
            'email_verified' => false,
        ]);

        // TODO: Send email with password
        // Mail::to($customer->email)->send(new WelcomeCustomer($customer, $password));

        return response()->json([
            'success' => true,
            'message' => 'Registrasi berhasil. Password telah dikirim ke email Anda.',
            'customer' => [
                'id' => $customer->id,
                'name' => $customer->name,
                'email' => $customer->email,
            ],
            'temp_password' => $password // Remove in production
        ], 201);
    }

    /**
     * Forgot Password
     */
    public function forgotPassword(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'email' => 'required|email',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        $customer = Customer::where('email', $request->email)->first();

        if (!$customer) {
            return response()->json([
                'success' => false,
                'message' => 'Email tidak ditemukan'
            ], 404);
        }

        // Generate reset token
        $token = Str::random(60);
        $customer->password_reset_token = $token;
        $customer->password_reset_expires = Carbon::now()->addHours(1);
        $customer->save();

        // TODO: Send email with reset link
        // Mail::to($customer->email)->send(new ResetPassword($customer, $token));

        return response()->json([
            'success' => true,
            'message' => 'Link reset password telah dikirim ke email Anda',
        ]);
    }

    /**
     * Reset Password
     */
    public function resetPassword(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'token' => 'required|string',
            'new_password' => 'required|string|min:6',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validasi gagal',
                'errors' => $validator->errors()
            ], 422);
        }

        $customer = Customer::where('password_reset_token', $request->token)
            ->where('password_reset_expires', '>', Carbon::now())
            ->first();

        if (!$customer) {
            return response()->json([
                'success' => false,
                'message' => 'Token tidak valid atau sudah kadaluarsa'
            ], 400);
        }

        $customer->password = Hash::make($request->new_password);
        $customer->password_reset_token = null;
        $customer->password_reset_expires = null;
        $customer->save();

        return response()->json([
            'success' => true,
            'message' => 'Password berhasil direset'
        ]);
    }

    /**
     * Get authenticated customer
     */
    public function me(Request $request)
    {
        $customer = auth()->user();
        
        return response()->json([
            'success' => true,
            'user' => $customer
        ]);
    }

    /**
     * Logout
     */
    public function logout()
    {
        auth()->logout();
        
        return response()->json([
            'success' => true,
            'message' => 'Berhasil logout'
        ]);
    }
}
