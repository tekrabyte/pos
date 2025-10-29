import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Alert, AlertDescription } from '@/components/ui/alert';
import axios from 'axios';
import { UserPlus, Mail, Phone, User, Info } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}`;

const CustomerRegister = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    
    // Validate phone format
    if (!phone.startsWith('08')) {
      toast.error('Nomor telepon harus dimulai dengan 08');
      return;
    }
    
    if (phone.length < 10) {
      toast.error('Nomor telepon minimal 10 digit');
      return;
    }
    
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/customer/register`, {
        name,
        email,
        phone,
        address,
      });

      if (response.data.success) {
        // Show success with password info
        toast.success('Registrasi berhasil! Password telah dikirim ke email Anda.', {
          duration: 5000
        });
        
        // If email failed to send, show password
        if (!response.data.email_sent && response.data.temp_password) {
          toast.info(`Password Anda: ${response.data.temp_password}`, {
            duration: 10000
          });
        }
        
        // Navigate to login after 2 seconds
        setTimeout(() => {
          navigate('/customer/login');
        }, 2000);
      }
    } catch (error) {
      console.error('Registration error:', error);
      const errorMsg = error.response?.data?.detail || 'Gagal melakukan registrasi';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 p-4">
      <Card className="w-full max-w-md shadow-xl">
        <CardHeader className="text-center space-y-2">
          <div className="flex justify-center mb-4">
            <div className="p-4 bg-green-600 rounded-2xl">
              <UserPlus className="h-10 w-10 text-white" />
            </div>
          </div>
          <CardTitle className="text-3xl font-bold text-gray-800">Daftar Akun Baru</CardTitle>
          <CardDescription className="text-base">Isi data Anda untuk membuat akun</CardDescription>
        </CardHeader>
        <CardContent>
          {/* Info Box */}
          <Alert className="mb-4 bg-blue-50 border-blue-200">
            <Info className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-sm text-blue-700">
              Password akan otomatis dibuat dan dikirim ke email Anda
            </AlertDescription>
          </Alert>

          <form onSubmit={handleRegister} className="space-y-4">
            {/* Name */}
            <div className="space-y-2">
              <Label htmlFor="name" className="flex items-center gap-2">
                <User className="h-4 w-4" />
                Nama Lengkap *
              </Label>
              <Input
                id="name"
                type="text"
                placeholder="Contoh: John Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="text-base"
              />
            </div>

            {/* Email */}
            <div className="space-y-2">
              <Label htmlFor="email" className="flex items-center gap-2">
                <Mail className="h-4 w-4" />
                Email *
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="email@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="text-base"
              />
              <p className="text-xs text-gray-500">Password akan dikirim ke email ini</p>
            </div>

            {/* Phone */}
            <div className="space-y-2">
              <Label htmlFor="phone" className="flex items-center gap-2">
                <Phone className="h-4 w-4" />
                Nomor Telepon *
              </Label>
              <Input
                id="phone"
                type="tel"
                placeholder="08xxxxxxxxxx"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
                pattern="08[0-9]{8,11}"
                className="text-base"
              />
              <p className="text-xs text-gray-500">Format: 08xxxxxxxxxx (10-13 digit)</p>
            </div>

            {/* Address (Optional) */}
            <div className="space-y-2">
              <Label htmlFor="address">Alamat (Opsional)</Label>
              <Input
                id="address"
                type="text"
                placeholder="Alamat lengkap"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                className="text-base"
              />
            </div>

            <Button
              type="submit"
              className="w-full bg-green-600 hover:bg-green-700 h-12 text-base font-semibold"
              disabled={loading}
            >
              {loading ? 'Mendaftar...' : 'Daftar Sekarang'}
            </Button>
          </form>

          <div className="mt-6 text-center space-y-3">
            <p className="text-sm text-gray-600">
              Sudah punya akun?{' '}
              <Link to="/customer/login" className="text-green-600 hover:underline font-medium">
                Login di sini
              </Link>
            </p>
            <div className="pt-3 border-t">
              <Link to="/" className="text-sm text-gray-600 hover:underline">
                ← Kembali ke Beranda
              </Link>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CustomerRegister;