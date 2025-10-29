import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Plus, Search, Edit, Trash2 } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Products = () => {
  const [products, setProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [deleteId, setDeleteId] = useState(null);
  const navigate = useNavigate();

  const formatCurrency = (value) => {
    if (value === null || value === undefined || isNaN(value)) {
      return '0';
    }
    return parseFloat(value).toLocaleString('id-ID');
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  useEffect(() => {
    if (searchTerm) {
      setFilteredProducts(
        products.filter(
          (p) =>
            p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            p.sku.toLowerCase().includes(searchTerm.toLowerCase())
        )
      );
    } else {
      setFilteredProducts(products);
    }
  }, [searchTerm, products]);

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API}/products`);
      setProducts(response.data);
      setFilteredProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
      toast.error('Gagal mengambil data produk');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    try {
      await axios.delete(`${API}/products/${deleteId}`);
      toast.success('Produk berhasil dihapus');
      fetchProducts();
      setDeleteId(null);
    } catch (error) {
      console.error('Error deleting product:', error);
      toast.error('Gagal menghapus produk');
    }
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
      <div className="space-y-6" data-testid="products-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">Semua Produk</h1>
          <Button
            onClick={() => navigate('/products/add')}
            className="bg-blue-600 hover:bg-blue-700"
            data-testid="add-product-btn"
          >
            <Plus className="h-4 w-4 mr-2" />
            Tambah Produk
          </Button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Cari produk berdasarkan nama atau SKU..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
            data-testid="search-product-input"
          />
        </div>

        {/* Products Grid */}
        {filteredProducts.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <p className="text-gray-500 mb-4">Belum ada produk</p>
              <Button
                onClick={() => navigate('/products/add')}
                variant="outline"
                data-testid="empty-add-product-btn"
              >
                <Plus className="h-4 w-4 mr-2" />
                Tambah Produk Pertama
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredProducts.map((product) => (
              <Card
                key={product.id}
                className="hover:shadow-lg transition-shadow"
                data-testid={`product-card-${product.id}`}
              >
                <CardContent className="p-4">
                  <div className="aspect-square bg-gray-100 rounded-lg mb-4 flex items-center justify-center overflow-hidden">
                    {product.image_url ? (
                      <img
                        src={product.image_url}
                        alt={product.name}
                        className="w-full h-full object-cover"
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
                    <div className="flex gap-2 pt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => navigate(`/products/edit/${product.id}`)}
                        data-testid={`edit-product-${product.id}`}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        onClick={() => setDeleteId(product.id)}
                        data-testid={`delete-product-${product.id}`}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteId !== null} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Hapus Produk?</AlertDialogTitle>
            <AlertDialogDescription>
              Tindakan ini tidak dapat dibatalkan. Produk akan dihapus secara permanen.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="cancel-delete-btn">Batal</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
              data-testid="confirm-delete-btn"
            >
              Hapus
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Layout>
  );
};

export default Products;