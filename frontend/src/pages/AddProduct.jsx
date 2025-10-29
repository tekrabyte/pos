import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ArrowLeft, Plus, Trash2, Loader2 } from 'lucide-react';
import { Checkbox } from '@/components/ui/checkbox';
import { toast } from 'sonner';
import { api } from '@/config/axios';
import { useFetch, useMutation } from '@/hooks/useApi';
import { clearCacheByPattern } from '@/hooks/useApi';

const AddProduct = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    price: '',
    stock: '',
    category_id: null,
    brand_id: null,
    description: '',
    image_url: '',
    status: 'active',
    is_bundle: false,
    bundle_items: [],
  });

  // Fetch categories, brands, and products using custom hook
  const { data: categories = [], loading: loadingCategories } = useFetch('/categories', {
    initialData: [],
    cacheKey: 'categories-list',
  });

  const { data: brands = [], loading: loadingBrands } = useFetch('/brands', {
    initialData: [],
    cacheKey: 'brands-list',
  });

  const { data: allProducts = [], loading: loadingProducts } = useFetch('/products', {
    initialData: [],
    cacheKey: 'products-list',
  });

  // Fetch product for edit mode
  useEffect(() => {
    if (id) {
      fetchProduct();
    }
  }, [id]);

  const fetchProduct = async () => {
    try {
      const response = await api.get(`/products/${id}`);
      setFormData({
        name: response.name,
        sku: response.sku,
        price: response.price,
        stock: response.stock,
        category_id: response.category_id || null,
        brand_id: response.brand_id || null,
        description: response.description || '',
        image_url: response.image_url || '',
        status: response.status,
        is_bundle: response.is_bundle || false,
        bundle_items: response.bundle_items || [],
      });
    } catch (error) {
      console.error('Error fetching product:', error);
      toast.error('Gagal mengambil data produk');
    }
  };

  // Mutation for create/update product
  const { mutate: saveProduct, loading: saving } = useMutation(
    async (payload) => {
      if (id) {
        return await api.put(`/products/${id}`, payload);
      } else {
        return await api.post('/products', payload);
      }
    },
    {
      onSuccess: () => {
        toast.success(id ? 'Produk berhasil diperbarui' : 'Produk berhasil ditambahkan');
        // Clear products cache to force refresh
        clearCacheByPattern('products');
        setTimeout(() => navigate('/products'), 500);
      },
      onError: (error) => {
        console.error('Error saving product:', error);
        toast.error(id ? 'Gagal memperbarui produk' : 'Gagal menambahkan produk');
      },
    }
  );

  const handleSubmit = async (e) => {
    e.preventDefault();

    const payload = {
      ...formData,
      price: parseFloat(formData.price),
      stock: parseFloat(formData.stock),
      category_id: formData.category_id ? parseInt(formData.category_id) : null,
      brand_id: formData.brand_id ? parseInt(formData.brand_id) : null,
    };

    await saveProduct(payload);
  };

  const handleChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
  };

  const addBundleItem = () => {
    setFormData({
      ...formData,
      bundle_items: [...formData.bundle_items, { product_id: '', quantity: 1 }],
    });
  };

  const removeBundleItem = (index) => {
    const newItems = formData.bundle_items.filter((_, i) => i !== index);
    setFormData({ ...formData, bundle_items: newItems });
  };

  const updateBundleItem = (index, field, value) => {
    const newItems = [...formData.bundle_items];
    newItems[index][field] = field === 'quantity' ? parseFloat(value) : value;
    setFormData({ ...formData, bundle_items: newItems });
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6" data-testid="add-product-page">
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            size="icon"
            onClick={() => navigate('/products')}
            data-testid="back-btn"
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <h1 className="text-2xl font-bold text-gray-800">
            {id ? 'Edit Produk' : 'Tambah Produk Baru'}
          </h1>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Informasi Produk</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Nama Produk *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => handleChange('name', e.target.value)}
                    placeholder="Masukkan nama produk"
                    required
                    data-testid="product-name-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="sku">SKU *</Label>
                  <Input
                    id="sku"
                    value={formData.sku}
                    onChange={(e) => handleChange('sku', e.target.value)}
                    placeholder="Masukkan SKU"
                    required
                    data-testid="product-sku-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="price">Harga *</Label>
                  <Input
                    id="price"
                    type="number"
                    step="0.01"
                    value={formData.price}
                    onChange={(e) => handleChange('price', e.target.value)}
                    placeholder="Masukkan harga"
                    required
                    data-testid="product-price-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="stock">Stok (bisa desimal) *</Label>
                  <Input
                    id="stock"
                    type="number"
                    step="0.01"
                    value={formData.stock}
                    onChange={(e) => handleChange('stock', e.target.value)}
                    placeholder="Masukkan jumlah stok"
                    required
                    data-testid="product-stock-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="category">Kategori</Label>
                  <Select
                    value={formData.category_id?.toString() || 'none'}
                    onValueChange={(value) => handleChange('category_id', value === 'none' ? null : value)}
                  >
                    <SelectTrigger data-testid="product-category-select">
                      <SelectValue placeholder="Pilih kategori" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Tidak ada kategori</SelectItem>
                      {Array.isArray(categories) && categories.map((cat) => (
                        <SelectItem key={cat.id} value={cat.id.toString()}>
                          {cat.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="brand">Brand</Label>
                  <Select
                    value={formData.brand_id?.toString() || 'none'}
                    onValueChange={(value) => handleChange('brand_id', value === 'none' ? null : value)}
                  >
                    <SelectTrigger data-testid="product-brand-select">
                      <SelectValue placeholder="Pilih brand" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Tidak ada brand</SelectItem>
                      {Array.isArray(brands) && brands.map((brand) => (
                        <SelectItem key={brand.id} value={brand.id.toString()}>
                          {brand.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="status">Status</Label>
                  <Select value={formData.status} onValueChange={(value) => handleChange('status', value)}>
                    <SelectTrigger data-testid="product-status-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="inactive">Inactive</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="image_url">URL Gambar</Label>
                  <Input
                    id="image_url"
                    value={formData.image_url}
                    onChange={(e) => handleChange('image_url', e.target.value)}
                    placeholder="https://example.com/image.jpg"
                    data-testid="product-image-input"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Deskripsi</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => handleChange('description', e.target.value)}
                  placeholder="Masukkan deskripsi produk"
                  rows={4}
                  data-testid="product-description-input"
                />
              </div>

              {/* Bundle Product Section */}
              <div className="space-y-4 border-t pt-4">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="is_bundle"
                    checked={formData.is_bundle}
                    onCheckedChange={(checked) => handleChange('is_bundle', checked)}
                    data-testid="is-bundle-checkbox"
                  />
                  <Label htmlFor="is_bundle" className="cursor-pointer">
                    Ini adalah Bundle / Paket Produk
                  </Label>
                </div>

                {formData.is_bundle && (
                  <div className="space-y-3 p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <Label className="text-sm font-medium">Item dalam Bundle</Label>
                      <Button type="button" size="sm" onClick={addBundleItem} data-testid="add-bundle-item">
                        <Plus className="h-4 w-4 mr-2" />
                        Tambah Item
                      </Button>
                    </div>

                    {formData.bundle_items.map((item, index) => (
                      <div key={index} className="flex gap-2 items-end">
                        <div className="flex-1">
                          <Label className="text-xs">Produk</Label>
                          <Select
                            value={item.product_id.toString()}
                            onValueChange={(value) => updateBundleItem(index, 'product_id', parseInt(value))}
                          >
                            <SelectTrigger data-testid={`bundle-product-${index}`}>
                              <SelectValue placeholder="Pilih produk" />
                            </SelectTrigger>
                            <SelectContent>
                              {Array.isArray(allProducts) && allProducts
                                .filter((p) => !p.is_bundle)
                                .map((product) => (
                                  <SelectItem key={product.id} value={product.id.toString()}>
                                    {product.name}
                                  </SelectItem>
                                ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="w-32">
                          <Label className="text-xs">Jumlah</Label>
                          <Input
                            type="number"
                            step="0.01"
                            value={item.quantity}
                            onChange={(e) => updateBundleItem(index, 'quantity', e.target.value)}
                            data-testid={`bundle-quantity-${index}`}
                          />
                        </div>
                        <Button
                          type="button"
                          variant="destructive"
                          size="icon"
                          onClick={() => removeBundleItem(index)}
                          data-testid={`remove-bundle-${index}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}

                    {formData.bundle_items.length === 0 && (
                      <p className="text-sm text-gray-500 text-center py-4">Belum ada item. Klik "Tambah Item" untuk menambahkan produk ke bundle.</p>
                    )}
                  </div>
                )}
              </div>

              <div className="flex gap-4 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate('/products')}
                  className="flex-1"
                  data-testid="cancel-btn"
                  disabled={saving}
                >
                  Batal
                </Button>
                <Button
                  type="submit"
                  disabled={saving || loadingCategories || loadingBrands}
                  className="flex-1 bg-blue-600 hover:bg-blue-700"
                  data-testid="save-product-btn"
                >
                  {saving ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Menyimpan...
                    </>
                  ) : (
                    id ? 'Update Produk' : 'Simpan Produk'
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default AddProduct;