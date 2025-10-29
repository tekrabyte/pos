package main

import (
	"github.com/gofiber/fiber/v2"
)

func SetupRoutes(app *fiber.App) {
	// API group
	api := app.Group("/api")

	// Health check
	api.Get("/health", HealthCheck)

	// Authentication routes
	auth := api.Group("/auth")
	
	// Staff authentication
	staff := auth.Group("/staff")
	staff.Post("/login", StaffLogin)
	staff.Get("/me", AuthMiddleware, GetCurrentUser)
	staff.Post("/logout", AuthMiddleware, Logout)

	// Customer authentication
	customer := auth.Group("/customer")
	customer.Post("/register", CustomerRegister)
	customer.Post("/login", CustomerLogin)
	
	// Customer routes
	api.Post("/customer/change-password", AuthMiddleware, CustomerChangePassword)

	// Product management
	api.Get("/products", GetProducts)
	api.Get("/products/:id", GetProduct)
	api.Post("/products", AuthMiddleware, CreateProduct)
	api.Put("/products/:id", AuthMiddleware, UpdateProduct)
	api.Delete("/products/:id", AuthMiddleware, DeleteProduct)

	// Categories
	api.Get("/categories", GetCategories)
	api.Get("/categories/:id", GetCategory)
	api.Post("/categories", AuthMiddleware, CreateCategory)
	api.Put("/categories/:id", AuthMiddleware, UpdateCategory)
	api.Delete("/categories/:id", AuthMiddleware, DeleteCategory)

	// Brands
	api.Get("/brands", GetBrands)
	api.Get("/brands/:id", GetBrand)
	api.Post("/brands", AuthMiddleware, CreateBrand)
	api.Put("/brands/:id", AuthMiddleware, UpdateBrand)
	api.Delete("/brands/:id", AuthMiddleware, DeleteBrand)

	// Orders
	api.Get("/orders", GetOrders)
	api.Get("/orders/:id", GetOrder)
	api.Post("/orders", AuthMiddleware, CreateOrder)
	api.Put("/orders/:id", AuthMiddleware, UpdateOrder)
	api.Delete("/orders/:id", AuthMiddleware, DeleteOrder)
	api.Put("/orders/:id/status", AuthMiddleware, UpdateOrderStatus)

	// Tables
	api.Get("/tables", GetTables)
	api.Get("/tables/:id", GetTable)
	api.Get("/tables/token/:token", GetTableByToken)
	api.Post("/tables", AuthMiddleware, CreateTable)
	api.Put("/tables/:id", AuthMiddleware, UpdateTable)
	api.Delete("/tables/:id", AuthMiddleware, DeleteTable)
	api.Post("/tables/:id/regenerate-qr", AuthMiddleware, RegenerateTableQR)

	// Customers
	api.Get("/customers", GetCustomers)
	api.Get("/customers/:id", GetCustomer)
	api.Post("/customers", AuthMiddleware, CreateCustomer)
	api.Put("/customers/:id", AuthMiddleware, UpdateCustomer)
	api.Delete("/customers/:id", AuthMiddleware, DeleteCustomer)

	// Coupons
	api.Get("/coupons/available", GetAvailableCoupons)
	api.Get("/coupons", GetCoupons)
	api.Get("/coupons/:id", GetCoupon)
	api.Post("/coupons", AuthMiddleware, CreateCoupon)
	api.Put("/coupons/:id", AuthMiddleware, UpdateCoupon)
	api.Delete("/coupons/:id", AuthMiddleware, DeleteCoupon)

	// Outlets
	api.Get("/outlets", GetOutlets)
	api.Get("/outlets/:id", GetOutlet)
	api.Post("/outlets", AuthMiddleware, CreateOutlet)
	api.Put("/outlets/:id", AuthMiddleware, UpdateOutlet)
	api.Delete("/outlets/:id", AuthMiddleware, DeleteOutlet)

	// Payment Methods
	api.Get("/payment-methods", GetPaymentMethods)
	api.Get("/payment-methods/:id", GetPaymentMethod)
	api.Post("/payment-methods", AuthMiddleware, CreatePaymentMethod)
	api.Put("/payment-methods/:id", AuthMiddleware, UpdatePaymentMethod)
	api.Delete("/payment-methods/:id", AuthMiddleware, DeletePaymentMethod)

	// Dashboard & Analytics
	api.Get("/dashboard/stats", AuthMiddleware, GetDashboardStats)
	api.Get("/analytics", AuthMiddleware, GetAnalytics)

	// Roles
	api.Get("/roles", GetRoles)
	api.Get("/roles/:id", GetRole)
	api.Post("/roles", AuthMiddleware, CreateRole)
	api.Put("/roles/:id", AuthMiddleware, UpdateRole)
	api.Delete("/roles/:id", AuthMiddleware, DeleteRole)

	// Bank Accounts
	api.Get("/bank-accounts", GetBankAccounts)
	api.Get("/bank-accounts/:id", GetBankAccount)
	api.Post("/bank-accounts", AuthMiddleware, CreateBankAccount)
	api.Put("/bank-accounts/:id", AuthMiddleware, UpdateBankAccount)
	api.Delete("/bank-accounts/:id", AuthMiddleware, DeleteBankAccount)

	// Store Settings
	api.Get("/store-settings", GetStoreSettings)
	api.Post("/store-settings", AuthMiddleware, UpdateStoreSettings)
	api.Put("/store-settings", AuthMiddleware, UpdateStoreSettings)

	// Store Banners
	api.Get("/store-banners", GetStoreBanners)
	api.Get("/store-banners/:id", GetStoreBanner)
	api.Post("/store-banners", AuthMiddleware, CreateStoreBanner)
	api.Put("/store-banners/:id", AuthMiddleware, UpdateStoreBanner)
	api.Delete("/store-banners/:id", AuthMiddleware, DeleteStoreBanner)

	// Coupons - Available
	api.Get("/coupons/available", GetAvailableCoupons)

	// File Uploads
	api.Post("/upload/payment-proof", UploadPaymentProof)
	api.Post("/upload/qris", UploadQRIS)

	// QRIS & Payment Settings
	api.Get("/payment-settings/qris", GetQRISSettings)
	api.Post("/payment-settings/qris", AuthMiddleware, UpdateQRISSettings)
	api.Post("/qris/generate", GenerateQRIS)
}
