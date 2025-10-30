import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '@/components/Layout';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Search, RefreshCw, Plus, Edit, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import axiosInstance from '@/config/axios';
import { toast } from 'sonner';

const Products = () => {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const response = await axiosInstance.get('/products');
      const productsData = response.data.products || response.data || [];
      setProducts(Array.isArray(productsData) ? productsData : []);
    } catch (error) {
      console.error('Error fetching products:', error);
      toast.error('Gagal mengambil data produk');
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id, productName) => {
    if (window.confirm(`Apakah Anda yakin ingin menghapus produk "${productName}"?`)) {
      try {
        await axiosInstance.delete(`/products/${id}`);
        toast.success('Produk berhasil dihapus');
        fetchProducts();
      } catch (error) {
        console.error('Error deleting product:', error);
        toast.error('Gagal menghapus produk');
      }
    }
  };

  const formatCurrency = (value) => {
    if (value === null || value === undefined || isNaN(value)) {
      return '0';
    }
    return parseFloat(value).toLocaleString('id-ID');
  };

  const filteredProducts = useMemo(() => {
    if (!searchTerm) return products;
    const search = searchTerm.toLowerCase();
    return products.filter(
      (p) =>
        p.name?.toLowerCase().includes(search) ||
        p.sku?.toLowerCase().includes(search) ||
        p.category_name?.toLowerCase().includes(search) ||
        p.brand_name?.toLowerCase().includes(search)
    );
  }, [searchTerm, products]);

  if (loading) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center h-64 space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <div className="text-gray-500">Memuat data produk...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">Semua Produk</h1>
          <div className="flex items-center gap-3">
            <div className="text-sm text-gray-500">
              Total: {filteredProducts.length} produk
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchProducts}
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button
              onClick={() => navigate('/products/add')}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="h-4 w-4 mr-2" />
              Tambah Produk
            </Button>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Cari produk berdasarkan nama, SKU, kategori, atau brand..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
          {searchTerm && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs text-gray-400">
              {filteredProducts.length} hasil
            </div>
          )}
        </div>

        {/* Products Grid */}
        {filteredProducts.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <p className="text-gray-500 mb-4">Tidak ada produk ditemukan</p>
              {products.length === 0 && (
                <Button
                  onClick={() => navigate('/products/add')}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Tambah Produk Pertama
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredProducts.map((product) => (
              <Card
                key={product.id}
                className="hover:shadow-lg transition-shadow"
              >
                <CardContent className="p-4">
                  <div className="aspect-square bg-gray-100 rounded-lg mb-3 flex items-center justify-center overflow-hidden">
                    {product.image_url ? (
                      <img
                        src={product.image_url}
                        alt={product.name}
                        className="w-full h-full object-cover"
                        loading="lazy"
                      />
                    ) : (
                      <div className="text-gray-400 text-4xl">📦</div>
                    )}
                  </div>
                  <div className="space-y-2">
                    <h3 className="font-semibold text-gray-800 truncate" title={product.name}>
                      {product.name}
                    </h3>
                    <p className="text-xs text-gray-500">SKU: {product.sku}</p>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-lg font-bold text-blue-600">
                          Rp {formatCurrency(product.price)}
                        </p>
                        <p className="text-xs text-gray-500">Stok: {product.stock}</p>
                      </div>
                      <span
                        className={`text-xs px-2 py-1 rounded-full ${
                          product.status === 'active'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {product.status}
                      </span>
                    </div>
                    {product.category_name && (
                      <p className="text-xs text-gray-600">Kategori: {product.category_name}</p>
                    )}
                    {product.brand_name && (
                      <p className="text-xs text-gray-600">Brand: {product.brand_name}</p>
                    )}
                    {product.is_bundle && (
                      <span className="inline-block text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded-full">
                        Bundle/Paket
                      </span>
                    )}
                  </div>
                  
                  {/* Action Buttons */}
                  <div className="flex gap-2 mt-4 pt-3 border-t">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => navigate(`/products/edit/${product.id}`)}
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      onClick={() => handleDelete(product.id, product.name)}
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
    </Layout>
  );
};

export default Products;