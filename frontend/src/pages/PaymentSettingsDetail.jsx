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
const API = `${BACKEND_URL}/api`;

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

        <Tabs defaultValue="qris" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="qris" className="flex items-center gap-2">
              <QrCode className="h-4 w-4" />
              QRIS
            </TabsTrigger>
            <TabsTrigger value="bank" className="flex items-center gap-2">
              <CreditCard className="h-4 w-4" />
              Transfer Bank
            </TabsTrigger>
          </TabsList>

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
    </Layout>
  );
};

export default PaymentSettingsDetail;
