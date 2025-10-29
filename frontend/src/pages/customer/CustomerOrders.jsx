import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Clock, CheckCircle, XCircle, ChefHat, Package } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const statusConfig = {
  pending: { label: 'Pending', color: 'bg-yellow-100 text-yellow-800', icon: Clock },
  confirmed: { label: 'Confirmed', color: 'bg-blue-100 text-blue-800', icon: CheckCircle },
  cooking: { label: 'Cooking', color: 'bg-orange-100 text-orange-800', icon: ChefHat },
  ready: { label: 'Ready', color: 'bg-green-100 text-green-800', icon: Package },
  completed: { label: 'Completed', color: 'bg-gray-100 text-gray-800', icon: CheckCircle },
  cancelled: { label: 'Cancelled', color: 'bg-red-100 text-red-800', icon: XCircle },
};

const CustomerOrders = () => {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [customer, setCustomer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);

  useEffect(() => {
    const customerData = localStorage.getItem('customer');
    if (!customerData) {
      toast.error('Please login first');
      navigate('/customer/login');
      return;
    }
    setCustomer(JSON.parse(customerData));
    fetchOrders();
  }, [navigate]);

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API_URL}/orders`);
      // Filter orders for this customer
      const customerData = JSON.parse(localStorage.getItem('customer'));
      const ordersArray = response.data.orders || [];
      const customerOrders = ordersArray.filter(
        order => order.customer_id === customerData.id
      );
      setOrders(customerOrders);
    } catch (error) {
      console.error('Error fetching orders:', error);
      toast.error('Failed to load orders');
    } finally {
      setLoading(false);
    }
  };

  const fetchOrderDetails = async (orderId) => {
    try {
      const response = await axios.get(`${API_URL}/orders/${orderId}`);
      setSelectedOrder(response.data);
    } catch (error) {
      console.error('Error fetching order details:', error);
      toast.error('Failed to load order details');
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading orders...</p>
        </div>
      </div>
    );
  }

  if (selectedOrder) {
    const StatusIcon = statusConfig[selectedOrder.status]?.icon || Clock;
    
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white shadow-md">
          <div className="max-w-4xl mx-auto px-4 py-4">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSelectedOrder(null)}
              >
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <div>
                <h1 className="text-xl font-bold text-gray-800">Order Details</h1>
                <p className="text-sm text-gray-600">{selectedOrder.order_number}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-4 py-6 space-y-4">
          {/* Status */}
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`p-3 rounded-full ${statusConfig[selectedOrder.status]?.color}`}>
                  <StatusIcon className="h-6 w-6" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Order Status</p>
                  <p className="font-semibold text-lg">{statusConfig[selectedOrder.status]?.label}</p>
                </div>
              </div>
              <Badge variant={selectedOrder.payment_verified ? 'default' : 'secondary'}>
                {selectedOrder.payment_verified ? 'Payment Verified' : 'Pending Verification'}
              </Badge>
            </div>
          </Card>

          {/* Order Info */}
          <Card className="p-4">
            <h2 className="font-semibold mb-3">Order Information</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Order Date</span>
                <span className="font-medium">{formatDate(selectedOrder.created_at)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Order Type</span>
                <span className="font-medium capitalize">{selectedOrder.order_type}</span>
              </div>
              {selectedOrder.table_number && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Table</span>
                  <span className="font-medium">{selectedOrder.table_number}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-600">Payment Method</span>
                <span className="font-medium uppercase">{selectedOrder.payment_method}</span>
              </div>
            </div>
          </Card>

          {/* Order Items */}
          <Card className="p-4">
            <h2 className="font-semibold mb-3">Order Items</h2>
            <div className="space-y-3">
              {selectedOrder.items?.map((item, index) => (
                <div key={index} className="flex justify-between items-start py-2 border-b last:border-b-0">
                  <div className="flex-1">
                    <p className="font-medium">{item.product_name}</p>
                    <p className="text-sm text-gray-600">
                      Rp {item.price.toLocaleString('id-ID')} x {item.quantity}
                    </p>
                  </div>
                  <p className="font-semibold">
                    Rp {item.subtotal.toLocaleString('id-ID')}
                  </p>
                </div>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t">
              <div className="flex justify-between items-center text-lg font-bold">
                <span>Total</span>
                <span>Rp {selectedOrder.total_amount.toLocaleString('id-ID')}</span>
              </div>
            </div>
          </Card>

          {/* Payment Proof */}
          {selectedOrder.payment_proof && (
            <Card className="p-4">
              <h2 className="font-semibold mb-3">Payment Proof</h2>
              <img
                src={`${API_URL}${selectedOrder.payment_proof}`}
                alt="Payment Proof"
                className="w-full max-w-md mx-auto rounded-lg border"
              />
            </Card>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-md">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate('/customer/menu')}
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">My Orders</h1>
              {customer && (
                <p className="text-sm text-gray-600">{customer.name}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6">
        {orders.length === 0 ? (
          <Card className="p-12 text-center">
            <div className="text-gray-400 mb-4">
              <Package className="h-16 w-16 mx-auto" />
            </div>
            <h3 className="text-lg font-semibold text-gray-700 mb-2">No orders yet</h3>
            <p className="text-gray-600 mb-4">Start ordering to see your order history</p>
            <Button onClick={() => navigate('/customer/menu')}>
              Browse Menu
            </Button>
          </Card>
        ) : (
          <div className="space-y-4">
            {orders.map(order => {
              const StatusIcon = statusConfig[order.status]?.icon || Clock;
              
              return (
                <Card
                  key={order.id}
                  className="p-4 cursor-pointer hover:shadow-lg transition-shadow"
                  onClick={() => fetchOrderDetails(order.id)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="font-semibold text-lg">{order.order_number}</p>
                      <p className="text-sm text-gray-600">{formatDate(order.created_at)}</p>
                    </div>
                    <Badge className={statusConfig[order.status]?.color}>
                      <StatusIcon className="h-4 w-4 mr-1" />
                      {statusConfig[order.status]?.label}
                    </Badge>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <div className="text-sm text-gray-600">
                      <span className="capitalize">{order.order_type}</span>
                      {order.table_number && ` • Table ${order.table_number}`}
                    </div>
                    <p className="font-bold text-lg">
                      Rp {order.total_amount.toLocaleString('id-ID')}
                    </p>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default CustomerOrders;