import asyncio
import aiomysql
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def fix_database_schema():
    """Fix database schema to match code requirements"""
    conn = await aiomysql.connect(
        host=os.environ.get('MYSQL_HOST', 'localhost'),
        port=int(os.environ.get('MYSQL_PORT', 3306)),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', ''),
        db=os.environ.get('MYSQL_DB', 'pos_db'),
        autocommit=False
    )
    
    try:
        async with conn.cursor() as cursor:
            print("Checking and fixing database schema...")
            
            # Check and fix customers table
            await cursor.execute("SHOW COLUMNS FROM customers LIKE 'password'")
            if not await cursor.fetchone():
                print("Adding password column to customers table...")
                await cursor.execute("ALTER TABLE customers ADD COLUMN password VARCHAR(255) NOT NULL AFTER email")
                await conn.commit()
                print("✓ Added password column to customers")
            else:
                print("✓ customers.password column exists")
            
            # Check and fix orders table
            await cursor.execute("SHOW COLUMNS FROM orders LIKE 'table_id'")
            if not await cursor.fetchone():
                print("Adding missing columns to orders table...")
                await cursor.execute("""
                    ALTER TABLE orders 
                    ADD COLUMN table_id INT AFTER customer_id,
                    ADD COLUMN order_type VARCHAR(50) NOT NULL AFTER table_id,
                    ADD COLUMN customer_name VARCHAR(255) AFTER order_type,
                    ADD COLUMN customer_phone VARCHAR(50) AFTER customer_name,
                    ADD COLUMN payment_proof VARCHAR(500) AFTER payment_method,
                    ADD COLUMN payment_verified BOOLEAN DEFAULT FALSE AFTER payment_proof
                """)
                await conn.commit()
                print("✓ Added missing columns to orders")
            else:
                print("✓ orders table columns exist")
            
            # Check and fix users table for role column
            await cursor.execute("SHOW COLUMNS FROM users LIKE 'role'")
            if not await cursor.fetchone():
                print("Checking for role_id column...")
                await cursor.execute("SHOW COLUMNS FROM users LIKE 'role_id'")
                if await cursor.fetchone():
                    print("Converting role_id to role column...")
                    await cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'cashier' AFTER full_name")
                    await cursor.execute("UPDATE users SET role = CASE WHEN role_id = 1 THEN 'admin' WHEN role_id = 2 THEN 'cashier' ELSE 'staff' END")
                    await conn.commit()
                    print("✓ Converted role_id to role column")
                else:
                    print("Adding role column to users table...")
                    await cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'cashier' AFTER full_name")
                    await conn.commit()
                    print("✓ Added role column to users")
            else:
                print("✓ users.role column exists")
            
            # Verify admin user has correct password
            await cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s AND password = %s", ('admin', 'admin123'))
            admin_exists = (await cursor.fetchone())[0]
            if admin_exists == 0:
                print("Updating admin credentials...")
                await cursor.execute("UPDATE users SET password = %s WHERE username = %s", ('admin123', 'admin'))
                if cursor.rowcount == 0:
                    print("Admin user not found, creating...")
                    await cursor.execute(
                        "INSERT INTO users (username, password, full_name, role, is_active) VALUES (%s, %s, %s, %s, %s)",
                        ('admin', 'admin123', 'Administrator', 'admin', True)
                    )
                await conn.commit()
                print("✓ Admin credentials updated")
            else:
                print("✓ Admin user exists with correct password")
            
            print("\n✅ Database schema fixed successfully!")
            
    except Exception as e:
        print(f"❌ Error fixing schema: {e}")
        await conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    asyncio.run(fix_database_schema())
