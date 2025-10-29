package main

import (
	"database/sql"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"
)

// Response helpers
func SuccessResponse(c *fiber.Ctx, data interface{}) error {
	return c.JSON(fiber.Map{
		"success": true,
		"data":    data,
	})
}

func ErrorResponse(c *fiber.Ctx, message string, statusCode int) error {
	return c.Status(statusCode).JSON(fiber.Map{
		"success": false,
		"message": message,
	})
}

// Health Check
func HealthCheck(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{
		"status":    "OK",
		"message":   "Laravel POS API is running",
		"timestamp": time.Now().Format("2006-01-02 15:04:05"),
		"version":   "1.0.0",
	})
}

// JWT Claims
type Claims struct {
	UserID   int    `json:"user_id"`
	Username string `json:"username"`
	Role     string `json:"role"`
	jwt.RegisteredClaims
}

// Generate JWT token
func GenerateToken(user *User) (string, error) {
	expirationTime := time.Now().Add(24 * time.Hour)
	
	roleStr := ""
	if user.Role.Valid {
		roleStr = user.Role.String
	}
	
	claims := &Claims{
		UserID:   user.ID,
		Username: user.Username,
		Role:     roleStr,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(expirationTime),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	jwtSecret := os.Getenv("JWT_SECRET")
	if jwtSecret == "" {
		jwtSecret = "default_secret"
	}
	return token.SignedString([]byte(jwtSecret))
}

// Auth Middleware
func AuthMiddleware(c *fiber.Ctx) error {
	authHeader := c.Get("Authorization")
	if authHeader == "" {
		return ErrorResponse(c, "Authorization header required", fiber.StatusUnauthorized)
	}

	tokenString := strings.TrimPrefix(authHeader, "Bearer ")
	if tokenString == authHeader {
		return ErrorResponse(c, "Invalid authorization format", fiber.StatusUnauthorized)
	}

	claims := &Claims{}
	jwtSecret := os.Getenv("JWT_SECRET")
	if jwtSecret == "" {
		jwtSecret = "default_secret"
	}

	token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
		return []byte(jwtSecret), nil
	})

	if err != nil || !token.Valid {
		return ErrorResponse(c, "Invalid or expired token", fiber.StatusUnauthorized)
	}

	c.Locals("user_id", claims.UserID)
	c.Locals("username", claims.Username)
	c.Locals("role", claims.Role)
	return c.Next()
}

// Staff Login
func StaffLogin(c *fiber.Ctx) error {
	var loginReq struct {
		Username string `json:"username"`
		Password string `json:"password"`
	}

	if err := c.BodyParser(&loginReq); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	var user User
	query := "SELECT id, full_name, username, email, password, role, role_id, outlet_id, is_active, created_at FROM users WHERE username = ? LIMIT 1"
	err := DB.QueryRow(query, loginReq.Username).Scan(
		&user.ID, &user.FullName, &user.Username, &user.Email, &user.Password,
		&user.Role, &user.RoleID, &user.OutletID, &user.IsActive, &user.CreatedAt,
	)

	if err == sql.ErrNoRows {
		return ErrorResponse(c, "Invalid credentials", fiber.StatusUnauthorized)
	}
	if err != nil {
		return ErrorResponse(c, fmt.Sprintf("Database error: %v", err), fiber.StatusInternalServerError)
	}

	// Check password
	if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(loginReq.Password)); err != nil {
		return ErrorResponse(c, "Invalid credentials", fiber.StatusUnauthorized)
	}

	// Generate token
	token, err := GenerateToken(&user)
	if err != nil {
		return ErrorResponse(c, "Failed to generate token", fiber.StatusInternalServerError)
	}

	roleStr := ""
	if user.Role.Valid {
		roleStr = user.Role.String
	}

	return c.JSON(fiber.Map{
		"success": true,
		"token":   token,
		"user": fiber.Map{
			"id":        user.ID,
			"full_name": user.FullName,
			"username":  user.Username,
			"email":     user.Email,
			"role":      roleStr,
		},
	})
}

// Get Current User
func GetCurrentUser(c *fiber.Ctx) error {
	userID := c.Locals("user_id").(int)

	var user User
	query := "SELECT id, full_name, username, email, role, role_id, outlet_id, is_active, created_at FROM users WHERE id = ? LIMIT 1"
	err := DB.QueryRow(query, userID).Scan(
		&user.ID, &user.FullName, &user.Username, &user.Email,
		&user.Role, &user.RoleID, &user.OutletID, &user.IsActive, &user.CreatedAt,
	)

	if err == sql.ErrNoRows {
		return ErrorResponse(c, "User not found", fiber.StatusNotFound)
	}
	if err != nil {
		return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"user":    user,
	})
}

// Logout
func Logout(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{
		"success": true,
		"message": "Logged out successfully",
	})
}

