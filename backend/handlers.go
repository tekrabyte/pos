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

// Helper to convert sql.Null types to plain values
func getNullString(ns sql.NullString) string {
        if ns.Valid {
                return ns.String
        }
        return ""
}

func getNullInt(ni sql.NullInt64) *int {
        if ni.Valid {
                val := int(ni.Int64)
                return &val
        }
        return nil
}

func getNullFloat(nf sql.NullFloat64) *float64 {
        if nf.Valid {
                return &nf.Float64
        }
        return nil
}

func getNullTime(nt sql.NullTime) *string {
        if nt.Valid {
                formatted := nt.Time.Format(time.RFC3339)
                return &formatted
        }
        return nil
}

func getNullBool(nb sql.NullBool) *bool {
        if nb.Valid {
                return &nb.Bool
        }
        return nil
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
        startTime := time.Now()
        
        var loginReq struct {
                Username string `json:"username"`
                Password string `json:"password"`
        }

        if err := c.BodyParser(&loginReq); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        var user User
        // Optimized query - only fetch necessary fields for login
        query := "SELECT id, full_name, username, email, password, role, role_id, outlet_id, is_active, created_at FROM users WHERE username = ? AND is_active = 1 LIMIT 1"
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

        // Log performance for monitoring
        duration := time.Since(startTime).Milliseconds()
        if duration > 500 {
                fmt.Printf("⚠️ Slow login: %dms for user %s\n", duration, loginReq.Username)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "token":   token,
                "user": fiber.Map{
                        "id":        user.ID,
                        "full_name": getNullString(user.FullName),
                        "username":  user.Username,
                        "email":     getNullString(user.Email),
                        "role":      getNullString(user.Role),
                        "role_id":   getNullInt(user.RoleID),
                        "outlet_id": getNullInt(user.OutletID),
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
                "user": fiber.Map{
                        "id":         user.ID,
                        "full_name":  getNullString(user.FullName),
                        "username":   user.Username,
                        "email":      getNullString(user.Email),
                        "role":       getNullString(user.Role),
                        "role_id":    getNullInt(user.RoleID),
                        "outlet_id":  getNullInt(user.OutletID),
                        "is_active":  getNullBool(user.IsActive),
                        "created_at": getNullTime(user.CreatedAt),
                },
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

        var products []map[string]interface{}
        for rows.Next() {
                var p Product
                err := rows.Scan(&p.ID, &p.Name, &p.SKU, &p.Price, &p.Stock,
                        &p.CategoryID, &p.BrandID, &p.Description, &p.ImageURL, &p.Status,
                        &p.CreatedAt, &p.UpdatedAt)
                if err != nil {
                        continue
                }
                
                products = append(products, map[string]interface{}{
                        "id":          p.ID,
                        "name":        p.Name,
                        "sku":         getNullString(p.SKU),
                        "price":       p.Price,
                        "stock":       p.Stock,
                        "category_id": getNullInt(p.CategoryID),
                        "brand_id":    getNullInt(p.BrandID),
                        "description": getNullString(p.Description),
                        "image_url":   getNullString(p.ImageURL),
                        "status":      getNullString(p.Status),
                        "created_at":  getNullTime(p.CreatedAt),
                        "updated_at":  getNullTime(p.UpdatedAt),
                })
        }

        if products == nil {
                products = []map[string]interface{}{}
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

// Create Product
func CreateProduct(c *fiber.Ctx) error {
        var req struct {
                Name        string  `json:"name"`
                SKU         string  `json:"sku"`
                Price       float64 `json:"price"`
                Stock       int     `json:"stock"`
                CategoryID  *int    `json:"category_id"`
                BrandID     *int    `json:"brand_id"`
                Description string  `json:"description"`
                ImageURL    string  `json:"image_url"`
                Status      string  `json:"status"`
        }

        if err := c.BodyParser(&req); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        if req.Name == "" {
                return ErrorResponse(c, "Product name is required", fiber.StatusBadRequest)
        }

        result, err := DB.Exec(`
                INSERT INTO products (name, sku, price, stock, category_id, brand_id, description, image_url, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())
        `, req.Name, req.SKU, req.Price, req.Stock, req.CategoryID, req.BrandID, req.Description, req.ImageURL, req.Status)

        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to create product: %v", err), fiber.StatusInternalServerError)
        }

        id, _ := result.LastInsertId()

        return c.Status(fiber.StatusCreated).JSON(fiber.Map{
                "success": true,
                "message": "Product created successfully",
                "product": fiber.Map{
                        "id":          id,
                        "name":        req.Name,
                        "sku":         req.SKU,
                        "price":       req.Price,
                        "stock":       req.Stock,
                        "category_id": req.CategoryID,
                        "brand_id":    req.BrandID,
                        "description": req.Description,
                        "image_url":   req.ImageURL,
                        "status":      req.Status,
                },
        })
}

// Update Product
func UpdateProduct(c *fiber.Ctx) error {
        id := c.Params("id")
        
        var req struct {
                Name        string  `json:"name"`
                SKU         string  `json:"sku"`
                Price       float64 `json:"price"`
                Stock       int     `json:"stock"`
                CategoryID  *int    `json:"category_id"`
                BrandID     *int    `json:"brand_id"`
                Description string  `json:"description"`
                ImageURL    string  `json:"image_url"`
                Status      string  `json:"status"`
        }

        if err := c.BodyParser(&req); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        _, err := DB.Exec(`
                UPDATE products 
                SET name = ?, sku = ?, price = ?, stock = ?, category_id = ?, brand_id = ?, 
                    description = ?, image_url = ?, status = ?, updated_at = NOW()
                WHERE id = ?
        `, req.Name, req.SKU, req.Price, req.Stock, req.CategoryID, req.BrandID, 
           req.Description, req.ImageURL, req.Status, id)

        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to update product: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Product updated successfully",
        })
}

// Delete Product
func DeleteProduct(c *fiber.Ctx) error {
        id := c.Params("id")

        _, err := DB.Exec("DELETE FROM products WHERE id = ?", id)
        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to delete product: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Product deleted successfully",
        })
}

// Get Categories
func GetCategories(c *fiber.Ctx) error {
        rows, err := DB.Query("SELECT id, name, description, parent_id, created_at FROM categories ORDER BY name")
        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Database error: %v", err), fiber.StatusInternalServerError)
        }
        defer rows.Close()

        var categories []map[string]interface{}
        for rows.Next() {
                var cat Category
                if err := rows.Scan(&cat.ID, &cat.Name, &cat.Description, &cat.ParentID, &cat.CreatedAt); err != nil {
                        continue
                }
                categories = append(categories, map[string]interface{}{
                        "id":          cat.ID,
                        "name":        cat.Name,
                        "description": getNullString(cat.Description),
                        "parent_id":   getNullInt(cat.ParentID),
                        "created_at":  getNullTime(cat.CreatedAt),
                })
        }

        if categories == nil {
                categories = []map[string]interface{}{}
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
        var req struct {
                Name        string `json:"name"`
                Description string `json:"description"`
                ParentID    *int   `json:"parent_id"`
        }

        if err := c.BodyParser(&req); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        if req.Name == "" {
                return ErrorResponse(c, "Category name is required", fiber.StatusBadRequest)
        }

        result, err := DB.Exec(`
                INSERT INTO categories (name, description, parent_id, created_at)
                VALUES (?, ?, ?, NOW())
        `, req.Name, req.Description, req.ParentID)

        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to create category: %v", err), fiber.StatusInternalServerError)
        }

        id, _ := result.LastInsertId()

        return c.Status(fiber.StatusCreated).JSON(fiber.Map{
                "success": true,
                "message": "Category created successfully",
                "category": fiber.Map{
                        "id":          id,
                        "name":        req.Name,
                        "description": req.Description,
                        "parent_id":   req.ParentID,
                },
        })
}

// Update Category
func UpdateCategory(c *fiber.Ctx) error {
        id := c.Params("id")
        
        var req struct {
                Name        string `json:"name"`
                Description string `json:"description"`
                ParentID    *int   `json:"parent_id"`
        }

        if err := c.BodyParser(&req); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        _, err := DB.Exec(`
                UPDATE categories 
                SET name = ?, description = ?, parent_id = ?
                WHERE id = ?
        `, req.Name, req.Description, req.ParentID, id)

        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to update category: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Category updated successfully",
        })
}

// Delete Category
func DeleteCategory(c *fiber.Ctx) error {
        id := c.Params("id")

        _, err := DB.Exec("DELETE FROM categories WHERE id = ?", id)
        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to delete category: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Category deleted successfully",
        })
}

