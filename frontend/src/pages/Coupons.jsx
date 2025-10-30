import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Edit, Trash2, Ticket } from 'lucide-react';
import axiosInstance from '@/config/axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}`;

const Coupons = () => {
  const [coupons, setCoupons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editId, setEditId] = useState(null);
  const [formData, setFormData] = useState({
    code: '',
    discount_type: 'percentage',
    discount_value: '',
    min_purchase: '',
    max_discount: '',
    is_active: true,
  });

  useEffect(() => {
    fetchCoupons();
  }, []);

  const fetchCoupons = async () => {
    try {
      const response = await axiosInstance.get(`/coupons`);
      setCoupons(response.data.coupons || response.data || []);
    } catch (error) {
      console.error('Error fetching coupons:', error);
      toast.error('Gagal mengambil data kupon');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        discount_value: parseFloat(formData.discount_value),
        min_purchase: formData.min_purchase ? parseFloat(formData.min_purchase) : null,
        max_discount: formData.max_discount ? parseFloat(formData.max_discount) : null,
      };

      if (editId) {
        await axiosInstance.put(`/coupons/${editId}`, payload);
        toast.success('Kupon berhasil diperbarui');
      } else {
        await axiosInstance.post(`/coupons`, payload);
        toast.success('Kupon berhasil ditambahkan');
      }
      setShowDialog(false);
      setFormData({
        code: '',
        discount_type: 'percentage',
        discount_value: '',
        min_purchase: '',
        max_discount: '',
        is_active: true,
      });
      setEditId(null);
      fetchCoupons();
    } catch (error) {
      console.error('Error saving coupon:', error);
      toast.error('Gagal menyimpan kupon');
    }
  };

  const handleEdit = (coupon) => {
    setEditId(coupon.id);
    setFormData({
      code: coupon.code,
      discount_type: coupon.discount_type,
      discount_value: coupon.discount_value.toString(),
      min_purchase: coupon.min_purchase?.toString() || '',
      max_discount: coupon.max_discount?.toString() || '',
      is_active: coupon.is_active,
    });
    setShowDialog(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Apakah Anda yakin ingin menghapus kupon ini?')) {
      try {
        await axiosInstance.delete(`/coupons/${id}`);
        toast.success('Kupon berhasil dihapus');
        fetchCoupons();
      } catch (error) {
        console.error('Error deleting coupon:', error);
        toast.error('Gagal menghapus kupon');
      }
    }
  };

  const handleAddNew = () => {
    setEditId(null);
    setFormData({
      code: '',
      discount_type: 'percentage',
      discount_value: '',
      min_purchase: '',
      max_discount: '',
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
      <div className="space-y-6" data-testid="coupons-page">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">Kupon & Diskon</h1>
          <Button onClick={handleAddNew} className="bg-blue-600 hover:bg-blue-700" data-testid="add-coupon-btn">
            <Plus className="h-4 w-4 mr-2" />
            Tambah Kupon
          </Button>
        </div>

        {coupons.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Ticket className="h-16 w-16 text-gray-300 mb-4" />
              <p className="text-gray-500 mb-4">Belum ada kupon</p>
              <Button onClick={handleAddNew} variant="outline" data-testid="empty-add-coupon-btn">
                <Plus className="h-4 w-4 mr-2" />
                Tambah Kupon Pertama
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {coupons.map((coupon) => (
              <Card
                key={coupon.id}
                className={`hover:shadow-lg transition-shadow ${!coupon.is_active ? 'opacity-60' : ''}`}
                data-testid={`coupon-card-${coupon.id}`}
              >
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-blue-100 rounded-lg">
                        <Ticket className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="font-bold text-lg">{coupon.code}</p>
                        <span
                          className={`text-xs px-2 py-1 rounded-full ${
                            coupon.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          {coupon.is_active ? 'Aktif' : 'Nonaktif'}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-2 text-sm text-gray-600 mb-4">
                    <p>
                      <span className="font-medium">Diskon:</span>{' '}
                      {coupon.discount_type === 'percentage'
                        ? `${coupon.discount_value}%`
                        : `Rp ${parseFloat(coupon.discount_value).toLocaleString('id-ID')}`}
                    </p>
                    {coupon.min_purchase && (
                      <p>
                        <span className="font-medium">Min. Pembelian:</span> Rp{' '}
                        {parseFloat(coupon.min_purchase).toLocaleString('id-ID')}
                      </p>
                    )}
                    {coupon.max_discount && (
                      <p>
                        <span className="font-medium">Max. Diskon:</span> Rp{' '}
                        {parseFloat(coupon.max_discount).toLocaleString('id-ID')}
                      </p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => handleEdit(coupon)}
                      data-testid={`edit-coupon-${coupon.id}`}
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      onClick={() => handleDelete(coupon.id)}
                      data-testid={`delete-coupon-${coupon.id}`}
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
        <DialogContent data-testid="coupon-dialog">
          <DialogHeader>
            <DialogTitle>{editId ? 'Edit Kupon' : 'Tambah Kupon Baru'}</DialogTitle>
            <DialogDescription>Masukkan informasi kupon diskon</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="code">Kode Kupon *</Label>
                <Input
                  id="code"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                  placeholder="DISKON50"
                  required
                  data-testid="coupon-code-input"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="discount_type">Tipe Diskon</Label>
                  <Select
                    value={formData.discount_type}
                    onValueChange={(value) => setFormData({ ...formData, discount_type: value })}
                  >
                    <SelectTrigger data-testid="coupon-type-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="percentage">Persentase</SelectItem>
                      <SelectItem value="fixed">Nominal</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="discount_value">Nilai Diskon *</Label>
                  <Input
                    id="discount_value"
                    type="number"
                    step="0.01"
                    value={formData.discount_value}
                    onChange={(e) => setFormData({ ...formData, discount_value: e.target.value })}
                    placeholder="10"
                    required
                    data-testid="coupon-value-input"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="min_purchase">Min. Pembelian</Label>
                  <Input
                    id="min_purchase"
                    type="number"
                    step="0.01"
                    value={formData.min_purchase}
                    onChange={(e) => setFormData({ ...formData, min_purchase: e.target.value })}
                    placeholder="100000"
                    data-testid="coupon-min-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="max_discount">Max. Diskon</Label>
                  <Input
                    id="max_discount"
                    type="number"
                    step="0.01"
                    value={formData.max_discount}
                    onChange={(e) => setFormData({ ...formData, max_discount: e.target.value })}
                    placeholder="50000"
                    data-testid="coupon-max-input"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="is_active">Status</Label>
                <Select
                  value={formData.is_active.toString()}
                  onValueChange={(value) => setFormData({ ...formData, is_active: value === 'true' })}
                >
                  <SelectTrigger data-testid="coupon-status-select">
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
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)} data-testid="cancel-coupon-btn">
                Batal
              </Button>
              <Button type="submit" className="bg-blue-600 hover:bg-blue-700" data-testid="save-coupon-btn">
                {editId ? 'Update' : 'Simpan'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </Layout>
  );
};

export default Coupons;