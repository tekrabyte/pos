import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import axiosInstance from '@/config/axios';
import { Shield } from 'lucide-react';

const StaffLogin = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axiosInstance.post('/auth/staff/login', {
        username,
        password,
      });

      if (response.data.success) {
        const user = response.data.user;
        // Save to 'user' key to match Layout.jsx expectations
        localStorage.setItem('user', JSON.stringify(user));
        localStorage.setItem('token', response.data.token);
        toast.success('Login berhasil!');
        
        // Small delay to ensure localStorage is set before navigation
        setTimeout(() => {
          if (user.role === 'admin') {
            navigate('/dashboard');
          } else {
            navigate('/pos');
          }
        }, 100);
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

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-4">
      <Card className="w-full max-w-md shadow-2xl border-slate-700" data-testid="staff-login-card">
        <CardHeader className="text-center space-y-2">
          <div className="flex justify-center mb-4">
            <div className="p-4 bg-blue-600 rounded-2xl">
              <Shield className="h-10 w-10 text-white" />
            </div>
          </div>
          <CardTitle className="text-3xl font-bold">Staff Login</CardTitle>
          <CardDescription>Login untuk akses sistem POS</CardDescription>
        </CardHeader>
        <CardContent>
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
              className="w-full bg-blue-600 hover:bg-blue-700 h-12"
              disabled={loading}
              data-testid="login-btn"
            >
              {loading ? 'Memproses...' : 'Login'}
            </Button>
          </form>
          <div className="mt-6 text-center space-y-2">
            <p className="text-sm text-gray-500">Default: admin / admin123</p>
            <div className="pt-4 border-t">
              <p className="text-sm text-gray-600">Customer?</p>
              <Link to="/customer/login" className="text-blue-600 hover:underline text-sm font-medium">
                Login sebagai Customer
              </Link>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default StaffLogin;
