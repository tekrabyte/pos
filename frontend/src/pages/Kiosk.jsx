import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import {
  Search,
  ShoppingCart,
  Plus,
  Minus,
  Trash2,
  CreditCard,
  ArrowLeft,
  Check,
  QrCode,
  Sparkles,
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}`;

const Kiosk = () => {
  const [products, setProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [cart, setCart] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCart, setShowCart] = useState(false);
  const [showPayment, setShowPayment] = useState(false);
  const [showQRIS, setShowQRIS] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [qrisData, setQrisData] = useState(null);
  const [orderNumber, setOrderNumber] = useState('');

  useEffect(() => {
    fetchProducts();
    fetchCategories();
  }, []);

  useEffect(() => {
    let filtered = products;

    if (selectedCategory) {
      filtered = filtered.filter((p) => p.category_id === selectedCategory);
    }

    if (searchTerm) {
      filtered = filtered.filter((p) => p.name.toLowerCase().includes(searchTerm.toLowerCase()));
    }

    setFilteredProducts(filtered);
  }, [searchTerm, selectedCategory, products]);

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API}/products`);
      const activeProducts = response.data.filter((p) => p.status === 'active' && p.stock > 0);
      setProducts(activeProducts);
      setFilteredProducts(activeProducts);
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/categories`);
      setCategories(response.data.categories || []);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const addToCart = (product) => {
    const existing = cart.find((item) => item.product_id === product.id);
    if (existing) {
      if (existing.quantity < product.stock) {
        setCart(
          cart.map((item) =>
            item.product_id === product.id ? { ...item, quantity: item.quantity + 1, subtotal: item.price * (item.quantity + 1) } : item
          )
        );
        toast.success(`${product.name} ditambahkan`);
      } else {
        toast.error('Stok tidak mencukupi');
      }
    } else {
      setCart([
        ...cart,
        {
          product_id: product.id,
          product_name: product.name,
          price: product.price,
          quantity: 1,
          subtotal: product.price,
        },
      ]);
      toast.success(`${product.name} ditambahkan`);
    }
  };

  const updateQuantity = (productId, newQuantity) => {
    if (newQuantity <= 0) {
      setCart(cart.filter((item) => item.product_id !== productId));
    } else {
      const product = products.find((p) => p.id === productId);
      if (product && newQuantity <= product.stock) {
        setCart(
          cart.map((item) =>
            item.product_id === productId ? { ...item, quantity: newQuantity, subtotal: item.price * newQuantity } : item
          )
        );
      } else {
        toast.error('Stok tidak mencukupi');
      }
    }
  };

  const removeFromCart = (productId) => {
    setCart(cart.filter((item) => item.product_id !== productId));
  };

  const getTotalAmount = () => {
    return cart.reduce((sum, item) => sum + item.subtotal, 0);
  };

  const getTotalItems = () => {
    return cart.reduce((sum, item) => sum + item.quantity, 0);
  };

  const handleCheckout = () => {
    if (cart.length === 0) {
      toast.error('Keranjang masih kosong');
      return;
    }
    setShowCart(false);
    setShowPayment(true);
  };

  const generateQRIS = async () => {
    try {
      const response = await axios.post(`${API}/qris/generate`, {
        amount: getTotalAmount(),
        product_name: cart.map((item) => item.product_name).join(', '),
      });
      setQrisData(response.data);
      setShowQRIS(true);
    } catch (error) {
      console.error('Error generating QRIS:', error);
      toast.error('Gagal generate QRIS');
    }
  };

  const completeOrder = async () => {
    try {
      const response = await axios.post(`${API}/orders`, {
        customer_id: null,
        outlet_id: 1,
        user_id: 1,
        items: cart,
        payment_method: showQRIS ? 'qris' : 'cash',
        total_amount: getTotalAmount(),
      });

      setOrderNumber(response.data.order_number || `ORD-${Date.now()}`);
      setShowPayment(false);
      setShowQRIS(false);
      setShowSuccess(true);

      // Reset after 5 seconds
      setTimeout(() => {
        setCart([]);
        setShowSuccess(false);
        setSelectedCategory(null);
        setSearchTerm('');
      }, 5000);

      toast.success('Pesanan berhasil!');
    } catch (error) {
      console.error('Error completing order:', error);
      toast.error('Gagal menyelesaikan pesanan');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50" data-testid="kiosk-page">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-lg border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
                <Sparkles className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Self-Service Kiosk
                </h1>
                <p className="text-sm text-gray-600">Pesan dengan mudah dan cepat</p>
              </div>
            </div>
            <button
              onClick={() => setShowCart(true)}
              className="relative p-3 bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-xl hover:shadow-lg transition-all"
              data-testid="cart-button"
            >
              <ShoppingCart className="h-6 w-6" />
              {getTotalItems() > 0 && (
                <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold rounded-full h-6 w-6 flex items-center justify-center animate-bounce">
                  {getTotalItems()}
                </span>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Search & Filter */}
        <div className="mb-8 space-y-4">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <Input
              placeholder="Cari produk..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-12 h-14 text-lg rounded-2xl border-2 border-gray-200 focus:border-blue-500"
              data-testid="search-input"
            />
          </div>

          {/* Category Filter */}
          <div className="flex gap-3 overflow-x-auto pb-2">
            <button
              onClick={() => setSelectedCategory(null)}
              className={`px-6 py-3 rounded-xl font-medium transition-all whitespace-nowrap ${
                selectedCategory === null
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
              data-testid="category-all"
            >
              Semua Produk
            </button>
            {categories.map((category) => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`px-6 py-3 rounded-xl font-medium transition-all whitespace-nowrap ${
                  selectedCategory === category.id
                    ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
                data-testid={`category-${category.id}`}
              >
                {category.name}
              </button>
            ))}
          </div>
        </div>

        {/* Products Grid */}
        {filteredProducts.length === 0 ? (
          <div className="text-center py-20">
            <div className="inline-block p-6 bg-white rounded-2xl shadow-lg">
              <ShoppingCart className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <p className="text-xl text-gray-500">Tidak ada produk tersedia</p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {filteredProducts.map((product) => (
              <Card
                key={product.id}
                className="group hover:shadow-2xl transition-all duration-300 cursor-pointer border-2 border-transparent hover:border-blue-500 rounded-2xl overflow-hidden"
                onClick={() => addToCart(product)}
                data-testid={`product-${product.id}`}
              >
                <CardContent className="p-0">
                  <div className="aspect-square bg-gradient-to-br from-gray-100 to-gray-200 relative overflow-hidden">
                    {product.image_url ? (
                      <img src={product.image_url} alt={product.name} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <ShoppingCart className="h-20 w-20 text-gray-300" />
                      </div>
                    )}
                    {product.stock < 10 && (
                      <Badge className="absolute top-2 right-2 bg-orange-500">Stok Terbatas</Badge>
                    )}
                  </div>
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-800 mb-1 line-clamp-2 group-hover:text-blue-600 transition-colors">
                      {product.name}
                    </h3>
                    <p className="text-xs text-gray-500 mb-2">Stok: {product.stock}</p>
                    <div className="flex items-center justify-between">
                      <p className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                        Rp {parseFloat(product.price).toLocaleString('id-ID')}
                      </p>
                      <button className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-lg group-hover:shadow-lg transition-all">
                        <Plus className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Cart Dialog */}
      <Dialog open={showCart} onOpenChange={setShowCart}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden" data-testid="cart-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl">Keranjang Belanja</DialogTitle>
            <DialogDescription>{getTotalItems()} item dalam keranjang</DialogDescription>
          </DialogHeader>
          <div className="flex-1 overflow-auto py-4">
            {cart.length === 0 ? (
              <div className="text-center py-12">
                <ShoppingCart className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">Keranjang kosong</p>
              </div>
            ) : (
              <div className="space-y-3">
                {cart.map((item) => (
                  <div key={item.product_id} className="flex items-center gap-4 p-4 bg-gray-50 rounded-xl" data-testid={`cart-item-${item.product_id}`}>
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-800">{item.product_name}</h4>
                      <p className="text-sm text-gray-600">Rp {parseFloat(item.price).toLocaleString('id-ID')}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                        className="p-2 bg-white rounded-lg hover:bg-gray-100 border"
                        data-testid={`decrease-${item.product_id}`}
                      >
                        <Minus className="h-4 w-4" />
                      </button>
                      <span className="font-semibold w-8 text-center">{item.quantity}</span>
                      <button
                        onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                        className="p-2 bg-white rounded-lg hover:bg-gray-100 border"
                        data-testid={`increase-${item.product_id}`}
                      >
                        <Plus className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => removeFromCart(item.product_id)}
                        className="p-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100"
                        data-testid={`remove-${item.product_id}`}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                    <p className="font-bold text-blue-600 w-32 text-right">Rp {item.subtotal.toLocaleString('id-ID')}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="border-t pt-4 space-y-4">
            <div className="flex items-center justify-between text-xl font-bold">
              <span>Total:</span>
              <span className="text-blue-600" data-testid="cart-total">
                Rp {getTotalAmount().toLocaleString('id-ID')}
              </span>
            </div>
            <Button onClick={handleCheckout} className="w-full h-14 text-lg bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700" data-testid="checkout-button">
              <CreditCard className="h-5 w-5 mr-2" />
              Lanjut ke Pembayaran
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Payment Dialog */}
      <Dialog open={showPayment} onOpenChange={setShowPayment}>
        <DialogContent className="max-w-md" data-testid="payment-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl">Pilih Metode Pembayaran</DialogTitle>
            <DialogDescription>Total: Rp {getTotalAmount().toLocaleString('id-ID')}</DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-4">
            <button
              onClick={completeOrder}
              className="w-full p-6 border-2 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition-all"
              data-testid="payment-cash"
            >
              <CreditCard className="h-8 w-8 mx-auto mb-2 text-blue-600" />
              <p className="font-semibold text-lg">Cash</p>
              <p className="text-sm text-gray-600">Bayar di kasir</p>
            </button>
            <button
              onClick={generateQRIS}
              className="w-full p-6 border-2 rounded-xl hover:border-purple-500 hover:bg-purple-50 transition-all"
              data-testid="payment-qris"
            >
              <QrCode className="h-8 w-8 mx-auto mb-2 text-purple-600" />
              <p className="font-semibold text-lg">QRIS</p>
              <p className="text-sm text-gray-600">Scan untuk bayar</p>
            </button>
          </div>
        </DialogContent>
      </Dialog>

      {/* QRIS Dialog */}
      <Dialog open={showQRIS} onOpenChange={setShowQRIS}>
        <DialogContent className="max-w-md" data-testid="qris-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl">Scan QRIS</DialogTitle>
            <DialogDescription>Scan dengan aplikasi mobile banking Anda</DialogDescription>
          </DialogHeader>
          <div className="py-6">
            <div className="bg-white p-8 rounded-2xl border-4 border-dashed border-purple-300">
              <div className="aspect-square bg-gradient-to-br from-purple-100 to-blue-100 rounded-xl flex items-center justify-center">
                <QrCode className="h-32 w-32 text-purple-600" />
              </div>
              <p className="text-center mt-4 text-sm text-gray-600 font-mono">{qrisData?.qris_string}</p>
            </div>
            <div className="text-center mt-6">
              <p className="text-2xl font-bold text-purple-600 mb-2">Rp {getTotalAmount().toLocaleString('id-ID')}</p>
              <p className="text-sm text-gray-600">Mock QRIS - Demo Mode</p>
            </div>
            <Button onClick={completeOrder} className="w-full mt-6 h-12 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700" data-testid="confirm-payment">
              <Check className="h-5 w-5 mr-2" />
              Konfirmasi Pembayaran
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Success Dialog */}
      <Dialog open={showSuccess} onOpenChange={setShowSuccess}>
        <DialogContent className="max-w-md" data-testid="success-dialog">
          <div className="text-center py-8">
            <div className="inline-block p-4 bg-green-100 rounded-full mb-6">
              <Check className="h-16 w-16 text-green-600" />
            </div>
            <h2 className="text-3xl font-bold text-gray-800 mb-2">Pesanan Berhasil!</h2>
            <p className="text-gray-600 mb-6">Nomor pesanan Anda:</p>
            <div className="inline-block px-6 py-3 bg-blue-50 rounded-xl">
              <p className="text-2xl font-bold text-blue-600">{orderNumber}</p>
            </div>
            <p className="text-sm text-gray-500 mt-6">Terima kasih telah berbelanja</p>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Kiosk;