// Get Products
func GetProducts(c *fiber.Ctx) error {
	rows, err := DB.Query(`
		SELECT id, name, sku, price, stock, category_id, brand_id, 
		       description, image_url, status, created_at, updated_at 
		FROM products 
		ORDER BY created_at DESC
	`)
	if err != nil {
		return ErrorResponse(c, fmt.Sprintf("Database error: %v", err), fiber.StatusInternalServerError)
	}
	defer rows.Close()

	var products []Product
	for rows.Next() {
		var p Product
		err := rows.Scan(&p.ID, &p.Name, &p.SKU, &p.Price, &p.Stock,
			&p.CategoryID, &p.BrandID, &p.Description, &p.ImageURL, &p.Status,
			&p.CreatedAt, &p.UpdatedAt)
		if err != nil {
			continue
		}
		products = append(products, p)
	}

	if products == nil {
		products = []Product{}
	}

	return c.JSON(fiber.Map{
		"success":  true,
		"products": products,
	})
}

// Get Single Product
func GetProduct(c *fiber.Ctx) error {
	id := c.Params("id")
	var p Product

	query := `SELECT id, name, sku, description, price, cost, stock, category_id, brand_id, 
	          image, is_active, created_at, updated_at FROM products WHERE id = ?`
	err := DB.QueryRow(query, id).Scan(
		&p.ID, &p.Name, &p.SKU, &p.Description, &p.Price, &p.Cost,
		&p.Stock, &p.CategoryID, &p.BrandID, &p.Image, &p.IsActive,
		&p.CreatedAt, &p.UpdatedAt,
	)

	if err == sql.ErrNoRows {
		return ErrorResponse(c, "Product not found", fiber.StatusNotFound)
	}
	if err != nil {
		return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"product": p,
	})
}

// Create Product
func CreateProduct(c *fiber.Ctx) error {
	var p Product
	if err := c.BodyParser(&p); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	result, err := DB.Exec(`
		INSERT INTO products (name, sku, description, price, cost, stock, category_id, brand_id, image, is_active)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`, p.Name, p.SKU, p.Description, p.Price, p.Cost, p.Stock, p.CategoryID, p.BrandID, p.Image, p.IsActive)

	if err != nil {
		return ErrorResponse(c, "Failed to create product", fiber.StatusInternalServerError)
	}

	id, _ := result.LastInsertId()
	p.ID = int(id)

	return c.Status(fiber.StatusCreated).JSON(fiber.Map{
		"success": true,
		"product": p,
	})
}

// Update Product
func UpdateProduct(c *fiber.Ctx) error {
	id := c.Params("id")
	var p Product
	if err := c.BodyParser(&p); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	_, err := DB.Exec(`
		UPDATE products SET name=?, sku=?, description=?, price=?, cost=?, stock=?, 
		category_id=?, brand_id=?, image=?, is_active=?, updated_at=NOW()
		WHERE id=?
	`, p.Name, p.SKU, p.Description, p.Price, p.Cost, p.Stock, p.CategoryID, p.BrandID, p.Image, p.IsActive, id)

	if err != nil {
		return ErrorResponse(c, "Failed to update product", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Product updated successfully",
	})
}

// Delete Product
func DeleteProduct(c *fiber.Ctx) error {
	id := c.Params("id")
	_, err := DB.Exec("DELETE FROM products WHERE id=?", id)
	if err != nil {
		return ErrorResponse(c, "Failed to delete product", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Product deleted successfully",
	})
}

// Get Categories
func GetCategories(c *fiber.Ctx) error {
	rows, err := DB.Query("SELECT id, name, created_at, updated_at FROM categories ORDER BY name")
	if err != nil {
		return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
	}
	defer rows.Close()

	var categories []Category
	for rows.Next() {
		var cat Category
		if err := rows.Scan(&cat.ID, &cat.Name, &cat.CreatedAt, &cat.UpdatedAt); err != nil {
			continue
		}
		categories = append(categories, cat)
	}

	if categories == nil {
		categories = []Category{}
	}

	return c.JSON(fiber.Map{
		"success":    true,
		"categories": categories,
	})
}

// Get Single Category
func GetCategory(c *fiber.Ctx) error {
	id := c.Params("id")
	var cat Category
	err := DB.QueryRow("SELECT id, name, created_at, updated_at FROM categories WHERE id=?", id).
		Scan(&cat.ID, &cat.Name, &cat.CreatedAt, &cat.UpdatedAt)

	if err == sql.ErrNoRows {
		return ErrorResponse(c, "Category not found", fiber.StatusNotFound)
	}
	if err != nil {
		return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success":  true,
		"category": cat,
	})
}

