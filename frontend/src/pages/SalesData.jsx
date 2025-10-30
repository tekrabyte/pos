import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosInstance from '@/config/axios';
import { CheckCircle, XCircle, Eye, Download, Calendar, TrendingUp, DollarSign, ShoppingCart, UtensilsCrossed, ShoppingBag, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { toast } from 'sonner';
import Layout from '@/components/Layout';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const statusConfig = {
  completed: { label: 'Selesai', color: 'bg-green-100 text-green-800 border-green-300', icon: CheckCircle },
  cancelled: { label: 'Dibatalkan', color: 'bg-red-100 text-red-800 border-red-300', icon: XCircle },
};

const SalesData = () => {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState('all');
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  
  // Date filters
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  
  // Analytics
  const [analytics, setAnalytics] = useState({
    totalSales: 0,
    totalOrders: 0,
    completedOrders: 0,
    cancelledOrders: 0,
    averageOrderValue: 0,
  });

  useEffect(() => {
    // Check authentication
    const user = localStorage.getItem('user');
    if (!user) {
      toast.error('Silakan login terlebih dahulu');
      navigate('/staff/login');
      return;
    }

    // Set default date range (last 30 days)
    const today = new Date();
    const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
    setStartDate(thirtyDaysAgo.toISOString().split('T')[0]);
    setEndDate(today.toISOString().split('T')[0]);

    fetchCompletedOrders();
  }, [navigate]);

  useEffect(() => {
    // Recalculate analytics whenever orders change
    calculateAnalytics();
  }, [orders]);

  const fetchCompletedOrders = async () => {
    setLoading(true);
    try {
      // Fetch orders with status: completed, cancelled
      const response = await axiosInstance.get('/orders/filter?status=completed');
      const ordersData = Array.isArray(response.data) ? response.data : (response.data.orders || []);
      setOrders(ordersData);
    } catch (error) {
      console.error('Error fetching completed orders:', error);
      toast.error('Gagal memuat data penjualan');
    } finally {
      setLoading(false);
    }
  };

  const calculateAnalytics = () => {
    const completed = orders.filter(o => o.status === 'completed');
    const cancelled = orders.filter(o => o.status === 'cancelled');
    
    const totalSales = completed.reduce((sum, order) => sum + (order.total_amount || 0), 0);
    const totalOrders = orders.length;
    const averageOrderValue = completed.length > 0 ? totalSales / completed.length : 0;

    setAnalytics({
      totalSales,
      totalOrders,
      completedOrders: completed.length,
      cancelledOrders: cancelled.length,
      averageOrderValue,
    });
  };

  const fetchOrderDetails = async (orderId) => {
    try {
      const response = await axiosInstance.get(`/orders/${orderId}`);
      const orderData = response.data.order || response.data;
      setSelectedOrder(orderData);
      setShowDetailDialog(true);
    } catch (error) {
      console.error('Error fetching order details:', error);
      toast.error('Gagal memuat detail pesanan');
    }
  };

  const getFilteredOrders = () => {
    let filtered = orders;

    // Filter by tab
    if (selectedTab === 'completed') {
      filtered = filtered.filter(order => order.status === 'completed');
    } else if (selectedTab === 'cancelled') {
      filtered = filtered.filter(order => order.status === 'cancelled');
    } else if (selectedTab === 'dine-in') {
      filtered = filtered.filter(order => order.order_type === 'dine-in' && order.status === 'completed');
    } else if (selectedTab === 'takeaway') {
      filtered = filtered.filter(order => order.order_type === 'takeaway' && order.status === 'completed');
    }

    // Filter by date range
    if (startDate && endDate) {
      const start = new Date(startDate);
      const end = new Date(endDate);
      end.setHours(23, 59, 59, 999); // Include the entire end date
      
      filtered = filtered.filter(order => {
        const orderDate = new Date(order.created_at);
        return orderDate >= start && orderDate <= end;
      });
    }

    return filtered;
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('id-ID', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const exportToCSV = () => {
    const filtered = getFilteredOrders();
    
    if (filtered.length === 0) {
      toast.error('Tidak ada data untuk diekspor');
      return;
    }

    // Create CSV content
    const headers = ['No. Pesanan', 'Tanggal', 'Tipe', 'Pelanggan', 'Total', 'Metode Pembayaran', 'Status'];
    const rows = filtered.map(order => [
      order.order_number,
      formatDate(order.created_at),
      order.order_type === 'dine-in' ? 'Dine-in' : 'Takeaway',
      order.customer_name || 'Guest',
      order.total_amount,
      order.payment_method,
      order.status === 'completed' ? 'Selesai' : 'Dibatalkan',
    ]);

    let csvContent = headers.join(',') + '\n';
    rows.forEach(row => {
      csvContent += row.map(cell => `"${cell}"`).join(',') + '\n';
    });

    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `sales_data_${new Date().getTime()}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    toast.success('Data berhasil diekspor');
  };

  const filteredOrders = getFilteredOrders();

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-full">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600">Memuat data penjualan...</span>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Data Penjualan</h1>
            <p className="text-gray-600 mt-1">
              Laporan penjualan dan riwayat transaksi yang sudah selesai
            </p>
          </div>
          <Button onClick={exportToCSV} variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
        </div>

        {/* Date Range Filter */}
        <Card className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
            <div>
              <Label htmlFor="start-date">Tanggal Mulai</Label>
              <Input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="end-date">Tanggal Akhir</Label>
              <Input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
            <Button onClick={fetchCompletedOrders} variant="default">
              <Calendar className="h-4 w-4 mr-2" />
              Filter
            </Button>
          </div>
        </Card>

        {/* Analytics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-green-100 rounded-lg">
                <DollarSign className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Penjualan</p>
                <p className="text-xl font-bold">{formatCurrency(analytics.totalSales)}</p>
              </div>
            </div>
          </Card>
          
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-100 rounded-lg">
                <ShoppingCart className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Pesanan</p>
                <p className="text-xl font-bold">{analytics.totalOrders}</p>
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-purple-100 rounded-lg">
                <CheckCircle className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Selesai</p>
                <p className="text-xl font-bold">{analytics.completedOrders}</p>
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-orange-100 rounded-lg">
                <TrendingUp className="h-6 w-6 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Rata-rata</p>
                <p className="text-xl font-bold">{formatCurrency(analytics.averageOrderValue)}</p>
              </div>
            </div>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={selectedTab} onValueChange={setSelectedTab}>
          <TabsList className="grid w-full max-w-2xl grid-cols-5">
            <TabsTrigger value="all">
              Semua ({orders.length})
            </TabsTrigger>
            <TabsTrigger value="completed">
              <CheckCircle className="h-4 w-4 mr-2" />
              Selesai ({orders.filter(o => o.status === 'completed').length})
            </TabsTrigger>
            <TabsTrigger value="cancelled">
              <XCircle className="h-4 w-4 mr-2" />
              Batal ({orders.filter(o => o.status === 'cancelled').length})
            </TabsTrigger>
            <TabsTrigger value="dine-in">
              <UtensilsCrossed className="h-4 w-4 mr-2" />
              Dine-in
            </TabsTrigger>
            <TabsTrigger value="takeaway">
              <ShoppingBag className="h-4 w-4 mr-2" />
              Takeaway
            </TabsTrigger>
          </TabsList>

          <TabsContent value={selectedTab} className="mt-6">
            {filteredOrders.length === 0 ? (
              <Card className="p-12 text-center">
                <ShoppingCart className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-700 mb-2">
                  Tidak ada data penjualan
                </h3>
                <p className="text-gray-500">
                  {startDate && endDate 
                    ? 'Tidak ada transaksi dalam rentang tanggal yang dipilih'
                    : 'Belum ada transaksi yang selesai'}
                </p>
              </Card>
            ) : (
              <div className="space-y-3">
                {filteredOrders.map((order) => {
                  const StatusIcon = statusConfig[order.status]?.icon || CheckCircle;
                  return (
                    <Card key={order.id} className="p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between">
                        {/* Order Info */}
                        <div className="flex-1 grid grid-cols-1 md:grid-cols-5 gap-4">
                          {/* Order Number & Date */}
                          <div>
                            <h3 className="font-bold text-sm">{order.order_number}</h3>
                            <p className="text-xs text-gray-600">{formatDate(order.created_at)}</p>
                          </div>

                          {/* Order Type */}
                          <div className="flex items-center gap-2">
                            {order.order_type === 'dine-in' ? (
                              <Badge variant="outline" className="bg-blue-50 text-blue-700 text-xs">
                                <UtensilsCrossed className="h-3 w-3 mr-1" />
                                Dine-in
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="bg-green-50 text-green-700 text-xs">
                                <ShoppingBag className="h-3 w-3 mr-1" />
                                Takeaway
                              </Badge>
                            )}
                          </div>

                          {/* Customer */}
                          <div>
                            <p className="text-sm font-medium">{order.customer_name || 'Guest'}</p>
                            {order.customer_phone && (
                              <p className="text-xs text-gray-600">{order.customer_phone}</p>
                            )}
                          </div>

                          {/* Total */}
                          <div>
                            <p className="text-sm font-bold text-green-600">
                              {formatCurrency(order.total_amount)}
                            </p>
                            <p className="text-xs text-gray-600">
                              {order.payment_method === 'cash' ? 'Cash' : 
                               order.payment_method === 'qris' ? 'QRIS' : 
                               order.payment_method === 'bank_transfer' ? 'Transfer' : 
                               order.payment_method}
                            </p>
                          </div>

                          {/* Status */}
                          <div className="flex items-center gap-2">
                            <Badge className={`${statusConfig[order.status]?.color} border text-xs`}>
                              <StatusIcon className="h-3 w-3 mr-1" />
                              {statusConfig[order.status]?.label}
                            </Badge>
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="ml-4">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => fetchOrderDetails(order.id)}
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            Detail
                          </Button>
                        </div>
                      </div>
                    </Card>
                  );
                })}
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Order Detail Dialog */}
        <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            {selectedOrder && (
              <>
                <DialogHeader>
                  <DialogTitle className="text-2xl">Detail Pesanan</DialogTitle>
                  <DialogDescription>
                    {selectedOrder.order_number} - {formatDate(selectedOrder.created_at)}
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-4">
                  {/* Status */}
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-700">Status:</span>
                    <Badge className={`${statusConfig[selectedOrder.status]?.color} border`}>
                      {statusConfig[selectedOrder.status]?.label}
                    </Badge>
                  </div>

                  {/* Order Type */}
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-700">Tipe Pesanan:</span>
                    {selectedOrder.order_type === 'dine-in' ? (
                      <Badge variant="outline" className="bg-blue-50 text-blue-700">
                        <UtensilsCrossed className="h-3 w-3 mr-1" />
                        Dine-in {selectedOrder.table_id && `- Meja #${selectedOrder.table_id}`}
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="bg-green-50 text-green-700">
                        <ShoppingBag className="h-3 w-3 mr-1" />
                        Takeaway
                      </Badge>
                    )}
                  </div>

                  {/* Customer Info */}
                  <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                    <h4 className="font-semibold text-gray-900">Informasi Pelanggan</h4>
                    <p className="text-sm"><span className="font-medium">Nama:</span> {selectedOrder.customer_name || 'Guest'}</p>
                    {selectedOrder.customer_phone && (
                      <p className="text-sm"><span className="font-medium">Telepon:</span> {selectedOrder.customer_phone}</p>
                    )}
                  </div>

                  {/* Order Items */}
                  {selectedOrder.items && selectedOrder.items.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Item Pesanan</h4>
                      <div className="space-y-2">
                        {selectedOrder.items.map((item, idx) => (
                          <div key={idx} className="flex justify-between items-center border-b pb-2">
                            <div>
                              <p className="font-medium">{item.product_name}</p>
                              <p className="text-sm text-gray-600">
                                {item.quantity} x {formatCurrency(item.price)}
                              </p>
                            </div>
                            <p className="font-semibold">{formatCurrency(item.quantity * item.price)}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Payment Info */}
                  <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                    <h4 className="font-semibold text-gray-900">Informasi Pembayaran</h4>
                    <div className="flex justify-between">
                      <span className="text-sm">Subtotal:</span>
                      <span className="font-medium">{formatCurrency(selectedOrder.original_amount || selectedOrder.total_amount)}</span>
                    </div>
                    {selectedOrder.discount_amount > 0 && (
                      <div className="flex justify-between text-green-600">
                        <span className="text-sm">Diskon:</span>
                        <span className="font-medium">-{formatCurrency(selectedOrder.discount_amount)}</span>
                      </div>
                    )}
                    <div className="flex justify-between text-lg font-bold border-t pt-2">
                      <span>Total:</span>
                      <span>{formatCurrency(selectedOrder.total_amount)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Metode Pembayaran:</span>
                      <Badge variant="outline">
                        {selectedOrder.payment_method === 'cash' ? 'Cash' : 
                         selectedOrder.payment_method === 'qris' ? 'QRIS' : 
                         selectedOrder.payment_method === 'bank_transfer' ? 'Transfer Bank' : 
                         selectedOrder.payment_method}
                      </Badge>
                    </div>
                  </div>

                  {/* Completed/Cancelled Info */}
                  {selectedOrder.completed_at && (
                    <div className="bg-green-50 p-4 rounded-lg">
                      <p className="text-sm text-green-800">
                        <span className="font-medium">
                          {selectedOrder.status === 'completed' ? 'Selesai pada:' : 'Dibatalkan pada:'}
                        </span>{' '}
                        {formatDate(selectedOrder.completed_at)}
                      </p>
                    </div>
                  )}
                </div>
              </>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
};

export default SalesData;
