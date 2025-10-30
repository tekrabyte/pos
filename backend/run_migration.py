#!/usr/bin/env python3
"""
Database Migration Script - Add Bundle and Portion Support
"""
import pymysql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Database connection
db_config = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
}

print("🚀 Starting database migrations...")
print(f"Connecting to {db_config['host']}:{db_config['port']} as {db_config['user']}")

try:
    # Connect to database
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()
    
    print("✅ Connected to database")
    
    # Migration queries
    migrations = [
        ("is_bundle", "ALTER TABLE products ADD COLUMN is_bundle BOOLEAN DEFAULT FALSE AFTER status"),
        ("bundle_items", "ALTER TABLE products ADD COLUMN bundle_items TEXT DEFAULT NULL AFTER is_bundle"),
        ("has_portions", "ALTER TABLE products ADD COLUMN has_portions BOOLEAN DEFAULT FALSE AFTER bundle_items"),
        ("unit", "ALTER TABLE products ADD COLUMN unit VARCHAR(50) DEFAULT 'pcs' AFTER has_portions"),
        ("portion_size", "ALTER TABLE products ADD COLUMN portion_size DECIMAL(10,2) DEFAULT 1.00 AFTER unit"),
    ]
    
    # Run migrations
    for column_name, query in migrations:
        try:
            cursor.execute(query)
            connection.commit()
            print(f"✅ Added column: {column_name}")
        except pymysql.err.OperationalError as e:
            if "Duplicate column name" in str(e):
                print(f"✓ Column {column_name} already exists (skipped)")
            else:
                print(f"⚠️  Error adding {column_name}: {e}")
        except Exception as e:
            print(f"⚠️  Error adding {column_name}: {e}")
    
    # Update existing products with defaults
    print("\n📝 Updating existing products with defaults...")
    update_query = """
        UPDATE products 
        SET is_bundle = COALESCE(is_bundle, FALSE), 
            has_portions = COALESCE(has_portions, FALSE), 
            unit = COALESCE(unit, 'pcs'), 
            portion_size = COALESCE(portion_size, 1.00)
        WHERE unit IS NULL OR portion_size IS NULL OR is_bundle IS NULL OR has_portions IS NULL
    """
    
    try:
        cursor.execute(update_query)
        connection.commit()
        rows_affected = cursor.rowcount
        print(f"✅ Updated {rows_affected} products")
    except Exception as e:
        print(f"⚠️  Update failed: {e}")
    
    # Verify columns exist
    print("\n🔍 Verifying table structure...")
    cursor.execute("DESCRIBE products")
    columns = cursor.fetchall()
    
    required_columns = ['is_bundle', 'bundle_items', 'has_portions', 'unit', 'portion_size']
    found_columns = [col[0] for col in columns]
    
    all_present = all(col in found_columns for col in required_columns)
    
    if all_present:
        print("✅ All required columns are present:")
        for col in required_columns:
            print(f"   ✓ {col}")
    else:
        print("⚠️  Some columns are missing:")
        for col in required_columns:
            if col in found_columns:
                print(f"   ✓ {col}")
            else:
                print(f"   ✗ {col} (MISSING)")
    
    cursor.close()
    connection.close()
    
    print("\n🎉 Migration completed successfully!")
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    exit(1)
