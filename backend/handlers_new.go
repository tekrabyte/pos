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

	query := `SELECT id, name, sku, price, stock, category_id, brand_id, 
	          description, image_url, status, created_at, updated_at FROM products WHERE id = ?`
	err := DB.QueryRow(query, id).Scan(
		&p.ID, &p.Name, &p.SKU, &p.Price, &p.Stock,
		&p.CategoryID, &p.BrandID, &p.Description, &p.ImageURL, &p.Status,
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

// Create Product - simplified
func CreateProduct(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{
		"success": true,
		"message": "Create product endpoint - to be implemented",
	})
}

// Update Product - simplified
func UpdateProduct(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{
		"success": true,
		"message": "Update product endpoint - to be implemented",
	})
}

// Delete Product - simplified
func DeleteProduct(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{
		"success": true,
		"message": "Delete product endpoint - to be implemented",
	})
}

// Get Categories
func GetCategories(c *fiber.Ctx) error {
	rows, err := DB.Query("SELECT id, name, description, parent_id, created_at FROM categories ORDER BY name")
	if err != nil {
		return ErrorResponse(c, fmt.Sprintf("Database error: %v", err), fiber.StatusInternalServerError)
	}
	defer rows.Close()

	var categories []Category
	for rows.Next() {
		var cat Category
		if err := rows.Scan(&cat.ID, &cat.Name, &cat.Description, &cat.ParentID, &cat.CreatedAt); err != nil {
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
	err := DB.QueryRow("SELECT id, name, description, parent_id, created_at FROM categories WHERE id=?", id).
		Scan(&cat.ID, &cat.Name, &cat.Description, &cat.ParentID, &cat.CreatedAt)

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
	return c.JSON(fiber.Map{
		"success": true,
		"message": "Create category endpoint - to be implemented",
	})
}

// Update Category
func UpdateCategory(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{
		"success": true,
		"message": "Update category endpoint - to be implemented",
	})
}

// Delete Category
func DeleteCategory(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{
		"success": true,
		"message": "Delete category endpoint - to be implemented",
	})
}

// Get Brands
func GetBrands(c *fiber.Ctx) error {
	rows, err := DB.Query("SELECT id, name, description, logo_url, created_at FROM brands ORDER BY name")
	if err != nil {
		return ErrorResponse(c, fmt.Sprintf("Database error: %v", err), fiber.StatusInternalServerError)
	}
	defer rows.Close()

	var brands []Brand
	for rows.Next() {
		var b Brand
		if err := rows.Scan(&b.ID, &b.Name, &b.Description, &b.LogoURL, &b.CreatedAt); err != nil {
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
	err := DB.QueryRow("SELECT id, name, description, logo_url, created_at FROM brands WHERE id=?", id).
		Scan(&b.ID, &b.Name, &b.Description, &b.LogoURL, &b.CreatedAt)

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

// Simplified CRUD operations for other entities
func CreateBrand(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Create brand - to be implemented"})
}

func UpdateBrand(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Update brand - to be implemented"})
}

func DeleteBrand(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Delete brand - to be implemented"})
}

// Get Orders
func GetOrders(c *fiber.Ctx) error {
	rows, err := DB.Query(`
		SELECT id, order_number, customer_id, table_id, order_type, customer_name,
		       customer_phone, outlet_id, user_id, total_amount, payment_method,
		       payment_proof, payment_verified, status, created_at, coupon_id,
		       coupon_code, discount_amount, original_amount, estimated_time, completed_at
		FROM orders ORDER BY created_at DESC
	`)
	if err != nil {
		return ErrorResponse(c, fmt.Sprintf("Database error: %v", err), fiber.StatusInternalServerError)
	}
	defer rows.Close()

	var orders []Order
	for rows.Next() {
		var o Order
		err := rows.Scan(&o.ID, &o.OrderNumber, &o.CustomerID, &o.TableID, &o.OrderType,
			&o.CustomerName, &o.CustomerPhone, &o.OutletID, &o.UserID, &o.TotalAmount,
			&o.PaymentMethod, &o.PaymentProof, &o.PaymentVerified, &o.Status, &o.CreatedAt,
			&o.CouponID, &o.CouponCode, &o.DiscountAmount, &o.OriginalAmount,
			&o.EstimatedTime, &o.CompletedAt)
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

// Simplified CRUD for Orders
func GetOrder(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Get order - to be implemented"})
}

func CreateOrder(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Create order - to be implemented"})
}

func UpdateOrder(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Update order - to be implemented"})
}

func DeleteOrder(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Delete order - to be implemented"})
}

func UpdateOrderStatus(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Update order status - to be implemented"})
}

// Simplified handlers for other entities
func GetTables(c *fiber.Ctx) error {
	rows, err := DB.Query("SELECT id, name, token, qr_code, status, outlet_id, created_at, updated_at FROM tables ORDER BY name")
	if err != nil {
		return c.JSON(fiber.Map{"success": true, "tables": []interface{}{}})
	}
	defer rows.Close()
	
	var tables []Table
	for rows.Next() {
		var t Table
		rows.Scan(&t.ID, &t.Name, &t.Token, &t.QRCode, &t.Status, &t.OutletID, &t.CreatedAt, &t.UpdatedAt)
		tables = append(tables, t)
	}
	
	if tables == nil {
		tables = []Table{}
	}
	
	return c.JSON(fiber.Map{"success": true, "tables": tables})
}

func GetTable(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Get table - to be implemented"})
}

func GetTableByToken(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Get table by token - to be implemented"})
}

func CreateTable(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Create table - to be implemented"})
}

func UpdateTable(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Update table - to be implemented"})
}

func DeleteTable(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Delete table - to be implemented"})
}

func RegenerateTableQR(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Regenerate QR - to be implemented"})
}

func GetCustomers(c *fiber.Ctx) error {
	rows, err := DB.Query("SELECT id, name, email, phone, address, points, created_at FROM customers ORDER BY created_at DESC LIMIT 100")
	if err != nil {
		return c.JSON(fiber.Map{"success": true, "customers": []interface{}{}})
	}
	defer rows.Close()
	
	var customers []Customer
	for rows.Next() {
		var cust Customer
		rows.Scan(&cust.ID, &cust.Name, &cust.Email, &cust.Phone, &cust.Address, &cust.Points, &cust.CreatedAt)
		customers = append(customers, cust)
	}
	
	if customers == nil {
		customers = []Customer{}
	}
	
	return c.JSON(fiber.Map{"success": true, "customers": customers})
}

func GetCustomer(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Get customer - to be implemented"})
}

func CreateCustomer(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Create customer - to be implemented"})
}

func UpdateCustomer(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Update customer - to be implemented"})
}

func DeleteCustomer(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Delete customer - to be implemented"})
}

func GetCoupons(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "coupons": []interface{}{}})
}

func GetCoupon(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Get coupon - to be implemented"})
}

func CreateCoupon(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Create coupon - to be implemented"})
}

func UpdateCoupon(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Update coupon - to be implemented"})
}

func DeleteCoupon(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Delete coupon - to be implemented"})
}

func GetOutlets(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "outlets": []interface{}{}})
}

func GetOutlet(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Get outlet - to be implemented"})
}

func CreateOutlet(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Create outlet - to be implemented"})
}

func UpdateOutlet(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Update outlet - to be implemented"})
}

func DeleteOutlet(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Delete outlet - to be implemented"})
}

func GetPaymentMethods(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "payment_methods": []interface{}{}})
}