// Create Category
func CreateCategory(c *fiber.Ctx) error {
	var cat Category
	if err := c.BodyParser(&cat); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	result, err := DB.Exec("INSERT INTO categories (name) VALUES (?)", cat.Name)
	if err != nil {
		return ErrorResponse(c, "Failed to create category", fiber.StatusInternalServerError)
	}

	id, _ := result.LastInsertId()
	cat.ID = int(id)

	return c.Status(fiber.StatusCreated).JSON(fiber.Map{
		"success":  true,
		"category": cat,
	})
}

// Update Category
func UpdateCategory(c *fiber.Ctx) error {
	id := c.Params("id")
	var cat Category
	if err := c.BodyParser(&cat); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	_, err := DB.Exec("UPDATE categories SET name=?, updated_at=NOW() WHERE id=?", cat.Name, id)
	if err != nil {
		return ErrorResponse(c, "Failed to update category", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Category updated successfully",
	})
}

// Delete Category
func DeleteCategory(c *fiber.Ctx) error {
	id := c.Params("id")
	_, err := DB.Exec("DELETE FROM categories WHERE id=?", id)
	if err != nil {
		return ErrorResponse(c, "Failed to delete category", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Category deleted successfully",
	})
}

// Get Brands
func GetBrands(c *fiber.Ctx) error {
	rows, err := DB.Query("SELECT id, name, created_at, updated_at FROM brands ORDER BY name")
	if err != nil {
		return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
	}
	defer rows.Close()

	var brands []Brand
	for rows.Next() {
		var b Brand
		if err := rows.Scan(&b.ID, &b.Name, &b.CreatedAt, &b.UpdatedAt); err != nil {
			continue
		}
		brands = append(brands, b)
	}

	if brands == nil {
		brands = []Brand{}
	}

	return c.JSON(fiber.Map{
		"success": true,
		"brands":  brands,
	})
}

// Get Single Brand
func GetBrand(c *fiber.Ctx) error {
	id := c.Params("id")
	var b Brand
	err := DB.QueryRow("SELECT id, name, created_at, updated_at FROM brands WHERE id=?", id).
		Scan(&b.ID, &b.Name, &b.CreatedAt, &b.UpdatedAt)

	if err == sql.ErrNoRows {
		return ErrorResponse(c, "Brand not found", fiber.StatusNotFound)
	}
	if err != nil {
		return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"brand":   b,
	})
}

// Create Brand
func CreateBrand(c *fiber.Ctx) error {
	var b Brand
	if err := c.BodyParser(&b); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	result, err := DB.Exec("INSERT INTO brands (name) VALUES (?)", b.Name)
	if err != nil {
		return ErrorResponse(c, "Failed to create brand", fiber.StatusInternalServerError)
	}

	id, _ := result.LastInsertId()
	b.ID = int(id)

	return c.Status(fiber.StatusCreated).JSON(fiber.Map{
		"success": true,
		"brand":   b,
	})
}

// Update Brand
func UpdateBrand(c *fiber.Ctx) error {
	id := c.Params("id")
	var b Brand
	if err := c.BodyParser(&b); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	_, err := DB.Exec("UPDATE brands SET name=?, updated_at=NOW() WHERE id=?", b.Name, id)
	if err != nil {
		return ErrorResponse(c, "Failed to update brand", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Brand updated successfully",
	})
}

// Delete Brand
func DeleteBrand(c *fiber.Ctx) error {
	id := c.Params("id")
	_, err := DB.Exec("DELETE FROM brands WHERE id=?", id)
	if err != nil {
		return ErrorResponse(c, "Failed to delete brand", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Brand deleted successfully",
	})
}

// Get Orders
func GetOrders(c *fiber.Ctx) error {
	rows, err := DB.Query(`
		SELECT id, order_number, customer_id, table_id, total_amount, discount_amount,
		       tax_amount, final_amount, status, payment_method, payment_status, notes,
		       created_by, created_at, updated_at
		FROM orders ORDER BY created_at DESC
	`)
	if err != nil {
		return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
	}
	defer rows.Close()

	var orders []Order
	for rows.Next() {
		var o Order
		err := rows.Scan(&o.ID, &o.OrderNumber, &o.CustomerID, &o.TableID, &o.TotalAmount,
			&o.DiscountAmount, &o.TaxAmount, &o.FinalAmount, &o.Status, &o.PaymentMethod,
			&o.PaymentStatus, &o.Notes, &o.CreatedBy, &o.CreatedAt, &o.UpdatedAt)
		if err != nil {
			continue
		}
		orders = append(orders, o)
	}

	if orders == nil {
		orders = []Order{}
	}

	return c.JSON(fiber.Map{
		"success": true,
		"orders":  orders,
	})
}

