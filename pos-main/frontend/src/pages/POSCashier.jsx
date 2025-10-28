import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  LayoutDashboard,
  Package,
  ShoppingCart,
  Users,
  BarChart,
  Search,
  Plus,
  Minus,
  Trash2,
  CreditCard,
  User,
  Cloud,
  CloudOff,
  RefreshCw,
  LogOut,
  Home,
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const POSCashier = () => {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [showQRIS, setShowQRIS] = useState(false);
  const [qrisData, setQrisData] = useState(null);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [isSyncing, setIsSyncing] = useState(false);
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  useEffect(() => {
    fetchProducts();
    fetchCustomers();
    fetchPaymentMethods();

    // Load cart from localStorage
    const savedCart = localStorage.getItem('pos_cart');
    if (savedCart) {
      setCart(JSON.parse(savedCart));
    }

    // Online/offline detection
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  useEffect(() => {
    // Save cart to localStorage
    localStorage.setItem('pos_cart', JSON.stringify(cart));
  }, [cart]);

  useEffect(() => {
    if (searchTerm) {
      setFilteredProducts(
        products.filter((p) => p.name.toLowerCase().includes(searchTerm.toLowerCase()) || p.sku.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    } else {
      setFilteredProducts(products);
    }
  }, [searchTerm, products]);

  const handleOnline = () => {
    setIsOnline(true);
    toast.success('Koneksi online kembali');
    syncPendingOrders();
  };

  const handleOffline = () => {
    setIsOnline(false);
    toast.warning('Mode offline - Transaksi akan disinkronkan nanti');
  };

  const syncPendingOrders = async () => {
    setIsSyncing(true);
    const pendingOrders = JSON.parse(localStorage.getItem('pending_orders') || '[]');

    if (pendingOrders.length > 0) {
      for (const order of pendingOrders) {
        try {
          await axios.post(`${API}/orders`, order);
        } catch (error) {
          console.error('Error syncing order:', error);
        }
      }
      localStorage.removeItem('pending_orders');
      toast.success(`${pendingOrders.length} transaksi berhasil disinkronkan`);
    }
    setIsSyncing(false);
  };

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API}/products`);
      setProducts(response.data.filter((p) => p.status === 'active' && p.stock > 0));
      setFilteredProducts(response.data.filter((p) => p.status === 'active' && p.stock > 0));
    } catch (error) {
      console.error('Error fetching products:', error);
      // Load from localStorage if offline
      const cachedProducts = localStorage.getItem('cached_products');
      if (cachedProducts) {
        const parsed = JSON.parse(cachedProducts);
        setProducts(parsed);
        setFilteredProducts(parsed);
      }
    }
  };

  const fetchCustomers = async () => {
    try {
      const response = await axios.get(`${API}/customers`);
      setCustomers(response.data);
    } catch (error) {
      console.error('Error fetching customers:', error);
    }
  };

  const fetchPaymentMethods = async () => {
    try {
      const response = await axios.get(`${API}/payment-methods`);
      setPaymentMethods(response.data);
    } catch (error) {
      console.error('Error fetching payment methods:', error);
    }
  };

  const addToCart = (product) => {
    const existing = cart.find((item) => item.product_id === product.id);
    if (existing) {
      if (existing.quantity < product.stock) {
        setCart(cart.map((item) => (item.product_id === product.id ? { ...item, quantity: item.quantity + 1 } : item)));
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
    }
  };

  const updateQuantity = (productId, quantity) => {
    if (quantity <= 0) {
      setCart(cart.filter((item) => item.product_id !== productId));
    } else {
      const product = products.find((p) => p.id === productId);
      if (product && quantity <= product.stock) {
        setCart(
          cart.map((item) =>
            item.product_id === productId
              ? { ...item, quantity, subtotal: item.price * quantity }
              : item
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

  const handlePayment = () => {
    if (cart.length === 0) {
      toast.error('Keranjang masih kosong');
      return;
    }
    setShowPaymentDialog(true);
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

  const completeTransaction = async () => {
    try {
      const orderData = {
        customer_id: selectedCustomer,
        outlet_id: user.outlet_id || 1,
        user_id: user.id,
        items: cart,
        payment_method: paymentMethod,
        total_amount: getTotalAmount(),
      };

      if (isOnline) {
        await axios.post(`${API}/orders`, orderData);
        toast.success('Transaksi berhasil!');
      } else {
        // Save to pending orders
        const pendingOrders = JSON.parse(localStorage.getItem('pending_orders') || '[]');
        pendingOrders.push(orderData);
        localStorage.setItem('pending_orders', JSON.stringify(pendingOrders));
        toast.success('Transaksi disimpan (akan disinkronkan saat online)');
      }

      // Reset cart
      setCart([]);
      setSelectedCustomer(null);
      setPaymentMethod('cash');
      setShowPaymentDialog(false);
      setShowQRIS(false);
      fetchProducts();
    } catch (error) {
      console.error('Error completing transaction:', error);
      toast.error('Gagal menyelesaikan transaksi');
    }
  };

  return (
    <div className="flex h-screen bg-gray-50" data-testid="pos-cashier-page">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200">
        <div className="p-4 border-b">
          <h1 className="text-xl font-bold text-gray-800">POS Cashier</h1>
        </div>
        <nav className="p-4 space-y-2">
          <button
            onClick={() => navigate('/dashboard')}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100"
            data-testid="nav-dashboard"
          >
            <Home className="h-5 w-5" />
            <span>Dashboard</span>
          </button>
          <button
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg bg-blue-50 text-blue-600"
            data-testid="nav-pos"
          >
            <ShoppingCart className="h-5 w-5" />
            <span>POS</span>
          </button>
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Cari produk..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 w-80"
                  data-testid="search-product"
                />
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                {isSyncing ? (
                  <RefreshCw className="h-5 w-5 text-blue-600 animate-spin" />
                ) : isOnline ? (
                  <Cloud className="h-5 w-5 text-green-600" />
                ) : (
                  <CloudOff className="h-5 w-5 text-red-600" />
                )}
                <span className="text-sm text-gray-600">{isOnline ? 'Online' : 'Offline'}</span>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-800">{user.full_name || user.username}</p>
                <p className="text-xs text-gray-500">Kasir</p>
              </div>
              <Button variant="outline" size="icon" onClick={() => navigate('/dashboard')} data-testid="logout-pos">
                <LogOut className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Products Grid */}
          <div className="flex-1 overflow-auto p-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Produk Tersedia</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {filteredProducts.map((product) => (
                <Card
                  key={product.id}
                  className="cursor-pointer hover:shadow-lg transition-shadow"
                  onClick={() => addToCart(product)}
                  data-testid={`pos-product-${product.id}`}
                >
                  <CardContent className="p-4">
                    <div className="aspect-square bg-gray-100 rounded-lg mb-3 flex items-center justify-center">
                      {product.image_url ? (
                        <img src={product.image_url} alt={product.name} className="w-full h-full object-cover rounded-lg" />
                      ) : (
                        <Package className="h-12 w-12 text-gray-400" />
                      )}
                    </div>
                    <h3 className="font-medium text-sm text-gray-800 truncate">{product.name}</h3>
                    <p className="text-xs text-gray-500 mb-2">Stok: {product.stock}</p>
                    <p className="text-lg font-bold text-blue-600">Rp {parseFloat(product.price).toLocaleString('id-ID')}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Cart */}
          <div className="w-96 bg-white border-l border-gray-200 flex flex-col">
            <div className="p-4 border-b">
              <h2 className="text-lg font-semibold text-gray-800">Keranjang</h2>
            </div>

            {/* Customer Selection */}
            <div className="p-4 border-b">
              <Select value={selectedCustomer?.toString()} onValueChange={(value) => setSelectedCustomer(parseInt(value))}>
                <SelectTrigger data-testid="select-customer">
                  <SelectValue placeholder="Pilih pelanggan (opsional)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="0">Guest</SelectItem>
                  {customers.map((customer) => (
                    <SelectItem key={customer.id} value={customer.id.toString()}>
                      {customer.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Cart Items */}
            <div className="flex-1 overflow-auto p-4">
              {cart.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-400">
                  <ShoppingCart className="h-16 w-16 mb-4" />
                  <p>Keranjang kosong</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {cart.map((item) => (
                    <Card key={item.product_id} data-testid={`cart-item-${item.product_id}`}>
                      <CardContent className="p-3">
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-medium text-sm flex-1">{item.product_name}</h4>
                          <button
                            onClick={() => removeFromCart(item.product_id)}
                            className="text-red-600 hover:text-red-700"
                            data-testid={`remove-cart-${item.product_id}`}
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                              className="p-1 bg-gray-100 rounded hover:bg-gray-200"
                              data-testid={`decrease-qty-${item.product_id}`}
                            >
                              <Minus className="h-3 w-3" />
                            </button>
                            <span className="w-8 text-center font-medium">{item.quantity}</span>
                            <button
                              onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                              className="p-1 bg-gray-100 rounded hover:bg-gray-200"
                              data-testid={`increase-qty-${item.product_id}`}
                            >
                              <Plus className="h-3 w-3" />
                            </button>
                          </div>
                          <p className="font-semibold text-blue-600">Rp {item.subtotal.toLocaleString('id-ID')}</p>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>

            {/* Total & Checkout */}
            <div className="p-4 border-t space-y-4">
              <div className="flex items-center justify-between text-lg font-bold">
                <span>Total:</span>
                <span className="text-blue-600" data-testid="cart-total">
                  Rp {getTotalAmount().toLocaleString('id-ID')}
                </span>
              </div>
              <Button onClick={handlePayment} className="w-full bg-blue-600 hover:bg-blue-700 h-12" data-testid="checkout-btn">
                <CreditCard className="h-5 w-5 mr-2" />
                Bayar Sekarang
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Payment Dialog */}
      <Dialog open={showPaymentDialog} onOpenChange={setShowPaymentDialog}>
        <DialogContent data-testid="payment-dialog">
          <DialogHeader>
            <DialogTitle>Pilih Metode Pembayaran</DialogTitle>
            <DialogDescription>Total: Rp {getTotalAmount().toLocaleString('id-ID')}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-3">
              {paymentMethods.length > 0 ? (
                paymentMethods.map((method) => (
                  <button
                    key={method.id}
                    onClick={() => setPaymentMethod(method.type)}
                    data-testid={`payment-method-${method.type}`}
                    className={`p-4 border-2 rounded-lg hover:border-blue-600 transition-colors ${
                      paymentMethod === method.type ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
                    }`}
                  >
                    <CreditCard className="h-6 w-6 mb-2 mx-auto" />
                    <p className="font-medium text-sm">{method.name}</p>
                  </button>
                ))
              ) : (
                <>
                  <button
                    onClick={() => setPaymentMethod('cash')}
                    data-testid="payment-method-cash"
                    className={`p-4 border-2 rounded-lg hover:border-blue-600 transition-colors ${
                      paymentMethod === 'cash' ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
                    }`}
                  >
                    <CreditCard className="h-6 w-6 mb-2 mx-auto" />
                    <p className="font-medium text-sm">Cash</p>
                  </button>
                  <button
                    onClick={() => {
                      setPaymentMethod('qris');
                      generateQRIS();
                    }}
                    data-testid="payment-method-qris"
                    className={`p-4 border-2 rounded-lg hover:border-blue-600 transition-colors ${
                      paymentMethod === 'qris' ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
                    }`}
                  >
                    <CreditCard className="h-6 w-6 mb-2 mx-auto" />
                    <p className="font-medium text-sm">QRIS</p>
                  </button>
                </>
              )}
            </div>

            {showQRIS && qrisData && (
              <div className="p-4 bg-gray-50 rounded-lg text-center">
                <p className="text-sm text-gray-600 mb-2">Scan QRIS untuk membayar</p>
                <div className="bg-white p-4 rounded-lg inline-block">
                  <p className="text-xs font-mono break-all">{qrisData.qris_string}</p>
                </div>
                <p className="text-sm text-gray-600 mt-2">Mock QRIS - Rp {getTotalAmount().toLocaleString('id-ID')}</p>
              </div>
            )}

            <Button onClick={completeTransaction} className="w-full bg-green-600 hover:bg-green-700" data-testid="complete-payment-btn">
              Selesaikan Transaksi
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default POSCashier;
