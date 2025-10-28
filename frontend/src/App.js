import '@/App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import Products from '@/pages/Products';
import AddProduct from '@/pages/AddProduct';
import Categories from '@/pages/Categories';
import Brands from '@/pages/Brands';
import Orders from '@/pages/Orders';
import Customers from '@/pages/Customers';
import Analytics from '@/pages/Analytics';
import Coupons from '@/pages/Coupons';
import Outlets from '@/pages/Outlets';
import Roles from '@/pages/Roles';
import PaymentSettings from '@/pages/PaymentSettings';
import POSCashier from '@/pages/POSCashier';
import Kiosk from '@/pages/Kiosk';

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/kiosk" element={<Kiosk />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/add" element={<AddProduct />} />
          <Route path="/products/edit/:id" element={<AddProduct />} />
          <Route path="/categories" element={<Categories />} />
          <Route path="/brands" element={<Brands />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/customers" element={<Customers />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/coupons" element={<Coupons />} />
          <Route path="/outlets" element={<Outlets />} />
          <Route path="/roles" element={<Roles />} />
          <Route path="/payment-settings" element={<PaymentSettings />} />
          <Route path="/pos" element={<POSCashier />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" />
    </div>
  );
}

export default App;