// Get Brands
func GetBrands(c *fiber.Ctx) error {
        rows, err := DB.Query("SELECT id, name, description, logo_url, created_at FROM brands ORDER BY name")
        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Database error: %v", err), fiber.StatusInternalServerError)
        }
        defer rows.Close()

        var brands []map[string]interface{}
        for rows.Next() {
                var b Brand
                if err := rows.Scan(&b.ID, &b.Name, &b.Description, &b.LogoURL, &b.CreatedAt); err != nil {
                        continue
                }
                brands = append(brands, map[string]interface{}{
                        "id":          b.ID,
                        "name":        b.Name,
                        "description": getNullString(b.Description),
                        "logo_url":    getNullString(b.LogoURL),
                        "created_at":  getNullTime(b.CreatedAt),
                })
        }

        if brands == nil {
                brands = []map[string]interface{}{}
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
        var req struct {
                Name        string `json:"name"`
                Description string `json:"description"`
                LogoURL     string `json:"logo_url"`
        }

        if err := c.BodyParser(&req); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        if req.Name == "" {
                return ErrorResponse(c, "Brand name is required", fiber.StatusBadRequest)
        }

        result, err := DB.Exec(`
                INSERT INTO brands (name, description, logo_url, created_at)
                VALUES (?, ?, ?, NOW())
        `, req.Name, req.Description, req.LogoURL)

        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to create brand: %v", err), fiber.StatusInternalServerError)
        }

        id, _ := result.LastInsertId()

        return c.Status(fiber.StatusCreated).JSON(fiber.Map{
                "success": true,
                "message": "Brand created successfully",
                "brand": fiber.Map{
                        "id":          id,
                        "name":        req.Name,
                        "description": req.Description,
                        "logo_url":    req.LogoURL,
                },
        })
}

func UpdateBrand(c *fiber.Ctx) error {
        id := c.Params("id")
        
        var req struct {
                Name        string `json:"name"`
                Description string `json:"description"`
                LogoURL     string `json:"logo_url"`
        }

        if err := c.BodyParser(&req); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        _, err := DB.Exec(`
                UPDATE brands 
                SET name = ?, description = ?, logo_url = ?
                WHERE id = ?
        `, req.Name, req.Description, req.LogoURL, id)

        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to update brand: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Brand updated successfully",
        })
}

func DeleteBrand(c *fiber.Ctx) error {
        id := c.Params("id")

        _, err := DB.Exec("DELETE FROM brands WHERE id = ?", id)
        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to delete brand: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Brand deleted successfully",
        })
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

        var orders []map[string]interface{}
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
                
                orders = append(orders, map[string]interface{}{
                        "id":               o.ID,
                        "order_number":     o.OrderNumber,
                        "customer_id":      getNullInt(o.CustomerID),
                        "table_id":         getNullInt(o.TableID),
                        "order_type":       getNullString(o.OrderType),
                        "customer_name":    getNullString(o.CustomerName),
                        "customer_phone":   getNullString(o.CustomerPhone),
                        "outlet_id":        getNullInt(o.OutletID),
                        "user_id":          getNullInt(o.UserID),
                        "total_amount":     o.TotalAmount,
                        "payment_method":   getNullString(o.PaymentMethod),
                        "payment_proof":    getNullString(o.PaymentProof),
                        "payment_verified": o.PaymentVerified,
                        "status":           getNullString(o.Status),
                        "created_at":       getNullTime(o.CreatedAt),
                        "coupon_id":        getNullInt(o.CouponID),
                        "coupon_code":      getNullString(o.CouponCode),
                        "discount_amount":  getNullFloat(o.DiscountAmount),
                        "original_amount":  getNullFloat(o.OriginalAmount),
                        "estimated_time":   getNullInt(o.EstimatedTime),
                        "completed_at":     getNullTime(o.CompletedAt),
                })
        }

        if orders == nil {
                orders = []map[string]interface{}{}
        }

        return c.JSON(fiber.Map{
                "success": true,
                "orders":  orders,
        })
}

// Simplified CRUD for Orders
func GetOrder(c *fiber.Ctx) error {
        id := c.Params("id")
        var order Order

        query := `SELECT id, order_number, customer_id, table_id, order_type, customer_name, 
                  customer_phone, outlet_id, user_id, total_amount, payment_method, payment_proof,
                  payment_verified, status, created_at, coupon_id, coupon_code, discount_amount,
                  original_amount, estimated_time, completed_at
                  FROM orders WHERE id = ?`
        
        err := DB.QueryRow(query, id).Scan(
                &order.ID, &order.OrderNumber, &order.CustomerID, &order.TableID, &order.OrderType,
                &order.CustomerName, &order.CustomerPhone, &order.OutletID, &order.UserID,
                &order.TotalAmount, &order.PaymentMethod, &order.PaymentProof, &order.PaymentVerified,
                &order.Status, &order.CreatedAt, &order.CouponID, &order.CouponCode,
                &order.DiscountAmount, &order.OriginalAmount, &order.EstimatedTime, &order.CompletedAt,
        )

        if err == sql.ErrNoRows {
                return ErrorResponse(c, "Order not found", fiber.StatusNotFound)
        }
        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Database error: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{"success": true, "order": order})
}

func CreateOrder(c *fiber.Ctx) error {
        var req struct {
                OrderNumber      string  `json:"order_number"`
                CustomerID       *int    `json:"customer_id"`
                TableID          *int    `json:"table_id"`
                OrderType        string  `json:"order_type"`
                CustomerName     string  `json:"customer_name"`
                CustomerPhone    string  `json:"customer_phone"`
                OutletID         *int    `json:"outlet_id"`
                UserID           *int    `json:"user_id"`
                TotalAmount      float64 `json:"total_amount"`
                PaymentMethod    string  `json:"payment_method"`
                PaymentProof     string  `json:"payment_proof"`
                PaymentVerified  bool    `json:"payment_verified"`
                Status           string  `json:"status"`
                CouponID         *int    `json:"coupon_id"`
                CouponCode       string  `json:"coupon_code"`
                DiscountAmount   float64 `json:"discount_amount"`
                OriginalAmount   float64 `json:"original_amount"`
                EstimatedTime    int     `json:"estimated_time"`
        }

        if err := c.BodyParser(&req); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        result, err := DB.Exec(`
                INSERT INTO orders (order_number, customer_id, table_id, order_type, customer_name, 
                                   customer_phone, outlet_id, user_id, total_amount, payment_method, 
                                   payment_proof, payment_verified, status, created_at, coupon_id, 
                                   coupon_code, discount_amount, original_amount, estimated_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), ?, ?, ?, ?, ?)
        `, req.OrderNumber, req.CustomerID, req.TableID, req.OrderType, req.CustomerName,
                req.CustomerPhone, req.OutletID, req.UserID, req.TotalAmount, req.PaymentMethod,
                req.PaymentProof, req.PaymentVerified, req.Status, req.CouponID, req.CouponCode,
                req.DiscountAmount, req.OriginalAmount, req.EstimatedTime)

        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to create order: %v", err), fiber.StatusInternalServerError)
        }

        id, _ := result.LastInsertId()

        return c.Status(fiber.StatusCreated).JSON(fiber.Map{
                "success": true,
                "message": "Order created successfully",
                "order_id": id,
        })
}

func UpdateOrder(c *fiber.Ctx) error {
        id := c.Params("id")
        
        var req struct {
                CustomerID      *int    `json:"customer_id"`
                TableID         *int    `json:"table_id"`
                OrderType       string  `json:"order_type"`
                CustomerName    string  `json:"customer_name"`
                CustomerPhone   string  `json:"customer_phone"`
                TotalAmount     float64 `json:"total_amount"`
                PaymentMethod   string  `json:"payment_method"`
                PaymentProof    string  `json:"payment_proof"`
                PaymentVerified bool    `json:"payment_verified"`
                Status          string  `json:"status"`
        }

        if err := c.BodyParser(&req); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        _, err := DB.Exec(`
                UPDATE orders 
                SET customer_id = ?, table_id = ?, order_type = ?, customer_name = ?, 
                    customer_phone = ?, total_amount = ?, payment_method = ?, 
                    payment_proof = ?, payment_verified = ?, status = ?
                WHERE id = ?
        `, req.CustomerID, req.TableID, req.OrderType, req.CustomerName, req.CustomerPhone,
                req.TotalAmount, req.PaymentMethod, req.PaymentProof, req.PaymentVerified,
                req.Status, id)

        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to update order: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Order updated successfully",
        })
}

func DeleteOrder(c *fiber.Ctx) error {
        id := c.Params("id")

        _, err := DB.Exec("DELETE FROM orders WHERE id = ?", id)
        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to delete order: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Order deleted successfully",
        })
}

func UpdateOrderStatus(c *fiber.Ctx) error {
        id := c.Params("id")
        
        var req struct {
                Status string `json:"status"`
        }

        if err := c.BodyParser(&req); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        _, err := DB.Exec("UPDATE orders SET status = ? WHERE id = ?", req.Status, id)
        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to update order status: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Order status updated successfully",
        })
}

