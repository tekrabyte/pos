import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Plus, Edit, Trash2 } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}`;

const Brands = () => {
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editId, setEditId] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    logo_url: '',
  });

  useEffect(() => {
    fetchBrands();
  }, []);

  const fetchBrands = async () => {
    try {
      const response = await axios.get(`${API}/brands`);
      setBrands(response.data);
    } catch (error) {
      console.error('Error fetching brands:', error);
      toast.error('Gagal mengambil data brand');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editId) {
        await axios.put(`${API}/brands/${editId}`, formData);
        toast.success('Brand berhasil diperbarui');
      } else {
        await axios.post(`${API}/brands`, formData);
        toast.success('Brand berhasil ditambahkan');
      }
      setShowDialog(false);
      setFormData({ name: '', description: '', logo_url: '' });
      setEditId(null);
      fetchBrands();
    } catch (error) {
      console.error('Error saving brand:', error);
      toast.error('Gagal menyimpan brand');
    }
  };

  const handleEdit = (brand) => {
    setEditId(brand.id);
    setFormData({
      name: brand.name,
      description: brand.description || '',
      logo_url: brand.logo_url || '',
    });
    setShowDialog(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Apakah Anda yakin ingin menghapus brand ini?')) {
      try {
        await axios.delete(`${API}/brands/${id}`);
        toast.success('Brand berhasil dihapus');
        fetchBrands();
      } catch (error) {
        console.error('Error deleting brand:', error);
        toast.error('Gagal menghapus brand');
      }
    }
  };

  const handleAddNew = () => {
    setEditId(null);
    setFormData({ name: '', description: '', logo_url: '' });
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
      <div className="space-y-6" data-testid="brands-page">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">Brand / Merek</h1>
          <Button onClick={handleAddNew} className="bg-blue-600 hover:bg-blue-700" data-testid="add-brand-btn">
            <Plus className="h-4 w-4 mr-2" />
            Tambah Brand
          </Button>
        </div>

        {brands.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <p className="text-gray-500 mb-4">Belum ada brand</p>
              <Button onClick={handleAddNew} variant="outline" data-testid="empty-add-brand-btn">
                <Plus className="h-4 w-4 mr-2" />
                Tambah Brand Pertama
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {brands.map((brand) => (
              <Card key={brand.id} className="hover:shadow-lg transition-shadow" data-testid={`brand-card-${brand.id}`}>
                <CardContent className="p-6">
                  {brand.logo_url && (
                    <div className="mb-4 flex justify-center">
                      <img src={brand.logo_url} alt={brand.name} className="h-16 object-contain" />
                    </div>
                  )}
                  <h3 className="font-semibold text-lg text-gray-800 mb-2 text-center">{brand.name}</h3>
                  <p className="text-sm text-gray-600 mb-4 text-center">{brand.description || 'Tidak ada deskripsi'}</p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => handleEdit(brand)}
                      data-testid={`edit-brand-${brand.id}`}
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      onClick={() => handleDelete(brand.id)}
                      data-testid={`delete-brand-${brand.id}`}
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
        <DialogContent data-testid="brand-dialog">
          <DialogHeader>
            <DialogTitle>{editId ? 'Edit Brand' : 'Tambah Brand Baru'}</DialogTitle>
            <DialogDescription>Masukkan informasi brand produk</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nama Brand *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Masukkan nama brand"
                  required
                  data-testid="brand-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="logo_url">URL Logo</Label>
                <Input
                  id="logo_url"
                  value={formData.logo_url}
                  onChange={(e) => setFormData({ ...formData, logo_url: e.target.value })}
                  placeholder="https://example.com/logo.png"
                  data-testid="brand-logo-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Deskripsi</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Masukkan deskripsi brand"
                  rows={3}
                  data-testid="brand-description-input"
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)} data-testid="cancel-brand-btn">
                Batal
              </Button>
              <Button type="submit" className="bg-blue-600 hover:bg-blue-700" data-testid="save-brand-btn">
                {editId ? 'Update' : 'Simpan'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </Layout>
  );
};

export default Brands;