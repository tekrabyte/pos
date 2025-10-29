import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import axios from 'axios';
import { toast } from 'sonner';
import { format } from 'date-fns';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showDialog, setShowDialog] = useState(false);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API}/orders`);
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
      toast.error('Gagal mengambil data pesanan');
    } finally {
      setLoading(false);
    }
  };

  const fetchOrderDetail = async (orderId) => {
    try {
      const response = await axios.get(`${API}/orders/${orderId}`);
      setSelectedOrder(response.data);
      setShowDialog(true);
    } catch (error) {
      console.error('Error fetching order detail:', error);
      toast.error('Gagal mengambil detail pesanan');
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
      <div className="space-y-6" data-testid="orders-page">
        <h1 className="text-2xl font-bold text-gray-800">Daftar Pesanan</h1>

        {orders.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <p className="text-gray-500">Belum ada pesanan</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {orders.map((order) => (
              <Card key={order.id} className="hover:shadow-lg transition-shadow" data-testid={`order-card-${order.id}`}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-lg">{order.order_number}</h3>
                        <Badge
                          variant={order.status === 'completed' ? 'default' : 'secondary'}
                          className={order.status === 'completed' ? 'bg-green-500' : 'bg-yellow-500'}
                        >
                          {order.status}
                        </Badge>
                      </div>
                      <div className="space-y-1 text-sm text-gray-600">
                        <p>Pelanggan: {order.customer_name || 'Guest'}</p>
                        <p>Outlet: {order.outlet_name || '-'}</p>
                        <p>Kasir: {order.user_name || '-'}</p>
                        <p>Pembayaran: {order.payment_method}</p>
                        {order.created_at && (
                          <p>Tanggal: {format(new Date(order.created_at), 'dd MMM yyyy HH:mm')}</p>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-blue-600 mb-4">
                        Rp {parseFloat(order.total_amount).toLocaleString('id-ID')}
                      </p>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => fetchOrderDetail(order.id)}
                        data-testid={`view-order-${order.id}`}
                      >
                        <Eye className="h-4 w-4 mr-2" />
                        Detail
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-2xl" data-testid="order-detail-dialog">
          <DialogHeader>
            <DialogTitle>Detail Pesanan</DialogTitle>
            <DialogDescription>{selectedOrder?.order_number}</DialogDescription>
          </DialogHeader>
          {selectedOrder && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">Pelanggan</p>
                  <p className="font-medium">{selectedOrder.customer_name || 'Guest'}</p>
                </div>
                <div>
                  <p className="text-gray-600">Status</p>
                  <Badge
                    variant={selectedOrder.status === 'completed' ? 'default' : 'secondary'}
                    className={selectedOrder.status === 'completed' ? 'bg-green-500' : 'bg-yellow-500'}
                  >
                    {selectedOrder.status}
                  </Badge>
                </div>
                <div>
                  <p className="text-gray-600">Outlet</p>
                  <p className="font-medium">{selectedOrder.outlet_name || '-'}</p>
                </div>
                <div>
                  <p className="text-gray-600">Kasir</p>
                  <p className="font-medium">{selectedOrder.user_name || '-'}</p>
                </div>
                <div>
                  <p className="text-gray-600">Pembayaran</p>
                  <p className="font-medium">{selectedOrder.payment_method}</p>
                </div>
                <div>
                  <p className="text-gray-600">Tanggal</p>
                  <p className="font-medium">
                    {selectedOrder.created_at ? format(new Date(selectedOrder.created_at), 'dd MMM yyyy HH:mm') : '-'}
                  </p>
                </div>
              </div>

              <div className="border-t pt-4">
                <h4 className="font-semibold mb-3">Item Pesanan</h4>
                <div className="space-y-2">
                  {selectedOrder.items?.map((item, index) => (
                    <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded" data-testid={`order-item-${index}`}>
                      <div>
                        <p className="font-medium">{item.product_name}</p>
                        <p className="text-sm text-gray-600">
                          {item.quantity} x Rp {parseFloat(item.price).toLocaleString('id-ID')}
                        </p>
                      </div>
                      <p className="font-semibold">Rp {parseFloat(item.subtotal).toLocaleString('id-ID')}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="border-t pt-4">
                <div className="flex justify-between items-center">
                  <p className="text-lg font-semibold">Total</p>
                  <p className="text-2xl font-bold text-blue-600">
                    Rp {parseFloat(selectedOrder.total_amount).toLocaleString('id-ID')}
                  </p>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </Layout>
  );
};

export default Orders;