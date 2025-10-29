import '@/App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';

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
import PaymentSettings from '@/pages/PaymentSettings';

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          {/* Auth Routes */}
          <Route path="/" element={<StaffLogin />} />
          <Route path="/staff/login" element={<StaffLogin />} />
          <Route path="/customer/login" element={<CustomerLogin />} />
          <Route path="/customer/register" element={<CustomerRegister />} />
          
          {/* Customer Routes */}
          <Route path="/customer/menu" element={<CustomerMenu />} />
          <Route path="/customer/cart" element={<CustomerCart />} />
          <Route path="/customer/orders" element={<CustomerOrders />} />
          <Route path="/customer/profile" element={<CustomerProfile />} />
          
          {/* Staff/Admin Routes */}
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/customers" element={<Customers />} />
          <Route path="/coupons" element={<Coupons />} />
          <Route path="/outlets" element={<Outlets />} />
          <Route path="/roles" element={<Roles />} />
          <Route path="/payment-settings" element={<PaymentSettings />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/add" element={<AddProduct />} />
          <Route path="/brands" element={<Brands />} />
          <Route path="/categories" element={<Categories />} />
          <Route path="/pos" element={<POSCashier />} />
          <Route path="/kiosk" element={<Kiosk />} />
          <Route path="/tables" element={<TableManagement />} />
          <Route path="/orders" element={<OrderManagement />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" />
    </div>
  );
}

export default App;
