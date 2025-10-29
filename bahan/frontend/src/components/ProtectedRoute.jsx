import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children, requiredAuth = 'staff' }) => {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const token = localStorage.getItem('token');
  const customerToken = localStorage.getItem('customer_token');

  // Check staff authentication
  if (requiredAuth === 'staff') {
    if (!token || !user.id) {
      return <Navigate to="/staff/login" replace />;
    }
  }

  // Check customer authentication
  if (requiredAuth === 'customer') {
    if (!customerToken) {
      return <Navigate to="/customer/login" replace />;
    }
  }

  return children;
};

export default ProtectedRoute;
