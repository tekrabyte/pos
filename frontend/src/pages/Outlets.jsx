import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Checkbox } from '@/components/ui/checkbox';
import { Plus, Edit, Store, MapPin, Trash2 } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Outlets = () => {
  const [outlets, setOutlets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editId, setEditId] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    city: '',
    country: '',
    postal_code: '',
    is_main: false,
  });

  useEffect(() => {
    fetchOutlets();
  }, []);

  const fetchOutlets = async () => {
    try {
      const response = await axios.get(`${API}/outlets`);
      setOutlets(response.data);
    } catch (error) {
      console.error('Error fetching outlets:', error);
      toast.error('Gagal mengambil data outlet');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editId) {
        await axios.put(`${API}/outlets/${editId}`, formData);
        toast.success('Outlet berhasil diperbarui');
      } else {
        await axios.post(`${API}/outlets`, formData);
        toast.success('Outlet berhasil ditambahkan');
      }
      setShowDialog(false);
      setFormData({
        name: '',
        address: '',
        city: '',
        country: '',
        postal_code: '',
        is_main: false,
      });
      setEditId(null);
      fetchOutlets();
    } catch (error) {
      console.error('Error saving outlet:', error);
      toast.error('Gagal menyimpan outlet');
    }
  };

  const handleEdit = (outlet) => {
    setEditId(outlet.id);
    setFormData({
      name: outlet.name,
      address: outlet.address || '',
      city: outlet.city || '',
      country: outlet.country || '',
      postal_code: outlet.postal_code || '',
      is_main: outlet.is_main || false,
    });
    setShowDialog(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Apakah Anda yakin ingin menghapus outlet ini?')) {
      try {
        await axios.delete(`${API}/outlets/${id}`);
        toast.success('Outlet berhasil dihapus');
        fetchOutlets();
      } catch (error) {
        console.error('Error deleting outlet:', error);
        toast.error('Gagal menghapus outlet');
      }
    }
  };

  const handleAddNew = () => {
    setEditId(null);
    setFormData({
      name: '',
      address: '',
      city: '',
      country: '',
      postal_code: '',
      is_main: false,
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
      <div className="space-y-6" data-testid="outlets-page">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">Outlet / Cabang</h1>
          <Button onClick={handleAddNew} className="bg-blue-600 hover:bg-blue-700" data-testid="add-outlet-btn">
            <Plus className="h-4 w-4 mr-2" />
            Tambah Outlet
          </Button>
        </div>

        {outlets.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Store className="h-16 w-16 text-gray-300 mb-4" />
              <p className="text-gray-500 mb-4">Belum ada outlet</p>
              <Button onClick={handleAddNew} variant="outline" data-testid="empty-add-outlet-btn">
                <Plus className="h-4 w-4 mr-2" />
                Tambah Outlet Pertama
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {outlets.map((outlet) => (
              <Card key={outlet.id} className="hover:shadow-lg transition-shadow" data-testid={`outlet-card-${outlet.id}`}>
                <CardContent className="p-6">
                  <div className="flex items-start gap-3 mb-4">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <Store className="h-6 w-6 text-blue-600" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-lg text-gray-800">{outlet.name}</h3>
                        {outlet.is_main && (
                          <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full">
                            Main
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="space-y-2 text-sm text-gray-600 mb-4">
                    <div className="flex items-start gap-2">
                      <MapPin className="h-4 w-4 mt-0.5 flex-shrink-0" />
                      <div>
                        <p>{outlet.address}</p>
                        <p>
                          {outlet.city && `${outlet.city}, `}
                          {outlet.country}
                          {outlet.postal_code && ` ${outlet.postal_code}`}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => handleEdit(outlet)}
                      data-testid={`edit-outlet-${outlet.id}`}
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      onClick={() => handleDelete(outlet.id)}
                      data-testid={`delete-outlet-${outlet.id}`}
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
        <DialogContent className="max-w-xl" data-testid="outlet-dialog">
          <DialogHeader>
            <DialogTitle>{editId ? 'Edit Outlet' : 'Tambah Outlet Baru'}</DialogTitle>
            <DialogDescription>Masukkan informasi outlet/cabang</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nama Outlet *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Cabang Utama"
                  required
                  data-testid="outlet-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="address">Alamat *</Label>
                <Input
                  id="address"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  placeholder="Jl. Contoh No. 123"
                  required
                  data-testid="outlet-address-input"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="city">Kota</Label>
                  <Input
                    id="city"
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    placeholder="Jakarta"
                    data-testid="outlet-city-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="country">Negara</Label>
                  <Input
                    id="country"
                    value={formData.country}
                    onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                    placeholder="Indonesia"
                    data-testid="outlet-country-input"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="postal_code">Kode Pos</Label>
                <Input
                  id="postal_code"
                  value={formData.postal_code}
                  onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
                  placeholder="12345"
                  data-testid="outlet-postal-input"
                />
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_main"
                  checked={formData.is_main}
                  onCheckedChange={(checked) => setFormData({ ...formData, is_main: checked })}
                  data-testid="outlet-main-checkbox"
                />
                <Label htmlFor="is_main" className="cursor-pointer">Set sebagai outlet utama</Label>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)} data-testid="cancel-outlet-btn">
                Batal
              </Button>
              <Button type="submit" className="bg-blue-600 hover:bg-blue-700" data-testid="save-outlet-btn">
                {editId ? 'Update' : 'Simpan'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </Layout>
  );
};

export default Outlets;
