import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import axios from 'axios';
import { ShoppingCart, User, UserPlus } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Customer registration
  const [custName, setCustName] = useState('');
  const [custEmail, setCustEmail] = useState('');
  const [custPhone, setCustPhone] = useState('');
  const [custAddress, setCustAddress] = useState('');
  const [regLoading, setRegLoading] = useState(false);
  
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/login`, {
        username,
        password,
      });

      if (response.data.success) {
        const user = response.data.user;
        localStorage.setItem('user', JSON.stringify(user));
        toast.success('Login berhasil!');
        
        // Check role and navigate accordingly
        if (user.role_id === 1 || user.role_id === 3) {
          // Admin or Manager
          navigate('/dashboard');
        } else {
          // Cashier
          navigate('/pos');
        }
      } else {
        toast.error(response.data.message || 'Login gagal');
      }
    } catch (error) {
      console.error('Login error:', error);
      toast.error('Terjadi kesalahan saat login');
    } finally {
      setLoading(false);
    }
  };

  const handleCustomerRegister = async (e) => {
    e.preventDefault();
    setRegLoading(true);

    try {
      const response = await axios.post(`${API}/auth/register-customer`, {
        name: custName,
        email: custEmail,
        phone: custPhone,
        address: custAddress,
      });

      if (response.data.success) {
        toast.success('Registrasi berhasil! Silakan hubungi kasir untuk berbelanja.');
        setCustName('');
        setCustEmail('');
        setCustPhone('');
        setCustAddress('');
      }
    } catch (error) {
      console.error('Registration error:', error);
      toast.error(error.response?.data?.detail || 'Gagal melakukan registrasi');
    } finally {
      setRegLoading(false);
    }
  };

  const handleGuestCheckout = () => {
    navigate('/pos?mode=guest');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-4">
      <div className="w-full max-w-5xl grid md:grid-cols-2 gap-8 items-center">
        {/* Left Side - Branding */}
        <div className="hidden md:block space-y-6">
          <div className="flex items-center gap-3">
            <div className="p-4 bg-blue-600 rounded-2xl">
              <ShoppingCart className="h-12 w-12 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-900">POS System</h1>
              <p className="text-gray-600">Point of Sale Modern</p>
            </div>
          </div>
          <div className="space-y-4 text-gray-700">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
              <p>Kasir cepat & efisien</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
              <p>QRIS & multiple payment</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
              <p>Barcode scanner support</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
              <p>Print receipt otomatis</p>
            </div>
          </div>
        </div>

        {/* Right Side - Login/Register */}
        <Card className="w-full shadow-xl" data-testid="auth-card">
          <CardHeader className="text-center">
            <div className="flex justify-center mb-2 md:hidden">
              <div className="p-3 bg-blue-100 rounded-full">
                <ShoppingCart className="h-8 w-8 text-blue-600" />
              </div>
            </div>
            <CardTitle className="text-2xl">Selamat Datang</CardTitle>
            <CardDescription>Login sebagai kasir atau daftar sebagai customer</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="staff" className="w-full">
              <TabsList className="grid w-full grid-cols-2 mb-6">
                <TabsTrigger value="staff" data-testid="tab-staff">
                  <User className="h-4 w-4 mr-2" />
                  Staff/Kasir
                </TabsTrigger>
                <TabsTrigger value="customer" data-testid="tab-customer">
                  <UserPlus className="h-4 w-4 mr-2" />
                  Customer
                </TabsTrigger>
              </TabsList>
              
              {/* Staff Login */}
              <TabsContent value="staff" data-testid="staff-login-form">
                <form onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="username">Username</Label>
                    <Input
                      id="username"
                      type="text"
                      placeholder="Masukkan username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      required
                      data-testid="username-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      type="password"
                      placeholder="Masukkan password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      data-testid="password-input"
                    />
                  </div>
                  <Button
                    type="submit"
                    className="w-full bg-blue-600 hover:bg-blue-700"
                    disabled={loading}
                    data-testid="login-btn"
                  >
                    {loading ? 'Memproses...' : 'Login'}
                  </Button>
                  <p className="text-xs text-center text-gray-500">Default: admin / admin123</p>
                </form>
              </TabsContent>
              
              {/* Customer Registration */}
              <TabsContent value="customer" data-testid="customer-register-form">
                <form onSubmit={handleCustomerRegister} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="cust-name">Nama Lengkap</Label>
                    <Input
                      id="cust-name"
                      type="text"
                      placeholder="Masukkan nama"
                      value={custName}
                      onChange={(e) => setCustName(e.target.value)}
                      required
                      data-testid="cust-name-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="cust-email">Email (Opsional)</Label>
                    <Input
                      id="cust-email"
                      type="email"
                      placeholder="email@example.com"
                      value={custEmail}
                      onChange={(e) => setCustEmail(e.target.value)}
                      data-testid="cust-email-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="cust-phone">No. Telepon</Label>
                    <Input
                      id="cust-phone"
                      type="tel"
                      placeholder="08123456789"
                      value={custPhone}
                      onChange={(e) => setCustPhone(e.target.value)}
                      data-testid="cust-phone-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="cust-address">Alamat (Opsional)</Label>
                    <Input
                      id="cust-address"
                      type="text"
                      placeholder="Alamat lengkap"
                      value={custAddress}
                      onChange={(e) => setCustAddress(e.target.value)}
                      data-testid="cust-address-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Button
                      type="submit"
                      className="w-full bg-green-600 hover:bg-green-700"
                      disabled={regLoading}
                      data-testid="register-btn"
                    >
                      {regLoading ? 'Mendaftar...' : 'Daftar Customer'}
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      className="w-full"
                      onClick={handleGuestCheckout}
                      data-testid="guest-checkout-btn"
                    >
                      Belanja Sebagai Guest
                    </Button>
                  </div>
                </form>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Login;