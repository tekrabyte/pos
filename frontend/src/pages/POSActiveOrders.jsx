import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosInstance from '@/config/axios';
import { Clock, CheckCircle, XCircle, Eye, Check, X, UtensilsCrossed, ShoppingBag, ImageIcon, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { toast } from 'sonner';
import Layout from '@/components/Layout';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';

const statusConfig = {
  pending: { label: 'Pending', color: 'bg-yellow-100 text-yellow-800 border-yellow-300', icon: Clock },
  processing: { label: 'Processing', color: 'bg-blue-100 text-blue-800 border-blue-300', icon: Clock },
  preparing: { label: 'Preparing', color: 'bg-orange-100 text-orange-800 border-orange-300', icon: Clock },
  completed: { label: 'Completed', color: 'bg-green-100 text-green-800 border-green-300', icon: CheckCircle },
  cancelled: { label: 'Cancelled', color: 'bg-red-100 text-red-800 border-red-300', icon: XCircle },
};

const POSActiveOrders = () => {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState('all');
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showPaymentProof, setShowPaymentProof] = useState(false);
  const [paymentProofUrl, setPaymentProofUrl] = useState('');
  const [verifyAction, setVerifyAction] = useState(null); // 'approve' or 'reject'
  const [showVerifyDialog, setShowVerifyDialog] = useState(false);
  const [verifyingOrderId, setVerifyingOrderId] = useState(null);

  useEffect(() => {
    // Check authentication
    const user = localStorage.getItem('user');
    if (!user) {
      toast.error('Silakan login terlebih dahulu');
      navigate('/staff/login');
      return;
    }

    fetchActiveOrders();
    
    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchActiveOrders, 10000);
    return () => clearInterval(interval);
  }, [navigate]);

  const fetchActiveOrders = async () => {
    try {
      // Fetch orders with status: pending, processing, preparing
      const response = await axiosInstance.get('/orders/filter?status=active');
      const ordersData = Array.isArray(response.data) ? response.data : (response.data.orders || []);
      setOrders(ordersData);
    } catch (error) {
      console.error('Error fetching active orders:', error);
      toast.error('Gagal memuat pesanan aktif');
    } finally {
      setLoading(false);
    }
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

  const handleVerifyPayment = async (orderId, approve) => {
    setVerifyingOrderId(orderId);
    try {
      await axiosInstance.put(`/orders/${orderId}/verify-payment`, {
        verified: approve,
        status: approve ? 'processing' : 'cancelled'
      });
      
      toast.success(approve ? 'Pembayaran diverifikasi' : 'Pembayaran ditolak');
      fetchActiveOrders();
      
      if (selectedOrder && selectedOrder.id === orderId) {
        setShowDetailDialog(false);
        setSelectedOrder(null);
      }
    } catch (error) {
      console.error('Error verifying payment:', error);
      toast.error('Gagal memverifikasi pembayaran');
    } finally {
      setVerifyingOrderId(null);
      setShowVerifyDialog(false);
    }
  };

  const handleShowPaymentProof = (proofUrl) => {
    const fullUrl = proofUrl.startsWith('http') ? proofUrl : `${process.env.REACT_APP_BACKEND_URL}${proofUrl}`;
    setPaymentProofUrl(fullUrl);
    setShowPaymentProof(true);
  };

  const getFilteredOrders = () => {
    if (selectedTab === 'all') return orders;
    if (selectedTab === 'dine-in') return orders.filter(order => order.order_type === 'dine-in');
    if (selectedTab === 'takeaway') return orders.filter(order => order.order_type === 'takeaway');
    return orders;
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

  const filteredOrders = getFilteredOrders();

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-full">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600">Memuat pesanan aktif...</span>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Pesanan Aktif - POS Cashier</h1>
          <p className="text-gray-600 mt-1">
            Kelola pesanan yang sedang dalam proses (Pending, Processing, Preparing)
          </p>
        </div>

        {/* Tabs */}
        <Tabs value={selectedTab} onValueChange={setSelectedTab}>
          <TabsList className="grid w-full max-w-md grid-cols-3">
            <TabsTrigger value="all">
              Semua ({filteredOrders.length})
            </TabsTrigger>
            <TabsTrigger value="dine-in">
              <UtensilsCrossed className="h-4 w-4 mr-2" />
              Dine-in ({orders.filter(o => o.order_type === 'dine-in').length})
            </TabsTrigger>
            <TabsTrigger value="takeaway">
              <ShoppingBag className="h-4 w-4 mr-2" />
              Takeaway ({orders.filter(o => o.order_type === 'takeaway').length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value={selectedTab} className="mt-6">
            {filteredOrders.length === 0 ? (
              <Card className="p-12 text-center">
                <CheckCircle className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-700 mb-2">
                  Tidak ada pesanan aktif
                </h3>
                <p className="text-gray-500">
                  Semua pesanan sudah diproses atau belum ada pesanan masuk
                </p>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredOrders.map((order) => {
                  const StatusIcon = statusConfig[order.status]?.icon || Clock;
                  return (
                    <Card key={order.id} className="p-4 hover:shadow-lg transition-shadow">
                      <div className="space-y-3">
                        {/* Order Header */}
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="font-bold text-lg">{order.order_number}</h3>
                            <p className="text-sm text-gray-600">{formatDate(order.created_at)}</p>
                          </div>
                          <Badge className={`${statusConfig[order.status]?.color} border`}>
                            <StatusIcon className="h-3 w-3 mr-1" />
                            {statusConfig[order.status]?.label}
                          </Badge>
                        </div>

                        {/* Order Type */}
                        <div className="flex items-center gap-2">
                          {order.order_type === 'dine-in' ? (
                            <Badge variant="outline" className="bg-blue-50 text-blue-700">
                              <UtensilsCrossed className="h-3 w-3 mr-1" />
                              Dine-in
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="bg-green-50 text-green-700">
                              <ShoppingBag className="h-3 w-3 mr-1" />
                              Takeaway
                            </Badge>
                          )}
                          {order.table_id && (
                            <span className="text-sm text-gray-600">
                              Meja #{order.table_id}
                            </span>
                          )}
                        </div>

                        {/* Customer Info */}
                        <div className="border-t pt-2">
                          <p className="text-sm font-medium">{order.customer_name || 'Guest'}</p>
                          {order.customer_phone && (
                            <p className="text-sm text-gray-600">{order.customer_phone}</p>
                          )}
                        </div>

                        {/* Payment Info */}
                        <div className="border-t pt-2">
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">Total:</span>
                            <span className="font-bold text-lg">{formatCurrency(order.total_amount)}</span>
                          </div>
                          <div className="flex justify-between items-center mt-1">
                            <span className="text-sm text-gray-600">Metode:</span>
                            <Badge variant="outline" className="text-xs">
                              {order.payment_method === 'cash' ? 'Cash' : 
                               order.payment_method === 'qris' ? 'QRIS' : 
                               order.payment_method === 'bank_transfer' ? 'Transfer Bank' : 
                               order.payment_method}
                            </Badge>
                          </div>
                        </div>

                        {/* Payment Verification Status */}
                        {order.payment_proof && (
                          <div className="border-t pt-2">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium text-gray-700">Bukti Bayar:</span>
                              {order.payment_verified ? (
                                <Badge className="bg-green-100 text-green-800 border-green-300">
                                  <CheckCircle className="h-3 w-3 mr-1" />
                                  Terverifikasi
                                </Badge>
                              ) : (
                                <Badge className="bg-yellow-100 text-yellow-800 border-yellow-300">
                                  <Clock className="h-3 w-3 mr-1" />
                                  Menunggu Verifikasi
                                </Badge>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Actions */}
                        <div className="flex gap-2 pt-2 border-t">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => fetchOrderDetails(order.id)}
                            className="flex-1"
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            Detail
                          </Button>
                          
                          {order.payment_proof && !order.payment_verified && (
                            <>
                              <Button
                                size="sm"
                                variant="default"
                                onClick={() => {
                                  setVerifyAction('approve');
                                  setVerifyingOrderId(order.id);
                                  setShowVerifyDialog(true);
                                }}
                                className="flex-1 bg-green-600 hover:bg-green-700"
                                disabled={verifyingOrderId === order.id}
                              >
                                {verifyingOrderId === order.id && verifyAction === 'approve' ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <>
                                    <Check className="h-4 w-4 mr-1" />
                                    Verifikasi
                                  </>
                                )}
                              </Button>
                              <Button
                                size="sm"
                                variant="destructive"
                                onClick={() => {
                                  setVerifyAction('reject');
                                  setVerifyingOrderId(order.id);
                                  setShowVerifyDialog(true);
                                }}
                                disabled={verifyingOrderId === order.id}
                              >
                                {verifyingOrderId === order.id && verifyAction === 'reject' ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <X className="h-4 w-4" />
                                )}
                              </Button>
                            </>
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

                  {/* Payment Proof */}
                  {selectedOrder.payment_proof && (
                    <div className="bg-blue-50 p-4 rounded-lg space-y-2">
                      <h4 className="font-semibold text-gray-900">Bukti Pembayaran</h4>
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Status Verifikasi:</span>
                        {selectedOrder.payment_verified ? (
                          <Badge className="bg-green-100 text-green-800 border-green-300">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Terverifikasi
                          </Badge>
                        ) : (
                          <Badge className="bg-yellow-100 text-yellow-800 border-yellow-300">
                            <Clock className="h-3 w-3 mr-1" />
                            Menunggu Verifikasi
                          </Badge>
                        )}
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleShowPaymentProof(selectedOrder.payment_proof)}
                        className="w-full"
                      >
                        <ImageIcon className="h-4 w-4 mr-2" />
                        Lihat Bukti Pembayaran
                      </Button>
                      
                      {!selectedOrder.payment_verified && (
                        <div className="flex gap-2 mt-4">
                          <Button
                            variant="default"
                            onClick={() => {
                              setVerifyAction('approve');
                              setShowVerifyDialog(true);
                            }}
                            className="flex-1 bg-green-600 hover:bg-green-700"
                          >
                            <Check className="h-4 w-4 mr-2" />
                            Verifikasi Pembayaran
                          </Button>
                          <Button
                            variant="destructive"
                            onClick={() => {
                              setVerifyAction('reject');
                              setShowVerifyDialog(true);
                            }}
                          >
                            <X className="h-4 w-4 mr-2" />
                            Tolak
                          </Button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </>
            )}
          </DialogContent>
        </Dialog>

        {/* Payment Proof Dialog */}
        <Dialog open={showPaymentProof} onOpenChange={setShowPaymentProof}>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle>Bukti Pembayaran</DialogTitle>
            </DialogHeader>
            <div className="flex items-center justify-center bg-gray-100 rounded-lg p-4">
              <img
                src={paymentProofUrl}
                alt="Payment Proof"
                className="max-w-full max-h-[70vh] object-contain"
                onError={(e) => {
                  e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTgiIGZpbGw9IiM5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5HYWdhbCBtZW11YXQgZ2FtYmFyPC90ZXh0Pjwvc3ZnPg==';
                }}
              />
            </div>
          </DialogContent>
        </Dialog>

        {/* Verify Payment Confirmation Dialog */}
        <AlertDialog open={showVerifyDialog} onOpenChange={setShowVerifyDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>
                {verifyAction === 'approve' ? 'Verifikasi Pembayaran?' : 'Tolak Pembayaran?'}
              </AlertDialogTitle>
              <AlertDialogDescription>
                {verifyAction === 'approve' 
                  ? 'Setelah diverifikasi, pesanan akan diproses. Pastikan pembayaran sudah diterima.'
                  : 'Pesanan akan dibatalkan dan pelanggan perlu melakukan pembayaran ulang.'}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Batal</AlertDialogCancel>
              <AlertDialogAction
                onClick={() => handleVerifyPayment(
                  selectedOrder?.id || verifyingOrderId,
                  verifyAction === 'approve'
                )}
                className={verifyAction === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}
              >
                {verifyAction === 'approve' ? 'Ya, Verifikasi' : 'Ya, Tolak'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </Layout>
  );
};

export default POSActiveOrders;
