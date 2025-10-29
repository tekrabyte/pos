import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import axios from 'axios';
import { 
  User, 
  UserPlus, 
  Mail, 
  Phone, 
  Lock, 
  ShoppingCart, 
  Trash2,
  Info,
  ArrowRight
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}`;

const CustomerAuthCart = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('login');
  const [cart, setCart] = useState([]);
  
  // Login state
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);
  
  // Register state
  const [registerName, setRegisterName] = useState('');
  const [registerEmail, setRegisterEmail] = useState('');
  const [registerPhone, setRegisterPhone] = useState('');
  const [registerAddress, setRegisterAddress] = useState('');
  const [registerLoading, setRegisterLoading] = useState(false);

  useEffect(() => {
    // Load cart from localStorage
    const savedCart = localStorage.getItem('cart');
    if (savedCart) {
      setCart(JSON.parse(savedCart));
    }
  }, []);

  const calculateTotal = () => {
    return cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  };

  const removeFromCart = (productId) => {
    const updatedCart = cart.filter(item => item.id !== productId);
    setCart(updatedCart);
    localStorage.setItem('cart', JSON.stringify(updatedCart));
    toast.success('Item dihapus dari keranjang');
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginLoading(true);

    try {
      const response = await axios.post(`${API}/auth/customer/login`, {
        email: loginEmail,
        password: loginPassword,
      });

      if (response.data.success) {
        const customer = response.data.user;
        localStorage.setItem('customer', JSON.stringify(customer));
        localStorage.setItem('customer_token', response.data.token);
        toast.success('Login berhasil!');
        
        // Navigate to cart checkout
        setTimeout(() => {
          navigate('/customer/cart');
        }, 500);
      } else {
        toast.error(response.data.message || 'Login gagal');
      }
    } catch (error) {
      console.error('Login error:', error);
      toast.error('Email atau password salah');
    } finally {
      setLoginLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    
    // Validate phone format
    if (!registerPhone.startsWith('08')) {
      toast.error('Nomor telepon harus dimulai dengan 08');
      return;
    }
    
    if (registerPhone.length < 10) {
      toast.error('Nomor telepon minimal 10 digit');
      return;
    }
    
    setRegisterLoading(true);

    try {
      const response = await axios.post(`${API}/auth/customer/register`, {
        name: registerName,
        email: registerEmail,
        phone: registerPhone,
        address: registerAddress,
      });

      if (response.data.success) {
        toast.success('Registrasi berhasil! Silakan login dengan password yang dikirim ke email.', {
          duration: 5000
        });
        
        // Show password if email failed
        if (!response.data.email_sent && response.data.temp_password) {
          toast.info(`Password Anda: ${response.data.temp_password}`, {
            duration: 10000
          });
        }
        
        // Switch to login tab
        setActiveTab('login');
        setLoginEmail(registerEmail);
      }
    } catch (error) {
      console.error('Registration error:', error);
      const errorMsg = error.response?.data?.detail || 'Gagal melakukan registrasi';
      toast.error(errorMsg);
    } finally {
      setRegisterLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-emerald-700">
              🛒 Checkout
            </h1>
            <Button 
              variant="outline" 
              onClick={() => navigate('/')}
              size="sm"
            >
              Kembali ke Menu
            </Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-7xl mx-auto">
          {/* Left Column - Auth Forms */}
          <div className="order-2 lg:order-1">
            <Card className="shadow-xl">
              <CardHeader className="text-center pb-4">
                <CardTitle className="text-2xl font-bold text-gray-800">
                  Login atau Daftar
                </CardTitle>
                <p className="text-sm text-gray-600 mt-2">
                  Masuk untuk melanjutkan checkout
                </p>
              </CardHeader>
              <CardContent>
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                  <TabsList className="grid w-full grid-cols-2 mb-6">
                    <TabsTrigger value="login" className="flex items-center gap-2">
                      <User className="h-4 w-4" />
                      Login
                    </TabsTrigger>
                    <TabsTrigger value="register" className="flex items-center gap-2">
                      <UserPlus className="h-4 w-4" />
                      Daftar
                    </TabsTrigger>
                  </TabsList>

                  {/* Login Form */}
                  <TabsContent value="login" className="mt-0">
                    <form onSubmit={handleLogin} className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="login-email" className="flex items-center gap-2">
                          <Mail className="h-4 w-4" />
                          Email
                        </Label>
                        <Input
                          id="login-email"
                          type="email"
                          placeholder="email@example.com"
                          value={loginEmail}
                          onChange={(e) => setLoginEmail(e.target.value)}
                          required
                          className="h-11"
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="login-password" className="flex items-center gap-2">
                          <Lock className="h-4 w-4" />
                          Password
                        </Label>
                        <Input
                          id="login-password"
                          type="password"
                          placeholder="Masukkan password"
                          value={loginPassword}
                          onChange={(e) => setLoginPassword(e.target.value)}
                          required
                          className="h-11"
                        />
                      </div>

                      <Button
                        type="submit"
                        className="w-full h-12 bg-emerald-600 hover:bg-emerald-700 text-base font-semibold"
                        disabled={loginLoading}
                      >
                        {loginLoading ? 'Memproses...' : (
                          <>
                            Login & Lanjutkan
                            <ArrowRight className="ml-2 h-5 w-5" />
                          </>
                        )}
                      </Button>
                    </form>
                  </TabsContent>

                  {/* Register Form */}
                  <TabsContent value="register" className="mt-0">
                    <Alert className="mb-4 bg-blue-50 border-blue-200">
                      <Info className="h-4 w-4 text-blue-600" />
                      <AlertDescription className="text-sm text-blue-700">
                        Password akan otomatis dibuat dan dikirim ke email Anda
                      </AlertDescription>
                    </Alert>

                    <form onSubmit={handleRegister} className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="register-name" className="flex items-center gap-2">
                          <User className="h-4 w-4" />
                          Nama Lengkap *
                        </Label>
                        <Input
                          id="register-name"
                          type="text"
                          placeholder="Contoh: John Doe"
                          value={registerName}
                          onChange={(e) => setRegisterName(e.target.value)}
                          required
                          className="h-11"
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="register-email" className="flex items-center gap-2">
                          <Mail className="h-4 w-4" />
                          Email *
                        </Label>
                        <Input
                          id="register-email"
                          type="email"
                          placeholder="email@example.com"
                          value={registerEmail}
                          onChange={(e) => setRegisterEmail(e.target.value)}
                          required
                          className="h-11"
                        />
                        <p className="text-xs text-gray-500">Password akan dikirim ke email ini</p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="register-phone" className="flex items-center gap-2">
                          <Phone className="h-4 w-4" />
                          Nomor Telepon *
                        </Label>
                        <Input
                          id="register-phone"
                          type="tel"
                          placeholder="08xxxxxxxxxx"
                          value={registerPhone}
                          onChange={(e) => setRegisterPhone(e.target.value)}
                          required
                          pattern="08[0-9]{8,11}"
                          className="h-11"
                        />
                        <p className="text-xs text-gray-500">Format: 08xxxxxxxxxx</p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="register-address">Alamat (Opsional)</Label>
                        <Input
                          id="register-address"
                          type="text"
                          placeholder="Alamat lengkap"
                          value={registerAddress}
                          onChange={(e) => setRegisterAddress(e.target.value)}
                          className="h-11"
                        />
                      </div>

                      <Button
                        type="submit"
                        className="w-full h-12 bg-emerald-600 hover:bg-emerald-700 text-base font-semibold"
                        disabled={registerLoading}
                      >
                        {registerLoading ? 'Mendaftar...' : 'Daftar Sekarang'}
                      </Button>
                    </form>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Cart Summary */}
          <div className="order-1 lg:order-2">
            <Card className="shadow-xl sticky top-8">
              <CardHeader className="bg-emerald-600 text-white rounded-t-lg">
                <div className="flex items-center gap-2">
                  <ShoppingCart className="h-6 w-6" />
                  <CardTitle className="text-xl">Keranjang Belanja</CardTitle>
                </div>
                <p className="text-emerald-100 text-sm mt-1">
                  {cart.length} item dalam keranjang
                </p>
              </CardHeader>
              <CardContent className="pt-6">
                {cart.length === 0 ? (
                  <div className="text-center py-12">
                    <ShoppingCart className="h-16 w-16 mx-auto text-gray-300 mb-4" />
                    <p className="text-gray-500 text-lg font-medium">Keranjang Kosong</p>
                    <p className="text-gray-400 text-sm mt-2">
                      Tambahkan produk untuk melanjutkan
                    </p>
                    <Button 
                      onClick={() => navigate('/')} 
                      className="mt-4 bg-emerald-600 hover:bg-emerald-700"
                    >
                      Lihat Menu
                    </Button>
                  </div>
                ) : (
                  <>
                    {/* Cart Items */}
                    <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
                      {cart.map((item) => (
                        <div 
                          key={item.id} 
                          className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
                        >
                          <div className="flex-1">
                            <h4 className="font-semibold text-gray-800">{item.name}</h4>
                            <p className="text-sm text-gray-600 mt-1">
                              Rp {item.price.toLocaleString('id-ID')} x {item.quantity}
                            </p>
                            <p className="text-emerald-700 font-semibold mt-1">
                              Rp {(item.price * item.quantity).toLocaleString('id-ID')}
                            </p>
                          </div>
                          <Button
                            size="icon"
                            variant="ghost"
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            onClick={() => removeFromCart(item.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>

                    {/* Total */}
                    <div className="mt-6 pt-6 border-t border-gray-200">
                      <div className="flex justify-between items-center mb-4">
                        <span className="text-gray-600">Subtotal</span>
                        <span className="font-semibold">
                          Rp {calculateTotal().toLocaleString('id-ID')}
                        </span>
                      </div>
                      <div className="flex justify-between items-center text-lg font-bold text-gray-900">
                        <span>Total</span>
                        <span className="text-emerald-700">
                          Rp {calculateTotal().toLocaleString('id-ID')}
                        </span>
                      </div>
                    </div>

                    {/* Info */}
                    <div className="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-200">
                      <p className="text-sm text-amber-800 text-center">
                        💡 Login untuk melanjutkan ke pembayaran
                      </p>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CustomerAuthCart;
