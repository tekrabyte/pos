-- Migration: Add bundle and portion support to products table

-- Add is_bundle column (whether this product is a bundle/paket)
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS is_bundle BOOLEAN DEFAULT FALSE AFTER status;

-- Add bundle_items column (JSON array of {product_id, quantity})
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS bundle_items JSON DEFAULT NULL AFTER is_bundle;

-- Add has_portions column (whether this product is sold by portions/porsi)
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS has_portions BOOLEAN DEFAULT FALSE AFTER bundle_items;

-- Add unit column (satuan: kg, pcs, liter, porsi, etc.)
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS unit VARCHAR(50) DEFAULT 'pcs' AFTER has_portions;

-- Add portion_size column (size of one portion in base unit)
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS portion_size DECIMAL(10,2) DEFAULT 1.00 AFTER unit;

-- Update existing products to have default values
UPDATE products 
SET is_bundle = FALSE, has_portions = FALSE, unit = 'pcs', portion_size = 1.00 
WHERE is_bundle IS NULL OR has_portions IS NULL OR unit IS NULL;
