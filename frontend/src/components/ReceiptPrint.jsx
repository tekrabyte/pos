import React, { forwardRef } from 'react';

const ReceiptPrint = forwardRef(({ orderData, cart, totalAmount }, ref) => {
  const formatDate = (date) => {
    return new Date(date).toLocaleString('id-ID', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div ref={ref} className="p-8 bg-white" style={{ width: '302px' }}>
      <style>
        {`
          @media print {
            @page {
              size: 80mm auto;
              margin: 0;
            }
            body {
              margin: 0;
              padding: 0;
            }
          }
        `}
      </style>
      
      <div className="text-center mb-4">
        <h1 className="text-xl font-bold">POS MERCHANT</h1>
        <p className="text-xs">Jl. Utama No. 1, Jakarta</p>
        <p className="text-xs">Telp: 021-1234567</p>
        <div className="border-t border-dashed my-2"></div>
      </div>

      <div className="text-xs space-y-1 mb-2">
        <div className="flex justify-between">
          <span>No. Order:</span>
          <span className="font-semibold">{orderData?.order_number || 'ORD-XXXX'}</span>
        </div>
        <div className="flex justify-between">
          <span>Tanggal:</span>
          <span>{formatDate(new Date())}</span>
        </div>
        <div className="flex justify-between">
          <span>Kasir:</span>
          <span>{orderData?.user_name || 'Kasir'}</span>
        </div>
        {orderData?.customer_name && (
          <div className="flex justify-between">
            <span>Customer:</span>
            <span>{orderData.customer_name}</span>
          </div>
        )}
      </div>

      <div className="border-t border-dashed my-2"></div>

      <table className="w-full text-xs mb-2">
        <thead>
          <tr className="border-b">
            <th className="text-left py-1">Item</th>
            <th className="text-center py-1">Qty</th>
            <th className="text-right py-1">Harga</th>
            <th className="text-right py-1">Total</th>
          </tr>
        </thead>
        <tbody>
          {cart.map((item, index) => (
            <tr key={index} className="border-b">
              <td className="py-1">{item.product_name}</td>
              <td className="text-center py-1">{item.quantity}</td>
              <td className="text-right py-1">
                {parseFloat(item.price).toLocaleString('id-ID')}
              </td>
              <td className="text-right py-1">
                {parseFloat(item.subtotal).toLocaleString('id-ID')}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="border-t border-dashed my-2"></div>

      <div className="text-xs space-y-1">
        <div className="flex justify-between font-semibold text-base">
          <span>TOTAL:</span>
          <span>Rp {parseFloat(totalAmount).toLocaleString('id-ID')}</span>
        </div>
        <div className="flex justify-between">
          <span>Pembayaran:</span>
          <span className="uppercase">{orderData?.payment_method || 'CASH'}</span>
        </div>
      </div>

      <div className="border-t border-dashed my-2"></div>

      <div className="text-center text-xs space-y-1">
        <p className="font-semibold">TERIMA KASIH</p>
        <p>Barang yang sudah dibeli</p>
        <p>tidak dapat dikembalikan</p>
      </div>
    </div>
  );
});

ReceiptPrint.displayName = 'ReceiptPrint';

export default ReceiptPrint;
