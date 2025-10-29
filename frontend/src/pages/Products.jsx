import { useState, useMemo } from 'react';
import Layout from '@/components/Layout';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Search, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useFetch, useDebounce } from '@/hooks/useApi';

const Products = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 300);

  const { data: products = [], loading, refetch } = useFetch('/products', {
    initialData: [],
    cacheKey: 'products-list',
  });

  const formatCurrency = (value) => {
    if (value === null || value === undefined || isNaN(value)) {
      return '0';
    }
    return parseFloat(value).toLocaleString('id-ID');
  };

  const filteredProducts = useMemo(() => {
    if (!debouncedSearch) return products;
    const search = debouncedSearch.toLowerCase();
    return products.filter(
      (p) =>
        p.name?.toLowerCase().includes(search) ||
        p.sku?.toLowerCase().includes(search)
    );
  }, [debouncedSearch, products]);

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
              onClick={() => refetch()}
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Cari produk berdasarkan nama atau SKU..."
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
              <p className="text-gray-500">Tidak ada produk ditemukan</p>
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
                    <h3 className="font-semibold text-gray-800 truncate">{product.name}</h3>
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