// Get Single Order
func GetOrder(c *fiber.Ctx) error {
	id := c.Params("id")
	var o Order
	query := `SELECT id, order_number, customer_id, table_id, total_amount, discount_amount,
	          tax_amount, final_amount, status, payment_method, payment_status, notes,
	          created_by, created_at, updated_at FROM orders WHERE id=?`
	err := DB.QueryRow(query, id).Scan(
		&o.ID, &o.OrderNumber, &o.CustomerID, &o.TableID, &o.TotalAmount,
		&o.DiscountAmount, &o.TaxAmount, &o.FinalAmount, &o.Status, &o.PaymentMethod,
		&o.PaymentStatus, &o.Notes, &o.CreatedBy, &o.CreatedAt, &o.UpdatedAt,
	)

	if err == sql.ErrNoRows {
		return ErrorResponse(c, "Order not found", fiber.StatusNotFound)
	}
	if err != nil {
		return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"order":   o,
	})
}

// Create Order
func CreateOrder(c *fiber.Ctx) error {
	var o Order
	if err := c.BodyParser(&o); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	userID := c.Locals("user_id").(int)
	result, err := DB.Exec(`
		INSERT INTO orders (order_number, customer_id, table_id, total_amount, discount_amount,
		                    tax_amount, final_amount, status, payment_method, payment_status, 
		                    notes, created_by)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`, o.OrderNumber, o.CustomerID, o.TableID, o.TotalAmount, o.DiscountAmount,
		o.TaxAmount, o.FinalAmount, o.Status, o.PaymentMethod, o.PaymentStatus,
		o.Notes, userID)

	if err != nil {
		return ErrorResponse(c, "Failed to create order", fiber.StatusInternalServerError)
	}

	id, _ := result.LastInsertId()
	o.ID = int(id)

	return c.Status(fiber.StatusCreated).JSON(fiber.Map{
		"success": true,
		"order":   o,
	})
}

// Update Order
func UpdateOrder(c *fiber.Ctx) error {
	id := c.Params("id")
	var o Order
	if err := c.BodyParser(&o); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	_, err := DB.Exec(`
		UPDATE orders SET customer_id=?, table_id=?, total_amount=?, discount_amount=?,
		       tax_amount=?, final_amount=?, status=?, payment_method=?, payment_status=?,
		       notes=?, updated_at=NOW()
		WHERE id=?
	`, o.CustomerID, o.TableID, o.TotalAmount, o.DiscountAmount, o.TaxAmount,
		o.FinalAmount, o.Status, o.PaymentMethod, o.PaymentStatus, o.Notes, id)

	if err != nil {
		return ErrorResponse(c, "Failed to update order", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Order updated successfully",
	})
}

// Delete Order
func DeleteOrder(c *fiber.Ctx) error {
	id := c.Params("id")
	_, err := DB.Exec("DELETE FROM orders WHERE id=?", id)
	if err != nil {
		return ErrorResponse(c, "Failed to delete order", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Order deleted successfully",
	})
}

// Update Order Status
func UpdateOrderStatus(c *fiber.Ctx) error {
	id := c.Params("id")
	var req struct {
		Status string `json:"status"`
	}

	if err := c.BodyParser(&req); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	_, err := DB.Exec("UPDATE orders SET status=?, updated_at=NOW() WHERE id=?", req.Status, id)
	if err != nil {
		return ErrorResponse(c, "Failed to update order status", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Order status updated successfully",
	})
}

// Get Tables
func GetTables(c *fiber.Ctx) error {
	rows, err := DB.Query(`
		SELECT id, name, token, qr_code, status, outlet_id, created_at, updated_at
		FROM tables ORDER BY name
	`)
	if err != nil {
		return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
	}
	defer rows.Close()

	var tables []Table
	for rows.Next() {
		var t Table
		err := rows.Scan(&t.ID, &t.Name, &t.Token, &t.QRCode, &t.Status,
			&t.OutletID, &t.CreatedAt, &t.UpdatedAt)
		if err != nil {
			continue
		}
		tables = append(tables, t)
	}

	if tables == nil {
		tables = []Table{}
	}

	return c.JSON(fiber.Map{
		"success": true,
		"tables":  tables,
	})
}

// Get Single Table
func GetTable(c *fiber.Ctx) error {
	id := c.Params("id")
	var t Table
	query := `SELECT id, name, token, qr_code, status, outlet_id, created_at, updated_at 
	          FROM tables WHERE id=?`
	err := DB.QueryRow(query, id).Scan(
		&t.ID, &t.Name, &t.Token, &t.QRCode, &t.Status,
		&t.OutletID, &t.CreatedAt, &t.UpdatedAt,
	)

	if err == sql.ErrNoRows {
		return ErrorResponse(c, "Table not found", fiber.StatusNotFound)
	}
	if err != nil {
		return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"table":   t,
	})
}

// Get Table by Token
func GetTableByToken(c *fiber.Ctx) error {
	token := c.Params("token")
	var t Table
	query := `SELECT id, name, token, qr_code, status, outlet_id, created_at, updated_at 
	          FROM tables WHERE token=?`
	err := DB.QueryRow(query, token).Scan(
		&t.ID, &t.Name, &t.Token, &t.QRCode, &t.Status,
		&t.OutletID, &t.CreatedAt, &t.UpdatedAt,
	)

	if err == sql.ErrNoRows {
		return ErrorResponse(c, "Table not found", fiber.StatusNotFound)
	}
	if err != nil {
		return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"table":   t,
	})
}

