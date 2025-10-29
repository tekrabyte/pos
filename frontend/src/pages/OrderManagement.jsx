import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Bell, Clock, CheckCircle, XCircle, ChefHat, Package, Eye, Check, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';
import Layout from '@/components/Layout';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const WS_URL = API_URL.replace('https://', 'wss://').replace('http://', 'ws://');

const statusConfig = {
  pending: { label: 'Pending', color: 'bg-yellow-100 text-yellow-800 border-yellow-300', icon: Clock },
  confirmed: { label: 'Confirmed', color: 'bg-blue-100 text-blue-800 border-blue-300', icon: CheckCircle },
  cooking: { label: 'Cooking', color: 'bg-orange-100 text-orange-800 border-orange-300', icon: ChefHat },
  ready: { label: 'Ready', color: 'bg-green-100 text-green-800 border-green-300', icon: Package },
  completed: { label: 'Completed', color: 'bg-gray-100 text-gray-800 border-gray-300', icon: CheckCircle },
  cancelled: { label: 'Cancelled', color: 'bg-red-100 text-red-800 border-red-300', icon: XCircle },
};

const OrderManagement = () => {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState('all');
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [pendingCount, setPendingCount] = useState(0);
  const wsRef = useRef(null);
  const audioRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  useEffect(() => {
    // Check authentication
    const user = localStorage.getItem('user');
    if (!user) {
      toast.error('Silakan login terlebih dahulu');
      navigate('/staff/login');
      return;
    }

    fetchOrders();
    
    // Create audio element for notification sound
    if (!audioRef.current) {
      audioRef.current = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBTGH0fPTgjMGHm7A7+OZRQ0RUqfn77BhGAg+ltrzxnMpBSh+zPLaizsIGGS57OihUhELTKXh8bllHAU2jdXzzn0vBSF1xe/glUQME1mu5O+rWBYKQ5zd8sFuJAUuhM/z1YU2Bhxqvu7mnEoODk+k5vCzZBsHO5HU8sp3LgUme8rx3I4+CRZiturqpVYTC0mi4POzaB8GM4nR88p1KwUme8nw3I1ACRdhtuvsp1kVDEyn5O+wYxsIO5TU8sx4LgUleMnw24w/CRZftO3so1YVDE2o5PC0ZhwFOI/U88t2LQUmd8jw24s+CRZetuzrpVgVDEyl4/CyZBoGOpHU88p3LwUles7y24w+CRVftOzsplkUDEqm5PC0ZhsGOZDU88p2LwUme8vx241ACRVetOzrpVcTDEuo4/GxYhgFNozT8sl2LAUidsjv24k+CRRctOvrpFYTDEuk4/CxYhgFNo3T88p4LgUme8rx3I4/CRVbtOvqpVYTC0qj4fCyYxkFNo3T88t5LwUle8vx3I4+CRVatuzqpFUSDEuh4PCxYRcFNIzS88l2LAUiesjv24k+CRRbtOvrpFYTDEqk4/CxYRcFNIvS88l2KwUhe8fw24g+CRRbtOvqo1UTDEyk4/CxYRgGNozT8sl2LQUjeMfu24k+CRRbtOvqo1QTDE2o5PC0ZxwGOZHV88p3LwUme8rx3I4/CRZftuzsp1oWDU6p5fGzaBwHO5LW88t5MAUmfcrx3Y9BCRZS');
    }
    
    // Connect WebSocket only if not already connected
    if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
      connectWebSocket();
    }

    return () => {
      // Clear reconnect timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      
      // Close WebSocket connection
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [navigate]);

  const connectWebSocket = () => {
    // Prevent multiple connections
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    try {
      const ws = new WebSocket(`${WS_URL}/api/ws/orders`);
      
      ws.onopen = () => {
        console.log('WebSocket connected successfully');
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'new_order') {
          // Play notification sound
          audioRef.current?.play().catch(e => console.log('Audio play failed:', e));
          
          // Show toast notification
          toast.success('Pesanan Baru Masuk!', {
            description: `Order #${data.order_number} - Rp ${data.total_amount.toLocaleString('id-ID')}`,
            duration: 5000,
          });
          
          // Refresh orders
          fetchOrders();
        } else if (data.type === 'order_status_update') {
          // Refresh orders on status update
          fetchOrders();
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected');
        wsRef.current = null;
        
        // Only reconnect if it wasn't a clean close and component is still mounted
        if (!event.wasClean && reconnectTimeoutRef.current === null) {
          console.log('Attempting to reconnect in 3 seconds...');
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectTimeoutRef.current = null;
            connectWebSocket();
          }, 3000);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('WebSocket connection error:', error);
      
      // Retry connection after 3 seconds
      if (reconnectTimeoutRef.current === null) {
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectTimeoutRef.current = null;
          connectWebSocket();
        }, 3000);
      }
    }
  };

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/orders`);
      setOrders(response.data);
      
      // Update pending count
      const pending = response.data.filter(order => order.status === 'pending').length;
      setPendingCount(pending);
    } catch (error) {
      console.error('Error fetching orders:', error);
      toast.error('Failed to load orders');
    } finally {
      setLoading(false);
    }
  };

  const fetchOrderDetails = async (orderId) => {
    try {
      const response = await axios.get(`${API_URL}/api/orders/${orderId}`);
      setSelectedOrder(response.data);
    } catch (error) {
      console.error('Error fetching order details:', error);
      toast.error('Failed to load order details');
    }
  };

  const updateOrderStatus = async (orderId, newStatus, paymentVerified = null) => {
    try {
      const updateData = { status: newStatus };
      if (paymentVerified !== null) {
        updateData.payment_verified = paymentVerified;
      }

      await axios.put(`${API_URL}/api/orders/${orderId}/status`, updateData);
      toast.success(`Order ${newStatus}`);
      fetchOrders();
      
      if (selectedOrder && selectedOrder.id === orderId) {
        fetchOrderDetails(orderId);
      }
    } catch (error) {
      console.error('Error updating order status:', error);
      toast.error('Failed to update order status');
    }
  };

  const confirmOrder = (orderId) => {
    updateOrderStatus(orderId, 'confirmed', true);
  };

  const rejectOrder = (orderId) => {
    if (window.confirm('Are you sure you want to reject this order?')) {
      updateOrderStatus(orderId, 'cancelled', false);
    }
  };

  const getFilteredOrders = () => {
    if (selectedTab === 'all') return orders;
    return orders.filter(order => order.status === selectedTab);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('id-ID', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading orders...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">Order Management</h1>
            <p className="text-gray-600 mt-1">Manage all restaurant orders in real-time</p>
          </div>
          <div className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-gray-600" />
            <span className="text-sm text-gray-600">Real-time notifications enabled</span>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-yellow-100 rounded-lg">
                <Clock className="h-6 w-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Pending</p>
                <p className="text-2xl font-bold">{orders.filter(o => o.status === 'pending').length}</p>
              </div>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-100 rounded-lg">
                <CheckCircle className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Confirmed</p>
                <p className="text-2xl font-bold">{orders.filter(o => o.status === 'confirmed').length}</p>
              </div>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-orange-100 rounded-lg">
                <ChefHat className="h-6 w-6 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Cooking</p>
                <p className="text-2xl font-bold">{orders.filter(o => o.status === 'cooking').length}</p>
              </div>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-green-100 rounded-lg">
                <Package className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Ready</p>
                <p className="text-2xl font-bold">{orders.filter(o => o.status === 'ready').length}</p>
              </div>
            </div>
          </Card>
        </div>

        {/* Orders Tabs */}
        <Tabs value={selectedTab} onValueChange={setSelectedTab}>
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="all">All ({orders.length})</TabsTrigger>
            <TabsTrigger value="pending" className="relative">
              Pending
              {pendingCount > 0 && (
                <Badge className="ml-2 bg-red-500">{pendingCount}</Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="confirmed">Confirmed</TabsTrigger>
            <TabsTrigger value="cooking">Cooking</TabsTrigger>
            <TabsTrigger value="ready">Ready</TabsTrigger>
            <TabsTrigger value="completed">Completed</TabsTrigger>
          </TabsList>

          <TabsContent value={selectedTab} className="space-y-4 mt-6">
            {getFilteredOrders().length === 0 ? (
              <Card className="p-12 text-center">
                <Package className="h-16 w-16 mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-semibold text-gray-700 mb-2">No orders found</h3>
                <p className="text-gray-600">Orders will appear here when customers place them</p>
              </Card>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {getFilteredOrders().map(order => {
                  const StatusIcon = statusConfig[order.status]?.icon || Clock;
                  
                  return (
                    <Card
                      key={order.id}
                      className={`p-4 border-l-4 ${order.status === 'pending' ? 'border-l-yellow-500 bg-yellow-50' : ''}`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="font-bold text-lg">{order.order_number}</h3>
                            <Badge className={statusConfig[order.status]?.color}>
                              <StatusIcon className="h-3 w-3 mr-1" />
                              {statusConfig[order.status]?.label}
                            </Badge>
                            {!order.payment_verified && order.status === 'pending' && (
                              <Badge variant="destructive">Payment Not Verified</Badge>
                            )}
                          </div>
                          
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
                            <div>
                              <p className="font-medium">Type</p>
                              <p className="capitalize">{order.order_type}</p>
                            </div>
                            {order.table_number && (
                              <div>
                                <p className="font-medium">Table</p>
                                <p>{order.table_number}</p>
                              </div>
                            )}
                            {order.customer_name && (
                              <div>
                                <p className="font-medium">Customer</p>
                                <p>{order.customer_name}</p>
                              </div>
                            )}
                            <div>
                              <p className="font-medium">Total</p>
                              <p className="font-bold text-green-600">
                                Rp {order.total_amount.toLocaleString('id-ID')}
                              </p>
                            </div>
                            <div>
                              <p className="font-medium">Time</p>
                              <p>{formatDate(order.created_at)}</p>
                            </div>
                          </div>
                        </div>

                        <div className="flex gap-2 ml-4">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => fetchOrderDetails(order.id)}
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            View
                          </Button>
                          
                          {order.status === 'pending' && (
                            <>
                              <Button
                                variant="default"
                                size="sm"
                                onClick={() => confirmOrder(order.id)}
                                className="bg-green-600 hover:bg-green-700"
                              >
                                <Check className="h-4 w-4 mr-1" />
                                Confirm
                              </Button>
                              <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => rejectOrder(order.id)}
                              >
                                <X className="h-4 w-4 mr-1" />
                                Reject
                              </Button>
                            </>
                          )}
                          
                          {order.status === 'confirmed' && (
                            <Button
                              variant="default"
                              size="sm"
                              onClick={() => updateOrderStatus(order.id, 'cooking')}
                            >
                              Start Cooking
                            </Button>
                          )}
                          
                          {order.status === 'cooking' && (
                            <Button
                              variant="default"
                              size="sm"
                              onClick={() => updateOrderStatus(order.id, 'ready')}
                            >
                              Mark Ready
                            </Button>
                          )}
                          
                          {order.status === 'ready' && (
                            <Button
                              variant="default"
                              size="sm"
                              onClick={() => updateOrderStatus(order.id, 'completed')}
                            >
                              Complete
                            </Button>
                          )}
                        </div>
                      </div>
                    </Card>
                  );
                })}
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Order Details Dialog */}
        <Dialog open={!!selectedOrder} onOpenChange={() => setSelectedOrder(null)}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            {selectedOrder && (
              <>
                <DialogHeader>
                  <DialogTitle>Order Details - {selectedOrder.order_number}</DialogTitle>
                </DialogHeader>
                
                <div className="space-y-4">
                  {/* Status */}
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <Badge className={statusConfig[selectedOrder.status]?.color}>
                        {statusConfig[selectedOrder.status]?.label}
                      </Badge>
                      {selectedOrder.payment_verified ? (
                        <Badge variant="default">Payment Verified</Badge>
                      ) : (
                        <Badge variant="secondary">Payment Pending</Badge>
                      )}
                    </div>
                    <div className="text-sm text-gray-600">
                      {formatDate(selectedOrder.created_at)}
                    </div>
                  </div>

                  {/* Order Info */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Order Type</p>
                      <p className="font-medium capitalize">{selectedOrder.order_type}</p>
                    </div>
                    {selectedOrder.table_number && (
                      <div>
                        <p className="text-gray-600">Table</p>
                        <p className="font-medium">{selectedOrder.table_number}</p>
                      </div>
                    )}
                    {selectedOrder.customer_name && (
                      <div>
                        <p className="text-gray-600">Customer</p>
                        <p className="font-medium">{selectedOrder.customer_name}</p>
                      </div>
                    )}
                    {selectedOrder.customer_phone && (
                      <div>
                        <p className="text-gray-600">Phone</p>
                        <p className="font-medium">{selectedOrder.customer_phone}</p>
                      </div>
                    )}
                    <div>
                      <p className="text-gray-600">Payment Method</p>
                      <p className="font-medium uppercase">{selectedOrder.payment_method}</p>
                    </div>
                  </div>

                  {/* Items */}
                  <div>
                    <h3 className="font-semibold mb-2">Order Items</h3>
                    <div className="space-y-2">
                      {selectedOrder.items?.map((item, index) => (
                        <div key={index} className="flex justify-between items-center py-2 border-b">
                          <div>
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
                    <div className="flex justify-between items-center pt-3 border-t-2 font-bold text-lg">
                      <span>Total</span>
                      <span>Rp {selectedOrder.total_amount.toLocaleString('id-ID')}</span>
                    </div>
                  </div>

                  {/* Payment Proof */}
                  {selectedOrder.payment_proof && (
                    <div>
                      <h3 className="font-semibold mb-2">Payment Proof</h3>
                      <img
                        src={`${API_URL}${selectedOrder.payment_proof}`}
                        alt="Payment Proof"
                        className="w-full max-w-md mx-auto rounded-lg border"
                      />
                    </div>
                  )}

                  {/* Actions */}
                  {selectedOrder.status === 'pending' && (
                    <div className="flex gap-2">
                      <Button
                        onClick={() => {
                          confirmOrder(selectedOrder.id);
                          setSelectedOrder(null);
                        }}
                        className="flex-1 bg-green-600 hover:bg-green-700"
                      >
                        Confirm Order
                      </Button>
                      <Button
                        variant="destructive"
                        onClick={() => {
                          rejectOrder(selectedOrder.id);
                          setSelectedOrder(null);
                        }}
                        className="flex-1"
                      >
                        Reject Order
                      </Button>
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

export default OrderManagement;