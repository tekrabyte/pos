import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { QrCode, Plus, Trash2, Download, Printer } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { toast } from 'sonner';
import Layout from '@/components/Layout';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const TableManagement = () => {
  const navigate = useNavigate();
  const [tables, setTables] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [newTable, setNewTable] = useState({
    table_number: '',
    capacity: 4,
    status: 'available'
  });
  const printRef = useRef();

  useEffect(() => {
    // Check authentication
    const user = localStorage.getItem('user');
    if (!user) {
      toast.error('Please login first');
      navigate('/staff/login');
      return;
    }
    fetchTables();
  }, [navigate]);

  const fetchTables = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/tables`);
      setTables(response.data);
    } catch (error) {
      console.error('Error fetching tables:', error);
      toast.error('Failed to load tables');
    } finally {
      setLoading(false);
    }
  };

  const handleAddTable = async () => {
    if (!newTable.table_number) {
      toast.error('Please enter table number');
      return;
    }

    try {
      await axios.post(`${API_URL}/api/tables`, newTable);
      toast.success('Table added successfully');
      setIsAddDialogOpen(false);
      setNewTable({ table_number: '', capacity: 4, status: 'available' });
      fetchTables();
    } catch (error) {
      console.error('Error adding table:', error);
      toast.error(error.response?.data?.detail || 'Failed to add table');
    }
  };

  const handleDeleteTable = async (tableId) => {
    if (!window.confirm('Are you sure you want to delete this table?')) {
      return;
    }

    try {
      await axios.delete(`${API_URL}/api/tables/${tableId}`);
      toast.success('Table deleted successfully');
      fetchTables();
    } catch (error) {
      console.error('Error deleting table:', error);
      toast.error('Failed to delete table');
    }
  };

  const downloadQR = (qrCode, tableNumber) => {
    const link = document.createElement('a');
    link.href = qrCode;
    link.download = `table-${tableNumber}-qr.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('QR Code downloaded');
  };

  const printQR = (qrCode, tableNumber) => {
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <html>
        <head>
          <title>Print QR Code - Table ${tableNumber}</title>
          <style>
            body {
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              min-height: 100vh;
              margin: 0;
              font-family: Arial, sans-serif;
            }
            .container {
              text-align: center;
              padding: 20px;
            }
            h1 {
              font-size: 32px;
              margin-bottom: 10px;
            }
            p {
              font-size: 18px;
              color: #666;
              margin-bottom: 20px;
            }
            img {
              width: 400px;
              height: 400px;
              border: 2px solid #333;
            }
            @media print {
              body {
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
              }
            }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>Table ${tableNumber}</h1>
            <p>Scan to Order</p>
            <img src="${qrCode}" alt="QR Code" />
          </div>
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.onload = () => {
      printWindow.print();
      printWindow.close();
    };
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading tables...</p>
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
            <h1 className="text-3xl font-bold text-gray-800">Table Management</h1>
            <p className="text-gray-600 mt-1">Manage restaurant tables and QR codes</p>
          </div>
          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <Plus className="h-4 w-4" />
                Add Table
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add New Table</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="table_number">Table Number *</Label>
                  <Input
                    id="table_number"
                    placeholder="e.g., T01, A1, Table 1"
                    value={newTable.table_number}
                    onChange={(e) => setNewTable({ ...newTable, table_number: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="capacity">Capacity</Label>
                  <Input
                    id="capacity"
                    type="number"
                    min="1"
                    value={newTable.capacity}
                    onChange={(e) => setNewTable({ ...newTable, capacity: parseInt(e.target.value) })}
                  />
                </div>
                <Button onClick={handleAddTable} className="w-full">
                  Create Table with QR Code
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Tables Grid */}
        {tables.length === 0 ? (
          <Card className="p-12 text-center">
            <QrCode className="h-16 w-16 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-700 mb-2">No tables yet</h3>
            <p className="text-gray-600 mb-4">Add your first table to generate a QR code</p>
            <Button onClick={() => setIsAddDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Table
            </Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {tables.map(table => (
              <Card key={table.id} className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-bold text-gray-800">Table {table.table_number}</h3>
                    <p className="text-sm text-gray-600">Capacity: {table.capacity} persons</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDeleteTable(table.id)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>

                {/* QR Code */}
                <div className="bg-white border-2 border-gray-200 rounded-lg p-4 mb-4">
                  {table.qr_code ? (
                    <img
                      src={table.qr_code}
                      alt={`QR Code for Table ${table.table_number}`}
                      className="w-full h-auto"
                    />
                  ) : (
                    <div className="aspect-square flex items-center justify-center bg-gray-100 rounded">
                      <QrCode className="h-12 w-12 text-gray-400" />
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => downloadQR(table.qr_code, table.table_number)}
                    className="gap-1"
                  >
                    <Download className="h-4 w-4" />
                    Download
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => printQR(table.qr_code, table.table_number)}
                    className="gap-1"
                  >
                    <Printer className="h-4 w-4" />
                    Print
                  </Button>
                </div>

                {/* Table Info */}
                <div className="mt-4 pt-4 border-t text-xs text-gray-500">
                  <p>Created: {new Date(table.created_at).toLocaleDateString('id-ID')}</p>
                  <p className="truncate" title={table.qr_token}>Token: {table.qr_token?.substring(0, 16)}...</p>
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