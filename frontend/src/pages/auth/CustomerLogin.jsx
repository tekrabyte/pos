import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import axios from 'axios';
import { User } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CustomerLogin = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/customer/login`, {
        email,
        password,
      });

      if (response.data.success) {
        const customer = response.data.user;
        localStorage.setItem('customer', JSON.stringify(customer));
        localStorage.setItem('customer_token', response.data.token);
        toast.success('Login berhasil!');
        
        // Check if there's a redirect path saved
        const redirectPath = localStorage.getItem('redirectAfterLogin');
        
        // Small delay to ensure localStorage is set before navigation
        setTimeout(() => {
          if (redirectPath) {
            localStorage.removeItem('redirectAfterLogin');
            navigate(redirectPath);
          } else {
            navigate('/');
          }
        }, 100);
      } else {
        toast.error(response.data.message || 'Login gagal');
      }
    } catch (error) {
      console.error('Login error:', error);
      toast.error('Email atau password salah');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 p-4">
      <Card className="w-full max-w-md shadow-xl" data-testid="customer-login-card">
        <CardHeader className="text-center space-y-2">
          <div className="flex justify-center mb-4">
            <div className="p-4 bg-emerald-600 rounded-2xl">
              <User className="h-10 w-10 text-white" />
            </div>
          </div>
          <CardTitle className="text-3xl font-bold">Customer Login</CardTitle>
          <CardDescription>Login untuk order takeaway</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="email@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                data-testid="email-input"
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
              className="w-full bg-emerald-600 hover:bg-emerald-700 h-12"
              disabled={loading}
              data-testid="login-btn"
            >
              {loading ? 'Memproses...' : 'Login'}
            </Button>
          </form>
          <div className="mt-6 text-center space-y-2">
            <p className="text-sm text-gray-600">
              Belum punya akun?{' '}
              <Link to="/customer/register" className="text-emerald-600 hover:underline font-medium">
                Daftar di sini
              </Link>
            </p>
            <div className="pt-4 border-t">
              <Link to="/staff/login" className="text-gray-600 hover:underline text-sm">
                Login sebagai Staff
              </Link>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CustomerLogin;
