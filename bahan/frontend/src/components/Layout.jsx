import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { 
  LayoutDashboard, Package, ShoppingCart, Users, Tag, 
  BarChart3, Settings, Store, UserCog, CreditCard,
  Menu, X, LogOut, Boxes, Percent, ChevronDown, Monitor, 
  QrCode, UtensilsCrossed
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const menuItems = [
    { icon: LayoutDashboard, label: 'Beranda', path: '/dashboard' },
    { icon: ShoppingCart, label: 'Pesanan', path: '/orders' },
    { icon: QrCode, label: 'Meja / Tables', path: '/tables' },
    { icon: Users, label: 'Pelanggan', path: '/customers' },
    { icon: Percent, label: 'Kupon', path: '/coupons' },
    { icon: BarChart3, label: 'Analytics', path: '/analytics' },
    { icon: Store, label: 'Outlet', path: '/outlets' },
    { icon: UserCog, label: 'Roles', path: '/roles' },
    { icon: CreditCard, label: 'Payment', path: '/payment-settings' },
  ];

  const productMenu = [
    { label: 'Semua Produk', path: '/products' },
    { label: 'Tambah Produk', path: '/products/add' },
    { label: 'Brand / Merek', path: '/brands' },
    { label: 'Kategori', path: '/categories' },
  ];

  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    navigate('/staff/login');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 h-full bg-white border-r border-gray-200 transition-all duration-300 z-40 ${
          sidebarOpen ? 'w-64' : 'w-0'
        } overflow-hidden`}
      >
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold text-gray-800">POS System</h1>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden"
              data-testid="close-sidebar-btn"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
        </div>

        <nav className="p-4 space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                data-testid={`menu-${item.label.toLowerCase()}`}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive(item.path)
                    ? 'bg-blue-50 text-blue-600'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Icon className="h-5 w-5" />
                <span className="font-medium">{item.label}</span>
              </button>
            );
          })}

          {/* Product Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                data-testid="menu-produk"
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  location.pathname.startsWith('/products') ||
                  location.pathname === '/brands' ||
                  location.pathname === '/categories'
                    ? 'bg-blue-50 text-blue-600'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Package className="h-5 w-5" />
                <span className="font-medium flex-1 text-left">Produk</span>
                <ChevronDown className="h-4 w-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-56">
              {productMenu.map((item) => (
                <DropdownMenuItem
                  key={item.path}
                  onClick={() => navigate(item.path)}
                  data-testid={`submenu-${item.label.toLowerCase().replace(/ /g, '-')}`}
                  className="cursor-pointer"
                >
                  {item.label}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* POS Button */}
          <button
            onClick={() => navigate('/pos')}
            data-testid="menu-pos"
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg bg-gradient-to-r from-green-500 to-emerald-600 text-white hover:from-green-600 hover:to-emerald-700 transition-all mt-4"
          >
            <Boxes className="h-5 w-5" />
            <span className="font-medium">Kasir / POS</span>
          </button>

          {/* Kiosk Button */}
          <button
            onClick={() => navigate('/kiosk')}
            data-testid="menu-kiosk"
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700 transition-all mt-2"
          >
            <Monitor className="h-5 w-5" />
            <span className="font-medium">Kiosk Self-Service</span>
          </button>
        </nav>
      </aside>

      {/* Main Content */}
      <div
        className={`flex-1 flex flex-col transition-all duration-300 ${
          sidebarOpen ? 'lg:ml-64' : 'ml-0'
        }`}
      >
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                data-testid="toggle-sidebar-btn"
              >
                <Menu className="h-5 w-5" />
              </Button>
              <h2 className="text-xl font-semibold text-gray-800">
                {location.pathname === '/dashboard'
                  ? 'Beranda'
                  : location.pathname
                      .split('/')
                      .pop()
                      .charAt(0)
                      .toUpperCase() +
                    location.pathname.split('/').pop().slice(1)}
              </h2>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-800">
                  {user.full_name || user.username}
                </p>
                <p className="text-xs text-gray-500">Administrator</p>
              </div>
              <Button
                variant="outline"
                size="icon"
                onClick={handleLogout}
                data-testid="logout-btn"
              >
                <LogOut className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  );
};

export default Layout;