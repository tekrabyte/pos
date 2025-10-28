import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Plus, UserCog, Percent } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Roles = () => {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    max_discount: '',
  });

  useEffect(() => {
    fetchRoles();
  }, []);

  const fetchRoles = async () => {
    try {
      const response = await axios.get(`${API}/roles`);
      setRoles(response.data);
    } catch (error) {
      console.error('Error fetching roles:', error);
      toast.error('Gagal mengambil data role');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        name: formData.name,
        max_discount: parseFloat(formData.max_discount),
      };
      await axios.post(`${API}/roles`, payload);
      toast.success('Role berhasil ditambahkan');
      setShowDialog(false);
      setFormData({
        name: '',
        max_discount: '',
      });
      fetchRoles();
    } catch (error) {
      console.error('Error saving role:', error);
      toast.error('Gagal menyimpan role');
    }
  };

  const handleAddNew = () => {
    setFormData({
      name: '',
      max_discount: '',
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
      <div className="space-y-6" data-testid="roles-page">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">Roles / Hak Akses</h1>
          <Button onClick={handleAddNew} className="bg-blue-600 hover:bg-blue-700" data-testid="add-role-btn">
            <Plus className="h-4 w-4 mr-2" />
            Tambah Role
          </Button>
        </div>

        {roles.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <UserCog className="h-16 w-16 text-gray-300 mb-4" />
              <p className="text-gray-500 mb-4">Belum ada role</p>
              <Button onClick={handleAddNew} variant="outline" data-testid="empty-add-role-btn">
                <Plus className="h-4 w-4 mr-2" />
                Tambah Role Pertama
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {roles.map((role) => (
              <Card key={role.id} className="hover:shadow-lg transition-shadow" data-testid={`role-card-${role.id}`}>
                <CardContent className="p-6">
                  <div className="flex items-start gap-3 mb-4">
                    <div className="p-2 bg-purple-100 rounded-lg">
                      <UserCog className="h-6 w-6 text-purple-600" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg text-gray-800">{role.name}</h3>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <Percent className="h-4 w-4 text-gray-500" />
                    <span className="text-gray-600">Max Diskon:</span>
                    <span className="font-semibold text-blue-600">{parseFloat(role.max_discount)}%</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent data-testid="role-dialog">
          <DialogHeader>
            <DialogTitle>Tambah Role Baru</DialogTitle>
            <DialogDescription>Masukkan informasi role/hak akses</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nama Role *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Manager"
                  required
                  data-testid="role-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="max_discount">Max Diskon (%) *</Label>
                <Input
                  id="max_discount"
                  type="number"
                  step="0.01"
                  value={formData.max_discount}
                  onChange={(e) => setFormData({ ...formData, max_discount: e.target.value })}
                  placeholder="20"
                  required
                  data-testid="role-discount-input"
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)} data-testid="cancel-role-btn">
                Batal
              </Button>
              <Button type="submit" className="bg-blue-600 hover:bg-blue-700" data-testid="save-role-btn">
                Simpan
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </Layout>
  );
};

export default Roles;