// Simplified handlers for other entities
func GetTables(c *fiber.Ctx) error {
        rows, err := DB.Query("SELECT id, table_number, token, qr_code, status, outlet_id, created_at, updated_at FROM tables ORDER BY table_number")
        if err != nil {
                return c.JSON(fiber.Map{"success": true, "tables": []interface{}{}})
        }
        defer rows.Close()
        
        var tables []map[string]interface{}
        for rows.Next() {
                var id int
                var tableNumber string
                var token string
                var qrCode, status sql.NullString
                var outletID sql.NullInt64
                var createdAt, updatedAt sql.NullTime
                rows.Scan(&id, &tableNumber, &token, &qrCode, &status, &outletID, &createdAt, &updatedAt)
                tables = append(tables, map[string]interface{}{
                        "id":           id,
                        "table_number": tableNumber,
                        "token":        token,
                        "qr_code":      qrCode,
                        "status":       status,
                        "outlet_id":    outletID,
                        "created_at":   createdAt,
                        "updated_at":   updatedAt,
                })
        }
        
        if tables == nil {
                tables = []map[string]interface{}{}
        }
        
        return c.JSON(fiber.Map{"success": true, "tables": tables})
}

func GetTable(c *fiber.Ctx) error {
        id := c.Params("id")
        
        var tid int
        var tableNumber, token string
        var qrCode, status sql.NullString
        var outletID sql.NullInt64
        var createdAt, updatedAt sql.NullTime

        query := "SELECT id, table_number, token, qr_code, status, outlet_id, created_at, updated_at FROM tables WHERE id = ?"
        err := DB.QueryRow(query, id).Scan(&tid, &tableNumber, &token, &qrCode, &status, &outletID, &createdAt, &updatedAt)

        if err == sql.ErrNoRows {
                return ErrorResponse(c, "Table not found", fiber.StatusNotFound)
        }
        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Database error: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{"success": true, "table": map[string]interface{}{
                "id":           tid,
                "table_number": tableNumber,
                "token":        token,
                "qr_code":      qrCode,
                "status":       status,
                "outlet_id":    outletID,
                "created_at":   createdAt,
                "updated_at":   updatedAt,
        }})
}

func GetTableByToken(c *fiber.Ctx) error {
        token := c.Params("token")
        
        var tid int
        var tableNumber, ttoken string
        var qrCode, status sql.NullString
        var outletID sql.NullInt64
        var createdAt, updatedAt sql.NullTime

        query := "SELECT id, table_number, token, qr_code, status, outlet_id, created_at, updated_at FROM tables WHERE token = ?"
        err := DB.QueryRow(query, token).Scan(&tid, &tableNumber, &ttoken, &qrCode, &status, &outletID, &createdAt, &updatedAt)

        if err == sql.ErrNoRows {
                return ErrorResponse(c, "Table not found", fiber.StatusNotFound)
        }
        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Database error: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{"success": true, "table": map[string]interface{}{
                "id":           tid,
                "table_number": tableNumber,
                "token":        ttoken,
                "qr_code":      qrCode,
                "status":       status,
                "outlet_id":    outletID,
                "created_at":   createdAt,
                "updated_at":   updatedAt,
        }})
}

func CreateTable(c *fiber.Ctx) error {
        var req struct {
                TableNumber string `json:"table_number"`
                Status      string `json:"status"`
                OutletID    *int   `json:"outlet_id"`
        }

        if err := c.BodyParser(&req); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        if req.TableNumber == "" {
                return ErrorResponse(c, "Table number is required", fiber.StatusBadRequest)
        }

        // Generate unique token
        token := fmt.Sprintf("TBL-%d", time.Now().Unix())

        result, err := DB.Exec(`
                INSERT INTO tables (table_number, token, status, outlet_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, NOW(), NOW())
        `, req.TableNumber, token, req.Status, req.OutletID)

        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to create table: %v", err), fiber.StatusInternalServerError)
        }

        id, _ := result.LastInsertId()

        return c.Status(fiber.StatusCreated).JSON(fiber.Map{
                "success": true,
                "message": "Table created successfully",
                "table": fiber.Map{
                        "id":           id,
                        "table_number": req.TableNumber,
                        "token":        token,
                        "status":       req.Status,
                },
        })
}

func UpdateTable(c *fiber.Ctx) error {
        id := c.Params("id")
        
        var req struct {
                TableNumber string `json:"table_number"`
                Status      string `json:"status"`
                OutletID    *int   `json:"outlet_id"`
        }

        if err := c.BodyParser(&req); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        _, err := DB.Exec(`
                UPDATE tables 
                SET table_number = ?, status = ?, outlet_id = ?, updated_at = NOW()
                WHERE id = ?
        `, req.TableNumber, req.Status, req.OutletID, id)

        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to update table: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Table updated successfully",
        })
}

func DeleteTable(c *fiber.Ctx) error {
        id := c.Params("id")

        _, err := DB.Exec("DELETE FROM tables WHERE id = ?", id)
        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to delete table: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Table deleted successfully",
        })
}

func RegenerateTableQR(c *fiber.Ctx) error {
        id := c.Params("id")
        
        // Generate new token
        newToken := fmt.Sprintf("TBL-%d", time.Now().Unix())

        _, err := DB.Exec("UPDATE tables SET token = ?, updated_at = NOW() WHERE id = ?", newToken, id)
        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to regenerate QR: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "QR code regenerated successfully",
                "token":   newToken,
        })
}

func GetCustomers(c *fiber.Ctx) error {
        rows, err := DB.Query("SELECT id, name, email, phone, address, created_at FROM customers ORDER BY created_at DESC LIMIT 100")
        if err != nil {
                return c.JSON(fiber.Map{"success": true, "customers": []interface{}{}})
        }
        defer rows.Close()
        
        var customers []map[string]interface{}
        for rows.Next() {
                var id int
                var name string
                var email, phone, address sql.NullString
                var createdAt sql.NullTime
                rows.Scan(&id, &name, &email, &phone, &address, &createdAt)
                customers = append(customers, map[string]interface{}{
                        "id":         id,
                        "name":       name,
                        "email":      email,
                        "phone":      phone,
                        "address":    address,
                        "created_at": createdAt,
                })
        }
        
        if customers == nil {
                customers = []map[string]interface{}{}
        }
        
        return c.JSON(fiber.Map{"success": true, "customers": customers})
}

func GetCustomer(c *fiber.Ctx) error {
        id := c.Params("id")
        
        var cid int
        var name string
        var email, phone, address sql.NullString
        var createdAt sql.NullTime

        query := "SELECT id, name, email, phone, address, created_at FROM customers WHERE id = ?"
        err := DB.QueryRow(query, id).Scan(&cid, &name, &email, &phone, &address, &createdAt)

        if err == sql.ErrNoRows {
                return ErrorResponse(c, "Customer not found", fiber.StatusNotFound)
        }
        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Database error: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{"success": true, "customer": map[string]interface{}{
                "id":         cid,
                "name":       name,
                "email":      email,
                "phone":      phone,
                "address":    address,
                "created_at": createdAt,
        }})
}

func CreateCustomer(c *fiber.Ctx) error {
        var req struct {
                Name    string `json:"name"`
                Email   string `json:"email"`
                Phone   string `json:"phone"`
                Address string `json:"address"`
        }

        if err := c.BodyParser(&req); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        if req.Name == "" {
                return ErrorResponse(c, "Customer name is required", fiber.StatusBadRequest)
        }

        result, err := DB.Exec(`
                INSERT INTO customers (name, email, phone, address, created_at)
                VALUES (?, ?, ?, ?, NOW())
        `, req.Name, req.Email, req.Phone, req.Address)

        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to create customer: %v", err), fiber.StatusInternalServerError)
        }

        id, _ := result.LastInsertId()

        return c.Status(fiber.StatusCreated).JSON(fiber.Map{
                "success": true,
                "message": "Customer created successfully",
                "customer": fiber.Map{
                        "id":      id,
                        "name":    req.Name,
                        "email":   req.Email,
                        "phone":   req.Phone,
                        "address": req.Address,
                },
        })
}

func UpdateCustomer(c *fiber.Ctx) error {
        id := c.Params("id")
        
        var req struct {
                Name    string `json:"name"`
                Email   string `json:"email"`
                Phone   string `json:"phone"`
                Address string `json:"address"`
        }

        if err := c.BodyParser(&req); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        _, err := DB.Exec(`
                UPDATE customers 
                SET name = ?, email = ?, phone = ?, address = ?
                WHERE id = ?
        `, req.Name, req.Email, req.Phone, req.Address, id)

        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to update customer: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Customer updated successfully",
        })
}

func DeleteCustomer(c *fiber.Ctx) error {
        id := c.Params("id")

        _, err := DB.Exec("DELETE FROM customers WHERE id = ?", id)
        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to delete customer: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Customer deleted successfully",
        })
}

