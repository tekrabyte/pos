package main

import (
	"database/sql"
	"time"
)

type User struct {
	ID        int            `json:"id"`
	FullName  sql.NullString `json:"full_name"`
	Username  string         `json:"username"`
	Email     sql.NullString `json:"email"`
	Password  string         `json:"-"`
	Role      sql.NullString `json:"role"`
	RoleID    sql.NullInt64  `json:"role_id"`
	OutletID  sql.NullInt64  `json:"outlet_id"`
	IsActive  sql.NullBool   `json:"is_active"`
	CreatedAt sql.NullTime   `json:"created_at"`
}

type Product struct {
	ID           int            `json:"id"`
	Name         string         `json:"name"`
	SKU          sql.NullString `json:"sku"`
	Price        float64        `json:"price"`
	Stock        int            `json:"stock"`
	CategoryID   sql.NullInt64  `json:"category_id"`
	BrandID      sql.NullInt64  `json:"brand_id"`
	Description  sql.NullString `json:"description"`
	ImageURL     sql.NullString `json:"image_url"`
	Status       sql.NullString `json:"status"`
	IsBundle     sql.NullBool   `json:"is_bundle"`
	BundleItems  sql.NullString `json:"bundle_items"` // JSON string
	HasPortions  sql.NullBool   `json:"has_portions"`
	Unit         sql.NullString `json:"unit"`
	PortionSize  sql.NullFloat64 `json:"portion_size"`
	CreatedAt    sql.NullTime   `json:"created_at"`
	UpdatedAt    sql.NullTime   `json:"updated_at"`
}

type Category struct {
	ID          int            `json:"id"`
	Name        string         `json:"name"`
	Description sql.NullString `json:"description"`
	ParentID    sql.NullInt64  `json:"parent_id"`
	CreatedAt   sql.NullTime   `json:"created_at"`
}

type Brand struct {
	ID          int            `json:"id"`
	Name        string         `json:"name"`
	Description sql.NullString `json:"description"`
	LogoURL     sql.NullString `json:"logo_url"`
	CreatedAt   sql.NullTime   `json:"created_at"`
}

type Order struct {
	ID               int            `json:"id"`
	OrderNumber      string         `json:"order_number"`
	CustomerID       sql.NullInt64  `json:"customer_id"`
	TableID          sql.NullInt64  `json:"table_id"`
	OrderType        sql.NullString `json:"order_type"`
	CustomerName     sql.NullString `json:"customer_name"`
	CustomerPhone    sql.NullString `json:"customer_phone"`
	OutletID         sql.NullInt64  `json:"outlet_id"`
	UserID           sql.NullInt64  `json:"user_id"`
	TotalAmount      float64        `json:"total_amount"`
	PaymentMethod    sql.NullString `json:"payment_method"`
	PaymentProof     sql.NullString `json:"payment_proof"`
	PaymentVerified  sql.NullBool   `json:"payment_verified"`
	Status           sql.NullString `json:"status"`
	CreatedAt        sql.NullTime   `json:"created_at"`
	CouponID         sql.NullInt64  `json:"coupon_id"`
	CouponCode       sql.NullString `json:"coupon_code"`
	DiscountAmount   sql.NullFloat64 `json:"discount_amount"`
	OriginalAmount   sql.NullFloat64 `json:"original_amount"`
	EstimatedTime    sql.NullInt64  `json:"estimated_time"`
	CompletedAt      sql.NullTime   `json:"completed_at"`
}

type Table struct {
	ID        int            `json:"id"`
	Name      string         `json:"name"`
	Token     string         `json:"token"`
	QRCode    sql.NullString `json:"qr_code"`
	Status    string         `json:"status"`
	OutletID  sql.NullInt64  `json:"outlet_id"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"updated_at"`
}

type Customer struct {
	ID          int            `json:"id"`
	Name        string         `json:"name"`
	Email       sql.NullString `json:"email"`
	Phone       sql.NullString `json:"phone"`
	Address     sql.NullString `json:"address"`
	Points      int            `json:"points"`
	CreatedAt   time.Time      `json:"created_at"`
	UpdatedAt   time.Time      `json:"updated_at"`
}

type Coupon struct {
	ID             int            `json:"id"`
	Code           string         `json:"code"`
	Type           string         `json:"type"`
	Value          float64        `json:"value"`
	MinPurchase    float64        `json:"min_purchase"`
	MaxDiscount    sql.NullFloat64 `json:"max_discount"`
	StartDate      sql.NullTime   `json:"start_date"`
	EndDate        sql.NullTime   `json:"end_date"`
	UsageLimit     sql.NullInt64  `json:"usage_limit"`
	UsageCount     int            `json:"usage_count"`
	IsActive       bool           `json:"is_active"`
	CreatedAt      time.Time      `json:"created_at"`
	UpdatedAt      time.Time      `json:"updated_at"`
}

type Outlet struct {
	ID        int            `json:"id"`
	Name      string         `json:"name"`
	Address   sql.NullString `json:"address"`
	Phone     sql.NullString `json:"phone"`
	IsActive  bool           `json:"is_active"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"updated_at"`
}

type PaymentMethod struct {
	ID        int            `json:"id"`
	Name      string         `json:"name"`
	Type      string         `json:"type"`
	IsActive  bool           `json:"is_active"`
	Config    sql.NullString `json:"config"`
	CreatedAt sql.NullTime   `json:"created_at"`
}

type Role struct {
	ID          int       `json:"id"`
	Name        string    `json:"name"`
	MaxDiscount float64   `json:"max_discount"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

type BankAccount struct {
	ID            int            `json:"id"`
	BankName      string         `json:"bank_name"`
	AccountNumber string         `json:"account_number"`
	AccountName   string         `json:"account_name"`
	IsActive      bool           `json:"is_active"`
	CreatedAt     time.Time      `json:"created_at"`
	UpdatedAt     time.Time      `json:"updated_at"`
}

type StoreSetting struct {
	ID        int            `json:"id"`
	Key       string         `json:"key"`
	Value     sql.NullString `json:"value"`
	UpdatedAt time.Time      `json:"updated_at"`
}

type StoreBanner struct {
	ID        int            `json:"id"`
	Title     sql.NullString `json:"title"`
	ImageURL  string         `json:"image_url"`
	Link      sql.NullString `json:"link"`
	IsActive  bool           `json:"is_active"`
	Order     int            `json:"order"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"updated_at"`
}

type CustomerAuth struct {
	ID        int            `json:"id"`
	Name      string         `json:"name"`
	Email     string         `json:"email"`
	Phone     sql.NullString `json:"phone"`
	Password  string         `json:"-"`
	Points    int            `json:"points"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"updated_at"`
}
