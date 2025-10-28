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
const API = `${BACKEND_URL}/api`;

const Categories = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editId, setEditId] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/categories`);
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
      toast.error('Gagal mengambil data kategori');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editId) {
        await axios.put(`${API}/categories/${editId}`, formData);
        toast.success('Kategori berhasil diperbarui');
      } else {
        await axios.post(`${API}/categories`, formData);
        toast.success('Kategori berhasil ditambahkan');
      }
      setShowDialog(false);
      setFormData({ name: '', description: '' });
      setEditId(null);
      fetchCategories();
    } catch (error) {
      console.error('Error saving category:', error);
      toast.error('Gagal menyimpan kategori');
    }
  };

  const handleEdit = (category) => {
    setEditId(category.id);
    setFormData({
      name: category.name,
      description: category.description || '',
    });
    setShowDialog(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Apakah Anda yakin ingin menghapus kategori ini?')) {
      try {
        await axios.delete(`${API}/categories/${id}`);
        toast.success('Kategori berhasil dihapus');
        fetchCategories();
      } catch (error) {
        console.error('Error deleting category:', error);
        toast.error('Gagal menghapus kategori');
      }
    }
  };

  const handleAddNew = () => {
    setEditId(null);
    setFormData({ name: '', description: '' });
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
      <div className="space-y-6" data-testid="categories-page">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">Kategori Produk</h1>
          <Button onClick={handleAddNew} className="bg-blue-600 hover:bg-blue-700" data-testid="add-category-btn">
            <Plus className="h-4 w-4 mr-2" />
            Tambah Kategori
          </Button>
        </div>

        {categories.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <p className="text-gray-500 mb-4">Belum ada kategori</p>
              <Button onClick={handleAddNew} variant="outline" data-testid="empty-add-category-btn">
                <Plus className="h-4 w-4 mr-2" />
                Tambah Kategori Pertama
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {categories.map((category) => (
              <Card key={category.id} className="hover:shadow-lg transition-shadow" data-testid={`category-card-${category.id}`}>
                <CardContent className="p-6">
                  <h3 className="font-semibold text-lg text-gray-800 mb-2">{category.name}</h3>
                  <p className="text-sm text-gray-600 mb-4">{category.description || 'Tidak ada deskripsi'}</p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => handleEdit(category)}
                      data-testid={`edit-category-${category.id}`}
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      onClick={() => handleDelete(category.id)}
                      data-testid={`delete-category-${category.id}`}
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
        <DialogContent data-testid="category-dialog">
          <DialogHeader>
            <DialogTitle>{editId ? 'Edit Kategori' : 'Tambah Kategori Baru'}</DialogTitle>
            <DialogDescription>Masukkan informasi kategori produk</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nama Kategori *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Masukkan nama kategori"
                  required
                  data-testid="category-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Deskripsi</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Masukkan deskripsi kategori"
                  rows={3}
                  data-testid="category-description-input"
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)} data-testid="cancel-category-btn">
                Batal
              </Button>
              <Button type="submit" className="bg-blue-600 hover:bg-blue-700" data-testid="save-category-btn">
                {editId ? 'Update' : 'Simpan'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </Layout>
  );
};

export default Categories;