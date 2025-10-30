import React, { useState, useEffect } from 'react';
import { Settings, Image, Palette, Upload, Trash2, Eye, EyeOff, Plus, ChevronUp, ChevronDown, Save, RotateCcw } from 'lucide-react';
import Layout from '@/components/Layout';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import axios from 'axios';
import { useTheme } from '@/contexts/ThemeContext';
import { HexColorPicker } from 'react-colorful';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const StoreSettings = () => {
  const { themeSettings, updateTheme, updateColors, resetTheme } = useTheme();
  
  // Basic Settings State
  const [storeName, setStoreName] = useState('');
  const [storeDescription, setStoreDescription] = useState('');
  const [logoUrl, setLogoUrl] = useState('');
  const [logoFile, setLogoFile] = useState(null);
  const [isLoadingBasic, setIsLoadingBasic] = useState(false);

  // Theme Settings State
  const [tempColors, setTempColors] = useState(themeSettings.colors);
  const [themeMode, setThemeMode] = useState(themeSettings.mode);

  // Banner Settings State
  const [banners, setBanners] = useState([]);
  const [isLoadingBanners, setIsLoadingBanners] = useState(false);
  const [showBannerDialog, setShowBannerDialog] = useState(false);
  const [editingBanner, setEditingBanner] = useState(null);
  const [bannerForm, setBannerForm] = useState({
    title: '',
    subtitle: '',
    image_url: '',
    link_url: '',
    button_text: '',
    display_order: 0,
    is_active: true,
  });
  const [bannerFile, setBannerFile] = useState(null);

  useEffect(() => {
    fetchStoreSettings();
    fetchBanners();
  }, []);

  useEffect(() => {
    setTempColors(themeSettings.colors);
    setThemeMode(themeSettings.mode);
  }, [themeSettings]);

  const fetchStoreSettings = async () => {
    try {
      const response = await axios.get(`${API_URL}/store-settings`);
      const data = response.data;
      setStoreName(data.store_name || '');
      setStoreDescription(data.store_description || '');
      setLogoUrl(data.logo_url || '');
    } catch (error) {
      console.error('Error fetching store settings:', error);
    }
  };

  const fetchBanners = async () => {
    try {
      setIsLoadingBanners(true);
      const response = await axios.get(`${API_URL}/store-banners`);
      setBanners(response.data.banners || []);
    } catch (error) {
      console.error('Error fetching banners:', error);
      toast.error('Gagal memuat banner');
    } finally {
      setIsLoadingBanners(false);
    }
  };

  const handleLogoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setLogoFile(file);
    // Preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setLogoUrl(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleSaveBasicSettings = async () => {
    try {
      setIsLoadingBasic(true);
      
      let uploadedLogoUrl = logoUrl;
      
      // Upload logo if new file selected
      if (logoFile) {
        const formData = new FormData();
        formData.append('file', logoFile);
        const uploadResponse = await axios.post(`${API_URL}/upload/image?type=logos`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        uploadedLogoUrl = uploadResponse.data.url;
      }

      // Save store settings
      await axios.post(`${API_URL}/store-settings`, {
        store_name: storeName,
        store_description: storeDescription,
        logo_url: uploadedLogoUrl,
      });

      toast.success('Pengaturan dasar berhasil disimpan');
      setLogoFile(null);
    } catch (error) {
      console.error('Error saving basic settings:', error);
      toast.error('Gagal menyimpan pengaturan dasar');
    } finally {
      setIsLoadingBasic(false);
    }
  };

  const handleSaveThemeSettings = () => {
    updateTheme({ mode: themeMode });
    updateColors(tempColors);
    toast.success('Tema berhasil disimpan');
  };

  const handleColorChange = (colorKey, property, value) => {
    setTempColors((prev) => ({
      ...prev,
      [colorKey]: {
        ...prev[colorKey],
        [property]: parseInt(value),
      },
    }));
  };

  const hslToHex = (h, s, l) => {
    l /= 100;
    const a = s * Math.min(l, 1 - l) / 100;
    const f = n => {
      const k = (n + h / 30) % 12;
      const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
      return Math.round(255 * color).toString(16).padStart(2, '0');
    };
    return `#${f(0)}${f(8)}${f(4)}`;
  };

  const handleResetTheme = () => {
    resetTheme();
    toast.success('Tema dikembalikan ke default');
  };

  const handleBannerFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setBannerFile(file);
    // Preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setBannerForm({ ...bannerForm, image_url: reader.result });
    };
    reader.readAsDataURL(file);
  };

  const handleCreateBanner = () => {
    const maxOrder = banners.length > 0 ? Math.max(...banners.map(b => b.display_order)) : -1;
    setBannerForm({
      title: '',
      subtitle: '',
      image_url: '',
      link_url: '',
      button_text: '',
      display_order: maxOrder + 1,
      is_active: true,
    });
    setEditingBanner(null);
    setBannerFile(null);
    setShowBannerDialog(true);
  };

  const handleEditBanner = (banner) => {
    setBannerForm({
      title: banner.title || '',
      subtitle: banner.subtitle || '',
      image_url: banner.image_url || '',
      link_url: banner.link_url || '',
      button_text: banner.button_text || '',
      display_order: banner.display_order,
      is_active: banner.is_active,
    });
    setEditingBanner(banner);
    setBannerFile(null);
    setShowBannerDialog(true);
  };

  const handleSaveBanner = async () => {
    try {
      let uploadedImageUrl = bannerForm.image_url;

      // Upload banner image if new file selected
      if (bannerFile) {
        const formData = new FormData();
        formData.append('file', bannerFile);
        const uploadResponse = await axios.post(`${API_URL}/upload/image?type=banners`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        uploadedImageUrl = uploadResponse.data.url;
      }

      const bannerData = {
        ...bannerForm,
        image_url: uploadedImageUrl,
      };

      if (editingBanner) {
        // Update existing banner
        await axios.put(`${API_URL}/store-banners/${editingBanner.id}`, bannerData);
        toast.success('Banner berhasil diupdate');
      } else {
        // Create new banner
        await axios.post(`${API_URL}/store-banners`, bannerData);
        toast.success('Banner berhasil dibuat');
      }

      setShowBannerDialog(false);
      setBannerFile(null);
      fetchBanners();
    } catch (error) {
      console.error('Error saving banner:', error);
      toast.error('Gagal menyimpan banner');
    }
  };

  const handleDeleteBanner = async (bannerId) => {
    if (!window.confirm('Apakah Anda yakin ingin menghapus banner ini?')) return;

    try {
      await axios.delete(`${API_URL}/store-banners/${bannerId}`);
      toast.success('Banner berhasil dihapus');
      fetchBanners();
    } catch (error) {
      console.error('Error deleting banner:', error);
      toast.error('Gagal menghapus banner');
    }
  };

  const handleToggleBannerActive = async (banner) => {
    try {
      await axios.put(`${API_URL}/store-banners/${banner.id}`, {
        ...banner,
        is_active: !banner.is_active,
      });
      toast.success(`Banner ${!banner.is_active ? 'diaktifkan' : 'dinonaktifkan'}`);
      fetchBanners();
    } catch (error) {
      console.error('Error toggling banner:', error);
      toast.error('Gagal mengubah status banner');
    }
  };

  const handleMoveBanner = async (banner, direction) => {
    const currentIndex = banners.findIndex(b => b.id === banner.id);
    if (
      (direction === 'up' && currentIndex === 0) ||
      (direction === 'down' && currentIndex === banners.length - 1)
    ) {
      return;
    }

    const newIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
    const swapBanner = banners[newIndex];

    try {
      // Swap display orders
      await axios.put(`${API_URL}/store-banners/${banner.id}`, {
        ...banner,
        display_order: swapBanner.display_order,
      });
      await axios.put(`${API_URL}/store-banners/${swapBanner.id}`, {
        ...swapBanner,
        display_order: banner.display_order,
      });
      toast.success('Urutan banner berhasil diubah');
      fetchBanners();
    } catch (error) {
      console.error('Error moving banner:', error);
      toast.error('Gagal mengubah urutan banner');
    }
  };

  return (
    <Layout>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 dark:text-white">Pengaturan Toko</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">Kelola pengaturan toko, tema, dan banner</p>
          </div>
        </div>

        <Tabs defaultValue="basic" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-6">
            <TabsTrigger value="basic" className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              Pengaturan Dasar
            </TabsTrigger>
            <TabsTrigger value="theme" className="flex items-center gap-2">
              <Palette className="w-4 h-4" />
              Tema & Warna
            </TabsTrigger>
            <TabsTrigger value="banners" className="flex items-center gap-2">
              <Image className="w-4 h-4" />
              Banner
            </TabsTrigger>
          </TabsList>

          {/* Basic Settings Tab */}
          <TabsContent value="basic">
            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-4">Informasi Toko</h2>
              
              <div className="space-y-4">
                <div>
                  <Label htmlFor="storeName">Nama Toko</Label>
                  <Input
                    id="storeName"
                    value={storeName}
                    onChange={(e) => setStoreName(e.target.value)}
                    placeholder="Masukkan nama toko"
                  />
                </div>

                <div>
                  <Label htmlFor="storeDescription">Deskripsi Toko</Label>
                  <Textarea
                    id="storeDescription"
                    value={storeDescription}
                    onChange={(e) => setStoreDescription(e.target.value)}
                    placeholder="Masukkan deskripsi toko"
                    rows={4}
                  />
                </div>

                <div>
                  <Label>Logo Toko</Label>
                  <div className="mt-2 flex items-center gap-4">
                    {logoUrl && (
                      <div className="w-24 h-24 border rounded-lg overflow-hidden">
                        <img src={logoUrl} alt="Logo" className="w-full h-full object-cover" />
                      </div>
                    )}
                    <div>
                      <input
                        type="file"
                        id="logoUpload"
                        accept="image/*"
                        onChange={handleLogoUpload}
                        className="hidden"
                      />
                      <Button
                        onClick={() => document.getElementById('logoUpload').click()}
                        variant="outline"
                      >
                        <Upload className="w-4 h-4 mr-2" />
                        Upload Logo
                      </Button>
                    </div>
                  </div>
                </div>

                <Button
                  onClick={handleSaveBasicSettings}
                  disabled={isLoadingBasic}
                  className="w-full"
                >
                  <Save className="w-4 h-4 mr-2" />
                  {isLoadingBasic ? 'Menyimpan...' : 'Simpan Pengaturan Dasar'}
                </Button>
              </div>
            </Card>
          </TabsContent>

          {/* Theme Settings Tab */}
          <TabsContent value="theme">
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Tema & Warna</h2>
                <Button onClick={handleResetTheme} variant="outline" size="sm">
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Reset ke Default
                </Button>
              </div>

              <div className="space-y-6">
                {/* Theme Mode */}
                <div>
                  <Label>Mode Tema</Label>
                  <div className="grid grid-cols-3 gap-2 mt-2">
                    {['light', 'dark', 'system'].map((mode) => (
                      <Button
                        key={mode}
                        variant={themeMode === mode ? 'default' : 'outline'}
                        onClick={() => setThemeMode(mode)}
                        className="capitalize"
                      >
                        {mode === 'light' ? 'Terang' : mode === 'dark' ? 'Gelap' : 'Sistem'}
                      </Button>
                    ))}
                  </div>
                </div>

                {/* Color Pickers */}
                {Object.entries(tempColors).map(([colorKey, hsl]) => (
                  <div key={colorKey} className="space-y-2">
                    <Label className="capitalize">{colorKey.replace('_', ' ')}</Label>
                    <div className="flex items-center gap-4">
                      <div
                        className="w-16 h-16 rounded-lg border-2"
                        style={{ backgroundColor: hslToHex(hsl.h, hsl.s, hsl.l) }}
                      />
                      <div className="flex-1 space-y-2">
                        <div className="grid grid-cols-3 gap-2">
                          <div>
                            <Label className="text-xs">Hue (H)</Label>
                            <Input
                              type="number"
                              min="0"
                              max="360"
                              value={hsl.h}
                              onChange={(e) => handleColorChange(colorKey, 'h', e.target.value)}
                            />
                          </div>
                          <div>
                            <Label className="text-xs">Saturation (S%)</Label>
                            <Input
                              type="number"
                              min="0"
                              max="100"
                              value={hsl.s}
                              onChange={(e) => handleColorChange(colorKey, 's', e.target.value)}
                            />
                          </div>
                          <div>
                            <Label className="text-xs">Lightness (L%)</Label>
                            <Input
                              type="number"
                              min="0"
                              max="100"
                              value={hsl.l}
                              onChange={(e) => handleColorChange(colorKey, 'l', e.target.value)}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                <Button onClick={handleSaveThemeSettings} className="w-full">
                  <Save className="w-4 h-4 mr-2" />
                  Terapkan Tema
                </Button>
              </div>
            </Card>
          </TabsContent>

          {/* Banners Tab */}
          <TabsContent value="banners">
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Banner Management</h2>
                <Button onClick={handleCreateBanner}>
                  <Plus className="w-4 h-4 mr-2" />
                  Tambah Banner
                </Button>
              </div>

              {isLoadingBanners ? (
                <div className="text-center py-8">Memuat banner...</div>
              ) : banners.length === 0 ? (
                <div className="text-center py-8 text-gray-500">Belum ada banner</div>
              ) : (
                <div className="space-y-4">
                  {banners.map((banner, index) => (
                    <Card key={banner.id} className="p-4">
                      <div className="flex items-start gap-4">
                        <div className="w-32 h-20 rounded-lg overflow-hidden bg-gray-100 flex-shrink-0">
                          {banner.image_url ? (
                            <img
                              src={banner.image_url}
                              alt={banner.title}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-gray-400">
                              <Image className="w-8 h-8" />
                            </div>
                          )}
                        </div>

                        <div className="flex-1">
                          <div className="flex items-start justify-between">
                            <div>
                              <h3 className="font-semibold">{banner.title || 'Tanpa Judul'}</h3>
                              <p className="text-sm text-gray-600">{banner.subtitle || ''}</p>
                              <div className="flex items-center gap-2 mt-2">
                                <Badge variant={banner.is_active ? 'default' : 'secondary'}>
                                  {banner.is_active ? 'Aktif' : 'Nonaktif'}
                                </Badge>
                                <span className="text-xs text-gray-500">Order: {banner.display_order}</span>
                              </div>
                            </div>
                            <div className="flex items-center gap-1">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleMoveBanner(banner, 'up')}
                                disabled={index === 0}
                              >
                                <ChevronUp className="w-4 h-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleMoveBanner(banner, 'down')}
                                disabled={index === banners.length - 1}
                              >
                                <ChevronDown className="w-4 h-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleToggleBannerActive(banner)}
                              >
                                {banner.is_active ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleEditBanner(banner)}
                              >
                                Edit
                              </Button>
                              <Button
                                size="sm"
                                variant="destructive"
                                onClick={() => handleDeleteBanner(banner.id)}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </Card>
          </TabsContent>
        </Tabs>

        {/* Banner Dialog */}
        <Dialog open={showBannerDialog} onOpenChange={setShowBannerDialog}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{editingBanner ? 'Edit Banner' : 'Tambah Banner Baru'}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Gambar Banner</Label>
                <div className="mt-2">
                  {bannerForm.image_url && (
                    <div className="w-full h-48 rounded-lg overflow-hidden mb-2">
                      <img
                        src={bannerForm.image_url}
                        alt="Banner preview"
                        className="w-full h-full object-cover"
                      />
                    </div>
                  )}
                  <input
                    type="file"
                    id="bannerUpload"
                    accept="image/*"
                    onChange={handleBannerFileUpload}
                    className="hidden"
                  />
                  <Button
                    onClick={() => document.getElementById('bannerUpload').click()}
                    variant="outline"
                    className="w-full"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    Upload Gambar
                  </Button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="bannerTitle">Judul</Label>
                  <Input
                    id="bannerTitle"
                    value={bannerForm.title}
                    onChange={(e) => setBannerForm({ ...bannerForm, title: e.target.value })}
                    placeholder="Judul banner"
                  />
                </div>
                <div>
                  <Label htmlFor="bannerSubtitle">Subjudul</Label>
                  <Input
                    id="bannerSubtitle"
                    value={bannerForm.subtitle}
                    onChange={(e) => setBannerForm({ ...bannerForm, subtitle: e.target.value })}
                    placeholder="Subjudul banner"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="bannerLink">Link URL (opsional)</Label>
                  <Input
                    id="bannerLink"
                    value={bannerForm.link_url}
                    onChange={(e) => setBannerForm({ ...bannerForm, link_url: e.target.value })}
                    placeholder="https://..."
                  />
                </div>
                <div>
                  <Label htmlFor="bannerButton">Teks Tombol (opsional)</Label>
                  <Input
                    id="bannerButton"
                    value={bannerForm.button_text}
                    onChange={(e) => setBannerForm({ ...bannerForm, button_text: e.target.value })}
                    placeholder="Lihat Detail"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="bannerActive"
                  checked={bannerForm.is_active}
                  onChange={(e) => setBannerForm({ ...bannerForm, is_active: e.target.checked })}
                  className="w-4 h-4"
                />
                <Label htmlFor="bannerActive" className="cursor-pointer">Banner Aktif</Label>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowBannerDialog(false)}>
                Batal
              </Button>
              <Button onClick={handleSaveBanner}>
                <Save className="w-4 h-4 mr-2" />
                Simpan Banner
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
};

export default StoreSettings;
