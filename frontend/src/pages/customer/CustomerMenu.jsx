import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { ShoppingCart, Search, Plus, Minus, User, LogOut, ShoppingBag, LogIn, Star, Ticket, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const CustomerMenu = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const tableToken = searchParams.get('table');
  
  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [cart, setCart] = useState([]);
  const [tableInfo, setTableInfo] = useState(null);
  const [customer, setCustomer] = useState(null);
  const [isDineIn, setIsDineIn] = useState(false);
  const [storeSettings, setStoreSettings] = useState(null);
  const [banners, setBanners] = useState([]);
  const [coupons, setCoupons] = useState([]);
  const [currentBannerIndex, setCurrentBannerIndex] = useState(0);

  useEffect(() => {
    // Check if customer is logged in (optional)
    const customerData = localStorage.getItem('customer');
    if (customerData) {
      try {
        setCustomer(JSON.parse(customerData));
      } catch (error) {
        console.error('Error parsing customer data:', error);
      }
    }

    // If table token exists, it's dine-in
    if (tableToken) {
      setIsDineIn(true);
      fetchTableInfo();
    }

    // Load cart from localStorage
    const savedCart = localStorage.getItem('cart');
    if (savedCart) {
      try {
        setCart(JSON.parse(savedCart));
      } catch (error) {
        console.error('Error parsing cart data:', error);
      }
    }

    fetchStoreSettings();
    fetchBanners();
    fetchCoupons();
    fetchCategories();
    fetchProducts();
  }, [tableToken]);

  // Auto-rotate banners
  useEffect(() => {
    if (banners.length > 1) {
      const interval = setInterval(() => {
        setCurrentBannerIndex((prev) => (prev + 1) % banners.length);
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [banners]);

  const fetchStoreSettings = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/store-settings`);
      setStoreSettings(response.data);
    } catch (error) {
      console.error('Error fetching store settings:', error);
    }
  };

  const fetchBanners = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/store-banners`);
      setBanners(response.data);
    } catch (error) {
      console.error('Error fetching banners:', error);
    }
  };

  const fetchCoupons = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/coupons/available`);
      setCoupons(response.data);
    } catch (error) {
      console.error('Error fetching coupons:', error);
    }
  };

  const fetchTableInfo = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/tables/token/${tableToken}`);
      setTableInfo(response.data);
      toast.success(`Selamat datang di Meja ${response.data.table_number}`);
    } catch (error) {
      toast.error('Kode QR meja tidak valid');
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/categories`);
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/products`);
      setProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
      toast.error('Gagal memuat produk');
    }
  };

  const filteredProducts = products.filter(product => {
    const matchesCategory = selectedCategory === 'all' || product.category_id === selectedCategory;
    const matchesSearch = product.name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const addToCart = (product) => {
    const existingItem = cart.find(item => item.id === product.id);
    let newCart;
    
    if (existingItem) {
      newCart = cart.map(item =>
        item.id === product.id
          ? { ...item, quantity: item.quantity + 1 }
          : item
      );
    } else {
      newCart = [...cart, { ...product, quantity: 1 }];
    }
    
    setCart(newCart);
    localStorage.setItem('cart', JSON.stringify(newCart));
    toast.success(`${product.name} ditambahkan`);
  };

  const updateQuantity = (productId, change) => {
    const newCart = cart.map(item => {
      if (item.id === productId) {
        const newQuantity = item.quantity + change;
        return newQuantity > 0 ? { ...item, quantity: newQuantity } : null;
      }
      return item;
    }).filter(Boolean);
    
    setCart(newCart);
    localStorage.setItem('cart', JSON.stringify(newCart));
  };

  const getTotalItems = () => {
    return cart.reduce((sum, item) => sum + item.quantity, 0);
  };

  const handleCheckout = () => {
    if (cart.length === 0) {
      toast.error('Keranjang Anda kosong');
      return;
    }
    
    if (isDineIn && tableInfo) {
      localStorage.setItem('orderType', 'dine-in');
      localStorage.setItem('tableInfo', JSON.stringify(tableInfo));
    } else {
      localStorage.setItem('orderType', 'takeaway');
    }
    
    navigate('/customer/cart');
  };

  const handleLogout = () => {
    localStorage.removeItem('customer');
    localStorage.removeItem('customer_token');
    toast.success('Berhasil logout');
    setCustomer(null);
  };

  const nextBanner = () => {
    setCurrentBannerIndex((prev) => (prev + 1) % banners.length);
  };

  const prevBanner = () => {
    setCurrentBannerIndex((prev) => (prev - 1 + banners.length) % banners.length);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-md sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center mb-3">
            <div>
              <h1 className="text-2xl font-bold text-green-600">🍽️ {storeSettings?.store_name || 'QR Scan & Dine'}</h1>
              {isDineIn && tableInfo && (
                <p className="text-sm text-gray-600">Dine-in • Meja {tableInfo.table_number}</p>
              )}
            </div>
            <div className="flex items-center gap-2">
              {customer ? (
                <>
                  <Button variant="ghost" size="icon" onClick={() => navigate('/customer/orders')}>
                    <ShoppingBag className="h-5 w-5" />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => navigate('/customer/profile')}>
                    <User className="h-5 w-5" />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={handleLogout}>
                    <LogOut className="h-5 w-5" />
                  </Button>
                </>
              ) : (
                <Button variant="default" size="sm" onClick={() => navigate('/customer/login')} className="gap-2 bg-green-600 hover:bg-green-700">
                  <LogIn className="h-4 w-4" />
                  Masuk
                </Button>
              )}
            </div>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
            <Input
              type="text"
              placeholder="Cari menu favorit..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
      </div>

      {/* Banner Carousel */}
      {banners.length > 0 && (
        <div className="relative bg-white">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="relative h-48 rounded-xl overflow-hidden">
              <img
                src={banners[currentBannerIndex]?.image_url}
                alt={banners[currentBannerIndex]?.title}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end">
                <div className="p-6 text-white">
                  <h3 className="text-2xl font-bold mb-1">{banners[currentBannerIndex]?.title}</h3>
                  <p className="text-sm opacity-90">{banners[currentBannerIndex]?.subtitle}</p>
                </div>
              </div>
              {banners.length > 1 && (
                <>
                  <button onClick={prevBanner} className="absolute left-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white rounded-full p-2">
                    <ChevronLeft className="h-5 w-5" />
                  </button>
                  <button onClick={nextBanner} className="absolute right-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white rounded-full p-2">
                    <ChevronRight className="h-5 w-5" />
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Store Info Card */}
      {storeSettings && (
        <div className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <div className="flex items-center gap-1 bg-green-100 px-2 py-1 rounded">
                    <Star className="h-4 w-4 fill-green-600 text-green-600" />
                    <span className="font-bold text-green-700">{storeSettings.rating}</span>
                  </div>
                  <span className="text-sm text-gray-600">({storeSettings.total_reviews} ulasan)</span>
                  {storeSettings.is_open && (
                    <Badge className="bg-green-100 text-green-700 border-green-300">Buka</Badge>
                  )}
                </div>
                <p className="text-sm text-gray-600">{storeSettings.store_description}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Voucher Section */}
      {coupons.length > 0 && (
        <div className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <Ticket className="h-5 w-5 text-orange-500" />
              Promo & Voucher
            </h3>
            <div className="flex gap-3 overflow-x-auto pb-2">
              {coupons.slice(0, 3).map((coupon) => (
                <Card key={coupon.code} className="flex-shrink-0 w-64 p-3 border-2 border-dashed border-orange-300 bg-orange-50">
                  <div className="flex items-start gap-2">
                    <div className="bg-orange-500 text-white p-2 rounded">
                      <Ticket className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-bold text-sm text-orange-700">{coupon.code}</p>
                      <p className="text-xs text-gray-600 truncate">
                        {coupon.discount_type === 'percentage' 
                          ? `Diskon ${coupon.discount_value}%`
                          : `Potongan Rp ${coupon.discount_value.toLocaleString('id-ID')}`}
                      </p>
                      <p className="text-xs text-gray-500">
                        Min. Rp {coupon.min_purchase?.toLocaleString('id-ID')}
                      </p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Category Tabs */}
      <div className="bg-white border-b sticky top-[140px] z-10">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex gap-2 overflow-x-auto">
            <Button
              variant={selectedCategory === 'all' ? 'default' : 'outline'}
              onClick={() => setSelectedCategory('all')}
              className={`whitespace-nowrap ${selectedCategory === 'all' ? 'bg-green-600 hover:bg-green-700' : ''}`}
            >
              Semua
            </Button>
            {categories.map(category => (
              <Button
                key={category.id}
                variant={selectedCategory === category.id ? 'default' : 'outline'}
                onClick={() => setSelectedCategory(category.id)}
                className={`whitespace-nowrap ${selectedCategory === category.id ? 'bg-green-600 hover:bg-green-700' : ''}`}
              >
                {category.name}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* Products Grid */}
      <div className="max-w-7xl mx-auto px-4 py-6 pb-24">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredProducts.map(product => {
            const cartItem = cart.find(item => item.id === product.id);
            
            return (
              <Card key={product.id} className="overflow-hidden hover:shadow-lg transition-shadow">
                <div className="relative h-40 bg-gray-200">
                  {product.image_url ? (
                    <img src={product.image_url} alt={product.name} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-400">
                      <span className="text-5xl">🍽️</span>
                    </div>
                  )}
                  {product.stock <= 0 && (
                    <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                      <span className="text-white font-bold">Habis</span>
                    </div>
                  )}
                </div>
                
                <div className="p-3">
                  <h3 className="font-semibold text-sm text-gray-800 mb-1 line-clamp-1">{product.name}</h3>
                  {product.description && (
                    <p className="text-xs text-gray-600 mb-2 line-clamp-2">{product.description}</p>
                  )}
                  <div className="flex justify-between items-center">
                    <span className="text-base font-bold text-green-600">
                      Rp {product.price.toLocaleString('id-ID')}
                    </span>
                    {cartItem ? (
                      <div className="flex items-center gap-2 bg-green-100 rounded-lg px-2 py-1">
                        <button onClick={() => updateQuantity(product.id, -1)} className="text-green-700">
                          <Minus className="h-3 w-3" />
                        </button>
                        <span className="font-semibold text-sm min-w-[20px] text-center text-green-700">{cartItem.quantity}</span>
                        <button onClick={() => updateQuantity(product.id, 1)} disabled={product.stock <= cartItem.quantity} className="text-green-700">
                          <Plus className="h-3 w-3" />
                        </button>
                      </div>
                    ) : (
                      <Button size="sm" onClick={() => addToCart(product)} disabled={product.stock <= 0} className="gap-1 bg-green-600 hover:bg-green-700">
                        <Plus className="h-3 w-3" />
                        Tambah
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>

        {filteredProducts.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">Produk tidak ditemukan</p>
          </div>
        )}
      </div>

      {/* Floating Cart Button */}
      {cart.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t shadow-lg z-30">
          <div className="max-w-7xl mx-auto">
            <Button onClick={handleCheckout} className="w-full py-6 text-lg font-semibold bg-green-600 hover:bg-green-700">
              <ShoppingCart className="mr-2 h-5 w-5" />
              Lihat Keranjang ({getTotalItems()} item)
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CustomerMenu;