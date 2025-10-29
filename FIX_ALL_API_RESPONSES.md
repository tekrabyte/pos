# List of Files That Need Fixing

## Files with API Response Issues

1. TableManagement.jsx - line 32: `setTables(response.data || [])`
   - Should be: `setTables(response.data.tables || response.data || [])`

2. Orders.jsx - line 28: `setOrders(response.data)`
   - Should be: `setOrders(response.data.orders || response.data || [])`

3. Brands.jsx - line 34: `setBrands(response.data)`
   - Should be: `setBrands(response.data.brands || response.data || [])`

4. Customers.jsx - line 37: `setCustomers(response.data || [])`
   - Should be: `setCustomers(response.data.customers || response.data || [])`

5. Coupons.jsx - line 37: `setCoupons(response.data)`
   - Should be: `setCoupons(response.data.coupons || response.data || [])`

6. Outlets.jsx - line 37: `setOutlets(response.data)`
   - Should be: `setOutlets(response.data.outlets || response.data || [])`

7. Roles.jsx - line 32: `setRoles(response.data)`
   - Should be: `setRoles(response.data.roles || response.data || [])`

8. POSCashier.jsx - line 146: `setCustomers(response.data)`
   - Should be: `setCustomers(response.data.customers || response.data || [])`

9. CustomerMenu.jsx - line 96: `setCoupons(response.data)`
   - Should be: `setCoupons(response.data.coupons || response.data || [])`

10. Analytics.jsx - Needs early return check like Dashboard
