import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  Lock, 
  Edit, 
  Save,
  X,
  LogOut,
  ShoppingBag,
  ChevronRight,
  Eye,
  EyeOff,
  CheckCircle,
  AlertCircle,
  Trash2
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const CustomerProfileNew = () => {
  const navigate = useNavigate();
  const [customer, setCustomer] = useState(null);
  const [isEditMode, setIsEditMode] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // Edit profile state
  const [editData, setEditData] = useState({
    name: '',
    email: '',
    phone: '',
    address: ''
  });
  
  // Change password state
  const [passwordDialog, setPasswordDialog] = useState(false);
  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [showOldPassword, setShowOldPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  // Delete account state
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');

  useEffect(() => {
    loadCustomerData();
  }, []);

  const loadCustomerData = () => {
    const customerData = localStorage.getItem('customer');
    if (!customerData) {
      toast.error('Silakan login terlebih dahulu');
      navigate('/customer/login');
      return;
    }
    
    const parsedCustomer = JSON.parse(customerData);
    setCustomer(parsedCustomer);
    setEditData({
      name: parsedCustomer.name || '',
      email: parsedCustomer.email || '',
      phone: parsedCustomer.phone || '',
      address: parsedCustomer.address || ''
    });
  };

  const handleEditToggle = () => {
    if (isEditMode) {
      // Cancel edit - reset to original data
      setEditData({
        name: customer.name || '',
        email: customer.email || '',
        phone: customer.phone || '',
        address: customer.address || ''
      });
    }
    setIsEditMode(!isEditMode);
  };

  const handleSaveProfile = async () => {
    if (!editData.name || !editData.email || !editData.phone) {
      toast.error('Nama, email, dan nomor telepon wajib diisi');
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.put(
        `${API_URL}/customer/profile/${customer.id}`,
        editData
      );
      
      if (response.data.success) {
        const updatedCustomer = response.data.customer;
        setCustomer(updatedCustomer);
        localStorage.setItem('customer', JSON.stringify(updatedCustomer));
        toast.success('Profile berhasil diupdate!');
        setIsEditMode(false);
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      toast.error(error.response?.data?.detail || 'Gagal update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async () => {
    if (!passwordData.old_password || !passwordData.new_password || !passwordData.confirm_password) {
      toast.error('Semua field password wajib diisi');
      return;
    }
    
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error('Password baru dan konfirmasi tidak cocok');
      return;
    }
    
    if (passwordData.new_password.length < 6) {
      toast.error('Password minimal 6 karakter');
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/customer/change-password`, {
        customer_id: customer.id,
        old_password: passwordData.old_password,
        new_password: passwordData.new_password
      });
      
      if (response.data.success) {
        toast.success('Password berhasil diubah!');
        setPasswordDialog(false);
        setPasswordData({
          old_password: '',
          new_password: '',
          confirm_password: ''
        });
      }
    } catch (error) {
      console.error('Error changing password:', error);
      toast.error(error.response?.data?.detail || 'Gagal ubah password');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmation !== 'HAPUS') {
      toast.error('Ketik "HAPUS" untuk konfirmasi');
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.delete(`${API_URL}/customers/${customer.id}`);
      
      if (response.data.success) {
        toast.success('Akun berhasil dihapus');
        localStorage.removeItem('customer');
        localStorage.removeItem('customer_token');
        setTimeout(() => {
          navigate('/');
        }, 1500);
      }
    } catch (error) {
      console.error('Error deleting account:', error);
      toast.error(error.response?.data?.detail || 'Gagal menghapus akun');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('customer');
    localStorage.removeItem('customer_token');
    localStorage.removeItem('cart');
    toast.success('Berhasil logout');
    navigate('/');
  };

  if (!customer) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50">
      {/* Header */}
      <div className="bg-emerald-600 text-white">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center">
                <User className="h-8 w-8 text-emerald-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">{customer.name}</h1>
                <p className="text-emerald-100">{customer.email}</p>
              </div>
            </div>
            <Button 
              variant="ghost" 
              onClick={() => navigate('/')}
              className="text-white hover:bg-emerald-700"
            >
              Kembali
            </Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Profile Information Card */}
        <Card className="mb-6 shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-xl">Informasi Profil</CardTitle>
            {!isEditMode ? (
              <Button 
                onClick={handleEditToggle}
                variant="outline"
                size="sm"
                className="flex items-center gap-2"
              >
                <Edit className="h-4 w-4" />
                Edit
              </Button>
            ) : (
              <div className="flex gap-2">
                <Button 
                  onClick={handleSaveProfile}
                  disabled={loading}
                  size="sm"
                  className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700"
                >
                  <Save className="h-4 w-4" />
                  Simpan
                </Button>
                <Button 
                  onClick={handleEditToggle}
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-2"
                >
                  <X className="h-4 w-4" />
                  Batal
                </Button>
              </div>
            )}
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Name */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <User className="h-4 w-4" />
                Nama Lengkap
              </Label>
              {isEditMode ? (
                <Input
                  value={editData.name}
                  onChange={(e) => setEditData({...editData, name: e.target.value})}
                  placeholder="Nama lengkap"
                />
              ) : (
                <p className="text-gray-700 p-3 bg-gray-50 rounded-lg">{customer.name}</p>
              )}
            </div>

            {/* Email */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Mail className="h-4 w-4" />
                Email
              </Label>
              {isEditMode ? (
                <Input
                  type="email"
                  value={editData.email}
                  onChange={(e) => setEditData({...editData, email: e.target.value})}
                  placeholder="Email"
                />
              ) : (
                <p className="text-gray-700 p-3 bg-gray-50 rounded-lg">{customer.email}</p>
              )}
            </div>

            {/* Phone */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Phone className="h-4 w-4" />
                Nomor Telepon
              </Label>
              {isEditMode ? (
                <Input
                  value={editData.phone}
                  onChange={(e) => setEditData({...editData, phone: e.target.value})}
                  placeholder="08xxxxxxxxxx"
                />
              ) : (
                <p className="text-gray-700 p-3 bg-gray-50 rounded-lg">{customer.phone}</p>
              )}
            </div>

            {/* Address */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                Alamat
              </Label>
              {isEditMode ? (
                <Input
                  value={editData.address}
                  onChange={(e) => setEditData({...editData, address: e.target.value})}
                  placeholder="Alamat lengkap"
                />
              ) : (
                <p className="text-gray-700 p-3 bg-gray-50 rounded-lg">
                  {customer.address || 'Belum diisi'}
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Menu Cards */}
        <div className="space-y-4">
          {/* My Orders */}
          <Card 
            className="hover:shadow-lg transition cursor-pointer"
            onClick={() => navigate('/customer/orders')}
          >
            <CardContent className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-blue-100 rounded-full">
                  <ShoppingBag className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold">Pesanan Saya</h3>
                  <p className="text-sm text-gray-600">Lihat riwayat pesanan</p>
                </div>
              </div>
              <ChevronRight className="h-5 w-5 text-gray-400" />
            </CardContent>
          </Card>

          {/* Change Password */}
          <Dialog open={passwordDialog} onOpenChange={setPasswordDialog}>
            <DialogTrigger asChild>
              <Card className="hover:shadow-lg transition cursor-pointer">
                <CardContent className="flex items-center justify-between p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-yellow-100 rounded-full">
                      <Lock className="h-6 w-6 text-yellow-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold">Ubah Password</h3>
                      <p className="text-sm text-gray-600">Ganti password akun</p>
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-gray-400" />
                </CardContent>
              </Card>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Ubah Password</DialogTitle>
                <DialogDescription>
                  Masukkan password lama dan password baru Anda
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 mt-4">
                {/* Old Password */}
                <div className="space-y-2">
                  <Label>Password Lama</Label>
                  <div className="relative">
                    <Input
                      type={showOldPassword ? "text" : "password"}
                      value={passwordData.old_password}
                      onChange={(e) => setPasswordData({...passwordData, old_password: e.target.value})}
                      placeholder="Masukkan password lama"
                    />
                    <button
                      type="button"
                      onClick={() => setShowOldPassword(!showOldPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2"
                    >
                      {showOldPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                {/* New Password */}
                <div className="space-y-2">
                  <Label>Password Baru</Label>
                  <div className="relative">
                    <Input
                      type={showNewPassword ? "text" : "password"}
                      value={passwordData.new_password}
                      onChange={(e) => setPasswordData({...passwordData, new_password: e.target.value})}
                      placeholder="Minimal 6 karakter"
                    />
                    <button
                      type="button"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2"
                    >
                      {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                {/* Confirm Password */}
                <div className="space-y-2">
                  <Label>Konfirmasi Password Baru</Label>
                  <div className="relative">
                    <Input
                      type={showConfirmPassword ? "text" : "password"}
                      value={passwordData.confirm_password}
                      onChange={(e) => setPasswordData({...passwordData, confirm_password: e.target.value})}
                      placeholder="Ulangi password baru"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2"
                    >
                      {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                {/* Info */}
                {passwordData.new_password && passwordData.confirm_password && (
                  <Alert className={passwordData.new_password === passwordData.confirm_password ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"}>
                    {passwordData.new_password === passwordData.confirm_password ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-red-600" />
                    )}
                    <AlertDescription className={passwordData.new_password === passwordData.confirm_password ? "text-green-700" : "text-red-700"}>
                      {passwordData.new_password === passwordData.confirm_password 
                        ? "Password cocok" 
                        : "Password tidak cocok"}
                    </AlertDescription>
                  </Alert>
                )}

                <Button
                  onClick={handleChangePassword}
                  disabled={loading}
                  className="w-full bg-emerald-600 hover:bg-emerald-700"
                >
                  {loading ? 'Memproses...' : 'Ubah Password'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>

          {/* Logout */}
          <Card 
            className="hover:shadow-lg transition cursor-pointer border-red-200"
            onClick={handleLogout}
          >
            <CardContent className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-red-100 rounded-full">
                  <LogOut className="h-6 w-6 text-red-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-red-600">Keluar</h3>
                  <p className="text-sm text-gray-600">Logout dari akun</p>
                </div>
              </div>
              <ChevronRight className="h-5 w-5 text-gray-400" />
            </CardContent>
          </Card>

          {/* Delete Account */}
          <Dialog open={deleteDialog} onOpenChange={setDeleteDialog}>
            <DialogTrigger asChild>
              <Card className="hover:shadow-lg transition cursor-pointer border-red-300">
                <CardContent className="flex items-center justify-between p-4">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-red-100 rounded-full">
                      <Trash2 className="h-6 w-6 text-red-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-red-600">Hapus Akun</h3>
                      <p className="text-sm text-gray-600">Hapus akun permanen</p>
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-gray-400" />
                </CardContent>
              </Card>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="text-red-600">Hapus Akun</DialogTitle>
                <DialogDescription>
                  Tindakan ini tidak dapat dibatalkan. Semua data Anda akan dihapus permanen.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 mt-4">
                <Alert className="bg-red-50 border-red-200">
                  <AlertCircle className="h-4 w-4 text-red-600" />
                  <AlertDescription className="text-red-700">
                    Ketik <strong>"HAPUS"</strong> untuk konfirmasi
                  </AlertDescription>
                </Alert>

                <div className="space-y-2">
                  <Label>Konfirmasi Penghapusan</Label>
                  <Input
                    value={deleteConfirmation}
                    onChange={(e) => setDeleteConfirmation(e.target.value)}
                    placeholder='Ketik "HAPUS"'
                  />
                </div>

                <Button
                  onClick={handleDeleteAccount}
                  disabled={loading || deleteConfirmation !== 'HAPUS'}
                  className="w-full bg-red-600 hover:bg-red-700"
                >
                  {loading ? 'Memproses...' : 'Hapus Akun Saya'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Info Default Password */}
        <Card className="mt-6 bg-blue-50 border-blue-200">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
              <div className="text-sm text-blue-800">
                <p className="font-semibold mb-1">Password Default</p>
                <p>Untuk akun baru, password default adalah: <strong>12345678</strong></p>
                <p className="mt-1">Segera ubah password Anda untuk keamanan akun.</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CustomerProfileNew;
