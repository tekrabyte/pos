package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"

	"github.com/gofiber/fiber/v2"
)

// Xendit API Base URL
const XenditBaseURL = "https://api.xendit.co"

// Xendit request/response structs
type QRISPaymentRequest struct {
	Amount      float64 `json:"amount"`
	OrderID     *int    `json:"order_id"`
	ChannelID   string  `json:"channel_id"`
	CustomerName string  `json:"customer_name"`
}

type VirtualAccountRequest struct {
	Amount       float64 `json:"amount"`
	BankCode     string  `json:"bank_code"`
	OrderID      *int    `json:"order_id"`
	ChannelID    string  `json:"channel_id"`
	CustomerName string  `json:"customer_name"`
}

type EWalletRequest struct {
	Amount       float64 `json:"amount"`
	WalletType   string  `json:"wallet_type"`
	OrderID      *int    `json:"order_id"`
	ChannelID    string  `json:"channel_id"`
	SuccessURL   string  `json:"success_url"`
	FailureURL   string  `json:"failure_url"`
}

// CreateQRISPayment creates a QRIS payment via Xendit Invoice API
func CreateQRISPayment(c *fiber.Ctx) error {
	var req QRISPaymentRequest
	if err := c.BodyParser(&req); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	// Generate reference ID
	referenceID := fmt.Sprintf("qris_%s_%d", req.ChannelID, time.Now().UnixNano())

	// Create Xendit Invoice
	invoiceData := map[string]interface{}{
		"external_id":      referenceID,
		"amount":           int(req.Amount),
		"payer_email":      "customer@pos-system.com",
		"description":      fmt.Sprintf("Payment for order %s", referenceID),
		"invoice_duration": 86400, // 24 hours
		"currency":         "IDR",
		"payment_methods":  []string{"QRIS"},
	}

	jsonData, _ := json.Marshal(invoiceData)
	
	httpReq, err := http.NewRequest("POST", XenditBaseURL+"/v2/invoices", bytes.NewBuffer(jsonData))
	if err != nil {
		return ErrorResponse(c, "Failed to create request", fiber.StatusInternalServerError)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.SetBasicAuth(os.Getenv("XENDIT_API_KEY"), "")

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(httpReq)
	if err != nil {
		return ErrorResponse(c, fmt.Sprintf("Xendit API error: %v", err), fiber.StatusInternalServerError)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	
	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		return ErrorResponse(c, fmt.Sprintf("Xendit error: %s", string(body)), fiber.StatusInternalServerError)
	}

	var result map[string]interface{}
	json.Unmarshal(body, &result)

	// Store payment in database
	_, err = DB.Exec(`
		INSERT INTO xendit_payments 
		(reference_id, payment_id, payment_type, channel_code, amount, status, order_id, 
		 customer_name, channel_id, metadata, created_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())
	`, referenceID, result["id"], "qris", "QRIS", req.Amount, result["status"], 
	   req.OrderID, req.CustomerName, req.ChannelID, string(body))

	if err != nil {
		fmt.Printf("Failed to store payment: %v\n", err)
	}

	return c.JSON(fiber.Map{
		"success":      true,
		"payment_id":   result["id"],
		"reference_id": referenceID,
		"qr_string":    result["invoice_url"],
		"status":       result["status"],
		"amount":       req.Amount,
	})
}

// CreateVirtualAccountPayment creates a Virtual Account payment
func CreateVirtualAccountPayment(c *fiber.Ctx) error {
	var req VirtualAccountRequest
	if err := c.BodyParser(&req); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	referenceID := fmt.Sprintf("va_%s_%d", req.BankCode, time.Now().UnixNano())

	// Create Xendit Fixed Virtual Account
	vaData := map[string]interface{}{
		"external_id":     referenceID,
		"bank_code":       req.BankCode,
		"name":            req.CustomerName,
		"expected_amount": int(req.Amount),
		"is_closed":       true,
		"is_single_use":   true,
	}

	jsonData, _ := json.Marshal(vaData)
	
	httpReq, err := http.NewRequest("POST", XenditBaseURL+"/callback_virtual_accounts", bytes.NewBuffer(jsonData))
	if err != nil {
		return ErrorResponse(c, "Failed to create request", fiber.StatusInternalServerError)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.SetBasicAuth(os.Getenv("XENDIT_API_KEY"), "")

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(httpReq)
	if err != nil {
		return ErrorResponse(c, fmt.Sprintf("Xendit API error: %v", err), fiber.StatusInternalServerError)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	
	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		return ErrorResponse(c, fmt.Sprintf("Xendit error: %s", string(body)), fiber.StatusInternalServerError)
	}

	var result map[string]interface{}
	json.Unmarshal(body, &result)

	// Store payment in database
	_, err = DB.Exec(`
		INSERT INTO xendit_payments 
		(reference_id, payment_id, payment_type, channel_code, amount, status, order_id, 
		 customer_name, channel_id, metadata, created_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())
	`, referenceID, result["id"], "virtual_account", req.BankCode, req.Amount, result["status"],
	   req.OrderID, req.CustomerName, req.ChannelID, string(body))

	if err != nil {
		fmt.Printf("Failed to store payment: %v\n", err)
	}

	bankNames := map[string]string{
		"BCA":     "Bank Central Asia",
		"BNI":     "Bank Negara Indonesia",
		"BRI":     "Bank Rakyat Indonesia",
		"MANDIRI": "Bank Mandiri",
		"PERMATA": "Bank Permata",
	}

	return c.JSON(fiber.Map{
		"success":        true,
		"payment_id":     result["id"],
		"reference_id":   referenceID,
		"account_number": result["account_number"],
		"bank_code":      req.BankCode,
		"bank_name":      bankNames[req.BankCode],
		"status":         result["status"],
		"amount":         req.Amount,
	})
}

// CreateEWalletPayment creates an E-wallet payment
func CreateEWalletPayment(c *fiber.Ctx) error {
	var req EWalletRequest
	if err := c.BodyParser(&req); err != nil {
		return ErrorResponse(c, "Invalid request body", fiber.StatusBadRequest)
	}

	referenceID := fmt.Sprintf("ewallet_%s_%d", req.WalletType, time.Now().UnixNano())

	// Create Xendit E-wallet Charge
	ewalletData := map[string]interface{}{
		"reference_id": referenceID,
		"currency":     "IDR",
		"amount":       int(req.Amount),
		"checkout_method": "ONE_TIME_PAYMENT",
		"channel_code": req.WalletType,
		"channel_properties": map[string]string{
			"success_redirect_url": req.SuccessURL,
			"failure_redirect_url": req.FailureURL,
		},
	}

	jsonData, _ := json.Marshal(ewalletData)
	
	httpReq, err := http.NewRequest("POST", XenditBaseURL+"/ewallets/charges", bytes.NewBuffer(jsonData))
	if err != nil {
		return ErrorResponse(c, "Failed to create request", fiber.StatusInternalServerError)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.SetBasicAuth(os.Getenv("XENDIT_API_KEY"), "")

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(httpReq)
	if err != nil {
		return ErrorResponse(c, fmt.Sprintf("Xendit API error: %v", err), fiber.StatusInternalServerError)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	
	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		return ErrorResponse(c, fmt.Sprintf("Xendit error: %s", string(body)), fiber.StatusInternalServerError)
	}

	var result map[string]interface{}
	json.Unmarshal(body, &result)

	// Store payment in database
	_, err = DB.Exec(`
		INSERT INTO xendit_payments 
		(reference_id, payment_id, payment_type, channel_code, amount, status, order_id, 
		 customer_name, channel_id, metadata, created_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())
	`, referenceID, result["id"], "ewallet", req.WalletType, req.Amount, result["status"],
	   req.OrderID, req.CustomerName, req.ChannelID, string(body))

	if err != nil {
		fmt.Printf("Failed to store payment: %v\n", err)
	}

	// Get redirect URL from actions
	var redirectURL string
	if actions, ok := result["actions"].(map[string]interface{}); ok {
		if url, ok := actions["desktop_web_checkout_url"].(string); ok {
			redirectURL = url
		}
	}

	return c.JSON(fiber.Map{
		"success":      true,
		"payment_id":   result["id"],
		"reference_id": referenceID,
		"redirect_url": redirectURL,
		"status":       result["status"],
		"amount":       req.Amount,
		"wallet_type":  req.WalletType,
	})
}

// GetPaymentStatus gets payment status from database
func GetPaymentStatus(c *fiber.Ctx) error {
	paymentID := c.Params("id")

	var payment struct {
		ID           int     `json:"id"`
		PaymentID    string  `json:"payment_id"`
		ReferenceID  string  `json:"reference_id"`
		PaymentType  string  `json:"payment_type"`
		ChannelCode  string  `json:"channel_code"`
		Amount       float64 `json:"amount"`
		Status       string  `json:"status"`
		OrderID      *int    `json:"order_id"`
		CustomerName string  `json:"customer_name"`
		Metadata     string  `json:"metadata"`
		CreatedAt    time.Time `json:"created_at"`
	}

	err := DB.QueryRow(`
		SELECT id, payment_id, reference_id, payment_type, channel_code, amount, status, 
		       order_id, customer_name, metadata, created_at
		FROM xendit_payments 
		WHERE payment_id = ? OR reference_id = ?
	`, paymentID, paymentID).Scan(
		&payment.ID, &payment.PaymentID, &payment.ReferenceID, &payment.PaymentType,
		&payment.ChannelCode, &payment.Amount, &payment.Status, &payment.OrderID,
		&payment.CustomerName, &payment.Metadata, &payment.CreatedAt,
	)

	if err == sql.ErrNoRows {
		return ErrorResponse(c, "Payment not found", fiber.StatusNotFound)
	}
	if err != nil {
		return ErrorResponse(c, fmt.Sprintf("Database error: %v", err), fiber.StatusInternalServerError)
	}

	return c.JSON(fiber.Map{
		"success": true,
		"payment": payment,
	})
}

// XenditWebhook handles webhook callbacks from Xendit
func XenditWebhook(c *fiber.Ctx) error {
	// Verify webhook token
	token := c.Get("x-callback-token")
	expectedToken := os.Getenv("XENDIT_WEBHOOK_TOKEN")
	
	if token != expectedToken {
		fmt.Printf("Webhook token mismatch\n")
		return ErrorResponse(c, "Unauthorized", fiber.StatusUnauthorized)
	}

	// Parse webhook data
	var data map[string]interface{}
	if err := c.BodyParser(&data); err != nil {
		return ErrorResponse(c, "Invalid payload", fiber.StatusBadRequest)
	}

	fmt.Printf("Xendit webhook received: %+v\n", data)

	// Extract IDs
	externalID := ""
	if val, ok := data["external_id"].(string); ok {
		externalID = val
	} else if val, ok := data["reference_id"].(string); ok {
		externalID = val
	}

	paymentID := ""
	if val, ok := data["id"].(string); ok {
		paymentID = val
	}

	status := "PENDING"
	if val, ok := data["status"].(string); ok {
		status = val
	}

	paidAmount := 0.0
	if val, ok := data["paid_amount"].(float64); ok {
		paidAmount = val
	} else if val, ok := data["amount"].(float64); ok {
		paidAmount = val
	}

	// Update payment in database
	if externalID != "" {
		_, err := DB.Exec(`
			UPDATE xendit_payments 
			SET status = ?, paid_amount = ?,
			    paid_at = CASE WHEN ? IN ('PAID', 'SETTLED', 'COMPLETED') THEN NOW() ELSE paid_at END,
			    updated_at = NOW()
			WHERE reference_id = ? OR payment_id = ?
		`, status, paidAmount, status, externalID, paymentID)

		if err != nil {
			fmt.Printf("Failed to update payment: %v\n", err)
		}

		// Update order if payment successful
		if status == "PAID" || status == "SETTLED" || status == "COMPLETED" {
			_, err = DB.Exec(`
				UPDATE orders o
				JOIN xendit_payments xp ON o.id = xp.order_id
				SET o.payment_verified = TRUE, o.status = 'confirmed'
				WHERE xp.reference_id = ? OR xp.payment_id = ?
			`, externalID, paymentID)

			if err != nil {
				fmt.Printf("Failed to update order: %v\n", err)
			}
		}
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Webhook processed",
	})
}
