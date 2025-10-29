import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Plus, Edit, Trash2, Mail, Phone, MapPin, KeyRound, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Customers = () => {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [showResetDialog, setShowResetDialog] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [resetMode, setResetMode] = useState('auto'); // 'auto' or 'custom'
  const [customPassword, setCustomPassword] = useState('');
  const [editId, setEditId] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    address: '',
  });

  useEffect(() => {
    fetchCustomers();
  }, []);

  const fetchCustomers = async () => {
    try {
      const response = await axios.get(`${API}/customers`);
      setCustomers(response.data);
    } catch (error) {
      console.error('Error fetching customers:', error);
      toast.error('Gagal mengambil data pelanggan');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editId) {
        await axios.put(`${API}/customers/${editId}`, formData);
        toast.success('Pelanggan berhasil diperbarui');
      } else {
        await axios.post(`${API}/customers`, formData);
        toast.success('Pelanggan berhasil ditambahkan');
      }
      setShowDialog(false);
      setFormData({ name: '', email: '', phone: '', address: '' });
      setEditId(null);
      fetchCustomers();
    } catch (error) {
      console.error('Error saving customer:', error);
      toast.error('Gagal menyimpan pelanggan');
    }
  };

  const handleEdit = (customer) => {
    setEditId(customer.id);
    setFormData({
      name: customer.name,
      email: customer.email || '',
      phone: customer.phone || '',
      address: customer.address || '',
    });
    setShowDialog(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Apakah Anda yakin ingin menghapus pelanggan ini?')) {
      try {
        await axios.delete(`${API}/customers/${id}`);
        toast.success('Pelanggan berhasil dihapus');
        fetchCustomers();
      } catch (error) {
        console.error('Error deleting customer:', error);
        toast.error('Gagal menghapus pelanggan');
      }
    }
  };

  const handleAddNew = () => {
    setEditId(null);
    setFormData({ name: '', email: '', phone: '', address: '' });
    setShowDialog(true);
  };

  const handleResetPassword = (customer) => {
    setSelectedCustomer(customer);
    setResetMode('auto');
    setCustomPassword('');
    setShowResetDialog(true);
  };

  const handleResetPasswordSubmit = async () => {
    if (resetMode === 'custom' && !customPassword) {
      toast.error('Silakan masukkan password baru');
      return;
    }

    if (resetMode === 'custom' && customPassword.length < 6) {
      toast.error('Password minimal 6 karakter');
      return;
    }

    setResetLoading(true);

    try {
      const payload = resetMode === 'auto' 
        ? {} 
        : { new_password: customPassword };

      const response = await axios.post(
        `${API}/admin/customers/${selectedCustomer.id}/reset-password`,
        payload
      );

      if (response.data.success) {
        toast.success(response.data.message, {
          duration: 5000
        });

        // Show password if email failed
        if (!response.data.email_sent && response.data.temp_password) {
          toast.info(`Password Baru: ${response.data.temp_password}`, {
            duration: 10000
          });
        }

        setShowResetDialog(false);
        setSelectedCustomer(null);
        setCustomPassword('');
      }
    } catch (error) {
      console.error('Error resetting password:', error);
      const errorMsg = error.response?.data?.detail || 'Gagal reset password';
      toast.error(errorMsg);
    } finally {
      setResetLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500">Memuat data...</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6" data-testid="customers-page">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">Data Pelanggan</h1>
          <Button onClick={handleAddNew} className="bg-blue-600 hover:bg-blue-700" data-testid="add-customer-btn">
            <Plus className="h-4 w-4 mr-2" />
            Tambah Pelanggan
          </Button>
        </div>

        {customers.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <p className="text-gray-500 mb-4">Belum ada pelanggan</p>
              <Button onClick={handleAddNew} variant="outline" data-testid="empty-add-customer-btn">
                <Plus className="h-4 w-4 mr-2" />
                Tambah Pelanggan Pertama
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {customers.map((customer) => (
              <Card key={customer.id} className="hover:shadow-lg transition-shadow" data-testid={`customer-card-${customer.id}`}>
                <CardContent className="p-6">
                  <h3 className="font-semibold text-lg text-gray-800 mb-4">{customer.name}</h3>
                  <div className="space-y-2 text-sm text-gray-600 mb-4">
                    {customer.email && (
                      <div className="flex items-center gap-2">
                        <Mail className="h-4 w-4" />
                        <span>{customer.email}</span>
                      </div>
                    )}
                    {customer.phone && (
                      <div className="flex items-center gap-2">
                        <Phone className="h-4 w-4" />
                        <span>{customer.phone}</span>
                      </div>
                    )}
                    {customer.address && (
                      <div className="flex items-start gap-2">
                        <MapPin className="h-4 w-4 mt-0.5" />
                        <span>{customer.address}</span>
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => handleEdit(customer)}
                      data-testid={`edit-customer-${customer.id}`}
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      onClick={() => handleDelete(customer.id)}
                      data-testid={`delete-customer-${customer.id}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent data-testid="customer-dialog">
          <DialogHeader>
            <DialogTitle>{editId ? 'Edit Pelanggan' : 'Tambah Pelanggan Baru'}</DialogTitle>
            <DialogDescription>Masukkan informasi pelanggan</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nama *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Masukkan nama pelanggan"
                  required
                  data-testid="customer-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="email@example.com"
                  data-testid="customer-email-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Telepon</Label>
                <Input
                  id="phone"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="08123456789"
                  data-testid="customer-phone-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="address">Alamat</Label>
                <Input
                  id="address"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  placeholder="Masukkan alamat"
                  data-testid="customer-address-input"
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)} data-testid="cancel-customer-btn">
                Batal
              </Button>
              <Button type="submit" className="bg-blue-600 hover:bg-blue-700" data-testid="save-customer-btn">
                {editId ? 'Update' : 'Simpan'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </Layout>
  );
};

export default Customers;