func GetCoupons(c *fiber.Ctx) error {
        rows, err := DB.Query(`
                SELECT id, code, discount_type, discount_value, min_purchase, max_discount,
                       valid_from, valid_until, is_active, created_at, usage_limit, used_count
                FROM coupons
                ORDER BY created_at DESC
        `)
        if err != nil {
                return ErrorResponse(c, "Failed to fetch coupons: "+err.Error(), fiber.StatusInternalServerError)
        }
        defer rows.Close()

        var coupons []map[string]interface{}
        for rows.Next() {
                var id int
                var code, discountType string
                var discountValue, minPurchase, maxDiscount float64
                var validFrom, validUntil sql.NullTime
                var isActive bool
                var createdAt time.Time
                var usageLimit, usedCount sql.NullInt64

                if err := rows.Scan(&id, &code, &discountType, &discountValue, &minPurchase, &maxDiscount,
                        &validFrom, &validUntil, &isActive, &createdAt, &usageLimit, &usedCount); err != nil {
                        continue
                }

                coupon := map[string]interface{}{
                        "id":             id,
                        "code":           code,
                        "discount_type":  discountType,
                        "discount_value": discountValue,
                        "min_purchase":   minPurchase,
                        "max_discount":   maxDiscount,
                        "is_active":      isActive,
                        "created_at":     createdAt,
                }

                if validFrom.Valid {
                        coupon["valid_from"] = validFrom.Time
                }
                if validUntil.Valid {
                        coupon["valid_until"] = validUntil.Time
                }
                if usageLimit.Valid {
                        coupon["usage_limit"] = usageLimit.Int64
                }
                if usedCount.Valid {
                        coupon["used_count"] = usedCount.Int64
                }

                coupons = append(coupons, coupon)
        }

        if coupons == nil {
                coupons = []map[string]interface{}{}
        }

        return c.JSON(fiber.Map{
                "success": true,
                "coupons": coupons,
        })
}

func GetCoupon(c *fiber.Ctx) error {
        id := c.Params("id")
        var couponID int
        var code, discountType string
        var discountValue, minPurchase, maxDiscount float64
        var validFrom, validUntil sql.NullTime
        var isActive bool
        var createdAt time.Time
        var usageLimit, usedCount sql.NullInt64

        err := DB.QueryRow(`
                SELECT id, code, discount_type, discount_value, min_purchase, max_discount,
                       valid_from, valid_until, is_active, created_at, usage_limit, used_count
                FROM coupons WHERE id = ?
        `, id).Scan(&couponID, &code, &discountType, &discountValue, &minPurchase, &maxDiscount,
                &validFrom, &validUntil, &isActive, &createdAt, &usageLimit, &usedCount)

        if err == sql.ErrNoRows {
                return ErrorResponse(c, "Coupon not found", fiber.StatusNotFound)
        }
        if err != nil {
                return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
        }

        coupon := map[string]interface{}{
                "id":             couponID,
                "code":           code,
                "discount_type":  discountType,
                "discount_value": discountValue,
                "min_purchase":   minPurchase,
                "max_discount":   maxDiscount,
                "is_active":      isActive,
                "created_at":     createdAt,
        }

        if validFrom.Valid {
                coupon["valid_from"] = validFrom.Time
        }
        if validUntil.Valid {
                coupon["valid_until"] = validUntil.Time
        }
        if usageLimit.Valid {
                coupon["usage_limit"] = usageLimit.Int64
        }
        if usedCount.Valid {
                coupon["used_count"] = usedCount.Int64
        }

        return c.JSON(fiber.Map{
                "success": true,
                "coupon":  coupon,
        })
}

func CreateCoupon(c *fiber.Ctx) error {
        var input struct {
                Code          string  `json:"code"`
                DiscountType  string  `json:"discount_type"`
                DiscountValue float64 `json:"discount_value"`
                MinPurchase   float64 `json:"min_purchase"`
                MaxDiscount   float64 `json:"max_discount"`
                ValidFrom     *time.Time `json:"valid_from"`
                ValidUntil    *time.Time `json:"valid_until"`
                IsActive      bool    `json:"is_active"`
                UsageLimit    *int    `json:"usage_limit"`
        }

        if err := c.BodyParser(&input); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        result, err := DB.Exec(`
                INSERT INTO coupons (code, discount_type, discount_value, min_purchase, max_discount,
                                    valid_from, valid_until, is_active, created_at, usage_limit, used_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, NOW(), ?, 0)
        `, input.Code, input.DiscountType, input.DiscountValue, input.MinPurchase, input.MaxDiscount,
                input.ValidFrom, input.ValidUntil, input.IsActive, input.UsageLimit)

        if err != nil {
                return ErrorResponse(c, "Failed to create coupon: "+err.Error(), fiber.StatusInternalServerError)
        }

        id, _ := result.LastInsertId()

        return c.Status(fiber.StatusCreated).JSON(fiber.Map{
                "success": true,
                "message": "Coupon created successfully",
                "data": map[string]interface{}{
                        "id":             id,
                        "code":           input.Code,
                        "discount_type":  input.DiscountType,
                        "discount_value": input.DiscountValue,
                        "min_purchase":   input.MinPurchase,
                        "max_discount":   input.MaxDiscount,
                        "is_active":      input.IsActive,
                },
        })
}

func UpdateCoupon(c *fiber.Ctx) error {
        id := c.Params("id")
        var input struct {
                Code          string  `json:"code"`
                DiscountType  string  `json:"discount_type"`
                DiscountValue float64 `json:"discount_value"`
                MinPurchase   float64 `json:"min_purchase"`
                MaxDiscount   float64 `json:"max_discount"`
                ValidFrom     *time.Time `json:"valid_from"`
                ValidUntil    *time.Time `json:"valid_until"`
                IsActive      bool    `json:"is_active"`
                UsageLimit    *int    `json:"usage_limit"`
        }

        if err := c.BodyParser(&input); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        _, err := DB.Exec(`
                UPDATE coupons 
                SET code = ?, discount_type = ?, discount_value = ?, min_purchase = ?, max_discount = ?,
                    valid_from = ?, valid_until = ?, is_active = ?, usage_limit = ?
                WHERE id = ?
        `, input.Code, input.DiscountType, input.DiscountValue, input.MinPurchase, input.MaxDiscount,
                input.ValidFrom, input.ValidUntil, input.IsActive, input.UsageLimit, id)

        if err != nil {
                return ErrorResponse(c, "Failed to update coupon", fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Coupon updated successfully",
        })
}

func DeleteCoupon(c *fiber.Ctx) error {
        id := c.Params("id")

        _, err := DB.Exec("DELETE FROM coupons WHERE id = ?", id)
        if err != nil {
                return ErrorResponse(c, "Failed to delete coupon", fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Coupon deleted successfully",
        })
}

func GetOutlets(c *fiber.Ctx) error {
        return c.JSON(fiber.Map{"success": true, "outlets": []interface{}{}})
}

func GetOutlet(c *fiber.Ctx) error {
        id := c.Params("id")
        var outlet Outlet

        query := "SELECT id, name, address, phone, is_active, created_at, updated_at FROM outlets WHERE id = ?"
        err := DB.QueryRow(query, id).Scan(&outlet.ID, &outlet.Name, &outlet.Address, &outlet.Phone,
                &outlet.IsActive, &outlet.CreatedAt, &outlet.UpdatedAt)

        if err == sql.ErrNoRows {
                return ErrorResponse(c, "Outlet not found", fiber.StatusNotFound)
        }
        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Database error: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{"success": true, "outlet": outlet})
}

func CreateOutlet(c *fiber.Ctx) error {
        var req struct {
                Name     string `json:"name"`
                Address  string `json:"address"`
                Phone    string `json:"phone"`
                IsActive bool   `json:"is_active"`
        }

        if err := c.BodyParser(&req); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        if req.Name == "" {
                return ErrorResponse(c, "Outlet name is required", fiber.StatusBadRequest)
        }

        result, err := DB.Exec(`
                INSERT INTO outlets (name, address, phone, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, NOW(), NOW())
        `, req.Name, req.Address, req.Phone, req.IsActive)

        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to create outlet: %v", err), fiber.StatusInternalServerError)
        }

        id, _ := result.LastInsertId()

        return c.Status(fiber.StatusCreated).JSON(fiber.Map{
                "success": true,
                "message": "Outlet created successfully",
                "outlet": fiber.Map{
                        "id":        id,
                        "name":      req.Name,
                        "address":   req.Address,
                        "phone":     req.Phone,
                        "is_active": req.IsActive,
                },
        })
}

