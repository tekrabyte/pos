import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, CreditCard, Smartphone, Edit, Trash2 } from 'lucide-react';
import axiosInstance from '@/config/axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}`;

const PaymentSettings = () => {
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editId, setEditId] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    type: 'cash',
    is_active: true,
  });

  useEffect(() => {
    fetchPaymentMethods();
  }, []);

  const fetchPaymentMethods = async () => {
    try {
      const response = await axiosInstance.get(`/payment-methods`);
      setPaymentMethods(response.data);
    } catch (error) {
      console.error('Error fetching payment methods:', error);
      toast.error('Gagal mengambil data metode pembayaran');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editId) {
        await axiosInstance.put(`/payment-methods/${editId}`, formData);
        toast.success('Metode pembayaran berhasil diperbarui');
      } else {
        await axiosInstance.post(`/payment-methods`, formData);
        toast.success('Metode pembayaran berhasil ditambahkan');
      }
      setShowDialog(false);
      setFormData({
        name: '',
        type: 'cash',
        is_active: true,
      });
      setEditId(null);
      fetchPaymentMethods();
    } catch (error) {
      console.error('Error saving payment method:', error);
      toast.error('Gagal menyimpan metode pembayaran');
    }
  };

  const handleEdit = (method) => {
    setEditId(method.id);
    setFormData({
      name: method.name,
      type: method.type,
      is_active: method.is_active,
    });
    setShowDialog(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Apakah Anda yakin ingin menghapus metode pembayaran ini?')) {
      try {
        await axiosInstance.delete(`/payment-methods/${id}`);
        toast.success('Metode pembayaran berhasil dihapus');
        fetchPaymentMethods();
      } catch (error) {
        console.error('Error deleting payment method:', error);
        toast.error('Gagal menghapus metode pembayaran');
      }
    }
  };

  const handleAddNew = () => {
    setEditId(null);
    setFormData({
      name: '',
      type: 'cash',
      is_active: true,
    });
    setShowDialog(true);
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
      <div className="space-y-6" data-testid="payment-settings-page">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">Pengaturan Pembayaran</h1>
          <Button onClick={handleAddNew} className="bg-blue-600 hover:bg-blue-700" data-testid="add-payment-btn">
            <Plus className="h-4 w-4 mr-2" />
            Tambah Metode
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Metode Pembayaran Tersedia</CardTitle>
          </CardHeader>
          <CardContent>
            {paymentMethods.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12">
                <CreditCard className="h-16 w-16 text-gray-300 mb-4" />
                <p className="text-gray-500 mb-4">Belum ada metode pembayaran</p>
                <Button onClick={handleAddNew} variant="outline" data-testid="empty-add-payment-btn">
                  <Plus className="h-4 w-4 mr-2" />
                  Tambah Metode Pertama
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {paymentMethods.map((method) => (
                  <div
                    key={method.id}
                    className="p-4 border rounded-lg hover:shadow-md transition-shadow"
                    data-testid={`payment-method-${method.id}`}
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-2 bg-blue-100 rounded-lg">
                        {method.type === 'qris' ? (
                          <Smartphone className="h-5 w-5 text-blue-600" />
                        ) : (
                          <CreditCard className="h-5 w-5 text-blue-600" />
                        )}
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold">{method.name}</p>
                        <p className="text-sm text-gray-600 capitalize">{method.type}</p>
                      </div>
                      <span
                        className={`text-xs px-2 py-1 rounded-full ${
                          method.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {method.is_active ? 'Aktif' : 'Nonaktif'}
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => handleEdit(method)}
                        data-testid={`edit-payment-${method.id}`}
                      >
                        <Edit className="h-4 w-4 mr-2" />
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        onClick={() => handleDelete(method.id)}
                        data-testid={`delete-payment-${method.id}`}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Invoice Print Settings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Font Size</Label>
                  <Input type="number" placeholder="12" defaultValue="12" data-testid="font-size-input" />
                </div>
                <div className="space-y-2">
                  <Label>Margin</Label>
                  <Input type="number" placeholder="10" defaultValue="10" data-testid="margin-input" />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Logo URL</Label>
                <Input placeholder="https://example.com/logo.png" data-testid="logo-url-input" />
              </div>
              <div className="space-y-2">
                <Label>Header Text</Label>
                <Input placeholder="Nama Toko" data-testid="header-text-input" />
              </div>
              <div className="space-y-2">
                <Label>Footer Text</Label>
                <Input placeholder="Terima kasih telah berbelanja" data-testid="footer-text-input" />
              </div>
              <Button className="w-full" data-testid="save-invoice-settings-btn">
                Simpan Pengaturan Invoice
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent data-testid="payment-dialog">
          <DialogHeader>
            <DialogTitle>{editId ? 'Edit Metode Pembayaran' : 'Tambah Metode Pembayaran'}</DialogTitle>
            <DialogDescription>Masukkan informasi metode pembayaran</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nama Metode *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="QRIS"
                  required
                  data-testid="payment-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="type">Tipe *</Label>
                <Select value={formData.type} onValueChange={(value) => setFormData({ ...formData, type: value })}>
                  <SelectTrigger data-testid="payment-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="cash">Cash</SelectItem>
                    <SelectItem value="qris">QRIS</SelectItem>
                    <SelectItem value="card">Card</SelectItem>
                    <SelectItem value="transfer">Transfer</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="is_active">Status</Label>
                <Select
                  value={formData.is_active.toString()}
                  onValueChange={(value) => setFormData({ ...formData, is_active: value === 'true' })}
                >
                  <SelectTrigger data-testid="payment-status-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="true">Aktif</SelectItem>
                    <SelectItem value="false">Nonaktif</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)} data-testid="cancel-payment-btn">
                Batal
              </Button>
              <Button type="submit" className="bg-blue-600 hover:bg-blue-700" data-testid="save-payment-btn">
                {editId ? 'Update' : 'Simpan'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </Layout>
  );
};

export default PaymentSettings;