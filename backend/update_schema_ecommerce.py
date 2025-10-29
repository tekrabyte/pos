import aiomysql
import asyncio
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def update_database_schema():
    """Update database schema for e-commerce features"""
    
    connection = await aiomysql.connect(
        host=os.environ.get('MYSQL_HOST', 'localhost'),
        port=int(os.environ.get('MYSQL_PORT', 3306)),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', ''),
        db=os.environ.get('MYSQL_DB', 'pos_db'),
        autocommit=True
    )
    
    try:
        async with connection.cursor() as cursor:
            print("🔄 Updating database schema for e-commerce features...")
            
            # 1. Add password reset fields to customers table
            print("1. Adding password reset fields to customers...")
            await cursor.execute("""
                ALTER TABLE customers 
                ADD COLUMN IF NOT EXISTS password_reset_token VARCHAR(100) NULL,
                ADD COLUMN IF NOT EXISTS password_reset_expires DATETIME NULL,
                ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE
            """)
            
            # 2. Create store_settings table
            print("2. Creating store_settings table...")
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS store_settings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    store_name VARCHAR(255) NOT NULL DEFAULT 'QR Scan & Dine',
                    store_description TEXT,
                    banner_url VARCHAR(500),
                    logo_url VARCHAR(500),
                    address TEXT,
                    phone VARCHAR(20),
                    email VARCHAR(100),
                    rating DECIMAL(2,1) DEFAULT 4.5,
                    total_reviews INT DEFAULT 0,
                    opening_hours TEXT,
                    is_open BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default store settings
            await cursor.execute("""
                INSERT INTO store_settings (store_name, store_description, rating, total_reviews)
                SELECT 'QR Scan & Dine', 'Restoran modern dengan sistem pemesanan digital', 4.5, 127
                WHERE NOT EXISTS (SELECT 1 FROM store_settings LIMIT 1)
            """)
            
            # 3. Update coupons table structure
            print("3. Updating coupons table...")
            await cursor.execute("""
                ALTER TABLE coupons
                ADD COLUMN IF NOT EXISTS discount_type ENUM('percentage', 'nominal') DEFAULT 'percentage',
                ADD COLUMN IF NOT EXISTS discount_value DECIMAL(10,2) DEFAULT 0,
                ADD COLUMN IF NOT EXISTS min_purchase DECIMAL(10,2) DEFAULT 0,
                ADD COLUMN IF NOT EXISTS max_discount DECIMAL(10,2) NULL,
                ADD COLUMN IF NOT EXISTS usage_limit INT DEFAULT 0,
                ADD COLUMN IF NOT EXISTS used_count INT DEFAULT 0,
                ADD COLUMN IF NOT EXISTS start_date DATETIME NULL,
                ADD COLUMN IF NOT EXISTS end_date DATETIME NULL,
                ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE
            """)
            
            # Update existing coupons with default values
            await cursor.execute("""
                UPDATE coupons 
                SET discount_type = 'percentage', 
                    discount_value = 10,
                    is_active = TRUE
                WHERE discount_value = 0 OR discount_value IS NULL
            """)
            
            # 4. Create order_ratings table
            print("4. Creating order_ratings table...")
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_ratings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    order_id INT NOT NULL,
                    customer_id INT NOT NULL,
                    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
                    review TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_order_rating (order_id)
                )
            """)
            
            # 5. Add coupon fields to orders table
            print("5. Adding coupon fields to orders...")
            await cursor.execute("""
                ALTER TABLE orders
                ADD COLUMN IF NOT EXISTS coupon_id INT NULL,
                ADD COLUMN IF NOT EXISTS coupon_code VARCHAR(50) NULL,
                ADD COLUMN IF NOT EXISTS discount_amount DECIMAL(10,2) DEFAULT 0,
                ADD COLUMN IF NOT EXISTS original_amount DECIMAL(10,2) NULL
            """)
            
            # 6. Add tracking fields to orders
            print("6. Adding tracking fields to orders...")
            await cursor.execute("""
                ALTER TABLE orders
                ADD COLUMN IF NOT EXISTS estimated_time INT DEFAULT 30 COMMENT 'Estimated time in minutes',
                ADD COLUMN IF NOT EXISTS completed_at DATETIME NULL
            """)
            
            # 7. Create store_banners table for promotional banners
            print("7. Creating store_banners table...")
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS store_banners (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    subtitle VARCHAR(255),
                    image_url VARCHAR(500),
                    link_url VARCHAR(500),
                    button_text VARCHAR(50),
                    display_order INT DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default banners
            await cursor.execute("""
                INSERT INTO store_banners (title, subtitle, image_url, button_text, display_order, is_active)
                SELECT * FROM (
                    SELECT 'Promo Spesial Hari Ini!' as title, 
                           'Diskon hingga 50% untuk menu pilihan' as subtitle,
                           'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800' as image_url,
                           'Pesan Sekarang' as button_text,
                           1 as display_order,
                           TRUE as is_active
                    UNION ALL
                    SELECT 'Menu Baru Tersedia!',
                           'Coba menu spesial chef kami',
                           'https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=800',
                           'Lihat Menu',
                           2,
                           TRUE
                    UNION ALL
                    SELECT 'Gratis Ongkir',
                           'Untuk pembelian minimal Rp 50.000',
                           'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800',
                           'Order Sekarang',
                           3,
                           TRUE
                ) as temp
                WHERE NOT EXISTS (SELECT 1 FROM store_banners LIMIT 1)
            """)
            
            # 8. Add sample coupons if none exist
            print("8. Adding sample coupons...")
            await cursor.execute("SELECT COUNT(*) as count FROM coupons")
            result = await cursor.fetchone()
            
            if result[0] == 0:
                await cursor.execute("""
                    INSERT INTO coupons (code, description, discount_type, discount_value, min_purchase, max_discount, usage_limit, is_active, start_date, end_date)
                    VALUES 
                    ('WELCOME10', 'Diskon 10% untuk pelanggan baru', 'percentage', 10.00, 30000, 50000, 100, TRUE, NOW(), DATE_ADD(NOW(), INTERVAL 30 DAY)),
                    ('HEMAT20K', 'Potongan Rp 20.000 untuk pembelian min Rp 100.000', 'nominal', 20000, 100000, NULL, 50, TRUE, NOW(), DATE_ADD(NOW(), INTERVAL 30 DAY)),
                    ('SPESIAL25', 'Diskon spesial 25% max Rp 75.000', 'percentage', 25.00, 50000, 75000, 30, TRUE, NOW(), DATE_ADD(NOW(), INTERVAL 7 DAY))
                """)
            
            print("✅ Database schema updated successfully!")
            print("\n📊 Summary:")
            print("  - Added password reset fields to customers table")
            print("  - Created store_settings table with default data")
            print("  - Updated coupons table with discount types")
            print("  - Created order_ratings table")
            print("  - Added coupon fields to orders table")
            print("  - Added tracking fields to orders table")
            print("  - Created store_banners table with default banners")
            print("  - Added sample coupons (if none existed)")
            
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        raise
    finally:
        connection.close()

if __name__ == "__main__":
    asyncio.run(update_database_schema())