func UpdateOutlet(c *fiber.Ctx) error {
        id := c.Params("id")
        
        var req struct {
                Name     string `json:"name"`
                Address  string `json:"address"`
                Phone    string `json:"phone"`
                IsActive bool   `json:"is_active"`
        }

        if err := c.BodyParser(&req); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        _, err := DB.Exec(`
                UPDATE outlets 
                SET name = ?, address = ?, phone = ?, is_active = ?, updated_at = NOW()
                WHERE id = ?
        `, req.Name, req.Address, req.Phone, req.IsActive, id)

        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to update outlet: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Outlet updated successfully",
        })
}

func DeleteOutlet(c *fiber.Ctx) error {
        id := c.Params("id")

        _, err := DB.Exec("DELETE FROM outlets WHERE id = ?", id)
        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to delete outlet: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Outlet deleted successfully",
        })
}

func GetPaymentMethods(c *fiber.Ctx) error {
        rows, err := DB.Query("SELECT id, name, type, is_active, config, created_at FROM payment_methods ORDER BY created_at DESC")
        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Database error: %v", err), fiber.StatusInternalServerError)
        }
        defer rows.Close()

        var methods []map[string]interface{}
        for rows.Next() {
                var pm PaymentMethod
                if err := rows.Scan(&pm.ID, &pm.Name, &pm.Type, &pm.IsActive, &pm.Config, &pm.CreatedAt); err != nil {
                        continue
                }
                methods = append(methods, map[string]interface{}{
                        "id":         pm.ID,
                        "name":       pm.Name,
                        "type":       pm.Type,
                        "is_active":  pm.IsActive,
                        "config":     getNullString(pm.Config),
                        "created_at": getNullTime(pm.CreatedAt),
                })
        }

        if methods == nil {
                methods = []map[string]interface{}{}
        }

        return c.JSON(fiber.Map{"success": true, "payment_methods": methods})
}

func GetPaymentMethod(c *fiber.Ctx) error {
        id := c.Params("id")
        var pm PaymentMethod

        query := "SELECT id, name, type, is_active, created_at FROM payment_methods WHERE id = ?"
        err := DB.QueryRow(query, id).Scan(&pm.ID, &pm.Name, &pm.Type, &pm.IsActive, &pm.CreatedAt)

        if err == sql.ErrNoRows {
                return ErrorResponse(c, "Payment method not found", fiber.StatusNotFound)
        }
        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Database error: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{"success": true, "payment_method": pm})
}

func CreatePaymentMethod(c *fiber.Ctx) error {
        var req struct {
                Name     string `json:"name"`
                Type     string `json:"type"`
                IsActive bool   `json:"is_active"`
        }

        if err := c.BodyParser(&req); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        if req.Name == "" {
                return ErrorResponse(c, "Payment method name is required", fiber.StatusBadRequest)
        }

        result, err := DB.Exec(`
                INSERT INTO payment_methods (name, type, is_active, created_at, updated_at)
                VALUES (?, ?, ?, NOW(), NOW())
        `, req.Name, req.Type, req.IsActive)

        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to create payment method: %v", err), fiber.StatusInternalServerError)
        }

        id, _ := result.LastInsertId()

        return c.Status(fiber.StatusCreated).JSON(fiber.Map{
                "success": true,
                "message": "Payment method created successfully",
                "payment_method": fiber.Map{
                        "id":        id,
                        "name":      req.Name,
                        "type":      req.Type,
                        "is_active": req.IsActive,
                },
        })
}

func UpdatePaymentMethod(c *fiber.Ctx) error {
        id := c.Params("id")
        
        var req struct {
                Name     string `json:"name"`
                Type     string `json:"type"`
                IsActive bool   `json:"is_active"`
        }

        if err := c.BodyParser(&req); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        _, err := DB.Exec(`
                UPDATE payment_methods 
                SET name = ?, type = ?, is_active = ?, updated_at = NOW()
                WHERE id = ?
        `, req.Name, req.Type, req.IsActive, id)

        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to update payment method: %v", err), fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Payment method updated successfully",
        })
}

func DeletePaymentMethod(c *fiber.Ctx) error {
        id := c.Params("id")

        _, err := DB.Exec("DELETE FROM payment_methods WHERE id = ?", id)
        if err != nil {
                return ErrorResponse(c, fmt.Sprintf("Failed to delete payment method: %v", err), fiber.StatusInternalServerError)
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
        var totalRevenue float64
        var totalOrders, totalProducts, totalCustomers int

        // Revenue and orders
        DB.QueryRow(`
                SELECT COALESCE(SUM(total_amount), 0), COUNT(*)
                FROM orders
                WHERE status = 'completed'
        `).Scan(&totalRevenue, &totalOrders)

        // Total products
        DB.QueryRow("SELECT COUNT(*) FROM products").Scan(&totalProducts)

        // Total customers
        DB.QueryRow("SELECT COUNT(*) FROM customers").Scan(&totalCustomers)

        // Top products
        topProductsRows, _ := DB.Query(`
                SELECT p.name, COALESCE(SUM(oi.quantity), 0) as total_sold, 
                       COALESCE(SUM(oi.subtotal), 0) as total_revenue
                FROM products p
                LEFT JOIN order_items oi ON p.id = oi.product_id
                LEFT JOIN orders o ON oi.order_id = o.id AND o.status = 'completed'
                GROUP BY p.id, p.name
                HAVING total_sold > 0
                ORDER BY total_sold DESC
                LIMIT 5
        `)

        var topProducts []map[string]interface{}
        if topProductsRows != nil {
                defer topProductsRows.Close()
                for topProductsRows.Next() {
                        var name string
                        var totalSold int
                        var totalRevenue float64
                        if err := topProductsRows.Scan(&name, &totalSold, &totalRevenue); err == nil {
                                topProducts = append(topProducts, map[string]interface{}{
                                        "name":          name,
                                        "total_sold":    totalSold,
                                        "total_revenue": totalRevenue,
                                })
                        }
                }
        }

        if topProducts == nil {
                topProducts = []map[string]interface{}{}
        }

        return c.JSON(fiber.Map{
                "success":         true,
                "total_revenue":   totalRevenue,
                "total_orders":    totalOrders,
                "total_products":  totalProducts,
                "total_customers": totalCustomers,
                "top_products":    topProducts,
                "recent_orders":   []interface{}{},
        })
}


// ========== CUSTOMER AUTHENTICATION ==========

func CustomerRegister(c *fiber.Ctx) error {
        var input struct {
                Name     string `json:"name"`
                Email    string `json:"email"`
                Phone    string `json:"phone"`
                Password string `json:"password"`
        }

        if err := c.BodyParser(&input); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        // Validate required fields
        if input.Name == "" || input.Email == "" || input.Password == "" {
                return ErrorResponse(c, "Name, email, and password are required", fiber.StatusBadRequest)
        }

        // Check if email already exists
        var exists int
        DB.QueryRow("SELECT COUNT(*) FROM customers WHERE email = ?", input.Email).Scan(&exists)
        if exists > 0 {
                return ErrorResponse(c, "Email already registered", fiber.StatusConflict)
        }

        // Hash password
        hashedPassword, err := bcrypt.GenerateFromPassword([]byte(input.Password), bcrypt.DefaultCost)
        if err != nil {
                return ErrorResponse(c, "Failed to hash password", fiber.StatusInternalServerError)
        }

        // Insert customer
        result, err := DB.Exec(`
                INSERT INTO customers (name, email, phone, password, created_at)
                VALUES (?, ?, ?, ?, NOW())
        `, input.Name, input.Email, input.Phone, string(hashedPassword))

        if err != nil {
                return ErrorResponse(c, "Failed to create customer: "+err.Error(), fiber.StatusInternalServerError)
        }

        customerID, _ := result.LastInsertId()

        // Generate token
        token, err := GenerateToken(&User{
                ID:       int(customerID),
                Username: input.Email,
                FullName: sql.NullString{String: input.Name, Valid: true},
        })

        if err != nil {
                return ErrorResponse(c, "Failed to generate token", fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Customer registered successfully",
                "token":   token,
                "customer": fiber.Map{
                        "id":    customerID,
                        "name":  input.Name,
                        "email": input.Email,
                        "phone": input.Phone,
                },
        })
}

func CustomerLogin(c *fiber.Ctx) error {
        var input struct {
                Email    string `json:"email"`
                Password string `json:"password"`
        }

        if err := c.BodyParser(&input); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        // Get customer by email
        var customer struct {
                ID       int
                Name     string
                Email    string
                Phone    sql.NullString
                Password string
                Points   int
        }

        err := DB.QueryRow(`
                SELECT id, name, email, phone, password, points
                FROM customers
                WHERE email = ?
        `, input.Email).Scan(&customer.ID, &customer.Name, &customer.Email, &customer.Phone, &customer.Password, &customer.Points)

        if err == sql.ErrNoRows {
                return ErrorResponse(c, "Invalid email or password", fiber.StatusUnauthorized)
        }
        if err != nil {
                return ErrorResponse(c, "Database error: "+err.Error(), fiber.StatusInternalServerError)
        }

        // Compare password
        if err := bcrypt.CompareHashAndPassword([]byte(customer.Password), []byte(input.Password)); err != nil {
                return ErrorResponse(c, "Invalid email or password", fiber.StatusUnauthorized)
        }

        // Generate token
        token, err := GenerateToken(&User{
                ID:       customer.ID,
                Username: customer.Email,
                FullName: sql.NullString{String: customer.Name, Valid: true},
        })

        if err != nil {
                return ErrorResponse(c, "Failed to generate token", fiber.StatusInternalServerError)
        }

        phone := ""
        if customer.Phone.Valid {
                phone = customer.Phone.String
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Login successful",
                "token":   token,
                "customer": fiber.Map{
                        "id":     customer.ID,
                        "name":   customer.Name,
                        "email":  customer.Email,
                        "phone":  phone,
                        "points": customer.Points,
                },
        })
}