func GetPaymentMethod(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Get payment method - to be implemented"})
}

func CreatePaymentMethod(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Create payment method - to be implemented"})
}

func UpdatePaymentMethod(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Update payment method - to be implemented"})
}

func DeletePaymentMethod(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{"success": true, "message": "Delete payment method - to be implemented"})
}

// Get Dashboard Stats
func GetDashboardStats(c *fiber.Ctx) error {
	var todayRevenue, monthRevenue, totalRevenue float64
	var todayOrders, monthOrders, totalOrders int

	// Today stats
	DB.QueryRow(`
		SELECT COALESCE(SUM(total_amount), 0), COUNT(*)
		FROM orders
		WHERE DATE(created_at) = CURDATE() AND status = 'completed'
	`).Scan(&todayRevenue, &todayOrders)

	// Month stats
	DB.QueryRow(`
		SELECT COALESCE(SUM(total_amount), 0), COUNT(*)
		FROM orders
		WHERE YEAR(created_at) = YEAR(CURDATE()) 
		AND MONTH(created_at) = MONTH(CURDATE())
		AND status = 'completed'
	`).Scan(&monthRevenue, &monthOrders)

	// Total stats
	DB.QueryRow(`
		SELECT COALESCE(SUM(total_amount), 0), COUNT(*)
		FROM orders
		WHERE status = 'completed'
	`).Scan(&totalRevenue, &totalOrders)

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
		"recent_orders": []interface{}{},
	})
}

// Get Analytics
func GetAnalytics(c *fiber.Ctx) error {
	var totalRevenue, avgOrderValue float64
	var totalOrders int

	// Revenue and orders
	DB.QueryRow(`
		SELECT COALESCE(SUM(total_amount), 0), COUNT(*)
		FROM orders
		WHERE status = 'completed'
	`).Scan(&totalRevenue, &totalOrders)

	// Average order value
	if totalOrders > 0 {
		avgOrderValue = totalRevenue / float64(totalOrders)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"analytics": fiber.Map{
			"revenue":             totalRevenue,
			"orders":              totalOrders,
			"average_order_value": avgOrderValue,
			"new_customers":       0,
			"returning_customers": 0,
			"products_sold":       0,
		},
	})
}
