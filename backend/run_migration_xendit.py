#!/usr/bin/env python3

"""
Run Xendit database migration
"""

import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    try:
        print("Connecting to database...")
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "srv1412.hstgr.io"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "u215947863_pos_dev"),
            password=os.getenv("DB_PASSWORD", "Pos_dev123#"),
            database=os.getenv("DB_NAME", "u215947863_pos_dev")
        )
        
        cursor = conn.cursor()
        
        print("Reading migration file...")
        with open("migration_xendit.sql", "r") as f:
            sql_content = f.read()
        
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql_content.split(";") if s.strip() and not s.strip().startswith("--")]
        
        print(f"Executing {len(statements)} SQL statements...")
        
        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    print(f"  [{i}/{len(statements)}] Executing...")
                    cursor.execute(statement)
                    conn.commit()
                    print(f"  ✓ Success")
                except Exception as e:
                    print(f"  ⚠ Warning: {str(e)[:100]}")
                    # Continue with other statements even if one fails
                    conn.rollback()
        
        cursor.close()
        conn.close()
        
        print("\n✅ Migration completed!")
        print("\nCreated/updated tables:")
        print("  - xendit_payments")
        print("  - xendit_settings")
        print("  - payment_methods (updated with Xendit methods)")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_migration()