func CustomerChangePassword(c *fiber.Ctx) error {
        userID := c.Locals("userID")
        if userID == nil {
                return ErrorResponse(c, "Unauthorized", fiber.StatusUnauthorized)
        }

        var input struct {
                OldPassword string `json:"old_password"`
                NewPassword string `json:"new_password"`
        }

        if err := c.BodyParser(&input); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        // Get current password
        var currentPassword string
        err := DB.QueryRow("SELECT password FROM customers WHERE id = ?", userID).Scan(&currentPassword)
        if err != nil {
                return ErrorResponse(c, "Customer not found", fiber.StatusNotFound)
        }

        // Verify old password
        if err := bcrypt.CompareHashAndPassword([]byte(currentPassword), []byte(input.OldPassword)); err != nil {
                return ErrorResponse(c, "Invalid old password", fiber.StatusBadRequest)
        }

        // Hash new password
        hashedPassword, err := bcrypt.GenerateFromPassword([]byte(input.NewPassword), bcrypt.DefaultCost)
        if err != nil {
                return ErrorResponse(c, "Failed to hash password", fiber.StatusInternalServerError)
        }

        // Update password
        _, err = DB.Exec("UPDATE customers SET password = ?, updated_at = NOW() WHERE id = ?", string(hashedPassword), userID)
        if err != nil {
                return ErrorResponse(c, "Failed to update password", fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Password changed successfully",
        })
}

// ========== ROLES CRUD ==========

func GetRoles(c *fiber.Ctx) error {
        rows, err := DB.Query("SELECT id, name, max_discount, created_at FROM roles ORDER BY created_at DESC")
        if err != nil {
                return ErrorResponse(c, "Failed to fetch roles: "+err.Error(), fiber.StatusInternalServerError)
        }
        defer rows.Close()

        var roles []map[string]interface{}
        for rows.Next() {
                var id int
                var name string
                var maxDiscount float64
                var createdAt time.Time
                if err := rows.Scan(&id, &name, &maxDiscount, &createdAt); err != nil {
                        continue
                }
                roles = append(roles, map[string]interface{}{
                        "id":           id,
                        "name":         name,
                        "max_discount": maxDiscount,
                        "created_at":   createdAt,
                })
        }

        if roles == nil {
                roles = []map[string]interface{}{}
        }

        return c.JSON(fiber.Map{
                "success": true,
                "roles":   roles,
        })
}

func GetRole(c *fiber.Ctx) error {
        id := c.Params("id")
        var role map[string]interface{}
        var roleID int
        var name string
        var maxDiscount float64
        var createdAt time.Time

        err := DB.QueryRow("SELECT id, name, max_discount, created_at FROM roles WHERE id = ?", id).
                Scan(&roleID, &name, &maxDiscount, &createdAt)

        if err == sql.ErrNoRows {
                return ErrorResponse(c, "Role not found", fiber.StatusNotFound)
        }
        if err != nil {
                return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
        }

        role = map[string]interface{}{
                "id":           roleID,
                "name":         name,
                "max_discount": maxDiscount,
                "created_at":   createdAt,
        }

        return c.JSON(role)
}

func CreateRole(c *fiber.Ctx) error {
        var input struct {
                Name        string  `json:"name"`
                MaxDiscount float64 `json:"max_discount"`
        }
        
        if err := c.BodyParser(&input); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        result, err := DB.Exec(`
                INSERT INTO roles (name, max_discount, created_at)
                VALUES (?, ?, NOW())
        `, input.Name, input.MaxDiscount)

        if err != nil {
                return ErrorResponse(c, "Failed to create role: "+err.Error(), fiber.StatusInternalServerError)
        }

        id, _ := result.LastInsertId()

        return c.Status(fiber.StatusCreated).JSON(fiber.Map{
                "success": true,
                "message": "Role created successfully",
                "data": map[string]interface{}{
                        "id":           id,
                        "name":         input.Name,
                        "max_discount": input.MaxDiscount,
                },
        })
}

func UpdateRole(c *fiber.Ctx) error {
        id := c.Params("id")
        var input struct {
                Name        string  `json:"name"`
                MaxDiscount float64 `json:"max_discount"`
        }

        if err := c.BodyParser(&input); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        _, err := DB.Exec(`
                UPDATE roles 
                SET name = ?, max_discount = ?
                WHERE id = ?
        `, input.Name, input.MaxDiscount, id)

        if err != nil {
                return ErrorResponse(c, "Failed to update role", fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Role updated successfully",
        })
}

func DeleteRole(c *fiber.Ctx) error {
        id := c.Params("id")

        _, err := DB.Exec("DELETE FROM roles WHERE id = ?", id)
        if err != nil {
                return ErrorResponse(c, "Failed to delete role", fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Role deleted successfully",
        })
}

// ========== BANK ACCOUNTS CRUD ==========

func GetBankAccounts(c *fiber.Ctx) error {
        rows, err := DB.Query("SELECT id, bank_name, account_number, account_name, is_active, created_at FROM bank_accounts ORDER BY created_at DESC")
        if err != nil {
                return ErrorResponse(c, "Failed to fetch bank accounts: "+err.Error(), fiber.StatusInternalServerError)
        }
        defer rows.Close()

        var accounts []map[string]interface{}
        for rows.Next() {
                var id int
                var bankName, accountNumber, accountName string
                var isActive bool
                var createdAt time.Time
                if err := rows.Scan(&id, &bankName, &accountNumber, &accountName, &isActive, &createdAt); err != nil {
                        continue
                }
                accounts = append(accounts, map[string]interface{}{
                        "id":             id,
                        "bank_name":      bankName,
                        "account_number": accountNumber,
                        "account_name":   accountName,
                        "is_active":      isActive,
                        "created_at":     createdAt,
                })
        }

        if accounts == nil {
                accounts = []map[string]interface{}{}
        }

        return c.JSON(fiber.Map{
                "success":       true,
                "bank_accounts": accounts,
        })
}

func GetBankAccount(c *fiber.Ctx) error {
        id := c.Params("id")
        var accountID int
        var bankName, accountNumber, accountName string
        var isActive bool
        var createdAt time.Time

        err := DB.QueryRow("SELECT id, bank_name, account_number, account_name, is_active, created_at FROM bank_accounts WHERE id = ?", id).
                Scan(&accountID, &bankName, &accountNumber, &accountName, &isActive, &createdAt)

        if err == sql.ErrNoRows {
                return ErrorResponse(c, "Bank account not found", fiber.StatusNotFound)
        }
        if err != nil {
                return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
        }

        return c.JSON(map[string]interface{}{
                "id":             accountID,
                "bank_name":      bankName,
                "account_number": accountNumber,
                "account_name":   accountName,
                "is_active":      isActive,
                "created_at":     createdAt,
        })
}

func CreateBankAccount(c *fiber.Ctx) error {
        var input struct {
                BankName      string `json:"bank_name"`
                AccountNumber string `json:"account_number"`
                AccountName   string `json:"account_name"`
                IsActive      bool   `json:"is_active"`
        }
        
        if err := c.BodyParser(&input); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        result, err := DB.Exec(`
                INSERT INTO bank_accounts (bank_name, account_number, account_name, is_active, created_at)
                VALUES (?, ?, ?, ?, NOW())
        `, input.BankName, input.AccountNumber, input.AccountName, input.IsActive)

        if err != nil {
                return ErrorResponse(c, "Failed to create bank account: "+err.Error(), fiber.StatusInternalServerError)
        }

        id, _ := result.LastInsertId()

        return c.Status(fiber.StatusCreated).JSON(fiber.Map{
                "success": true,
                "message": "Bank account created successfully",
                "data": map[string]interface{}{
                        "id":             id,
                        "bank_name":      input.BankName,
                        "account_number": input.AccountNumber,
                        "account_name":   input.AccountName,
                        "is_active":      input.IsActive,
                },
        })
}

