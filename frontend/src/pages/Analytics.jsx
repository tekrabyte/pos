import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart3, TrendingUp, Package, ShoppingCart } from 'lucide-react';
import axiosInstance from '@/config/axios';
import { toast } from 'sonner';

const Analytics = () => {
  const [analytics, setAnalytics] = useState({
    total_revenue: 0,
    total_orders: 0,
    total_products: 0,
    total_customers: 0,
    recent_orders: [],
    top_products: [],
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    
    if (!token || !user) {
      // Don't fetch data if not logged in
      setLoading(false);
      return;
    }
    
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await axiosInstance.get('/analytics');
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
      toast.error('Gagal mengambil data analytics');
    } finally {
      setLoading(false);
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
      <div className="space-y-6" data-testid="analytics-page">
        <h1 className="text-2xl font-bold text-gray-800">Analytics & Laporan</h1>

        {/* Revenue Card */}
        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 mb-2">Total Pendapatan</p>
                <p className="text-4xl font-bold">Rp {analytics.total_revenue.toLocaleString('id-ID')}</p>
              </div>
              <div className="p-4 bg-white/20 rounded-full">
                <TrendingUp className="h-10 w-10" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 mb-2">Total Pesanan</p>
                  <p className="text-3xl font-bold">{analytics.total_orders}</p>
                </div>
                <div className="p-3 bg-green-100 rounded-full">
                  <ShoppingCart className="h-6 w-6 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 mb-2">Total Produk</p>
                  <p className="text-3xl font-bold">{analytics.total_products}</p>
                </div>
                <div className="p-3 bg-purple-100 rounded-full">
                  <Package className="h-6 w-6 text-purple-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 mb-2">Total Pelanggan</p>
                  <p className="text-3xl font-bold">{analytics.total_customers}</p>
                </div>
                <div className="p-3 bg-orange-100 rounded-full">
                  <BarChart3 className="h-6 w-6 text-orange-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Top Products */}
        <Card>
          <CardHeader>
            <CardTitle>Produk Terlaris</CardTitle>
            <CardDescription>Berdasarkan jumlah penjualan</CardDescription>
          </CardHeader>
          <CardContent>
            {analytics.top_products.length === 0 ? (
              <p className="text-gray-500 text-center py-8">Belum ada data penjualan</p>
            ) : (
              <div className="space-y-4">
                {analytics.top_products.map((product, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                    data-testid={`analytics-top-product-${index}`}
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
                        {index + 1}
                      </div>
                      <div>
                        <p className="font-semibold text-gray-800">{product.name}</p>
                        <p className="text-sm text-gray-600">{product.total_sold} unit terjual</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-lg text-blue-600">
                        Rp {parseFloat(product.total_revenue).toLocaleString('id-ID')}
                      </p>
                      <p className="text-xs text-gray-500">Total Pendapatan</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default Analytics;