// Create Table
func CreateTable(c *fiber.Ctx) error {
	var t Table
	if err := c.BodyParser(&t); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	result, err := DB.Exec(`
		INSERT INTO tables (name, token, qr_code, status, outlet_id)
		VALUES (?, ?, ?, ?, ?)
	`, t.Name, t.Token, t.QRCode, t.Status, t.OutletID)

	if err != nil {
		return ErrorResponse(c, "Failed to create table", fiber.StatusInternalServerError)
	}

	id, _ := result.LastInsertId()
	t.ID = int(id)

	return c.Status(fiber.StatusCreated).JSON(fiber.Map{
		"success": true,
		"table":   t,
	})
}

// Update Table
func UpdateTable(c *fiber.Ctx) error {
	id := c.Params("id")
	var t Table
	if err := c.BodyParser(&t); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	_, err := DB.Exec(`
		UPDATE tables SET name=?, token=?, qr_code=?, status=?, outlet_id=?, updated_at=NOW()
		WHERE id=?
	`, t.Name, t.Token, t.QRCode, t.Status, t.OutletID, id)

	if err != nil {
		return ErrorResponse(c, "Failed to update table", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Table updated successfully",
	})
}

// Delete Table
func DeleteTable(c *fiber.Ctx) error {
	id := c.Params("id")
	_, err := DB.Exec("DELETE FROM tables WHERE id=?", id)
	if err != nil {
		return ErrorResponse(c, "Failed to delete table", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Table deleted successfully",
	})
}

// Regenerate Table QR
func RegenerateTableQR(c *fiber.Ctx) error {
	id := c.Params("id")
	// Generate new token (simplified version)
	newToken := fmt.Sprintf("TBL-%d-%d", time.Now().Unix(), id)

	_, err := DB.Exec("UPDATE tables SET token=?, updated_at=NOW() WHERE id=?", newToken, id)
	if err != nil {
		return ErrorResponse(c, "Failed to regenerate QR", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"token":   newToken,
		"message": "QR code regenerated successfully",
	})
}

// Get Customers
func GetCustomers(c *fiber.Ctx) error {
	rows, err := DB.Query(`
		SELECT id, name, email, phone, address, points, created_at, updated_at
		FROM customers ORDER BY created_at DESC
	`)
	if err != nil {
		return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
	}
	defer rows.Close()

	var customers []Customer
	for rows.Next() {
		var cust Customer
		err := rows.Scan(&cust.ID, &cust.Name, &cust.Email, &cust.Phone,
			&cust.Address, &cust.Points, &cust.CreatedAt, &cust.UpdatedAt)
		if err != nil {
			continue
		}
		customers = append(customers, cust)
	}

	if customers == nil {
		customers = []Customer{}
	}

	return c.JSON(fiber.Map{
		"success":   true,
		"customers": customers,
	})
}

// Get Single Customer
func GetCustomer(c *fiber.Ctx) error {
	id := c.Params("id")
	var cust Customer
	query := `SELECT id, name, email, phone, address, points, created_at, updated_at 
	          FROM customers WHERE id=?`
	err := DB.QueryRow(query, id).Scan(
		&cust.ID, &cust.Name, &cust.Email, &cust.Phone,
		&cust.Address, &cust.Points, &cust.CreatedAt, &cust.UpdatedAt,
	)

	if err == sql.ErrNoRows {
		return ErrorResponse(c, "Customer not found", fiber.StatusNotFound)
	}
	if err != nil {
		return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success":  true,
		"customer": cust,
	})
}

// Create Customer
func CreateCustomer(c *fiber.Ctx) error {
	var cust Customer
	if err := c.BodyParser(&cust); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	result, err := DB.Exec(`
		INSERT INTO customers (name, email, phone, address, points)
		VALUES (?, ?, ?, ?, ?)
	`, cust.Name, cust.Email, cust.Phone, cust.Address, cust.Points)

	if err != nil {
		return ErrorResponse(c, "Failed to create customer", fiber.StatusInternalServerError)
	}

	id, _ := result.LastInsertId()
	cust.ID = int(id)

	return c.Status(fiber.StatusCreated).JSON(fiber.Map{
		"success":  true,
		"customer": cust,
	})
}

// Update Customer
func UpdateCustomer(c *fiber.Ctx) error {
	id := c.Params("id")
	var cust Customer
	if err := c.BodyParser(&cust); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	_, err := DB.Exec(`
		UPDATE customers SET name=?, email=?, phone=?, address=?, points=?, updated_at=NOW()
		WHERE id=?
	`, cust.Name, cust.Email, cust.Phone, cust.Address, cust.Points, id)

	if err != nil {
		return ErrorResponse(c, "Failed to update customer", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Customer updated successfully",
	})
}