func UpdateBankAccount(c *fiber.Ctx) error {
        id := c.Params("id")
        var input struct {
                BankName      string `json:"bank_name"`
                AccountNumber string `json:"account_number"`
                AccountName   string `json:"account_name"`
                IsActive      bool   `json:"is_active"`
        }

        if err := c.BodyParser(&input); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        _, err := DB.Exec(`
                UPDATE bank_accounts 
                SET bank_name = ?, account_number = ?, account_name = ?, is_active = ?
                WHERE id = ?
        `, input.BankName, input.AccountNumber, input.AccountName, input.IsActive, id)

        if err != nil {
                return ErrorResponse(c, "Failed to update bank account", fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Bank account updated successfully",
        })
}

func DeleteBankAccount(c *fiber.Ctx) error {
        id := c.Params("id")

        _, err := DB.Exec("DELETE FROM bank_accounts WHERE id = ?", id)
        if err != nil {
                return ErrorResponse(c, "Failed to delete bank account", fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Bank account deleted successfully",
        })
}

// ========== STORE SETTINGS ==========

func GetStoreSettings(c *fiber.Ctx) error {
        var settings map[string]interface{}
        var id int
        var storeName, storeDescription, bannerURL, logoURL, address, phone, email, openingHours sql.NullString
        var rating sql.NullFloat64
        var totalReviews sql.NullInt64
        var isOpen sql.NullBool
        var createdAt, updatedAt time.Time

        err := DB.QueryRow(`
                SELECT id, store_name, store_description, banner_url, logo_url, address, phone, email, 
                       rating, total_reviews, opening_hours, is_open, created_at, updated_at
                FROM store_settings LIMIT 1
        `).Scan(&id, &storeName, &storeDescription, &bannerURL, &logoURL, &address, &phone, &email,
                &rating, &totalReviews, &openingHours, &isOpen, &createdAt, &updatedAt)

        if err == sql.ErrNoRows {
                // Return default empty settings
                return c.JSON(map[string]interface{}{
                        "store_name":        "",
                        "store_description": "",
                        "banner_url":        "",
                        "logo_url":          "",
                        "address":           "",
                        "phone":             "",
                        "email":             "",
                        "rating":            0.0,
                        "total_reviews":     0,
                        "opening_hours":     "",
                        "is_open":           true,
                })
        }
        if err != nil {
                return ErrorResponse(c, "Failed to fetch store settings: "+err.Error(), fiber.StatusInternalServerError)
        }

        settings = map[string]interface{}{
                "id":                id,
                "store_name":        nullStringToString(storeName),
                "store_description": nullStringToString(storeDescription),
                "banner_url":        nullStringToString(bannerURL),
                "logo_url":          nullStringToString(logoURL),
                "address":           nullStringToString(address),
                "phone":             nullStringToString(phone),
                "email":             nullStringToString(email),
                "rating":            nullFloat64ToFloat(rating),
                "total_reviews":     nullInt64ToInt(totalReviews),
                "opening_hours":     nullStringToString(openingHours),
                "is_open":           nullBoolToBool(isOpen),
                "created_at":        createdAt,
                "updated_at":        updatedAt,
        }

        return c.JSON(settings)
}

func UpdateStoreSettings(c *fiber.Ctx) error {
        var input map[string]interface{}
        if err := c.BodyParser(&input); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        // Check if settings exist
        var count int
        DB.QueryRow("SELECT COUNT(*) FROM store_settings").Scan(&count)

        if count == 0 {
                // Insert new settings
                _, err := DB.Exec(`
                        INSERT INTO store_settings (store_name, store_description, banner_url, logo_url, address, 
                                                   phone, email, rating, total_reviews, opening_hours, is_open, 
                                                   created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())
                `, 
                        getMapValue(input, "store_name"),
                        getMapValue(input, "store_description"),
                        getMapValue(input, "banner_url"),
                        getMapValue(input, "logo_url"),
                        getMapValue(input, "address"),
                        getMapValue(input, "phone"),
                        getMapValue(input, "email"),
                        getMapValue(input, "rating"),
                        getMapValue(input, "total_reviews"),
                        getMapValue(input, "opening_hours"),
                        getMapValue(input, "is_open"),
                )
                if err != nil {
                        return ErrorResponse(c, "Failed to create store settings: "+err.Error(), fiber.StatusInternalServerError)
                }
        } else {
                // Update existing settings
                _, err := DB.Exec(`
                        UPDATE store_settings 
                        SET store_name = ?, store_description = ?, banner_url = ?, logo_url = ?, address = ?,
                            phone = ?, email = ?, rating = ?, total_reviews = ?, opening_hours = ?, is_open = ?,
                            updated_at = NOW()
                        WHERE id = (SELECT id FROM (SELECT id FROM store_settings LIMIT 1) as temp)
                `,
                        getMapValue(input, "store_name"),
                        getMapValue(input, "store_description"),
                        getMapValue(input, "banner_url"),
                        getMapValue(input, "logo_url"),
                        getMapValue(input, "address"),
                        getMapValue(input, "phone"),
                        getMapValue(input, "email"),
                        getMapValue(input, "rating"),
                        getMapValue(input, "total_reviews"),
                        getMapValue(input, "opening_hours"),
                        getMapValue(input, "is_open"),
                )
                if err != nil {
                        return ErrorResponse(c, "Failed to update store settings: "+err.Error(), fiber.StatusInternalServerError)
                }
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Store settings updated successfully",
        })
}

// Helper functions
func nullStringToString(ns sql.NullString) string {
        if ns.Valid {
                return ns.String
        }
        return ""
}

func nullFloat64ToFloat(nf sql.NullFloat64) float64 {
        if nf.Valid {
                return nf.Float64
        }
        return 0.0
}

func nullInt64ToInt(ni sql.NullInt64) int {
        if ni.Valid {
                return int(ni.Int64)
        }
        return 0
}

func nullBoolToBool(nb sql.NullBool) bool {
        if nb.Valid {
                return nb.Bool
        }
        return false
}

func getMapValue(m map[string]interface{}, key string) interface{} {
        if val, ok := m[key]; ok {
                return val
        }
        return nil
}

// ========== STORE BANNERS CRUD ==========

func GetStoreBanners(c *fiber.Ctx) error {
        rows, err := DB.Query("SELECT id, title, subtitle, image_url, link_url, button_text, display_order, is_active, created_at, updated_at FROM store_banners ORDER BY display_order ASC")
        if err != nil {
                return ErrorResponse(c, "Failed to fetch store banners: "+err.Error(), fiber.StatusInternalServerError)
        }
        defer rows.Close()

        var banners []map[string]interface{}
        for rows.Next() {
                var id, displayOrder int
                var title, subtitle, imageURL, linkURL, buttonText sql.NullString
                var isActive bool
                var createdAt, updatedAt time.Time
                
                if err := rows.Scan(&id, &title, &subtitle, &imageURL, &linkURL, &buttonText, &displayOrder, &isActive, &createdAt, &updatedAt); err != nil {
                        continue
                }
                banners = append(banners, map[string]interface{}{
                        "id":            id,
                        "title":         nullStringToString(title),
                        "subtitle":      nullStringToString(subtitle),
                        "image_url":     nullStringToString(imageURL),
                        "link_url":      nullStringToString(linkURL),
                        "button_text":   nullStringToString(buttonText),
                        "display_order": displayOrder,
                        "is_active":     isActive,
                        "created_at":    createdAt,
                        "updated_at":    updatedAt,
                })
        }

        if banners == nil {
                banners = []map[string]interface{}{}
        }

        return c.JSON(banners)
}

func GetStoreBanner(c *fiber.Ctx) error {
        id := c.Params("id")
        var bannerID, displayOrder int
        var title, subtitle, imageURL, linkURL, buttonText sql.NullString
        var isActive bool
        var createdAt, updatedAt time.Time

        err := DB.QueryRow("SELECT id, title, subtitle, image_url, link_url, button_text, display_order, is_active, created_at, updated_at FROM store_banners WHERE id = ?", id).
                Scan(&bannerID, &title, &subtitle, &imageURL, &linkURL, &buttonText, &displayOrder, &isActive, &createdAt, &updatedAt)

        if err == sql.ErrNoRows {
                return ErrorResponse(c, "Store banner not found", fiber.StatusNotFound)
        }
        if err != nil {
                return ErrorResponse(c, "Database error", fiber.StatusInternalServerError)
        }

        return c.JSON(map[string]interface{}{
                "id":            bannerID,
                "title":         nullStringToString(title),
                "subtitle":      nullStringToString(subtitle),
                "image_url":     nullStringToString(imageURL),
                "link_url":      nullStringToString(linkURL),
                "button_text":   nullStringToString(buttonText),
                "display_order": displayOrder,
                "is_active":     isActive,
                "created_at":    createdAt,
                "updated_at":    updatedAt,
        })
}

