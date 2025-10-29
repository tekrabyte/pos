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
	ID          int            `json:"id"`
	Name        string         `json:"name"`
	SKU         sql.NullString `json:"sku"`
	Description sql.NullString `json:"description"`
	Price       float64        `json:"price"`
	Cost        float64        `json:"cost"`
	Stock       int            `json:"stock"`
	CategoryID  sql.NullInt64  `json:"category_id"`
	BrandID     sql.NullInt64  `json:"brand_id"`
	Image       sql.NullString `json:"image"`
	IsActive    bool           `json:"is_active"`
	CreatedAt   time.Time      `json:"created_at"`
	UpdatedAt   time.Time      `json:"updated_at"`
}

type Category struct {
	ID        int       `json:"id"`
	Name      string    `json:"name"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type Brand struct {
	ID        int       `json:"id"`
	Name      string    `json:"name"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type Order struct {
	ID              int            `json:"id"`
	OrderNumber     string         `json:"order_number"`
	CustomerID      sql.NullInt64  `json:"customer_id"`
	TableID         sql.NullInt64  `json:"table_id"`
	TotalAmount     float64        `json:"total_amount"`
	DiscountAmount  float64        `json:"discount_amount"`
	TaxAmount       float64        `json:"tax_amount"`
	FinalAmount     float64        `json:"final_amount"`
	Status          string         `json:"status"`
	PaymentMethod   sql.NullString `json:"payment_method"`
	PaymentStatus   string         `json:"payment_status"`
	Notes           sql.NullString `json:"notes"`
	CreatedBy       sql.NullInt64  `json:"created_by"`
	CreatedAt       time.Time      `json:"created_at"`
	UpdatedAt       time.Time      `json:"updated_at"`
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
	ID        int       `json:"id"`
	Name      string    `json:"name"`
	Type      string    `json:"type"`
	IsActive  bool      `json:"is_active"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}