// Delete Customer
func DeleteCustomer(c *fiber.Ctx) error {
	id := c.Params("id")
	_, err := DB.Exec("DELETE FROM customers WHERE id=?", id)
	if err != nil {
		return ErrorResponse(c, "Failed to delete customer", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Customer deleted successfully",
	})
}

// Get Coupons
func GetCoupons(c *fiber.Ctx) error {
	rows, err := DB.Query(`
		SELECT id, code, type, value, min_purchase, max_discount, start_date, end_date,
		       usage_limit, usage_count, is_active, created_at, updated_at
		FROM coupons ORDER BY created_at DESC
	`)
	if err != nil {
		return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
	}
	defer rows.Close()

	var coupons []Coupon
	for rows.Next() {
		var coup Coupon
		err := rows.Scan(&coup.ID, &coup.Code, &coup.Type, &coup.Value, &coup.MinPurchase,
			&coup.MaxDiscount, &coup.StartDate, &coup.EndDate, &coup.UsageLimit,
			&coup.UsageCount, &coup.IsActive, &coup.CreatedAt, &coup.UpdatedAt)
		if err != nil {
			continue
		}
		coupons = append(coupons, coup)
	}

	if coupons == nil {
		coupons = []Coupon{}
	}

	return c.JSON(fiber.Map{
		"success": true,
		"coupons": coupons,
	})
}

// Get Single Coupon
func GetCoupon(c *fiber.Ctx) error {
	id := c.Params("id")
	var coup Coupon
	query := `SELECT id, code, type, value, min_purchase, max_discount, start_date, end_date,
	          usage_limit, usage_count, is_active, created_at, updated_at
	          FROM coupons WHERE id=?`
	err := DB.QueryRow(query, id).Scan(
		&coup.ID, &coup.Code, &coup.Type, &coup.Value, &coup.MinPurchase,
		&coup.MaxDiscount, &coup.StartDate, &coup.EndDate, &coup.UsageLimit,
		&coup.UsageCount, &coup.IsActive, &coup.CreatedAt, &coup.UpdatedAt,
	)

	if err == sql.ErrNoRows {
		return ErrorResponse(c, "Coupon not found", fiber.StatusNotFound)
	}
	if err != nil {
		return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"coupon":  coup,
	})
}

// Create Coupon
func CreateCoupon(c *fiber.Ctx) error {
	var coup Coupon
	if err := c.BodyParser(&coup); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	result, err := DB.Exec(`
		INSERT INTO coupons (code, type, value, min_purchase, max_discount, start_date, 
		                     end_date, usage_limit, usage_count, is_active)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`, coup.Code, coup.Type, coup.Value, coup.MinPurchase, coup.MaxDiscount,
		coup.StartDate, coup.EndDate, coup.UsageLimit, coup.UsageCount, coup.IsActive)

	if err != nil {
		return ErrorResponse(c, "Failed to create coupon", fiber.StatusInternalServerError)
	}

	id, _ := result.LastInsertId()
	coup.ID = int(id)

	return c.Status(fiber.StatusCreated).JSON(fiber.Map{
		"success": true,
		"coupon":  coup,
	})
}

// Update Coupon
func UpdateCoupon(c *fiber.Ctx) error {
	id := c.Params("id")
	var coup Coupon
	if err := c.BodyParser(&coup); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	_, err := DB.Exec(`
		UPDATE coupons SET code=?, type=?, value=?, min_purchase=?, max_discount=?,
		       start_date=?, end_date=?, usage_limit=?, usage_count=?, is_active=?, 
		       updated_at=NOW()
		WHERE id=?
	`, coup.Code, coup.Type, coup.Value, coup.MinPurchase, coup.MaxDiscount,
		coup.StartDate, coup.EndDate, coup.UsageLimit, coup.UsageCount, coup.IsActive, id)

	if err != nil {
		return ErrorResponse(c, "Failed to update coupon", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Coupon updated successfully",
	})
}

// Delete Coupon
func DeleteCoupon(c *fiber.Ctx) error {
	id := c.Params("id")
	_, err := DB.Exec("DELETE FROM coupons WHERE id=?", id)
	if err != nil {
		return ErrorResponse(c, "Failed to delete coupon", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Coupon deleted successfully",
	})
}

// Get Outlets
func GetOutlets(c *fiber.Ctx) error {
	rows, err := DB.Query(`
		SELECT id, name, address, phone, is_active, created_at, updated_at
		FROM outlets ORDER BY name
	`)
	if err != nil {
		return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
	}
	defer rows.Close()

	var outlets []Outlet
	for rows.Next() {
		var out Outlet
		err := rows.Scan(&out.ID, &out.Name, &out.Address, &out.Phone,
			&out.IsActive, &out.CreatedAt, &out.UpdatedAt)
		if err != nil {
			continue
		}
		outlets = append(outlets, out)
	}

	if outlets == nil {
		outlets = []Outlet{}
	}

	return c.JSON(fiber.Map{
		"success": true,
		"outlets": outlets,
	})
}

