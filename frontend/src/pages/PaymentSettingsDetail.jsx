import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Upload, Save, X, QrCode, CreditCard, Plus, Settings, Edit, Trash2, Smartphone } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}`;

const PaymentSettingsDetail = () => {
  const [loading, setLoading] = useState(false);
  const [qrisImage, setQrisImage] = useState(null);
  const [qrisPreview, setQrisPreview] = useState('');
  const [bankAccounts, setBankAccounts] = useState([]);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [showMethodDialog, setShowMethodDialog] = useState(false);
  const [editMethodId, setEditMethodId] = useState(null);
  const [methodFormData, setMethodFormData] = useState({
    name: '',
    type: 'cash',
    is_active: true,
  });
  const [qrisSettings, setQrisSettings] = useState({
    merchant_name: 'QR Scan & Dine',
    merchant_id: '',
    qris_image_url: '',
  });

  useEffect(() => {
    fetchBankAccounts();
    fetchQrisSettings();
    fetchPaymentMethods();
  }, []);

  const fetchBankAccounts = async () => {
    try {
      const response = await axios.get(`${API}/bank-accounts`);
      setBankAccounts(response.data);
    } catch (error) {
      console.error('Error fetching bank accounts:', error);
    }
  };

  const fetchQrisSettings = async () => {
    try {
      const response = await axios.get(`${API}/payment-settings/qris`);
      if (response.data) {
        setQrisSettings(response.data);
        if (response.data.qris_image_url) {
          setQrisPreview(response.data.qris_image_url);
        }
      }
    } catch (error) {
      console.log('QRIS settings not found, using defaults');
    }
  };

  const fetchPaymentMethods = async () => {
    try {
      const response = await axios.get(`${API}/payment-methods`);
      setPaymentMethods(response.data);
    } catch (error) {
      console.error('Error fetching payment methods:', error);
      toast.error('Gagal mengambil data metode pembayaran');
    }
  };

  const handleMethodSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editMethodId) {
        await axios.put(`${API}/payment-methods/${editMethodId}`, methodFormData);
        toast.success('Metode pembayaran berhasil diperbarui');
      } else {
        await axios.post(`${API}/payment-methods`, methodFormData);
        toast.success('Metode pembayaran berhasil ditambahkan');
      }
      setShowMethodDialog(false);
      setMethodFormData({
        name: '',
        type: 'cash',
        is_active: true,
      });
      setEditMethodId(null);
      fetchPaymentMethods();
    } catch (error) {
      console.error('Error saving payment method:', error);
      toast.error('Gagal menyimpan metode pembayaran');
    }
  };

  const handleEditMethod = (method) => {
    setEditMethodId(method.id);
    setMethodFormData({
      name: method.name,
      type: method.type,
      is_active: method.is_active,
    });
    setShowMethodDialog(true);
  };

  const handleDeleteMethod = async (id) => {
    if (window.confirm('Apakah Anda yakin ingin menghapus metode pembayaran ini?')) {
      try {
        await axios.delete(`${API}/payment-methods/${id}`);
        toast.success('Metode pembayaran berhasil dihapus');
        fetchPaymentMethods();
      } catch (error) {
        console.error('Error deleting payment method:', error);
        toast.error('Gagal menghapus metode pembayaran');
      }
    }
  };

  const handleAddNewMethod = () => {
    setEditMethodId(null);
    setMethodFormData({
      name: '',
      type: 'cash',
      is_active: true,
    });
    setShowMethodDialog(true);
  };

  const handleQrisImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        toast.error('Ukuran file terlalu besar. Maksimal 5MB');
        return;
      }
      setQrisImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setQrisPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSaveQris = async () => {
    try {
      setLoading(true);
      let qrisImageUrl = qrisSettings.qris_image_url;

      // Upload image if new file selected
      if (qrisImage) {
        const formData = new FormData();
        formData.append('file', qrisImage);

        const uploadResponse = await axios.post(`${API}/upload/qris`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        qrisImageUrl = uploadResponse.data.url;
      }

      // Save QRIS settings
      await axios.post(`${API}/payment-settings/qris`, {
        merchant_name: qrisSettings.merchant_name,
        merchant_id: qrisSettings.merchant_id,
        qris_image_url: qrisImageUrl,
      });

      toast.success('Pengaturan QRIS berhasil disimpan');
      fetchQrisSettings();
      setQrisImage(null);
    } catch (error) {
      console.error('Error saving QRIS settings:', error);
      toast.error('Gagal menyimpan pengaturan QRIS');
    } finally {
      setLoading(false);
    }
  };

  const handleAddBankAccount = async () => {
    const accountName = prompt('Nama Pemilik Rekening:');
    if (!accountName) return;

    const bankName = prompt('Nama Bank:');
    if (!bankName) return;

    const accountNumber = prompt('Nomor Rekening:');
    if (!accountNumber) return;

    try {
      await axios.post(`${API}/bank-accounts`, {
        account_name: accountName,
        bank_name: bankName,
        account_number: accountNumber,
        is_active: true,
      });
      toast.success('Rekening bank berhasil ditambahkan');
      fetchBankAccounts();
    } catch (error) {
      console.error('Error adding bank account:', error);
      toast.error('Gagal menambahkan rekening bank');
    }
  };

  const handleDeleteBankAccount = async (id) => {
    if (!window.confirm('Apakah Anda yakin ingin menghapus rekening ini?')) return;

    try {
      await axios.delete(`${API}/bank-accounts/${id}`);
      toast.success('Rekening bank berhasil dihapus');
      fetchBankAccounts();
    } catch (error) {
      console.error('Error deleting bank account:', error);
      toast.error('Gagal menghapus rekening bank');
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Detail Pengaturan Pembayaran</h1>
            <p className="text-sm text-gray-500 mt-1">Kelola metode pembayaran untuk customer</p>
          </div>
        </div>

        <Tabs defaultValue="methods" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="methods" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Metode Pembayaran
            </TabsTrigger>
            <TabsTrigger value="qris" className="flex items-center gap-2">
              <QrCode className="h-4 w-4" />
              QRIS
            </TabsTrigger>
            <TabsTrigger value="bank" className="flex items-center gap-2">
              <CreditCard className="h-4 w-4" />
              Transfer Bank
            </TabsTrigger>
          </TabsList>

          <TabsContent value="methods" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Kelola Metode Pembayaran</CardTitle>
                <Button onClick={handleAddNewMethod} size="sm" className="bg-blue-600 hover:bg-blue-700" data-testid="add-payment-btn">
                  <Plus className="h-4 w-4 mr-2" />
                  Tambah Metode
                </Button>
              </CardHeader>
              <CardContent>
                {paymentMethods.length === 0 ? (
                  <div className="text-center py-12">
                    <CreditCard className="h-16 w-16 mx-auto text-gray-300 mb-4" />
                    <p className="text-gray-500 mb-4">Belum ada metode pembayaran</p>
                    <Button onClick={handleAddNewMethod} variant="outline" data-testid="empty-add-payment-btn">
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
                            onClick={() => handleEditMethod(method)}
                            data-testid={`edit-payment-${method.id}`}
                          >
                            <Edit className="h-4 w-4 mr-2" />
                            Edit
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            onClick={() => handleDeleteMethod(method.id)}
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
          </TabsContent>

          <TabsContent value="qris" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Pengaturan QRIS</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="merchant_name">Nama Merchant</Label>
                  <Input
                    id="merchant_name"
                    value={qrisSettings.merchant_name}
                    onChange={(e) => setQrisSettings({ ...qrisSettings, merchant_name: e.target.value })}
                    placeholder="Nama toko Anda"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="merchant_id">Merchant ID (Opsional)</Label>
                  <Input
                    id="merchant_id"
                    value={qrisSettings.merchant_id}
                    onChange={(e) => setQrisSettings({ ...qrisSettings, merchant_id: e.target.value })}
                    placeholder="ID123456789"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Upload QRIS Image</Label>
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors">
                    {qrisPreview ? (
                      <div className="space-y-4">
                        <div className="flex justify-center">
                          <img
                            src={qrisPreview}
                            alt="QRIS Preview"
                            className="max-w-xs max-h-64 object-contain"
                          />
                        </div>
                        <div className="flex gap-2 justify-center">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setQrisImage(null);
                              setQrisPreview('');
                            }}
                          >
                            <X className="h-4 w-4 mr-2" />
                            Hapus
                          </Button>
                          <Label htmlFor="qris-upload">
                            <Button variant="outline" size="sm" asChild>
                              <span>
                                <Upload className="h-4 w-4 mr-2" />
                                Ganti Gambar
                              </span>
                            </Button>
                          </Label>
                        </div>
                      </div>
                    ) : (
                      <Label htmlFor="qris-upload" className="cursor-pointer">
                        <div className="space-y-2">
                          <Upload className="h-12 w-12 mx-auto text-gray-400" />
                          <div>
                            <p className="text-sm font-medium text-gray-700">
                              Klik untuk upload QRIS image
                            </p>
                            <p className="text-xs text-gray-500">PNG, JPG up to 5MB</p>
                          </div>
                        </div>
                      </Label>
                    )}
                    <Input
                      id="qris-upload"
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={handleQrisImageChange}
                    />
                  </div>
                  <p className="text-xs text-gray-500">
                    Upload gambar QRIS statis dari merchant Anda untuk pembayaran manual
                  </p>
                </div>

                <div className="flex justify-end">
                  <Button
                    onClick={handleSaveQris}
                    disabled={loading}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    <Save className="h-4 w-4 mr-2" />
                    {loading ? 'Menyimpan...' : 'Simpan Pengaturan QRIS'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="bank" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Rekening Bank</CardTitle>
                <Button onClick={handleAddBankAccount} size="sm" className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="h-4 w-4 mr-2" />
                  Tambah Rekening
                </Button>
              </CardHeader>
              <CardContent>
                {bankAccounts.length === 0 ? (
                  <div className="text-center py-12">
                    <CreditCard className="h-16 w-16 mx-auto text-gray-300 mb-4" />
                    <p className="text-gray-500 mb-4">Belum ada rekening bank</p>
                    <Button onClick={handleAddBankAccount} variant="outline">
                      <Plus className="h-4 w-4 mr-2" />
                      Tambah Rekening Pertama
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {bankAccounts.map((account) => (
                      <div
                        key={account.id}
                        className="flex items-center justify-between p-4 border rounded-lg hover:border-blue-500 transition-colors"
                      >
                        <div className="flex items-center gap-4">
                          <div className="p-2 bg-blue-100 rounded-lg">
                            <CreditCard className="h-6 w-6 text-blue-600" />
                          </div>
                          <div>
                            <p className="font-semibold text-gray-800">{account.bank_name}</p>
                            <p className="text-sm text-gray-600">{account.account_number}</p>
                            <p className="text-sm text-gray-500">{account.account_name}</p>
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          onClick={() => handleDeleteBankAccount(account.id)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Payment Methods Dialog */}
      <Dialog open={showMethodDialog} onOpenChange={setShowMethodDialog}>
        <DialogContent data-testid="payment-dialog">
          <DialogHeader>
            <DialogTitle>{editMethodId ? 'Edit Metode Pembayaran' : 'Tambah Metode Pembayaran'}</DialogTitle>
            <DialogDescription>Masukkan informasi metode pembayaran</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleMethodSubmit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nama Metode *</Label>
                <Input
                  id="name"
                  value={methodFormData.name}
                  onChange={(e) => setMethodFormData({ ...methodFormData, name: e.target.value })}
                  placeholder="QRIS / Cash / Transfer"
                  required
                  data-testid="payment-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="type">Tipe *</Label>
                <Select value={methodFormData.type} onValueChange={(value) => setMethodFormData({ ...methodFormData, type: value })}>
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
                  value={methodFormData.is_active.toString()}
                  onValueChange={(value) => setMethodFormData({ ...methodFormData, is_active: value === 'true' })}
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
              <Button type="button" variant="outline" onClick={() => setShowMethodDialog(false)} data-testid="cancel-payment-btn">
                Batal
              </Button>
              <Button type="submit" className="bg-blue-600 hover:bg-blue-700" data-testid="save-payment-btn">
                {editMethodId ? 'Update' : 'Simpan'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </Layout>
  );
};

export default PaymentSettingsDetail;
