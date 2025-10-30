import React, { useState, useEffect } from 'react';
import { UserPlus, Edit, Trash2, Search, Shield, User } from 'lucide-react';
import Layout from '@/components/Layout';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { toast } from 'sonner';
import axiosInstance from '@/config/axios';

const UsersManagement = () => {
  const [users, setUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRole, setSelectedRole] = useState('all');
  const [isLoading, setIsLoading] = useState(false);
  const [showUserDialog, setShowUserDialog] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [userForm, setUserForm] = useState({
    name: '',
    username: '',
    email: '',
    password: '',
    role: 'staff',
    outlet_id: 1,
    is_active: true,
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setIsLoading(true);
      const response = await axiosInstance.get('/users');
      const usersData = response.data.users || response.data || [];
      setUsers(Array.isArray(usersData) ? usersData : []);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Gagal memuat data pengguna');
      setUsers([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateUser = () => {
    setUserForm({
      name: '',
      username: '',
      email: '',
      password: '',
      role: 'staff',
      outlet_id: 1,
      is_active: true,
    });
    setEditingUser(null);
    setShowUserDialog(true);
  };

  const handleEditUser = (user) => {
    setUserForm({
      name: user.name || '',
      username: user.username || '',
      email: user.email || '',
      password: '', // Don't show existing password
      role: user.role || 'staff',
      outlet_id: user.outlet_id || 1,
      is_active: user.is_active !== undefined ? user.is_active : true,
    });
    setEditingUser(user);
    setShowUserDialog(true);
  };

  const handleSaveUser = async () => {
    // Validation
    if (!userForm.name || !userForm.username) {
      toast.error('Nama dan username wajib diisi');
      return;
    }

    if (!editingUser && !userForm.password) {
      toast.error('Password wajib diisi untuk user baru');
      return;
    }

    try {
      if (editingUser) {
        // Update existing user
        const updateData = {
          name: userForm.name,
          username: userForm.username,
          email: userForm.email,
          role: userForm.role,
          outlet_id: userForm.outlet_id,
          is_active: userForm.is_active,
        };

        // Only include password if it's provided
        if (userForm.password) {
          updateData.password = userForm.password;
        }

        await axios.put(`${API_URL}/users/${editingUser.id}`, updateData);
        toast.success('User berhasil diupdate');
      } else {
        // Create new user
        await axios.post(`${API_URL}/users`, userForm);
        toast.success('User berhasil dibuat');
      }

      setShowUserDialog(false);
      fetchUsers();
    } catch (error) {
      console.error('Error saving user:', error);
      const errorMessage = error.response?.data?.message || 'Gagal menyimpan user';
      toast.error(errorMessage);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Apakah Anda yakin ingin menghapus user ini?')) return;

    try {
      await axios.delete(`${API_URL}/users/${userId}`);
      toast.success('User berhasil dihapus');
      fetchUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      toast.error('Gagal menghapus user');
    }
  };

  const filteredUsers = users.filter((user) => {
    const matchesSearch =
      user.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.username?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRole = selectedRole === 'all' || user.role === selectedRole;
    return matchesSearch && matchesRole;
  });

  const getRoleBadgeColor = (role) => {
    switch (role) {
      case 'admin':
        return 'bg-purple-100 text-purple-700 border-purple-300';
      case 'cashier':
        return 'bg-blue-100 text-blue-700 border-blue-300';
      case 'staff':
        return 'bg-green-100 text-green-700 border-green-300';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300';
    }
  };

  return (
    <Layout>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 dark:text-white">Users & Staff Management</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">Kelola pengguna dan staff sistem POS</p>
          </div>
          <Button onClick={handleCreateUser} className="gap-2">
            <UserPlus className="w-4 h-4" />
            Tambah User
          </Button>
        </div>

        {/* Filters */}
        <Card className="p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
              <Input
                type="text"
                placeholder="Cari nama, username, atau email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              <Button
                variant={selectedRole === 'all' ? 'default' : 'outline'}
                onClick={() => setSelectedRole('all')}
                size="sm"
              >
                Semua
              </Button>
              <Button
                variant={selectedRole === 'admin' ? 'default' : 'outline'}
                onClick={() => setSelectedRole('admin')}
                size="sm"
              >
                Admin
              </Button>
              <Button
                variant={selectedRole === 'cashier' ? 'default' : 'outline'}
                onClick={() => setSelectedRole('cashier')}
                size="sm"
              >
                Cashier
              </Button>
              <Button
                variant={selectedRole === 'staff' ? 'default' : 'outline'}
                onClick={() => setSelectedRole('staff')}
                size="sm"
              >
                Staff
              </Button>
            </div>
          </div>
        </Card>

        {/* Users List */}
        {isLoading ? (
          <div className="text-center py-8">Memuat data...</div>
        ) : filteredUsers.length === 0 ? (
          <Card className="p-8 text-center">
            <User className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">Tidak ada user ditemukan</p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredUsers.map((user) => (
              <Card key={user.id} className="p-4 hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg">
                      {user.name?.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-800 dark:text-white">{user.name}</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">@{user.username}</p>
                    </div>
                  </div>
                  <Badge className={getRoleBadgeColor(user.role)}>
                    {user.role}
                  </Badge>
                </div>

                <div className="space-y-2 mb-4">
                  {user.email && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-2">
                      <span className="font-medium">Email:</span>
                      {user.email}
                    </p>
                  )}
                  <div className="flex items-center gap-2">
                    <Badge variant={user.is_active ? 'default' : 'secondary'}>
                      {user.is_active ? 'Aktif' : 'Nonaktif'}
                    </Badge>
                    {user.outlet_id && (
                      <span className="text-xs text-gray-500">Outlet ID: {user.outlet_id}</span>
                    )}
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEditUser(user)}
                    className="flex-1"
                  >
                    <Edit className="w-4 h-4 mr-1" />
                    Edit
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDeleteUser(user.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* User Dialog */}
        <Dialog open={showUserDialog} onOpenChange={setShowUserDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>{editingUser ? 'Edit User' : 'Tambah User Baru'}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="userName">Nama Lengkap *</Label>
                <Input
                  id="userName"
                  value={userForm.name}
                  onChange={(e) => setUserForm({ ...userForm, name: e.target.value })}
                  placeholder="John Doe"
                />
              </div>

              <div>
                <Label htmlFor="userUsername">Username *</Label>
                <Input
                  id="userUsername"
                  value={userForm.username}
                  onChange={(e) => setUserForm({ ...userForm, username: e.target.value })}
                  placeholder="johndoe"
                />
              </div>

              <div>
                <Label htmlFor="userEmail">Email</Label>
                <Input
                  id="userEmail"
                  type="email"
                  value={userForm.email}
                  onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                  placeholder="john@example.com"
                />
              </div>

              <div>
                <Label htmlFor="userPassword">
                  Password {!editingUser && '*'} {editingUser && '(kosongkan jika tidak diubah)'}
                </Label>
                <Input
                  id="userPassword"
                  type="password"
                  value={userForm.password}
                  onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                  placeholder={editingUser ? 'Kosongkan jika tidak diubah' : 'Masukkan password'}
                />
              </div>

              <div>
                <Label htmlFor="userRole">Role</Label>
                <select
                  id="userRole"
                  value={userForm.role}
                  onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="admin">Admin</option>
                  <option value="cashier">Cashier</option>
                  <option value="staff">Staff</option>
                </select>
              </div>

              <div>
                <Label htmlFor="userOutlet">Outlet ID</Label>
                <Input
                  id="userOutlet"
                  type="number"
                  value={userForm.outlet_id}
                  onChange={(e) => setUserForm({ ...userForm, outlet_id: parseInt(e.target.value) })}
                  placeholder="1"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="userActive"
                  checked={userForm.is_active}
                  onChange={(e) => setUserForm({ ...userForm, is_active: e.target.checked })}
                  className="w-4 h-4"
                />
                <Label htmlFor="userActive" className="cursor-pointer">User Aktif</Label>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowUserDialog(false)}>
                Batal
              </Button>
              <Button onClick={handleSaveUser}>
                {editingUser ? 'Update User' : 'Buat User'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
};

export default UsersManagement;
