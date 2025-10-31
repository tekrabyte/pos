-- Xendit Payments Table Migration
-- Creates tables for Xendit payment integration

-- Create xendit_payments table
CREATE TABLE IF NOT EXISTS xendit_payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reference_id VARCHAR(255) UNIQUE NOT NULL,
    payment_id VARCHAR(255) NOT NULL,
    payment_type ENUM('qris', 'virtual_account', 'ewallet') NOT NULL,
    channel_code VARCHAR(50) NOT NULL COMMENT 'QRIS, BCA, BNI, OVO, etc',
    amount DECIMAL(15, 2) NOT NULL,
    paid_amount DECIMAL(15, 2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'PENDING',
    order_id INT NULL,
    customer_name VARCHAR(255) NULL,
    channel_id VARCHAR(50) DEFAULT 'pos_main' COMMENT 'pos_main, dine_in, takeaway',
    metadata TEXT NULL COMMENT 'JSON data with QR string, VA number, etc',
    webhook_data TEXT NULL COMMENT 'Raw webhook data',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_reference_id (reference_id),
    INDEX idx_payment_id (payment_id),
    INDEX idx_order_id (order_id),
    INDEX idx_status (status),
    INDEX idx_channel_id (channel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Update payment_methods table to support channel-specific configuration
ALTER TABLE payment_methods 
ADD COLUMN IF NOT EXISTS channel_id VARCHAR(50) DEFAULT 'all' COMMENT 'all, pos_main, dine_in, takeaway';

ALTER TABLE payment_methods 
ADD COLUMN IF NOT EXISTS channel_code VARCHAR(50) NULL COMMENT 'Xendit channel code';

ALTER TABLE payment_methods 
ADD COLUMN IF NOT EXISTS display_name VARCHAR(255) NULL;

ALTER TABLE payment_methods 
ADD COLUMN IF NOT EXISTS display_order INT DEFAULT 0;

ALTER TABLE payment_methods 
ADD COLUMN IF NOT EXISTS min_amount DECIMAL(15, 2) DEFAULT 1000;

ALTER TABLE payment_methods 
ADD COLUMN IF NOT EXISTS max_amount DECIMAL(15, 2) DEFAULT 10000000;

ALTER TABLE payment_methods 
ADD COLUMN IF NOT EXISTS icon_url VARCHAR(512) NULL;

-- Add Xendit settings table
CREATE TABLE IF NOT EXISTS xendit_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT NULL,
    description TEXT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default Xendit settings
INSERT INTO xendit_settings (setting_key, setting_value, description) VALUES
('xendit_enabled', 'true', 'Enable/disable Xendit payment gateway'),
('xendit_environment', 'development', 'Xendit environment (development/production)')
ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value);

-- Insert default payment methods for Xendit
INSERT INTO payment_methods (name, type, channel_code, display_name, is_active, channel_id, display_order, min_amount, max_amount, config) VALUES
('QRIS', 'qris', 'QRIS', 'QRIS (Scan & Pay)', TRUE, 'all', 1, 1000, 10000000, '{"provider":"xendit"}'),
('Bank Transfer BCA', 'virtual_account', 'BCA', 'Transfer Bank BCA', TRUE, 'all', 2, 10000, 50000000, '{"provider":"xendit"}'),
('Bank Transfer BNI', 'virtual_account', 'BNI', 'Transfer Bank BNI', TRUE, 'all', 3, 10000, 50000000, '{"provider":"xendit"}'),
('Bank Transfer BRI', 'virtual_account', 'BRI', 'Transfer Bank BRI', TRUE, 'all', 4, 10000, 50000000, '{"provider":"xendit"}'),
('Bank Transfer Mandiri', 'virtual_account', 'MANDIRI', 'Transfer Bank Mandiri', TRUE, 'all', 5, 10000, 50000000, '{"provider":"xendit"}'),
('OVO', 'ewallet', 'OVO', 'OVO E-wallet', TRUE, 'all', 6, 10000, 10000000, '{"provider":"xendit"}'),
('DANA', 'ewallet', 'DANA', 'DANA E-wallet', TRUE, 'all', 7, 10000, 10000000, '{"provider":"xendit"}'),
('LinkAja', 'ewallet', 'LINKAJA', 'LinkAja E-wallet', TRUE, 'all', 8, 10000, 10000000, '{"provider":"xendit"}'),
('ShopeePay', 'ewallet', 'SHOPEEPAY', 'ShopeePay', TRUE, 'all', 9, 10000, 10000000, '{"provider":"xendit"}'),
('Cash', 'cash', 'CASH', 'Tunai', TRUE, 'pos_main', 10, 0, 999999999, '{"provider":"internal"}')
ON DUPLICATE KEY UPDATE 
    display_name = VALUES(display_name),
    channel_code = VALUES(channel_code),
    display_order = VALUES(display_order);

-- Add payment verification status to orders table if not exists
ALTER TABLE orders 
ADD COLUMN IF NOT EXISTS xendit_payment_id VARCHAR(255) NULL AFTER payment_proof;

ALTER TABLE orders
ADD INDEX IF NOT EXISTS idx_xendit_payment (xendit_payment_id);