// Get Single Outlet
func GetOutlet(c *fiber.Ctx) error {
	id := c.Params("id")
	var out Outlet
	query := `SELECT id, name, address, phone, is_active, created_at, updated_at 
	          FROM outlets WHERE id=?`
	err := DB.QueryRow(query, id).Scan(
		&out.ID, &out.Name, &out.Address, &out.Phone,
		&out.IsActive, &out.CreatedAt, &out.UpdatedAt,
	)

	if err == sql.ErrNoRows {
		return ErrorResponse(c, "Outlet not found", fiber.StatusNotFound)
	}
	if err != nil {
		return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"outlet":  out,
	})
}

// Create Outlet
func CreateOutlet(c *fiber.Ctx) error {
	var out Outlet
	if err := c.BodyParser(&out); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	result, err := DB.Exec(`
		INSERT INTO outlets (name, address, phone, is_active)
		VALUES (?, ?, ?, ?)
	`, out.Name, out.Address, out.Phone, out.IsActive)

	if err != nil {
		return ErrorResponse(c, "Failed to create outlet", fiber.StatusInternalServerError)
	}

	id, _ := result.LastInsertId()
	out.ID = int(id)

	return c.Status(fiber.StatusCreated).JSON(fiber.Map{
		"success": true,
		"outlet":  out,
	})
}

// Update Outlet
func UpdateOutlet(c *fiber.Ctx) error {
	id := c.Params("id")
	var out Outlet
	if err := c.BodyParser(&out); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	_, err := DB.Exec(`
		UPDATE outlets SET name=?, address=?, phone=?, is_active=?, updated_at=NOW()
		WHERE id=?
	`, out.Name, out.Address, out.Phone, out.IsActive, id)

	if err != nil {
		return ErrorResponse(c, "Failed to update outlet", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Outlet updated successfully",
	})
}

// Delete Outlet
func DeleteOutlet(c *fiber.Ctx) error {
	id := c.Params("id")
	_, err := DB.Exec("DELETE FROM outlets WHERE id=?", id)
	if err != nil {
		return ErrorResponse(c, "Failed to delete outlet", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Outlet deleted successfully",
	})
}

// Get Payment Methods
func GetPaymentMethods(c *fiber.Ctx) error {
	rows, err := DB.Query(`
		SELECT id, name, type, is_active, created_at, updated_at
		FROM payment_methods ORDER BY name
	`)
	if err != nil {
		return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
	}
	defer rows.Close()

	var methods []PaymentMethod
	for rows.Next() {
		var pm PaymentMethod
		err := rows.Scan(&pm.ID, &pm.Name, &pm.Type, &pm.IsActive,
			&pm.CreatedAt, &pm.UpdatedAt)
		if err != nil {
			continue
		}
		methods = append(methods, pm)
	}

	if methods == nil {
		methods = []PaymentMethod{}
	}

	return c.JSON(fiber.Map{
		"success":         true,
		"payment_methods": methods,
	})
}

// Get Single Payment Method
func GetPaymentMethod(c *fiber.Ctx) error {
	id := c.Params("id")
	var pm PaymentMethod
	query := `SELECT id, name, type, is_active, created_at, updated_at 
	          FROM payment_methods WHERE id=?`
	err := DB.QueryRow(query, id).Scan(
		&pm.ID, &pm.Name, &pm.Type, &pm.IsActive,
		&pm.CreatedAt, &pm.UpdatedAt,
	)

	if err == sql.ErrNoRows {
		return ErrorResponse(c, "Payment method not found", fiber.StatusNotFound)
	}
	if err != nil {
		return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success":        true,
		"payment_method": pm,
	})
}

// Create Payment Method
func CreatePaymentMethod(c *fiber.Ctx) error {
	var pm PaymentMethod
	if err := c.BodyParser(&pm); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	result, err := DB.Exec(`
		INSERT INTO payment_methods (name, type, is_active)
		VALUES (?, ?, ?)
	`, pm.Name, pm.Type, pm.IsActive)

	if err != nil {
		return ErrorResponse(c, "Failed to create payment method", fiber.StatusInternalServerError)
	}

	id, _ := result.LastInsertId()
	pm.ID = int(id)

	return c.Status(fiber.StatusCreated).JSON(fiber.Map{
		"success":        true,
		"payment_method": pm,
	})
}

