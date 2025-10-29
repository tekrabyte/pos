import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { QrCode, Download, Printer, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import Layout from '@/components/Layout';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const TableManagement = () => {
  const navigate = useNavigate();
  const [tables, setTables] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const user = localStorage.getItem('user');
    if (!user) {
      toast.error('Silakan login terlebih dahulu');
      navigate('/staff/login');
      return;
    }
    fetchTables();
  }, [navigate]);

  const fetchTables = async () => {
    try {
      const response = await axios.get(`${API_URL}/tables`);
      setTables(response.data.tables || response.data || []);
    } catch (error) {
      console.error('Error fetching tables:', error);
      toast.error('Gagal memuat data meja');
    } finally {
      setLoading(false);
    }
  };

  const filteredTables = tables.filter(table =>
    table.table_number?.toString().includes(searchTerm)
  );

  const downloadQR = (qrCode, tableNumber) => {
    const link = document.createElement('a');
    link.href = qrCode;
    link.download = `table-${tableNumber}-qr.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('QR Code berhasil diunduh');
  };

  const printQR = (qrCode, tableNumber) => {
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <html>
        <head>
          <title>Print QR Code - Meja ${tableNumber}</title>
          <style>
            body {
              display: flex;
              flex-direction: column;
              justify-content: center;
              align-items: center;
              height: 100vh;
              margin: 0;
              font-family: Arial, sans-serif;
            }
            .print-container {
              text-align: center;
            }
            img {
              max-width: 300px;
              height: auto;
            }
            h2 {
              margin-top: 20px;
              font-size: 24px;
            }
            @media print {
              body {
                margin: 0;
              }
            }
          </style>
        </head>
        <body>
          <div class="print-container">
            <h2>Meja ${tableNumber}</h2>
            <img src="${qrCode}" alt="QR Code" />
            <p>Scan untuk memesan</p>
          </div>
          <script>
            window.onload = function() {
              window.print();
              window.onafterprint = function() {
                window.close();
              };
            };
          </script>
        </body>
      </html>
    `);
    printWindow.document.close();
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-pulse text-gray-500">Memuat data...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Manajemen Meja</h1>
            <p className="text-sm text-gray-500 mt-1">Kelola QR code untuk setiap meja</p>
          </div>
          <div className="text-sm text-gray-500">
            Total: {filteredTables.length} meja
          </div>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Cari nomor meja..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>

        {filteredTables.length === 0 ? (
          <Card className="p-12 text-center">
            <QrCode className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">Tidak ada meja ditemukan</p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredTables.map((table) => (
              <Card key={table.id} className="p-6 hover:shadow-lg transition-shadow">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold">Meja {table.table_number}</h3>
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        table.status === 'available'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-red-100 text-red-700'
                      }`}
                    >
                      {table.status === 'available' ? 'Tersedia' : 'Terisi'}
                    </span>
                  </div>

                  <div className="bg-white border-2 border-gray-200 rounded-lg p-4">
                    {table.qr_code ? (
                      <img
                        src={table.qr_code}
                        alt={`QR Code Meja ${table.table_number}`}
                        className="w-full h-auto"
                        loading="lazy"
                      />
                    ) : (
                      <div className="aspect-square flex items-center justify-center text-gray-400">
                        <QrCode className="h-16 w-16" />
                      </div>
                    )}
                  </div>

                  <p className="text-sm text-gray-600">
                    Kapasitas: {table.capacity} orang
                  </p>

                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => downloadQR(table.qr_code, table.table_number)}
                    >
                      <Download className="h-4 w-4 mr-1" />
                      Unduh
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => printQR(table.qr_code, table.table_number)}
                    >
                      <Printer className="h-4 w-4 mr-1" />
                      Cetak
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default TableManagement;