func CreateStoreBanner(c *fiber.Ctx) error {
        var input struct {
                Title        string `json:"title"`
                Subtitle     string `json:"subtitle"`
                ImageURL     string `json:"image_url"`
                LinkURL      string `json:"link_url"`
                ButtonText   string `json:"button_text"`
                DisplayOrder int    `json:"display_order"`
                IsActive     bool   `json:"is_active"`
        }
        
        if err := c.BodyParser(&input); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        result, err := DB.Exec(`
                INSERT INTO store_banners (title, subtitle, image_url, link_url, button_text, display_order, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, NOW(), NOW())
        `, input.Title, input.Subtitle, input.ImageURL, input.LinkURL, input.ButtonText, input.DisplayOrder, input.IsActive)

        if err != nil {
                return ErrorResponse(c, "Failed to create store banner: "+err.Error(), fiber.StatusInternalServerError)
        }

        id, _ := result.LastInsertId()

        return c.Status(fiber.StatusCreated).JSON(fiber.Map{
                "success": true,
                "message": "Store banner created successfully",
                "data": map[string]interface{}{
                        "id":            id,
                        "title":         input.Title,
                        "subtitle":      input.Subtitle,
                        "image_url":     input.ImageURL,
                        "link_url":      input.LinkURL,
                        "button_text":   input.ButtonText,
                        "display_order": input.DisplayOrder,
                        "is_active":     input.IsActive,
                },
        })
}

func UpdateStoreBanner(c *fiber.Ctx) error {
        id := c.Params("id")
        var input struct {
                Title        string `json:"title"`
                Subtitle     string `json:"subtitle"`
                ImageURL     string `json:"image_url"`
                LinkURL      string `json:"link_url"`
                ButtonText   string `json:"button_text"`
                DisplayOrder int    `json:"display_order"`
                IsActive     bool   `json:"is_active"`
        }

        if err := c.BodyParser(&input); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        _, err := DB.Exec(`
                UPDATE store_banners 
                SET title = ?, subtitle = ?, image_url = ?, link_url = ?, button_text = ?, display_order = ?, is_active = ?, updated_at = NOW()
                WHERE id = ?
        `, input.Title, input.Subtitle, input.ImageURL, input.LinkURL, input.ButtonText, input.DisplayOrder, input.IsActive, id)

        if err != nil {
                return ErrorResponse(c, "Failed to update store banner", fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Store banner updated successfully",
        })
}

func DeleteStoreBanner(c *fiber.Ctx) error {
        id := c.Params("id")

        _, err := DB.Exec("DELETE FROM store_banners WHERE id = ?", id)
        if err != nil {
                return ErrorResponse(c, "Failed to delete store banner", fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "Store banner deleted successfully",
        })
}

// ========== COUPONS AVAILABLE ==========

func GetAvailableCoupons(c *fiber.Ctx) error {
        rows, err := DB.Query(`
                SELECT id, code, discount_type, discount_value, min_purchase, max_discount, 
                       valid_from, valid_until, is_active, created_at, usage_limit, used_count
                FROM coupons
                WHERE is_active = 1
                AND (valid_from IS NULL OR valid_from <= NOW())
                AND (valid_until IS NULL OR valid_until >= NOW())
                AND (usage_limit IS NULL OR used_count < usage_limit)
                ORDER BY created_at DESC
        `)
        if err != nil {
                return ErrorResponse(c, "Failed to fetch available coupons: "+err.Error(), fiber.StatusInternalServerError)
        }
        defer rows.Close()

        var coupons []map[string]interface{}
        for rows.Next() {
                var id int
                var code, discountType string
                var discountValue, minPurchase, maxDiscount float64
                var validFrom, validUntil sql.NullTime
                var isActive bool
                var createdAt time.Time
                var usageLimit, usedCount sql.NullInt64

                if err := rows.Scan(&id, &code, &discountType, &discountValue, &minPurchase, &maxDiscount,
                        &validFrom, &validUntil, &isActive, &createdAt, &usageLimit, &usedCount); err != nil {
                        continue
                }

                coupon := map[string]interface{}{
                        "id":             id,
                        "code":           code,
                        "discount_type":  discountType,
                        "discount_value": discountValue,
                        "min_purchase":   minPurchase,
                        "max_discount":   maxDiscount,
                        "is_active":      isActive,
                        "created_at":     createdAt,
                }

                if validFrom.Valid {
                        coupon["valid_from"] = validFrom.Time
                }
                if validUntil.Valid {
                        coupon["valid_until"] = validUntil.Time
                }
                if usageLimit.Valid {
                        coupon["usage_limit"] = usageLimit.Int64
                }
                if usedCount.Valid {
                        coupon["used_count"] = usedCount.Int64
                }

                coupons = append(coupons, coupon)
        }

        if coupons == nil {
                coupons = []map[string]interface{}{}
        }

        return c.JSON(coupons)
}

// ========== FILE UPLOAD HANDLERS ==========

func UploadPaymentProof(c *fiber.Ctx) error {
        file, err := c.FormFile("file")
        if err != nil {
                return ErrorResponse(c, "No file uploaded", fiber.StatusBadRequest)
        }

        // Create upload directory if not exists
        uploadDir := "./uploads/payment-proofs"
        os.MkdirAll(uploadDir, 0755)

        // Generate unique filename
        filename := fmt.Sprintf("%d_%s", time.Now().Unix(), file.Filename)
        filepath := fmt.Sprintf("%s/%s", uploadDir, filename)

        // Save file
        if err := c.SaveFile(file, filepath); err != nil {
                return ErrorResponse(c, "Failed to save file", fiber.StatusInternalServerError)
        }

        // Return file URL
        fileURL := fmt.Sprintf("/uploads/payment-proofs/%s", filename)
        return c.JSON(fiber.Map{
                "success": true,
                "message": "File uploaded successfully",
                "url":     fileURL,
        })
}

func UploadQRIS(c *fiber.Ctx) error {
        file, err := c.FormFile("file")
        if err != nil {
                return ErrorResponse(c, "No file uploaded", fiber.StatusBadRequest)
        }

        // Create upload directory if not exists
        uploadDir := "./uploads/qris"
        os.MkdirAll(uploadDir, 0755)

        // Generate unique filename
        filename := fmt.Sprintf("%d_%s", time.Now().Unix(), file.Filename)
        filepath := fmt.Sprintf("%s/%s", uploadDir, filename)

        // Save file
        if err := c.SaveFile(file, filepath); err != nil {
                return ErrorResponse(c, "Failed to save file", fiber.StatusInternalServerError)
        }

        // Return file URL
        fileURL := fmt.Sprintf("/uploads/qris/%s", filename)
        return c.JSON(fiber.Map{
                "success": true,
                "message": "QRIS file uploaded successfully",
                "url":     fileURL,
        })
}

// ========== QRIS & PAYMENT SETTINGS ==========

func GetQRISSettings(c *fiber.Ctx) error {
        var qrisURL sql.NullString
        err := DB.QueryRow("SELECT value FROM store_settings WHERE `key` = 'qris_image_url'").Scan(&qrisURL)

        if err == sql.ErrNoRows {
                return c.JSON(fiber.Map{
                        "qris_image_url": "",
                })
        }
        if err != nil {
                return ErrorResponse(c, "Failed to fetch QRIS settings", fiber.StatusInternalServerError)
        }

        url := ""
        if qrisURL.Valid {
                url = qrisURL.String
        }

        return c.JSON(fiber.Map{
                "qris_image_url": url,
        })
}

func UpdateQRISSettings(c *fiber.Ctx) error {
        var input struct {
                QRISImageURL string `json:"qris_image_url"`
        }

        if err := c.BodyParser(&input); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        _, err := DB.Exec(`
                INSERT INTO store_settings (` + "`key`" + `, value, updated_at)
                VALUES ('qris_image_url', ?, NOW())
                ON DUPLICATE KEY UPDATE value = ?, updated_at = NOW()
        `, input.QRISImageURL, input.QRISImageURL)

        if err != nil {
                return ErrorResponse(c, "Failed to update QRIS settings", fiber.StatusInternalServerError)
        }

        return c.JSON(fiber.Map{
                "success": true,
                "message": "QRIS settings updated successfully",
        })
}

func GenerateQRIS(c *fiber.Ctx) error {
        var input struct {
                Amount float64 `json:"amount"`
                OrderID string `json:"order_id"`
        }

        if err := c.BodyParser(&input); err != nil {
                return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
        }

        // For now, return a simple response
        // In production, integrate with actual QRIS provider
        return c.JSON(fiber.Map{
                "success": true,
                "message": "QRIS generated successfully",
                "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "amount":  input.Amount,
                "order_id": input.OrderID,
        })
}