// Update Payment Method
func UpdatePaymentMethod(c *fiber.Ctx) error {
	id := c.Params("id")
	var pm PaymentMethod
	if err := c.BodyParser(&pm); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	_, err := DB.Exec(`
		UPDATE payment_methods SET name=?, type=?, is_active=?, updated_at=NOW()
		WHERE id=?
	`, pm.Name, pm.Type, pm.IsActive, id)

	if err != nil {
		return ErrorResponse(c, "Failed to update payment method", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Payment method updated successfully",
	})
}

// Delete Payment Method
func DeletePaymentMethod(c *fiber.Ctx) error {
	id := c.Params("id")
	_, err := DB.Exec("DELETE FROM payment_methods WHERE id=?", id)
	if err != nil {
		return ErrorResponse(c, "Failed to delete payment method", fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Payment method deleted successfully",
	})
}

// Get Dashboard Stats
func GetDashboardStats(c *fiber.Ctx) error {
	var todayRevenue, monthRevenue, totalRevenue float64
	var todayOrders, monthOrders, totalOrders int

	// Today stats
	DB.QueryRow(`
		SELECT COALESCE(SUM(final_amount), 0), COUNT(*)
		FROM orders
		WHERE DATE(created_at) = CURDATE() AND payment_status = 'paid'
	`).Scan(&todayRevenue, &todayOrders)

	// Month stats
	DB.QueryRow(`
		SELECT COALESCE(SUM(final_amount), 0), COUNT(*)
		FROM orders
		WHERE YEAR(created_at) = YEAR(CURDATE()) 
		AND MONTH(created_at) = MONTH(CURDATE())
		AND payment_status = 'paid'
	`).Scan(&monthRevenue, &monthOrders)

	// Total stats
	DB.QueryRow(`
		SELECT COALESCE(SUM(final_amount), 0), COUNT(*)
		FROM orders
		WHERE payment_status = 'paid'
	`).Scan(&totalRevenue, &totalOrders)

	// Recent orders
	rows, _ := DB.Query(`
		SELECT id, order_number, customer_id, total_amount, final_amount, status, 
		       payment_status, created_at
		FROM orders
		ORDER BY created_at DESC
		LIMIT 10
	`)
	defer rows.Close()

	var recentOrders []fiber.Map
	for rows.Next() {
		var id int
		var orderNumber string
		var customerID sql.NullInt64
		var totalAmount, finalAmount float64
		var status, paymentStatus string
		var createdAt time.Time

		rows.Scan(&id, &orderNumber, &customerID, &totalAmount, &finalAmount,
			&status, &paymentStatus, &createdAt)

		recentOrders = append(recentOrders, fiber.Map{
			"id":             id,
			"order_number":   orderNumber,
			"customer_id":    customerID,
			"total_amount":   totalAmount,
			"final_amount":   finalAmount,
			"status":         status,
			"payment_status": paymentStatus,
			"created_at":     createdAt,
		})
	}

	if recentOrders == nil {
		recentOrders = []fiber.Map{}
	}

	return c.JSON(fiber.Map{
		"success": true,
		"stats": fiber.Map{
			"today": fiber.Map{
				"revenue": todayRevenue,
				"orders":  todayOrders,
			},
			"month": fiber.Map{
				"revenue": monthRevenue,
				"orders":  monthOrders,
			},
			"total": fiber.Map{
				"revenue": totalRevenue,
				"orders":  totalOrders,
			},
		},
		"recent_orders": recentOrders,
	})
}

// Get Analytics
func GetAnalytics(c *fiber.Ctx) error {
	var totalRevenue, avgOrderValue float64
	var totalOrders, newCustomers, returningCustomers, productsSold int

	// Revenue and orders
	DB.QueryRow(`
		SELECT COALESCE(SUM(final_amount), 0), COUNT(*)
		FROM orders
		WHERE payment_status = 'paid'
	`).Scan(&totalRevenue, &totalOrders)

	// Average order value
	if totalOrders > 0 {
		avgOrderValue = totalRevenue / float64(totalOrders)
	}

	// New customers (created in last 30 days)
	DB.QueryRow(`
		SELECT COUNT(*)
		FROM customers
		WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
	`).Scan(&newCustomers)

	// Returning customers (customers with more than 1 order)
	DB.QueryRow(`
		SELECT COUNT(DISTINCT customer_id)
		FROM orders
		WHERE customer_id IS NOT NULL
		GROUP BY customer_id
		HAVING COUNT(*) > 1
	`).Scan(&returningCustomers)

	// Products sold (from order_items if table exists)
	DB.QueryRow(`
		SELECT COALESCE(SUM(quantity), 0)
		FROM order_items
	`).Scan(&productsSold)

	return c.JSON(fiber.Map{
		"success": true,
		"analytics": fiber.Map{
			"revenue":              totalRevenue,
			"orders":               totalOrders,
			"average_order_value":  avgOrderValue,
			"new_customers":        newCustomers,
			"returning_customers":  returningCustomers,
			"products_sold":        productsSold,
		},
	})
}
