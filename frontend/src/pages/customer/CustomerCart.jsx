import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Trash2, Upload, CreditCard, Building2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const CustomerCart = () => {
  const navigate = useNavigate();
  const [cart, setCart] = useState([]);
  const [customer, setCustomer] = useState(null);
  const [orderType, setOrderType] = useState('takeaway');
  const [tableInfo, setTableInfo] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState('qris');
  const [paymentProof, setPaymentProof] = useState(null);
  const [paymentProofUrl, setPaymentProofUrl] = useState('');
  const [bankAccounts, setBankAccounts] = useState([]);
  const [qrisData, setQrisData] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    // Load cart
    const savedCart = localStorage.getItem('cart');
    if (savedCart) {
      setCart(JSON.parse(savedCart));
    } else {
      toast.error('Your cart is empty');
      navigate('/customer/menu');
      return;
    }

    // Load customer
    const customerData = localStorage.getItem('customer');
    if (customerData) {
      setCustomer(JSON.parse(customerData));
    }

    // Load order type and table info
    const type = localStorage.getItem('orderType') || 'takeaway';
    setOrderType(type);
    
    if (type === 'dine-in') {
      const table = localStorage.getItem('tableInfo');
      if (table) {
        setTableInfo(JSON.parse(table));
      }
    }

    fetchBankAccounts();
  }, [navigate]);

  useEffect(() => {
    if (paymentMethod === 'qris' && cart.length > 0) {
      generateQRIS();
    }
  }, [paymentMethod, cart]);

  const fetchBankAccounts = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/bank-accounts`);
      setBankAccounts(response.data);
    } catch (error) {
      console.error('Error fetching bank accounts:', error);
    }
  };

  const generateQRIS = async () => {
    try {
      const total = calculateTotal();
      const response = await axios.post(`${API_URL}/api/qris/generate`, {
        amount: total,
        order_number: `TEMP-${Date.now()}`,
        merchant_id: 'POSMERCHANT001'
      });
      setQrisData(response.data);
    } catch (error) {
      console.error('Error generating QRIS:', error);
    }
  };

  const calculateTotal = () => {
    return cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        toast.error('File size must be less than 5MB');
        return;
      }

      setPaymentProof(file);
      
      // Upload immediately
      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await axios.post(`${API_URL}/api/upload/payment-proof`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        setPaymentProofUrl(response.data.url);
        toast.success('Payment proof uploaded');
      } catch (error) {
        toast.error('Failed to upload payment proof');
        console.error(error);
      }
    }
  };

  const handleSubmitOrder = async () => {
    if (!paymentProofUrl) {
      toast.error('Please upload payment proof');
      return;
    }

    if (orderType === 'takeaway' && !customer) {
      toast.error('Please login to place takeaway order');
      navigate('/customer/login');
      return;
    }

    setIsSubmitting(true);

    try {
      const orderData = {
        customer_id: customer?.id || null,
        table_id: tableInfo?.id || null,
        order_type: orderType,
        customer_name: customer?.name || null,
        customer_phone: customer?.phone || null,
        items: cart.map(item => ({
          product_id: item.id,
          product_name: item.name,
          quantity: item.quantity,
          price: item.price,
          subtotal: item.price * item.quantity
        })),
        payment_method: paymentMethod,
        payment_proof: paymentProofUrl,
        total_amount: calculateTotal()
      };

      const response = await axios.post(`${API_URL}/api/orders`, orderData);
      
      // Clear cart
      localStorage.removeItem('cart');
      localStorage.removeItem('orderType');
      localStorage.removeItem('tableInfo');
      
      toast.success('Order placed successfully!');
      navigate('/customer/orders');
    } catch (error) {
      console.error('Error submitting order:', error);
      toast.error(error.response?.data?.detail || 'Failed to place order');
    } finally {
      setIsSubmitting(false);
    }
  };

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
            <h1 className="text-2xl font-bold text-gray-800">Checkout</h1>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Order Type Info */}
        <Card className="p-4">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-sm text-gray-600">Order Type</p>
              <p className="font-semibold text-lg capitalize">{orderType}</p>
              {tableInfo && (
                <p className="text-sm text-gray-600">Table {tableInfo.table_number}</p>
              )}
            </div>
            {customer && (
              <div className="text-right">
                <p className="text-sm text-gray-600">Customer</p>
                <p className="font-semibold">{customer.name}</p>
                <p className="text-sm text-gray-600">{customer.phone}</p>
              </div>
            )}
          </div>
        </Card>

        {/* Cart Items */}
        <Card className="p-4">
          <h2 className="font-semibold text-lg mb-4">Order Items</h2>
          <div className="space-y-3">
            {cart.map(item => (
              <div key={item.id} className="flex justify-between items-center py-2 border-b last:border-b-0">
                <div className="flex-1">
                  <p className="font-medium">{item.name}</p>
                  <p className="text-sm text-gray-600">
                    Rp {item.price.toLocaleString('id-ID')} x {item.quantity}
                  </p>
                </div>
                <p className="font-semibold">
                  Rp {(item.price * item.quantity).toLocaleString('id-ID')}
                </p>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t">
            <div className="flex justify-between items-center text-lg font-bold">
              <span>Total</span>
              <span>Rp {calculateTotal().toLocaleString('id-ID')}</span>
            </div>
          </div>
        </Card>

        {/* Payment Method */}
        <Card className="p-4">
          <h2 className="font-semibold text-lg mb-4">Payment Method</h2>
          <RadioGroup value={paymentMethod} onValueChange={setPaymentMethod}>
            <div className="flex items-center space-x-2 p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
              <RadioGroupItem value="qris" id="qris" />
              <Label htmlFor="qris" className="flex-1 cursor-pointer">
                <div className="flex items-center gap-2">
                  <CreditCard className="h-5 w-5" />
                  <span className="font-medium">QRIS</span>
                </div>
              </Label>
            </div>
            <div className="flex items-center space-x-2 p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
              <RadioGroupItem value="bank_transfer" id="bank_transfer" />
              <Label htmlFor="bank_transfer" className="flex-1 cursor-pointer">
                <div className="flex items-center gap-2">
                  <Building2 className="h-5 w-5" />
                  <span className="font-medium">Bank Transfer</span>
                </div>
              </Label>
            </div>
          </RadioGroup>

          {/* QRIS Display */}
          {paymentMethod === 'qris' && qrisData && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg text-center">
              <p className="text-sm text-gray-600 mb-2">Scan QR Code to Pay</p>
              <img 
                src={qrisData.qr_code_image} 
                alt="QRIS" 
                className="mx-auto w-64 h-64 border-2 border-gray-300 rounded-lg"
              />
              <p className="text-lg font-bold mt-2">
                Rp {calculateTotal().toLocaleString('id-ID')}
              </p>
            </div>
          )}

          {/* Bank Transfer Info */}
          {paymentMethod === 'bank_transfer' && (
            <div className="mt-4 space-y-2">
              {bankAccounts.map(bank => (
                <div key={bank.id} className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-semibold">{bank.bank_name}</p>
                  <p className="text-sm text-gray-600">{bank.account_number}</p>
                  <p className="text-sm text-gray-600">{bank.account_name}</p>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Upload Payment Proof */}
        <Card className="p-4">
          <h2 className="font-semibold text-lg mb-4">Upload Payment Proof</h2>
          <div className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <Input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="hidden"
                id="payment-proof"
              />
              <Label htmlFor="payment-proof" className="cursor-pointer">
                <Upload className="h-12 w-12 mx-auto text-gray-400 mb-2" />
                <p className="text-sm text-gray-600">
                  {paymentProof ? paymentProof.name : 'Click to upload payment proof'}
                </p>
                <p className="text-xs text-gray-500 mt-1">Max 5MB (JPG, PNG)</p>
              </Label>
            </div>

            {paymentProofUrl && (
              <div className="text-center">
                <img 
                  src={`${API_URL}${paymentProofUrl}`} 
                  alt="Payment Proof" 
                  className="mx-auto max-h-64 rounded-lg border"
                />
              </div>
            )}
          </div>
        </Card>

        {/* Submit Button */}
        <Button
          onClick={handleSubmitOrder}
          disabled={!paymentProofUrl || isSubmitting}
          className="w-full py-6 text-lg font-semibold"
          size="lg"
        >
          {isSubmitting ? 'Placing Order...' : 'Place Order'}
        </Button>
      </div>
    </div>
  );
};

export default CustomerCart;