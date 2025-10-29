import '@/App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { lazy, Suspense } from 'react';

// Components
import ProtectedRoute from '@/components/ProtectedRoute';

// Loading Component
const PageLoader = () => (
  <div className="flex flex-col items-center justify-center h-screen">
    <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600"></div>
    <div className="mt-4 text-gray-600 text-lg">Memuat halaman...</div>
  </div>
);

// Auth Pages - Direct import (small, need quick load)
import StaffLogin from '@/pages/auth/StaffLogin';
import CustomerLogin from '@/pages/auth/CustomerLogin';
import CustomerRegister from '@/pages/auth/CustomerRegister';

// Customer Pages - Lazy load
const CustomerMenu = lazy(() => import('@/pages/customer/CustomerMenu'));
const CustomerCart = lazy(() => import('@/pages/customer/CustomerCart'));
const CustomerOrders = lazy(() => import('@/pages/customer/CustomerOrders'));
const CustomerProfile = lazy(() => import('@/pages/customer/CustomerProfile'));

// Staff Pages - Lazy load
const Dashboard = lazy(() => import('@/pages/Dashboard'));
const Products = lazy(() => import('@/pages/Products'));
const AddProduct = lazy(() => import('@/pages/AddProduct'));
const Categories = lazy(() => import('@/pages/Categories'));
const Brands = lazy(() => import('@/pages/Brands'));
const POSCashier = lazy(() => import('@/pages/POSCashier'));
const TableManagement = lazy(() => import('@/pages/TableManagement'));
const OrderManagement = lazy(() => import('@/pages/OrderManagement'));
const Analytics = lazy(() => import('@/pages/Analytics'));
const Customers = lazy(() => import('@/pages/Customers'));
const Coupons = lazy(() => import('@/pages/Coupons'));
const Outlets = lazy(() => import('@/pages/Outlets'));
const Kiosk = lazy(() => import('@/pages/Kiosk'));
const Roles = lazy(() => import('@/pages/Roles'));
const PaymentSettingsDetail = lazy(() => import('@/pages/PaymentSettingsDetail'));

// Error Pages
const NotFound = lazy(() => import('@/pages/NotFound'));

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          {/* Main Route - E-commerce Menu */}
          <Route path="/" element={<CustomerMenu />} />
          
          {/* Auth Routes */}
          <Route path="/staff/login" element={<StaffLogin />} />
          <Route path="/customer/login" element={<CustomerLogin />} />
          <Route path="/customer/register" element={<CustomerRegister />} />
          
          {/* Customer Routes */}
          <Route path="/customer/menu" element={<CustomerMenu />} />
          <Route path="/customer/cart" element={<CustomerCart />} />
          <Route path="/customer/orders" element={
            <ProtectedRoute requiredAuth="customer">
              <CustomerOrders />
            </ProtectedRoute>
          } />
          <Route path="/customer/profile" element={
            <ProtectedRoute requiredAuth="customer">
              <CustomerProfile />
            </ProtectedRoute>
          } />
          
          {/* Staff/Admin Routes */}
          <Route path="/dashboard" element={
            <ProtectedRoute requiredAuth="staff">
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/analytics" element={
            <ProtectedRoute requiredAuth="staff">
              <Analytics />
            </ProtectedRoute>
          } />
          <Route path="/customers" element={
            <ProtectedRoute requiredAuth="staff">
              <Customers />
            </ProtectedRoute>
          } />
          <Route path="/coupons" element={
            <ProtectedRoute requiredAuth="staff">
              <Coupons />
            </ProtectedRoute>
          } />
          <Route path="/outlets" element={
            <ProtectedRoute requiredAuth="staff">
              <Outlets />
            </ProtectedRoute>
          } />
          <Route path="/roles" element={
            <ProtectedRoute requiredAuth="staff">
              <Roles />
            </ProtectedRoute>
          } />
          <Route path="/payment-settings" element={
            <ProtectedRoute requiredAuth="staff">
              <PaymentSettingsDetail />
            </ProtectedRoute>
          } />
          <Route path="/products" element={
            <ProtectedRoute requiredAuth="staff">
              <Products />
            </ProtectedRoute>
          } />
          <Route path="/products/add" element={
            <ProtectedRoute requiredAuth="staff">
              <AddProduct />
            </ProtectedRoute>
          } />
          <Route path="/brands" element={
            <ProtectedRoute requiredAuth="staff">
              <Brands />
            </ProtectedRoute>
          } />
          <Route path="/categories" element={
            <ProtectedRoute requiredAuth="staff">
              <Categories />
            </ProtectedRoute>
          } />
          <Route path="/pos" element={
            <ProtectedRoute requiredAuth="staff">
              <POSCashier />
            </ProtectedRoute>
          } />
          <Route path="/kiosk" element={<Kiosk />} />
          <Route path="/tables" element={
            <ProtectedRoute requiredAuth="staff">
              <TableManagement />
            </ProtectedRoute>
          } />
          <Route path="/orders" element={
            <ProtectedRoute requiredAuth="staff">
              <OrderManagement />
            </ProtectedRoute>
          } />
          
          {/* 404 Not Found */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" />
    </div>
  );
}

export default App;
