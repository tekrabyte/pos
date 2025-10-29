import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Package, ShoppingCart, Users, TrendingUp } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}`;

const Dashboard = () => {
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
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      const data = response.data;
      
      // Transform data to match component structure
      setAnalytics({
        total_revenue: data.stats?.total?.revenue || 0,
        total_orders: data.stats?.total?.orders || 0,
        total_products: data.stats?.total?.products || 0,
        total_customers: data.stats?.total?.customers || 0,
        recent_orders: data.recent_orders || [],
        top_products: data.top_products || [],
      });
    } catch (error) {
      console.error('Error fetching analytics:', error);
      toast.error('Gagal mengambil data analytics');
    } finally {
      setLoading(false);
    }
  };

  const stats = [
    {
      title: 'Total Pendapatan',
      value: `Rp ${analytics.total_revenue.toLocaleString('id-ID')}`,
      icon: TrendingUp,
      color: 'text-green-600',
      bg: 'bg-green-100',
    },
    {
      title: 'Total Pesanan',
      value: analytics.total_orders,
      icon: ShoppingCart,
      color: 'text-blue-600',
      bg: 'bg-blue-100',
    },
    {
      title: 'Total Produk',
      value: analytics.total_products,
      icon: Package,
      color: 'text-purple-600',
      bg: 'bg-purple-100',
    },
    {
      title: 'Total Pelanggan',
      value: analytics.total_customers,
      icon: Users,
      color: 'text-orange-600',
      bg: 'bg-orange-100',
    },
  ];

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
      <div className="space-y-6" data-testid="dashboard-page">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <Card key={index} className="hover:shadow-lg transition-shadow" data-testid={`stat-card-${index}`}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">{stat.title}</p>
                      <p className="text-2xl font-bold mt-2">{stat.value}</p>
                    </div>
                    <div className={`p-3 rounded-full ${stat.bg}`}>
                      <Icon className={`h-6 w-6 ${stat.color}`} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Orders */}
          <Card data-testid="recent-orders-card">
            <CardHeader>
              <CardTitle>Pesanan Terbaru</CardTitle>
              <CardDescription>10 pesanan terakhir</CardDescription>
            </CardHeader>
            <CardContent>
              {analytics.recent_orders.length === 0 ? (
                <p className="text-gray-500 text-center py-4">Belum ada pesanan</p>
              ) : (
                <div className="space-y-3">
                  {analytics.recent_orders.map((order) => (
                    <div
                      key={order.id}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      data-testid={`recent-order-${order.id}`}
                    >
                      <div>
                        <p className="font-medium">{order.order_number}</p>
                        <p className="text-sm text-gray-600">{order.customer_name || 'Guest'}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">Rp {parseFloat(order.total_amount).toLocaleString('id-ID')}</p>
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          order.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                        }`}>
                          {order.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Top Products */}
          <Card data-testid="top-products-card">
            <CardHeader>
              <CardTitle>Produk Terlaris</CardTitle>
              <CardDescription>Berdasarkan jumlah penjualan</CardDescription>
            </CardHeader>
            <CardContent>
              {analytics.top_products.length === 0 ? (
                <p className="text-gray-500 text-center py-4">Belum ada data penjualan</p>
              ) : (
                <div className="space-y-3">
                  {analytics.top_products.map((product, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      data-testid={`top-product-${index}`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-blue-600 font-semibold">{index + 1}</span>
                        </div>
                        <div>
                          <p className="font-medium">{product.name}</p>
                          <p className="text-sm text-gray-600">{product.total_sold} terjual</p>
                        </div>
                      </div>
                      <p className="font-semibold">Rp {parseFloat(product.total_revenue).toLocaleString('id-ID')}</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;