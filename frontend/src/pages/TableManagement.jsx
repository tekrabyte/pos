import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Plus, Edit, Trash2, Search, RefreshCw, QrCode, Download, Printer } from 'lucide-react';
import axiosInstance from '@/config/axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const TableManagement = () => {
  const [tables, setTables] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editId, setEditId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState({
    table_number: '',
    status: 'available',
  });

  useEffect(() => {
    fetchTables();
  }, []);

  const fetchTables = async () => {
    setLoading(true);
    try {
      const response = await axiosInstance.get('/tables');
      setTables(response.data.tables || response.data || []);
    } catch (error) {
      console.error('Error fetching tables:', error);
      toast.error('Gagal mengambil data meja');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editId) {
        await axiosInstance.put(`/tables/${editId}`, formData);
        toast.success('Meja berhasil diperbarui');
      } else {
        await axiosInstance.post('/tables', formData);
        toast.success('Meja berhasil ditambahkan');
      }
      setShowDialog(false);
      setFormData({ name: '', status: 'available' });
      setEditId(null);
      fetchTables();
    } catch (error) {
      console.error('Error saving table:', error);
      toast.error('Gagal menyimpan meja');
    }
  };

  const handleEdit = (table) => {
    setEditId(table.id);
    setFormData({
      name: table.name || '',
      status: table.status || 'available',
    });
    setShowDialog(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Apakah Anda yakin ingin menghapus meja ini?')) {
      try {
        await axiosInstance.delete(`/tables/${id}`);
        toast.success('Meja berhasil dihapus');
        fetchTables();
      } catch (error) {
        console.error('Error deleting table:', error);
        toast.error('Gagal menghapus meja');
      }
    }
  };

  const handleAddNew = () => {
    setEditId(null);
    setFormData({ name: '', status: 'available' });
    setShowDialog(true);
  };

  const regenerateQR = async (tableId) => {
    try {
      await axiosInstance.post(`/tables/${tableId}/regenerate-qr`);
      toast.success('QR Code berhasil di-generate ulang');
      fetchTables();
    } catch (error) {
      console.error('Error regenerating QR:', error);
      toast.error('Gagal generate QR Code');
    }
  };

  const downloadQR = (qrCode, tableName) => {
    const link = document.createElement('a');
    link.href = qrCode;
    link.download = `table-${tableName}-qr.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('QR Code berhasil diunduh');
  };

  const printQR = (qrCode, tableName) => {
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <html>
        <head>
          <title>Print QR Code - ${tableName}</title>
          <style>
            body {
              display: flex;
              flex-direction: column;
              justify-content: center;
              align-items: center;
              height: 100vh;
              margin: 0;
              font-family: Arial, sans-serif;
            }
            .print-container {
              text-align: center;
            }
            img {
              max-width: 300px;
              height: auto;
            }
            h2 {
              margin-top: 20px;
              font-size: 24px;
            }
            @media print {
              body { margin: 0; }
            }
          </style>
        </head>
        <body>
          <div class="print-container">
            <h2>${tableName}</h2>
            <img src="${qrCode}" alt="QR Code" />
            <p>Scan untuk memesan</p>
          </div>
          <script>
            window.onload = function() {
              window.print();
              window.onafterprint = function() {
                window.close();
              };
            };
          </script>
        </body>
      </html>
    `);
    printWindow.document.close();
  };

  const filteredTables = tables.filter(table =>
    table.name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusColor = (status) => {
    switch (status) {
      case 'available':
        return 'bg-green-100 text-green-800';
      case 'occupied':
        return 'bg-red-100 text-red-800';
      case 'reserved':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="text-gray-500">Memuat data meja...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Manajemen Meja</h1>
          <Button onClick={handleAddNew} className="bg-blue-600 hover:bg-blue-700">
            <Plus className="h-4 w-4 mr-2" />
            Tambah Meja
          </Button>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Cari meja..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button variant="outline" onClick={fetchTables}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {filteredTables.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <p className="text-gray-500">Tidak ada meja ditemukan</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredTables.map((table) => (
              <Card key={table.id} className="hover:shadow-lg transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xl font-bold text-gray-800">{table.name}</h3>
                    <Badge className={getStatusColor(table.status)}>
                      {table.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {table.qr_code && (
                    <div className="bg-white p-2 rounded border border-gray-200">
                      <img
                        src={table.qr_code}
                        alt={`QR Code ${table.name}`}
                        className="w-full h-auto"
                      />
                    </div>
                  )}
                  
                  <div className="flex flex-wrap gap-2">
                    {table.qr_code && (
                      <>
                        <Button
                          variant="outline"
                          size="sm"
                          className="flex-1"
                          onClick={() => downloadQR(table.qr_code, table.name)}
                        >
                          <Download className="h-4 w-4 mr-1" />
                          Download
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="flex-1"
                          onClick={() => printQR(table.qr_code, table.name)}
                        >
                          <Printer className="h-4 w-4 mr-1" />
                          Print
                        </Button>
                      </>
                    )}
                  </div>
                  
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => regenerateQR(table.id)}
                      className="flex-1"
                    >
                      <QrCode className="h-4 w-4 mr-1" />
                      Regenerate QR
                    </Button>
                  </div>
                  
                  <div className="flex gap-2 pt-2 border-t">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => handleEdit(table)}
                    >
                      <Edit className="h-4 w-4 mr-1" />
                      Edit
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      onClick={() => handleDelete(table.id)}
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
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editId ? 'Edit Meja' : 'Tambah Meja Baru'}</DialogTitle>
            <DialogDescription>Masukkan informasi meja</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nama/Nomor Meja *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Contoh: Meja 1, Table A"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <select
                  id="status"
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="available">Available</option>
                  <option value="occupied">Occupied</option>
                  <option value="reserved">Reserved</option>
                </select>
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowDialog(false)}
              >
                Batal
              </Button>
              <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
                {editId ? 'Update' : 'Simpan'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </Layout>
  );
};

export default TableManagement;
