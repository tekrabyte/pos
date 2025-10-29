import '@/App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';

// Components
import ProtectedRoute from '@/components/ProtectedRoute';

// Auth Pages
import StaffLogin from '@/pages/auth/StaffLogin';
import CustomerLogin from '@/pages/auth/CustomerLogin';
import CustomerRegister from '@/pages/auth/CustomerRegister';

// Customer Pages
import CustomerMenu from '@/pages/customer/CustomerMenu';
import CustomerCart from '@/pages/customer/CustomerCart';
import CustomerOrders from '@/pages/customer/CustomerOrders';
import CustomerProfile from '@/pages/customer/CustomerProfile';

// Staff Pages
import Dashboard from '@/pages/Dashboard';
import Products from '@/pages/Products';
import AddProduct from '@/pages/AddProduct';
import Categories from '@/pages/Categories';
import Brands from '@/pages/Brands';
import POSCashier from '@/pages/POSCashier';
import TableManagement from '@/pages/TableManagement';
import OrderManagement from '@/pages/OrderManagement';
import Analytics from '@/pages/Analytics';
import Customers from '@/pages/Customers';
import Coupons from '@/pages/Coupons';
import Outlets from '@/pages/Outlets';
import Kiosk from '@/pages/Kiosk';
import Roles from '@/pages/Roles';
import PaymentSettingsDetail from '@/pages/PaymentSettingsDetail';

// Error Pages
import NotFound from '@/pages/NotFound';

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
